"""Ingestion: PDF -> page layout model (deterministic, no model call).  Owner: Piyush.

Public contract:
    ingest(db, doc_id) -> dict            read the PDF, write the layout JSON, update document status
    layout(doc_id) -> dict                the stored layout model (see technical-architecture.md section 5.9)
    page(doc_id, page_no) -> dict         one page: {"page", "width", "height", "method", "unreviewed", "lines": [...]}
    page_png(doc_id, page_no) -> bytes    rendered page image for screen 1

Line numbers ("page 5, lines 6 to 8") are 1-based within each page, in reading order.
Coordinates are PDF points, origin top-left (PyMuPDF), rounded to 0.01.

Stage 0 reads native text only. Still to build (Piyush, see team/PLAN.md):
    OCR for pages with no text layer (Tesseract TSV via subprocess, config.TESSERACT_CMD)
    tables (pdfplumber), headers/footers and table-of-contents detection.
Pages with no readable text are marked unreviewed, never silently skipped (rule R5).
OCR must stay optional: on a machine without Tesseract, mark the page unreviewed ("OCR not available").

Frozen parse: the parsing machine (Piyush, with Tesseract) runs `python -m scripts.freeze_layout <pdf>`,
which writes data/layout_cache/<sha256>.json (committed). ingest() uses that file when it exists, so
everyone else gets the same layout, line numbers and highlights without installing the OCR stack.
"""
import json

import pymupdf
from sqlalchemy.orm import Session

from app.core import config
from app.modules.opportunities import service as opportunities

PIPELINE_VERSION = f"pymupdf-{pymupdf.VersionBind}/native-1"
LAYOUT_CACHE = config.DATA / "layout_cache"   # committed: frozen parses of sample RFPs
LAYOUTS = config.STORE / "layouts"            # local: parses of uploaded files
PAGES = config.STORE / "pages"


def parse(path: str, doc_id: str) -> dict:
    """PDF -> layout model. Pure function of the file and the pipeline version (no DB)."""
    with pymupdf.open(path) as pdf:
        pages = [_read_page(p) for p in pdf]
    return {"document": doc_id, "pipeline_version": PIPELINE_VERSION, "page_count": len(pages), "pages": pages}


def ingest(db: Session, doc_id: str, refresh: bool = False) -> dict:
    """refresh=True ignores the committed layout cache (use it on the parsing machine when the parser changes)."""
    doc = opportunities.get_document(db, doc_id)
    opportunities.set_document_status(db, doc_id, "ingesting")
    frozen = LAYOUT_CACHE / f"{doc_id}.json"
    try:
        model = json.loads(frozen.read_text("utf-8")) if frozen.exists() and not refresh else parse(doc.path, doc_id)
    except Exception as exc:  # damaged or encrypted PDF: report, don't skip (rule R5)
        opportunities.set_document_status(db, doc_id, "failed")
        return {"document": doc_id, "error": str(exc)}
    pages = model["pages"]
    LAYOUTS.mkdir(parents=True, exist_ok=True)
    (LAYOUTS / f"{doc_id}.json").write_text(json.dumps(model, sort_keys=True, ensure_ascii=False), "utf-8")
    opportunities.set_document_status(db, doc_id, "ingested", page_count=len(pages))
    return {"document": doc_id, "page_count": len(pages),
            "unreviewed_pages": [p["page"] for p in pages if p["unreviewed"]]}


def _read_page(p: pymupdf.Page) -> dict:
    lines = []
    for block in p.get_text("dict", sort=True)["blocks"]:
        for line in block.get("lines", []):
            text = "".join(s["text"] for s in line["spans"]).strip()
            if text:
                lines.append({"n": len(lines) + 1, "text": text, "bbox": [round(v, 2) for v in line["bbox"]]})
    return {"page": p.number + 1, "width": round(p.rect.width, 2), "height": round(p.rect.height, 2),
            "method": "native" if lines else "none", "unreviewed": not lines, "lines": lines}


def layout(doc_id: str) -> dict:
    return json.loads((LAYOUTS / f"{doc_id}.json").read_text("utf-8"))


def page(doc_id: str, page_no: int) -> dict:
    return layout(doc_id)["pages"][page_no - 1]


def page_png(db: Session, doc_id: str, page_no: int) -> bytes:
    path = PAGES / doc_id / f"{page_no}.png"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with pymupdf.open(opportunities.get_document(db, doc_id).path) as pdf:
            pdf[page_no - 1].get_pixmap(dpi=110).save(path)
    return path.read_bytes()
