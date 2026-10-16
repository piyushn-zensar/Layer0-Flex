"""P-37 part 1 (C-29 points 5 and 7): retrieval follows the task profile (collections, values only), returns only
published evidence with citations, never market context and never another bid's evidence; a reassessment is a new
numbered run of append-only records that keeps earlier runs and never changes a requirement."""
import os
import tempfile
from pathlib import Path

os.environ["STORE_DIR"] = tempfile.mkdtemp()

from conftest import auth, signed_in  # noqa: E402

TMP = Path(tempfile.mkdtemp())


def _md(name: str, text: str) -> Path:
    p = TMP / name
    p.write_text(text, encoding="utf-8")
    return p


def test_retrieval_profiles_and_reassessment():
    from app.core.db import SessionLocal
    from app.modules.knowledge import service as k
    from app.modules.knowledge.models import KbPassage
    from app.modules.requirements import service as requirements
    from scripts import seed_demo

    seed_demo.main()
    client = signed_in()
    opp = client.get("/api/portfolio").json()[0]["opp"]["id"]
    with SessionLocal() as db:
        ref, _ = k.register(db, _md("p37-ref.md", "# Busway ratings\nThe busway is rated 4000 A at 40 C ambient.\n"),
                            "Test", "engineering_reference", "Busway guide")
        mkt, _ = k.register(db, _md("p37-mkt.md", "# Vendor view\nOur busway is rated 4000 A and leads the market.\n"),
                            "Test", "market_context", "Vendor blog")
        bid, _ = k.register(db, _md("p37-bid.md", "# Site\nThe site busway must carry 4000 A.\n"), "Test", "bid_evidence",
                            "Site notes", opp_id=opp)
        other, _ = k.register(db, _md("p37-other.md", "# Other site\nThe other busway carries 4000 A too.\n"), "Test",
                              "bid_evidence", "Other bid notes", opp_id="OPP-9999")
        k.review_source(db, ref.ks_id, True, "", "Crown Design Engineer", "design_engineer")
        k.review_source(db, mkt.ks_id, True, "", "Bid Manager", "bid_manager")
        k.review_source(db, bid.ks_id, True, "", "Bid Manager", "bid_manager")
        k.review_source(db, other.ks_id, True, "", "Bid Manager", "bid_manager")

        hits = k.retrieve(db, "requirement_interpretation", "busway rated 4000 A", opp)
        ids = {h["ks_id"] for h in hits}
        assert {ref.ks_id, bid.ks_id} <= ids and mkt.ks_id not in ids and other.ks_id not in ids  # profile and bid isolation
        assert all(h["citation"].startswith(h["ks_id"]) for h in hits) and hits[0]["score"] < 1
        assert ref.ks_id in {h["ks_id"] for h in k.retrieve(db, "technical_explanation", "busway 4000 A")}
        assert k.retrieve(db, "numerical_assessment", "busway 4000 A") == []  # no annotated values yet
        passage = db.query(KbPassage).filter_by(source_id=ref.id).first()
        passage.annotations = {"topics": [], "content_type": "rating_or_limit", "applicability": "", "ambiguities": [],
                               "attributes": [{"name": "rated current", "value": "4000", "unit": "A", "conditions": "40 C"}]}
        db.commit()
        assert [h["ks_id"] for h in k.retrieve(db, "numerical_assessment", "busway 4000 A")] == [ref.ks_id]
        before = sorted((r.req_id, r.version, r.text) for r in requirements.current(db, opp, include_children=True))

    assert client.post(f"/api/bids/{opp}/reassessments", json={"reason": "x"}, headers=auth("crown.pm")).status_code == 403
    one = client.post(f"/api/bids/{opp}/reassessments", json={"reason": "first evidence pack"}).json()
    two = client.post(f"/api/bids/{opp}/reassessments", json={"reason": "new reference reviewed"}).json()
    assert (one["run"], two["run"]) == (1, 2) and one["records"] == two["records"] > 0
    latest = client.get(f"/api/bids/{opp}/assessments").json()
    assert latest["runs"] == [1, 2] and latest["run"] == 2 and len(latest["records"]) == two["records"]
    rec = latest["records"][0]
    assert rec["model"] == "retrieval only" and rec["prompt_hash"] and rec["reason"] == "new reference reviewed"
    assert all(c["ks_id"] in rec["evidence_versions"] for c in rec["citations"])
    assert len(client.get(f"/api/bids/{opp}/assessments", params={"run": 1}).json()["records"]) == one["records"]
    assert client.get("/api/knowledge/retrieve", params={"task": "nonsense", "q": "x"}).status_code == 409
    with SessionLocal() as db:
        assert sorted((r.req_id, r.version, r.text) for r in requirements.current(db, opp, include_children=True)) == before


def test_evidence_enters_prompts_only_when_reviewed(monkeypatch):
    """P-37 part 2: reviewed evidence goes into the matcher and outline prompts (keyword-ranked, so the same offline),
    only where it exists; an outline paragraph keeps the evidence it cites, an out-of-range citation is dropped."""
    from app.modules.consolidation import agent as outline
    from app.modules.matching import agent as matcher

    seen = []

    def fake(task, system, prompt, schema):
        seen.append((task, system, prompt, schema))
        if task == "draft_outline":
            ev = "evidence" in schema["properties"]["paragraphs"]["items"]["properties"]
            return {"paragraphs": [{"text": "The proposer offers it.", "cites": [1], **({"evidence": [1, 9]} if ev else {})}], "gaps": []}
        return {"answers": []}
    monkeypatch.setattr(matcher, "complete_json", fake)
    monkeypatch.setattr(outline, "complete_json", fake)
    reqs = [{"category": "technical", "quote": "4000 A busway", "evidence": ["[KS-0001 v1, p. 1, lines 1-2] rated 4000 A"]},
            {"category": "technical", "quote": "15 kV switchgear"}]
    matcher.propose_page("", reqs, [], [])
    matcher.propose_page("", [{"category": "technical", "quote": "15 kV switchgear"}], [], [])
    assert "REVIEWED EVIDENCE" in seen[0][2] and "For 1: [KS-0001" in seen[0][2] and "For 2" not in seen[0][2]
    assert "REVIEWED EVIDENCE" not in seen[1][2]  # no evidence: the prompt (and its frozen answer) is unchanged
    answers = [{"unit": "Anord", "compliance": "Comply", "product": "-", "requirement": "busway", "wording": "w", "response": "Met."}]
    d = outline.draft("Technical", answers, [], ["KS-0001 v1, p. 1, lines 1-2: rated 4000 A"])
    assert d["paragraphs"][0]["evidence"] == [1] and "[E1] KS-0001" in seen[2][2] and seen[2][1] == outline.SYSTEM_EVIDENCE
    outline.draft("Technical", answers, [])
    assert seen[3][1] == outline.SYSTEM and "REVIEWED EVIDENCE" not in seen[3][2]
