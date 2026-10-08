"""Smoke test: the demo flow runs through every module and every screen renders.

Run:  .venv\\Scripts\\python -m pytest -q
Uses a temporary store, so it never touches your local database.
"""
import os
import re
import tempfile
from pathlib import Path

os.environ["STORE_DIR"] = tempfile.mkdtemp()
os.environ["LLM_PROVIDER"] = "mock"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.db import engine  # noqa: E402
from app.main import app  # noqa: E402
from scripts import seed_demo  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def test_demo_flow_and_api():
    seed_demo.main()
    client = TestClient(app)
    for url in ["/api/portfolio", "/api/people", "/api/opportunities/OPP-0001",
                "/api/opportunities/OPP-0001/requirements", "/api/opportunities/OPP-0001/trace",
                "/api/opportunities/OPP-0001/decisions", "/api/opportunities/OPP-0001/consolidation",
                "/api/opportunities/OPP-0001/changes", "/api/inbox/CROWN", "/api/inbox/EP2", "/api/inbox/BID",
                "/api/catalog?q=relay"]:
        assert client.get(url).status_code == 200, url
    trace = client.get("/api/opportunities/OPP-0001/trace").json()
    by_id = {r["req"]["req_id"]: r for r in trace["rows"]}
    assert by_id["REQ-0001-0006"]["req"]["source"].startswith("p. 55")
    assert by_id["REQ-0001-0002"]["unit"]["code"] == "EP2"
    assert client.get(f"/api/documents/{trace['doc']['id']}/pages/55.png").headers["content-type"] == "image/png"
    csv = client.get("/api/opportunities/OPP-0001/compliance-matrix.csv").text
    assert "p. 55, lines" in csv

    # actor header is URL-encoded by the web app (EP² is not ASCII)
    a = next(i for i in client.get("/api/inbox/EP2").json()["items"] if not i["responded_by"])
    r = client.post(f"/api/assignments/{a['id']}/respond", json={"compliance": "met", "response": "ok"},
                    headers={"X-Actor": "EP%C2%B2%20Design%20Engineer"})
    assert r.status_code == 200
    after = {i["id"]: i for i in client.get("/api/inbox/EP2").json()["items"]}
    assert after[a["id"]]["responded_by"] == "EP² Design Engineer"

    with pytest.raises(Exception, match="append-only"):  # rule R8
        with engine.begin() as conn:
            conn.execute(text("UPDATE audit_event SET actor = 'someone else'"))


def test_modules_talk_only_through_services():
    """Modular-monolith rule: module A may import module B's service.py, never its models/agent/controller."""
    for f in (ROOT / "app" / "modules").rglob("*.py"):
        own = f.relative_to(ROOT / "app" / "modules").parts[0]
        for mod, part in re.findall(r"app\.modules\.(\w+)\.(\w+)", f.read_text("utf-8")):
            assert mod == own or part == "service", f"{f.name} imports app.modules.{mod}.{part}"


def test_people_decide_and_dispatch_needs_go():
    """Rule R4: re-running matching keeps people's decisions; dispatch needs a go; bad input is refused.
    Appended by Atharv (append-only on this shared file)."""
    seed_demo.main()  # its own opportunity, so this test does not depend on test order
    client = TestClient(app)
    opp = client.get("/api/portfolio").json()[0]["opp"]["id"]  # newest first
    rows = client.get(f"/api/opportunities/{opp}/trace").json()["rows"]
    rejected, accepted = rows[0]["match"], rows[1]["match"]
    assert client.post(f"/api/matches/{rejected['id']}/decide", json={"action": "reject"}).status_code == 200
    assert client.post(f"/api/matches/{accepted['id']}/decide", json={"action": "accept"}).status_code == 200
    assert client.post(f"/api/opportunities/{opp}/match").json()["kept"] == 2
    after = {r["req"]["req_id"]: r["match"] for r in client.get(f"/api/opportunities/{opp}/trace").json()["rows"]}
    assert after[rejected["req_id"]] is None  # stays rejected: no older proposal comes back
    assert after[accepted["req_id"]]["id"] == accepted["id"] and after[accepted["req_id"]]["status"] == "accepted"

    a = client.get("/api/inbox/CROWN").json()["items"][0]
    assert client.post(f"/api/matches/{accepted['id']}/decide", json={"action": "maybe"}).status_code == 422
    assert client.post("/api/matches/999999/decide", json={"action": "accept"}).status_code == 404
    assert client.post(f"/api/assignments/{a['id']}/respond", json={"compliance": "yes"}).status_code == 422
    assert client.post("/api/assignments/999999/respond", json={"compliance": "met"}).status_code == 404
    assert client.post(f"/api/opportunities/{opp}/go-no-go", json={"outcome": "maybe"}).status_code == 422
    assert client.get(f"/api/opportunities/{opp}/decisions").json()["go_no_go"]["outcome"] == "go"

    client.post(f"/api/opportunities/{opp}/go-no-go", json={"outcome": "no_go"})
    assert client.post(f"/api/opportunities/{opp}/dispatch").status_code == 409
    assert client.get(f"/api/opportunities/{opp}").json()["opportunity"]["status"] == "no_go"
