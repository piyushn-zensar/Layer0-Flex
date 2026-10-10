"""Trace: the three linked screens and the portfolio view. Read-only.  Owner: Janvia.

Screen 1 = original RFP page with highlights; screen 2 = requirement line items;
screen 3 = requirement -> business unit, product, offering type, BOM and unit response.

Public contract:
    portfolio(db) -> list[dict]
    trace(db, opp_id) -> dict         LookupError if the opportunity does not exist. "docs": the main RFP first, then
                                      the change documents that current requirements are anchored in (P-11).
                                      Each row's "bboxes": its highlight boxes, see _highlights
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


def _highlights(req, children: list, grouped: bool) -> list:
    """A group's boxes come from its active sub-requirements on its own page: the stored boxes are a copy taken at
    grouping time, so after a sub-requirement is revised into an addendum or removed (P-11) they would still mark its
    old lines. Kept as stored: an item, a group with no sub-requirement on record (`grouped`), and a group revised
    itself (version > 1: its boxes are its own wording in the change document). Nothing is written."""
    if req.kind != "group" or req.version > 1 or not grouped:
        return req.bboxes
    return [b for k in children if k.document_id == req.document_id and k.page == req.page for b in k.bboxes]


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
    grouped = {r.parent_id for r in requirements.current(db, opp_id, include_inactive=True, include_children=True)}
    rows = []
    for req in requirements.current(db, opp_id):
        m = matches.get(req.req_id)
        product = catalog.product(m.product_id) if m and m.product_id else None
        rows.append({"req": req, "match": m, "product": product,
                     "unit": catalog.unit(m.bu) if m and m.bu else None,
                     "bom": catalog.bom(product["id"]) if product else [],
                     "assignments": assignments.get(req.req_id, []), "children": kids.get(req.req_id, []),
                     "bboxes": _highlights(req, kids.get(req.req_id, []), req.req_id in grouped)})
    # the main RFP first, then each change document that a current requirement version is anchored in (P-11)
    docs = [{"id": doc.id, "filename": doc.filename, "role": doc.role, "pages": _sizes(pages)}] if doc else []
    for d in opportunities.documents(db, opp_id):
        if d.role != "main" and d.id in anchored and d.status == "ingested":
            docs.append({"id": d.id, "filename": d.filename, "role": d.role, "pages": _sizes(ingestion.layout(d.id)["pages"])})
    return {"opp": opp, "doc": doc, "rows": rows, "pages": _sizes(pages), "docs": docs,
            "progress": workpackages.progress(db, opp_id)}
