"""
Module M13 — Deterministic Solver (LV power distribution).

Scope is deliberately narrow. This solves ONLY low-voltage power
distribution arithmetic where the governing rules are published and
public: circuit ampacity, continuous-load derating, load balance and
capacity headroom.

It does NOT attempt medium-voltage switchgear, thermal design, arc-flash
study, protection coordination, or anything else requiring engineering
judgment. For those it returns NOT_SOLVABLE with a reason. That refusal
is a first-class result, not an error: a system that produces a complete
answer for bespoke 15kV switchgear will be checked by an application
engineer within ninety seconds and found wrong.

No language model is involved. Every number is arithmetic, and every
rule carries its published reference so an engineer can verify it with
a calculator.

STANDARDS BASIS
---------------
All references below are to publicly published code values, carried in
knowledge_base/engineering_rules.json under `physical_rules` and tagged:

    [Standard NEC/IEC Reference - Subject to SpinCo Line-Specific
     Validation]

They are generic-standard values, NOT SpinCo line-specific engineering
limits. Before any production use, a SpinCo power engineer must confirm
which standards and derating practices each product line designs against.
"""
import math

from rag.retriever import get_full_rules


class SolveStatus:
    SOLVED = "SOLVED"
    SOLVED_WITH_WARNINGS = "SOLVED_WITH_WARNINGS"
    NOT_SOLVABLE = "NOT_SOLVABLE"


def _rules() -> dict:
    return get_full_rules().get("physical_rules", {})


def _step(label, expression, result, unit, reference):
    """One line of visible working, so the whole calculation can be
    checked by hand."""
    return {
        "step": label,
        "expression": expression,
        "result": round(result, 3) if isinstance(result, (int, float)) else result,
        "unit": unit,
        "reference": reference,
    }


# ---------------------------------------------------------------------
# Solvability gate
# ---------------------------------------------------------------------

def assess_solvability(layer: dict, tier: str, requirements: dict) -> dict:
    """Decides whether this layer can be solved arithmetically at all.

    The tier is necessary but not sufficient: a CTO_AUTOMATE layer whose
    inputs are missing still cannot be solved. Both conditions are
    reported separately so the reason is specific.
    """
    n = layer.get("n")
    reasons = []

    if tier != "CTO_AUTOMATE":
        reasons.append(
            f"Layer {n} is classified {tier}. Only CTO_AUTOMATE lines are solved "
            f"arithmetically; this requires engineering judgment."
        )

    # Solver covers LV distribution and rack power only (layers 3 and 4).
    if n not in (3, 4):
        reasons.append(
            f"Layer {n} ({layer.get('name')}) is outside the solver's scope. "
            f"This solver covers low-voltage distribution and rack power only."
        )

    voltage = str(requirements.get("voltage_arch") or "")
    if "kV" in voltage and "medium voltage" in voltage.lower():
        reasons.append(
            "Medium-voltage equipment is out of scope: MV switchgear requires "
            "protection coordination and arc-flash study, not arithmetic."
        )

    if reasons:
        return {"solvable": False, "reasons": reasons}
    return {"solvable": True, "reasons": []}


# ---------------------------------------------------------------------
# The solve
# ---------------------------------------------------------------------

def solve_lv_distribution(requirements: dict) -> dict:
    """Solves an LV power distribution scope: UPS capacity against rack
    count and branch circuit provision.

    Returns a full working, or NOT_SOLVABLE if inputs are absent. Missing
    inputs are never defaulted — a guessed input produces a confident
    wrong answer, which is worse than no answer.
    """
    r = _rules()
    pf = r.get("assumed_power_factor", {}).get("value", 1.0)
    pf_ref = r.get("assumed_power_factor", {}).get("reference", "assumption")
    derate = r.get("continuous_load_derating", {}).get("value", 0.8)
    derate_ref = r.get("continuous_load_derating", {}).get("reference", "NEC 210.20(A)")

    ups_kva = requirements.get("ups_kva")
    rack_count = requirements.get("rack_count")
    circuits = requirements.get("branch_circuits")
    circuit_v = requirements.get("branch_circuit_voltage")

    missing = [name for name, val in [
        ("ups_kva", ups_kva), ("rack_count", rack_count)] if val is None]
    if missing:
        return {
            "status": SolveStatus.NOT_SOLVABLE,
            "reasons": [f"Required input(s) absent from the RFP: {', '.join(missing)}. "
                        f"The solver does not assume values it was not given."],
            "working": [],
        }

    working = []
    warnings = []

    # 1. Usable UPS capacity after continuous-load derating
    usable_kva = ups_kva * derate
    working.append(_step(
        "Usable UPS capacity after continuous-load derating",
        f"{ups_kva} kVA x {derate}", usable_kva, "kVA", derate_ref))

    # 2. Real power available
    usable_kw = usable_kva * pf
    working.append(_step(
        "Real power available",
        f"{round(usable_kva,3)} kVA x PF {pf}", usable_kw, "kW", pf_ref))

    # 3. Capacity per rack
    per_rack_kw = usable_kw / rack_count
    working.append(_step(
        "Available capacity per rack",
        f"{round(usable_kw,3)} kW / {rack_count} racks", per_rack_kw, "kW/rack",
        "derived"))

    # 4. Branch circuit analysis, where the RFP stated circuits
    if circuits and circuit_v:
        amps_per_circuit = r.get("assumed_branch_circuit_amps", {}).get("value", 20)
        amps_ref = r.get("assumed_branch_circuit_amps", {}).get(
            "reference", "NEC 210.24 typical branch circuit rating")
        circuit_kw = (circuit_v * amps_per_circuit * derate) / 1000.0
        working.append(_step(
            "Derated capacity per branch circuit",
            f"({circuit_v} V x {amps_per_circuit} A x {derate}) / 1000",
            circuit_kw, "kW/circuit", f"{amps_ref}; derating {derate_ref}"))

        total_circuit_kw = circuit_kw * circuits
        working.append(_step(
            "Total branch circuit capacity",
            f"{round(circuit_kw,3)} kW x {circuits} circuits",
            total_circuit_kw, "kW", "derived"))

        circuits_per_rack = circuits / rack_count
        working.append(_step(
            "Branch circuits per rack",
            f"{circuits} / {rack_count}", circuits_per_rack, "circuits/rack",
            "derived"))

        # Consistency check: branch provision vs UPS capacity
        if total_circuit_kw < usable_kw * 0.95:
            warnings.append(
                f"Branch circuit provision ({round(total_circuit_kw,1)} kW) is below "
                f"derated UPS capacity ({round(usable_kw,1)} kW). The distribution "
                f"may constrain the UPS rather than the reverse \u2014 confirm intended "
                f"circuit ampacity, which the RFP did not state."
            )
        if circuits_per_rack < 2:
            warnings.append(
                f"{round(circuits_per_rack,1)} circuits per rack provides no A/B feed "
                f"redundancy. Confirm whether dual-corded loads are intended."
            )

    status = SolveStatus.SOLVED_WITH_WARNINGS if warnings else SolveStatus.SOLVED
    return {
        "status": status,
        "working": working,
        "warnings": warnings,
        "result": {
            "usable_capacity_kw": round(usable_kw, 2),
            "capacity_per_rack_kw": round(per_rack_kw, 2),
            "rack_count": rack_count,
            "branch_circuits": circuits,
        },
        "standards_note": ("[Standard NEC/IEC Reference \u2014 Subject to SpinCo "
                           "Line-Specific Validation] All derating and circuit "
                           "values are published generic-standard figures, not "
                           "SpinCo line-specific engineering limits."),
    }


def run(requirements: dict, layers: list, tiers: list) -> dict:
    """Attempts a solve per layer. Emits a result for every layer so the
    refusals are as visible as the solutions."""
    tier_by_n = {t["n"]: t["tier"] for t in tiers}
    results = []

    for layer in layers:
        n = layer["n"]
        tier = tier_by_n.get(n, "UNKNOWN")
        gate = assess_solvability(layer, tier, requirements)

        if not gate["solvable"]:
            results.append({
                "layer": n,
                "layer_name": layer["name"],
                "brand": layer.get("brand"),
                "tier": tier,
                "status": SolveStatus.NOT_SOLVABLE,
                "reasons": gate["reasons"],
                "routed_to": "engineering",
            })
            continue

        solved = solve_lv_distribution(requirements)
        results.append({
            "layer": n,
            "layer_name": layer["name"],
            "brand": layer.get("brand"),
            "tier": tier,
            **solved,
        })

    solved_n = sum(1 for r in results if r["status"] in
                   (SolveStatus.SOLVED, SolveStatus.SOLVED_WITH_WARNINGS))
    refused_n = sum(1 for r in results if r["status"] == SolveStatus.NOT_SOLVABLE)

    return {
        "results": results,
        "explanation": (
            f"Attempted arithmetic solve on {len(results)} layer(s): {solved_n} solved, "
            f"{refused_n} returned NOT_SOLVABLE and routed to engineering. Refusals are "
            f"expected outcomes, not failures \u2014 bespoke work is not solved arithmetically."
        ),
        "evidence": [{
            "source": "engineering_rules.json: physical_rules",
            "scope": "LV power distribution only (layers 3-4, CTO_AUTOMATE)",
        }],
    }
