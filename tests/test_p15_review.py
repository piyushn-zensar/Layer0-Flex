"""P-15 review: the stored quote is the selection on every frozen page, and a blank short text falls back to the quote.

Run:  .venv\\Scripts\\python -m pytest -q tests/test_p15_review.py
Uses a temporary store, so it never touches your local database.
"""
import json
import os
import tempfile
from pathlib import Path

os.environ["STORE_DIR"] = tempfile.mkdtemp()
os.environ["LLM_PROVIDER"] = "mock"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.modules.requirements import anchoring  # noqa: E402
from scripts import seed_demo  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def test_selection_anchors_exactly_on_every_frozen_page():
    """The rule add_from_lines uses (and the LinePicker preview mirrors): body lines in the range, joined by spaces,
    anchored in those lines only -> exactly their first / last line and boxes, native and OCR pages alike."""
    for f in (ROOT / "data/layout_cache").glob("*.json"):
        for page in json.loads(f.read_text("utf-8"))["pages"]:
            lines = page["lines"]
            for a in range(1, len(lines) + 1, 5):
                b = min(a + 39, len(lines))
                chosen = [l for l in lines if a <= l["n"] <= b and not l.get("furniture")
                          and anchoring.normalise(l["text"])]
                assert [l["n"] for l in chosen] == [l["n"] for l in lines if a <= l["n"] <= b
                                                    and not l.get("furniture") and l["text"].strip()]  # = preview
                if chosen:
                    hit = anchoring.find(" ".join(l["text"] for l in chosen), [{"page": page["page"], "lines": chosen}])
                    assert hit == {"page": page["page"], "line_start": chosen[0]["n"], "line_end": chosen[-1]["n"],
                                   "bboxes": [l["bbox"] for l in chosen]}, (f.name, page["page"], a)


def test_blank_short_text_falls_back_to_the_quote():
    client = TestClient(app)
    if client.get("/api/opportunities/OPP-0001").status_code == 404:
        seed_demo.main()  # test_smoke.py expects the demo to be OPP-0001
    opp = client.post("/api/opportunities", json={"title": "blank text"}).json()["id"]
    pdf = (ROOT / "data/RFP/RFP-2023-20-Switchgear-Procurement-Final.pdf").read_bytes()
    client.post(f"/api/opportunities/{opp}/documents", files={"file": ("rfp.pdf", pdf)})
    lines = client.post(f"/api/opportunities/{opp}/requirements/from-lines",
                        json={"page": 55, "line_start": 52, "line_end": 52, "text": "   "}).json()
    pasted = client.post(f"/api/opportunities/{opp}/requirements",
                         json={"quote": "Switchgear shall be Arc-resistant Type 2B.", "text": " "}).json()
    assert lines["text"] == lines["quote"].strip() and lines["text"].startswith("Switchgear shall be")
    assert pasted["text"] == "Switchgear shall be Arc-resistant Type 2B."
