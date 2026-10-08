"""
logic/bid_recommendation.py

Compares a Specification against Critical Power Products' standard
portfolio and produces a BID / HOLD / NO_BID recommendation.
"""

from models.specification import Specification

# --- Critical Power Products' standard portfolio baseline ---
PORTFOLIO_BASELINE = {
    "voltage_rating": 15000,       # 15kV
    "current_rating": 600,        # 600A
    "type": "metal-clad",
    "standard_arc_accessibility": "Type 2B",
    "standard_delivery_weeks": 32,
}

BASELINE_MARGIN = 0.18  # 18%
MARGIN_PENALTY_PER_DEVIATION = {
    "low": 0.0,
    "medium": 0.03,
    "high": 0.05,
}


def _severity_rank(sev: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(sev, 0)


def bid_recommendation(spec: Specification, rfp_timeline_weeks: int = None) -> dict:
    """
    Evaluate a Specification against the standard portfolio and return
    a structured bid recommendation.
    """
    deviations = []

    # 1. Voltage / current / type match against portfolio (in-portfolio check)
    in_portfolio = (
        spec.voltage_rating == PORTFOLIO_BASELINE["voltage_rating"]
        and spec.current_rating == PORTFOLIO_BASELINE["current_rating"]
        and spec.type == PORTFOLIO_BASELINE["type"]
    )
    if not in_portfolio:
        deviations.append({
            "field": "voltage_rating/current_rating/type",
            "detail": (
                f"Requested {spec.voltage_rating}V/{spec.current_rating}A/{spec.type} "
                f"vs. standard portfolio {PORTFOLIO_BASELINE['voltage_rating']}V/"
                f"{PORTFOLIO_BASELINE['current_rating']}A/{PORTFOLIO_BASELINE['type']}"
            ),
            "severity": "high",
        })

    # 2. Arc rating check
    if spec.arc_rating is not None:
        if spec.arc_rating.accessibility != PORTFOLIO_BASELINE["standard_arc_accessibility"]:
            deviations.append({
                "field": "arc_rating.accessibility",
                "detail": (
                    f"Requested {spec.arc_rating.accessibility} vs. standard "
                    f"{PORTFOLIO_BASELINE['standard_arc_accessibility']}"
                ),
                "severity": "medium",
            })
        # else: Type 2B is standard -> no deviation

    # 3. Delivery timeline check
    if rfp_timeline_weeks is not None:
        standard_weeks = PORTFOLIO_BASELINE["standard_delivery_weeks"]
        if rfp_timeline_weeks < standard_weeks:
            shortfall = standard_weeks - rfp_timeline_weeks
            severity = "high" if shortfall > 12 else "medium" if shortfall > 4 else "low"
            deviations.append({
                "field": "delivery_timeline",
                "detail": (
                    f"RFP requires delivery in {rfp_timeline_weeks} weeks vs. "
                    f"standard {standard_weeks}-week lead time (short by {shortfall} weeks)"
                ),
                "severity": severity,
            })

    # 4. Custom requirements (busbar material/thickness deviating from standard copper)
    if spec.busbar_material and spec.busbar_material.lower() != "copper":
        deviations.append({
            "field": "busbar_material",
            "detail": f"Non-standard busbar material requested: {spec.busbar_material}",
            "severity": "low",
        })

    # --- Aggregate severity ---
    if deviations:
        max_severity = max(deviations, key=lambda d: _severity_rank(d["severity"]))["severity"]
    else:
        max_severity = "low"

    # --- Margin estimate ---
    margin = BASELINE_MARGIN
    for d in deviations:
        margin -= MARGIN_PENALTY_PER_DEVIATION.get(d["severity"], 0.0)
    margin = max(margin, 0.0)

    # --- Recommendation logic ---
    if max_severity == "high" or margin < 0.13:
        recommendation = "NO_BID"
        confidence = 0.85
        reasoning = (
            "One or more high-severity deviations were detected (or margin has "
            "fallen below the acceptable floor), indicating significant risk or "
            "portfolio mismatch. Recommend NO_BID."
        )
    elif max_severity == "medium":
        recommendation = "HOLD"
        confidence = 0.80
        reasoning = (
            "Medium-severity deviations were detected. The spec is largely "
            "compatible with the standard portfolio, but timeline or rating "
            "deviations warrant engineering review before committing to a bid. "
            "Recommend HOLD pending clarification."
        )
    else:
        recommendation = "BID"
        confidence = 0.92 if not deviations else 0.85
        reasoning = (
            "Specification aligns with Critical Power Products' standard "
            "15kV/600A metal-clad portfolio with no more than low-severity "
            "deviations. Recommend BID at estimated margin."
        )

    return {
        "scenario": spec.scenario_type or "unknown_scenario",
        "recommendation": recommendation,
        "confidence": round(confidence, 2),
        "margin_estimate": round(margin, 3),
        "deviations_detected": deviations,
        "reasoning": reasoning,
    }


if __name__ == "__main__":
    import json
    from logic.extraction import load_scenario, extract_specification

    raw = load_scenario("data/scenario_1_utility_bid.json")
    spec = extract_specification(raw, scenario_type="scenario_1_utility_bid")

    # RFP required delivery: derive weeks from raw data (required_by - issue_date approx)
    # Scenario 1 test data: bid_due 2026-10-30, required_by 2027-06-30 -> ~35 weeks from due date
    rfp_timeline_weeks = raw.get("delivery_timeline", {}).get("lead_time_weeks", 32)

    result = bid_recommendation(spec, rfp_timeline_weeks=rfp_timeline_weeks)
    print(json.dumps(result, indent=2))
