"""P-43 (C-38, C-39): the Assessment Summary counts technical requirements only (legal, commercial and schedule items
leave it unchanged; standards items are listed, not counted), and an engineer's validated partial answer counts as
reviewed and corrected."""
import os
import tempfile

os.environ["STORE_DIR"] = tempfile.mkdtemp()

from conftest import signed_in  # noqa: E402


def test_summary_counts_technical_only_and_engineer_reviews():
    from app.core.db import SessionLocal
    from app.modules.requirements import service as requirements
    from app.modules.workpackages import service as workpackages
    from scripts import seed_demo

    seed_demo.main()
    client = signed_in()
    opp = client.get("/api/portfolio").json()[0]["opp"]["id"]
    url = f"/api/bids/{opp}/assessment-score"
    s = client.get(url).json()
    m = s["measures"]
    cats = {r["req"]["req_id"]: r["req"]["category"] for r in client.get(f"/api/bids/{opp}/trace").json()["rows"]}
    assert set(m) == {"technical_match", "engineer_reviewed", "review_progress"}
    assert all(cats[i] == "technical" for i in m["technical_match"]["req_ids"]) and m["technical_match"]["of"] == s["technical"]
    assert s["standards"]["req_ids"] and all(cats[i] == "compliance" for i in s["standards"]["req_ids"])
    er = m["engineer_reviewed"]
    assert er["confirmed"] + er["corrected"] == er["n"] <= er["of"] == s["technical"]
    before = (m["technical_match"]["n"], m["technical_match"]["of"], er["of"], len(s["standards"]["req_ids"]))

    with SessionLocal() as db:  # C-38: a legal, a commercial and a schedule item leave the percentage unchanged
        src = next(r for r in requirements.current(db, opp) if r.status == "approved" and r.page)
        for cat in ("legal", "commercial", "schedule"):
            assert requirements.add(db, opp, src.document_id, src.quote, f"Test {cat} item", cat, "test").status == "approved"
    s = client.get(url).json()
    m = s["measures"]
    assert (m["technical_match"]["n"], m["technical_match"]["of"], m["engineer_reviewed"]["of"], len(s["standards"]["req_ids"])) == before

    with SessionLocal() as db:  # C-39: an engineer's partially compliant answer, validated, is reviewed and corrected
        work = workpackages.by_requirement(db, opp)
        a = next(items[0] for req_id, items in work.items()  # one unit holds it, so its answer alone completes the review
                 if cats.get(req_id) == "technical" and len(items) == 1 and items[0].bu != "BID" and items[0].status == "assigned")
        who = workpackages.people(db, a)
        workpackages.respond(db, a.id, "partial", None, "Test", who["answer"][0], reason="Rating lower")
        workpackages.validate(db, a.id, True, "", who["validate"][0])
    er2 = client.get(url).json()["measures"]["engineer_reviewed"]
    assert er2["n"] == er["n"] + 1 and er2["corrected"] == er["corrected"] + 1 and er2["confirmed"] == er["confirmed"]
    assert er2["not_compliant_answer"] == er["not_compliant_answer"] + 1  # every reviewed answer other than Compliant


def test_technical_match_is_the_system_proposal():
    from conftest import auth
    from scripts import seed_demo

    seed_demo.main()
    client = signed_in()
    opp = client.get("/api/portfolio").json()[0]["opp"]["id"]
    url = f"/api/bids/{opp}/assessment-score"
    before = client.get(url).json()
    t = next(r for r in client.get(f"/api/bids/{opp}/trace").json()["rows"]
             if r["req"]["req_id"] in before["measures"]["technical_match"]["req_ids"] and r["match"]["bu"] == "CROWN")
    assert client.post(f"/api/bids/{opp}/requirements/{t['req']['req_id']}/match", json={"units": []},
                       headers=auth("crown.de")).status_code == 200  # the engineer: not Crown's, no unit now
    after = client.get(url).json()
    assert after["measures"]["technical_match"]["req_ids"] == before["measures"]["technical_match"]["req_ids"]  # C-39
    assert t["req"]["req_id"] in next(g["req_ids"] for g in after["gaps"] if g["kind"] == "not_in_domain")
