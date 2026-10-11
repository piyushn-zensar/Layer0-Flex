"""Regression tests for the pre-demo QA pass (findings QA-01, 03, 05, 06, 08, 09, 12, 15, 16 and B-14).

Run:  .venv\\Scripts\\python -m pytest -q tests/test_poc_pass.py
Uses a temporary store, so it never touches your local database (no model call: frozen answers only).
"""
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ["STORE_DIR"] = tempfile.mkdtemp()
os.environ["LLM_PROVIDER"] = "mock"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.db import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.changes import service as changes  # noqa: E402
from app.modules.decisions import service as decisions  # noqa: E402
from app.modules.requirements import service as requirements  # noqa: E402
from scripts import seed_demo  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RFP = ROOT / "data/RFP/RFP-2023-20-Switchgear-Procurement-Final.pdf"
OTHER_PDF = ROOT / "data/RFP/samples/rfp_hyperscale_campus.pdf"  # no frozen answer from the change agent
QUOTE = "Switchgear shall be Arc-resistant Type 2B."


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="module")
def seeded(client) -> str:
    """The quick 13-item Syracuse opportunity: frozen, go, dispatched, some answers validated."""
    seed_demo.main()
    return client.get("/api/portfolio").json()[0]["opp"]["id"]  # newest first


@pytest.fixture(scope="module")
def draft(client) -> str:
    """An opportunity in review (not frozen) with the Syracuse RFP read from its frozen layout."""
    opp = client.post("/api/opportunities", json={"title": "qa pass"}).json()["id"]
    r = client.post(f"/api/opportunities/{opp}/documents", files={"file": ("rfp.pdf", RFP.read_bytes())})
    assert r.status_code == 200 and r.json()["existing"] is False
    return opp


def _add(client, opp: str, n: int) -> list[str]:
    return [client.post(f"/api/opportunities/{opp}/requirements", json={"quote": QUOTE, "text": f"item {i}"}).json()["req_id"]
            for i in range(n)]


def test_parallel_reviews_do_not_fail_with_database_locked(client, draft):
    """QA-06: the bulk bar used to send every review at once; a burst of writes must all land (busy timeout + WAL)."""
    with engine.connect() as conn:  # the settings themselves: the test client's burst is gentler than 348 browser calls
        assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert conn.execute(text("PRAGMA busy_timeout")).scalar() == 30000
    ids = _add(client, draft, 120)
    with ThreadPoolExecutor(32) as pool:
        codes = list(pool.map(lambda r: client.post(f"/api/requirements/{r}/review", json={"action": "approve"}).status_code, ids))
    assert codes.count(200) == len(ids), {c: codes.count(c) for c in set(codes)}
    rows = {r["req_id"]: r for r in client.get(f"/api/opportunities/{draft}/requirements").json()["requirements"]}
    assert all(rows[r]["status"] == "approved" for r in ids)


def test_repeated_approve_records_one_event(client, draft):
    """QA-16: the same decision twice is one history event, not two."""
    (req,) = _add(client, draft, 1)
    for _ in range(2):
        assert client.post(f"/api/requirements/{req}/review", json={"action": "approve"}).status_code == 200
    actions = [e["action"] for e in client.get(f"/api/requirements/{req}/history").json()["events"]]
    assert actions == ["proposed", "approve"]
    # an edit that changes the wording is still recorded
    client.post(f"/api/requirements/{req}/review", json={"action": "edit", "text": "new wording"})
    assert [e["action"] for e in client.get(f"/api/requirements/{req}/history").json()["events"]][-1] == "edit"


def test_approving_a_rejected_item_or_group_restores_it(client, draft):
    """QA-03: a mis-click on Reject is undone with Approve; a restored group brings its sub-requirements back."""
    (req,) = _add(client, draft, 1)
    client.post(f"/api/requirements/{req}/review", json={"action": "reject"})
    assert client.post(f"/api/requirements/{req}/review", json={"action": "approve"}).json()["status"] == "approved"

    a, b = _add(client, draft, 2)
    with SessionLocal() as db:  # groups come from the grouping agent on the real seed; built directly here
        group = requirements._create_group(db, draft, [requirements.get(db, a), requirements.get(db, b)],
                                           "two items", "technical", "grouping agent (test)").req_id
        db.commit()
    client.post(f"/api/requirements/{group}/review", json={"action": "reject"})
    rows = {r["req_id"]: r["status"] for r in client.get(f"/api/opportunities/{draft}/requirements").json()["requirements"]}
    assert (rows[group], rows[a], rows[b]) == ("rejected", "rejected", "rejected")
    client.post(f"/api/requirements/{group}/review", json={"action": "approve"})
    rows = {r["req_id"]: r["status"] for r in client.get(f"/api/opportunities/{draft}/requirements").json()["requirements"]}
    assert (rows[group], rows[a], rows[b]) == ("approved", "approved", "approved")
    assert [e["action"] for e in client.get(f"/api/requirements/{group}/history").json()["events"]] == \
        ["grouped", "reject", "approve"]


def test_go_after_no_go_resumes_where_the_bid_stopped(client, seeded):
    """QA-16: a dispatched bid stopped with no_go and resumed with go is dispatched again, not back at go."""
    assert client.get(f"/api/opportunities/{seeded}").json()["opportunity"]["status"] == "dispatched"
    client.post(f"/api/opportunities/{seeded}/go-no-go", json={"outcome": "no_go", "rationale": "stop"})
    assert client.get(f"/api/opportunities/{seeded}").json()["opportunity"]["status"] == "no_go"
    client.post(f"/api/opportunities/{seeded}/go-no-go", json={"outcome": "go", "rationale": "resume"})
    assert client.get(f"/api/opportunities/{seeded}").json()["opportunity"]["status"] == "dispatched"


def test_unknown_opportunity_and_unit_are_404(client):
    """QA-08: pages for an unknown opportunity or unit must not render as if they existed."""
    for url in ("/api/opportunities/OPP-9999/requirements", "/api/opportunities/OPP-9999/decisions", "/api/inbox/NOPE"):
        assert client.get(url).status_code == 404, url
    assert client.get("/api/inbox/BID").status_code == 200


def test_reupload_of_the_same_file_says_so(client, draft):
    """QA-09: attaching the same file again adds nothing; the page gets a signal instead of a silent no-op."""
    before = client.get(f"/api/opportunities/{draft}").json()["documents"]
    r = client.post(f"/api/opportunities/{draft}/documents", files={"file": ("rfp.pdf", RFP.read_bytes())})
    assert r.status_code == 200 and r.json()["existing"] is True and r.json()["id"] == before[0]["id"]
    assert len(client.get(f"/api/opportunities/{draft}").json()["documents"]) == len(before)


def test_capacity_criterion_without_unit_work():
    """QA-12: no dispatched work yet is said in words, not an empty join."""
    ok, detail = decisions._capacity_criterion({"rows": []})
    assert ok and detail == "Open work vs capacity: no unit work yet. Capacity is a placeholder."


def test_offline_wording_for_missing_frozen_answers(client, seeded):
    """QA-01 / QA-15: when the frozen answers do not cover a call, the page says so in the audience's words."""
    # a change document with no frozen answer is refused, and no change set is created
    r = client.post(f"/api/opportunities/{seeded}/changes",
                    files={"file": (OTHER_PDF.name, OTHER_PDF.read_bytes(), "application/pdf")})
    assert r.status_code == 409 and r.json()["detail"] == str(changes._unavailable(OTHER_PDF.name))
    assert "offline demo" in r.json()["detail"] and "LLM_PROVIDER" not in r.json()["detail"]
    assert client.get(f"/api/opportunities/{seeded}/changes").json()["sets"] == []
    # validating one more answer changes the chapter's prompt: the outline keeps the raw answers with a plain note
    outline = client.get(f"/api/opportunities/{seeded}/response-outline").json()
    assert outline["summary"]["drafted"]
    submitted = [a for a in client.get("/api/inbox/CROWN").json()["items"]
                 if a["status"] == "submitted" and a["opportunity_id"] == seeded]
    assert submitted
    assert client.post(f"/api/assignments/{submitted[0]['id']}/validate", json={"ok": True}).status_code == 200
    outline = client.get(f"/api/opportunities/{seeded}/response-outline").json()
    assert outline["summary"]["drafted"] is False
    assert outline["summary"]["note"].startswith("Draft not refreshed: the model service is not connected")


def test_windows_scripts_match_install_notes():
    """QA-05 / B-14: the API keeps idle connections open longer than the web proxy reuses them; setup asks for
    the Python version INSTALL.md names, and a failing web build shows its error."""
    start, setup = (ROOT / "start.cmd").read_text("utf-8"), (ROOT / "setup.cmd").read_text("utf-8")
    assert "--timeout-keep-alive 75" in start
    assert "sys.version_info < (3, 12)" in setup and "3.11" not in setup
    assert "call npm run build ||" in setup
