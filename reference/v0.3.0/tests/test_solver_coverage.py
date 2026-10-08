"""Tests for M13 (solver), M14 (coverage map) and M15 (proposal checker)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents import understand_agent as ua, tier_classifier as tc, design_agent as da
from agents import solver, coverage
from provenance.anchors import DocumentRef

SAMPLES = Path(__file__).resolve().parent.parent / "knowledge_base" / "sample_rfps"


def _pipeline(name):
    txt = (SAMPLES / name).read_text()
    req = ua.run(txt)
    tiers = tc.run(req, txt)["tiers"]
    layers = da.run(req)["layers"]
    sr = solver.run(req, layers, tiers)
    return txt, req, tiers, layers, sr


# --- M13 solver ---

def test_solver_solves_lv_distribution_on_real_ups_rfp():
    _, req, _, _, sr = _pipeline("rfp_REAL_ftlauderdale_ups.txt")
    solved = [r for r in sr["results"] if r["status"].startswith("SOLVED")]
    assert solved, "Ft. Lauderdale UPS scope must be solvable"
    r = solved[0]
    # 45 kVA x 0.8 derating x 0.9 PF = 32.4 kW over 10 racks = 3.24 kW/rack
    assert abs(r["result"]["usable_capacity_kw"] - 32.4) < 0.01
    assert abs(r["result"]["capacity_per_rack_kw"] - 3.24) < 0.01


def test_every_solved_step_cites_a_reference():
    """An engineer must be able to check each number against a standard."""
    _, _, _, _, sr = _pipeline("rfp_REAL_ftlauderdale_ups.txt")
    solved = [r for r in sr["results"] if r["status"].startswith("SOLVED")][0]
    assert solved["working"]
    for step in solved["working"]:
        assert step["reference"], f"step '{step['step']}' has no reference"


def test_solver_refuses_all_layers_on_mv_switchgear_rfp():
    """Bespoke 15kV switchgear must never be solved arithmetically."""
    _, _, _, _, sr = _pipeline("rfp_REAL_syracuse_switchgear.txt")
    assert all(r["status"] == "NOT_SOLVABLE" for r in sr["results"])
    assert all(r["reasons"] for r in sr["results"])


def test_solver_refuses_rather_than_assuming_missing_inputs():
    out = solver.solve_lv_distribution({"ups_kva": None, "rack_count": 10})
    assert out["status"] == "NOT_SOLVABLE"
    assert "ups_kva" in out["reasons"][0]


def test_solved_output_carries_standards_caveat():
    _, _, _, _, sr = _pipeline("rfp_REAL_ftlauderdale_ups.txt")
    solved = [r for r in sr["results"] if r["status"].startswith("SOLVED")][0]
    assert "Subject to SpinCo" in solved["standards_note"]


# --- M14 coverage map ---

def test_coverage_map_reports_unreviewed_regions_honestly():
    """Coverage must never be claimed over unsegmented text."""
    txt, req, tiers, _, sr = _pipeline("rfp_REAL_syracuse_switchgear.txt")
    cm = coverage.build_coverage_map(txt, req, tiers, sr["results"])
    assert cm["rows"]
    assert "UNREVIEWED" in cm["summary"]
    assert cm["unreviewed_regions"] >= 0


def test_coverage_map_marks_commercial_clauses_out_of_scope_by_design():
    txt, req, tiers, _, sr = _pipeline("rfp_REAL_syracuse_switchgear.txt")
    cm = coverage.build_coverage_map(txt, req, tiers, sr["results"])
    assert any(r["disposition"] == "OUT_OF_SCOPE_BY_DESIGN" for r in cm["rows"])


def test_coverage_rows_carry_source_anchors():
    txt, req, tiers, _, sr = _pipeline("rfp_REAL_syracuse_switchgear.txt")
    cm = coverage.build_coverage_map(txt, req, tiers, sr["results"])
    anchored = [r for r in cm["rows"] if r["source_anchor"]]
    assert len(anchored) >= len(cm["rows"]) // 2


# --- M15 proposal checker ---

_PROPOSAL_OMITTING_ARC = """PROPOSAL - Crown Technical Systems
We propose a 15kV two-section Metal Clad Switchgear lineup.
Breaker positions: 18 vacuum circuit breaker positions with protective relays.
Incoming supply: Two 13.2 kV utility feeders from National Grid.
Compliance: IEEE C37.20.2, NFPA 70.
"""


def test_checker_flags_requirements_missing_from_proposal():
    """The proposal omits instrument transformers and future bays entirely."""
    txt, req, tiers, _, sr = _pipeline("rfp_REAL_syracuse_switchgear.txt")
    cm = coverage.build_coverage_map(txt, req, tiers, sr["results"])
    chk = coverage.check_proposal(cm, _PROPOSAL_OMITTING_ARC, txt)
    gaps = [f for f in chk["findings"] if f["status"] in ("NOT_FOUND", "DEVIATION")]
    assert gaps, "checker must flag omissions"


def test_checker_never_asserts_conformance():
    """Fail-safe: the checker is advisory and never approves."""
    txt, req, tiers, _, sr = _pipeline("rfp_REAL_syracuse_switchgear.txt")
    cm = coverage.build_coverage_map(txt, req, tiers, sr["results"])
    chk = coverage.check_proposal(cm, _PROPOSAL_OMITTING_ARC, txt)
    statuses = {f["status"] for f in chk["findings"]}
    assert "CONFORMS" not in statuses
    assert statuses <= {"APPEARS_ADDRESSED", "NOT_FOUND", "DEVIATION"}
    assert "ADVISORY" in chk["explanation"] or "advisory" in chk["advisory_notice"].lower()


def test_checker_findings_link_both_documents():
    txt, req, tiers, _, sr = _pipeline("rfp_REAL_syracuse_switchgear.txt")
    cm = coverage.build_coverage_map(txt, req, tiers, sr["results"])
    chk = coverage.check_proposal(cm, _PROPOSAL_OMITTING_ARC, txt)
    assert any(f["rfp_anchor"] for f in chk["findings"])


def test_checker_states_addenda_not_handled():
    txt, req, tiers, _, sr = _pipeline("rfp_REAL_syracuse_switchgear.txt")
    cm = coverage.build_coverage_map(txt, req, tiers, sr["results"])
    chk = coverage.check_proposal(cm, _PROPOSAL_OMITTING_ARC, txt)
    assert "addenda not yet handled" in str(chk["evidence"])
