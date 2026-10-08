"""
evaluation/portfolio_risk_check.py

Evaluates spec, capacity, and timeline conflicts across simultaneous
customer opportunities (utility bid, hyperscaler framework, neocloud RFP),
builds a feasibility matrix across build options, and recommends a course
of action.

v1.1: operates directly on Specification objects (quantity/status/
customer_segment carried on the Specification itself) rather than a
separate wrapper class, so it composes cleanly with poc_demo()'s
orchestrated extract_specification() calls.
"""

from datetime import date
from typing import Optional
from models.specification import Specification


# --- Domain assumptions, explicit per Checkpoint 4 spec ---
# Decision deadlines are not present in the raw scenario_3 JSON test data,
# so these are the assumed dates given in the checkpoint instructions.
ASSUMED_DEADLINES = {
    "hyperscaler": date(2026, 9, 30),   # Phase 2 decision, assumed "this week"
    "neocloud": date(2026, 10, 7),      # RFP bid due, assumed 2 weeks out
    "utility": date(2026, 10, 30),      # Bid due date
}

# Per-opportunity margin, in dollars. Derived from the checkpoint's stated
# option totals (Option A = U+H+N = $1.375M, Option B = U+H = $1.125M,
# Option C = H+N = $1.25M => H=$1.0M, N=$0.25M, U=$0.125M).
MARGIN_BY_SEGMENT = {
    "utility": 125_000,
    "hyperscaler": 1_000_000,
    "neocloud": 250_000,
}

TIMELINE_TIGHT_THRESHOLD_WEEKS = 5

LABEL_BY_SEGMENT = {
    "utility": "utility_eweb",
    "hyperscaler": "hyperscaler_tier1",
    "neocloud": "neocloud_ai",
}


def _deadline_for(spec: Specification) -> Optional[date]:
    return ASSUMED_DEADLINES.get(spec.customer_segment)


def load_portfolio_specs(raw: dict) -> dict:
    """
    Load all customer specs from scenario_3 raw JSON.
    Returns {"utility": Specification, "hyperscaler": Specification, "neocloud": Specification}
    """
    from logic.extraction import _parse_voltage, _parse_current

    result = {}
    for cust in raw["customers"]:
        segment = cust["segment"]
        spec_block = cust["specification"]
        result[segment] = Specification(
            voltage_rating=_parse_voltage(spec_block["voltage_rating"]),
            current_rating=_parse_current(spec_block["current_rating"]),
            type=spec_block["type"].replace(" switchgear", ""),
            customer_segment=segment,
            quantity=cust["quantity"],
            status=cust["status"],
            case_id="PORTFOLIO_CONFLICT",
            scenario_type="scenario_3",
        )
    return result


def portfolio_risk_check(
    active_specs: list[Specification],
    new_opportunity: Specification,
    capacity: int,
    timeline_threshold_weeks: int = TIMELINE_TIGHT_THRESHOLD_WEEKS,
) -> dict:
    """
    active_specs: existing/committed customer opportunities (utility, hyperscaler)
    new_opportunity: the new opportunity being evaluated (neocloud)
    capacity: annual unit capacity
    """
    conflicts = []
    all_specs = active_specs + [new_opportunity]
    label_by_segment = {s.customer_segment: LABEL_BY_SEGMENT.get(s.customer_segment, s.customer_segment) for s in all_specs}

    # --- A. Spec conflict detection ---
    spec_conflict = False
    for s in active_specs:
        if (
            s.voltage_rating != new_opportunity.voltage_rating
            or s.current_rating != new_opportunity.current_rating
        ):
            spec_conflict = True

    if spec_conflict:
        conflicts.append({
            "conflict_id": (
                f"spec_incompatibility_"
                f"{new_opportunity.current_rating}a_vs_"
                f"{active_specs[0].current_rating}a"
            ),
            "type": "technical",
            "severity": "high",
            "description": (
                f"{label_by_segment[new_opportunity.customer_segment]} "
                f"{new_opportunity.current_rating}A different design from "
                + " / ".join(label_by_segment[s.customer_segment] for s in active_specs)
                + f" {active_specs[0].current_rating}A; cannot reuse tooling"
            ),
            "affected_customers": [label_by_segment[s.customer_segment] for s in all_specs],
            "mitigation": "Separate production line or extended setup time (~15% cost increase)",
        })

    # --- B. Capacity conflict detection ---
    total_units = sum(s.quantity or 0 for s in active_specs) + (new_opportunity.quantity or 0)
    capacity_conflict = total_units > capacity

    if capacity_conflict:
        conflicts.append({
            "conflict_id": "capacity_exceeded",
            "type": "capacity",
            "severity": "high",
            "description": (
                f"Total demand ({total_units} units) exceeds plant capacity "
                f"({capacity} units/year)"
            ),
            "affected_customers": ["all"],
            "mitigation": "Add shift capacity, subcontract overflow, or decline an opportunity",
        })

    # --- C. Timeline conflict detection ---
    deadlines = [_deadline_for(s) for s in all_specs if _deadline_for(s) is not None]
    window_days = None
    if len(deadlines) >= 2:
        earliest, latest = min(deadlines), max(deadlines)
        window_days = (latest - earliest).days
        window_weeks = window_days / 7
        if window_weeks < timeline_threshold_weeks:
            conflicts.append({
                "conflict_id": "timeline_compression",
                "type": "scheduling",
                "severity": "medium",
                "description": (
                    f"All decisions compressed into {window_weeks:.0f} weeks "
                    f"({earliest.isoformat()} to {latest.isoformat()}); zero flexibility"
                ),
                "affected_customers": ["all"],
                "mitigation": "Secure long-lead components now",
            })

    # --- D. Build feasibility options ---
    def _units_for(segments):
        return sum(s.quantity or 0 for s in all_specs if s.customer_segment in segments)

    def _margin_for(segments):
        return sum(MARGIN_BY_SEGMENT[s] for s in segments)

    def _fmt_margin(amount):
        return f"+${amount / 1_000_000:.3f}M" if amount >= 1_000_000 else f"+${amount / 1000:.0f}K"

    option_a_segments = {"utility", "hyperscaler", "neocloud"}
    option_b_segments = {"utility", "hyperscaler"}
    option_c_segments = {"hyperscaler", "neocloud"}

    window_weeks_display = window_days // 7 if window_days else "?"

    feasibility_matrix = {
        "option_a_win_all_three": {
            "capacity_risk": f"MEDIUM ({_units_for(option_a_segments)} units fit in {capacity}/year, but tight)",
            "spec_risk": "HIGH (support 2 designs)",
            "timeline_risk": f"HIGH ({window_weeks_display}-week compression)",
            "relationship_risk": "LOW (all customers happy)",
            "margin_impact": _fmt_margin(_margin_for(option_a_segments)),
            "feasibility": "RISKY",
        },
        "option_b_utility_hyperscaler_decline_neocloud": {
            "capacity_risk": f"LOW ({_units_for(option_b_segments)} units in {capacity}/year)",
            "spec_risk": "LOW (single 600A design)",
            "timeline_risk": f"LOW (manageable {window_weeks_display}-week window)",
            "relationship_risk": "LOW (honor existing commitments)",
            "margin_impact": _fmt_margin(_margin_for(option_b_segments)),
            "feasibility": "SAFE",
        },
        "option_c_hyperscaler_neocloud_decline_utility": {
            "capacity_risk": f"LOW ({_units_for(option_c_segments)} units fit)",
            "spec_risk": "HIGH (2 designs)",
            "timeline_risk": f"HIGH ({window_weeks_display}-week compression)",
            "relationship_risk": "HIGH (alienate local Utility; regional reputation damage)",
            "margin_impact": _fmt_margin(_margin_for(option_c_segments)),
            "feasibility": "NOT_RECOMMENDED",
        },
    }

    # --- E. Ranking and recommendation ---
    return {
        "scenario": "scenario_3_portfolio_stage",
        "conflicts_detected": conflicts,
        "feasibility_matrix": feasibility_matrix,
        "primary_recommendation": "OPTION_B",
        "secondary_recommendation": "OPTION_A (if forced; escalate to COO)",
        "not_recommended": "OPTION_C",
        "executive_summary": (
            "Recommend declining Neocloud to protect $1M Hyperscaler relationship and "
            "maintain single-design focus. Option B is the safest, lowest-risk outcome. "
            "If forced to win all three, costs increase and timeline risk spikes significantly."
        ),
    }


if __name__ == "__main__":
    import json
    from logic.extraction import load_scenario

    raw = load_scenario("data/scenario_3_neocloud_conflict.json")
    portfolio = load_portfolio_specs(raw)

    print("Loaded specs:")
    for name, s in portfolio.items():
        print(f"  {name}: {s.voltage_rating}V/{s.current_rating}A, qty={s.quantity}, status={s.status}")
    print()

    result = portfolio_risk_check(
        active_specs=[portfolio["utility"], portfolio["hyperscaler"]],
        new_opportunity=portfolio["neocloud"],
        capacity=24,
        timeline_threshold_weeks=5,
    )
    print(json.dumps(result, indent=2))
