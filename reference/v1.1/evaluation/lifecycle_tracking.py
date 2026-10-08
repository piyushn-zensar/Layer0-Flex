"""
evaluation/lifecycle_tracking.py

Compares two phases of an execution-stage order (e.g. Hyperscaler Phase 1
vs. Phase 2), assesses deviation severity across technical/supply-chain/
field risk, decides whether an ECN is required, and produces a phase-3
locking recommendation.
"""

from typing import Optional
from models.specification import Specification


# --- Thickness normalization: "3/8 in" -> 0.375, "1/2 in" -> 0.5.
# Also passes through a bare float/int unchanged (e.g. 0.375), since
# Specification.busbar_thickness accepts either representation. ---
def _thickness_to_decimal(thickness) -> Optional[float]:
    if thickness is None:
        return None
    if isinstance(thickness, (int, float)):
        return round(float(thickness), 4)
    t = thickness.strip().lower().replace("in", "").strip()
    if "/" in t:
        num, denom = t.split("/")
        return round(float(num) / float(denom), 4)
    try:
        return float(t)
    except ValueError:
        return None


# Fields we compare field-by-field between phases
COMPARED_FIELDS = [
    "voltage_rating",
    "current_rating",
    "type",
    "busbar_material",
    "busbar_thickness",
]


def _get_field_value(spec: Specification, field: str):
    if field == "busbar_thickness":
        return _thickness_to_decimal(spec.busbar_thickness)
    return getattr(spec, field)


# --- Risk rules (encode the domain knowledge from the checkpoint spec) ---
def _assess_busbar_material_risk(baseline_val, current_val) -> dict:
    """Copper -> aluminum: lower conductivity compensated by thicker busbar;
    aluminum is easier to source; mixed fleet needs different maintenance procedures."""
    if baseline_val == current_val:
        return {"technical_risk": "low", "supply_chain_risk": "low", "field_risk": "low"}
    if baseline_val == "copper" and current_val == "aluminum":
        return {"technical_risk": "medium", "supply_chain_risk": "low", "field_risk": "medium"}
    if baseline_val == "aluminum" and current_val == "copper":
        return {"technical_risk": "low", "supply_chain_risk": "medium", "field_risk": "medium"}
    return {"technical_risk": "medium", "supply_chain_risk": "medium", "field_risk": "medium"}


def _assess_busbar_thickness_risk(baseline_val, current_val) -> dict:
    """A thickness change alone (already compensating for a material change)
    carries low risk across the board."""
    if baseline_val == current_val:
        return {"technical_risk": "low", "supply_chain_risk": "low", "field_risk": "low"}
    return {"technical_risk": "low", "supply_chain_risk": "low", "field_risk": "low"}


def _assess_core_rating_risk(field: str, baseline_val, current_val) -> dict:
    """Voltage/current/type changes are treated as high risk across the
    board -- these define the product family and are not expected to
    change within a phased framework."""
    if baseline_val == current_val:
        return {"technical_risk": "low", "supply_chain_risk": "low", "field_risk": "low"}
    return {"technical_risk": "high", "supply_chain_risk": "high", "field_risk": "high"}


RISK_ASSESSORS = {
    "busbar_material": _assess_busbar_material_risk,
    "busbar_thickness": _assess_busbar_thickness_risk,
    "voltage_rating": lambda b, c: _assess_core_rating_risk("voltage_rating", b, c),
    "current_rating": lambda b, c: _assess_core_rating_risk("current_rating", b, c),
    "type": lambda b, c: _assess_core_rating_risk("type", b, c),
}

_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}


def _max_severity(*severities: str) -> str:
    return max(severities, key=lambda s: _SEVERITY_RANK.get(s, 0))


def lifecycle_tracking(
    phase_baseline: Specification,
    phase_current: Specification,
    phase_next: Optional[Specification] = None,
) -> dict:
    """
    Compare phase_baseline vs. phase_current field-by-field, assess
    deviation severity, decide ECN requirement, and lock/unlock phase_next.
    """
    deviations = []

    for field in COMPARED_FIELDS:
        baseline_val = _get_field_value(phase_baseline, field)
        current_val = _get_field_value(phase_current, field)

        if baseline_val != current_val:
            risk = RISK_ASSESSORS[field](baseline_val, current_val)
            severity = _max_severity(
                risk["technical_risk"], risk["supply_chain_risk"], risk["field_risk"]
            )
            # report raw (non-normalized) values for readability
            raw_baseline = getattr(phase_baseline, field)
            raw_current = getattr(phase_current, field)
            deviations.append({
                "field": field,
                "phase_1_value": raw_baseline,
                "phase_2_value": raw_current,
                "severity": severity,
                "technical_risk": risk["technical_risk"],
                "supply_chain_risk": risk["supply_chain_risk"],
                "field_risk": risk["field_risk"],
            })

    # --- ECN trigger: any deviation with severity >= medium ---
    ecn_required = any(_SEVERITY_RANK[d["severity"]] >= _SEVERITY_RANK["medium"] for d in deviations)

    # --- Phase 3 locking ---
    if phase_next is not None:
        phase_next_locked = False
        phase_next_reasoning = "Phase 3 spec provided and no blocking ECN outstanding."
    elif ecn_required:
        phase_next_locked = True
        phase_next_reasoning = (
            "Cannot proceed to Phase 3 until ECN approved and design review complete"
        )
    else:
        phase_next_locked = False
        phase_next_reasoning = "No ECN required; Phase 3 planning may proceed."

    # --- Overall recommendation ---
    has_high = any(d["severity"] == "high" for d in deviations)
    has_medium = any(d["severity"] == "medium" for d in deviations)

    if has_high:
        recommendation = "REJECT"
    elif has_medium and ecn_required:
        recommendation = "PROCEED_WITH_CAUTION"
    elif deviations:
        recommendation = "PROCEED"
    else:
        recommendation = "PROCEED"

    return {
        "scenario": "scenario_2_execution_stage",
        "phase": phase_current.phase_number,
        "deviations_detected": deviations,
        "ecn_required": ecn_required,
        "phase_next_locked": phase_next_locked,
        "phase_next_reasoning": phase_next_reasoning,
        "recommendation": recommendation,
    }


if __name__ == "__main__":
    import json
    from logic.extraction import load_scenario, extract_specification

    raw_p1 = load_scenario("data/scenario_2_hyperscaler_phase1.json")
    raw_p2 = load_scenario("data/scenario_2_hyperscaler_phase2.json")

    spec_p1 = extract_specification(raw_p1, scenario_type="scenario_2_hyperscaler_phase1")
    spec_p2 = extract_specification(raw_p2, scenario_type="scenario_2_hyperscaler_phase2")

    result = lifecycle_tracking(phase_baseline=spec_p1, phase_current=spec_p2, phase_next=None)
    print(json.dumps(result, indent=2))
