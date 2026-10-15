"""J-12 (C-15): the trace says whether the bid has been sent for assessment, so the screen shows unit responses only then.

Run:  .venv\\Scripts\\python -m pytest -q tests/test_j12_trace_gate.py
Uses a temporary store, so it never touches your local database (no model call).
"""
import os
import tempfile

os.environ["STORE_DIR"] = tempfile.mkdtemp()
os.environ["LLM_PROVIDER"] = "mock"

from conftest import signed_in  # noqa: E402

from scripts import seed_demo  # noqa: E402


def test_sent_for_assessment_follows_the_dispatched_work():
    seed_demo.main()  # the demo bid: dispatched, some answers validated
    client = signed_in()
    dispatched = client.get("/api/portfolio").json()[0]["opp"]["id"]
    t = client.get(f"/api/opportunities/{dispatched}/trace").json()
    assert t["sent_for_assessment"] is True and any(r["assignments"] for r in t["rows"])

    # a bid nobody dispatched has no unit work, so nothing to show yet
    fresh = client.post("/api/opportunities", json={"title": "not sent yet"}).json()["id"]
    t = client.get(f"/api/opportunities/{fresh}/trace").json()
    assert t["sent_for_assessment"] is False and t["progress"] == {}

    # a no-go withdraws only the open work: answers already submitted or validated stay, and so does the flag
    assert client.post(f"/api/opportunities/{dispatched}/go-no-go", json={"outcome": "no_go"}).status_code == 200
    t = client.get(f"/api/opportunities/{dispatched}/trace").json()
    assert t["opp"]["status"] == "no_go"
    assert t["sent_for_assessment"] is any(r["assignments"] for r in t["rows"])
    assert t["sent_for_assessment"] is True  # the seed has validated answers
