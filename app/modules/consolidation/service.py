"""Consolidation: coverage check and compliance matrix for the final response.  Owner: Janvia.

A requirement is ANSWERED when every assignment for it is validated. Anything else blocks completion.

Public contract:
    coverage(db, opp_id) -> dict      {"rows": [...], "total", "answered", "blocking": [req_id]}; LookupError if unknown
    compliance_matrix_csv(db, opp_id) -> str   one row per assignment, columns as in COLUMNS; starts with a UTF-8 byte
                                               order mark and its cells are safe to open in Excel (no formulas)
    compliance_matrix_xlsx(db, opp_id) -> bytes  Excel workbook: "Compliance matrix" for the customer (validated answers,
                                               RFP order, sub-requirements listed) and "Tracking" (the CSV's columns)
    response_outline(db, opp_id) -> dict       the response-outline agent's draft per chapter (P-10), with the validated
                                               answers it rests on, what is still open, and retrieval references
    response_outline_md(db, opp_id) -> str     the same outline as Markdown, for the bid manager to edit
"""
import csv
import io

from sqlalchemy.orm import Session

from app.modules.catalog import service as catalog
from app.modules.consolidation import agent, excel
from app.modules.ingestion import service as ingestion
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


def compliance_matrix_xlsx(db: Session, opp_id: str) -> bytes:
    opp = opportunities.require(db, opp_id)
    cov = coverage(db, opp_id)
    kids: dict[str, list] = {}  # approved sub-requirements per group, read in one pass
    for k in requirements.current(db, opp_id, include_children=True):
        if k.parent_id and k.status == "approved":
            kids.setdefault(k.parent_id, []).append(k)
    tracking = [_row(r["req"], r["match"], a, r["state"]) for r in cov["rows"] for a in r["assignments"] or [None]]
    return excel.build(opp.title, opp.customer, cov["rows"], kids, _unit_name, COLUMNS, tracking)


# The response outline (P-10) follows a proposal, not the RFP's own headings (about 170 on Syracuse): one chapter
# per group of requirement categories, in this order, plus an executive summary.
CHAPTERS = [("technical", "Technical response", {"technical"}),
            ("compliance", "Compliance, legal and contract terms", {"compliance", "legal"}),
            ("commercial", "Commercial terms and schedule", {"commercial", "schedule"}),
            ("staffing", "Project team and staffing", {"staffing"}),
            ("submission", "Submission requirements", {"submission"})]
OTHER = ("other", "Other requirements")
SUMMARY_ANSWERS = 40  # the executive summary drafts from the first validated answers in RFP order (one small call)
PAST_PER_UNIT = 2


def _unit_name(code: str) -> str:
    return "Bid desk" if code == "BID" else ((catalog.unit(code) or {}).get("name") or code)


def _product_name(product_id: str | None) -> str:
    return ((catalog.product(product_id) or {}).get("name") or product_id or "") if product_id else ""


def _answers(rows: list[dict]) -> list[dict]:
    """Every validated answer of these coverage rows, in RFP order: what the agent may write from."""
    out = []
    for r in rows:
        req = r["req"]
        for a in r["assignments"]:
            if a.status == "validated" and (a.response or "").strip():
                out.append({"req_id": req.req_id, "source": req.source, "bu": a.bu, "unit": _unit_name(a.bu),
                            "compliance": excel.COMPLIANCE_WORDS.get(a.compliance, a.compliance or ""),
                            "product": _product_name(a.product_ref), "requirement": req.text, "wording": req.quote or "",
                            "response": a.response.strip()})
    return out


def _past(answers: list[dict]) -> list[str]:
    """Past responses of the units that answered (house style only), chosen without search: see agent.py."""
    units, out = {a["bu"] for a in answers}, []
    for bu in sorted(units):
        out += [f"{p['requirement']} {p['response']}" for p in catalog.past_responses() if p["bu"] == bu][:PAST_PER_UNIT]
    return out


def _draft(title: str, answers: list[dict]) -> dict:
    d = agent.draft(title, [{k: a[k] for k in ("unit", "compliance", "product", "requirement", "wording", "response")}
                            for a in answers], _past(answers))
    paragraphs = [{"text": p["text"], "sources": list(dict.fromkeys(answers[c - 1]["req_id"] for c in p["cites"]))}
                  for p in d["paragraphs"]]
    return {k: v for k, v in d.items() if k != "paragraphs"} | {"paragraphs": paragraphs}


def _references(db: Session, opp_id: str, title: str, rows: list[dict]) -> dict:
    """Both retrieval indexes, for the bid manager to read beside the draft (never in the prompt)."""
    query = " ".join([title] + [r["req"].text for r in rows[:3]])
    try:
        rfp = ingestion.search_rfp(db, opp_id, query, k=3)
    except LookupError:
        rfp = {"mode": "", "passages": []}
    past = [h for h in catalog.search(query, k=8) if h.get("kind") == "past_response"][:3]
    return {"rfp": [{"page": p["page"], "line_start": p["line_start"], "line_end": p["line_end"], "text": p["text"][:300]}
                    for p in rfp["passages"]],
            "past": [{"id": h["id"], "bu": h["bu"], "text": h["text"][:300]} for h in past],
            "mode": {"rfp": rfp["mode"], "knowledge": catalog.index_mode()}}


def response_outline(db: Session, opp_id: str) -> dict:
    opp = opportunities.require(db, opp_id)
    cov = coverage(db, opp_id)
    titles = {cid: title for cid, title, _ in CHAPTERS} | {OTHER[0]: OTHER[1]}
    by_chapter: dict[str, list] = {}
    for r in cov["rows"]:
        cid = next((cid for cid, _, cats in CHAPTERS if r["req"].category in cats), OTHER[0])
        by_chapter.setdefault(cid, []).append(r)
    chapters, everything = [], []
    for cid, title in titles.items():
        rows = by_chapter.get(cid)
        if not rows:
            continue
        answers = _answers(rows)
        everything += answers
        chapters.append({
            "id": cid, "title": title, "total": len(rows), "answered": sum(r["state"] == "answered" for r in rows),
            "draft": _draft(title, answers), "material": answers,
            "exceptions": [a for a in answers if a["compliance"] != "Comply"],
            "open": [{"req_id": r["req"].req_id, "source": r["req"].source, "text": r["req"].text, "state": r["state"]}
                     for r in rows if r["state"] != "answered"],
            "references": _references(db, opp_id, title, rows)})
    order = {r["req"].req_id: i for i, r in enumerate(cov["rows"])}
    first = sorted(everything, key=lambda a: order[a["req_id"]])[:SUMMARY_ANSWERS]
    return {"opportunity": {"id": opp.id, "title": opp.title, "customer": opp.customer},
            "total": cov["total"], "answered": cov["answered"], "validated_answers": len(everything),
            "summary": _draft("Executive summary", first), "chapters": chapters,
            "note": "A first draft for the bid manager to edit, written only from validated answers; every paragraph "
                    "cites its requirements. Writing the final response stays a human task."}


def response_outline_md(db: Session, opp_id: str) -> str:
    """The outline as Markdown, to paste into the proposal template and edit."""
    o = response_outline(db, opp_id)

    def paragraphs(d: dict) -> list[str]:
        if not d["drafted"]:
            return [f"_Not drafted: {d['note'] or 'no validated answer yet.'}_", ""]
        out = []
        for p in d["paragraphs"]:
            out += [f"{p['text']} [{', '.join(p['sources'])}]", ""]
        return out + [f"- To add or confirm: {g}" for g in d["gaps"]] + ([""] if d["gaps"] else [])

    lines = [f"# Response outline: {o['opportunity']['title']}", "",
             f"DRAFT for the bid manager to edit. {o['answered']} of {o['total']} requirements answered and validated.", "",
             "## Executive summary", ""] + paragraphs(o["summary"])
    for n, c in enumerate(o["chapters"], 1):
        lines += [f"## {n}. {c['title']}", "", f"{c['answered']} of {c['total']} requirements answered.", ""]
        lines += paragraphs(c["draft"])
        if c["material"]:
            lines += ["### Validated answers", ""] + [
                f"- {a['req_id']} ({a['source']}), {a['unit']}, {a['compliance']}: {a['response']}" for a in c["material"]] + [""]
        if c["open"]:
            lines += [f"### Still open ({len(c['open'])})", ""] + [f"- {r['req_id']} ({r['source']}): {r['text']}" for r in c["open"]] + [""]
    return "\n".join(lines)


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
