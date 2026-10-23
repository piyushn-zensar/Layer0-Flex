"""Explain a component's configurator result (P-56; C-57, C-58, C-61; PLAN 12.2 decision 7). Code only, no model.

    explain(group, cat, parts) -> {"outcome", "reason", "requirements", "candidates", "near_matches", "assumptions",
                                   "checks", "inputs", "missing", "unit_issues", "system"}

Outcomes: match (every stated constraint met), near_match (fails one constraint; shown for review, never as a match),
insufficient_information (a needed input is not stated), no_match (with the reason), and for the other kinds
system_checks (the installation checks ran), not_applicable, not_assessed (no product table for the component).
Per requirement: satisfied, not_satisfied, cannot_assess, each with the reason. Nothing is relaxed silently: a near
match names the constraint it fails.
"""
from urllib.parse import quote

import pandas as pd

from app.modules.configurator import rfp_configurator as rc

OUTCOMES = {"match": "Match", "near_match": "Near match", "insufficient_information": "Insufficient information",
            "no_match": "No match", "system_checks": "System checks", "not_applicable": "Not applicable",
            "not_assessed": "Not assessed by the configurator"}

FILTER = {"input_v_min": "input_range", "input_v_max": "input_range", "output_v_min": "output_voltage",
          "output_v_max": "output_voltage", "output_power_w": "capacity_and_paralleling",
          "output_current_a": "capacity_and_paralleling", "peak_power_w": "capacity_and_paralleling",
          "redundancy": "capacity_and_paralleling", "design_margin_pct": "capacity_and_paralleling",
          "isolation": "isolation", "isolation_v_min": "isolation", "regulation": "regulation",
          "digital": "digital_interface", "applications": "application", "package_types": "package_type",
          "footprints": "footprint", "mountings": "mounting", "max_length_mm": "max_length",
          "max_width_mm": "max_width", "max_height_mm": "max_height", "min_efficiency_pct": "efficiency"}
LABEL = {"input_range": "input voltage range", "output_voltage": "output voltage",
         "capacity_and_paralleling": "power or current (with paralleling)", "isolation": "isolation",
         "regulation": "regulation", "digital_interface": "digital interface", "application": "application",
         "package_type": "package type", "footprint": "footprint", "mounting": "mounting", "max_length": "length",
         "max_width": "width", "max_height": "height", "efficiency": "efficiency"}
# system field -> the configure_system checks that use it
CHECKS = {"total_it_load_mw": ("module count", "CDU sizing"), "rack_density_kw": ("rack density",),
          "distribution_voltage": ("distribution voltage", "RPP voltage"),
          "coolant_supply_temp_c": ("coolant supply temperature",), "redundancy": ("redundancy",),
          "cooling_mode": ("CDU sizing", "cooling mode"), "liquid_capture_fraction": ("CDU sizing",)}
WORST = {"fail": 0, "unknown": 1, "review": 2, "pass": 3}
STATUS = {"pass": "satisfied", "fail": "not_satisfied"}


def _req(r: dict, status: str, why: str, fields: list[str] = (), inputs: dict | None = None) -> dict:
    """inputs: the run's provenance; a value the model interpreted (a category, not the RFP's words) is said."""
    guessed = [k.split(".", 1)[1] for k, v in (inputs or {}).items() if v.get("interpreted") and r["req_id"] in v["req_ids"]]
    if guessed:
        why += f" Interpreted from the text, to confirm: {', '.join(guessed)}."
    return {"req_id": r["req_id"], "text": r["text"], "document": r.get("document"), "page": r.get("page"),
            "status": status, "why": why, "fields": list(fields), "interpreted": guessed}


def _fields(inputs: dict) -> dict[str, list[str]]:
    """req_id -> the configurator fields it stated (board.x / system.x without the scope)."""
    out: dict[str, list[str]] = {}
    for key, p in inputs.items():
        for rid in p["req_ids"]:
            out.setdefault(rid, []).append(key.split(".", 1)[1])
    return out


def _stated(inputs: dict, fields: list[str], scope: str) -> str:
    return ", ".join(str(inputs[f"{scope}.{f}"]["stated"]) for f in fields if f"{scope}.{f}" in inputs)


def _alone(cat: pd.DataFrame, values: dict) -> rc.MatchResult:
    """The board match on one requirement's own values: does any part meet that requirement by itself?"""
    _, board, _, _ = rc.parse_requirements({"board": values})
    return rc.match_components(cat, board)


def _candidate(c: dict, parts: dict) -> dict:
    p = parts.get(c["part_number"], {})
    return c | {"link": "/catalog/product?part=" + quote(c["part_number"], safe=""), "family_key": p.get("family_key"),
                "series": p.get("series"), "verified": p.get("verified", False), "conflicts": p.get("conflicts", []),
                "multi_output": bool(p.get("multi_output")) or bool(p.get("outputs"))}


def _board(group: dict, cat: pd.DataFrame, parts: dict) -> dict:
    run, refs = group["run"], group["requirements"]
    b, inputs, missing = run["board"], run["inputs"], run["missing"]
    cands = [_candidate(c, parts) for c in b["candidates"]]
    near = [_candidate(c, parts) for c in b["near_misses"]]
    relax = b["relaxation"]
    best = max(relax, key=relax.get) if relax else None
    needs = "; ".join(m["needed_for"] for m in missing)
    if b["status"] in ("no_constraints", "invalid_requirements"):
        outcome = "insufficient_information"
        reason = ("The requirements state no DC/DC value the configurator can use." if b["status"] == "no_constraints"
                  else "The stated values are not valid configurator input: " + "; ".join(i["message"] for i in b["issues"]))
    elif b["status"] == "ok" and missing:
        outcome = "insufficient_information"
        reason = (f"Not stated in the RFP: {needs}. {len(cands)} parts meet the stated constraints; they are possible "
                  "candidates, not a recommendation, until the missing inputs are known.")
    elif b["status"] == "ok":
        outcome = "match"
        reason = f"{len(cands)} power modules meet every stated constraint (best first: fewest modules, efficiency, size)."
    elif near:
        outcome = "near_match"
        reason = (f"No part meets every stated constraint. Without the {LABEL.get(best, best)} constraint, {relax[best]} "
                  f"parts would; the closest are shown for review. They fail the {LABEL.get(best, best)} and are not a match.")
    else:
        outcome = "no_match"
        stops = next((f["stage"] for f in b["funnel"][1:] if f["remaining"] == 0), None)
        reason = (f"No catalogue power module meets the stated constraints, and dropping any one constraint does not "
                  f"help. First constraint that no part meets: {LABEL.get(stops, stops)}.")
        reason += "".join(" " + n for n in b["notes"] if "upstream conversion" in n)

    per_req, fields = [], _fields(inputs)
    for r in refs:
        fs = fields.get(r["req_id"], [])
        if not fs:
            per_req.append(_req(r, "cannot_assess", "Not a configurator input; for engineering review."))
            continue
        said = _stated(inputs, fs, "board")
        if outcome == "match" or (outcome == "insufficient_information" and cands):
            per_req.append(_req(r, "satisfied", f"Met by the {len(cands)} listed parts ({said}).", fs, inputs))
        elif outcome == "near_match":
            failing = [f for f in fs if FILTER.get(f) == best]
            per_req.append(_req(r, "not_satisfied", f"The near-match parts fail the {LABEL[best]} ({said}).", fs, inputs)
                           if failing else _req(r, "satisfied", f"Met by the near-match parts ({said}).", fs, inputs))
        elif outcome == "insufficient_information":
            per_req.append(_req(r, "cannot_assess", f"Stated ({said}), but the group lacks: {needs}.", fs, inputs))
        else:
            values = {f: run["input"]["board"][f]["value"] for f in fs if f in run["input"]["board"]}
            alone = _alone(cat, values)
            if alone.status == "ok":
                per_req.append(_req(r, "cannot_assess", f"{len(alone.candidates)} parts meet this requirement on its own "
                                    f"({said}), but no part meets every constraint of the component together.", fs,
                                    inputs))
            else:
                stops = next((f["stage"] for f in alone.funnel[1:] if f["remaining"] == 0), None)
                said = _stated(inputs, [f for f in fs if FILTER.get(f) == stops], "board") or said
                per_req.append(_req(r, "not_satisfied", f"No catalogue power module meets the {LABEL.get(stops, stops)} "
                                    f"({said}).", fs, inputs))

    stated = {k.split(".", 1)[1] for k in inputs}
    assumptions = [
        {"item": "Redundancy", "value": run["parsed"]["board"]["redundancy"],
         "basis": "stated in the RFP" if "redundancy" in stated else "configurator default, not in the RFP"},
        {"item": "Design margin", "value": f"{run['parsed']['board']['design_margin_pct']:.0f}%",
         "basis": "stated in the RFP" if "design_margin_pct" in stated else "configurator default, not in the RFP"},
        {"item": "Maximum modules in parallel", "value": str(run["parsed"]["board"]["max_parallel_modules"]),
         "basis": "configurator assumption; each datasheet sets the real limit"},
        {"item": "Module count", "value": "per candidate",
         "basis": "arithmetic from the per-module rating at datasheet conditions; not a design"},
    ]
    shown = cands or near
    checks = []
    if shown:
        if any(c["regulation"] == "Unregulated/Fixed Ratio" for c in shown):
            checks.append(("Fixed-ratio output", "open", "Some candidates are unregulated (output tracks input): confirm "
                                                         "the conversion ratio at the RFP's bus voltage and its tolerance."))
        if any((c["modules_total"] or 0) > 1 for c in shown):
            checks.append(("Parallel operation", "open", "Some candidates need modules in parallel: confirm the maximum "
                                                         "parallel count and current-sharing rules in each datasheet."))
        checks.append(("Thermal derating", "open", "Ratings are per module at datasheet conditions: confirm derating at "
                                                   "the RFP's ambient, airflow or cold-plate conditions."))
        if "peak_power_w" in stated or any(c["peak_w_per_module"] for c in shown):
            checks.append(("Peak power conditions", "open", "Confirm the peak rating's duration and repetition against "
                                                            "the RFP's load profile."))
        checks.append(("Certification applicability", "open", "Confirm the modules' safety approvals cover the standards "
                                                              "the RFP names for this equipment."))
        flagged = sorted({c["part_number"] for c in shown if c["conflicts"]})
        checks.append(("Catalogue values unverified", "open", "Values are the Flex Power Modules export as imported, "
                       "not confirmed by the unit" + (f"; the web pages disagree for {', '.join(flagged)}" if flagged else "")
                       + "."))
    checks.append(("Multiple outputs", "not_supported", "The configurator matches the main output only; second and "
                                                        "third outputs are not checked."))
    checks += [("Unit or value issue", "open", f"{i['field']}: {i['message']}") for i in run["unit_issues"]]
    return {"outcome": outcome, "reason": reason, "requirements": per_req, "candidates": cands,
            "near_matches": near if outcome == "near_match" else [], "assumptions": assumptions,
            "checks": [{"check": c, "status": s, "detail": d} for c, s, d in checks],
            "inputs": inputs, "missing": missing, "unit_issues": run["unit_issues"], "notes": b["notes"],
            "funnel": b["funnel"], "relaxation": relax}


def _system(group: dict) -> dict:
    run, refs = group["run"], group["requirements"]
    inputs = run["inputs"]
    if run["status"] == "not_applicable":
        return {"outcome": "not_applicable", "reason": run["reason"], "inputs": inputs, "missing": [],
                "requirements": [_req(r, "cannot_assess", "System checks do not apply to this RFP.") for r in refs],
                "assumptions": [], "checks": []}
    s = run["system"]
    by_item = {c["item"]: c for c in s["checks"]}
    per_req, fields = [], _fields(inputs)
    for r in refs:
        fs = fields.get(r["req_id"], [])
        found = [by_item[i] for f in fs for i in CHECKS.get(f, ()) if i in by_item]
        certs = [c for c in s["certifications"] if "certifications" in fs]
        if not found and not certs:
            per_req.append(_req(r, "cannot_assess", "Not a configurator input; for engineering review." if not fs
                                else "The configurator has no check for this value.", fs))
            continue
        worst = min((c["status"] for c in found), key=WORST.get, default="pass")
        if any(c["found_in"] is None for c in certs):
            worst = min(worst, "fail", key=WORST.get)
        detail = "; ".join(f"{c['item']}: {c['detail']}" for c in found) + "".join(
            f"; {c['requested']}: {c['status']}" for c in certs)
        per_req.append(_req(r, STATUS.get(worst, "cannot_assess"), detail.strip("; "), fs, inputs))
    assumptions = [{"item": "Assumption", "value": a, "basis": "configurator"} for a in s["assumptions"]]
    assumptions += [{"item": k.replace("_", " "), "value": str(v["value"]), "basis": v["source"] + ("" if v["verified"]
                     else "; not confirmed by Axiom")} for k, v in s["axiom_spec_used"].items()]
    counts = {k: sum(c["status"] == k for c in s["checks"]) for k in WORST}
    reason = (f"Installation checks: {counts['pass']} pass, {counts['fail']} fail, {counts['review']} to review, "
              f"{counts['unknown']} unknown. Configurator result, pending engineering review.")
    if s["gaps"]:
        reason += " Gaps: " + "; ".join(s["gaps"]) + "."
    return {"outcome": "system_checks", "reason": reason, "requirements": per_req, "inputs": inputs,
            "missing": run["missing"], "assumptions": assumptions,
            "checks": [{"check": c["item"], "status": c["status"], "detail": c["detail"]} for c in s["checks"]],
            "cdu_options": s["cdu_options"], "certifications": s["certifications"], "counts": counts}


def explain(group: dict, cat: pd.DataFrame, parts: dict) -> dict:
    """group: one entry of service.plan()["groups"] with its requirement refs ("requirements")."""
    if group["kind"] == "dc_dc":
        return _board(group, cat, parts)
    if group["kind"] == "system":
        return _system(group)
    return {"outcome": "not_assessed", "reason": "No product table was supplied for this component, so the configurator "
            "does not assess it; the unit's engineers do.", "inputs": {}, "missing": [], "assumptions": [], "checks": [],
            "requirements": [_req(r, "cannot_assess", "Assessed by the unit's engineers.") for r in group["requirements"]]}
