"""
Model-change regression guard.

Answers the question a serious technical reviewer will ask: "what happens
when you change the LLM?" The answer is: it must first reproduce every
blessed extraction in knowledge_base/accepted_extractions.json, or the
change is rejected.

The control is not that the model "obeys" a rule file — a probabilistic
model cannot be made to obey. The control is that the model must PASS an
exam of known-correct answers before it is allowed to ship. This turns
every real document we have processed and blessed into a permanent
regression guard, so a fixed bug cannot silently return.

Positive assertions (must_extract)  : the value the model must produce.
Negative assertions (must_not_extract): a value the model must NOT produce.
                                        These pin the fixed bugs — e.g. a
                                        transformer rating must never be
                                        read as a UPS.

Run directly:   python -m agents.model_guard
As a test:      pytest tests/test_model_guard.py
"""
from __future__ import annotations

import json
from pathlib import Path

from config import settings
from ingestion import ingest
from agents import understand_agent

ACCEPTED = settings.KNOWLEDGE_BASE_DIR / "accepted_extractions.json"


def _load_accepted() -> dict:
    with open(ACCEPTED) as f:
        return json.load(f)


def _extract_for_case(case: dict, project_root: Path) -> dict:
    fixture = project_root / case["fixture"]
    res = ingest.ingest_path(fixture)
    if not res.primary:
        raise RuntimeError(f"{case['case_id']}: fixture produced no text: {fixture}")
    return understand_agent.run(res.primary.text)


def check() -> dict:
    """Runs the current extractor over every accepted case and returns a
    structured pass/fail report. A failure means the current model has
    regressed against a blessed answer."""
    project_root = Path(__file__).resolve().parent.parent
    accepted = _load_accepted()
    results = []

    for case in accepted["cases"]:
        cid = case["case_id"]
        failures = []
        try:
            extracted = _extract_for_case(case, project_root)
        except Exception as e:
            results.append({"case_id": cid, "status": "ERROR", "failures": [str(e)]})
            continue

        # --- positive assertions ---
        for key, expected in case.get("must_extract", {}).items():
            if key.endswith("_contains"):
                real_key = key[:-len("_contains")]
                actual = extracted.get(real_key)
                if actual is None or str(expected).lower() not in str(actual).lower():
                    failures.append(
                        f"must_extract {real_key} should contain '{expected}', got '{actual}'")
            else:
                actual = extracted.get(key)
                if actual != expected:
                    failures.append(
                        f"must_extract {key} should be {expected!r}, got {actual!r}")

        # --- negative assertions ---
        for key, why in case.get("must_not_extract", {}).items():
            if key == "layer_5_in_scope":
                if 5 in (extracted.get("layers_in_scope") or []):
                    failures.append(f"must_not: Layer 5 in scope. {why}")
            elif key == "layer_6_in_scope":
                if 6 in (extracted.get("layers_in_scope") or []):
                    failures.append(f"must_not: Layer 6 in scope. {why}")
            else:
                actual = extracted.get(key)
                if actual is not None:
                    failures.append(f"must_not_extract {key} should be absent, got {actual!r}. {why}")

        # --- scope assertion ---
        if "must_scope" in case:
            actual_scope = sorted(extracted.get("layers_in_scope") or [])
            if actual_scope != sorted(case["must_scope"]):
                failures.append(
                    f"scope should be {sorted(case['must_scope'])}, got {actual_scope}")

        results.append({
            "case_id": cid,
            "status": "PASS" if not failures else "FAIL",
            "failures": failures,
        })

    passed = sum(1 for r in results if r["status"] == "PASS")
    return {
        "llm_mode": settings.LLM_MODE,
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
        "verdict": "SHIP" if passed == len(results) else "REJECT",
        "note": ("A REJECT means the current extractor/model regresses against a blessed "
                 "answer. Do not ship the model change until it passes, and never edit an "
                 "accepted value to force a pass."),
    }


def main():
    report = check()
    print(f"Model-change guard — LLM_MODE={report['llm_mode']}")
    print(f"  {report['passed']}/{report['total']} cases pass  ->  {report['verdict']}")
    for r in report["results"]:
        mark = {"PASS": "\u2713", "FAIL": "\u2717", "ERROR": "!"}[r["status"]]
        print(f"  {mark} {r['case_id']}")
        for f in r["failures"]:
            print(f"      - {f}")
    return 0 if report["verdict"] == "SHIP" else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
