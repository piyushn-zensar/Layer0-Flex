"""Response-outline agent (P-10): drafts each chapter of the response from the validated answers, for the bid
manager to edit. Writing the final response stays a human task; this is a first draft with its sources.

One call per chapter that has validated answers, plus one for the executive summary. The agent may only state
what a numbered validated answer says, and every paragraph cites the numbers it rests on; a paragraph without a
valid citation is dropped (the guard below), never shown. The prompt holds the RFP's own wording for each answer
and the past responses of the same units (tone only), chosen without search, so the frozen answer does not depend
on whether retrieval runs on embeddings or keywords. Search results from both indexes are shown beside the draft
as references for the bid manager (consolidation service). No requirement ID is in the prompt (numbers instead),
so the frozen answer stays valid when IDs change.
Without a model answer (mock mode, or a new answer not yet frozen) the chapter shows the validated answers as
they are, marked "not drafted": nothing is guessed."""
from app.core.llm import LLMUnavailable, complete_json

SYSTEM = """You draft one chapter of a proposal that answers a customer's RFP, for the bid manager to edit.
Write only from the numbered VALIDATED ANSWERS: never add a product, rating, standard, date, price or promise
that they do not state, and never turn a partial answer or an exception into full compliance. Add no
qualities or benefits the answers do not state (such as reliable, robust, safe, comprehensive, realistic). Keep the
customer's terms from the RFP wording given with each answer. PAST RESPONSES show the house style only; take
no facts from them.
Write 1 to 4 short paragraphs in plain, formal English, third person ("the proposer"), and cite in "cites" the
answer numbers each paragraph rests on (at least one). List in "gaps" what the bid manager still has to add or
confirm before the chapter can go to the customer (at most 4 short items; empty if none)."""

SCHEMA = {
    "type": "object",
    "properties": {
        "paragraphs": {"type": "array", "items": {
            "type": "object",
            "properties": {"text": {"type": "string"}, "cites": {"type": "array", "items": {"type": "integer"}}},
            "required": ["text", "cites"], "additionalProperties": False}},
        "gaps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["paragraphs", "gaps"],
    "additionalProperties": False,
}
MAX_GAPS = 4


def prompt(title: str, answers: list[dict], past: list[str]) -> str:
    """answers: [{"unit", "compliance", "product", "requirement", "wording", "response"}] in RFP order (numbered from 1)."""
    lines = [f"CHAPTER: {title}", "", "VALIDATED ANSWERS ([number] unit | compliance | product | requirement;"
             " RFP wording; answer)"]
    for n, a in enumerate(answers, 1):
        lines += [f"[{n}] {a['unit']} | {a['compliance']} | {a['product'] or '-'} | {a['requirement']}",
                  f"    RFP wording: {(a['wording'] or '-')[:400]}", f"    Answer: {a['response']}"]
    lines += ["", "PAST RESPONSES (style only)"] + [f"- {r[:300]}" for r in past]
    return "\n".join(lines)


def guard(answer: dict, n_answers: int) -> tuple[list[dict], list[str], int]:
    """Keep paragraphs whose citations are all valid answer numbers (at least one). Returns (paragraphs, gaps, dropped)."""
    kept, dropped = [], 0
    for p in answer.get("paragraphs", []):
        cites = sorted(set(p.get("cites") or []))
        if p.get("text", "").strip() and cites and all(1 <= c <= n_answers for c in cites):
            kept.append({"text": p["text"].strip(), "cites": cites})
        else:
            dropped += 1
    gaps = [g.strip() for g in answer.get("gaps", []) if g.strip()][:MAX_GAPS]
    return kept, gaps, dropped


def draft(title: str, answers: list[dict], past: list[str]) -> dict:
    """{"drafted": bool, "paragraphs": [{"text", "cites"}], "gaps", "dropped", "note"}; cites are answer numbers."""
    if not answers:
        return {"drafted": False, "paragraphs": [], "gaps": [], "dropped": 0, "note": "No validated answer yet."}
    try:
        answer = complete_json("draft_outline", SYSTEM, prompt(title, answers, past), SCHEMA)
    except LLMUnavailable:
        # the demo laptop replays frozen answers: a chapter whose validated set changed since they were frozen has none
        return {"drafted": False, "paragraphs": [], "gaps": [], "dropped": 0,
                "note": "Draft not refreshed: the model service is not connected in this demo, so the validated "
                        "answers are shown as they are."}
    paragraphs, gaps, dropped = guard(answer, len(answers))
    note = f"{dropped} paragraph(s) without a valid citation removed." if dropped else ""
    return {"drafted": bool(paragraphs), "paragraphs": paragraphs, "gaps": gaps, "dropped": dropped, "note": note}


if __name__ == "__main__":  # self-check: python -m app.modules.consolidation.agent
    ok = {"paragraphs": [{"text": "Meets it.", "cites": [1, 1]}, {"text": "Invented.", "cites": []},
                         {"text": "Out of range.", "cites": [3]}, {"text": " ", "cites": [1]}],
          "gaps": ["Confirm the delivery date.", " ", "a", "b", "c", "d"]}
    paragraphs, gaps, dropped = guard(ok, 2)
    assert paragraphs == [{"text": "Meets it.", "cites": [1]}] and dropped == 3 and len(gaps) == MAX_GAPS
    p = prompt("Technical", [{"unit": "Crown", "compliance": "Comply", "product": "CROWN-ARMV", "requirement": "r",
                              "wording": "w", "response": "a"}], ["past"])
    assert "[1] Crown | Comply | CROWN-ARMV | r\n    RFP wording: w\n    Answer: a" in p and "REQ-" not in p
    assert draft("x", [], [])["drafted"] is False
    print("outline agent ok")
