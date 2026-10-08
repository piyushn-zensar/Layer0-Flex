"""
CI gate for model change. If any blessed extraction regresses, this test
fails and the model change must not merge.

The test also proves the guard has teeth: a deliberately regressed
extractor must be caught, not silently passed. A guard that cannot fail
is not a guard.
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents import model_guard

PDF = (Path(__file__).resolve().parent.parent / "knowledge_base" /
       "sample_rfps" / "real_pdfs" / "RFP-2023-20-Switchgear-Procurement-Final.pdf")

pytestmark = pytest.mark.skipif(not PDF.exists(), reason="real PDF fixture not present")


def test_current_extractor_passes_the_golden_set():
    report = model_guard.check()
    failing = [r for r in report["results"] if r["status"] != "PASS"]
    assert not failing, f"Extractor regressed against blessed answers: {failing}"
    assert report["verdict"] == "SHIP"


def test_guard_catches_a_reintroduced_bug():
    """The transformer-as-UPS bug the real Syracuse document exposed must
    be caught if a model reintroduces it."""
    import agents.understand_agent as ua
    real = ua.run

    def regressed(text):
        r = real(text)
        if "Metal Clad Switchgear" in text:
            r["ups_kva"] = 112.5   # the exact defect
        return r

    model_guard.understand_agent.run = regressed
    try:
        report = model_guard.check()
    finally:
        model_guard.understand_agent.run = real

    assert report["verdict"] == "REJECT"
    syr = next(r for r in report["results"] if r["case_id"] == "RFP-SYR-2023-20")
    assert syr["status"] == "FAIL"
    assert any("ups_kva" in f for f in syr["failures"])


def test_guard_catches_scope_regression():
    """A model that scopes Thermal in from the single stray 'cooling'
    mention must be caught."""
    import agents.understand_agent as ua
    real = ua.run

    def regressed(text):
        r = real(text)
        if "Metal Clad Switchgear" in text:
            r["layers_in_scope"] = sorted(set((r.get("layers_in_scope") or []) + [5]))
        return r

    model_guard.understand_agent.run = regressed
    try:
        report = model_guard.check()
    finally:
        model_guard.understand_agent.run = real

    assert report["verdict"] == "REJECT"
