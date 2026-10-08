"""Tests for the REQ-xxxx requirement registry (models/)."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.registry import (Requirement, RequirementRegistry, RegistryAnchor,
                             Classification, Coverage, DerivedChain)
from models.registry_builder import build_registry, diff_against_proposal


def _anchor():
    return RegistryAnchor(doc_id="RFP", version="v1", page=1, span=(10, 30),
                          quote="Arc-resistant Type 2B")


def test_extracted_requires_anchor():
    with pytest.raises(ValueError):
        Requirement(req_id="REQ-0001", title="t", raw_text="x",
                    provenance_class="EXTRACTED", source_anchor=None)


def test_derived_requires_chain():
    with pytest.raises(ValueError):
        Requirement(req_id="REQ-0002", title="t", raw_text="x",
                    provenance_class="DERIVED", derived_chain=None)


def test_unanchored_requires_reason():
    with pytest.raises(ValueError):
        Requirement(req_id="REQ-0003", title="t", raw_text="x",
                    provenance_class="UNANCHORED", unanchored_reason=None)


def test_valid_extracted_requirement_constructs():
    r = Requirement(req_id="REQ-0004", title="Arc", raw_text="arc-resistant Type 2B",
                    provenance_class="EXTRACTED", source_anchor=_anchor())
    assert r.governance.status == "UNREVIEWED"
    assert r.provenance_class == "EXTRACTED"


def test_coverage_summary_reports_honest_denominator():
    reg = RequirementRegistry(case_id="C1", unreviewed_regions=5)
    reg.add(Requirement(req_id="REQ-0001", title="a", raw_text="x",
                        provenance_class="EXTRACTED", source_anchor=_anchor(),
                        coverage=Coverage(disposition="SOLVED")))
    reg.add(Requirement(req_id="REQ-0002", title="b", raw_text="y",
                        provenance_class="UNANCHORED", unanchored_reason="paraphrase"))
    s = reg.coverage_summary()
    assert s["total_requirements"] == 2
    assert s["anchored"] == 1 and s["unanchored"] == 1
    assert s["unreviewed_source_regions"] == 5
    assert "over segmented requirements only" in s["note"]


def test_builds_from_real_pipeline_output():
    """The registry must assemble from the actual coverage map + tiers, not
    hand-built dicts."""
    from ingestion import ingest
    from agents import understand_agent as ua, tier_classifier as tc, design_agent as da
    from agents import solver, coverage
    pdf = (Path(__file__).resolve().parent.parent / "knowledge_base" /
           "sample_rfps" / "real_pdfs" / "RFP-2023-20-Switchgear-Procurement-Final.pdf")
    if not pdf.exists():
        pytest.skip("real PDF not present")
    txt = ingest.ingest_path(pdf).primary.text
    req = ua.run(txt); tiers = tc.run(req, txt); layers = da.run(req)
    sr = solver.run(req, layers["layers"], tiers["tiers"])
    cm = coverage.build_coverage_map(txt, req, tiers["tiers"], sr["results"])
    reg = build_registry("CASE-SYR", cm, tiers)
    assert len(reg.requirements) == len(cm["rows"])
    assert all(r.req_id.startswith("REQ-") for r in reg.requirements)
    # every requirement that anchored carries a real page
    for r in reg.requirements:
        if r.provenance_class == "EXTRACTED":
            assert r.source_anchor.page >= 1


def test_proposal_diff_pivots_on_requirement_ids():
    """The RFP-vs-proposal diff must operate on REQ ids, never fuzzy text."""
    reg = RequirementRegistry(case_id="C1")
    reg.add(Requirement(req_id="REQ-0001", title="Clause 3.2", raw_text="arc-resistant",
                        provenance_class="EXTRACTED", source_anchor=_anchor()))
    checker_output = {"findings": [
        {"clause_id": "3.2", "status": "NOT_FOUND", "note": "arc-resistance absent"}]}
    reg = diff_against_proposal(reg, checker_output)
    assert reg.requirements[0].coverage.proposal_check_status == "NOT_FOUND"
