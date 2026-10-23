"""Spec tables (23 Oct 2026): ratings read from the supplied PDFs and the official product pages. A value is kept only
when its quote is the page's own words and its number is in that quote (the model never converts or derives); units
are converted by code; every item is unverified until the family's unit confirms it."""
import json
import os
import tempfile
from pathlib import Path

os.environ.setdefault("STORE_DIR", tempfile.mkdtemp())

from conftest import auth, signed_in  # noqa: E402

from scripts import extract_product_specs as x  # noqa: E402

SPECS = json.loads((x.OUT).read_text("utf-8"))


def test_units_converted_by_code():
    assert x.convert(1.2, "MW", "kW") == (1200.0, None) and x.convert(2800, "W", "kW") == (2.8, None)
    assert x.convert(100, "kA", "kA") == (100.0, None) and x.convert(65000, "A", "kA") == (65.0, None)
    assert x.convert(690, "VAC", "V") == (690.0, None) and x.convert(113, "°F", "C") == (45.0, None)
    assert x.convert(2.2, "m", "mm") == (2200.0, None) and x.convert(1200, "LPM", "L/min") == (1200.0, None)
    assert x.convert(3, "kA/1s", "kA")[0] is None


def test_guard_drops_converted_unquoted_and_off_page_values(monkeypatch):
    page = "Cooling Capacity Redundant 1.2 MW Performance 1.8 MW Approach Temp. 6ºC 9ºC"
    attr = lambda name, lo, hi, unit, quote, pg=1: {"name": name, "label": name, "min": lo, "max": hi, "text": "",  # noqa: E731
                                                     "unit": unit, "conditions": "", "page": pg, "quote": quote}
    answer = {"items": [{"variant": "Modular CDU", "attributes": [
        attr("cooling_capacity", 1.2, 1.8, "MW", "Cooling Capacity Redundant 1.2 MW Performance 1.8 MW"),  # kept
        attr("cooling_capacity", 1200, 1200, "kW", "Cooling Capacity Redundant 1.2 MW"),                     # converted
        attr("approach_temperature", 6, 9, "ºC", "Approach temperature of 6 to 9 degrees at full flow"),     # not the page's words
        attr("flow_rate", 600, 600, "LPM", "Cooling Capacity", pg=2)]}]}                                    # page not given
    monkeypatch.setattr(x.agent, "extract", lambda family, title, text: answer)
    items, issues = x.run_job({"file": "f.pdf", "url": None, "title": "t", "family_key": "JETCOOL-CDU/Modular CDU",
                               "family": "JETCOOL-CDU/Modular CDU", "texts": {1: page}})
    kept = items[0]["attributes"]
    assert [(a["name"], a["min_base"], a["max_base"]) for a in kept] == [("cooling_capacity", 1200.0, 1800.0)]
    assert sorted(i["why"] for i in issues) == ["1200, 1200 not in the quote", "page not in the chunk", "quote not found on the page"]


def test_committed_table_covers_the_asked_families_with_sources():
    families = {i["family_key"] for i in SPECS["items"]}
    for f in ("ANORD-LVSB/MDX", "ANORD-LVSB/SEN Plus", "ANORD-LVSB/AMX", "ANORD-BUSWAY/DATABAR DX", "ANORD-BUSWAY/IBAR HXC",
              "ANORD-BUSWAY/RESINBAR CXC", "JETCOOL-CDU/SmartSense CDU", "JETCOOL-CDU/Modular CDU", "ANORD-PDU/RPP"):
        assert f in families, f
    root = Path(x.FOLDER)
    for i in SPECS["items"]:
        assert i["verified"] is False and i["spec_id"].startswith("SPEC-")
        for a in i["attributes"]:
            assert a["quote"] and isinstance(a["page"], int) and (root / a["source"]["file"]).exists()
    assert len({i["spec_id"] for i in SPECS["items"]}) == len(SPECS["items"])


def test_unit_review_api():
    client = signed_in()
    rpp = client.get("/api/catalog/specs", params={"family": "ANORD-PDU/RPP"}).json()
    sid = rpp[0]["spec_id"]
    assert rpp and all(not s["verified"] for s in rpp)
    url = f"/api/catalog/specs/{sid}/review"
    assert client.post(url, json={"status": "confirmed"}).status_code == 403                          # bid manager
    assert client.post(url, json={"status": "confirmed"}, headers=auth("crown.pm")).status_code == 403  # another unit
    assert client.post(url, json={"status": "rejected"}, headers=auth("anord.de")).status_code == 422  # no note
    assert client.post(url, json={"status": "confirmed"}, headers=auth("anord.pm")).status_code == 200
    after = {s["spec_id"]: s for s in client.get("/api/catalog/specs", params={"family": "ANORD-PDU/RPP"}).json()}
    assert after[sid]["verified"] and after[sid]["review"]["by"] == "Anord Mardix Product Manager"
    detail = client.get("/api/catalog/product", params={"part": "ANORD-PDU/RPP"}).json()
    assert any(s["spec_id"] == sid and s["verified"] for s in detail["specs"])
    assert client.post("/api/catalog/specs/SPEC-nope/review", json={"status": "confirmed"}, headers=auth("anord.pm")).status_code == 404
