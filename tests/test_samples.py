"""Sample routes: the walkthrough's "Use example" path attaches a bundled sample document through the same code as
an upload (same JSON, same status transitions, same audit), so what the walkthrough shows is what a file upload does.

Run:  .venv\\Scripts\\python -m pytest -q tests/test_samples.py
"""
import os
import tempfile

os.environ["STORE_DIR"] = tempfile.mkdtemp()
os.environ["LLM_PROVIDER"] = "mock"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.modules.opportunities import service as opportunities  # noqa: E402
from scripts import seed_demo  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_samples_are_listed_without_paths(client):
    listed = client.get("/api/samples").json()["samples"]
    by_name = {s["name"]: s for s in listed}
    assert set(by_name) == {"syracuse_rfp", "hyperscale_rfp", "syracuse_addendum_1"} == set(opportunities.SAMPLES)
    assert by_name["syracuse_rfp"]["pages"] == 101 and by_name["syracuse_rfp"]["kind"] == "rfp"
    assert by_name["syracuse_addendum_1"]["kind"] == "change"
    for s in listed:
        assert "path" not in s and s["filename"].endswith(".pdf") and s["description"]


def test_sample_rfp_is_read_and_extracted_from_frozen_answers(client):
    """A new opportunity reads the Syracuse RFP from the sample route: the document JSON is the upload's, the file is
    read (101 pages) and the reader agent's frozen answers extract the requirements offline."""
    opp = client.post("/api/opportunities", json={"title": "Walkthrough: Syracuse switchgear"}).json()["id"]
    r = client.post(f"/api/opportunities/{opp}/documents/from-sample", json={"name": "syracuse_rfp"})
    assert r.status_code == 200, r.text
    doc = r.json()
    assert doc["opportunity_id"] == opp and doc["role"] == "main" and doc["existing"] is False
    assert doc["filename"] == "RFP-2023-20-Switchgear-Procurement-Final.pdf" and "path" not in doc
    assert doc["status"] in ("uploaded", "ingested")  # the answer comes before the reading, as for an upload
    stored = client.get(f"/api/opportunities/{opp}").json()["documents"]
    assert [d["id"] for d in stored] == [doc["id"]]
    assert stored[0]["status"] == "ingested" and stored[0]["page_count"] == 101
    # the same sample again: nothing new is added, the page can say so
    again = client.post(f"/api/opportunities/{opp}/documents/from-sample", json={"name": "syracuse_rfp"}).json()
    assert again["id"] == doc["id"] and again["existing"] is True
    # a second main RFP is refused like an upload would be
    r = client.post(f"/api/opportunities/{opp}/documents/from-sample", json={"name": "hyperscale_rfp"})
    assert r.status_code == 409 and "already has a main RFP" in r.json()["detail"]

    read = client.post(f"/api/opportunities/{opp}/requirements/extract")
    assert read.status_code == 200, read.text
    assert read.json()["requirements"] > 300 and not read.json()["problems"]
    assert client.get(f"/api/opportunities/{opp}").json()["opportunity"]["status"] == "review"


def test_sample_addendum_on_the_demo_opportunity(client):
    """The addendum sample goes through changes.upload like a file: read and classified from frozen answers."""
    seed_demo.main()  # its own opportunity: frozen, go, dispatched
    opp = client.get("/api/portfolio").json()[0]["opp"]["id"]
    r = client.post(f"/api/opportunities/{opp}/changes/from-sample", json={"name": "syracuse_addendum_1"})
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["status"] == "review" and s["filename"] == "rfp_syracuse_addendum_1.pdf" and s["items"]
    assert {i["proposed_kind"] for i in s["items"]} & {"modified", "added", "removed"}
    assert client.get(f"/api/opportunities/{opp}/changes").json()["sets"][0]["id"] == s["id"]
    assert {d["role"] for d in client.get(f"/api/opportunities/{opp}").json()["documents"]} == {"main", "change"}


def test_sample_errors(client):
    opp = client.post("/api/opportunities", json={"title": "no documents yet"}).json()["id"]
    assert client.post("/api/opportunities/OPP-9999/documents/from-sample", json={"name": "syracuse_rfp"}).status_code == 404
    assert client.post("/api/opportunities/OPP-9999/changes/from-sample", json={"name": "syracuse_addendum_1"}).status_code == 404
    for route, name in [("documents", "nope"), ("changes", "nope"),
                        ("documents", "syracuse_addendum_1"), ("changes", "syracuse_rfp")]:  # unknown, wrong kind
        r = client.post(f"/api/opportunities/{opp}/{route}/from-sample", json={"name": name})
        assert r.status_code == 409, (route, name, r.text)
    # a change document needs a frozen baseline, as for an upload
    r = client.post(f"/api/opportunities/{opp}/changes/from-sample", json={"name": "syracuse_addendum_1"})
    assert r.status_code == 409 and "Freeze the requirements first" in r.json()["detail"]
    assert client.get(f"/api/opportunities/{opp}").json()["documents"] == []  # nothing was stored
