"""
Runs both sample RFPs through the full five-stage pipeline in mock
mode, approving every stage automatically, and prints the result.
This is a smoke test for the orchestration logic — it exercises every
agent, the RAG retriever, the deterministic rules engine, and the
state store, without needing a running llama.cpp server.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from orchestration import pipeline


def run_sample(path: Path):
    rfp_text = path.read_text()
    print(f"\n{'='*70}\nRunning: {path.name}\n{'='*70}")

    run = pipeline.start_run(rfp_text)
    print(f"Run ID: {run['run_id']}")

    while run["status"] == "awaiting_approval":
        stage_n = run["current_stage"]
        stage_name = pipeline.STAGE_NAMES[stage_n]
        output = run["stage_outputs"][str(stage_n)]
        print(f"\n--- Stage {stage_n}: {stage_name} ---")
        print(f"Explanation: {output.get('explanation', '(none)')}")
        run = pipeline.approve_and_advance(run["run_id"], approver="smoke-test", note="auto-approved")

    print(f"\nFinal status: {run['status']}")
    assert run["status"] == "completed", f"Expected completed, got {run['status']}"
    proposal = run["stage_outputs"]["6"]
    print(f"\nProposal summary: {proposal['summary']}")


    # sanity assertions
    assert "1" in run["stage_outputs"] and "6" in run["stage_outputs"]
    assert len(run["approvals"]) == 6, f"Expected 6 approvals, got {len(run['approvals'])}"
    assert run["stage_outputs"]["3"]["layers"], "Stage 3 must produce 6 layers"
    assert len(run["stage_outputs"]["3"]["layers"]) == 6
    print("\nAll assertions passed for this sample.")
    return run


if __name__ == "__main__":
    print(f"LLM_MODE = {settings.LLM_MODE}")
    assert settings.LLM_MODE == "mock", "This smoke test is designed to run in mock mode."

    sample_dir = settings.SAMPLE_RFP_DIR
    results = []
    for sample_file in sorted(sample_dir.glob("*.txt")):
        results.append(run_sample(sample_file))

    print(f"\n{'='*70}\nSMOKE TEST COMPLETE — {len(results)} sample(s) ran end-to-end successfully.\n{'='*70}")
