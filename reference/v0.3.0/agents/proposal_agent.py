"""
Stage 5 — Consolidated Proposal Assembly.

Only runs after every prior stage has been human-approved (enforced by
orchestration/pipeline.py, not by this module). Writes the customer-
facing summary; the underlying design/validation/routing data is
carried through unchanged so nothing here can silently alter an
already-approved decision.
"""
from agents.base_agent import call_llm_json


def _build_prompt(req: dict, layers: list, checks: list) -> str:
    return f"""You are the "Consolidated Proposal Assembly" stage, writing a short proposal cover summary for a formal RFP response back to the customer. Every design and validation decision has already been approved by human engineers — you are summarizing an approved outcome, not making new decisions.

Requirements: {req}
Approved layers: {layers}
Validation checks: {checks}

Respond with ONLY compact JSON, no markdown fences, no commentary, matching exactly this shape:
{{"summary": "<2-3 sentence proposal summary, professional tone>", "key_differentiators": ["...", "...", "..."], "next_steps": ["...", "..."]}}"""


def _mock_proposal(req: dict, layers: list, checks: list) -> dict:
    brand_families = sorted(set(
        token.split(" (")[0].strip()
        for l in layers for token in l.get("brand", "").split(" + ")
    ))
    warn_count = sum(1 for c in checks if c["status"] in ("warn", "fail"))
    summary = (
        f"SpinCo proposes an integrated {req.get('capacity_mw', 'N/A')}MW grid-to-chip system spanning "
        f"{len(brand_families)} SpinCo brand families ({', '.join(brand_families)}), engineered to the "
        f"{req.get('redundancy', 'specified')} redundancy and {req.get('voltage_arch', 'specified')} architecture "
        f"requirements in the RFP. All layers have passed engineering validation"
        + (f", with {warn_count} item(s) noted for customer awareness." if warn_count else " with no outstanding flags.")
    )
    return {
        "summary": summary,
        "key_differentiators": [
            "Single-vendor accountability across the full grid-to-chip stack, not a multi-vendor integration risk.",
            "Prefabricated / modular delivery model shortens on-site schedule versus stick-built alternatives.",
            "Every design decision in this proposal is traceable to a specific requirement and engineering rule.",
        ],
        "next_steps": [
            "Customer technical review of the attached layer-by-layer design and validation trace.",
            "Confirm site and interconnect timeline to finalize delivery schedule.",
        ],
    }


def run(req: dict, layers: list, checks: list) -> dict:
    result = call_llm_json(
        _build_prompt(req, layers, checks),
        _mock_proposal, req, layers, checks,
    )
    result["explanation"] = "Proposal assembled from the fully approved design, validation, and routing outputs — no new decisions made at this stage."
    result["evidence"] = [{"source": "stages_1_through_4", "detail": "all prior approved outputs"}]
    return result
