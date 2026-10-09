"""Grouping agent: related line items on a page become one requirement with sub-requirements.

The reader agent lists every obligation separately, so a list such as "submit these 12 drawings" arrives as 12
line items. The model groups them per page (it never changes or drops an item: unassigned items stay on their own).
True duplicates (the same quote again, often a cover-page restatement of the specification) are found by text
comparison, not by the model, and point to the first occurrence.
Answers are cached and frozen by the model gateway, like the reader's.
"""
import difflib
from concurrent.futures import ThreadPoolExecutor

from app.core.llm import LLMUnavailable, complete_json
from app.modules.requirements import anchoring
from app.modules.requirements.models import CATEGORIES

MIN_ITEMS = 3            # a page with fewer items is not worth a call
DUPLICATE_RATIO = 0.92   # quotes this similar (after normalising) are the same requirement
PARALLEL_CALLS = 4

SYSTEM = """You organise the requirements a bidder must meet, found on one page of a request for proposal (RFP).

Group items that are parts of ONE obligation, so the bid team answers them together. Typical groups: a list of
drawings or documents to submit; a list of standards to comply with; the features of one piece of equipment;
the tests of one test programme; the parts of one insurance or bond requirement.

Rules:
- Use each item number at most once. Leave an item alone when it is a separate obligation.
- A group needs at least two items. Do not create groups of one.
- "title" is a short plain-English statement of the whole obligation (max 20 words).
- "category" is the category of the whole group.
- Do not invent items, and do not reword the items themselves."""

SCHEMA = {
    "type": "object",
    "properties": {
        "groups": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "category": {"type": "string", "enum": CATEGORIES},
                    "members": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["title", "category", "members"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["groups"],
    "additionalProperties": False,
}


def duplicates(items: list[dict]) -> dict[int, int]:
    """{index: index of the first occurrence} for items whose quote repeats an earlier one (any page)."""
    seen: list[tuple[int, str]] = []
    exact: dict[str, int] = {}
    out = {}
    for i, it in enumerate(items):
        q = anchoring.normalise(it["quote"]).rstrip(".;:, ")
        if q in exact:
            out[i] = exact[q]
            continue
        for j, earlier in seen:
            # cheap upper bounds first: a full comparison of every pair (about 350,000 for 840 items) takes minutes
            if len(q) > 40 and len(earlier) > 40:
                sm = difflib.SequenceMatcher(None, q, earlier, autojunk=False)
                if sm.real_quick_ratio() >= DUPLICATE_RATIO and sm.quick_ratio() >= DUPLICATE_RATIO \
                        and sm.ratio() >= DUPLICATE_RATIO:
                    out[i] = j
                    break
        else:
            seen.append((i, q))
            exact[q] = i
    return out


def group(items: list[dict]) -> tuple[list[dict], list[str]]:
    """items: [{"page", "text", "category", ...}] in document order (duplicates already removed).
    Returns ([{"title", "category", "members": [item indexes]}], problems)."""
    pages: dict[int, list[int]] = {}
    for i, it in enumerate(items):
        if it.get("page"):
            pages.setdefault(it["page"], []).append(i)
    work = [(p, idx) for p, idx in sorted(pages.items()) if len(idx) >= MIN_ITEMS]
    with ThreadPoolExecutor(PARALLEL_CALLS) as pool:
        answers = list(pool.map(lambda w: _group_page(w[0], w[1], items), work))
    groups = [g for gs, _ in answers for g in gs]
    return groups, [p for _, p in answers if p]


def _group_page(page: int, idx: list[int], items: list[dict]) -> tuple[list[dict], str | None]:
    prompt = f"Page {page} of the RFP. Items:\n" + "\n".join(
        f"{n}. [{items[i]['category']}] {items[i]['text']}" for n, i in enumerate(idx, 1))
    try:
        answer = complete_json("group_requirements", SYSTEM, prompt, SCHEMA)["groups"]
    except LLMUnavailable as exc:
        return [], f"page {page}: not grouped ({exc})"
    return checked(answer, idx), None


def checked(answer: list[dict], idx: list[int]) -> list[dict]:
    """Keep only valid groups: known item numbers, each used once, at least two per group."""
    used, out = set(), []
    for g in answer:
        members = [idx[n - 1] for n in dict.fromkeys(g["members"]) if 1 <= n <= len(idx) and idx[n - 1] not in used]
        if len(members) >= 2 and g["title"].strip():
            used.update(members)
            out.append({"title": g["title"].strip(), "category": g["category"], "members": members})
    return out


if __name__ == "__main__":  # self-check: python -m app.modules.requirements.grouping
    items = [{"quote": "Submit installation drawings."}, {"quote": "Submit connection diagrams."},
             {"quote": "Submit installation drawings"}, {"quote": "Submit Installation  Drawings."}]
    assert duplicates(items) == {2: 0, 3: 0}
    assert checked([{"title": "Drawings", "category": "submission", "members": [1, 2, 2, 9]},
                    {"title": "Alone", "category": "technical", "members": [3]},
                    {"title": "Reused", "category": "technical", "members": [1, 3]}], [10, 11, 12]) == [
        {"title": "Drawings", "category": "submission", "members": [10, 11]}]
    print("grouping ok")
