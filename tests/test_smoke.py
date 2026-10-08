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

    # rule R6: the same file in a second opportunity is that opportunity's own document
    opp2 = client.post("/api/opportunities", json={"title": "second"}).json()["id"]
    pdf = (ROOT / "data/RFP/RFP-2023-20-Switchgear-Procurement-Final.pdf").read_bytes()
    doc2 = client.post(f"/api/opportunities/{opp2}/documents", files={"file": ("rfp.pdf", pdf)}).json()
    assert doc2["opportunity_id"] == opp2 and doc2["id"] != trace["doc"]["id"]
    assert client.get(f"/api/opportunities/{opp2}").json()["documents"][0]["status"] == "ingested"

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


def test_requirement_review_actions():
    """P-06: edit, split, merge, add missed; freeze needs every line item decided; replaced items leave the flow."""
    client = TestClient(app)
    opp = client.post("/api/opportunities", json={"title": "review actions"}).json()["id"]
    pdf = (ROOT / "data/RFP/RFP-2023-20-Switchgear-Procurement-Final.pdf").read_bytes()
    client.post(f"/api/opportunities/{opp}/documents", files={"file": ("rfp.pdf", pdf)})
    assert client.post(f"/api/opportunities/{opp}/requirements/extract").json()["proposed"] > 100  # frozen GPT-4o answers
    reqs = {r["req_id"]: r for r in client.get(f"/api/opportunities/{opp}/requirements").json()["requirements"]}
    p55 = [r for r in reqs.values() if r["page"] == 55 and r["provenance"] == "EXTRACTED"]

    edited = client.post(f"/api/requirements/{p55[0]['req_id']}/review",
                         json={"action": "edit", "text": "Edited text", "category": "schedule"}).json()
    assert (edited["text"], edited["category"]) == ("Edited text", "schedule")
    assert client.post(f"/api/requirements/{p55[0]['req_id']}/review", json={"action": "edit", "category": "nope"}).status_code == 409

    q = p55[1]["quote"]
    half = q.rfind(" ", 0, len(q) // 2)
    parts = client.post(f"/api/requirements/{p55[1]['req_id']}/split",
                        json={"parts": [{"quote": q[:half]}, {"quote": q[half + 1:]}]}).json()
    assert len(parts) == 2 and all(p["provenance"] == "EXTRACTED" and p["derived_from"] == [p55[1]["req_id"]] for p in parts)

    merged = client.post(f"/api/opportunities/{opp}/requirements/merge",
                         json={"req_ids": [p55[2]["req_id"], p55[3]["req_id"]], "text": "One obligation"}).json()
    assert merged["derived_from"] == [p55[2]["req_id"], p55[3]["req_id"]] and merged["provenance"] == "EXTRACTED"
    assert client.post(f"/api/requirements/{p55[2]['req_id']}/split",
                       json={"parts": [{"quote": "a"}, {"quote": "b"}]}).status_code == 409  # already merged

    missed = client.post(f"/api/opportunities/{opp}/requirements",
                         json={"quote": "Each phase shall have 1 inch diameter ground ball.", "category": "technical", "page": 55}).json()
    assert missed["provenance"] == "EXTRACTED" and missed["page"] == 55

    assert client.post(f"/api/opportunities/{opp}/baselines").status_code == 409  # undecided items left
    rows = client.get(f"/api/opportunities/{opp}/requirements").json()["requirements"]
    for r in rows:
        if r["status"] == "proposed":
            client.post(f"/api/requirements/{r['req_id']}/review", json={"action": "approve"})
    assert client.post(f"/api/opportunities/{opp}/baselines").status_code == 200
    statuses = {r["req_id"]: r["status"] for r in client.get(f"/api/opportunities/{opp}/requirements").json()["requirements"]}
    assert statuses[p55[1]["req_id"]] == "split" and statuses[p55[2]["req_id"]] == "merged"
    trace_ids = {r["req"]["req_id"] for r in client.get(f"/api/opportunities/{opp}/trace").json()["rows"]}
    assert p55[1]["req_id"] not in trace_ids and merged["req_id"] in trace_ids  # replaced items leave the flow
