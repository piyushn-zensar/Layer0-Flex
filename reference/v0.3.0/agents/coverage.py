"""
Modules M14 (Coverage Map) and M15 (Proposal Checker).

M14 — COVERAGE MAP
------------------
Answers "does this actually satisfy the RFP?" by walking the source
document clause by clause and recording, for each requirement: what was
extracted from it, how it was classified, what happened to it, and where
in the document it came from.

The value is not showing what was handled. It is showing what was NOT —
and stating whether that is a gap or a deliberate boundary. A clause
that nobody looked at is reported as UNREVIEWED rather than quietly
omitted, because claiming "47 of 47 clauses" when 61 exist is worse
than claiming nothing.

M15 — PROPOSAL CHECKER
----------------------
For work the solver cannot touch — bespoke switchgear, novel topologies —
the system previously stopped at handoff and never saw the outcome. The
checker closes that loop: when an engineer's proposal returns, it is
compared back against the RFP clause by clause.

This is a fundamentally different task from solving. It requires no
engineering judgment: it is reading two documents and finding what is in
one but not the other. A language model is well suited to it, and the
liability profile is inverted — the risk is in MISSING something, which
is exactly what a checker exists to catch.

FAIL-SAFE DIRECTION
-------------------
The checker is biased toward flagging. A false "missing" is cheap: an
engineer glances and dismisses it. A false "covered" is dangerous: it
reports a clause as handled when it is not. The checker therefore never
emits "conforms" — only "appears addressed, verify" with anchors into
both documents. It is advisory, never approving.
"""
import re

from agents.base_agent import call_llm_json
from provenance.anchors import DocumentRef, paginate, anchor_quote


# ---------------------------------------------------------------------
# M14 — Clause segmentation and coverage
# ---------------------------------------------------------------------

# Matches numbered sections (3.2, 3.2.1), lettered appendices, and the
# dash-bulleted requirement lines common in public procurement documents.
_CLAUSE_PATTERNS = [
    re.compile(r"^\s*(?:§|Section\s+)?(\d+(?:\.\d+)+)\s*[\.\)\-:]?\s+(.{10,})$", re.I),
    re.compile(r"^\s*(Appendix\s+[A-Z])\s*[\.\)\-:]?\s+(.{10,})$", re.I),
    re.compile(r"^\s*[-\u2022]\s*([A-Z][A-Za-z /&]{3,40}):\s*(.{5,})$"),
]


def segment_clauses(rfp_text: str) -> dict:
    """Splits an RFP into addressable clauses.

    Real RFPs number inconsistently, nest sub-clauses, and put binding
    requirements in tables and appendices. Where no explicit marker is
    found, the region is reported as unsegmented rather than silently
    dropped — the coverage denominator must be honest.
    """
    clauses, unsegmented = [], []
    for lineno, line in enumerate(rfp_text.split("\n"), start=1):
        stripped = line.strip()
        if not stripped or len(stripped) < 8:
            continue
        matched = False
        for pat in _CLAUSE_PATTERNS:
            m = pat.match(stripped)
            if m:
                clauses.append({
                    "clause_id": m.group(1).strip(),
                    "text": m.group(2).strip(),
                    "line": lineno,
                })
                matched = True
                break
        if not matched and len(stripped) > 40 and not stripped.startswith(("---", "NOTE", "SOURCE", "URL")):
            unsegmented.append({"line": lineno, "text": stripped[:120]})
    return {"clauses": clauses, "unsegmented": unsegmented}


def _clause_outcome(clause: dict, requirements: dict, tiers: list,
                    solver_results: list, out_of_scope_markers: list) -> dict:
    """Determines what happened to a single clause."""
    text = (clause["clause_id"] + " " + clause["text"]).lower()

    # 1. Explicitly out of scope by design (commercial/administrative)
    for marker, reason in out_of_scope_markers:
        if marker in text:
            return {"disposition": "OUT_OF_SCOPE_BY_DESIGN", "detail": reason,
                    "extracted": None, "tier": None}

    # 2. Did any extracted parameter come from this clause?
    matched_param = None
    for key in ("voltage_class_kv", "arc_resistant", "breaker_positions", "ups_kva",
                "rack_count", "branch_circuits", "capacity_mw", "redundancy",
                "compliance", "onsite_generation"):
        val = requirements.get(key)
        if val is None:
            continue
        token = str(val).split(",")[0].strip().lower()[:18]
        if token and token in text:
            matched_param = (key, val)
            break

    if matched_param:
        key, val = matched_param
        layer = _layer_for_param(key)
        tier = next((t["tier"] for t in tiers if t["n"] == layer), None) if layer else None
        solved = next((r for r in solver_results
                       if r["layer"] == layer and r["status"] != "NOT_SOLVABLE"), None)
        return {
            "disposition": "EXTRACTED_AND_ROUTED" if solved else "CAPTURED_NOT_DESIGNED",
            "detail": ("Solved arithmetically" if solved
                       else "Requires engineering; captured in basis of design"),
            "extracted": f"{key}: {val}",
            "tier": tier,
        }

    # 3. Recognisably technical but nothing extracted
    if any(k in text for k in ("kv", "kva", "amp", "voltage", "ieee", "nfpa", "nec",
                               "switchgear", "breaker", "busbar", "cooling", "ups")):
        return {"disposition": "NOT_HANDLED", "extracted": None, "tier": None,
                "detail": "Technical requirement not extracted — possible coverage gap"}

    return {"disposition": "NOT_HANDLED", "extracted": None, "tier": None,
            "detail": "No extraction matched this clause"}


def _layer_for_param(key: str):
    return {
        "capacity_mw": 1, "onsite_generation": 1,
        "voltage_class_kv": 2, "arc_resistant": 2, "breaker_positions": 2,
        "branch_circuits": 3,
        "ups_kva": 4, "rack_count": 4,
    }.get(key)


def build_coverage_map(rfp_text: str, requirements: dict, tiers: list,
                       solver_results: list, doc: DocumentRef = None) -> dict:
    """M14 entry point."""
    doc = doc or DocumentRef(doc_id="rfp", version="as-submitted")
    pages = paginate(rfp_text)
    seg = segment_clauses(rfp_text)

    out_of_scope_markers = [
        ("mwbe", "Commercial/administrative participation goal — out of scope by design"),
        ("sdvob", "Commercial/administrative participation goal — out of scope by design"),
        ("participation goal", "Commercial/administrative — out of scope by design"),
        ("lump sum", "Commercial pricing basis — out of scope by design"),
        ("payment", "Commercial term — out of scope by design"),
        ("warranty", "Commercial term — out of scope by design"),
        ("bidder must submit", "Administrative submission requirement — out of scope by design"),
    ]

    rows = []
    for clause in seg["clauses"]:
        outcome = _clause_outcome(clause, requirements, tiers, solver_results,
                                  out_of_scope_markers)
        a = anchor_quote(clause["text"][:60], pages, doc)
        rows.append({
            "clause_id": clause["clause_id"],
            "requirement": clause["text"][:140],
            **outcome,
            "source_anchor": a.to_dict() if a else None,
        })

    counts = {}
    for r in rows:
        counts[r["disposition"]] = counts.get(r["disposition"], 0) + 1

    total = len(rows)
    summary = (
        f"Of {total} identified requirements: "
        f"{counts.get('EXTRACTED_AND_ROUTED', 0)} extracted and routed, "
        f"{counts.get('CAPTURED_NOT_DESIGNED', 0)} captured but not designed, "
        f"{counts.get('OUT_OF_SCOPE_BY_DESIGN', 0)} out of scope by design, "
        f"{counts.get('NOT_HANDLED', 0)} not handled. "
        f"{len(seg['unsegmented'])} region(s) were not segmented into clauses and are "
        f"reported as UNREVIEWED — coverage is claimed only over segmented clauses."
    )

    return {
        "rows": rows,
        "counts": counts,
        "unreviewed_regions": len(seg["unsegmented"]),
        "summary": summary,
        "explanation": summary,
        "evidence": [{"source": "clause segmentation over source document",
                      "clauses_identified": total,
                      "unsegmented_regions": len(seg["unsegmented"])}],
    }


# ---------------------------------------------------------------------
# M15 — Proposal checker
# ---------------------------------------------------------------------

def _build_check_prompt(coverage_rows: list, proposal_text: str) -> str:
    clauses = [{"clause_id": r["clause_id"], "requirement": r["requirement"]}
               for r in coverage_rows
               if r["disposition"] != "OUT_OF_SCOPE_BY_DESIGN"][:40]
    return f"""You are checking an engineering proposal against the requirements of the RFP it responds to. You are NOT evaluating whether the engineering is correct — only whether each requirement appears to be addressed.

Be biased toward flagging. A false "missing" costs an engineer ten seconds to dismiss. A false "addressed" means a requirement silently goes unmet. Never assert that something conforms; only that it appears addressed and should be verified.

RFP requirements:
{clauses}

Proposal text:
\"\"\"
{proposal_text[:6000]}
\"\"\"

Respond with ONLY compact JSON, no markdown fences, matching exactly:
{{"findings": [{{"clause_id": "...", "status": "APPEARS_ADDRESSED|NOT_FOUND|DEVIATION", "note": "<short>", "proposal_quote": "<verbatim quote from the proposal, or empty string>"}}]}}"""


def _mock_check(coverage_rows: list, proposal_text: str) -> dict:
    """Deterministic checker used when LLM_MODE=mock. Token-overlap based,
    biased toward NOT_FOUND, so the fail-safe direction holds in tests."""
    lower = proposal_text.lower()
    findings = []
    for r in coverage_rows:
        if r["disposition"] == "OUT_OF_SCOPE_BY_DESIGN":
            continue
        req = r["requirement"].lower()
        tokens = [t for t in re.findall(r"[a-z0-9\.]{4,}", req) if t not in
                  ("shall", "with", "that", "this", "from", "each", "the")][:6]
        if not tokens:
            continue
        hits = [t for t in tokens if t in lower]
        ratio = len(hits) / len(tokens)
        quote = ""
        if hits:
            idx = lower.find(hits[0])
            if idx != -1:
                quote = proposal_text[max(0, idx - 30): idx + 70].strip()
        if ratio >= 0.5:
            status, note = "APPEARS_ADDRESSED", f"{len(hits)}/{len(tokens)} key terms present — verify"
        elif ratio > 0:
            status, note = "DEVIATION", f"Partial match ({len(hits)}/{len(tokens)} terms) — possible deviation, review"
        else:
            status, note = "NOT_FOUND", "No matching content located in the proposal"
        findings.append({"clause_id": r["clause_id"], "status": status,
                         "note": note, "proposal_quote": quote})
    return {"findings": findings}


def check_proposal(coverage_map: dict, proposal_text: str,
                   rfp_text: str = "", doc: DocumentRef = None) -> dict:
    """M15 entry point. Compares a returned engineering proposal against
    the RFP requirements captured in the coverage map."""
    rows = coverage_map["rows"]
    result = call_llm_json(
        _build_check_prompt(rows, proposal_text),
        _mock_check, rows, proposal_text,
    )

    prop_doc = DocumentRef(doc_id="proposal", version="as-received")
    prop_pages = paginate(proposal_text)
    by_id = {r["clause_id"]: r for r in rows}

    findings = []
    for f in result.get("findings", []):
        row = by_id.get(f["clause_id"], {})
        anchor = anchor_quote(f.get("proposal_quote", ""), prop_pages, prop_doc)
        findings.append({
            "clause_id": f["clause_id"],
            "requirement": row.get("requirement"),
            "rfp_anchor": row.get("source_anchor"),
            "status": f["status"],
            "note": f["note"],
            "proposal_anchor": anchor.to_dict() if anchor else None,
        })

    counts = {}
    for f in findings:
        counts[f["status"]] = counts.get(f["status"], 0) + 1

    gaps = counts.get("NOT_FOUND", 0) + counts.get("DEVIATION", 0)
    return {
        "findings": findings,
        "counts": counts,
        "explanation": (
            f"Checked {len(findings)} requirement(s) against the returned proposal: "
            f"{counts.get('APPEARS_ADDRESSED', 0)} appear addressed, "
            f"{counts.get('DEVIATION', 0)} possible deviation(s), "
            f"{counts.get('NOT_FOUND', 0)} not located. "
            f"{gaps} item(s) require engineering review before submission. "
            f"This check is ADVISORY — it verifies coverage, not engineering correctness, "
            f"and never approves a proposal."
        ),
        "advisory_notice": ("This checker reports whether requirements appear addressed. "
                            "It does not verify that the engineering is correct, and it "
                            "does not constitute approval."),
        "evidence": [{"source": "coverage map vs proposal document",
                      "compared_against": "original RFP as submitted (addenda not yet handled)"}],
    }
