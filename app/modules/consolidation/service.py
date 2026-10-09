"""Consolidation: coverage check and compliance matrix for the final response.  Owner: Janvia.

A requirement is ANSWERED when every assignment for it is validated. Anything else blocks completion.

Public contract:
    coverage(db, opp_id) -> dict      {"rows": [...], "total", "answered", "blocking": [req_id]}; LookupError if unknown
    compliance_matrix_csv(db, opp_id) -> str   one row per assignment, columns as in COLUMNS; starts with a UTF-8 byte
                                               order mark and its cells are safe to open in Excel (no formulas)
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


# The last two columns were added on 9 Oct 2026 (traceability): they are appended so no earlier column moves.
COLUMNS = ["Requirement ID", "Source", "Category", "Requirement", "Quote", "Business unit", "Product",
           "Offering type", "Compliance", "Response", "Validated by", "State", "Assignment status", "Responded by"]
BOM = "\ufeff"  # Excel opens a UTF-8 CSV as UTF-8 only when it starts with a byte order mark (else it assumes ANSI)


def _row(req, m, a, state: str) -> list[str]:
    """One matrix row; `a` is the assignment (None for a requirement that is not assigned), `m` its match."""
    return [_cell(v) for v in (
        req.req_id, req.source, req.category, req.text, req.quote,
        a.bu if a else "", (a.product_ref if a else None) or (m.product_id if m else ""),
        _offering(m, a.bu if a else None), a.compliance if a else "", a.response if a else "",
        a.validated_by if a else "", state, a.status if a else "", a.responded_by if a else "")]


def compliance_matrix_csv(db: Session, opp_id: str) -> str:
    out = io.StringIO()
    out.write(BOM)
    w = csv.writer(out)
    w.writerow(COLUMNS)
    for row in coverage(db, opp_id)["rows"]:
        for a in row["assignments"] or [None]:
            w.writerow(_row(row["req"], row["match"], a, row["state"]))
    return out.getvalue()


if __name__ == "__main__":  # self-check: python -m app.modules.consolidation.service
    assert [_cell(v) for v in ("=1+1", "+cmd", "-2", "@SUM(A1)", "ok", None, 3)] == ["'=1+1", "'+cmd", "'-2", "'@SUM(A1)", "ok", "", "3"]
    from types import SimpleNamespace as NS
    assert COLUMNS[:12] == ["Requirement ID", "Source", "Category", "Requirement", "Quote", "Business unit", "Product",
                            "Offering type", "Compliance", "Response", "Validated by", "State"]  # earlier positions stay put
    assert COLUMNS[12:] == ["Assignment status", "Responded by"] and BOM.encode("utf-8") == b"\xef\xbb\xbf"
    req = NS(req_id="REQ-0001-0001", source="p. 55, line 16", category="technical", text="15 kV \u2013 EP\u00b2", quote="\u201cx\u201d")
    m = NS(product_id="EP2-RPP", offering_type="ETO", units=[])
    a = NS(bu="EP2", product_ref=None, compliance="met", response="=cmd", validated_by="Bid Manager", status="submitted",
           responded_by="EP\u00b2 Product Manager")
    row = _row(req, m, a, "pending")
    assert len(row) == len(COLUMNS) and row[COLUMNS.index("Assignment status")] == "submitted"
    assert row[COLUMNS.index("Responded by")] == "EP\u00b2 Product Manager" and row[COLUMNS.index("Response")] == "'=cmd"
    none = _row(req, None, None, "not_assigned")  # not assigned: the new columns are empty, the row keeps its width
    assert len(none) == len(COLUMNS) and none[-2:] == ["", ""]
    print("consolidation ok")
