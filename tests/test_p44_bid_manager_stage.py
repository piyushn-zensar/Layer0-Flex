"""P-44 (C-41): the bid manager's first stage is business relevance and routing. A technical match is accepted, rejected
or corrected by the designer / engineer of a unit on it (the bid manager gets 403); the bid manager routes, changing
the unit only; the compliance position is approved once a unit answer is validated (on the Bid decision)."""
import os
import tempfile

os.environ["STORE_DIR"] = tempfile.mkdtemp()

from conftest import auth, signed_in  # noqa: E402


def _bid():
    from scripts import seed_demo

    seed_demo.main()  # a dispatched bid: Crown and EP2 technical matches proposed, some answers validated
    client = signed_in()
    return client, client.get("/api/portfolio").json()[0]["opp"]["id"]


def test_bid_manager_routes_engineer_decides():
    client, opp = _bid()
    rows = client.get(f"/api/bids/{opp}/trace").json()["rows"]
    crown = [r for r in rows if r["req"]["category"] == "technical" and r["match"] and r["match"]["bu"] == "CROWN"
             and r["match"]["status"] == "proposed"]
    t, other = crown[0], crown[1]
    decide, change = f"/api/matches/{t['match']['id']}/decide", f"/api/bids/{opp}/requirements/{t['req']['req_id']}/match"
    ok = {"units": [{"product_id": "CROWN-ARMV", "offering_type": "ETO"}]}
    assert client.post(decide, json={"action": "accept"}).status_code == 403  # the bid manager approves no technical match
    assert client.post(change, json=ok).status_code == 403
    for who in ("crown.pm", "ep2.de"):  # the unit manager, another unit's engineer
        assert client.post(decide, json={"action": "accept"}, headers=auth(who)).status_code == 403, who

    assert t["can_change"] is False
    as_de = {r["req"]["req_id"]: r for r in client.get(f"/api/bids/{opp}/trace", headers=auth("crown.de")).json()["rows"]}
    assert as_de[t["req"]["req_id"]]["can_change"] is True
    assert next(r for r in rows if r["req"]["category"] not in ("technical", "compliance"))["can_change"] is True

    assert client.post(decide, json={"action": "accept"}, headers=auth("crown.de")).status_code == 200
    m = next(r for r in client.get(f"/api/bids/{opp}/trace").json()["rows"] if r["req"]["req_id"] == t["req"]["req_id"])["match"]
    assert (m["status"], m["decided_by"]) == ("accepted", "Crown Design Engineer")
    same = client.post(f"/api/bids/{opp}/requirements/{t['req']['req_id']}/route", json={"units": ["CROWN"]}).json()
    assert (same["id"], same["status"]) == (m["id"], "accepted")  # the same units: the engineer's decision stays

    item = next(r for r in rows if r["req"]["category"] not in ("technical", "compliance"))["req"]["req_id"]
    other_item = client.post(f"/api/bids/{opp}/requirements/{item}/route", json={"units": ["CROWN"]}).json()
    assert other_item["units"] == [{"bu": "CROWN", "product_id": None, "offering_type": "NONE"}]  # no solution placeholder

    route = f"/api/bids/{opp}/requirements/{other['req']['req_id']}/route"
    assert client.post(route, json={"units": ["EP2"]}, headers=auth("crown.de")).status_code == 403
    assert client.post(route, json={"units": ["XYZ"]}).status_code == 422
    assert client.post(f"/api/bids/{opp}/requirements/REQ-9999-0001/route", json={"units": ["EP2"]}).status_code == 404
    routed = client.post(route, json={"units": ["EP2"]}).json()
    assert (routed["method"], routed["status"]) == ("routed", "proposed")
    assert routed["units"] == [{"bu": "EP2", "product_id": None, "offering_type": "ETO"}]
    client.post(f"/api/bids/{opp}/match")  # a re-run keeps the bid manager's routing
    after = next(r for r in client.get(f"/api/bids/{opp}/trace").json()["rows"] if r["req"]["req_id"] == other["req"]["req_id"])
    assert after["match"]["method"] == "routed"
    ep2 = {"units": [{"product_id": "EP2-RPP", "offering_type": "ETO"}]}
    url = f"/api/bids/{opp}/requirements/{other['req']['req_id']}/match"
    assert client.post(url, json=ep2, headers=auth("crown.de")).status_code == 403  # no longer Crown's
    assert client.post(url, json=ep2, headers=auth("ep2.de")).status_code == 200
    assert client.get(f"/api/bids/{opp}/decisions").status_code == 200  # a unit with no solution yet breaks no check


def test_compliance_approval_waits_for_validated_answers():
    client, opp = _bid()
    rows = client.get(f"/api/bids/{opp}/trace").json()["rows"]
    for a in (a for r in rows for a in r["assignments"] if a["status"] == "validated"):  # back to the units
        assert client.post(f"/api/assignments/{a['id']}/validate", json={"ok": False, "note": "check"}).status_code == 200
    assert client.post(f"/api/bids/{opp}/approvals", json={"kind": "compliance"}).status_code == 409

    item = next(a for r in rows if r["req"]["category"] == "technical" for a in r["assignments"]
                if a["bu"] == "CROWN" and a["status"] == "assigned")
    url = f"/api/assignments/{item['id']}"
    assert client.post(f"{url}/respond", json={"compliance": "met"}, headers=auth("crown.de")).status_code == 200
    assert client.post(f"{url}/validate", json={"ok": True}, headers=auth("crown.pm")).status_code == 200
    assert client.post(f"/api/bids/{opp}/approvals", json={"kind": "compliance"}).status_code == 200


def test_capability_gap_decides_the_match_and_a_go_after_validation_moves_to_consolidating():
    from app.core.db import SessionLocal
    from app.modules.workpackages import service as workpackages

    client, opp = _bid()
    rows = client.get(f"/api/bids/{opp}/trace").json()["rows"]
    t = next(r for r in rows if r["req"]["category"] == "technical" and r["match"] and r["match"]["bu"] == "CROWN")
    req_id = t["req"]["req_id"]
    assert client.post(f"/api/matches/{t['match']['id']}/decide", json={"action": "reject"}, headers=auth("crown.de")).status_code == 200
    assert req_id in [o["req_id"] for o in client.get(f"/api/bids/{opp}/needs-owner").json()]
    assert client.post(f"/api/bids/{opp}/requirements/{req_id}/capability-gap",
                       json={"reason": "Not offered in this tender."}).status_code == 200
    m = next(r for r in client.get(f"/api/bids/{opp}/trace").json()["rows"] if r["req"]["req_id"] == req_id)["match"]
    assert (m["status"], m["units"], m["rationale"]) == ("accepted", [], "Capability gap: Not offered in this tender.")

    status = lambda: client.get(f"/api/bids/{opp}").json()["opportunity"]["status"]  # noqa: E731
    assert client.post(f"/api/bids/{opp}/go-no-go", json={"outcome": "go", "rationale": "test"}).status_code == 200
    assert status() == "dispatched"  # a go before every answer is validated: the status stays
    with SessionLocal() as db:
        for items in workpackages.by_requirement(db, opp).values():
            for a in items:
                who = workpackages.people(db, a)
                if a.status in ("assigned", "returned"):
                    workpackages.respond(db, a.id, "met", None, "Test", who["answer"][0])
                if a.status == "submitted":
                    workpackages.validate(db, a.id, True, "", who["validate"][0])
    assert status() == "consolidating"  # the last validation after the go moves the bid on
