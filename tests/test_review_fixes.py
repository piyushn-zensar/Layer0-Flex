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
