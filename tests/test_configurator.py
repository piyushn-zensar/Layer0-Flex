"""P-54 (C-55) and P-55 (C-56): the supplied configurator on the merged catalog, fed from frozen RFP requirements
grouped by component. The RC-1 items (tests/configurator_rc1_items.json: the 149 technical and compliance items of the
seeded RC-1 bid, with document and page) replay the frozen answers in data/llm_cache/configurator_{groups,assign,inputs}/."""
import json
from pathlib import Path

from app.modules.configurator import agent
from app.modules.configurator import rfp_configurator as rc
from app.modules.configurator import service as configurator

RC1 = json.loads((Path(__file__).parent / "configurator_rc1_items.json").read_text("utf-8"))


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


PLAN = configurator.plan(RC1)


def test_rc1_grouped_by_component():
    names = {g["kind"]: [] for g in PLAN["groups"]}
    for g in PLAN["groups"]:
        names[g["kind"]].append(g["name"])
    assert len(names["dc_dc"]) == 1 and "54 VDC" in names["dc_dc"][0]           # the rack shelf is its own search
    assert len(names["other"]) >= 8 and names["system"] == ["System parameters"]
    assert not PLAN["unassigned"] and not PLAN["unknown_ids"]                    # every item answered, no made-up ID
    other = [g for g in PLAN["groups"] if g["kind"] == "other"]
    assert all(g["run"] is None for g in other)                                  # no numeric table: no search


def test_rc1_rack_shelf_is_a_no_match_with_the_reason():
    shelf = next(g for g in PLAN["groups"] if g["kind"] == "dc_dc")["run"]
    stated = {k: v["stated"] for k, v in shelf["inputs"].items()}
    assert stated["board.input_v_min"] == "800 VDC" and stated["board.output_v_min"] == "54 VDC"
    assert stated["board.output_power_w"] == "15 kW" and "system" not in shelf      # board input only (C-56)
    assert shelf["board"]["status"] == "no_match" and shelf["status"] == "needs_review"
    assert any("upstream conversion stage" in n for n in shelf["board"]["notes"])
    assert shelf["inputs"]["board.applications"]["interpreted"]                  # a catalogue value the model chose


def test_rc1_system_checks_apart_from_the_components():
    s = PLAN["system"]
    assert "board" not in s and s["inputs"]["system.total_it_load_mw"]["stated"] == "120 MW"
    assert s["inputs"]["system.total_it_load_mw"]["req_ids"] == ["REQ-0003-0006"]
    checks = {c["item"]: c["status"] for c in s["system"]["checks"]}
    assert checks["distribution voltage"] == "pass" and checks["module count"] == "review"   # Axiom limits unverified
    assert {m["field"] for m in s["missing"]} == {"rack_density_kw"}             # stated as rack TDP; not read (known limit)


def test_system_checks_not_applicable_without_data_centre_parameters(monkeypatch):
    items = [{"req_id": "R1", "text": "", "quote": "Switchgear rated 13.2 kV", "section": "", "category": "technical",
              "document": "x.pdf", "page": 1}]
    monkeypatch.setattr(configurator.agent, "group", lambda its: {"groups": [{"name": "System parameters", "kind": "system",
                                                                               "req_ids": ["R1"]}], "unassigned": []})
    monkeypatch.setattr(configurator.agent, "extract", lambda its, vocab, component="": {"system": {
        "distribution_voltage": {"value": "13.2 kV", "req_ids": ["R1"], "source": "13.2 kV"}}, "board": {}})
    s = configurator.plan(items)["system"]
    assert s["status"] == "not_applicable" and "Axiom" in s["reason"] and s["inputs"]["system.distribution_voltage"]
