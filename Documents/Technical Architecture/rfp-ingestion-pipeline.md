# RFP Ingestion Pipeline: Technical Detail

Status: stage 0 **built** (native text); stage 1 **Proposed (inferred design)**. This covers workflow step 1, reading the RFP, in the `ingestion` module (`app/modules/ingestion/service.py`). Its output feeds the reader agent in the `requirements` module ([technical-architecture.md](../technical-architecture.md) section 6).

## Stack

| Tool | Job | Why |
|---|---|---|
| PyMuPDF (`pymupdf`) | Native text as lines with boxes, page sizes, page images for screen 1 | Fast, exact positions, needed for "page N, lines A to B" and highlights |
| pdfplumber | Ruled tables and cell boundaries | Better table geometry; used only where a table is found |
| Tesseract 5.5 (local executable) | OCR for pages or regions with no usable text layer | Called through `subprocess` with TSV output (word boxes and confidence); no extra Python package |

No model is called in this stage. It is deterministic library code; the model reads the result in the next stage.

## Per-page decision

```python
def read_page(page) -> dict:
    lines = native_lines(page)                 # built: PyMuPDF lines in reading order, numbered per page
    if not lines or unusable(lines):           # stage 1: no text layer, or unmapped characters above 5%
        lines = ocr_lines(page)                # Tesseract TSV -> lines with page-point boxes and confidence
    tables = ruled_tables(page)                # stage 1: pdfplumber "lines" strategy
    lines = drop_lines_inside(lines, tables)   # table text is not read twice
    return {"page": ..., "method": ..., "unreviewed": not lines and not tables, "lines": lines, "tables": tables}
```

A page where neither native reading nor OCR produces content is returned with `unreviewed: true` and shown with a warning. It is never dropped silently. On the Syracuse RFP, page 83 has no text layer and is the first OCR test case.

## Output

One JSON layout model per document, written to the local store and never edited:

```text
document, pipeline_version, page_count
pages[]: page, width, height, method, unreviewed
  lines[]: n (1-based within the page), text, bbox [x0, y0, x1, y1] in PDF points, top-left origin
```

Coordinates are rounded to 0.01 point and keys are sorted, so the same file and pipeline version give a byte-identical model.

## Self-check

- The smoke test ingests the 101-page Syracuse RFP and reports its unreviewed pages.
- Stage 1 adds: a native page gives `method == "native"`; an image-only page gives `method == "ocr"` with lines; a blank page gives `unreviewed == true`; two runs give identical JSON.

## Out of scope here

Requirement identification and matching. These happen in the `requirements` and `matching` modules, through the model gateway.
