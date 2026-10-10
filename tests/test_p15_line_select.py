"""P-15: a person adds a missed requirement by selecting its lines on the RFP page (no retyped quote).

Run:  .venv\\Scripts\\python -m pytest -q tests/test_p15_line_select.py
Uses a temporary store, so it never touches your local database.
"""
import os
import tempfile
from pathlib import Path

os.environ["STORE_DIR"] = tempfile.mkdtemp()
os.environ["LLM_PROVIDER"] = "mock"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from scripts import seed_demo  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def test_add_requirement_from_selected_lines():
    client = TestClient(app)
    if client.get("/api/opportunities/OPP-0001").status_code == 404:
        seed_demo.main()  # this file runs before test_smoke.py, which expects the demo to be OPP-0001
    opp = client.post("/api/opportunities", json={"title": "line select"}).json()["id"]
    pdf = (ROOT / "data/RFP/RFP-2023-20-Switchgear-Procurement-Final.pdf").read_bytes()
    doc = client.post(f"/api/opportunities/{opp}/documents", files={"file": ("rfp.pdf", pdf)}).json()["id"]
    page = client.get(f"/api/documents/{doc}/pages/55").json()
    lines = {line["n"]: line for line in page["lines"]}
    url = f"/api/opportunities/{opp}/requirements/from-lines"

    # p. 55, lines 52-53: "Switchgear shall be Arc-resistant Type 2B. ... IEEE C37.20.7." (the same words appear elsewhere)
    req = client.post(url, json={"page": 55, "line_start": 52, "line_end": 53, "category": "technical"},
                      headers={"X-Actor": "Crown%20Design%20Engineer"}).json()
    quote = f"{lines[52]['text']} {lines[53]['text']}"
    assert req["quote"] == quote and req["text"] == quote[:200]
    assert (req["provenance"], req["page"], req["line_start"], req["line_end"]) == ("EXTRACTED", 55, 52, 53)
    assert req["bboxes"] == [lines[52]["bbox"], lines[53]["bbox"]] and req["source"] == "p. 55, lines 52-53"
    assert req["document_id"] == doc and req["status"] == "proposed" and req["created_by"] == "Crown Design Engineer"
    h = client.get(f"/api/requirements/{req['req_id']}/history").json()
    assert [e["action"] for e in h["events"]] == ["proposed"] and h["events"][0]["by"] == "Crown Design Engineer"
    assert h["versions"][0]["text"] == quote[:200] and h["source"] == "p. 55, lines 52-53"

    # a page header in the range is left out of the quote, as the reader leaves it out; own text and category kept
    head = client.post(url, json={"page": 55, "line_start": 1, "line_end": 3, "text": "Part 1", "category": "legal"}).json()
    assert head["quote"] == lines[3]["text"] and (head["line_start"], head["line_end"]) == (3, 3)
    assert (head["text"], head["category"], head["bboxes"]) == ("Part 1", "legal", [lines[3]["bbox"]])
    assert head["req_id"] != req["req_id"]

    last = max(lines)
    for bad in [{"page": 55, "line_start": 5, "line_end": 4}, {"page": 55, "line_start": 0, "line_end": 2},
                {"page": 55, "line_start": 1, "line_end": last + 1}, {"page": 999, "line_start": 1, "line_end": 1},
                {"page": 0, "line_start": 1, "line_end": 1}, {"page": 55, "line_start": 3, "line_end": 60},
                {"page": 55, "line_start": 1, "line_end": 2},  # header lines only
                {"page": 55, "line_start": 52, "line_end": 53, "category": "nope"}]:
        r = client.post(url, json={"category": "technical"} | bad)
        assert r.status_code == 409, (bad, r.text)
    assert client.post("/api/opportunities/OPP-9997/requirements/from-lines",
                       json={"page": 1, "line_start": 1, "line_end": 1}).status_code == 404

    # after the freeze, missed requirements come in through the Changes page
    for r in (req, head):
        assert client.post(f"/api/requirements/{r['req_id']}/review", json={"action": "approve"}).status_code == 200
    assert client.post(f"/api/opportunities/{opp}/baselines").status_code == 200
    r = client.post(url, json={"page": 55, "line_start": 67, "line_end": 67})
    assert r.status_code == 409 and "Changes page" in r.json()["detail"]
    assert len(client.get(f"/api/opportunities/{opp}/requirements").json()["requirements"]) == 2
