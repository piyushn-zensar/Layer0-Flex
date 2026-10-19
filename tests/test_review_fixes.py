"""Fixes from the 19 Oct 2026 system review (client demo feedback of 16 Oct and the code review). Each test reproduces
one reported error first, so it failed before its fix. Atharv, with the owners' agreement ([contract] Piyush, Janvia)."""
import os
import tempfile

os.environ["STORE_DIR"] = tempfile.mkdtemp()
os.environ["LLM_PROVIDER"] = "mock"

import pytest  # noqa: E402
from conftest import auth, signed_in  # noqa: E402

from app.core.db import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402,F401
from app.modules.opportunities import service as opportunities  # noqa: E402
from scripts import seed_demo  # noqa: E402


@pytest.fixture(scope="module")
def opp():
    seed_demo.main()  # the 13-item Syracuse bid: frozen, matched, dispatched
    return signed_in().get("/api/portfolio").json()[0]["opp"]["id"]


def test_unknown_bid_is_404_everywhere(opp):
    client, ep2 = signed_in(), auth("ep2.pm")
    assert client.post("/api/bids/OPP-9999/dispatch").status_code == 404
    assert client.put("/api/bids/OPP-9999/units/EP2/completion", json={"estimated_completion": "2026-11-01"}, headers=ep2).status_code == 404
    assert client.get("/api/bids/OPP-9999/assessments").status_code == 404
    assert client.get("/api/bids/OPP-9999/knowledge").status_code == 404


def test_out_of_range_input_is_rejected_not_a_500(opp):
    client = signed_in()
    req_id = client.get(f"/api/bids/{opp}/trace").json()["rows"][0]["req"]["req_id"]
    assert client.post(f"/api/bids/{opp}/comments", json={"req_id": req_id, "text": "x", "assignment_id": 2**70}).status_code == 422
    for ref in ("9" * 30, "²"):
        assert client.post("/api/knowledge", json={"kind": "response", "ref": ref}).status_code in (404, 422), ref
    assert client.get(f"/api/bids/{opp}/assessments", params={"run": 10**20}).status_code == 422
    item = next(r["req"]["req_id"] for r in client.get(f"/api/bids/{opp}/trace").json()["rows"] if r["req"]["kind"] == "item")
    r = client.post(f"/api/bids/{opp}/corrections", json={"kind": "split", "reason": "r", "req_id": item, "parts": [{"quote": 5}, {"quote": 6}]})
    assert r.status_code in (409, 422), r.text


def test_document_type_is_checked_on_upload(opp):
    client = signed_in()
    fresh = client.post("/api/bids", json={"title": "role check"}).json()["id"]
    r = client.post(f"/api/bids/{fresh}/documents", data={"role": "bogus"}, files={"file": ("x.pdf", b"%PDF-1.4 bogus")})
    assert r.status_code == 422 and client.get(f"/api/bids/{fresh}").json()["documents"] == []


def test_a_stopped_bid_does_not_move_forward():
    with SessionLocal() as db:
        o = opportunities.create(db, "stopped", "", "", "Bid Manager").id
        opportunities.set_status(db, o, "frozen", "t")
        assert opportunities.set_status(db, o, "no_go", "t")
        assert opportunities.set_status(db, o, "consolidating", "t") is False  # only a go resumes a no-go
        assert opportunities.get(db, o).status == "no_go"


def test_a_failed_change_upload_leaves_no_document(opp):
    client = signed_in()
    seed_demo.independent()  # Logan: frozen; the Syracuse addendum has no frozen change-agent answers for it
    logan = client.get("/api/portfolio").json()[0]["opp"]["id"]
    r = client.post(f"/api/bids/{logan}/changes/from-sample", json={"name": "syracuse_addendum_1"})
    assert r.status_code == 409
    assert [d["role"] for d in client.get(f"/api/bids/{logan}").json()["documents"]] == ["main"]


def test_a_read_interrupted_by_a_restart_is_retried():
    with SessionLocal() as db:
        o = opportunities.create(db, "interrupted", "", "", "Bid Manager").id
        doc = opportunities.add_document(db, o, "rfp.pdf", b"%PDF-1.4 interrupted", "other", "Bid Manager")
        opportunities.set_document_status(db, doc.id, "ingesting")  # the API stopped while reading it
        assert opportunities.reset_interrupted_reads(db) >= 1
        assert opportunities.get_document(db, doc.id).status == "uploaded"  # the next upload or start reads it again


def _held(client, opp, test):
    return next(a for r in client.get(f"/api/bids/{opp}/trace").json()["rows"] for a in r["assignments"] if test(r, a))


def test_reopened_work_does_not_show_the_old_answer_as_current(opp):
    client, bm = signed_in(), auth("bid.manager")
    a = _held(client, opp, lambda r, a: a["bu"] == "CROWN" and a["status"] == "assigned" and r["req"]["category"] == "technical")
    client.post(f"/api/assignments/{a['id']}/respond", json={"compliance": "met", "response": "ok"}, headers=auth("crown.de"))
    client.post(f"/api/assignments/{a['id']}/validate", json={"ok": True}, headers=auth("crown.pm"))
    units = client.get(f"/api/bids/{opp}/decisions").json()["participation"]["units"]
    client.post(f"/api/bids/{opp}/participation", json={"units": [u for u in units if u != "CROWN"]}, headers=bm)
    client.post(f"/api/bids/{opp}/dispatch", headers=bm)  # CROWN's work withdrawn
    client.post(f"/api/bids/{opp}/participation", json={"units": units}, headers=bm)
    client.post(f"/api/bids/{opp}/dispatch", headers=bm)  # reopened
    again = next(x for x in client.get("/api/inbox/CROWN").json()["items"] if x["id"] == a["id"])
    assert (again["status"], again["compliance"], again["validated_by"]) == ("assigned", None, None)


def test_needs_an_owner_counts_agree_before_participation():
    from app.modules.matching import service as matching
    from app.modules.workpackages import service as workpackages
    seed_demo.independent()  # Logan: frozen, no participation yet
    client = signed_in()
    logan = client.get("/api/portfolio").json()[0]["opp"]["id"]
    with SessionLocal() as db:
        matching.match(db, logan, "test")
        owners = {o["req_id"] for o in workpackages.needs_owner(db, logan)}
    shown = {o["req_id"] for o in client.get(f"/api/bids/{logan}/assessment").json()["open_questions"]["needs_owner"]}
    assert owners == shown


def test_a_returned_capability_gap_survives_the_next_dispatch(opp):
    client, bm = signed_in(), auth("bid.manager")
    # the test makes its own product item without a unit (a person's "no unit"): what matching leaves unowned
    # depends on the knowledge earlier tests approved
    req = next(r for r in client.get(f"/api/bids/{opp}/requirements").json()["requirements"]
               if r["category"] == "technical" and r["status"] == "approved" and not r.get("parent_id"))
    assert client.post(f"/api/bids/{opp}/requirements/{req['req_id']}/match", json={"units": []}, headers=bm).status_code == 200
    gap = next(o for o in client.get(f"/api/bids/{opp}/needs-owner").json() if o["req_id"] == req["req_id"])
    client.post(f"/api/bids/{opp}/requirements/{gap['req_id']}/capability-gap", json={"reason": "no unit"}, headers=bm)
    a = _held(client, opp, lambda r, a: r["req"]["req_id"] == gap["req_id"] and a["bu"] == "BID")
    assert client.post(f"/api/assignments/{a['id']}/validate", json={"ok": False, "note": "Really none?"}, headers=bm).status_code == 200
    client.post(f"/api/bids/{opp}/dispatch", headers=bm)
    after = _held(client, opp, lambda r, x: x["id"] == a["id"])
    assert after["status"] == "returned"


def test_non_technical_unit_answers_are_validated_by_the_bid_manager(opp):
    client = signed_in()
    a = _held(client, opp, lambda r, a: a["bu"] == "CROWN" and a["status"] == "assigned" and r["req"]["category"] in ("commercial", "schedule", "staffing"))
    pm = auth("crown.pm")
    assert client.post(f"/api/assignments/{a['id']}/respond", json={"compliance": "met", "response": "week 30"}, headers=pm).status_code == 200
    assert client.post(f"/api/assignments/{a['id']}/validate", json={"ok": True}, headers=pm).status_code == 403  # not their own answer
    assert client.post(f"/api/assignments/{a['id']}/validate", json={"ok": True}, headers=auth("bid.manager")).status_code == 200


def test_a_non_compliant_schedule_answer_beats_the_dates():
    from app.modules.decisions import service as decisions
    ok = [type("A", (), {"compliance": "not_met"})()]
    assert decisions._schedule_criterion(["R1"], {"R1": ok})[0] == "not_met"  # and _schedule returns it before the dates


def test_lines_already_in_the_register_are_not_added_twice_and_an_incomplete_read_can_be_frozen(monkeypatch):
    from app.modules.requirements import service as requirements
    client, bm = signed_in(), auth("bid.manager")
    pdf = (seed_demo.config.ROOT / "data/RFP/RFP-2023-20-Switchgear-Procurement-Final.pdf").read_bytes()
    monkeypatch.setattr(requirements, "read_complete", lambda coverage: False)  # as if a chunk had failed
    o = client.post("/api/bids", json={"title": "incomplete"}).json()["id"]
    client.post(f"/api/bids/{o}/documents", files={"file": ("rfp.pdf", pdf)})
    assert client.post(f"/api/bids/{o}/requirements/extract").json()["frozen"] is None
    lines = {"page": 55, "line_start": 14, "line_end": 14, "category": "technical"}
    assert client.post(f"/api/bids/{o}/requirements/from-lines", json=lines).status_code == 200
    assert client.post(f"/api/bids/{o}/requirements/from-lines", json=lines).status_code == 409  # already in the register
    for _ in range(requirements.MAX_REREADS):  # re-reads are allowed although a correction was made
        assert client.post(f"/api/bids/{o}/requirements/extract", json={"reason": "retry"}).status_code == 200
    assert client.post(f"/api/bids/{o}/requirements/extract", json={"reason": "again"}).status_code == 409
    assert client.post(f"/api/bids/{o}/requirements/freeze", json={"reason": "x"}, headers=auth("crown.pm")).status_code == 403
    assert client.post(f"/api/bids/{o}/requirements/freeze", json={"reason": "page 12 is a scan"}, headers=bm).json()["number"] == 1
