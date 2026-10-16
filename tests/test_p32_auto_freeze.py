"""P-32 (C-27): a successful extraction freezes the requirements at once, with no approval; a document instance is read
once: the same file sent to another bid opens the bid that read it; matching and knowledge never rewrite the frozen
requirements."""
import os
import tempfile

os.environ["STORE_DIR"] = tempfile.mkdtemp()

from conftest import auth, signed_in  # noqa: E402


def test_auto_freeze_and_known_instance(monkeypatch):
    from app.core import fileid
    from app.core.db import SessionLocal
    from app.modules.knowledge import service as knowledge
    from app.modules.matching import service as matching
    from app.modules.opportunities import service as opportunities
    from app.modules.requirements import service as requirements

    monkeypatch.setattr(requirements, "FREEZE_ON_READ", True)  # the product default (conftest switches it off)
    client = signed_in()
    first = client.post("/api/opportunities", json={"title": "Syracuse switchgear"}).json()["id"]
    up = client.post(f"/api/opportunities/{first}/documents/from-sample", json={"name": "syracuse_rfp"}).json()
    assert up["status"] in ("uploaded", "ingested")  # other tests may have read this sample: read-once is checked below
    r = client.post(f"/api/opportunities/{first}/requirements/extract", json={})
    assert r.status_code == 200 and r.json()["frozen"] == 1, r.text   # frozen at once, nobody approved it
    assert client.get(f"/api/opportunities/{first}").json()["opportunity"]["status"] == "frozen"
    assert client.post(f"/api/opportunities/{first}/requirements/extract", json={"reason": "again"}).status_code == 409

    with SessionLocal() as db:
        doc = opportunities.main_document(db, first)
        ident = opportunities.identity_of(db, doc.id)
        assert (ident.doc_ident, ident.instance_ident, ident.id_source) == fileid.identity(open(doc.path, "rb").read(), ".pdf")
        rows = lambda: sorted((x.req_id, x.version, x.text, x.baseline) for x in requirements.current(db, first, include_children=True))
        before = rows()
        matching.match(db, first, "matching agent (test)")
        req = requirements.current(db, first)[0]
        item = knowledge.nominate(db, "requirement", req.req_id, "Bid Manager")
        knowledge.review(db, item.kb_id, True, "", {"name": "Bid Manager", "role": "bid_manager", "bu": None})
        assert rows() == before and requirements.baseline(db, first).number == 1   # nothing rewrote the baseline

    monkeypatch.setattr(opportunities, "READ_ONCE", True)  # the product default: the newest bid that read it wins
    second = client.post("/api/opportunities", json={"title": "Same RFP again"}).json()["id"]
    again = client.post(f"/api/opportunities/{second}/documents/from-sample", json={"name": "syracuse_rfp"}).json()
    assert again["existing_bid"] == first and "not read again" in again["message"]
    assert client.get(f"/api/opportunities/{second}").json()["documents"] == []   # nothing attached, nothing read
    assert client.post(f"/api/opportunities/{second}/documents/from-sample", json={"name": "syracuse_rfp"},
                       headers=auth("crown.pm")).status_code == 403
