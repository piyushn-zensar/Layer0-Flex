"""Unit tests for M11 — provenance & traceability."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from provenance.anchors import (DocumentRef, SpanAnchor, ProvenanceClass, paginate,
                                anchor_quote, provenance_for_quote, extracted, derived,
                                unanchored, parameter, build_index)

SRC = (Path(__file__).resolve().parent.parent /
       "knowledge_base" / "sample_rfps" / "rfp_REAL_syracuse_switchgear.txt")


def _doc_and_pages():
    txt = SRC.read_text()
    doc = DocumentRef(doc_id="RFP-SYR-2023-20", version="Rev_3",
                      extractor="inline-text",
                      content_sha256=DocumentRef.hash_content(txt))
    return doc, paginate(txt), txt


def test_extracted_value_gets_real_span_anchor():
    doc, pages, _ = _doc_and_pages()
    p = provenance_for_quote("Arc-resistant Type 2B", pages, doc, "arc_resistant")
    d = p.to_dict()
    assert d["class"] == ProvenanceClass.EXTRACTED
    a = d["anchor"]
    assert a["page"] >= 1
    assert a["span"][1] > a["span"][0]
    assert a["quote"] == "Arc-resistant Type 2B"
    assert a["version"] == "Rev_3"
    assert a["extractor"] == "inline-text"


def test_offsets_are_page_local_and_resolve_back_to_source():
    """The offset must actually index the page text it claims to."""
    doc, pages, _ = _doc_and_pages()
    a = anchor_quote("15kV two-section Metal Clad Switchgear", pages, doc)
    assert a is not None
    page_text = pages[a.page - 1]
    assert page_text[a.span[0]:a.span[1]] == a.quote


def test_unlocatable_quote_returns_unanchored_never_fabricates():
    """A wrong anchor is worse than no anchor — it looks authoritative."""
    doc, pages, _ = _doc_and_pages()
    p = provenance_for_quote("this sentence does not appear anywhere", pages, doc, "phantom")
    d = p.to_dict()
    assert d["class"] == ProvenanceClass.UNANCHORED
    assert d["warning_flag"] is True
    assert "anchor" not in d


def test_missing_quote_returns_unanchored():
    doc, pages, _ = _doc_and_pages()
    d = provenance_for_quote(None, pages, doc, "nothing").to_dict()
    assert d["class"] == ProvenanceClass.UNANCHORED
    assert d["warning_flag"] is True


def test_derived_carries_rule_and_structured_parent_anchors():
    """A tier appears in no document — it is DERIVED, with parent anchors
    kept as structured objects, never colon-delimited strings."""
    doc, pages, _ = _doc_and_pages()
    parent = anchor_quote("Arc-resistant Type 2B", pages, doc)
    d = derived("KB-L2-ARC-RESISTANT", [parent],
                reason="Arc-resistant requirement implies utility-grade brand").to_dict()
    assert d["class"] == ProvenanceClass.DERIVED
    assert d["rule_id"] == "KB-L2-ARC-RESISTANT"
    assert isinstance(d["parent_anchors"], list)
    assert isinstance(d["parent_anchors"][0], dict)
    assert d["parent_anchors"][0]["doc_id"] == "RFP-SYR-2023-20"


def test_doc_id_with_colon_survives_round_trip():
    """Real procurement ids contain colons; flat strings would be ambiguous."""
    a = SpanAnchor(doc_id="RFP-SYR-2026:REV3", version="v3.1", page=14,
                   span=(1204, 1222), quote="4000A copper main bus")
    d = a.to_dict()
    assert d["doc_id"] == "RFP-SYR-2026:REV3"
    assert d["span"] == [1204, 1222]


def test_bidirectional_index_supports_dual_view():
    doc, pages, _ = _doc_and_pages()
    params = [
        parameter("arc_resistant", "Type 2B",
                  provenance_for_quote("Arc-resistant Type 2B", pages, doc, "arc_resistant")),
        parameter("voltage_class_kv", 15.0,
                  provenance_for_quote("15kV two-section Metal Clad Switchgear", pages, doc, "voltage_class_kv")),
        parameter("redundancy", "N+1", unanchored("model paraphrased")),
    ]
    idx = build_index(params)
    assert idx["coverage"]["total"] == 3
    assert idx["coverage"]["anchored"] == 2
    assert idx["coverage"]["unanchored"] == 1
    assert "arc_resistant" in idx["backward_by_parameter"]
    assert any("arc_resistant" in v for v in idx["forward_by_page"].values())
    assert idx["unanchored"][0]["parameter"] == "redundancy"


def test_content_hash_detects_document_substitution():
    a = DocumentRef.hash_content("original spec text")
    b = DocumentRef.hash_content("amended spec text")
    assert a != b and len(a) == 64
