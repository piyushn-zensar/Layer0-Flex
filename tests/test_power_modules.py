"""P-53 (C-52 to C-54): the Flex Power Modules spreadsheet merged into the catalog, and the product table / detail API
(contract: team/PLAN.md 12.3)."""
import json
import os
import tempfile

os.environ.setdefault("STORE_DIR", tempfile.mkdtemp())

from conftest import signed_in  # noqa: E402

from scripts import import_power_modules as imp  # noqa: E402

WEB = json.loads(imp.WEB.read_text("utf-8"))["items"]


def _row(pn="BMR3161011/021", series="BMR316", power=1000, eff=97.7, vin=(38, 60), compat=None) -> tuple:
    r = [None] * 40
    r[:6] = [4, pn, "Power Modules", "Active", series, compat]
    if power is not None:
        r[8], r[9], r[10], r[11], r[12], r[15] = vin[0], vin[1], 9.5, 15, power, eff
    r[7], r[32] = "PMBus and GCB", "Telecom,Data Center and Cloud"
    return tuple(r)


def test_import_fields_boards_and_links():
    out = imp.build([_row(), _row("BMR316 Evaluation Board", "ROA170286", power=None, compat="BMR316")], {}, WEB, "2026-10-22")
    part, board = (next(i for i in out["items"] if i["product_type"] == t) for t in ("power_module", "evaluation_board"))
    assert part["series"] == "BMR316" and part["product_line"] == "Power Modules"        # the two Series columns
    assert part["family_key"] == "FPM-DCDC/BMR316" and part["web"]["source_url"].endswith("bmr316")
    assert part["interfaces"] == ["PMBus", "GCB"] and part["application"] == ["Telecom", "Data Center and Cloud"]
    assert part["current_a"] is None and part["imported"]["power_w"] == "2026-10-22"     # empty = unknown, not 0
    assert board["evaluates"] == ["BMR316"] and board["power_w"] is None and board["family_key"] == "FPM-DCDC/BMR316"


def test_repeat_import_empty_cell_and_conflict():
    first = imp.build([_row()], {}, WEB, "2026-10-22")
    old = {i["part_number"]: i for i in first["items"]}
    # same file again: no duplicate, nothing re-dated
    again = imp.build([_row()], old, WEB, "2026-10-30")
    assert again["items"] == first["items"]
    # an emptied cell keeps the earlier value; a changed value is re-dated and checked against the web page (2.8 kW peak)
    later = imp.build([_row(power=3000, eff=None)], old, WEB, "2026-11-05")["items"]
    assert len(later) == 1 and later[0]["efficiency_pct"] == 97.7 and later[0]["imported"]["efficiency_pct"] == "2026-10-22"
    assert later[0]["power_w"] == 3000 and later[0]["imported"]["power_w"] == "2026-11-05"
    assert [c["field"] for c in later[0]["conflicts"]] == ["power_w"] and later[0]["conflicts"][0]["web"] == 2800
    # a part missing from a later file stays, marked
    gone = imp.build([_row("BMR3161011/022")], old, WEB, "2026-11-05")["items"]
    assert {i["part_number"]: i["in_last_import"] for i in gone} == {"BMR3161011/021": False, "BMR3161011/022": True}


def test_committed_import_matches_the_spreadsheet():
    from app.modules.catalog import service as catalog
    items = catalog.power_modules()
    assert len(items) == len({i["part_number"] for i in items}) == 721
    assert sum(i["product_type"] == "evaluation_board" for i in items) == 27
    assert all(i["power_w"] is None for i in items if i["product_type"] == "evaluation_board")


def test_product_table_and_detail_api():
    client = signed_in()
    page = client.get("/api/catalog/products", params={"size": 10}).json()
    assert page["total"] == 721 + len(WEB) and len(page["items"]) == 10
    boards = client.get("/api/catalog/products", params={"type": "evaluation_board"}).json()
    assert boards["total"] == 27 and all(r["power_w"] is None for r in boards["items"])
    top = client.get("/api/catalog/products", params={"sort": "power_w", "dir": "desc", "size": 3}).json()["items"]
    assert top[0]["power_w"] >= top[1]["power_w"] >= top[2]["power_w"]
    last = client.get("/api/catalog/products", params={"sort": "power_w", "page": 4, "size": 200}).json()["items"]
    assert last[-1]["power_w"] is None                                   # unknown values sort last
    assert client.get("/api/catalog/products", params={"sort": "nope"}).status_code == 422
    assert client.get("/api/catalog/products", params={"q": "bmr492"}).json()["total"] == 20   # 19 parts + web series
    flagged = client.get("/api/catalog/products", params={"q": "BMR4920311/011"}).json()["items"][0]
    assert flagged["has_conflict"] and flagged["source"] == "both"

    part = client.get("/api/catalog/product", params={"part": "BMR3161011/021"}).json()
    assert part["family_key"] == "FPM-DCDC/BMR316" and [v["key"] for v in part["variants"]] == ["BMR316 Evaluation Board"]
    series = client.get("/api/catalog/product", params={"part": "FPM-DCDC/BMR316"}).json()
    assert series["product_type"] == "web_listing" and len(series["variants"]) == 6
    mdx = client.get("/api/catalog/product", params={"part": "ANORD-LVSB/MDX"}).json()
    assert any(d["file"] == "MDX-Switchgear-Catalog_2026.pdf" for d in mdx["documents"])
    assert client.get("/api/catalog/product", params={"part": "NOPE"}).status_code == 404
