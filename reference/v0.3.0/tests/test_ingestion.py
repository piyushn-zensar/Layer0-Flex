"""Tests for M1 — ingestion and boundary classification."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion import ingest
from provenance.anchors import anchor_quote

SAMPLES = Path(__file__).resolve().parent.parent / "knowledge_base" / "sample_rfps"


def _make_pdf(dest: Path, text: str):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(dest), pagesize=letter)
    y = 750
    c.setFont("Helvetica", 9)
    for line in text.split("\n"):
        if y < 60:
            c.showPage(); c.setFont("Helvetica", 9); y = 750
        c.drawString(50, y, line[:105]); y -= 12
    c.save()


def _bidpack(tmp: Path, with_unsupported=True):
    _make_pdf(tmp / "RFP.pdf", (SAMPLES / "rfp_REAL_syracuse_switchgear.txt").read_text())
    if with_unsupported:
        (tmp / "single-line.dwg").write_text("binary cad")
        (tmp / "BOQ.xlsm").write_text("macro sheet")
    return tmp


def test_pdf_yields_page_local_text():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); _make_pdf(tmp / "a.pdf", "Line one\nLine two")
        res = ingest.ingest_path(tmp / "a.pdf")
        assert res.documents and res.primary.page_count >= 1
        assert "Line one" in res.primary.text


def test_extractor_name_and_version_are_recorded():
    """Offsets are only reproducible against a known extractor."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); _make_pdf(tmp / "a.pdf", "Arc-resistant Type 2B required")
        res = ingest.ingest_path(tmp / "a.pdf")
        assert "pdfplumber-" in res.primary.doc_ref.extractor


def test_content_hash_recorded_for_tamper_evidence():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); _make_pdf(tmp / "a.pdf", "spec text")
        res = ingest.ingest_path(tmp / "a.pdf")
        assert len(res.primary.doc_ref.content_sha256) == 64


def test_anchors_resolve_against_real_pdf_pages():
    """Provenance offsets must index the actual PDF page text."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _make_pdf(tmp / "a.pdf", (SAMPLES / "rfp_REAL_syracuse_switchgear.txt").read_text())
        res = ingest.ingest_path(tmp / "a.pdf")
        d = res.primary
        a = anchor_quote("Arc-resistant Type 2B", d.pages, d.doc_ref)
        assert a is not None
        assert d.pages[a.page - 1][a.span[0]:a.span[1]] == a.quote


def test_cad_and_macro_files_are_refused_not_guessed():
    with tempfile.TemporaryDirectory() as td:
        res = ingest.ingest_path(_bidpack(Path(td)))
        names = {u["filename"] for u in res.unsupported}
        assert "single-line.dwg" in names
        assert "BOQ.xlsm" in names
        assert all(u["routed_to"] == "engineering" for u in res.unsupported)
        assert all(u["reason"] for u in res.unsupported)


def test_unsupported_files_do_not_prevent_ingestion():
    """A bid pack with CAD in it must still process the RFP."""
    with tempfile.TemporaryDirectory() as td:
        res = ingest.ingest_path(_bidpack(Path(td)))
        assert len(res.documents) == 1
        assert len(res.unsupported) == 2
        assert "15kV" in res.primary.text


def test_malformed_pdf_is_reported_not_raised():
    """A corrupt file must never end the run."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); (tmp / "broken.pdf").write_text("not really a pdf")
        res = ingest.ingest_path(tmp / "broken.pdf")
        assert res.errors and not res.documents
        assert res.errors[0]["routed_to"] == "engineering"


def test_scanned_pdf_pages_reported_as_unreviewed():
    """Pages with no text layer must not be silently treated as empty."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(str(tmp / "scan.pdf"), pagesize=letter)
        c.drawString(50, 750, "x")   # below MIN_CHARS_PER_PAGE
        c.save()
        res = ingest.ingest_path(tmp / "scan.pdf")
        assert res.primary.pages_without_text
        assert any("scanned" in w.lower() for w in res.primary.warnings)


def test_summary_states_what_happened():
    with tempfile.TemporaryDirectory() as td:
        res = ingest.ingest_path(_bidpack(Path(td)))
        assert "ingested" in res.summary and "unsupported" in res.summary


def test_full_chain_pdf_to_tier_classification():
    """End to end: real PDF in, correct routing out."""
    from agents import understand_agent as ua, tier_classifier as tc
    with tempfile.TemporaryDirectory() as td:
        out = ingest.run(str(_bidpack(Path(td))))
        req = ua.run(out["text"])
        assert req["voltage_class_kv"] == 15.0
        assert req["breaker_positions"] == 18
        tiers = tc.run(req, out["text"])["tiers"]
        l2 = next(t for t in tiers if t["n"] == 2)
        assert l2["tier"] == "ETO_GUIDED"
        assert any("Crown" in b for b in l2["hinted_brands"])
