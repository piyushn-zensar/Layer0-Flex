"""Reader agent: proposes requirement line items from the page layout model.

No regex. The model reads numbered lines and returns exact quotes; anchoring.py then
proves each quote exists on the page (or marks it UNANCHORED). Answers are cached and
frozen by the model gateway, so a re-run gives the same list.
"""
from app.core.llm import LLMUnavailable, complete_json
from app.modules.requirements.models import CATEGORIES

PAGES_PER_CALL = 6

SYSTEM = """You read pages of a customer's request for proposal (RFP) for engineered power and
cooling equipment, and list every requirement the bidder must meet or answer.

Rules:
- One item per distinct obligation (technical, compliance, commercial, schedule, submission, legal, staffing).
- "quote" must be copied character for character from ONE page's lines. Never paraphrase the quote.
- "text" is a short plain-English restatement (max 25 words).
- Skip the table of contents, page headers and footers, blank forms, signature blocks and pure definitions.
- If a page has no requirements, return nothing for it. Do not invent requirements."""

SCHEMA = {
    "type": "object",
    "properties": {
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "quote": {"type": "string"},
                    "text": {"type": "string"},
                    "category": {"type": "string", "enum": CATEGORIES},
                    "section": {"type": "string"},
                },
                "required": ["page", "quote", "text", "category", "section"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["requirements"],
    "additionalProperties": False,
}


def read(layout: dict) -> tuple[list[dict], list[str]]:
    """Returns (proposed requirements, problems). A chunk without a cached answer is a problem, not a guess."""
    pages = [p for p in layout["pages"] if p["lines"]]
    found, problems = [], []
    for i in range(0, len(pages), PAGES_PER_CALL):
        chunk = pages[i:i + PAGES_PER_CALL]
        prompt = "\n\n".join(
            f"=== Page {p['page']} ===\n" + "\n".join(f"L{l['n']}: {l['text']}" for l in p["lines"])
            for p in chunk
        )
        try:
            found += complete_json("read_requirements", SYSTEM, prompt, SCHEMA)["requirements"]
        except LLMUnavailable as exc:
            problems.append(f"pages {chunk[0]['page']}-{chunk[-1]['page']}: {exc}")
    return found, problems
