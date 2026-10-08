"""
Regression tests against the ACTUAL Syracuse RFP PDF — 101 pages, as
published by Syracuse Regional Airport Authority.

These exist because every earlier fixture was a hand-written text summary.
Summaries are written in the system's own vocabulary and are therefore
incapable of exposing vocabulary or scope failures. Running the genuine
document found four defects within minutes, one of them a false-automation
result of exactly the kind the tiering fail-safe exists to prevent.

Source: https://syrairport.org/wp-content/uploads/2023/08/
        RFP-2023-20-Switchgear-Procurement-Final.pdf
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion import ingest
from agents import understand_agent as ua, tier_classifier as tc

PDF = (Path(__file__).resolve().parent.parent / "knowledge_base" /
       "sample_rfps" / "real_pdfs" / "RFP-2023-20-Switchgear-Procurement-Final.pdf")

pytestmark = pytest.mark.skipif(not PDF.exists(), reason="real PDF fixture not present")


# Parsing 101 pages takes seconds; cache it across the module rather than
# re-parsing per test.
_CACHE = {}


def _ingested():
    if "res" not in _CACHE:
        _CACHE["res"] = ingest.ingest_path(PDF)
    return _CACHE["res"]


def _text():
    return _ingested().primary.text


def _req():
    if "req" not in _CACHE:
        _CACHE["req"] = ua.run(_text())
    return _CACHE["req"]


def test_ingests_all_101_pages():
    res = _ingested()
    d = res.primary
    assert d.page_count == 101
    assert len(d.text) > 200_000
    assert not res.errors


def test_detects_the_scanned_page_without_text_layer():
    """Page 83 is a scanned drawing. It must be reported as unreviewed,
    not silently treated as an empty page."""
    d = _ingested().primary
    assert 83 in d.pages_without_text
    assert any("scanned" in w.lower() for w in d.warnings)


def test_extracts_key_electrical_values_from_real_prose():
    req = _req()
    assert req["voltage_class_kv"] == 15.0
    assert "2B" in (req["arc_resistant"] or "")


def test_breaker_count_parsed_from_real_phrasing():
    """REGRESSION: the real document writes "eighteen (18) 15kV vacuum
    circuit breaker". The original pattern expected "18 x 15kV ... positions"
    and matched nothing at all."""
    req = _req()
    assert req["breaker_positions"] == 18


def test_transformer_rating_is_not_mistaken_for_a_ups():
    """REGRESSION: a single-line diagram contains "112.5KVA 13200V -208/120V",
    a distribution transformer. This was extracted as ups_kva, which would
    have fed the solver and produced a confident wrong answer. UPS context is
    now required near the figure."""
    req = _req()
    assert req["ups_kva"] is None


def test_scope_is_not_inflated_by_incidental_mentions():
    """REGRESSION — the most serious defect found. The word "cooling"
    appears exactly once in 101 pages, inside a list of lightning-conductor
    attachment points. That single mention put Thermal Management in scope,
    where it was then classified CTO_AUTOMATE: a false-automation result on
    a layer the RFP never asked about.

    Scope is now decided on weight of evidence.
    """
    req = _req()
    scope = req["layers_in_scope"]
    assert 2 in scope, "switchgear (163 mentions) must be in scope"
    assert 5 not in scope, "thermal must NOT be in scope from one stray mention"
    assert 6 not in scope, "compute must NOT be in scope"
    assert 4 not in scope, "rack power must NOT be in scope"


def test_scope_decision_is_explainable():
    """Every scope decision must state its basis, so a human can audit it."""
    req = _req()
    ev = req["scope_evidence"]
    assert ev[2]["in_scope"] and ev[2]["hits"] > 100
    assert not ev[5]["in_scope"]
    for n in range(1, 7):
        assert ev[n]["basis"]


def test_layer2_routes_to_crown_on_the_real_document():
    """The headline routing decision must survive the genuine document."""
    txt = _text()
    req = _req()
    tiers = tc.run(req, txt)["tiers"]
    l2 = next(t for t in tiers if t["n"] == 2)
    assert l2["tier"] == "ETO_GUIDED"
    assert any("Crown" in b for b in l2["hinted_brands"])


def test_no_out_of_scope_layer_is_marked_automatable():
    """The safety property: nothing outside scope should be presented as
    automatable work."""
    txt = _text()
    req = _req()
    scope = set(req["layers_in_scope"])
    tiers = tc.run(req, txt)["tiers"]
    for t in tiers:
        if t["n"] not in scope and t["tier"] == "CTO_AUTOMATE":
            assert t["n"] not in (5, 6), f"L{t['n']} out of scope yet marked automatable"
