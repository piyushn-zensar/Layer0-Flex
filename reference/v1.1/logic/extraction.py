"""
logic/extraction.py

Extracts a Specification object from raw scenario JSON test data.
"""

import json
import re
from pathlib import Path
from models.specification import Specification, ArcRating


def _parse_voltage(v: str | int) -> int:
    """'15kV' -> 15000, 15000 -> 15000"""
    if isinstance(v, int):
        return v
    m = re.match(r"([\d.]+)\s*kV", v, re.IGNORECASE)
    if m:
        return int(float(m.group(1)) * 1000)
    return int(re.sub(r"[^\d.]", "", v))


def _parse_current(v: str | int) -> int:
    """'600A' -> 600, 600 -> 600"""
    if isinstance(v, int):
        return v
    m = re.match(r"([\d.]+)\s*A", v, re.IGNORECASE)
    if m:
        return int(float(m.group(1)))
    return int(re.sub(r"[^\d.]", "", v))


def extract_specification(
    raw: dict,
    scenario_type: str = None,
    case_id: str = None,
    phase_number: int = None,
    customer_segment: str = None,
    quantity: int = None,
    status: str = None,
) -> Specification:
    """
    Extract a Specification from a raw scenario JSON dict (single-customer
    scenarios: scenario_1, scenario_2_phase_1/2).

    Optional overrides (case_id, phase_number, customer_segment, quantity,
    status) take priority over whatever the raw JSON contains -- this is
    what lets poc_demo() reuse the same raw payload for multiple case_ids
    without state bleeding between scenarios.
    """
    spec_block = raw.get("specification", {})
    customer = raw.get("customer", {})

    arc = None
    if "arc_rating" in spec_block and isinstance(spec_block["arc_rating"], dict):
        arc = ArcRating(**spec_block["arc_rating"])

    busbar = spec_block.get("busbar", {})

    return Specification(
        voltage_rating=_parse_voltage(spec_block.get("voltage_rating", "15kV")),
        current_rating=_parse_current(spec_block.get("current_rating", "600A")),
        type=spec_block.get("type", "metal-clad switchgear").replace(" switchgear", ""),
        standards=spec_block.get("standards", []),
        arc_rating=arc,
        short_circuit_rating=spec_block.get("short_circuit_rating"),
        bil=spec_block.get("bil"),
        busbar_material=busbar.get("material"),
        busbar_thickness=busbar.get("thickness"),
        scenario_type=scenario_type or raw.get("scenario_id"),
        phase_number=phase_number if phase_number is not None else raw.get("phase"),
        customer_segment=customer_segment or customer.get("segment"),
        case_id=case_id,
        quantity=quantity if quantity is not None else raw.get("quantity"),
        status=status or raw.get("status"),
    )


def load_scenario(path: str) -> dict:
    return json.loads(Path(path).read_text())


if __name__ == "__main__":
    raw = load_scenario("data/scenario_1_utility_bid.json")
    spec = extract_specification(raw, scenario_type="bid_stage")
    print("Extraction successful.")
    print(spec.model_dump_json(indent=2))

    assert spec.voltage_rating == 15000, f"Expected 15000, got {spec.voltage_rating}"
    assert spec.current_rating == 600, f"Expected 600, got {spec.current_rating}"
    assert spec.type == "metal-clad", f"Expected 'metal-clad', got {spec.type}"
    assert spec.customer_segment == "utility"
    print("\n✅ All extraction assertions passed.")
