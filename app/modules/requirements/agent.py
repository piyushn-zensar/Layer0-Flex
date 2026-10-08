"""Reader agent: proposes requirement line items from the page layout model.

No regex for identifying requirements. The model reads numbered lines and returns exact quotes; anchoring.py then
proves each quote exists on the page (or marks it UNANCHORED). Answers are cached and
frozen by the model gateway, so a re-run gives the same list.
"""
import re
from concurrent.futures import ThreadPoolExecutor

from app.core.llm import LLMUnavailable, complete_json
from app.modules.requirements.models import CATEGORIES

# One page per call: GPT-4o returns at most ~10-17 items per answer, so 6-page calls dropped dense specification
# pages entirely (measured against the golden list, P-05). Calls run in parallel; answers are cached either way.
PAGES_PER_CALL = 1
PARALLEL_CALLS = 4

SYSTEM = """You read pages of a customer's request for proposal (RFP) for engineered power and
cooling equipment, and list every requirement the bidder must meet or answer.

Rules:
- List EVERY requirement on the page: one item per distinct obligation (technical, compliance, commercial,
  schedule, submission, legal, staffing). Dense specification pages often have 15 to 30.
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
    chunks = [pages[i:i + PAGES_PER_CALL] for i in range(0, len(pages), PAGES_PER_CALL)]
    with ThreadPoolExecutor(PARALLEL_CALLS) as pool:
        answers = list(pool.map(_read_chunk, chunks))  # map keeps page order
    return [r for items, _ in answers for r in items], [problem for _, problem in answers if problem]


def _read_chunk(chunk: list[dict]) -> tuple[list[dict], str | None]:
    prompt = "\n\n".join(
        f"=== Page {p['page']} ===\n" + "\n".join(
            f"L{l['n']}: {l['text']}" + (" [low OCR confidence]" if l.get("low_confidence") else "")
            for l in p["lines"])
        for p in chunk
    )
    try:
        items = complete_json("read_requirements", SYSTEM, prompt, SCHEMA)["requirements"]
        return [r | {"quote": strip_line_labels(r["quote"])} for r in items], None
    except LLMUnavailable as exc:
        return [], f"pages {chunk[0]['page']}-{chunk[-1]['page']}: {exc}"


def strip_line_labels(quote: str) -> str:
    """Models sometimes copy the 'L12: ' labels we add to the prompt; they are not RFP text."""
    return re.sub(r"(?:^|\s)L\d+:\s", " ", quote).strip()


if __name__ == "__main__":  # self-check: python -m app.modules.requirements.agent
    assert strip_line_labels("L48: Switchgear shall be Arc-resistant Type 2B.") == "Switchgear shall be Arc-resistant Type 2B."
    assert strip_line_labels("L54: The switchgear shall meet L55: IEEE C37.20.7.") == "The switchgear shall meet IEEE C37.20.7."
    print("agent ok")
