"""P-56 (C-57, C-58, C-61): every configurator outcome explained (match, near match, insufficient information, no
match), per-requirement status, assumptions marked against what the RFP states, open and unsupported checks; stored
per bid and served by the API. Built on synthetic requirement items, so no model answer is needed."""
import os
import tempfile

os.environ.setdefault("STORE_DIR", tempfile.mkdtemp())

from conftest import auth, signed_in  # noqa: E402

from app.modules.configurator import explain, service  # noqa: E402

PARTS = {p["part_number"]: p for p in service.catalog.power_modules()}


def _item(rid: str, quote: str) -> dict:
    return {"req_id": rid, "text": quote, "quote": quote, "section": "", "category": "technical", "document": "rfp.pdf", "page": 3}


def _group(board: dict, items: list[dict]) -> dict:
    """A DC/DC group whose agent answer is `board` ({field: (as_written, req_id)})."""
    raw = {"system": {}, "board": {f: ({"as_written": v, "req_ids": [r], "source": v} if f not in service.agent.BOARD
                                       or service.agent.BOARD[f][0] == "number" else {"value": v, "req_ids": [r], "source": v})
                                   for f, (v, r) in board.items()}}
    prepared = service.normalise(raw, items)
    prepared["input"] = {"board": prepared["input"]["board"]}
    prepared |= {"requirements": items, "missing": service.missing(prepared["input"])}
    return {"name": "test", "kind": "dc_dc", "req_ids": [i["req_id"] for i in items], "requirements": items,
            "run": service.run(prepared)}


def _explain(board: dict, items: list[dict]) -> dict:
    return explain.explain(_group(board, items), service.catalog_frame(), PARTS)


def test_match_with_candidates_assumptions_and_checks():
    items = [_item("R1", "48 V bus, 40 to 60 V, to 12 V at 1500 W"), _item("R2", "PMBus"), _item("R3", "Ship in 6 weeks")]
    e = _explain({"input_v_min": ("40 V", "R1"), "input_v_max": ("60 V", "R1"), "output_v_min": ("12 V", "R1"),
                  "output_power_w": ("1500 W", "R1"), "digital": ("PMBus", "R2")}, items)
    assert e["outcome"] == "match" and e["candidates"] and not e["near_matches"]
    c = e["candidates"][0]
    assert c["link"].startswith("/catalog/product?part=") and "%2F" in c["link"] and c["verified"] is False
    status = {r["req_id"]: r["status"] for r in e["requirements"]}
    assert status == {"R1": "satisfied", "R2": "satisfied", "R3": "cannot_assess"}
    basis = {a["item"]: a["basis"] for a in e["assumptions"]}
    assert basis["Redundancy"] == "configurator default, not in the RFP" and "not in the RFP" in basis["Design margin"]
    checks = {k["check"]: k["status"] for k in e["checks"]}
    assert checks["Multiple outputs"] == "not_supported" and checks["Thermal derating"] == "open"
    assert checks["Catalogue values unverified"] == "open" and checks["Certification applicability"] == "open"


def test_near_match_names_the_failing_constraint_and_is_not_a_match():
    items = [_item("R1", "40 to 60 V in, 12 V out, 1500 W"), _item("R2", "height at most 5 mm")]
    e = _explain({"input_v_min": ("40 V", "R1"), "input_v_max": ("60 V", "R1"), "output_v_min": ("12 V", "R1"),
                  "output_power_w": ("1500 W", "R1"), "max_height_mm": ("5 mm", "R2")}, items)
    assert e["outcome"] == "near_match" and not e["candidates"] and e["near_matches"]
    assert "height" in e["reason"] and "not a match" in e["reason"]
    status = {r["req_id"]: r["status"] for r in e["requirements"]}
    assert status == {"R1": "satisfied", "R2": "not_satisfied"}


def test_insufficient_information_when_a_needed_input_is_missing():
    e = _explain({"input_v_min": ("40 V", "R1"), "input_v_max": ("60 V", "R1")}, [_item("R1", "input 40 to 60 V")])
    assert e["outcome"] == "insufficient_information" and "not a recommendation" in e["reason"]
    assert {m["needed_for"] for m in e["missing"]} == {"output voltage filter", "module count (power or current)"}


def test_no_match_explained_without_relaxing():
    items = [_item("R1", "800 VDC to 54 VDC, 15 kW"), _item("R2", "PMBus telemetry")]
    e = _explain({"input_v_min": ("800 V", "R1"), "output_v_min": ("54 V", "R1"), "output_power_w": ("15 kW", "R1"),
                  "digital": ("PMBus", "R2")}, items)
    assert e["outcome"] == "no_match" and not e["candidates"] and not e["near_matches"]
    assert "upstream conversion stage" in e["reason"]
    why = {r["req_id"]: (r["status"], r["why"]) for r in e["requirements"]}
    assert why["R1"][0] == "not_satisfied" and "input voltage range (800 V)" in why["R1"][1]
    assert why["R2"][0] == "cannot_assess" and "on its own" in why["R2"][1]


def test_stored_per_bid_and_served(monkeypatch):
    client = signed_in()
    opp = client.post("/api/bids", json={"title": "configurator"}).json()["id"]
    assert client.get(f"/api/bids/{opp}/components").json()["run"] is None
    items = [_item("R1", "48 V bus, 40 to 60 V, to 12 V at 1500 W")]
    group = _group({"input_v_min": ("40 V", "R1"), "input_v_max": ("60 V", "R1"), "output_v_min": ("12 V", "R1"),
                    "output_power_w": ("1500 W", "R1")}, items)
    other = {"name": "MV switchgear", "kind": "other", "req_ids": ["R9"], "run": None, "requirements": [_item("R9", "15 kV")]}
    monkeypatch.setattr(service, "components", lambda db, o: {"groups": [group, other], "system": None,
                                                               "ungrouped": [], "unassigned": [], "unknown_ids": []})
    assert client.post(f"/api/bids/{opp}/components", headers=auth("crown.de")).status_code == 403
    out = client.post(f"/api/bids/{opp}/components").json()
    assert [c["outcome"] for c in out["components"]] == ["match", "not_assessed"]
    assert out["run"]["catalog_import"] == service.catalog.power_modules_import() and "pending engineering review" in out["note"]
    mine = client.get(f"/api/bids/{opp}/requirements/R1/components").json()
    assert mine[0]["component"]["name"] == "test" and mine[0]["requirement"]["status"] == "satisfied"
    assert client.get("/api/bids/OPP-9999/components").status_code == 404
