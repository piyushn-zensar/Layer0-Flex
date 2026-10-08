"""Consolidation: coverage check and compliance matrix for the final response.  Owner: Janvia.

A requirement is ANSWERED when every assignment for it is validated. Anything else blocks completion.

Public contract:
    coverage(db, opp_id) -> dict      {"rows": [...], "total", "answered", "blocking": [req_id]}
    compliance_matrix_csv(db, opp_id) -> str
"""
import csv
import io

from sqlalchemy.orm import Session

from app.modules.matching import service as matching
from app.modules.requirements import service as requirements
from app.modules.workpackages import service as workpackages


def coverage(db: Session, opp_id: str) -> dict:
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


def compliance_matrix_csv(db: Session, opp_id: str) -> str:
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Requirement ID", "Source", "Category", "Requirement", "Quote", "Business unit", "Product",
                "Offering type", "Compliance", "Response", "Validated by", "State"])
    for row in coverage(db, opp_id)["rows"]:
        req, m = row["req"], row["match"]
        for a in row["assignments"] or [None]:
            w.writerow([req.req_id, req.source, req.category, req.text, req.quote,
                        a.bu if a else "", (a.product_ref if a else None) or (m.product_id if m else ""),
                        m.offering_type if m else "", a.compliance if a else "", a.response if a else "",
                        a.validated_by if a else "", row["state"]])
    return out.getvalue()
