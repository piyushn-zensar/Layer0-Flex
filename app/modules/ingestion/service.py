"""Ingestion: PDF -> page layout model (deterministic, no model call).  Owner: Piyush.

Public contract:
    ingest(db, doc_id) -> dict            read the PDF, write the layout JSON, update document status
    layout(doc_id) -> dict                the stored layout model (see technical-architecture.md section 5.9)
    page(db, doc_id, page_no) -> dict      one page: {"page", "width", "height", "method", "unreviewed", "toc",
                                          "lines": [...], "tables": [...]}; LookupError if the document or page does not exist
    page_png(doc_id, page_no) -> bytes    rendered page image for screen 1

Line numbers ("page 5, lines 6 to 8") are 1-based within each page, in reading order.
Coordinates are PDF points, origin top-left (PyMuPDF), rounded to 0.01.

Built: native text (PyMuPDF), whole-page OCR (Tesseract TSV via subprocess, config.TESSERACT_CMD), headers /
footers and contents pages, ruled tables (pdfplumber). A table is kept beside the lines, never instead of them:
each line inside a table cell gets "cell": [table id, row, column], so line numbers, anchors and the frozen reader
answers do not change. Pages with no readable text are marked unreviewed, never silently skipped (rule R5).
OCR must stay optional: on a machine without Tesseract, mark the page unreviewed ("OCR not available").

Frozen parse: the parsing machine (Piyush, with Tesseract) runs `python -m scripts.freeze_layout <pdf>`,
which writes data/layout_cache/<sha256>.json (committed). ingest() uses that file when it exists, so
everyone else gets the same layout, line numbers and highlights without installing the OCR stack.
"""
import csv
import io
import json
import os
import re
import subprocess
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import pdfplumber
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
BAND = 0.08                # top / bottom share of the page where headers and footers live
FURNITURE_MIN_PAGES = 3    # a band line repeated on this many pages is page furniture
TOC_SHORT_LINE_WORDS = 6   # contents entries are short
TOC_SHORT_SHARE = 0.6      # share of short lines on a page with a "Contents" heading
TOC_LEADER_SHARE = 0.3     # share of dot-leader lines ("Scope ........ 4") that makes a contents page
TABLE_MAX_COLS = 20        # wider ruled grids are drawing grids or form layouts, not tables
TABLE_MIN_FILL = 0.3       # share of non-empty cells; blank forms and drawing grids fall below it
DRAWING_EDGES = 3000       # a page with more drawn lines and boxes is a drawing sheet: no table search (slow, noise)
COLUMN_TOLERANCE = 2.0     # points; a table continues on the next page when its column edges line up


@lru_cache
def tesseract_version() -> str | None:
    """None when Tesseract is not installed: OCR is optional (parsing machine only)."""
    if not Path(config.TESSERACT_CMD).exists():
        return None
    out = subprocess.run([config.TESSERACT_CMD, "--version"], capture_output=True, text=True).stdout
    return out.split()[1] if out else None


def pipeline_version() -> str:
    return (f"pymupdf-{pymupdf.VersionBind}/pdfplumber-{pdfplumber.__version__}"
            f"/tesseract-{tesseract_version() or 'none'}/layout-3")


def parse(path: str, doc_id: str) -> dict:
    """PDF -> layout model. Pure function of the file and the pipeline version (no DB)."""
    with pymupdf.open(path) as pdf:
        pages = [_read_page(p) for p in pdf]
    _add_tables(path, pages)
    _mark_furniture(pages)
    for page in pages:
        page["toc"] = _is_toc(page)
    return {"document": doc_id, "pipeline_version": pipeline_version(), "page_count": len(pages), "pages": pages}


def ingest(db: Session, doc_id: str, refresh: bool = False) -> dict:
    """refresh=True ignores the committed layout cache (use it on the parsing machine when the parser changes)."""
    doc = opportunities.get_document(db, doc_id)
    if doc is None:
        raise LookupError(f"Document {doc_id!r} not found.")
    if doc.status == "unsupported":  # e.g. a Word or CAD file: recorded, never read, never "failed"
        return {"document": doc_id, "error": "unsupported file type; recorded but not read"}
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


def _add_tables(path: str, pages: list[dict]) -> None:
    """Ruled tables (pdfplumber "lines" strategy) as rows of cells with text and boxes, in the same page points as
    the lines (both libraries measure from the top-left of the page). Merged cells are null."""
    previous = None  # the last table of the previous page, for tables that continue across a page break
    with pdfplumber.open(path) as pdf:
        for page, pl in zip(pages, pdf.pages):
            page["tables"] = []
            if len(pl.lines) + len(pl.rects) + len(pl.curves) > DRAWING_EDGES:
                previous = None
                continue
            for found in pl.find_tables({"vertical_strategy": "lines", "horizontal_strategy": "lines"}):
                texts = found.extract()
                rows = [[None if box is None else {"text": (text or "").strip(), "bbox": [round(v, 2) for v in box]}
                         for box, text in zip(row.cells, row_text)] for row, row_text in zip(found.rows, texts)]
                cells = [c for r in rows for c in r]
                width = max(len(r) for r in rows)
                filled = sum(1 for c in cells if c and c["text"]) / len(cells)
                if len(rows) < 2 or width < 2 or width > TABLE_MAX_COLS or filled < TABLE_MIN_FILL:
                    continue
                table = {"id": f"p{page['page']}-t{len(page['tables']) + 1}", "bbox": [round(v, 2) for v in found.bbox],
                         "columns": len(rows[0]), "continues_from": None, "rows": rows}
                if not page["tables"] and previous and _same_columns(previous, table):
                    table["continues_from"] = previous["id"]
                page["tables"].append(table)
            previous = page["tables"][-1] if page["tables"] else None
            _tag_lines(page)


def _column_edges(table: dict) -> list[float]:
    return sorted({c["bbox"][0] for r in table["rows"] for c in r if c} | {c["bbox"][2] for r in table["rows"] for c in r if c})


def _same_columns(a: dict, b: dict) -> bool:
    ea, eb = _column_edges(a), _column_edges(b)
    return len(ea) == len(eb) and all(abs(x - y) <= COLUMN_TOLERANCE for x, y in zip(ea, eb))


def _tag_lines(page: dict) -> None:
    """A line whose centre lies in a cell gets "cell": [table id, row, column] (0-based). Nothing else changes."""
    for line in page["lines"]:
        x0, y0, x1, y1 = line["bbox"]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        line.pop("cell", None)
        for table in page["tables"]:
            for r, row in enumerate(table["rows"]):
                for c, cell in enumerate(row):
                    if cell and cell["bbox"][0] <= cx <= cell["bbox"][2] and cell["bbox"][1] <= cy <= cell["bbox"][3]:
                        line["cell"] = [table["id"], r, c]


def _furniture_key(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\d+", "#", text.lower())).strip()


def _mark_furniture(pages: list[dict]) -> None:
    """Headers and footers: the same text (digits ignored) in the top or bottom band of several pages.
    Marked, never deleted, so line numbers and highlights stay stable (technical-architecture.md 5.4)."""
    seen = defaultdict(set)
    in_band = lambda line, page: line["bbox"][3] < BAND * page["height"] or line["bbox"][1] > (1 - BAND) * page["height"]
    for page in pages:
        for line in page["lines"]:
            if in_band(line, page):
                seen[_furniture_key(line["text"])].add(page["page"])
    for page in pages:
        for line in page["lines"]:
            line["furniture"] = in_band(line, page) and len(seen[_furniture_key(line["text"])]) >= FURNITURE_MIN_PAGES


def _is_toc(page: dict) -> bool:
    """Contents page: a 'Contents' heading with mostly short entries, or many dot-leader lines.
    Layout clean-up only; requirement identification itself never uses patterns (rule R5)."""
    body = [l for l in page["lines"] if not l.get("furniture")]
    if not body:
        return False
    heading = any(l["text"].strip().lower() in ("contents", "table of contents") for l in body[:5])
    short = sum(len(l["text"].split()) <= TOC_SHORT_LINE_WORDS for l in body) / len(body)
    leaders = sum(bool(re.search(r"(\.{4,}|…{2,})\s*\d{1,4}$", l["text"])) for l in body) / len(body)
    return (heading and short >= TOC_SHORT_SHARE) or leaders >= TOC_LEADER_SHARE


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
    # Document IDs are "<opportunity>-<hash>"; anything else (a path) is refused before touching the disk.
    if not re.fullmatch(r"[A-Za-z0-9-]{1,40}", doc_id):
        raise LookupError(f"Document {doc_id!r} not found.")
    path = LAYOUTS / f"{doc_id}.json"
    if not path.exists():
        raise LookupError(f"Document {doc_id} has not been read yet.")
    return json.loads(path.read_text("utf-8"))


def _known(db: Session, doc_id: str, page_no: int):
    doc = opportunities.get_document(db, doc_id)
    if doc is None:
        raise LookupError(f"Document {doc_id!r} not found.")
    if not 1 <= page_no <= (doc.page_count or 0):
        raise LookupError(f"Page {page_no} not found; the document has {doc.page_count} pages.")
    return doc


def page(db: Session, doc_id: str, page_no: int) -> dict:
    _known(db, doc_id, page_no)
    return layout(doc_id)["pages"][page_no - 1]


def page_png(db: Session, doc_id: str, page_no: int) -> bytes:
    doc = _known(db, doc_id, page_no)
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
    toc = {"page": 1, "height": 792, "lines": [{"text": t, "bbox": [72, 100 + 14 * i, 300, 112 + 14 * i]} for i, t in
           enumerate(["CONTENTS", "1.1", "SCOPE", "1.2", "REFERENCES", "PART 2 - PRODUCTS"])]}
    body = {"page": 2, "height": 792, "lines": [{"text": "The switchgear shall be arc resistant and tested to IEEE C37.20.7.",
                                                 "bbox": [72, 100, 500, 112]}]}
    assert _is_toc(toc) and not _is_toc(body)
    pages = [{"page": n, "height": 792, "lines": [{"text": f"Page | {n}", "bbox": [280, 740, 330, 752]},
                                                  {"text": "Body text", "bbox": [72, 400, 200, 412]}]} for n in (1, 2, 3)]
    _mark_furniture(pages)
    assert all(p["lines"][0]["furniture"] and not p["lines"][1]["furniture"] for p in pages)
    # a ruled 3 x 2 table: kept, its cells read, its lines tagged; an empty ruled grid is not a table
    import tempfile
    doc = pymupdf.open()
    pg = doc.new_page(width=400, height=300)
    for x in (50, 200, 350):
        pg.draw_line((x, 50), (x, 140))
    for y in (50, 80, 110, 140):
        pg.draw_line((50, y), (350, y))
    for (x, y), t in zip([(55, 70), (205, 70), (55, 100), (205, 100), (55, 130), (205, 130)],
                         ["Description", "Requirement", "Rated voltage", "15 kV", "Arc resistance", "Type 2B"]):
        pg.insert_text((x, y), t, fontsize=10)
    blank = doc.new_page(width=400, height=300)
    for x in (50, 200, 350):
        blank.draw_line((x, 50), (x, 140))
    for y in (50, 80, 110, 140):
        blank.draw_line((50, y), (350, y))
    tmp = Path(tempfile.mkdtemp()) / "table.pdf"
    doc.save(tmp)
    model = parse(str(tmp), "selfcheck")
    t = model["pages"][0]["tables"]
    assert len(t) == 1 and t[0]["columns"] == 2 and [c["text"] for c in t[0]["rows"][1]] == ["Rated voltage", "15 kV"], t
    tagged = {l["text"]: l.get("cell") for l in model["pages"][0]["lines"]}
    assert tagged["15 kV"] == ["p1-t1", 1, 1] and tagged["Type 2B"] == ["p1-t1", 2, 1], tagged
    assert model["pages"][1]["tables"] == []  # empty grid
    print("ingestion ok", pipeline_version())
