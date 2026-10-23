"""P-38 (C-23), P-43 (C-39): the Assessment Summary keeps technical requirement match, reviewed by design engineers and
specialist review progress apart, each with the requirements it counts, reads product evidence from the latest
assessment run for the evidence gaps, and is never a probability. P-39 (C-29 point 8): the RAG evaluation runs and its passing
measures do not regress."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ["STORE_DIR"] = tempfile.mkdtemp()

from conftest import auth, signed_in  # noqa: E402


def test_assessment_score_measures_and_gaps():
    from app.core.db import SessionLocal
    from app.modules.knowledge import service as k
    from scripts import seed_demo

    seed_demo.main()
    client = signed_in()
    opp = client.get("/api/portfolio").json()[0]["opp"]["id"]
    s = client.get(f"/api/bids/{opp}/assessment-score").json()
    m = s["measures"]
    assert s["run"] is None and set(m) == {"technical_match", "engineer_reviewed", "review_progress"} and s["technical"] > 0
    assert m["technical_match"]["n"] == len(m["technical_match"]["req_ids"]) <= m["technical_match"]["of"] == s["technical"]
    assert m["review_progress"]["n"] <= m["review_progress"]["of"] and "not a probability" in s["note"]
    assert all(g["req_ids"] for g in s["gaps"])
    assert m["technical_match"]["label"] == "Technical Requirement Matching" and all("exception queue" not in g["label"] for g in s["gaps"])  # P-42 plain words

    first = m["technical_match"]["req_ids"][0]
    text = next(r["req"]["text"] for r in client.get(f"/api/bids/{opp}/trace").json()["rows"] if r["req"]["req_id"] == first)
    note = Path(tempfile.mkdtemp()) / "datasheet.md"
    note.write_text(f"# Datasheet\n{text}\n", "utf-8")
    with SessionLocal() as db:  # a verified datasheet that states exactly this requirement, reviewed by the unit
        src, _ = k.register(db, note, "Test", "product_evidence", "Datasheet")
        k.review_source(db, src.ks_id, True, "verified", "Crown Product Manager", "product_manager")
    assert client.post(f"/api/bids/{opp}/reassessments", json={"reason": "datasheet reviewed"}).status_code == 200
    s = client.get(f"/api/bids/{opp}/assessment-score").json()
    assert s["run"] == 1
    gap = {g["kind"]: g["req_ids"] for g in s["gaps"]}
    assert first not in gap.get("no_product_evidence", [])
    assert client.get("/api/bids/OPP-9999/assessment-score").status_code == 404


def test_rag_evaluation_does_not_regress():
    """Offline (keyword ranking) baseline of 16 Oct 2026: 10 of 13; retrieval relevance 3 of 6 (R-01, R-03, R-06)."""
    root = Path(__file__).resolve().parents[1]
    env = os.environ | {"LLM_PROVIDER": "mock", "PYTHONIOENCODING": "utf-8"}
    env.pop("STORE_DIR", None)  # the script makes its own throwaway store
    run = subprocess.run([sys.executable, "-m", "scripts.eval_rag", "--json"], cwd=root, env=env, capture_output=True,
                         text=True, encoding="utf-8", timeout=900)
    report = json.loads(run.stdout[run.stdout.index("{\n"):])
    ok = {c["id"] for c in report["cases"] if c["ok"]}
    assert {"R-01", "R-03", "R-06", "C-01", "N-01", "N-02", "U-01", "U-02", "I-01", "E-01"} <= ok, report["cases"]
    assert report["status"] == "draft" and report["reviewed_by"] is None  # counts only after an independent review
