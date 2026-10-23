"""P-62: the published-ratings search. Requirement values (read by a frozen model call, numbers checked in the
requirement text, units converted by code) against the spec tables of the families proposed for them: rules at least /
within / at most / parsed text, a short-time rating for fewer seconds does not count, a match needs two values
compared, nothing relaxed, and a variant that publishes too few of the asked ratings is no candidate."""
from app.modules.configurator import ranges
from app.modules.configurator import service as configurator


def _attr(name, lo, hi, unit, base_lo=None, base_hi=None, text="", conditions="", page=1):
    return {"name": name, "label": name, "min": lo, "max": hi, "text": text, "unit": unit, "conditions": conditions,
            "page": page, "quote": text or f"{name} {hi}", "min_base": base_lo, "max_base": base_hi,
            "source": {"file": "x.pdf", "page": page, "url": None}}


ITEM = {"spec_id": "SPEC-1", "family_key": "ANORD-LVSB/MDX", "variant": "MDX", "verified": False, "attributes": [
    _attr("rated_current", None, 6300, "A", None, 6300.0), _attr("rated_voltage_ac", None, 690, "VAC", None, 690.0),
    _attr("short_time_withstand", 50, 100, "kA", 50.0, 100.0, "50kA for 3s, up to 100kA for 1s", "1 s"),
    _attr("ip_rating", None, None, "", text="IP31"), _attr("form_of_separation", None, None, "", text="Form 4b Type 7")]}
CDU = {"spec_id": "SPEC-2", "family_key": "JETCOOL-CDU/Modular CDU", "variant": "x6", "verified": False,
       "attributes": [_attr("cooling_capacity", 1.2, 1.8, "MW", 1200.0, 1800.0)]}


def _cs(*pairs, req="R1"):
    items = [{"req_id": req, "text": " ".join(w for _, w in pairs), "quote": ""}]
    cs, _, issues = ranges.parse({"constraints": [{"attribute": a, "as_written": w, "req_ids": [req], "source": w}
                                                  for a, w in pairs]}, items)
    return ranges.dedupe(cs), issues


def test_rules_and_text_parsing():
    cs, issues = _cs(("rated_current", "4000 A"), ("rated_voltage_ac", "480 V"), ("ip_rating", "IP30"),
                     ("form_of_separation", "Form 3b"), ("short_time_withstand", "65 kA for 3 s"))
    assert not issues
    res = {r["attribute"]: r["status"] for r in ranges.search(cs, ["ANORD-LVSB"], [ITEM])[0]["results"]}
    assert res == {"rated_current": "met", "rated_voltage_ac": "met", "ip_rating": "met", "form_of_separation": "met",
                   "short_time_withstand": "not_met"}            # 100 kA is for 1 s only; 3 s asked: 50 kA
    cs, _ = _cs(("rated_current", "8000 A"), ("ip_rating", "IP54"), ("rated_voltage_ac", "15 kV"))
    assert {r["status"] for r in ranges.search(cs, ["ANORD-LVSB"], [ITEM])[0]["results"]} == {"not_met"}


def test_numbers_must_be_in_the_text_and_units_fit():
    items = [{"req_id": "R1", "text": "busway rated 2500 A", "quote": ""}]
    cs, _, issues = ranges.parse({"constraints": [
        {"attribute": "rated_current", "as_written": "2.5 kA", "req_ids": ["R1"], "source": "2500 A"},   # converted by the model
        {"attribute": "rated_current", "as_written": "2500 A", "req_ids": ["R1"], "source": "2500 A"},
        {"attribute": "frequency", "as_written": "2500 A", "req_ids": ["R1"], "source": "2500 A"}]}, items)
    assert [(c["attribute"], c["hi"]) for c in cs] == [("rated_current", 2500.0)]
    assert len(issues) == 2


def _explain(cs, specs, fams):
    group = {"name": "LV switchgear", "kind": "spec_range", "req_ids": ["R1"], "run": {
        "constraints": cs, "inputs": {}, "issues": [], "families": fams, "candidates": ranges.search(cs, fams, specs)},
        "requirements": [{"req_id": "R1", "parent": None, "text": "t", "document": "d", "page": 1}]}
    return ranges.explain(group)


def test_outcomes():
    cs, _ = _cs(("rated_current", "4000 A"), ("rated_voltage_ac", "400 V"))
    e = _explain(cs, [ITEM], ["ANORD-LVSB"])
    assert e["outcome"] == "match" and "not an orderable configuration" in e["reason"]
    assert e["requirements"][0]["status"] == "satisfied" and e["comparison"]["rows"]
    cs, _ = _cs(("rated_current", "4000 A"))
    assert _explain(cs, [ITEM], ["ANORD-LVSB"])["outcome"] == "insufficient_information"   # one value selects nothing
    cs, _ = _cs(("rated_current", "8000 A"), ("rated_voltage_ac", "400 V"))
    e = _explain(cs, [ITEM], ["ANORD-LVSB"])
    assert e["outcome"] == "near_match" and "not a match" in e["reason"] and e["requirements"][0]["status"] == "not_satisfied"
    cs, _ = _cs(("rated_current", "4000 A"), ("frequency", "50 Hz"), ("peak_withstand", "105 kA"))
    assert _explain(cs, [ITEM], ["ANORD-LVSB"])["outcome"] == "insufficient_information"   # 1 of 3 published: no candidate


def test_values_compared_only_with_families_proposed_for_their_requirement():
    cs, _ = _cs(("cooling_capacity", "1.5 MW"), ("rated_current", "4000 A"))
    cs[0]["families"], cs[1]["families"] = ["JETCOOL-CDU"], ["ANORD-LVSB"]
    found = {x["family_key"]: {r["attribute"]: r["status"] for r in x["results"]}
             for x in ranges.search(cs, ["JETCOOL-CDU", "ANORD-LVSB"], [ITEM, CDU])}
    assert found["JETCOOL-CDU/Modular CDU"] == {"cooling_capacity": "met", "rated_current": "not_compared"}
    assert found["ANORD-LVSB/MDX"] == {"cooling_capacity": "not_compared", "rated_current": "met"}


def test_plan_turns_rated_components_into_a_range_search(monkeypatch):
    from types import SimpleNamespace
    items = [{"req_id": "R1", "parent": None, "text": "Switchgear 4000 A at 400 V", "quote": "4000 A, 400 V", "section": "",
              "category": "technical", "document": "rfp.pdf", "page": 2}]
    monkeypatch.setattr(configurator.agent, "group", lambda its: {"groups": [{"name": "LV switchgear", "kind": "other",
                                                                               "req_ids": ["R1"]}], "unassigned": []})
    monkeypatch.setattr(configurator.agent, "range_inputs", lambda comp, attrs, refs: {"constraints": [
        {"attribute": "rated_current", "as_written": "4000 A", "req_ids": ["R1"], "source": "4000 A"},
        {"attribute": "rated_voltage_ac", "as_written": "400 V", "req_ids": ["R1"], "source": "400 V"}]})
    matches = {"R1": SimpleNamespace(units=[{"bu": "ANORD", "product_id": "ANORD-LVSB"}])}
    g = configurator.plan(items, matches, [ITEM])["groups"][0]
    assert g["kind"] == "spec_range" and g["run"]["families"] == ["ANORD-LVSB"]
    assert configurator.explain.explain(g, None, {})["outcome"] == "match"
    assert configurator.plan(items, {}, [ITEM])["groups"][0]["kind"] == "other"   # no proposed family: not searched
