"""P-36 (C-29 points 3 and 6): reviewed examples are nominated with what they teach, their conditions and limits;
corrections of a reading can be nominated; only qualified reviewers approve; a change is a new version that retires
the old one on approval; approved items come from the database into the search index and the evidence, illustrative
material never does."""
import os
import tempfile

os.environ["STORE_DIR"] = tempfile.mkdtemp()

from conftest import auth, signed_in  # noqa: E402


def test_reviewed_examples():
    from app.core.db import SessionLocal
    from app.modules.catalog import service as catalog
    from app.modules.knowledge import service as k
    from app.modules.knowledge.models import KbItem
    from app.modules.requirements import service as requirements
    from scripts import seed_demo

    seed_demo.main()  # a published, dispatched bid with validated answers
    client = signed_in()
    opp = client.get("/api/portfolio").json()[0]["opp"]["id"]
    with SessionLocal() as db:
        req = requirements.current(db, opp)[0]
        requirements.apply_correction(db, opp, "edit", {"req_id": req.req_id, "text": "Corrected wording of the line"},
                                      "Bid Manager", "the reader joined two lines")
        item = k.nominate(db, "correction", req.req_id, "Bid Manager", "reader mistake worth teaching",
                          "requirement", "two-column specification pages", "not for tables")
        assert item.response.startswith("Corrected to: Corrected wording of the line") and "joined two lines" in item.response
        assert item.requirement.startswith("Read as: ") and item.bu == "BID"
        try:
            k.nominate(db, "decision", "1", "Bid Manager", example_type="opinion")
            raise AssertionError("unknown example type accepted")
        except ValueError:
            pass

    # who reviews: the bid manager for bid-level items, a unit's specialists for its answers
    assert client.post(f"/api/knowledge/{item.kb_id}/review", json={"approve": True}, headers=auth("crown.pm")).status_code == 403
    mine = client.get("/api/knowledge", params={"status": "queued", "reviewable": True}).json()["items"]
    assert [i["kb_id"] for i in mine] == [item.kb_id] and mine[0]["may_review"]
    assert client.get("/api/knowledge", params={"status": "queued", "reviewable": True}, headers=auth("crown.pm")).json()["items"] == []
    v1 = client.post(f"/api/knowledge/{item.kb_id}/review", json={"approve": True}).json()
    assert v1["status"] == "approved" and v1["reviewed_by"] == "Bid Manager"

    # a change is a new version; the old one stays in use until the new one is approved, then it is retired
    v2 = client.post(f"/api/knowledge/{item.kb_id}/revise", json={"limits": "not for tables or drawings"}).json()
    assert (v2["status"], v2["version"], v2["supersedes"], v2["limits"]) == ("queued", 2, item.kb_id, "not for tables or drawings")
    assert client.post(f"/api/knowledge/{item.kb_id}/revise", json={"limits": "again"}).status_code == 409  # one at a time
    with SessionLocal() as db:
        assert item.kb_id in {e["ks_id"] for e in k.evidence(db, ["reviewed_example"])}  # other tests add their own
    client.post(f"/api/knowledge/{v2['kb_id']}/review", json={"approve": True})
    with SessionLocal() as db:
        assert db.query(KbItem).filter_by(kb_id=item.kb_id).one().status == "retired"
        ex = k.evidence(db, ["reviewed_example"])
        mine = [e for e in ex if e["ks_id"] in (item.kb_id, v2["kb_id"])]
        assert [e["ks_id"] for e in mine] == [v2["kb_id"]] and "Limits: not for tables or drawings" in mine[0]["text"]
        assert v2["kb_id"] in {e["id"] for e in k.learned(db)} and item.kb_id not in {e["id"] for e in k.learned(db)}  # from the database

        # illustrative material is never verified evidence, even when approved
        db.add(KbItem(kb_id="KB-9999", kind="response", source_ref="x", opportunity_id=opp, requirement="r",
                      response="sample", illustrative=True, status="approved", sent_by="seed"))
        db.commit()
        assert "KB-9999" not in {e["ks_id"] for e in k.evidence(db)} | {e["id"] for e in k.learned(db)}
    catalog.learn()
    assert v2["kb_id"] in {h["id"] for h in catalog.search("Corrected wording of the line", 5)}
    sample = next(h for h in catalog.search("relay and protection panels SCADA", 10) if h["kind"] == "past_response")
    assert sample.get("illustrative")  # the seeded past responses are labelled as samples
