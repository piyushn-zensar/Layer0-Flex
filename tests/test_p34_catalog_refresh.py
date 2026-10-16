"""P-34 (C-28): the published catalog is read from the official pages (no network here: pages are stubbed), stored
with source and time; a renamed product keeps its earlier name; a failed page keeps the last good records; robots.txt
is honoured; the matcher's prompt (curated catalog) does not change."""
import os
import tempfile

os.environ["STORE_DIR"] = tempfile.mkdtemp()

from conftest import auth, signed_in  # noqa: E402

PAGE = """<html><nav><h3>Menu</h3></nav><h2>Critical Power</h2>
<h3>{name}</h3><p>Key features:</p><ul><li>Available in UL and IEC</li><li>Two busway designs</li></ul>
<p><a href="https://anordmardix.com/products/databar/">View DATABARs</a></p>
<h3>MV switchgear</h3><ul><li>Up to 38 kV</li></ul><p><a href="https://crowntechnicalsystems.com/products/switchgear">View</a></p>
</html>"""


def test_refresh_versions_and_failures(monkeypatch):
    import httpx

    from app.core.db import SessionLocal
    from app.modules.catalog import scrape
    from app.modules.catalog import service as catalog
    from app.modules.matching import agent

    signed_in()
    pages = [("https://flex.com/products/power-and-cooling", "flex", None)]
    served = {"name": "DATABAR", "fail": False}

    def fetch(url):
        if url.endswith("/robots.txt"):
            return "User-agent: *\nDisallow: /wp-admin/\n"
        if served["fail"]:
            raise httpx.ConnectError("offline")
        return PAGE.format(name=served["name"])
    monkeypatch.setattr(scrape, "fetch", fetch)
    prompt_before = agent.catalog_text(catalog.products(), catalog.past_responses())

    with SessionLocal() as db:
        run = catalog.refresh(db, "test", pages)
        assert (run.status, run.added) == ("ok", 2) and run.sources[0]["sha256"]
        found = {p["name"]: p for p in catalog.published(db)["products"]}
        assert set(found) == {"DATABAR", "MV switchgear"}  # the menu heading has no features or link: not a product
        assert found["DATABAR"]["bu"] == "ANORD" and found["MV switchgear"]["bu"] == "CROWN"
        assert found["DATABAR"]["features"] == ["Available in UL and IEC", "Two busway designs"]
        assert found["DATABAR"]["category"] == "Critical Power" and found["DATABAR"]["source_url"] == pages[0][0]

        served["name"] = "DATABAR Plus"  # renamed on the page: same link, new version, old name kept
        run = catalog.refresh(db, "test", pages)
        assert (run.added, run.changed) == (0, 1)
        renamed = next(p for p in catalog.published(db)["products"] if p["key"].endswith("/databar"))
        assert renamed["name"] == "DATABAR Plus" and renamed["earlier_names"] == ["DATABAR"] and renamed["version"] == 2
        assert [v.name for v in catalog.versions(db, renamed["key"])] == ["DATABAR", "DATABAR Plus"]

        served["fail"] = True  # the page cannot be read: the run says so, the products stay as they were
        run = catalog.refresh(db, "test", pages)
        assert run.status == "failed" and "offline" in run.sources[0]["error"]
        assert {p["name"] for p in catalog.published(db)["products"] if p["active"]} == {"DATABAR Plus", "MV switchgear"}

        monkeypatch.setattr(scrape, "allowed", lambda url: False)  # robots.txt says no: nothing is fetched
        run = catalog.refresh(db, "test", pages)
        assert run.sources[0]["status"] == "skipped"

    assert agent.catalog_text(catalog.products(), catalog.past_responses()) == prompt_before  # frozen answers stay valid
    client = signed_in()
    assert client.get("/api/catalog/published").json()["catalog_version"]
    assert client.post("/api/catalog/refresh", headers=auth("crown.pm")).status_code == 403
