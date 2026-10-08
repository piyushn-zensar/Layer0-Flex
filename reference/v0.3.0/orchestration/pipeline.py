"""
Pipeline orchestration with mandatory approval gates.

Core rule, enforced here and nowhere else: no stage N+1 ever runs until
a human has explicitly approved stage N's output. This is not a UI
suggestion — `approve_and_advance` is the only function that causes a
subsequent stage to execute, and it refuses to do so unless the current
stage's status is genuinely "awaiting_approval". There is no code path
that lets the pipeline complete without a human approval recorded at
every one of the five stages.
"""
from datetime import datetime, timezone

from agents import (understand_agent, design_agent, validation_agent, routing_agent,
                    proposal_agent, tier_classifier, solver, coverage)
from orchestration import state_store

STAGE_NAMES = {
    1: "Understand",
    2: "Scope & Tier Classification",
    3: "Draft System Design",
    4: "Validation",
    5: "Solve or Refuse",
    6: "Coverage Map & Routing",
}


class PipelineError(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_stage(stage_n: int, run_data: dict) -> dict:
    outputs = run_data["stage_outputs"]
    rfp_text = run_data["rfp_text"]
    if stage_n == 1:
        return understand_agent.run(rfp_text)
    if stage_n == 2:
        return tier_classifier.run(outputs["1"], rfp_text)
    if stage_n == 3:
        return design_agent.run(outputs["1"])
    if stage_n == 4:
        return validation_agent.run(outputs["1"], outputs["3"]["layers"])
    if stage_n == 5:
        return solver.run(outputs["1"], outputs["3"]["layers"], outputs["2"]["tiers"])
    if stage_n == 6:
        cov = coverage.build_coverage_map(
            rfp_text, outputs["1"], outputs["2"]["tiers"], outputs["5"]["results"])
        routed = routing_agent.run(outputs["3"]["layers"])
        return {**cov, "work_packages": routed["work_packages"],
                "explanation": cov["explanation"] + " " + routed["explanation"],
                "evidence": cov["evidence"] + routed["evidence"]}
    raise PipelineError(f"Unknown stage number: {stage_n}")


def start_run(rfp_text: str) -> dict:
    run_id = state_store.create_run(rfp_text)
    run_data = state_store.get_run(run_id)

    stage_output = _run_stage(1, run_data)
    run_data["stage_outputs"]["1"] = stage_output
    run_data["current_stage"] = 1
    run_data["status"] = "awaiting_approval"
    state_store.save_run(run_id, run_data)
    return run_data


def get_run(run_id: str) -> dict:
    return state_store.get_run(run_id)


def list_runs() -> list:
    return state_store.list_runs()


def approve_and_advance(run_id: str, approver: str = "unknown", note: str = "") -> dict:
    run_data = state_store.get_run(run_id)
    if run_data["status"] != "awaiting_approval":
        raise PipelineError(
            f"Run {run_id} is not awaiting approval (status: {run_data['status']}). "
            f"Cannot advance a pipeline that isn't paused at an approval gate."
        )

    current_stage = run_data["current_stage"]
    run_data["approvals"][str(current_stage)] = {
        "approved": True, "approver": approver, "note": note, "timestamp": _now(),
    }

    if current_stage >= 6:
        run_data["status"] = "completed"
        state_store.save_run(run_id, run_data)
        return run_data

    next_stage = current_stage + 1
    stage_output = _run_stage(next_stage, run_data)
    run_data["stage_outputs"][str(next_stage)] = stage_output
    run_data["current_stage"] = next_stage
    run_data["status"] = "awaiting_approval"
    state_store.save_run(run_id, run_data)
    return run_data


def reject(run_id: str, approver: str = "unknown", reason: str = "") -> dict:
    run_data = state_store.get_run(run_id)
    if run_data["status"] != "awaiting_approval":
        raise PipelineError(f"Run {run_id} is not awaiting approval (status: {run_data['status']}).")

    current_stage = run_data["current_stage"]
    run_data["approvals"][str(current_stage)] = {
        "approved": False, "approver": approver, "note": reason, "timestamp": _now(),
    }
    run_data["status"] = "rejected"
    state_store.save_run(run_id, run_data)
    return run_data
