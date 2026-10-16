"""P-35 (C-29 points 1-4): knowledge sources are registered as drafts, read into located passages with heading
paths and tables, identified by their embedded IDs, admitted only by a reviewer of their collection, versioned,
annotated beside the passage, and current bid evidence never leaks into another bid."""
import os
import tempfile
from pathlib import Path

os.environ["STORE_DIR"] = tempfile.mkdtemp()

from conftest import auth, signed_in  # noqa: E402

TMP = Path(tempfile.mkdtemp())


def _pdf(name: str, instance: str) -> Path:
    """A 2-page PDF with an outline, a ruled table, and the file ID [DOC1, instance] (same document, new instance)."""
    import pymupdf
    doc = pymupdf.open()
    p1 = doc.new_page(width=400, height=500)
    p1.insert_text((50, 60), "1 Scope", fontsize=14)
    p1.insert_text((50, 90), "The power shelf shall deliver 800 VDC to the rack busbar.", fontsize=10)
    p2 = doc.new_page(width=400, height=500)
    p2.insert_text((50, 60), "2 Ratings", fontsize=14)
    for x in (50, 200, 350):
        p2.draw_line((x, 80), (x, 170))
    for y in (80, 110, 140, 170):
        p2.draw_line((50, y), (350, y))
    for (x, y), t in zip([(55, 100), (205, 100), (55, 130), (205, 130), (55, 160), (205, 160)],
                         ["Rating", "Value", "Input voltage", "13.8 kV", "Output", "800 VDC"]):
        p2.insert_text((x, y), t, fontsize=10)
    doc.set_toc([[1, "1 Scope", 1], [1, "2 Ratings", 2]])
    path = TMP / name
    doc.save(path)
    doc.close()
    doc = pymupdf.open(path)
    doc.xref_set_key(-1, "ID", f"[<D0C1D0C1><{instance}>]")
    doc.save(path.with_suffix(".id.pdf"), no_new_id=True)
    doc.close()
    return path.with_suffix(".id.pdf")


def test_register_review_version_and_isolation(monkeypatch):
    from app.core import llm
    from app.core.db import SessionLocal
    from app.modules.knowledge import service as k

    signed_in()  # creates the tables and accounts
    v1, v2 = _pdf("spec-v1.pdf", "AAAA0001"), _pdf("spec-v2.pdf", "AAAA0002")
    with SessionLocal() as db:
        s1, existing = k.register(db, v1, "Test", "engineering_reference", "SST spec", "OCP", "v0.3")
        assert not existing and s1.status == "draft" and s1.id_source == "embedded"
        assert (s1.document_id, s1.instance_id, s1.version) == ("D0C1D0C1", "AAAA0001", 1)
        ps = k.source_passages(db, s1.ks_id)
        assert ps[0].page == 1 and ps[0].heading == "1 Scope" and "800 VDC to the rack" in ps[0].text
        table = [p for p in ps if p.table]
        assert table and table[0].heading == "2 Ratings" and "13.8 kV" in table[0].text, [(p.heading, p.table, p.text) for p in ps]
        again, existing = k.register(db, v1, "Test", "engineering_reference")
        assert existing and again.ks_id == s1.ks_id  # same document instance: never read twice

        assert s1.ks_id not in {e["ks_id"] for e in k.evidence(db, ["engineering_reference"])}  # a draft is not evidence
        try:
            k.review_source(db, s1.ks_id, True, "", "Bid Manager", "bid_manager")
            raise AssertionError("the bid manager does not review engineering references")
        except PermissionError:
            pass
        k.review_source(db, s1.ks_id, True, "Checked", "Crown Design Engineer", "design_engineer")
        assert s1.ks_id in {e["ks_id"] for e in k.evidence(db, ["engineering_reference"])}

        s2, _ = k.register(db, v2, "Test", "engineering_reference", "SST spec", "OCP", "v0.4")
        assert s2.version == 2 and s2.document_id == s1.document_id
        k.review_source(db, s2.ks_id, True, "", "Crown Product Manager", "product_manager")
        db.refresh(s1)
        ev = {e["ks_id"] for e in k.evidence(db, ["engineering_reference"])}
        assert s1.status == "retired" and s2.ks_id in ev and s1.ks_id not in ev

        html = TMP / "bid.html"
        html.write_text("<html><nav>Menu</nav><h1>Site power</h1><p>The hosting site provides up to 2 MW.</p></html>", "utf-8")
        b, _ = k.register(db, html, "Test", "bid_evidence", "Site notes", opp_id="OPP-0042")
        assert [p.text for p in k.source_passages(db, b.ks_id)] == ["Site power The hosting site provides up to 2 MW."]
        k.review_source(db, b.ks_id, True, "", "Bid Manager", "bid_manager")
        assert b.ks_id in {e["ks_id"] for e in k.evidence(db, opp_id="OPP-0042")}
        assert b.ks_id not in {e["ks_id"] for e in k.evidence(db, opp_id="OPP-0043")}  # never another bid's evidence
        assert b.ks_id not in {e["ks_id"] for e in k.evidence(db)}

        calls = []

        def fake(task, system, prompt, schema):
            calls.append(task)
            n = prompt.count("\n[") + prompt.startswith("[")
            return {"passages": [{"n": i, "topics": ["800 VDC"], "content_type": "rating_or_limit",
                                  "attributes": [], "applicability": "", "ambiguities": []} for i in range(1, n + 1)]}
        monkeypatch.setattr(llm, "complete_json", fake)
        assert k.annotate(db, s2.ks_id, "Test") == len(k.source_passages(db, s2.ks_id)) and set(calls) == {"annotate_passages"}
        assert all(p.annotations["topics"] == ["800 VDC"] and p.text for p in k.source_passages(db, s2.ks_id))


def test_api_roles():
    client = signed_in()
    md = TMP / "note.md"
    md.write_text("# Liquid cooling\nCDU supply temperature up to 45 C.\n", "utf-8")
    with md.open("rb") as f:
        r = client.post("/api/knowledge/sources", files={"file": ("note.md", f, "text/markdown")},
                        data={"collection": "market_context", "title": "Cooling note"})
    assert r.status_code == 200 and r.json()["passages"] == 1 and r.json()["path"] is None, r.text
    ks = r.json()["ks_id"]
    assert client.get("/api/knowledge/sources").json()["collections"]["market_context"].startswith("Market")
    assert client.get(f"/api/knowledge/sources/{ks}").json()["passages"][0]["heading"] == "Liquid cooling"
    r = client.post(f"/api/knowledge/sources/{ks}/review", json={"approve": True}, headers=auth("crown.de"))
    assert r.status_code == 403, r.text  # market context: bid manager or product manager
    assert client.post(f"/api/knowledge/sources/{ks}/review", json={"approve": False}).status_code == 409  # needs a note
    assert client.post(f"/api/knowledge/sources/{ks}/review", json={"approve": True}).json()["status"] == "published"
    assert client.post(f"/api/knowledge/sources/{ks}/annotate", headers=auth("crown.pm")).status_code == 403
    assert client.post("/api/knowledge/sources", files={"file": ("x.exe", b"MZ", "application/octet-stream")},
                       data={"collection": "market_context"}).status_code == 409
