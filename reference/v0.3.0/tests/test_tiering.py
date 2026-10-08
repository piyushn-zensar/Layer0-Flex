"""
Unit tests for agents/tier_classifier.py. Pure deterministic logic, no
LLM call and no mock/real split needed — these run instantly.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.tier_classifier import classify_layer, run


BASE_REQ = {
    "capacity_mw": 6.0, "redundancy": "N+1", "voltage_arch": "415VAC",
    "rack_density_kw": 40, "site": "TBD", "timeline": "4 months",
}


def test_layer1_always_eto_exception_by_default():
    # Layer 1 has only one brand today (EPC Power), always ETO_EXCEPTION.
    result = classify_layer(1, BASE_REQ)
    assert result["tier"] == "ETO_EXCEPTION"
    assert result["source"] == "brand_default"


def test_layer2_cto_automate_without_2n_redundancy():
    req = {**BASE_REQ, "redundancy": "N+1"}
    result = classify_layer(2, req)
    assert result["tier"] == "CTO_AUTOMATE"
    assert "Anord Mardix" in result["hinted_brands"][0]


def test_layer2_eto_guided_with_2n_redundancy():
    req = {**BASE_REQ, "redundancy": "2N"}
    result = classify_layer(2, req)
    assert result["tier"] == "ETO_GUIDED"


def test_layer3_always_cto_automate():
    result = classify_layer(3, BASE_REQ)
    assert result["tier"] == "CTO_AUTOMATE"


def test_layer4_cto_automate_without_800vdc():
    req = {**BASE_REQ, "voltage_arch": "415VAC"}
    result = classify_layer(4, req)
    assert result["tier"] == "CTO_AUTOMATE"


def test_layer4_eto_exception_with_800vdc():
    # Both EPC Power (ETO_EXCEPTION) and Flex Power Modules (CTO_AUTOMATE)
    # apply at 800VDC — the most conservative tier must win.
    req = {**BASE_REQ, "voltage_arch": "800VDC"}
    result = classify_layer(4, req)
    assert result["tier"] == "ETO_EXCEPTION"
    assert len(result["hinted_brands"]) == 2


def test_layer5_and_6_always_cto_automate():
    assert classify_layer(5, BASE_REQ)["tier"] == "CTO_AUTOMATE"
    assert classify_layer(6, BASE_REQ)["tier"] == "CTO_AUTOMATE"


def test_downward_override_is_held_pending_human_confirmation():
    """OPTION B fail-safe: a downward demotion (ETO_GUIDED -> CTO_AUTOMATE)
    triggered by a prose keyword must NOT apply automatically. It is a
    false-CTO generator — it could route bespoke switchgear into an
    automated configurator. The safer tier holds; the override is emitted
    as a suggestion requiring human confirmation."""
    req = {**BASE_REQ, "redundancy": "2N"}
    result = classify_layer(2, req, requirement_text="This order uses a standard enclosure throughout.")
    assert result["tier"] == "ETO_GUIDED", "safer tier must hold"
    assert result["pending_suggestion"] is not None
    assert result["pending_suggestion"]["suggested_tier"] == "CTO_AUTOMATE"
    assert result["pending_suggestion"]["status"] == "PENDING_HUMAN_CONFIRMATION"
    assert result["pending_suggestion"]["matched_keyword"] == "standard enclosure"


def test_upward_override_applies_immediately():
    """Upward moves increase human involvement and are therefore fail-safe.
    They apply without gating."""
    req = {**BASE_REQ, "voltage_arch": "415VAC"}  # L4 would default to CTO_AUTOMATE
    result = classify_layer(4, req, requirement_text="This requires a novel topology never built before.")
    assert result["tier"] == "ETO_EXCEPTION"
    assert result["source"] == "component_override"
    assert result.get("pending_suggestion") is None


def test_run_surfaces_pending_confirmations():
    req = {**BASE_REQ, "redundancy": "2N"}
    out = run(req, "This order uses a standard enclosure throughout.")
    assert len(out["pending_confirmations"]) >= 1
    assert "pending human confirmation" in out["explanation"]


def test_component_override_is_scoped_to_its_layer():
    # "standard enclosure" only applies to Layer 2 — Layer 1 must be
    # unaffected by the same requirement text.
    text = "This order uses a standard enclosure throughout."
    result = classify_layer(1, BASE_REQ, requirement_text=text)
    assert result["source"] == "brand_default"
    assert result["tier"] == "ETO_EXCEPTION"


def test_novel_topology_override_forces_exception():
    req = {**BASE_REQ, "voltage_arch": "415VAC"}  # would otherwise be CTO_AUTOMATE
    result = classify_layer(4, req, requirement_text="This requires a novel topology never built before.")
    assert result["tier"] == "ETO_EXCEPTION"
    assert result["source"] == "component_override"


def test_run_produces_six_layers_with_correct_counts():
    output = run(BASE_REQ)
    assert len(output["tiers"]) == 6
    tiers = [t["tier"] for t in output["tiers"]]
    # Under BASE_REQ (N+1, 415VAC): Layer 1 and would-be EPC layers are the
    # only ETO_EXCEPTION; layers 2,3,4,5,6 are CTO_AUTOMATE at these settings.
    assert tiers.count("ETO_EXCEPTION") == 1
    assert tiers.count("CTO_AUTOMATE") == 5
    assert "explanation" in output and "evidence" in output


if __name__ == "__main__":
    import inspect
    test_fns = [obj for name, obj in list(globals().items()) if name.startswith("test_") and inspect.isfunction(obj)]
    passed, failed = 0, 0
    for fn in test_fns:
        try:
            fn()
            print(f"PASS: {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {fn.__name__} — {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


# --- Regression tests against REAL public RFPs ---
# These exist because the synthetic RFPs were written in the system's own
# vocabulary and therefore could not catch vocabulary or scope failures.
# Each fixture is a technical summary of a verifiable public document.

from pathlib import Path as _Path
from agents import understand_agent as _ua

_SAMPLES = _Path(__file__).resolve().parent.parent / "knowledge_base" / "sample_rfps"


def _load(name):
    text = (_SAMPLES / name).read_text()
    return text, _ua.run(text)


def test_real_syracuse_extracts_mv_electrical_vocabulary():
    """The original extraction returned None for every field on this document."""
    _, req = _load("rfp_REAL_syracuse_switchgear.txt")
    assert req["voltage_class_kv"] == 15.0
    assert req["arc_resistant"] is not None and "2B" in req["arc_resistant"]
    assert req["breaker_positions"] == 18


def test_real_syracuse_routes_layer2_to_crown_eto_guided():
    """Arc-resistant MV switchgear must route to Crown per the KB's own
    selection rules — not to Anord Mardix / CTO_AUTOMATE."""
    text, req = _load("rfp_REAL_syracuse_switchgear.txt")
    result = run(req, text)
    l2 = next(t for t in result["tiers"] if t["n"] == 2)
    assert l2["tier"] == "ETO_GUIDED"
    assert any("Crown" in b for b in l2["hinted_brands"])


def test_real_syracuse_scope_excludes_thermal_and_compute():
    """The 'NOT SPECIFIED' section must not put cooling in scope."""
    _, req = _load("rfp_REAL_syracuse_switchgear.txt")
    assert 2 in req["layers_in_scope"]
    assert 5 not in req["layers_in_scope"]
    assert 6 not in req["layers_in_scope"]


def test_real_ftlauderdale_extracts_ups_and_rack_count():
    _, req = _load("rfp_REAL_ftlauderdale_ups.txt")
    assert req["ups_kva"] == 45.0
    assert req["rack_count"] == 10
    assert "208" in (req["voltage_arch"] or "")


def test_real_ftlauderdale_scope_is_distribution_and_rack_power():
    _, req = _load("rfp_REAL_ftlauderdale_ups.txt")
    assert set(req["layers_in_scope"]) == {3, 4}


def test_real_davis_monthan_detects_grid_interface_scope():
    """A land-lease RFP with onsite generation / BESS / microgrid must put
    Layer 1 (grid interface) in scope — EPC Power territory."""
    _, req = _load("rfp_REAL_davis_monthan_ai_dc.txt")
    assert 1 in req["layers_in_scope"]
    assert req["onsite_generation"] is True
    assert req["capacity_mw"] is not None
