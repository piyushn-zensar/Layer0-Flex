"""P-33 (C-24): each participating unit's manager gives an estimated completion date; the consolidated schedule and the
planned submission date follow; the bid manager approves only the overall schedule (once every unit has a date) and
the high-level compliance position; a later change reopens the approval; the schedule criterion reads the dates."""
import os
import tempfile

os.environ["STORE_DIR"] = tempfile.mkdtemp()

from conftest import auth, signed_in  # noqa: E402


def test_schedule_and_approvals():
    from scripts import seed_demo

    seed_demo.main()  # a bid with participating units, dispatched, some answers validated
    client = signed_in()
    opp = client.get("/api/portfolio").json()[0]["opp"]["id"]
    base = f"/api/opportunities/{opp}"
    s = client.get(f"{base}/schedule").json()
    units = [u["bu"] for u in s["units"]]
    assert "CROWN" in units and not s["ready"] and s["planned_submission"] is None and s["compliance"]

    assert client.post(f"{base}/approvals", json={"kind": "schedule"}).status_code == 409  # dates missing
    assert client.put(f"{base}/schedule", json={"due_date": "2026-11-20", "consolidation_days": 3},
                      headers=auth("crown.pm")).status_code == 403
    assert client.put(f"{base}/schedule", json={"due_date": "2026-11-20", "consolidation_days": 3}).status_code == 200

    date = {"estimated_completion": "2026-11-10", "note": "drawings after the kick-off"}
    assert client.put(f"{base}/units/CROWN/completion", json=date, headers=auth("crown.de")).status_code == 403  # not the manager
    assert client.put(f"{base}/units/CROWN/completion", json=date, headers=auth("ep2.pm")).status_code == 403   # another unit
    assert client.put(f"{base}/units/JETCOOL/completion", json=date, headers=auth("jetcool.pm")).status_code in (200, 409)
    for bu in units:
        r = client.put(f"{base}/units/{bu}/completion", json=date, headers=auth(f"{bu.lower()}.pm"))
        assert r.status_code == 200, (bu, r.text)
    s = client.get(f"{base}/schedule").json()
    assert s["ready"] and s["planned_submission"] == "2026-11-13" and not s["after_due"]

    ok = client.post(f"{base}/approvals", json={"kind": "schedule", "note": "dates agreed"})
    assert ok.status_code == 200 and ok.json()["current"] and ok.json()["approved_by"] == "Bid Manager"
    assert client.post(f"{base}/approvals", json={"kind": "compliance"}).json()["current"]
    assert client.post(f"{base}/approvals", json={"kind": "schedule"}, headers=auth("crown.pm")).status_code == 403

    crit = {c["id"]: c for c in client.get(f"{base}/decisions").json()["summary"]["criteria"]}["schedule"]
    assert crit["status"] == "met" and "2026" in crit["detail"], crit

    # a unit moves its date past the due date: the approval reopens and the criterion turns not met
    late = {"estimated_completion": "2026-11-19", "note": "late material"}
    assert client.put(f"{base}/units/CROWN/completion", json=late, headers=auth("crown.pm")).status_code == 200
    s = client.get(f"{base}/schedule").json()
    assert s["after_due"] and s["approvals"]["schedule"]["current"] is False
    crit = {c["id"]: c for c in client.get(f"{base}/decisions").json()["summary"]["criteria"]}["schedule"]
    assert crit["status"] == "not_met"
