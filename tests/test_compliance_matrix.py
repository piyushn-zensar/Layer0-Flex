"""J-11 phase 1: GET /api/bids/{id}/compliance-matrix, the rows behind the Compliance matrix screen.

Run:  .venv\\Scripts\\python -m pytest -q tests/test_compliance_matrix.py
Uses a temporary store, so it never touches your local database (no model call: frozen answers only).
"""
import os
import tempfile
from types import SimpleNamespace

os.environ["STORE_DIR"] = tempfile.mkdtemp()
os.environ["LLM_PROVIDER"] = "mock"

from conftest import signed_in  # noqa: E402

from app.core.db import SessionLocal  # noqa: E402
from app.modules.consolidation import service  # noqa: E402
from app.modules.workpackages.models import Assignment  # noqa: E402
from scripts import seed_demo  # noqa: E402

ROW_KEYS = {"req_id", "requirement", "quote", "category", "state", "source", "document_id", "page", "line_start",
            "line_end", "spans", "assignments", "unit", "unit_name", "product", "offering_type",
            "assignment_id", "status", "compliance", "compliance_label", "response", "responded_by", "validated_by",
            "validation_note", "reason", "conditions", "workaround", "next_steps"}


def _seeded():
    seed_demo.main()  # the 13-item Syracuse seed: dispatched, some answers submitted or validated
    client = signed_in()
    opp = client.get("/api/portfolio").json()[0]["opp"]["id"]
    return client, opp


def test_matrix_response_shape_and_unknown_bid():
    client, opp = _seeded()
    assert client.get("/api/bids/OPP-9999/compliance-matrix").status_code == 404
    res = client.get(f"/api/bids/{opp}/compliance-matrix")
    assert res.status_code == 200
    data = res.json()
    assert set(data) == {"rows", "total", "answered", "blocking"} and data["total"] == 13
    assert data["answered"] == 13 - len(data["blocking"]) and len(data["rows"]) == 13
    assert all(set(r) == ROW_KEYS for r in data["rows"])
    places = [(r["page"], r["line_start"]) for r in data["rows"]]
    assert places == sorted(places)  # RFP order: by page, then line
    met = next(r for r in data["rows"] if r["compliance"] == "met")
    assert met["compliance_label"] == "Fully compliant" and met["unit_name"]
    open_row = next(r for r in data["rows"] if r["compliance"] is None)
    assert open_row["compliance_label"] == "" and open_row["status"] == "assigned"


def test_a18_fields_are_empty_before_a18_and_read_when_present():
    client, opp = _seeded()
    for r in client.get(f"/api/bids/{opp}/compliance-matrix").json()["rows"]:
        assert all(r[f] is None for f in service.EXTENDED) or r["compliance"] in ("partial", "not_met")  # after A-18
    bare = SimpleNamespace(id=1, status="submitted", compliance="partial", response="Lead time 14 weeks")  # no A-18 fields
    out = service._response_fields(bare)
    assert out["compliance_label"] == "Partially compliant" and all(out[f] is None for f in service.EXTENDED)
    full = SimpleNamespace(id=2, status="submitted", compliance="not_met", reason="No 38 kV design", conditions="",
                           workaround="Offer 27 kV", next_steps="Ask the customer")
    out = service._response_fields(full)
    assert (out["reason"], out["workaround"], out["next_steps"]) == ("No 38 kV design", "Offer 27 kV", "Ask the customer")
    assert out["conditions"] is None  # blank stays "not provided", never a made-up text
    none = service._response_fields(None)  # a requirement nobody holds
    assert none["assignment_id"] is None and none["compliance_label"] == "" and none["response"] == ""


def test_source_metadata_points_at_the_page_and_boxes():
    client, opp = _seeded()
    main = client.get(f"/api/bids/{opp}").json()["documents"][0]["id"]
    rows = client.get(f"/api/bids/{opp}/compliance-matrix").json()["rows"]
    for r in rows:
        assert r["document_id"] == main and isinstance(r["page"], int) and r["source"].startswith("p. ")
        assert r["spans"] and all(s["document_id"] == main and s["page"] >= 1 and s["bboxes"] for s in r["spans"])
        assert all(len(b) == 4 for s in r["spans"] for b in s["bboxes"])
        assert r["line_start"] is not None and r["line_end"] >= r["line_start"]


def test_one_row_per_requirement_and_assignment_keeps_each_units_answer():
    client, opp = _seeded()
    req = opp.replace("OPP-", "REQ-") + "-0001"  # held by CROWN, validated
    with SessionLocal() as db:
        db.add(Assignment(opportunity_id=opp, req_id=req, bu="EP2", owner="EP² Product Manager", status="submitted",
                          compliance="partial", response="Auxiliary supply only", responded_by="EP² Product Manager"))
        withdrawn = db.query(Assignment).filter_by(opportunity_id=opp, req_id=opp.replace("OPP-", "REQ-") + "-0013").one()
        withdrawn.status = "withdrawn"  # nobody holds this one any more
        db.commit()
    data = client.get(f"/api/bids/{opp}/compliance-matrix").json()
    assert len(data["rows"]) == 14 and data["total"] == 13  # 13 requirements, one with two units, one with none
    mine = {r["unit"]: r for r in data["rows"] if r["req_id"] == req}
    assert set(mine) == {"CROWN", "EP2"} and all(r["assignments"] == 2 for r in mine.values())
    assert (mine["CROWN"]["status"], mine["CROWN"]["compliance"]) == ("validated", "met")
    assert (mine["EP2"]["status"], mine["EP2"]["compliance"], mine["EP2"]["response"]) == ("submitted", "partial", "Auxiliary supply only")
    assert mine["EP2"]["compliance_label"] == "Partially compliant" and mine["CROWN"]["state"] == mine["EP2"]["state"] == "pending"
    free = next(r for r in data["rows"] if r["req_id"] == opp.replace("OPP-", "REQ-") + "-0013")
    assert free["assignments"] == 0 and free["unit"] is None and free["assignment_id"] is None and free["state"] == "not_assigned"
    assert opp.replace("OPP-", "REQ-") + "-0013" in data["blocking"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main(["-q", __file__]))
