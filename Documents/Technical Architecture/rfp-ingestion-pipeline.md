# RFP Ingestion Pipeline — Technical Architecture

Status: **Proposed (inferred design)**, now concrete on a chosen stack. Covers workflow step 1 only ([architecture-overview.md](../architecture-overview.md) component (a): "RFP intake and source references"). Output feeds step (b), requirement extraction — not covered here.

## Stack

| Tool | Job | Why not the others |
|---|---|---|
| PyMuPDF (`fitz`) | Native text, word/char bounding boxes, fonts, page size, image region locations | Fastest native extractor with per-word bboxes, needed for exact source anchors |
| pdfplumber | Ruled-line tables and cell boundaries | Better table geometry than PyMuPDF; used only where a table is suspected |
| Tesseract (`pytesseract`) | OCR for image-only pages/regions | Only path for scanned pages; already installed |

No LLM in this stage. Model-gateway principle (design principle 1): the model reads only in stage (b); this stage is deterministic library code.

## Per-page decision (one function, no plugin framework)

```python
def process_page(page) -> PageContent:
    spans = extract_native(page)                       # PyMuPDF words w/ bbox, font
    coverage = text_area(spans) / page_area(page)
    if coverage < 0.05 or not spans:                    # ponytail: fixed 5% threshold,
        spans = extract_ocr(page)                       # tune against real SpinCo PDFs
        source = "ocr"
    else:
        source = "native"
    tables = extract_tables(page) if has_ruled_lines(page) else []
    spans = drop_spans_under(spans, tables)              # don't double-report table text as prose
    unreviewed = not spans and not tables                # principle 7: never silently skip
    return PageContent(page.number, spans, tables, source, unreviewed)
```

`extract_tables` tries `vertical_strategy="lines", horizontal_strategy="lines"` first; falls back to `"text"` strategy only if no ruled lines exist, flagged lower-confidence.

## Data model

```python
@dataclass
class TextSpan:
    page: int
    bbox: tuple[float, float, float, float]
    text: str
    font: str | None
    source: Literal["native", "ocr"]
    confidence: float | None   # OCR confidence; None for native (treated as exact)

@dataclass
class TableRegion:
    page: int
    bbox: tuple[float, float, float, float]
    cells: list[list[str]]
    strategy: Literal["lines", "text"]

@dataclass
class PageContent:
    page_no: int
    spans: list[TextSpan]
    tables: list[TableRegion]
    source: Literal["native", "ocr"]
    unreviewed: bool
```

Every span/cell carries `(page, bbox, verbatim text)` — the exact source reference design principle 3 requires for every value extraction produces downstream (`EXTRACTED`/`DERIVED`/`UNANCHORED`).

## Unreviewed pages

A page where neither native extraction nor OCR produces any content (corrupted image, encrypted stream) is returned with `unreviewed=True` and surfaced to the operator list — never dropped silently (principle 7).

## Module layout

```
ingestion/
  models.py   # the three dataclasses above
  extract.py  # extract_native, extract_tables, extract_ocr, process_page, process_document
  test_extract.py  # smoke test, see below
```

No strategy/plugin registry — three fixed functions called in sequence. Add a registry only if a fourth extractor actually shows up.

## Install

```
pip install pymupdf pdfplumber pytesseract pillow
```
Tesseract binary must be on `PATH` (already installed).

## Self-check

`ingestion/test_extract.py`, assert-based:
- one native-text page → `source == "native"`, spans non-empty
- one image-only page (synthesize with PIL if no sample PDF on hand) → `source == "ocr"`, spans non-empty, `unreviewed is False`
- one blank/corrupted page → `unreviewed is True`

## Out of scope here

Requirement identification, classification, decomposition — stage (b). No model call anywhere in this stage.
