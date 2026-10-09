"""Matcher agent: requirement + retrieved catalog evidence -> business unit(s), product, offering type."""
import json

from app.core.llm import LLMUnavailable, complete_json
from app.modules.matching.models import OFFERING_TYPES

MAX_UNITS = 3  # ponytail: guard against a talkative answer flooding inboxes; raise if real bids need more

SYSTEM = """You map one requirement from a customer RFP to the SpinCo business units and products that would
meet it. You may only choose products from the candidates given: product_id must be the id of a candidate
whose kind is "product". Candidates of kind "past_response" are evidence only, never a product_id.
"units" lists the unit and product for each part of the requirement, the main one first. List more than one
only when the requirement needs products from several business units.
The page header names the document part the requirement comes from (for example a specification for one
piece of equipment). A line about construction, materials, finish, nameplates, wiring, testing, shipping or
installation inside such a specification belongs to the product that specification is for.
Offering types:
CTO = configure-to-order (catalog product with options, quoted through CPQ);
SEMI_CUSTOM = configured product plus additional workshop work for this customer;
ETO = engineered-to-order (designed for this requirement).
Return an empty "units" list when it is not a product requirement (commercial, submission, legal, or work
stated as by others or done by the purchaser): the bid manager answers it.
Explain the choice in one or two sentences that cite the candidates you used."""

SCHEMA = {
    "type": "object",
    "properties": {
        "units": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "bu": {"type": "string"},
                    "product_id": {"type": "string"},
                    "offering_type": {"type": "string", "enum": [t for t in OFFERING_TYPES if t != "NONE"]},
                },
                "required": ["bu", "product_id", "offering_type"],
                "additionalProperties": False,
            },
        },
        "confidence": {"type": "number"},
        "rationale": {"type": "string"},
    },
    "required": ["units", "confidence", "rationale"],
    "additionalProperties": False,
}


def propose(requirement: dict, candidates: list[dict]) -> dict:
    """Raises LLMUnavailable when there is no cached answer and no provider; the service then falls back."""
    # No requirement ID in the prompt: the frozen answer is keyed by the prompt, so the same RFP text gets the same
    # answer in every opportunity (demo, re-upload, laptop package) instead of new model calls each time.
    prompt = (f"Requirement ({requirement['category']}):\n{requirement['quote']}\n"
              f"Page header: {requirement['header'] or '(none)'}\n\n"
              f"Candidates:\n{json.dumps(candidates, indent=1)}")
    return complete_json("match_requirement", SYSTEM, prompt, SCHEMA)


def page_header(page: dict) -> str:
    """The page's header block: every line that starts above the bottom of the last header line in the top half.
    Catches a title line the header detection missed next to a header line (data sheet pages, two columns)."""
    top = [line["bbox"][3] for line in page["lines"] if line.get("furniture") and line["bbox"][1] < page["height"] / 2]
    return " ".join(line["text"] for line in page["lines"] if top and line["bbox"][1] < max(top))


def checked(out: dict, candidates: list[dict]) -> dict | None:
    """The model's answer with only candidate products kept (design 7.2), at most MAX_UNITS, one per product.
    Each unit comes from its product, so unit and product never disagree. None when the model named
    products but none of them is a candidate product; an empty list means not a product item."""
    products = {c["id"]: c for c in candidates if c["kind"] == "product"}
    units = []
    for u in out["units"]:
        p = products.get(u["product_id"])
        if p and all(x["product_id"] != p["id"] for x in units):
            units.append({"bu": p["bu"], "product_id": p["id"], "offering_type": u["offering_type"]})
    if out["units"] and not units:
        return None
    return out | {"units": units[:MAX_UNITS]}


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

    cands = [{"kind": "product", "id": "CROWN-ARMV", "bu": "CROWN"}, {"kind": "product", "id": "EP2-RPP", "bu": "EP2"},
             {"kind": "product", "id": "CROWN-ACC", "bu": "CROWN"}, {"kind": "product", "id": "ANORD-PDU", "bu": "ANORD"},
             {"kind": "past_response", "id": "PAST-1", "bu": "JETCOOL"}]
    unit = lambda pid, bu="X": {"bu": bu, "product_id": pid, "offering_type": "ETO"}
    answer = lambda *units: {"units": list(units), "confidence": 0.9, "rationale": ""}
    two = checked(answer(unit("CROWN-ARMV", "EP2"), unit("EP2-RPP")), cands)["units"]
    assert [(u["bu"], u["product_id"]) for u in two] == [("CROWN", "CROWN-ARMV"), ("EP2", "EP2-RPP")]  # unit from product
    assert checked(answer(unit("PAST-1")), cands) is None                    # a past response is not a product
    assert checked(answer(unit("NOT-A-CANDIDATE")), cands) is None
    assert checked(answer(), cands)["units"] == []                           # not a product item
    assert [u["product_id"] for u in checked(answer(unit("PAST-1"), unit("EP2-RPP")), cands)["units"]] == ["EP2-RPP"]
    assert len(checked(answer(*(unit(p) for p in ("CROWN-ARMV", "EP2-RPP", "CROWN-ACC", "ANORD-PDU", "EP2-RPP"))),
                       cands)["units"]) == MAX_UNITS                          # capped, duplicates dropped
    print("matching agent ok")
