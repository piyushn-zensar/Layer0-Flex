"""J-13 (C-16): the links of the matrix to a unit's answer history and to the bid's activity log.

The Compliance matrix screen opens GET /api/assignments/{assignment_id}/history with the row's assignment_id and links to
GET /api/opportunities/{id}/activity?req_id=...; the Activity page reads the same endpoint with entity / req_id / bu / person.

Run:  .venv\\Scripts\\python -m pytest -q tests/test_j13_history_links.py
Uses a temporary store, so it never touches your local database (no model call: frozen answers only).
"""
import os
import tempfile

os.environ["STORE_DIR"] = tempfile.mkdtemp()
os.environ["LLM_PROVIDER"] = "mock"

from conftest import signed_in  # noqa: E402

from scripts import seed_demo  # noqa: E402


def _seeded():
    seed_demo.main()  # the 13-item Syracuse seed: dispatched, some answers submitted or validated
    client = signed_in()
    opp = client.get("/api/portfolio").json()[0]["opp"]["id"]
    return client, opp


def test_matrix_rows_link_to_their_history_and_activity():
    client, opp = _seeded()
    rows = client.get(f"/api/opportunities/{opp}/compliance-matrix").json()["rows"]
    held = [r for r in rows if r["assignment_id"] is not None]
    assert held and all(r["unit"] for r in held)
    assert all(r["unit"] is None for r in rows if r["assignment_id"] is None)  # no unit, no history to open

    answered = next(r for r in held if r["status"] == "validated")
    history = client.get(f"/api/assignments/{answered['assignment_id']}/history")
    assert history.status_code == 200
    events = history.json()
    assert [e["action"] for e in events][0] == "assigned" and events[-1]["action"] == "validated"
    assert events[-1]["after"]["status"] == answered["status"]  # the row and its history agree
    assert all({"id", "at", "actor", "action", "note", "before", "after"} <= set(e) for e in events)

    # the matrix's "All activity for this requirement" link: the same events are in the bid's log, under the requirement
    log = client.get(f"/api/opportunities/{opp}/activity", params={"req_id": answered["req_id"]}).json()
    in_log = {e["id"] for e in log["events"]}
    assert {e["id"] for e in events} <= in_log
    assert all(e["entity_id"] == answered["req_id"] for e in log["events"])
    assert {"requirement", "assignment"} <= {e["entity"] for e in log["events"]}

    assert client.get("/api/assignments/999999/history").status_code == 404


def test_activity_filters_and_paging_for_the_activity_page():
    client, opp = _seeded()
    url = f"/api/opportunities/{opp}/activity"
    page = client.get(url, params={"limit": 5}).json()
    assert len(page["events"]) == 5 and page["total"] > 5 and page["next_before"] == page["events"][-1]["id"]
    ids = [e["id"] for e in page["events"]]
    assert ids == sorted(ids, reverse=True)  # newest first
    older = client.get(url, params={"limit": 5, "before": page["next_before"]}).json()
    assert older["events"][0]["id"] < page["next_before"] and not {e["id"] for e in older["events"]} & set(ids)

    opts = page["filters"]
    assert "assignment" in opts["entities"] and opts["people"] and opts["units"]
    by_unit = client.get(url, params={"bu": opts["units"][0]}).json()
    assert by_unit["total"] > 0 and all(e["data"].get("bu") == opts["units"][0] for e in by_unit["events"])
    by_person = client.get(url, params={"person": opts["people"][0]}).json()
    assert by_person["total"] > 0 and all(e["actor"] == opts["people"][0] for e in by_person["events"])
    nothing = client.get(url, params={"req_id": "REQ-9999-0001"}).json()
    assert nothing["events"] == [] and nothing["total"] == 0 and nothing["next_before"] is None
    assert client.get("/api/opportunities/OPP-9999/activity").status_code == 404
