"""Matcher agent: requirement + retrieved catalog evidence -> business unit, product, offering type."""
import json

from app.core.llm import LLMUnavailable, complete_json
from app.modules.matching.models import OFFERING_TYPES

SYSTEM = """You map one requirement from a customer RFP to the SpinCo business unit and product that would
meet it. You may only choose a product from the candidates given: product_id must be the id of a candidate
whose kind is "product". Candidates of kind "past_response" are evidence only, never a product_id.
The page header names the document part the requirement comes from (for example a specification for one
piece of equipment). A line about construction, materials, finish, nameplates, wiring, testing, shipping or
installation inside such a specification belongs to the product that specification is for.
Offering types:
CTO = configure-to-order (catalog product with options, quoted through CPQ);
SEMI_CUSTOM = configured product plus additional workshop work for this customer;
ETO = engineered-to-order (designed for this requirement).
NONE = not a product requirement (commercial, submission, legal, or work stated as by others or done by the
purchaser); leave bu and product_id empty.
Explain the choice in one or two sentences that cite the candidate you used."""

SCHEMA = {
    "type": "object",
    "properties": {
        "bu": {"type": "string"},
        "product_id": {"type": "string"},
        "offering_type": {"type": "string", "enum": OFFERING_TYPES},
        "confidence": {"type": "number"},
        "rationale": {"type": "string"},
    },
    "required": ["bu", "product_id", "offering_type", "confidence", "rationale"],
    "additionalProperties": False,
}


def propose(requirement: dict, candidates: list[dict]) -> dict:
    """Raises LLMUnavailable when there is no cached answer and no provider; the service then falls back."""
    prompt = (f"Requirement {requirement['req_id']} ({requirement['category']}):\n{requirement['quote']}\n"
              f"Page header: {requirement['header'] or '(none)'}\n\n"
              f"Candidates:\n{json.dumps(candidates, indent=1)}")
    return complete_json("match_requirement", SYSTEM, prompt, SCHEMA)


def page_header(page: dict) -> str:
    """The page's header block: every line that starts above the bottom of the last header line in the top half.
    Catches a title line the header detection missed next to a header line (data sheet pages, two columns)."""
    top = [line["bbox"][3] for line in page["lines"] if line.get("furniture") and line["bbox"][1] < page["height"] / 2]
    return " ".join(line["text"] for line in page["lines"] if top and line["bbox"][1] < max(top))


def checked(out: dict, candidates: list[dict]) -> dict | None:
    """The model's answer, or None when it names something that is not a candidate product (design 7.2).
    The unit always comes from the chosen product, so unit and product never disagree."""
    if out["offering_type"] == "NONE":
        return out | {"bu": "", "product_id": ""}
    product = next((c for c in candidates if c["kind"] == "product" and c["id"] == out["product_id"]), None)
    return out | {"bu": product["bu"]} if product else None


__all__ = ["propose", "page_header", "checked", "LLMUnavailable"]


if __name__ == "__main__":  # self-check: python -m app.modules.matching.agent
    line = lambda text, y, furniture=False: {"text": text, "bbox": [0, y, 100, y + 10], "furniture": furniture}
    sheet = {"height": 800, "lines": [line("Technical Requirements Data Sheet", 10, True), line("Metal Clad Switchgear", 22),
                                      line("Attachment A", 34, True), line("Panel Material Steel", 60),
                                      line("Page 3", 780, True)]}
    assert page_header(sheet) == "Technical Requirements Data Sheet Metal Clad Switchgear Attachment A"
    two_columns = {"height": 792, "lines": [{"text": "Data Sheet", "bbox": [72, 36, 230, 50.7], "furniture": True},
                                            {"text": "Metal Clad Switchgear", "bbox": [72, 48.9, 175, 63.7]},
                                            {"text": "first body line", "bbox": [72, 70, 300, 80]}]}
    assert page_header(two_columns) == "Data Sheet Metal Clad Switchgear"  # starts in the header, ends below it
    assert page_header({"height": 800, "lines": [line("no header here", 10)]}) == ""
    cands = [{"kind": "product", "id": "CROWN-ARMV", "bu": "CROWN"}, {"kind": "past_response", "id": "PAST-1", "bu": "JETCOOL"}]
    answer = {"bu": "EP2", "product_id": "CROWN-ARMV", "offering_type": "ETO", "confidence": 0.9, "rationale": ""}
    assert checked(answer, cands)["bu"] == "CROWN"                                   # unit taken from the product
    assert checked(answer | {"product_id": "PAST-1"}, cands) is None                 # past response is not a product
    assert checked(answer | {"product_id": "NOT-A-CANDIDATE"}, cands) is None
    assert checked(answer | {"offering_type": "NONE"}, cands)["product_id"] == ""    # not a product item
    print("matching agent ok")
