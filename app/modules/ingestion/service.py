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
import csv
import io
import json
import os
import subprocess
from functools import lru_cache
from pathlib import Path

import pymupdf
from sqlalchemy.orm import Session

from app.core import config
from app.modules.opportunities import service as opportunities

LAYOUT_CACHE = config.DATA / "layout_cache"   # committed: frozen parses of sample RFPs
LAYOUTS = config.STORE / "layouts"            # local: parses of uploaded files
PAGES = config.STORE / "pages"

# ponytail: starting thresholds (technical-architecture.md 5.3, 5.6); move to a data file when calibrated on real RFPs
OCR_DPI = 300
UNMAPPED_SHARE = 0.05      # share of U+FFFD characters that makes a native text layer unusable
LOW_CONFIDENCE = 60        # mean Tesseract word confidence below this marks the line for a person


@lru_cache
def tesseract_version() -> str | None:
    """None when Tesseract is not installed: OCR is optional (parsing machine only)."""
    if not Path(config.TESSERACT_CMD).exists():
        return None
    out = subprocess.run([config.TESSERACT_CMD, "--version"], capture_output=True, text=True).stdout
    return out.split()[1] if out else None


def pipeline_version() -> str:
    return f"pymupdf-{pymupdf.VersionBind}/tesseract-{tesseract_version() or 'none'}/ocr-1"


def parse(path: str, doc_id: str) -> dict:
    """PDF -> layout model. Pure function of the file and the pipeline version (no DB)."""
    with pymupdf.open(path) as pdf:
        pages = [_read_page(p) for p in pdf]
    return {"document": doc_id, "pipeline_version": pipeline_version(), "page_count": len(pages), "pages": pages}


def ingest(db: Session, doc_id: str, refresh: bool = False) -> dict:
    """refresh=True ignores the committed layout cache (use it on the parsing machine when the parser changes)."""
    doc = opportunities.get_document(db, doc_id)
    opportunities.set_document_status(db, doc_id, "ingesting")
    frozen = LAYOUT_CACHE / f"{doc.sha256}.json"
    try:
        model = json.loads(frozen.read_text("utf-8")) if frozen.exists() and not refresh else parse(doc.path, doc.sha256)
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
    page = {"page": p.number + 1, "width": round(p.rect.width, 2), "height": round(p.rect.height, 2)}
    lines = _native_lines(p)
    text = "".join(l["text"] for l in lines)
    if lines and text.count("�") <= UNMAPPED_SHARE * len(text):
        return page | {"method": "native", "unreviewed": False, "lines": lines}
    reason = "no text layer" if not lines else "text layer unreadable (unmapped characters)"
    if not tesseract_version():
        return page | {"method": "none", "unreviewed": True, "reason": f"{reason}; OCR not available on this machine",
                       "lines": []}
    lines = _ocr_lines(p)
    return page | {"method": "ocr", "unreviewed": not lines, "reason": reason if lines else f"{reason}; OCR found no text",
                   "lines": lines}


def _native_lines(p: pymupdf.Page) -> list[dict]:
    lines = []
    for block in p.get_text("dict", sort=True)["blocks"]:
        for line in block.get("lines", []):
            text = "".join(s["text"] for s in line["spans"]).strip()
            if text:
                lines.append({"n": len(lines) + 1, "text": text, "bbox": [round(v, 2) for v in line["bbox"]]})
    return lines


def _ocr_lines(p: pymupdf.Page) -> list[dict]:
    """Whole-page OCR: Tesseract TSV words grouped into lines, boxes converted to PDF points (rule R1)."""
    png = p.get_pixmap(dpi=OCR_DPI).tobytes("png")
    run = subprocess.run([config.TESSERACT_CMD, "stdin", "stdout", "-l", "eng", "--psm", "3", "tsv"],
                         input=png, capture_output=True, env=os.environ | {"OMP_THREAD_LIMIT": "1"})  # 1 thread: repeatable
    words: dict[tuple, list[dict]] = {}
    for w in csv.DictReader(io.StringIO(run.stdout.decode("utf-8", "replace")), delimiter="\t", quoting=csv.QUOTE_NONE):
        if w["level"] == "5" and w["text"].strip():
            words.setdefault((int(w["block_num"]), int(w["par_num"]), int(w["line_num"])), []).append(w)
    scale = 72 / OCR_DPI
    lines = []
    for key in sorted(words, key=lambda k: (min(int(w["top"]) for w in words[k]), k)):
        ws = words[key]
        x0, y0 = min(int(w["left"]) for w in ws), min(int(w["top"]) for w in ws)
        x1 = max(int(w["left"]) + int(w["width"]) for w in ws)
        y1 = max(int(w["top"]) + int(w["height"]) for w in ws)
        conf = round(sum(float(w["conf"]) for w in ws) / len(ws), 1)
        lines.append({"n": len(lines) + 1, "text": " ".join(w["text"] for w in ws), "conf": conf,
                      "low_confidence": conf < LOW_CONFIDENCE,
                      "bbox": [round(x0 * scale, 2), round(y0 * scale, 2), round(x1 * scale, 2), round(y1 * scale, 2)]})
    return lines


def layout(doc_id: str) -> dict:
    return json.loads((LAYOUTS / f"{doc_id}.json").read_text("utf-8"))


def page(doc_id: str, page_no: int) -> dict:
    return layout(doc_id)["pages"][page_no - 1]


def page_png(db: Session, doc_id: str, page_no: int) -> bytes:
    doc = opportunities.get_document(db, doc_id)
    path = PAGES / doc.sha256 / f"{page_no}.png"  # same file, same images
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with pymupdf.open(doc.path) as pdf:
            pdf[page_no - 1].get_pixmap(dpi=110).save(path)
    return path.read_bytes()


if __name__ == "__main__":  # self-check: python -m app.modules.ingestion.service
    src = pymupdf.open()
    src.new_page().insert_text((72, 100), "The switchgear shall be arc resistant.", fontsize=14)
    scanned = pymupdf.open()  # the same page as an image only: no text layer
    scanned.new_page().insert_image(scanned[0].rect, pixmap=src[0].get_pixmap(dpi=200))
    native, ocr = _read_page(src[0]), _read_page(scanned[0])
    assert native["method"] == "native" and native["lines"][0]["text"] == "The switchgear shall be arc resistant."
    if tesseract_version():
        assert ocr["method"] == "ocr" and "switchgear shall be arc resistant" in ocr["lines"][0]["text"], ocr
        x0, y0, x1, y1 = ocr["lines"][0]["bbox"]
        assert abs(x0 - 72) < 4 and abs(y1 - 100) < 6, ocr["lines"][0]["bbox"]  # boxes land in page points
    else:
        assert ocr["method"] == "none" and ocr["unreviewed"] and "OCR not available" in ocr["reason"]
    print("ingestion ok", pipeline_version())
