"""
evaluation/poc_demo.py

Orchestrates Scenarios 1, 2, and 3 end-to-end in a single call, with
case_id isolation so no scenario's Specification state bleeds into
another's, then aggregates all 3 results plus cross-scenario metrics.
"""

from datetime import datetime

from logic.extraction import extract_specification, load_scenario
from logic.bid_recommendation import bid_recommendation
from evaluation.lifecycle_tracking import lifecycle_tracking
from evaluation.portfolio_risk_check import portfolio_risk_check
from evaluation.metrics_calculator import (
    phase_level_metrics,
    portfolio_level_metrics,
    calculate_aggregate_metrics,
)


def _combine_hyperscaler_phases(raw_p1: dict, raw_p2: dict) -> dict:
    """
    Build a portfolio-level hyperscaler payload out of the two phase
    payloads: combined quantity (8 + 8 = 16), core rating fields taken
    from Phase 1 (voltage/current/type don't change between phases --
    only busbar material/thickness do, which don't matter for the
    portfolio-level spec-conflict check in Scenario 3).
    """
    p1_spec = raw_p1["specification"]
    return {
        "specification": {
            "voltage_rating": p1_spec["voltage_rating"],
            "current_rating": p1_spec["current_rating"],
            "type": p1_spec["type"],
        },
        "quantity": raw_p1["quantity"] + raw_p2["quantity"],
        "status": "pending",  # Phase 2 not yet committed
    }


def poc_demo() -> dict:
    """
    Orchestrate all 3 scenarios end-to-end.
    No state pollution; case_id isolation via Specification.
    """
    scenario_1_data = load_scenario("data/scenario_1_utility_bid.json")
    scenario_2_phase1_data = load_scenario("data/scenario_2_hyperscaler_phase1.json")
    scenario_2_phase2_data = load_scenario("data/scenario_2_hyperscaler_phase2.json")
    scenario_3_neocloud_data = load_scenario("data/scenario_3_neocloud_conflict.json")

    # --- SCENARIO 1: Bid-Stage Intake ---
    spec_1 = extract_specification(
        scenario_1_data,
        case_id="EWEB_25_151_G",
        scenario_type="bid_stage",
    )
    rfp_timeline_weeks = scenario_1_data.get("delivery_timeline", {}).get("lead_time_weeks", 32)
    result_1 = bid_recommendation(spec_1, rfp_timeline_weeks=rfp_timeline_weeks)

    # --- SCENARIO 2: Execution-Stage (Lifecycle Tracking) ---
    spec_2_phase1 = extract_specification(
        scenario_2_phase1_data,
        case_id="HYPERSCALER_TIER1_3YR",
        phase_number=1,
        scenario_type="execution_stage",
    )
    spec_2_phase2 = extract_specification(
        scenario_2_phase2_data,
        case_id="HYPERSCALER_TIER1_3YR",
        phase_number=2,
        scenario_type="execution_stage",
    )
    result_2 = lifecycle_tracking(spec_2_phase1, spec_2_phase2)

    # --- SCENARIO 3: Portfolio-Stage (Cross-Customer Risk) ---
    # Reuse scenario_1_data (utility) and the combined phase 1+2 payload
    # (hyperscaler), plus the dedicated neocloud conflict data -- each
    # extracted under case_id="PORTFOLIO_CONFLICT" so this pass is
    # isolated from the case_ids used above, even though the underlying
    # raw JSON is shared with Scenarios 1 and 2.
    scenario_2_phase1_and_2_combined = _combine_hyperscaler_phases(
        scenario_2_phase1_data, scenario_2_phase2_data
    )

    spec_3_utility = extract_specification(
        scenario_1_data,
        case_id="PORTFOLIO_CONFLICT",
        customer_segment="utility",
        scenario_type="portfolio_stage",
        quantity=scenario_1_data.get("quantity"),
        status=scenario_1_data.get("rfp", {}).get("status"),
    )
    spec_3_hyperscaler = extract_specification(
        scenario_2_phase1_and_2_combined,
        case_id="PORTFOLIO_CONFLICT",
        customer_segment="hyperscaler",
        scenario_type="portfolio_stage",
    )
    # Neocloud data lives inside scenario_3's "customers" list, not its
    # own single-customer payload, so pull it out directly.
    neocloud_raw = next(
        c for c in scenario_3_neocloud_data["customers"] if c["segment"] == "neocloud"
    )
    spec_3_neocloud = extract_specification(
        {"specification": neocloud_raw["specification"]},
        case_id="PORTFOLIO_CONFLICT",
        customer_segment="neocloud",
        scenario_type="portfolio_stage",
        quantity=neocloud_raw["quantity"],
        status=neocloud_raw["status"],
    )

    result_3 = portfolio_risk_check(
        active_specs=[spec_3_utility, spec_3_hyperscaler],
        new_opportunity=spec_3_neocloud,
        capacity=24,
        timeline_threshold_weeks=5,
    )

    # --- AGGREGATE RESULTS ---
    aggregate = {
        "scenario_1_bid_stage": result_1,
        "scenario_2_execution_stage": result_2,
        "scenario_3_portfolio_stage": result_3,
        "aggregate_metrics": calculate_aggregate_metrics(result_1, result_2, result_3),
        "timestamp": datetime.now().isoformat(),
    }

    return aggregate


if __name__ == "__main__":
    import json
    import time

    start = time.perf_counter()
    results = poc_demo()
    elapsed = time.perf_counter() - start

    print(json.dumps(results, indent=2))
    print(f"\n--- Execution time: {elapsed:.4f}s ---")
