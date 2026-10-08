"""
Unit tests for the deterministic engineering-rule checks in
validation_agent.py. These never call an LLM (mock or otherwise) — they
test pure Python logic, so they run instantly and belong in CI.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.validation_agent import _evaluate_deterministic_rules
from rag.retriever import get_full_rules, get_full_layer_stack


def _base_layers():
    stack = get_full_layer_stack()
    # brands is now a list of {"name", "automation_tier", "tier_rationale"}
    # objects; use the first brand's name string, matching the pre-tiering
    # layer shape validation_agent.py expects (brand as a plain string).
    return [
        {"n": l["n"], "name": l["name"], "brand": l["brands"][0]["name"], "spec": "placeholder"}
        for l in stack["layers"]
    ]


def test_voltage_consistency_pass_when_no_800vdc():
    rules = get_full_rules()
    req = {"voltage_arch": "415VAC", "rack_density_kw": 40, "redundancy": "N+1", "completeness_score": 100}
    layers = _base_layers()
    checks = _evaluate_deterministic_rules(req, layers, rules)
    voltage_check = next(c for c in checks if c["id"] == "R-001_voltage_consistency")
    assert voltage_check["status"] == "pass"


def test_voltage_consistency_fails_when_800vdc_not_reflected():
    rules = get_full_rules()
    req = {"voltage_arch": "800VDC", "rack_density_kw": 40, "redundancy": "N+1", "completeness_score": 100}
    layers = _base_layers()  # generic specs, none mention "800"
    checks = _evaluate_deterministic_rules(req, layers, rules)
    voltage_check = next(c for c in checks if c["id"] == "R-001_voltage_consistency")
    assert voltage_check["status"] == "fail"


def test_cooling_threshold_fails_below_100kw_without_direct_to_chip_note():
    rules = get_full_rules()
    req = {"voltage_arch": "415VAC", "rack_density_kw": 150, "redundancy": "N+1", "completeness_score": 100}
    layers = _base_layers()  # Layer 5 spec is "placeholder", no "direct-to-chip" mention
    checks = _evaluate_deterministic_rules(req, layers, rules)
    cooling_check = next(c for c in checks if c["id"] == "R-002_cooling_threshold")
    assert cooling_check["status"] == "fail"


def test_cooling_threshold_passes_under_100kw():
    rules = get_full_rules()
    req = {"voltage_arch": "415VAC", "rack_density_kw": 40, "redundancy": "N+1", "completeness_score": 100}
    layers = _base_layers()
    checks = _evaluate_deterministic_rules(req, layers, rules)
    cooling_check = next(c for c in checks if c["id"] == "R-002_cooling_threshold")
    assert cooling_check["status"] == "pass"


def test_epc_power_dependency_flagged():
    rules = get_full_rules()
    req = {"voltage_arch": "415VAC", "rack_density_kw": 40, "redundancy": "N+1", "completeness_score": 100}
    layers = _base_layers()  # Layer 1 brand includes "EPC Power" per the KB default
    checks = _evaluate_deterministic_rules(req, layers, rules)
    epc_check = next(c for c in checks if c["id"] == "R-004_epc_power_dependency")
    assert epc_check["status"] == "warn"


def test_completeness_check_reflects_stage1_score():
    rules = get_full_rules()
    req = {"voltage_arch": "415VAC", "rack_density_kw": 40, "redundancy": "N+1", "completeness_score": 40}
    layers = _base_layers()
    checks = _evaluate_deterministic_rules(req, layers, rules)
    completeness = next(c for c in checks if c["id"] == "completeness")
    assert completeness["status"] == "fail"


# --- Regression tests: unknown values must NOT be treated as safe ---
# A missing rack density previously coerced to 0 and "passed" the 100kW
# cooling threshold, reporting a validated cooling design for a spec that
# was never provided. Absence of data is not absence of risk.

def test_unknown_rack_density_warns_rather_than_passes():
    rules = get_full_rules()
    req = {"voltage_arch": "415VAC", "rack_density_kw": None, "redundancy": "N+1", "completeness_score": 60}
    layers = _base_layers()
    checks = _evaluate_deterministic_rules(req, layers, rules)
    cooling = next(c for c in checks if c["id"] == "R-002_cooling_threshold")
    assert cooling["status"] == "warn"
    assert "not specified" in cooling["note"].lower()


def test_unknown_voltage_arch_warns_rather_than_passes():
    rules = get_full_rules()
    req = {"voltage_arch": None, "rack_density_kw": 40, "redundancy": "N+1", "completeness_score": 60}
    layers = _base_layers()
    checks = _evaluate_deterministic_rules(req, layers, rules)
    voltage = next(c for c in checks if c["id"] == "R-001_voltage_consistency")
    assert voltage["status"] == "warn"


def test_unknown_redundancy_warns_rather_than_passes():
    rules = get_full_rules()
    req = {"voltage_arch": "415VAC", "rack_density_kw": 40, "redundancy": None, "completeness_score": 60}
    layers = _base_layers()
    checks = _evaluate_deterministic_rules(req, layers, rules)
    redundancy = next(c for c in checks if c["id"] == "R-003_redundancy_match")
    assert redundancy["status"] == "warn"


def test_known_safe_values_still_pass():
    # The fix must not make everything warn — genuinely safe, known values
    # must still return a clean pass.
    rules = get_full_rules()
    req = {"voltage_arch": "415VAC", "rack_density_kw": 40, "redundancy": "N+1", "completeness_score": 100}
    layers = _base_layers()
    checks = _evaluate_deterministic_rules(req, layers, rules)
    for rule_id in ("R-001_voltage_consistency", "R-002_cooling_threshold", "R-003_redundancy_match"):
        assert next(c for c in checks if c["id"] == rule_id)["status"] == "pass"


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
