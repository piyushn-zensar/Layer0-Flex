"""Change agents (P-11): read the change statements of an addendum, Q&A or change request, then classify each one
against the frozen baseline. Agents propose, a person confirms every classification (rule R4).

Two model tasks, each frozen by the model gateway like the reader's answers:
- read_changes: the change document's numbered lines -> statements with a verbatim quote, the requirement as it
  reads after the change, a category and what the document says it does (add, modify, delete, clarify, info).
  Pages are packed into calls the same way as the RFP reader (short pages share a call, long pages go alone).
- classify_change: one call per page of statements. Each statement comes with up to five candidate baseline
  requirements labelled A to E, ranked without search by the service (TF-IDF), so the frozen answer does not
  depend on whether retrieval runs on embeddings or keywords. No requirement ID is in the prompt (letters
  instead), so frozen answers stay valid when IDs change (same reason as matching/agent.py).
"info" statements (cover text, signatures, acknowledge-receipt instructions) are not_a_requirement by rule, with
no model call. Without a model answer both tasks raise LLMUnavailable: nothing is guessed.
"""
import re
from concurrent.futures import ThreadPoolExecutor

from app.core.llm import LLMUnavailable, complete_json
from app.modules.changes.models import ACTIONS, KINDS, NEEDS_TARGET
from app.modules.requirements.service import CATEGORIES

LINE_BUDGET = 60     # same packing as the RFP reader (requirements/agent.py, P-18)
MAX_PAGES = 4
BATCH = 12           # statements per classify call (one page; a long page is split)
PARALLEL_CALLS = 4
LETTERS = ["A", "B", "C", "D", "E"]  # one per candidate; the service sends at most five

READ_SYSTEM = """You read pages of a change document for a customer's request for proposal (RFP) for engineered
power and cooling equipment: an addendum, answers to bidders' questions, or a change request. List every
statement in it, one item per distinct change.

Rules:
- "quote" must be copied character for character from ONE page's lines, without the "L12:" line labels.
  Never paraphrase the quote.
- "text" is the requirement as it reads AFTER the change, in plain English (max 30 words), stated as the
  requirement itself ("Bids must be valid for 120 days."), never as a description of the change ("Bid
  validity changed to 120 days."). For a deletion, say what is deleted.
- "action": add = a new requirement; modify = an existing requirement is changed or replaced; delete = an
  existing requirement is deleted; clarify = an answer or note that explains or confirms the RFP without
  changing it (a question whose answer confirms the RFP unchanged is "clarify"); info = cover text, dates,
  signatures, instructions to acknowledge receipt of the addendum, anything else that is not a requirement.
- Skip page headers, footers and blank forms. If a page has nothing, return nothing for it. Do not invent."""

READ_SCHEMA = {
    "type": "object",
    "properties": {
        "statements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "quote": {"type": "string"},
                    "text": {"type": "string"},
                    "category": {"type": "string", "enum": CATEGORIES},
                    "action": {"type": "string", "enum": ACTIONS},
                },
                "required": ["page", "quote", "text", "category", "action"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["statements"],
    "additionalProperties": False,
}

CLASSIFY_SYSTEM = """You compare change statements from a change document (addendum, answers to bidders'
questions, change request) with the frozen requirements of a customer's RFP. Each numbered statement comes with
up to five CANDIDATE baseline requirements labelled A to E (short text and RFP wording). Answer every numbered
statement once, with its number in "n".

"change" is one of:
- added: a new requirement that no candidate covers;
- modified: the statement changes or replaces what one candidate requires;
- removed: the statement deletes one candidate;
- unchanged: the statement repeats, confirms or only explains one candidate without changing what the bidder
  must do;
- not_a_requirement: cover text, dates, signatures, instructions, or anything else the bidder need not meet.
"target" is the candidate's letter for modified, removed and unchanged, else "". Choose a candidate only when
it is the same obligation; a similar topic is not enough.
"new_text" is the requirement as it reads after the change, in plain English (max 30 words), stated as the
requirement itself ("Bids must be valid for 120 days."), never as a description of the change ("Bid validity
changed to 120 days."); for removed, what is removed; for not_a_requirement, "".
"rationale": one or two sentences citing the words that decided it. "confidence": between 0 and 1."""

CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "answers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "n": {"type": "integer"},
                    "change": {"type": "string", "enum": KINDS},
                    "target": {"type": "string", "enum": [""] + LETTERS},
                    "new_text": {"type": "string"},
                    "rationale": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["n", "change", "target", "new_text", "rationale", "confidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["answers"],
    "additionalProperties": False,
}


def read(layout: dict) -> list[dict]:
    """Change statements in document order: [{"page", "quote", "text", "category", "action"}].
    Raises LLMUnavailable when any page has no answer (a half-read addendum would hide changes)."""
    pages = [p | {"lines": [l for l in p["lines"] if not l.get("furniture")]} for p in layout["pages"] if not p.get("toc")]
    chunks = pack([p for p in pages if p["lines"]])
    with ThreadPoolExecutor(PARALLEL_CALLS) as pool:
        answers = list(pool.map(_read_chunk, chunks))  # map keeps page order; re-raises LLMUnavailable
    return [s for items in answers for s in items]


def _read_chunk(chunk: list[dict]) -> list[dict]:
    prompt = "\n\n".join(f"=== Page {p['page']} ===\n" + "\n".join(f"L{l['n']}: {l['text']}" for l in p["lines"])
                         for p in chunk)
    items = complete_json("read_changes", READ_SYSTEM, prompt, READ_SCHEMA)["statements"]
    return [s | {"quote": strip_line_labels(s["quote"]), "text": s["text"].strip()} for s in items if s["quote"].strip()]


def pack(pages: list[dict]) -> list[list[dict]]:
    """Consecutive pages share a call while their lines fit LINE_BUDGET (at most MAX_PAGES); longer pages go alone.
    Copied from requirements/agent.py (modules talk only through services)."""
    chunks: list[list[dict]] = []
    for page in pages:
        last = chunks[-1] if chunks else None
        if last and len(last) < MAX_PAGES and sum(len(p["lines"]) for p in last) + len(page["lines"]) <= LINE_BUDGET:
            last.append(page)
        else:
            chunks.append([page])
    return chunks


def strip_line_labels(quote: str) -> str:
    """Models sometimes copy the 'L12: ' labels we add to the prompt; they are not document text."""
    return re.sub(r"(?:^|\s)L\d+:\s", " ", quote).strip()


def classify(statements: list[dict]) -> list[dict]:
    """statements: [{"page", "quote", "text", "action", "candidates": [{"text", "quote"}] (at most 5)}].
    Returns one checked answer per statement, same order (see checked()). Raises LLMUnavailable."""
    out: list[dict | None] = [None] * len(statements)
    asked = []
    for i, s in enumerate(statements):
        if s["action"] == "info":  # rule, no model call
            out[i] = {"change": "not_a_requirement", "target": None, "new_text": s["text"], "confidence": 1.0,
                      "rationale": "Cover text, signature or instruction (reader: info): not a requirement."}
        elif asked and asked[-1][0] == s["page"] and len(asked[-1][1]) < BATCH:
            asked[-1][1].append(i)
        else:
            asked.append((s["page"], [i]))

    def ask(batch):
        _, idx = batch
        items = [statements[i] for i in idx]
        answers = complete_json("classify_change", CLASSIFY_SYSTEM, prompt(items), CLASSIFY_SCHEMA)["answers"]
        by_n = {}
        for a in answers:
            by_n.setdefault(a["n"], a)  # the first answer for a number counts
        return idx, [by_n.get(n) for n in range(1, len(items) + 1)]

    with ThreadPoolExecutor(PARALLEL_CALLS) as pool:
        for idx, answers in pool.map(ask, asked):
            for i, a in zip(idx, answers):
                s = statements[i]
                out[i] = checked(a, s["action"], len(s["candidates"]), s["text"])
    return out


def prompt(statements: list[dict]) -> str:
    """The numbered statements with their lettered candidates. No requirement IDs, no page numbers."""
    lines = []
    for n, s in enumerate(statements, 1):
        lines += [f"[{n}] Reader says: {s['action']}", f"    Change document: {s['quote']}",
                  f"    After the change: {s['text']}", "    Candidates:"]
        lines += [f"      {letter}. {c['text']} | RFP wording: {c['quote'][:400]}"
                  for letter, c in zip(LETTERS, s["candidates"])] or ["      (none)"]
    return "\n".join(lines)


def checked(answer: dict | None, action: str, n_candidates: int, text: str) -> dict:
    """The model's answer made safe: {"change", "target" (candidate index or None), "new_text", "rationale",
    "confidence"}. Guard:
    - no answer for the statement: "added" if the reader saw an addition, else not_a_requirement, confidence 0;
    - a target letter counts only if it names a candidate that was shown; added / not_a_requirement have none;
    - modified / removed / unchanged without a valid target: "added" if the reader saw an addition, else
      not_a_requirement, with a note in the rationale and confidence 0. A person confirms every item anyway."""
    fallback = "added" if action == "add" else "not_a_requirement"
    if answer is None:
        return {"change": fallback, "target": None, "new_text": text, "confidence": 0.0,
                "rationale": "The model gave no classification for this statement; a person decides."}
    change, letter = answer["change"], answer["target"]
    target = LETTERS.index(letter) if letter in LETTERS[:n_candidates] else None
    rationale, confidence = answer["rationale"].strip(), min(max(float(answer["confidence"]), 0.0), 1.0)
    if change not in KINDS or (change in NEEDS_TARGET and target is None):
        note = f"Model said {change} without a valid candidate ({letter or 'none'}); a person decides."
        change, rationale, confidence = fallback, f"{rationale} [{note}]".strip(), 0.0
    return {"change": change, "target": target if change in NEEDS_TARGET else None,
            "new_text": answer["new_text"].strip() or text, "rationale": rationale, "confidence": confidence}


__all__ = ["read", "classify", "prompt", "checked", "pack", "LLMUnavailable"]


if __name__ == "__main__":  # self-check: python -m app.modules.changes.agent
    a = lambda change, target, new_text="new", confidence=0.9: {"n": 1, "change": change, "target": target,
                                                                "new_text": new_text, "rationale": "r", "confidence": confidence}
    assert checked(a("modified", "B"), "modify", 3, "t") == {"change": "modified", "target": 1, "new_text": "new",
                                                              "rationale": "r", "confidence": 0.9}
    bad = checked(a("modified", "D"), "modify", 3, "t")             # D was not shown
    assert bad["change"] == "not_a_requirement" and bad["target"] is None and bad["confidence"] == 0.0
    assert "without a valid candidate (D)" in bad["rationale"]
    assert checked(a("removed", ""), "add", 2, "t")["change"] == "added"                   # no target, reader saw an add
    assert checked(a("added", "A"), "add", 2, "t")["target"] is None                       # added never has a target
    assert checked(a("not_a_requirement", "A"), "info", 1, "t")["target"] is None
    assert checked(a("unchanged", "A", "", 7), "clarify", 1, "t")["new_text"] == "t"      # empty text -> reader's text
    assert checked(a("unchanged", "A", "x", 7), "clarify", 1, "t")["confidence"] == 1.0   # clamped
    assert checked(None, "modify", 2, "t")["change"] == "not_a_requirement"
    assert checked(None, "add", 0, "t") | {"rationale": ""} == {"change": "added", "target": None, "new_text": "t",
                                                               "rationale": "", "confidence": 0.0}
    st = {"page": 1, "quote": "Delete 2.3.", "text": "Arc flash label removed", "action": "delete",
          "candidates": [{"text": "Arc flash labels", "quote": "Provide arc flash labels."}]}
    p = prompt([st, st | {"candidates": []}])
    assert "      A. Arc flash labels | RFP wording: Provide arc flash labels." in p and "(none)" in p and "REQ-" not in p
    assert classify([st | {"action": "info"}])[0]["change"] == "not_a_requirement"  # rule: no model call
    assert strip_line_labels("L4: Add a spare breaker.") == "Add a spare breaker."
    pg = lambda n, lines: {"page": n, "lines": [{"n": i, "text": "x"} for i in range(lines)]}
    assert [[p["page"] for p in c] for c in pack([pg(1, 10), pg(2, 30), pg(3, 25), pg(4, 90)])] == [[1, 2], [3], [4]]
    print("changes agent ok")
