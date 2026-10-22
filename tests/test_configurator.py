"""P-54 (C-55): the supplied configurator on the merged catalog, fed from frozen RFP requirements. The RC-1 items
(tests/configurator_rc1_items.json, taken from the seeded RC-1 bid with their document and page) replay the frozen
input-agent answers in data/llm_cache/configurator_inputs/."""
import json
from pathlib import Path

from app.modules.configurator import agent
from app.modules.configurator import rfp_configurator as rc
from app.modules.configurator import service as configurator

RC1 = json.loads((Path(__file__).parent / "configurator_rc1_items.json").read_text("utf-8"))


def _prepare(items: list[dict]) -> dict:
    """service.inputs() without the database: the same agent call on the same items."""
    prepared = configurator.normalise(agent.extract(items, rc.catalog_vocab(configurator.catalog_frame())), items)
    return {"requirements": items, **prepared, "missing": configurator.missing(prepared["input"])}


def test_supplied_selftest_and_same_answer_as_the_spreadsheet():
    cat = configurator.catalog_frame()
    assert rc.selftest(cat) == 0
    xlsx = rc.load_catalog(str(Path(__file__).parents[1] / "data/axiom_products/PowerModules-1791937030.xlsx"))
    probe = {"board": {"input_v_min": 36, "input_v_max": 75, "output_v_min": 12, "output_v_max": 12, "output_power_w": 600}}
    parts = lambda r: [(c["part_number"], c["modules_total"]) for c in r["board"]["candidates"]]  # noqa: E731
    assert parts(rc.configure(probe, cat)) == parts(rc.configure(probe, xlsx)) != []


def test_units_are_converted_by_code_and_numbers_must_be_in_the_text():
    items = [{"req_id": "R1", "text": "", "quote": "load 120,000 kW, rack 0.5 in, input 0.8 kVDC, six 15 kW converters, 113 °F"}]
    ref = lambda s: {"as_written": s, "req_ids": ["R1"], "source": s}  # noqa: E731
    n = configurator.normalise({"system": {"total_it_load_mw": ref("120,000 kW"), "coolant_supply_temp_c": ref("113 °F"),
                                           "redundancy": {"value": "N+1", "req_ids": ["R1"], "source": "six converters"}},
                                "board": {"input_v_min": ref("0.8 kVDC"), "max_height_mm": ref("0.5 in"),
                                          "output_power_w": ref("90 kW"), "output_current_a": ref("15 kW")}}, items)
    s, b = n["input"]["system"], n["input"]["board"]
    assert (s["total_it_load_mw"]["value"], s["coolant_supply_temp_c"]["value"]) == (120, 45)
    assert (b["input_v_min"]["value"], b["max_height_mm"]["value"]) == (800, 12.7)
    assert "output_power_w" not in b and "output_current_a" not in b          # added up / wrong quantity: dropped
    assert {i["field"] for i in n["unit_issues"]} == {"board.output_power_w", "board.output_current_a"}
    assert n["provenance"]["system.redundancy"]["interpreted"] and not n["provenance"]["board.input_v_min"]["interpreted"]


def test_rc1_system_checks_from_frozen_requirements():
    p = _prepare(RC1["system"])
    stated = {k: v["stated"] for k, v in p["provenance"].items()}
    assert stated == {"system.total_it_load_mw": "120 MW", "system.rack_density_kw": "330 kW",
                      "system.distribution_voltage": "800 VDC", "system.redundancy": "N+1"}
    assert p["provenance"]["system.total_it_load_mw"]["req_ids"] == ["REQ-0003-0006"]
    assert {m["field"] for m in p["missing"]} == {"cooling_mode", "coolant_supply_temp_c"}
    r = configurator.run(p)
    checks = {c["item"]: c["status"] for c in r["system"]["checks"]}
    assert checks["distribution voltage"] == "pass" and checks["module count"] == "review"  # 120 MW / 4 MW, unverified
    assert r["board"]["status"] == "no_constraints" and r["requirements"][0]["document"].startswith("RC-1")


def test_rc1_rack_shelf_is_a_no_match_with_the_reason():
    p = _prepare(RC1["board"])
    b = p["input"]["board"]
    assert (b["input_v_min"]["value"], b["output_v_min"]["value"], b["output_power_w"]["value"]) == (800, 54, 15000)
    r = configurator.run(p)
    assert r["board"]["status"] == "no_match" and r["status"] == "needs_review"
    assert any("upstream conversion stage" in n for n in r["board"]["notes"])
    assert r["board"]["relaxation"]["input_range"] == 0                        # no single relaxation would help
