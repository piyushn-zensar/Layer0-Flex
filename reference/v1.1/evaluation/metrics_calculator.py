"""
evaluation/metrics_calculator.py

Metrics functions for each scenario level, plus a cross-scenario aggregate
used by poc_demo()'s orchestrated run.
"""


def phase_level_metrics(lifecycle_result: dict) -> dict:
    """Compute metrics per phase (Scenario 2)"""
    return {
        "deviations_count": len(lifecycle_result.get("deviations_detected", [])),
        "ecn_required": lifecycle_result.get("ecn_required", False),
        "phase_next_locked": lifecycle_result.get("phase_next_locked", False),
        "recommendation": lifecycle_result.get("recommendation", "UNKNOWN"),
    }


def portfolio_level_metrics(portfolio_result: dict) -> dict:
    """Compute metrics across all customers (Scenario 3)"""
    return {
        "conflicts_detected": len(portfolio_result.get("conflicts_detected", [])),
        "primary_recommendation": portfolio_result.get("primary_recommendation", "UNKNOWN"),
        "highest_risk_factor": max([
            portfolio_result["feasibility_matrix"]["option_a_win_all_three"].get("feasibility", "UNKNOWN"),
            portfolio_result["feasibility_matrix"]["option_b_utility_hyperscaler_decline_neocloud"].get("feasibility", "UNKNOWN"),
            portfolio_result["feasibility_matrix"]["option_c_hyperscaler_neocloud_decline_utility"].get("feasibility", "UNKNOWN"),
        ]),
    }


def calculate_aggregate_metrics(result_1: dict, result_2: dict, result_3: dict) -> dict:
    """Aggregate metrics across all 3 scenarios"""
    return {
        "total_scenarios_executed": 3,
        "scenario_1_recommendation": result_1.get("recommendation", "UNKNOWN"),
        "scenario_1_margin_estimate": result_1.get("margin_estimate", None),
        "scenario_2_ecn_required": result_2.get("ecn_required", False),
        "scenario_2_phase_3_locked": result_2.get("phase_next_locked", False),
        "scenario_3_primary_recommendation": result_3.get("primary_recommendation", "UNKNOWN"),
        "portfolio_status": "All scenarios completed",
    }
