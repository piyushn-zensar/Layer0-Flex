"""
Stage 3 — Multi-Stage Validation.

Deliberately split in two, on purpose:

1. `_evaluate_deterministic_rules` — hard engineering constraints
   (voltage consistency, cooling capacity thresholds, redundancy
   requirements) are evaluated by plain Python against
   engineering_rules.json. These are facts, not judgment calls, and
   should never depend on a model's mood. This runs identically
   whether LLM_MODE is "mock" or "llama_cpp".

2. `run()` — takes the deterministic results and asks the model (or,
   in mock mode, a deterministic heuristic) to synthesize a plain-
   English confidence assessment per layer, flagging anything that
   looks genuinely novel or under-specified for human escalation.
   This is the one place judgment is appropriate — deciding whether
   something is "normal" or "worth a second look" is not a hard rule.

This mirrors the CPQ principle from the ETO/CPQ design: rules handle
the repeatable, deterministic share; the model (or a human) handles
the remainder.
"""
from agents.base_agent import call_llm_json
from rag.retriever import get_full_rules


def _evaluate_deterministic_rules(req: dict, layers: list, rules: dict) -> list:
    checks = []

    # Completeness (carried forward from Stage 1)
    completeness_score = req.get("completeness_score", 0)
    checks.append({
        "id": "completeness",
        "status": "pass" if completeness_score >= 80 else ("warn" if completeness_score >= 50 else "fail"),
        "note": f"Requirement completeness score: {completeness_score}%.",
    })

    # R-001: 800VDC consistency across the power path (layers 1, 3, 4)
    # NOTE: an ABSENT voltage_arch is not the same as a known-safe standard
    # architecture. Treating unknown as "pass" would let a spec that was
    # never provided read as validated — see R-002 note below.
    voltage_raw = req.get("voltage_arch")
    voltage = (voltage_raw or "").upper()
    power_path = {l["n"]: l for l in layers if l["n"] in (1, 3, 4)}
    mentions_800 = ["800" in power_path.get(n, {}).get("spec", "") for n in (1, 4)]
    if not voltage_raw:
        status = "warn"
        note = "Voltage architecture was not specified in the RFP — cannot verify power-path consistency. Requires clarification before quoting."
    elif "800" in voltage:
        status = "pass" if all(mentions_800) else "fail"
        note = "800VDC architecture is consistent across Layers 1 and 4." if status == "pass" \
            else "RFP specifies 800VDC but not all power-path layers reflect it — R-001 violation."
    else:
        status = "pass"
        note = f"Voltage architecture ({voltage_raw}) does not require 800VDC power-path verification."
    checks.append({"id": "R-001_voltage_consistency", "status": status, "note": note})

    # R-002: cooling threshold for high rack density
    # An unknown rack density MUST NOT silently coerce to 0 and then "pass"
    # the 100kW threshold — that would report a validated cooling design for
    # a spec that was never given. Unknown is flagged, not passed.
    density_raw = req.get("rack_density_kw")
    layer5 = next((l for l in layers if l["n"] == 5), {})
    if density_raw is None:
        status = "warn"
        note = "Rack density was not specified in the RFP — cooling adequacy cannot be verified. Requires clarification before quoting."
    elif density_raw >= 100:
        status = "pass" if "direct-to-chip" in layer5.get("spec", "").lower() or "direct-to-chip" in layer5.get("brand", "").lower() else "fail"
        note = f"Rack density {density_raw}kW requires direct-to-chip cooling — {'confirmed' if status=='pass' else 'NOT confirmed in Layer 5 selection'}."
    else:
        status = "pass"
        note = f"Rack density {density_raw}kW is below the 100kW direct-to-chip mandate."
    checks.append({"id": "R-002_cooling_threshold", "status": status, "note": note})

    # R-003: 2N redundancy needs utility-grade brand at Layer 2
    redundancy_raw = req.get("redundancy")
    redundancy = (redundancy_raw or "").upper()
    layer2 = next((l for l in layers if l["n"] == 2), {})
    if not redundancy_raw:
        status = "warn"
        note = "Redundancy class was not specified in the RFP — cannot verify Layer 2 selection is appropriate. Requires clarification before quoting."
    elif "2N" in redundancy:
        status = "pass" if any(b in layer2.get("brand", "") for b in ("EP2", "Crown")) else "warn"
        note = "2N redundancy is matched with a utility-grade Layer 2 brand." if status == "pass" \
            else "2N redundancy specified, but Layer 2 selection may not be utility-grade — review recommended."
    else:
        status = "pass"
        note = f"Redundancy class ({redundancy_raw}) does not require a utility-grade Layer 2 brand."
    checks.append({"id": "R-003_redundancy_match", "status": status, "note": note})

    # R-004: EPC Power pending-close dependency
    depends_on_epc = any("EPC Power" in l.get("brand", "") for l in layers)
    checks.append({
        "id": "R-004_epc_power_dependency",
        "status": "warn" if depends_on_epc else "pass",
        "note": "Design depends on EPC Power, a pending acquisition — flag as a supply-timeline dependency."
        if depends_on_epc else "Design does not depend on EPC Power.",
    })

    # cost/margin note
    brand_families = set()
    for l in layers:
        for token in l.get("brand", "").split(" + "):
            brand_families.add(token.split(" (")[0].strip())
    checks.append({
        "id": "cost_margin",
        "status": "pass",
        "note": f"Design spans {len(brand_families)} brand families. "
                f"{'Multi-brand combination — expect higher integration cost, higher margin per historical bundling patterns.' if len(brand_families) > 2 else 'Single/dual-brand — standard cost profile.'} "
                f"{'EPC Power dependency should carry a schedule contingency.' if depends_on_epc else ''}".strip(),
    })

    return checks


def _build_confidence_prompt(req: dict, layers: list, checks: list) -> str:
    return f"""You are the confidence-flagging step of a validation pipeline. Given the requirements, the drafted layer design, and the deterministic rule check results below, assess per-layer confidence and flag anything genuinely novel or under-specified for human escalation. Do not re-check the deterministic rules — assume they are correct. Focus on judgment: is this a routine, well-precedented configuration, or something unusual that a human should look at more closely?

Requirements: {req}
Layers: {layers}
Deterministic checks: {checks}

Respond with ONLY compact JSON, no markdown fences, no commentary, matching exactly this shape:
{{"confidence": [{{"n": 1, "level": "high|medium|low", "flag": "<short reason or empty string>"}}, ... one entry per layer n=1 to 6], "overall_summary": "<2-3 sentence plain-English summary of the validation result for a human approver>"}}"""


def _mock_confidence(req: dict, layers: list, checks: list) -> dict:
    confidence = []
    for l in layers:
        brand = l.get("brand", "")
        if "flagged for engineering review" in brand.lower() or "pending close" in brand.lower():
            level, flag = "low", f"Layer {l['n']} selection depends on an unconfirmed or pending element — needs human review."
        elif "warn" in [c["status"] for c in checks if str(l["n"]) in c.get("note", "") or c["id"].startswith(f"R-00")]:
            level, flag = "medium", "Associated rule check returned a warning — worth a second look."
        else:
            level, flag = "high", ""
        confidence.append({"n": l["n"], "level": level, "flag": flag})

    fails = [c for c in checks if c["status"] == "fail"]
    warns = [c for c in checks if c["status"] == "warn"]
    if fails:
        summary = f"Validation found {len(fails)} failing check(s) that must be resolved before this design can proceed: {'; '.join(c['note'] for c in fails)}"
    elif warns:
        summary = f"Validation passed with {len(warns)} warning(s) worth engineering attention: {'; '.join(c['note'] for c in warns)}"
    else:
        summary = "All deterministic checks passed. This is a well-precedented configuration with no flags."
    return {"confidence": confidence, "overall_summary": summary}


def run(req: dict, layers: list) -> dict:
    rules = get_full_rules()
    checks = _evaluate_deterministic_rules(req, layers, rules)

    result = call_llm_json(
        _build_confidence_prompt(req, layers, checks),
        _mock_confidence, req, layers, checks,
    )
    result["checks"] = checks
    result["explanation"] = (
        f"Ran {len(checks)} deterministic engineering-rule checks against the draft design, then synthesized "
        f"per-layer confidence. {result['overall_summary']}"
    )
    result["evidence"] = [{"source": "engineering_rules.json", "checks_evaluated": [c['id'] for c in checks]}]
    return result
