"""Matcher agent: requirement + retrieved catalog evidence -> business unit, product, offering type."""
import json

from app.core.llm import LLMUnavailable, complete_json
from app.modules.matching.models import OFFERING_TYPES

SYSTEM = """You map one requirement from a customer RFP to the SpinCo business unit and product that would
meet it. You may only choose a product from the candidates given. Offering types:
CTO = configure-to-order (catalog product with options, quoted through CPQ);
SEMI_CUSTOM = configured product plus additional workshop work for this customer;
ETO = engineered-to-order (designed for this requirement).
NONE = not a product requirement (commercial, submission, legal); leave bu and product_id empty.
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
    prompt = (f"Requirement {requirement['req_id']} ({requirement['category']}):\n{requirement['quote']}\n\n"
              f"Candidates:\n{json.dumps(candidates, indent=1)}")
    return complete_json("match_requirement", SYSTEM, prompt, SCHEMA)


__all__ = ["propose", "LLMUnavailable"]
