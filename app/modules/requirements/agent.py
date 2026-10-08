"""Reader agent: proposes requirement line items from the page layout model.

No regex for identifying requirements. The model reads numbered lines and returns exact quotes; anchoring.py then
proves each quote exists on the page (or marks it UNANCHORED). Answers are cached and
frozen by the model gateway, so a re-run gives the same list.
"""
import re

from app.core.llm import LLMUnavailable, complete_json
from app.modules.requirements.models import CATEGORIES

PAGES_PER_CALL = 6

SYSTEM = """You read pages of a customer's request for proposal (RFP) for engineered power and
cooling equipment, and list every requirement the bidder must meet or answer.

Rules:
- One item per distinct obligation (technical, compliance, commercial, schedule, submission, legal, staffing).
- "quote" must be copied character for character from ONE page's lines, without the "L12:" line labels.
  Never paraphrase the quote.
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
    # Contents pages and page furniture never reach the model (they used to become "requirements").
    pages = [p | {"lines": [l for l in p["lines"] if not l.get("furniture")]} for p in layout["pages"] if not p.get("toc")]
    pages = [p for p in pages if p["lines"]]
    found, problems = [], []
    for i in range(0, len(pages), PAGES_PER_CALL):
        chunk = pages[i:i + PAGES_PER_CALL]
        prompt = "\n\n".join(
            f"=== Page {p['page']} ===\n" + "\n".join(
                f"L{l['n']}: {l['text']}" + (" [low OCR confidence]" if l.get("low_confidence") else "")
                for l in p["lines"])
            for p in chunk
        )
        try:
            found += [r | {"quote": strip_line_labels(r["quote"])}
                      for r in complete_json("read_requirements", SYSTEM, prompt, SCHEMA)["requirements"]]
        except LLMUnavailable as exc:
            problems.append(f"pages {chunk[0]['page']}-{chunk[-1]['page']}: {exc}")
    return found, problems


def strip_line_labels(quote: str) -> str:
    """Models sometimes copy the 'L12: ' labels we add to the prompt; they are not RFP text."""
    return re.sub(r"(?:^|\s)L\d+:\s", " ", quote).strip()


if __name__ == "__main__":  # self-check: python -m app.modules.requirements.agent
    assert strip_line_labels("L48: Switchgear shall be Arc-resistant Type 2B.") == "Switchgear shall be Arc-resistant Type 2B."
    assert strip_line_labels("L54: The switchgear shall meet L55: IEEE C37.20.7.") == "The switchgear shall meet IEEE C37.20.7."
    print("agent ok")
