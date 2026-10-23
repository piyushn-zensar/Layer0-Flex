"""P-58 (C-64): the supplied product documents are registered as draft product capability evidence (pages and lines
kept), become evidence only when a unit manager publishes them, and give each requested component cited passages from
the documents tagged to the product families proposed for it. Evidence never changes an outcome."""
import os
import tempfile
from types import SimpleNamespace

os.environ.setdefault("STORE_DIR", tempfile.mkdtemp())

from conftest import signed_in  # noqa: E402

CDU = ["In-Rack CDU300 Datasheet (SmartSense CDU).pdf", "Modular CDU Datasheet.pdf"]   # two short datasheets: a fast test


def _item(rid: str, text: str) -> dict:
    return {"req_id": rid, "parent": None, "text": text, "quote": text, "section": "", "category": "technical",
            "document": "rfp.pdf", "page": 5}


def test_registered_published_and_cited_by_family(monkeypatch):
    signed_in()  # creates the tables
    from app.core.db import SessionLocal
    from app.modules.catalog import service as catalog
    from app.modules.configurator import service as configurator
    from app.modules.knowledge import service as knowledge
    supplied = [d for d in catalog.documents() if d["file"] in CDU]
    monkeypatch.setattr(catalog, "documents", lambda: supplied)
    group = {"name": "Cooling distribution units (CDUs)", "kind": "other", "req_ids": ["R1"],
             "requirements": [_item("R1", "CDUs shall be liquid-to-liquid with N+1 redundancy and 1.5 LPM per kW")]}
    cdu_match = {"R1": SimpleNamespace(units=[{"bu": "JETCOOL", "product_id": "JETCOOL-CDU"}])}
    with SessionLocal() as db:
        ids = knowledge.register_product_documents(db)
        assert len(ids) == 2 and knowledge.register_product_documents(db) == ids          # idempotent
        assert all(knowledge.get(db, i).collection == "product_evidence" for i in ids)
        assert configurator.evidence(db, group, cdu_match)["passages"] == []              # drafts are not evidence
        for i in ids:
            knowledge.review_source(db, i, True, "Supplied datasheet", "JetCool Product Manager", "product_manager")
        ev = configurator.evidence(db, group, cdu_match)
        assert ev["families"] == ["JETCOOL-CDU"] and sorted(ev["documents"]) == sorted(CDU)
        assert ev["passages"] and all(p["applies_to"] and p["applies_to"][0].startswith("JETCOOL-CDU/") for p in ev["passages"])
        assert all(", p. " in p["citation"] for p in ev["passages"])                       # page and lines cited
        other = {"R1": SimpleNamespace(units=[{"bu": "CROWN", "product_id": "CROWN-ARMV"}])}
        assert configurator.evidence(db, group, other)["passages"] == []                   # untagged family: nothing
