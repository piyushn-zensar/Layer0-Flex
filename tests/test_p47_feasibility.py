"""P-47 (C-42): each unit manager states the unit's estimate and five delivery factors (people, skills, manufacturing
capacity, materials, cost), each ok or a constraint with a note; the bid manager accepts the teams' estimates only
once every unit has stated all five; a changed factor reopens the acceptance; the schedule criterion lists the
constraints."""
import os
import tempfile

os.environ["STORE_DIR"] = tempfile.mkdtemp()

from conftest import auth, signed_in  # noqa: E402

FACTORS = ("people", "skills", "capacity", "materials", "cost")


def _criterion(client, base):
    return {c["id"]: c for c in client.get(f"{base}/decisions").json()["summary"]["criteria"]}["schedule"]


def test_delivery_feasibility():
    from scripts import seed_demo

    seed_demo.main()
    client = signed_in()  # the bid manager
    opp = client.get("/api/portfolio").json()[0]["opp"]["id"]
    base = f"/api/bids/{opp}"
    assert client.put(f"{base}/schedule", json={"due_date": "2026-11-20", "consolidation_days": 3}).status_code == 200
    units = [u["bu"] for u in client.get(f"{base}/schedule").json()["units"]]
    assert "CROWN" in units

    # a date only: not ready, the five factors are missing, the acceptance is refused
    for bu in units:
        assert client.put(f"{base}/units/{bu}/completion", json={"estimated_completion": "2026-11-10"},
                          headers=auth(f"{bu.lower()}.pm")).status_code == 200
    s = client.get(f"{base}/schedule").json()
    assert not s["ready"] and s["missing_factors"]["CROWN"] == list(FACTORS)
    refused = client.post(f"{base}/approvals", json={"kind": "schedule"})
    assert refused.status_code == 409 and "materials" in refused.json()["detail"]

    url, pm = f"{base}/units/CROWN/completion", auth("crown.pm")
    no_note = {"estimated_completion": "2026-11-10", "factors": [{"factor": "materials", "status": "constraint"}]}
    assert client.put(url, json=no_note, headers=pm).status_code == 422
    unknown = {"estimated_completion": "2026-11-10", "factors": [{"factor": "budget", "status": "ok"}]}
    assert client.put(url, json=unknown, headers=pm).status_code == 422
    assert client.put(url, json=no_note | {"factors": []}, headers=auth("crown.de")).status_code == 403  # not the manager
    assert client.put(url, json={"estimated_completion": "2026-11-10"}).status_code == 403  # the bid manager sets no unit date

    def five(**overrides):
        return [{"factor": f, "status": "ok"} | overrides.get(f, {}) for f in FACTORS]
    for bu in units:
        body = {"estimated_completion": "2026-11-10", "factors": five()}
        if bu == "CROWN":
            body["factors"] = five(materials={"status": "constraint", "note": "long-lead breakers"})
        assert client.put(f"{base}/units/{bu}/completion", json=body, headers=auth(f"{bu.lower()}.pm")).status_code == 200
    assert client.put(url, json={"estimated_completion": "2026-11-10", "factors": five(
        materials={"status": "constraint", "note": "long-lead breakers"})}, headers=pm).status_code == 200  # again: no duplicate rows
    s = client.get(f"{base}/schedule").json()
    assert s["ready"] and not s["missing_factors"]
    assert s["constraints"] == [{"bu": "CROWN", "factor": "materials", "note": "long-lead breakers"}]
    assert next(u for u in s["units"] if u["bu"] == "CROWN")["constraints"] == ["materials"]

    ok = client.post(f"{base}/approvals", json={"kind": "schedule"})
    assert ok.status_code == 200 and ok.json()["current"]
    crit = _criterion(client, base)
    assert crit["status"] == "met" and "materials" in crit["detail"] and "long-lead breakers" in crit["detail"], crit

    # a note edit keeps the acceptance; a status change reopens it
    assert client.put(url, json={"estimated_completion": "2026-11-10", "factors": five(
        materials={"status": "constraint", "note": "long-lead breakers, 14 weeks"})}, headers=pm).status_code == 200
    assert client.get(f"{base}/schedule").json()["approvals"]["schedule"]["current"]
    assert client.put(url, json={"estimated_completion": "2026-11-10", "factors": five()}, headers=pm).status_code == 200
    s = client.get(f"{base}/schedule").json()
    assert s["approvals"]["schedule"]["current"] is False and s["constraints"] == []
    assert "no team reports a constraint" in _criterion(client, base)["detail"]

    from app.core.db import SessionLocal
    from app.modules.opportunities.models import UnitFeasibility
    with SessionLocal() as db:
        assert db.query(UnitFeasibility).filter_by(opportunity_id=opp, bu="CROWN").count() == len(FACTORS)
