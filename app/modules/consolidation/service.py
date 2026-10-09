"""Consolidation: coverage check and compliance matrix for the final response.  Owner: Janvia.

A requirement is ANSWERED when every assignment for it is validated. Anything else blocks completion.

Public contract:
    coverage(db, opp_id) -> dict      {"rows": [...], "total", "answered", "blocking": [req_id]}; LookupError if unknown
    compliance_matrix_csv(db, opp_id) -> str   cells are safe to open in Excel (no formulas)
"""
import csv
import io

from sqlalchemy.orm import Session

from app.modules.matching import service as matching
from app.modules.opportunities import service as opportunities
from app.modules.requirements import service as requirements
from app.modules.workpackages import service as workpackages


def coverage(db: Session, opp_id: str) -> dict:
    opportunities.require(db, opp_id)
    assignments = workpackages.by_requirement(db, opp_id)
    matches = matching.for_opportunity(db, opp_id)
    rows = []
    for req in requirements.current(db, opp_id):
        items = assignments.get(req.req_id, [])
        state = ("not_assigned" if not items else
                 "answered" if all(a.status == "validated" for a in items) else "pending")
        rows.append({"req": req, "match": matches.get(req.req_id), "assignments": items, "state": state})
    blocking = [r["req"].req_id for r in rows if r["state"] != "answered"]
    return {"rows": rows, "total": len(rows), "answered": len(rows) - len(blocking), "blocking": blocking}


def _cell(value) -> str:
    """Text that starts like a formula (= + - @, tab, CR) would run when the file is opened in Excel; quote it."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def _offering(m, bu: str | None) -> str:
    """The offering type of the unit that holds the assignment (a match can name several units)."""
    if not m:
        return ""
    unit = next((u for u in (getattr(m, "units", None) or []) if u.get("bu") == bu), None)
    return unit["offering_type"] if unit else m.offering_type


def compliance_matrix_csv(db: Session, opp_id: str) -> str:
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Requirement ID", "Source", "Category", "Requirement", "Quote", "Business unit", "Product",
                "Offering type", "Compliance", "Response", "Validated by", "State"])
    for row in coverage(db, opp_id)["rows"]:
        req, m = row["req"], row["match"]
        for a in row["assignments"] or [None]:
            w.writerow([_cell(v) for v in (
                req.req_id, req.source, req.category, req.text, req.quote,
                a.bu if a else "", (a.product_ref if a else None) or (m.product_id if m else ""),
                _offering(m, a.bu if a else None), a.compliance if a else "", a.response if a else "",
                a.validated_by if a else "", row["state"])])
    return out.getvalue()


if __name__ == "__main__":  # self-check: python -m app.modules.consolidation.service
    assert [_cell(v) for v in ("=1+1", "+cmd", "-2", "@SUM(A1)", "ok", None, 3)] == ["'=1+1", "'+cmd", "'-2", "'@SUM(A1)", "ok", "", "3"]
    print("consolidation ok")
