"""Trace: the three linked screens and the portfolio view. Read-only.  Owner: Janvia.

Screen 1 = original RFP page with highlights; screen 2 = requirement line items;
screen 3 = requirement -> business unit, product, offering type, BOM and unit response.

Public contract:
    portfolio(db) -> list[dict]
    trace(db, opp_id) -> dict         LookupError if the opportunity does not exist. "docs": the main RFP first, then
                                      the change documents that current requirements are anchored in (P-11)
"""
from sqlalchemy.orm import Session

from app.modules.catalog import service as catalog
from app.modules.ingestion import service as ingestion
from app.modules.matching import service as matching
from app.modules.opportunities import service as opportunities
from app.modules.requirements import service as requirements
from app.modules.workpackages import service as workpackages


def portfolio(db: Session) -> list[dict]:
    return [{"opp": o, "requirements": len(requirements.current(db, o.id)),
             "progress": workpackages.progress(db, o.id)} for o in opportunities.list_all(db)]


def _sizes(pages: list[dict]) -> list[dict]:
    return [{"page": p["page"], "width": p["width"], "height": p["height"], "unreviewed": p["unreviewed"]} for p in pages]


def trace(db: Session, opp_id: str) -> dict:
    opp = opportunities.require(db, opp_id)
    doc = opportunities.main_document(db, opp_id)
    pages = ingestion.layout(doc.id)["pages"] if doc and doc.status == "ingested" else []
    matches = matching.for_opportunity(db, opp_id)
    assignments = workpackages.by_requirement(db, opp_id)
    kids: dict[str, list] = {}  # a group's active sub-requirements, read once
    anchored = set()            # documents that current requirements are anchored in
    for r in requirements.current(db, opp_id, include_children=True):
        anchored.add(r.document_id)
        if r.parent_id:
            kids.setdefault(r.parent_id, []).append(r)
    rows = []
    for req in requirements.current(db, opp_id):
        m = matches.get(req.req_id)
        product = catalog.product(m.product_id) if m and m.product_id else None
        rows.append({"req": req, "match": m, "product": product,
                     "unit": catalog.unit(m.bu) if m and m.bu else None,
                     "bom": catalog.bom(product["id"]) if product else [],
                     "assignments": assignments.get(req.req_id, []), "children": kids.get(req.req_id, [])})
    # the main RFP first, then each change document that a current requirement version is anchored in (P-11)
    docs = [{"id": doc.id, "filename": doc.filename, "role": doc.role, "pages": _sizes(pages)}] if doc else []
    for d in opportunities.documents(db, opp_id):
        if d.role != "main" and d.id in anchored and d.status == "ingested":
            docs.append({"id": d.id, "filename": d.filename, "role": d.role, "pages": _sizes(ingestion.layout(d.id)["pages"])})
    return {"opp": opp, "doc": doc, "rows": rows, "pages": _sizes(pages), "docs": docs,
            "progress": workpackages.progress(db, opp_id)}
