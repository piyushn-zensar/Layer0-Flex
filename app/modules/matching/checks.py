"""Evidence checks for the bid decision (task A-06), ported from reference/v0.3.0. No model call, no DB.

    scope(reqs, kb)                  M3: which grid-to-chip layers the frozen requirements cover, with REQ citations
    facts(reqs)                      the few facts the rules need, each citing the requirement it came from
    tier_flags(reqs, matches, kb)    M4: offering type vs. the unit's default automation tier (fail-safe)
    rules(facts, in_scope, matches, kb, eng)   M5: rules R-001..R-004 of engineering_rules.json
    solve(facts, in_scope, eng)      M13: low-voltage power arithmetic, or NOT_SOLVABLE with the reason

reqs = [{"req_id", "quote"}]; matches = {req_id: [{"bu", "product_id", "offering_type"}]} (Match.units).
Statuses: pass | warn | fail | n/a. A fact the RFP does not state is "warn", never "pass" (rule R5).
Facts are read from requirements the reader agent already identified; nothing here identifies requirements.
"""
import re

OFFERING_RANK = {"CTO": 0, "SEMI_CUSTOM": 1, "ETO": 2}
_NUMBER_WORDS = r"(?:(?:[a-z-]+\s+)?\((\d+)\)|\b(\d+))"  # "ten (10)" or "10"


def scope(reqs: list[dict], kb: dict) -> dict:
    """M3. A layer is in scope on weight of evidence: enough hits, several distinct terms, or one decisive term."""
    s = kb["scope"]
    layers, in_scope = [], []
    for layer in kb["layers"]:
        terms = []
        for kw in layer["keywords"]:
            ids = [r["req_id"] for r in reqs if kw in r["quote"].lower()]
            if ids:
                terms.append({"term": kw, "count": sum(r["quote"].lower().count(kw) for r in reqs), "req_ids": ids[:3]})
        hits, decisive = sum(t["count"] for t in terms), [t["term"] for t in terms if t["term"] in s["decisive_terms"]]
        yes = hits >= s["min_hits"] or len(terms) >= s["min_distinct_terms"] or bool(decisive)
        basis = ("decisive term" if decisive else f"{len(terms)} distinct terms" if len(terms) >= s["min_distinct_terms"]
                 else f"{hits} hits (threshold {s['min_hits']})")
        layers.append({"n": layer["n"], "name": layer["name"], "units": layer["units"], "in_scope": yes,
                       "basis": basis, "terms": sorted(terms, key=lambda t: -t["count"])[:5]})
        if yes:
            in_scope.append(layer["n"])
    if not in_scope:  # as v0.3.0: no evidence at all is not evidence of a narrow scope
        in_scope = [layer["n"] for layer in layers]
        for layer in layers:
            layer["in_scope"], layer["basis"] = True, "no layer met the threshold; full scope assumed"
    return {"in_scope": in_scope, "layers": layers}


def _first(reqs: list[dict], pattern: str, *, needs: tuple = ()) -> tuple | None:
    for r in reqs:
        q = r["quote"].lower()
        m = re.search(pattern, q)
        if m and all(n in q for n in needs):
            return m, r["req_id"]
    return None


def _num(m) -> float:
    return float(next(g for g in m.groups() if g))


def facts(reqs: list[dict]) -> dict:
    """Each fact is {"value", "req_id"} or None when the requirements don't state it."""
    out = {}
    hit = _first(reqs, r"\b800\s*-?\s*v\s*-?\s*dc\b|\b800vdc\b")
    out["vdc_800"] = {"value": True, "req_id": hit[1]} if hit else None
    hit = _first(reqs, r"\b\d+\s*-?\s*v\s*-?\s*(?:ac|dc)\b|\b\d+v(?:ac|dc)\b")
    out["voltage_stated"] = {"value": hit[0].group(0), "req_id": hit[1]} if hit else None
    densities = [(float(m.group(1)), r["req_id"]) for r in reqs
                 for m in re.finditer(r"(\d+(?:\.\d+)?)\s*kw\s*(?:per|/|a)\s*rack", r["quote"].lower())]
    out["rack_density_kw"] = {"value": max(densities)[0], "req_id": max(densities)[1]} if densities else None
    hit = _first(reqs, r"\b2n\b", needs=("utility",)) or _first(reqs, r"\b2n\b", needs=("substation",))
    out["redundancy_2n_utility"] = {"value": True, "req_id": hit[1]} if hit else None
    hit = _first(reqs, r"(\d+(?:\.\d+)?)\s*-?\s*kva\b", needs=("ups",))
    out["ups_kva"] = {"value": _num(hit[0]), "req_id": hit[1]} if hit else None
    hit = _first(reqs, _NUMBER_WORDS + r"\s*(?:data center\s+)?(?:equipment\s+)?racks\b")
    out["rack_count"] = {"value": int(_num(hit[0])), "req_id": hit[1]} if hit else None
    hit = _first(reqs, _NUMBER_WORDS + r"\s*(\d+)\s*v\s+(?:power whips|branch circuits)")
    out["branch_circuits"] = ({"value": int(hit[0].group(1) or hit[0].group(2)), "volts": int(hit[0].group(3)),
                               "req_id": hit[1]} if hit else None)
    hit = _first(reqs, r"medium[ -]voltage|\b\d+(?:\.\d+)?\s*kv\b")
    out["medium_voltage"] = {"value": True, "req_id": hit[1]} if hit else None
    return out


def tier_flags(reqs: list[dict], matches: dict, kb: dict) -> list[dict]:
    """M4 fail-safe. Most conservative wins: an offering type below the unit's default tier needs an engineer;
    a component keyword may only SUGGEST a lower tier (held for a person), but raises it at once."""
    quote = {r["req_id"]: r["quote"].lower() for r in reqs}
    layers_of = {u: {l["n"] for l in kb["layers"] if u in l["units"]} for u in kb["unit_tiers"]}
    floor = kb["tier_offering_floor"]
    rank = {t: i for i, t in enumerate(kb["tier_order"])}
    flags = []
    for req_id, units in matches.items():
        for u in units:
            default = kb["unit_tiers"].get(u["bu"], {}).get("tier")
            if not default:
                continue
            if OFFERING_RANK[u["offering_type"]] < OFFERING_RANK[floor[default]]:
                flags.append({"req_id": req_id, "bu": u["bu"], "product_id": u["product_id"], "kind": "below_default",
                              "note": f"{u['offering_type']} is below {u['bu']}'s default {default}: an engineer must "
                                      f"confirm this part is genuinely standard."})
            for o in kb["component_overrides"]:
                if o["keyword"] in quote.get(req_id, "") and layers_of[u["bu"]] & set(o["applies_to_layers"]):
                    up = rank[o["override_tier"]] > rank[default]
                    flags.append({"req_id": req_id, "bu": u["bu"], "product_id": u["product_id"],
                                  "kind": "raise" if up else "suggest_lower",
                                  "note": (f"'{o['keyword']}': treat as {o['override_tier']} ({o['reason']})" if up else
                                           f"'{o['keyword']}' suggests {o['override_tier']}; held at {default} until an "
                                           f"engineer confirms ({o['reason']})")})
    return flags


def rules(facts: dict, in_scope: list[int], matches: dict, kb: dict, eng: dict) -> list[dict]:
    """M5: R-001..R-004 (engineering_rules.json), adapted to scope: a rule about layers not in scope is n/a."""
    units = {u["bu"] for us in matches.values() for u in us}
    products = {u["product_id"] for us in matches.values() for u in us}
    text = {c["id"]: c["rule"] for c in eng["per_layer_constraints"]}
    cite = lambda f: f" ({f['req_id']})" if f else ""
    out = []

    if facts["vdc_800"]:  # a stated fact makes the rule apply, whatever the scope
        status, note = "warn", (f"800 V DC is required{cite(facts['vdc_800'])}: confirm every power-path product is "
                                f"800 V DC-compatible; the catalog holds no voltage ratings to check against.")
    elif not {1, 3, 4} & set(in_scope):
        status, note = "n/a", "No power-path layer (1, 3, 4) is in scope and 800 V DC is not stated."
    elif facts["voltage_stated"]:
        status, note = "pass", f"Voltage architecture {facts['voltage_stated']['value']}{cite(facts['voltage_stated'])} needs no 800 V DC check."
    else:
        status, note = "warn", "Voltage architecture is not stated: power-path consistency cannot be verified. Clarify before quoting."
    out.append({"id": "R-001", "rule": text["R-001"], "status": status, "note": note})

    d = facts["rack_density_kw"]
    if d and d["value"] >= 100:
        ok = "JETCOOL-PLATE" in products
        status, note = ("pass" if ok else "fail"), (f"{d['value']:g} kW per rack{cite(d)} needs direct-to-chip cooling: "
                                                    f"{'matched (JETCOOL-PLATE)' if ok else 'NOT among the matched products'}.")
    elif d:
        status, note = "pass", f"{d['value']:g} kW per rack{cite(d)} is below the 100 kW direct-to-chip threshold."
    elif 5 in in_scope:
        status, note = "warn", "Rack density is not stated: cooling adequacy cannot be verified. Clarify before quoting."
    else:
        status, note = "n/a", "Cooling (layer 5) is not in scope and no rack density is stated."
    out.append({"id": "R-002", "rule": text["R-002"], "status": status, "note": note})

    if facts["redundancy_2n_utility"]:
        ok = bool({"EP2", "CROWN"} & units)
        status, note = ("pass" if ok else "warn"), (f"2N at utility level{cite(facts['redundancy_2n_utility'])}: "
                                                    f"{'a utility-grade unit (EP2 or Crown) is matched' if ok else 'no EP2 or Crown match; review'}.")
    elif 2 not in in_scope:
        status, note = "n/a", "Utility / facility electrical (layer 2) is not in scope and no 2N redundancy is stated."
    else:
        status, note = "warn", "Redundancy class is not stated: the layer-2 selection cannot be verified. Clarify before quoting."
    out.append({"id": "R-003", "rule": text["R-003"], "status": status, "note": note})

    epc = "EPC" in units
    out.append({"id": "R-004", "rule": text["R-004"], "status": "warn" if epc else "pass",
                "note": "A match depends on EPC Power, a pending acquisition: flag the supply-timeline risk." if epc
                        else "No match depends on EPC Power."})
    return out


def solve(facts: dict, in_scope: list[int], eng: dict) -> dict:
    """M13: low-voltage distribution arithmetic (UPS capacity per rack, branch circuits), every step with its reference.
    Refusing is a first-class result: medium-voltage and bespoke work is not solved arithmetically."""
    reasons = []
    if not {3, 4} & set(in_scope):
        reasons.append("Low-voltage distribution and rack power (layers 3, 4) are not in scope.")
    if facts["medium_voltage"] and 2 in in_scope:
        reasons.append(f"Medium-voltage equipment ({facts['medium_voltage']['req_id']}) needs protection coordination "
                       f"and an arc-flash study, not arithmetic.")
    missing = [k for k in ("ups_kva", "rack_count") if not facts[k]]
    if not reasons and missing:
        reasons.append(f"Required input(s) not stated: {', '.join(missing)}. The solver does not assume values.")
    if reasons:
        return {"status": "NOT_SOLVABLE", "reasons": reasons, "working": [], "warnings": []}

    r = eng["physical_rules"]
    derate, pf, amps = (r["continuous_load_derating"], r["assumed_power_factor"], r["assumed_branch_circuit_amps"])
    kva, racks = facts["ups_kva"]["value"], facts["rack_count"]["value"]
    step = lambda label, expr, value, unit, ref: {"step": label, "expression": expr, "result": round(value, 3),
                                                  "unit": unit, "reference": ref}
    usable_kva = kva * derate["value"]
    usable_kw = usable_kva * pf["value"]
    working = [step("Usable UPS capacity after continuous-load derating", f"{kva:g} kVA x {derate['value']}", usable_kva, "kVA", derate["reference"]),
               step("Real power available", f"{usable_kva:g} kVA x PF {pf['value']}", usable_kw, "kW", pf["reference"]),
               step("Available capacity per rack", f"{usable_kw:g} kW / {racks} racks", usable_kw / racks, "kW/rack", "derived")]
    warnings = []
    bc = facts["branch_circuits"]
    if bc:
        circuit_kw = bc["volts"] * amps["value"] * derate["value"] / 1000
        working += [step("Derated capacity per branch circuit", f"({bc['volts']} V x {amps['value']} A x {derate['value']}) / 1000",
                         circuit_kw, "kW/circuit", f"{amps['reference']}; derating {derate['reference']}"),
                    step("Total branch circuit capacity", f"{circuit_kw:g} kW x {bc['value']} circuits", circuit_kw * bc["value"], "kW", "derived"),
                    step("Branch circuits per rack", f"{bc['value']} / {racks}", bc["value"] / racks, "circuits/rack", "derived")]
        if circuit_kw * bc["value"] < usable_kw * 0.95:
            warnings.append(f"Branch circuit provision ({circuit_kw * bc['value']:.1f} kW) is below derated UPS capacity "
                            f"({usable_kw:.1f} kW): confirm the intended circuit ampacity, which the RFP does not state.")
        if bc["value"] / racks < 2:
            warnings.append(f"{bc['value'] / racks:.1f} circuits per rack gives no A/B feed redundancy: confirm whether "
                            f"dual-corded loads are intended.")
    return {"status": "SOLVED_WITH_WARNINGS" if warnings else "SOLVED", "reasons": [], "working": working,
            "warnings": warnings, "inputs": {k: facts[k] for k in ("ups_kva", "rack_count", "branch_circuits")},
            "standards_note": r["_note"] if "_note" in r else "Generic NEC/IEC values, subject to SpinCo line-specific validation."}


if __name__ == "__main__":  # self-check: python -m app.modules.matching.checks
    import json
    from app.core import config
    kb = json.loads((config.KB / "spinco_layers.json").read_text("utf-8"))
    eng = json.loads((config.KB / "engineering_rules.json").read_text("utf-8"))
    R = lambda *qs: [{"req_id": f"REQ-0001-{i:04d}", "quote": q} for i, q in enumerate(qs, 1)]

    syracuse = R("One (1) 15kV two (2) section Metal Clad Switchgear lineup.", "Protective Relays and Controls.",
                 "Switchgear shall be Arc-resistant Type 2B.", "Proposals must be received via email no later than 09/15/2023.")
    s = scope(syracuse, kb)
    assert s["in_scope"] == [2], s["in_scope"]  # switchgear only; no stray cooling or rack layers
    f = facts(syracuse)
    assert f["medium_voltage"]["req_id"] == "REQ-0001-0001" and f["rack_density_kw"] is None
    ru = {r["id"]: r["status"] for r in rules(f, s["in_scope"], {"REQ-0001-0001": [{"bu": "CROWN", "product_id": "CROWN-ARMV", "offering_type": "ETO"}]}, kb, eng)}
    assert ru == {"R-001": "n/a", "R-002": "n/a", "R-003": "warn", "R-004": "pass"}, ru  # redundancy not stated = warn, never pass
    assert solve(f, s["in_scope"], eng)["status"] == "NOT_SOLVABLE"

    ups = R("UPS: 45-kVA online double-conversion UPS system", "Load served: ten (10) data center equipment racks",
            "Branch circuits: twenty-four (24) 208V power whips", "Rack power: rack-mounted PDUs",
            "Distribution: one dedicated power distribution cabinet")
    s = scope(ups, kb)
    assert {3, 4} <= set(s["in_scope"]) and 2 not in s["in_scope"], s["in_scope"]
    out = solve(facts(ups), s["in_scope"], eng)
    assert out["status"] == "SOLVED", out  # 79.9 kW of circuits > 32.4 kW usable; 2.4 circuits per rack allows A/B feeds
    assert [w["result"] for w in out["working"][:3]] == [36.0, 32.4, 3.24]  # 45 x 0.8; x 0.9; / 10 racks
    assert out["working"][3]["result"] == 3.328 and out["working"][4]["result"] == 79.872  # (208 x 20 x 0.8)/1000; x 24

    hyper = R("Redundancy: 2N at utility/substation level, N+1 at rack level",
              "Rack density: minimum 120kW per rack, liquid cooling required at rack and chip level",
              "Power architecture: preference for 800VDC rack-level distribution where mature")
    f, s = facts(hyper), scope(hyper, kb)
    m = {"REQ-0001-0002": [{"bu": "JETCOOL", "product_id": "JETCOOL-CDU", "offering_type": "SEMI_CUSTOM"}],
         "REQ-0001-0001": [{"bu": "ANORD", "product_id": "ANORD-LVSB", "offering_type": "CTO"}]}
    ru = {r["id"]: r["status"] for r in rules(f, s["in_scope"], m, kb, eng)}
    assert f["rack_density_kw"]["value"] == 120 and ru["R-002"] == "fail" and ru["R-001"] == "warn", (f, ru)
    assert ru["R-003"] == "warn"  # 2N at utility level but no EP2 / Crown matched

    flags = tier_flags(R("Provide a standard enclosure for the relays."),
                       {"REQ-0001-0001": [{"bu": "EP2", "product_id": "EP2-RPP", "offering_type": "CTO"}]}, kb)
    assert [x["kind"] for x in flags] == ["below_default", "suggest_lower"], flags  # flagged, never applied
    print("matching checks ok")
