"""
Module M1 — Ingestion & Boundary Classification.

Turns whatever the customer actually sends into clean, page-anchored
text — or refuses it explicitly.

WHY THE BOUNDARY CLASSIFIER MATTERS
-----------------------------------
Real bid packs are not clean PDFs. They arrive as archives containing
DWG single-line diagrams, macro-laden spreadsheets, scanned drawings and
photographs of marked-up prints. If the system guesses at these, it
produces confident nonsense on the most technically dense content in the
pack. If it crashes, a live demo ends.

So unsupported artefacts are a first-class result: the file is named, the
reason is stated, and it is routed to human engineering. "Three files
ingested, one CAD drawing cannot be parsed — routed to engineering" is a
credible outcome. Silence is not.

WHY PAGE-LOCAL TEXT MATTERS
---------------------------
Provenance anchors (M11) record page-local character offsets. When input
was pasted text, pages were synthetic — produced by paginate(). A real
PDF supplies genuine page boundaries, so anchors become directly
actionable: "page 12, characters 1010-1031" maps to what a human sees in
their own PDF viewer.

The extractor name and version are recorded on every DocumentRef, because
offsets are only reproducible against a known extractor. Upgrading
pdfplumber shifts offsets; without the recorded version, old anchors
would silently drift.

SCANNED DOCUMENTS
-----------------
A PDF whose pages yield almost no text is a scanned image, not a text
document. OCR is not attempted here. The page is reported as
NO_TEXT_LAYER so the coverage map can count it as unreviewed rather than
treating an empty page as a page with nothing in it.
"""
import hashlib
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from provenance.anchors import DocumentRef


EXTRACTOR_NAME = "pdfplumber"

# Extensions we can turn into text.
SUPPORTED_TEXT = {".txt", ".md"}
SUPPORTED_PDF = {".pdf"}

# Extensions we deliberately refuse, with the reason shown to the user.
UNSUPPORTED = {
    ".dwg": "CAD drawing — single-line diagrams require engineering interpretation, not text extraction",
    ".dxf": "CAD exchange file — requires engineering interpretation",
    ".step": "3D model — requires engineering interpretation",
    ".stp": "3D model — requires engineering interpretation",
    ".xlsm": "Macro-enabled spreadsheet — macros may encode pricing logic that must be reviewed by a human",
    ".xls": "Legacy spreadsheet — structured data extraction not implemented",
    ".xlsx": "Spreadsheet — BOQ tables require structured extraction, not implemented",
    ".doc": "Legacy Word format — not supported",
    ".rtf": "Rich text — not supported",
    ".jpg": "Image — likely a scanned drawing; OCR not performed",
    ".jpeg": "Image — likely a scanned drawing; OCR not performed",
    ".png": "Image — likely a scanned drawing; OCR not performed",
    ".tif": "Image — likely a scanned drawing; OCR not performed",
    ".tiff": "Image — likely a scanned drawing; OCR not performed",
}

# Below this many characters, a PDF page is treated as having no text layer.
MIN_CHARS_PER_PAGE = 40


@dataclass
class IngestedDocument:
    doc_ref: DocumentRef
    pages: list = field(default_factory=list)
    text: str = ""
    page_count: int = 0
    pages_without_text: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def to_dict(self):
        return {
            "doc_id": self.doc_ref.doc_id,
            "version": self.doc_ref.version,
            "filename": self.doc_ref.filename,
            "extractor": self.doc_ref.extractor,
            "content_sha256": self.doc_ref.content_sha256,
            "page_count": self.page_count,
            "pages_without_text": self.pages_without_text,
            "warnings": self.warnings,
        }


@dataclass
class IngestionResult:
    documents: list = field(default_factory=list)
    unsupported: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    @property
    def combined_text(self) -> str:
        return "\n\n".join(d.text for d in self.documents)

    @property
    def primary(self):
        """The largest ingested document — in a bid pack, the main
        specification is almost always the longest text document."""
        return max(self.documents, key=lambda d: len(d.text), default=None)

    def to_dict(self):
        return {
            "documents": [d.to_dict() for d in self.documents],
            "unsupported_artifacts": self.unsupported,
            "errors": self.errors,
            "summary": self.summary,
        }

    @property
    def summary(self) -> str:
        parts = [f"{len(self.documents)} document(s) ingested"]
        if self.unsupported:
            parts.append(f"{len(self.unsupported)} unsupported artefact(s) routed to engineering")
        if self.errors:
            parts.append(f"{len(self.errors)} file(s) failed to read")
        no_text = sum(len(d.pages_without_text) for d in self.documents)
        if no_text:
            parts.append(f"{no_text} page(s) had no text layer (likely scanned) and are unreviewed")
        return "; ".join(parts) + "."


def _extractor_version() -> str:
    try:
        import pdfplumber
        return f"{EXTRACTOR_NAME}-{pdfplumber.__version__}"
    except Exception:
        return EXTRACTOR_NAME


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_artifact(path: Path) -> tuple:
    """Returns (category, reason). Category is one of:
    'pdf', 'text', 'archive', 'unsupported'."""
    ext = path.suffix.lower()
    if ext in SUPPORTED_PDF:
        return "pdf", None
    if ext in SUPPORTED_TEXT:
        return "text", None
    if ext == ".zip":
        return "archive", None
    if ext in UNSUPPORTED:
        return "unsupported", UNSUPPORTED[ext]
    return "unsupported", f"Unrecognised file type '{ext or 'no extension'}' — not processed"


def ingest_pdf(path: Path, version: str = "as-received") -> IngestedDocument:
    """Extracts page-local text from a PDF.

    Pages are kept as a list so offsets recorded by M11 are page-local
    and directly usable in a PDF viewer.
    """
    import pdfplumber

    pages, empty = [], []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            txt = page.extract_text() or ""
            if len(txt.strip()) < MIN_CHARS_PER_PAGE:
                empty.append(i)
            pages.append(txt)

    warnings = []
    if empty:
        warnings.append(
            f"{len(empty)} of {len(pages)} page(s) contained little or no text layer "
            f"(pages {empty[:10]}{'...' if len(empty) > 10 else ''}). These are likely "
            f"scanned images. OCR was not performed; they are reported as unreviewed "
            f"rather than treated as empty."
        )
    if pages and len(empty) == len(pages):
        warnings.append(
            "No text layer found anywhere in this document. It appears to be a fully "
            "scanned PDF and cannot be processed without OCR."
        )

    doc_ref = DocumentRef(
        doc_id=path.stem,
        version=version,
        filename=path.name,
        content_sha256=_sha256_file(path),
        extractor=_extractor_version(),
    )
    return IngestedDocument(
        doc_ref=doc_ref,
        pages=pages,
        text="\n\n".join(pages),
        page_count=len(pages),
        pages_without_text=empty,
        warnings=warnings,
    )


def ingest_text_file(path: Path, version: str = "as-received") -> IngestedDocument:
    from provenance.anchors import paginate
    text = path.read_text(errors="replace")
    pages = paginate(text)
    doc_ref = DocumentRef(
        doc_id=path.stem,
        version=version,
        filename=path.name,
        content_sha256=_sha256_file(path),
        extractor="inline-text",
    )
    return IngestedDocument(doc_ref=doc_ref, pages=pages, text=text,
                            page_count=len(pages))


def ingest_path(path, version: str = "as-received") -> IngestionResult:
    """Main entry point. Accepts a file or a directory; archives are
    expanded one level. Never raises on a bad file — failures are
    collected and reported."""
    path = Path(path)
    result = IngestionResult()

    if path.is_dir():
        targets = sorted(p for p in path.rglob("*") if p.is_file())
    else:
        targets = [path]

    for t in targets:
        category, reason = classify_artifact(t)

        if category == "unsupported":
            result.unsupported.append({
                "filename": t.name,
                "reason": reason,
                "disposition": "UNSUPPORTED_ARTIFACT",
                "routed_to": "engineering",
            })
            continue

        if category == "archive":
            try:
                with zipfile.ZipFile(t) as z:
                    for name in z.namelist():
                        if name.endswith("/"):
                            continue
                        inner = Path(name)
                        cat, rsn = classify_artifact(inner)
                        if cat == "unsupported":
                            result.unsupported.append({
                                "filename": f"{t.name}:{name}",
                                "reason": rsn,
                                "disposition": "UNSUPPORTED_ARTIFACT",
                                "routed_to": "engineering",
                            })
                        else:
                            result.errors.append({
                                "filename": f"{t.name}:{name}",
                                "error": "Archive contents are listed but not extracted in this build",
                            })
            except Exception as e:
                result.errors.append({"filename": t.name, "error": f"Could not read archive: {e}"})
            continue

        try:
            if category == "pdf":
                result.documents.append(ingest_pdf(t, version))
            else:
                result.documents.append(ingest_text_file(t, version))
        except Exception as e:
            # A malformed file must never end the run.
            result.errors.append({
                "filename": t.name,
                "error": f"{type(e).__name__}: {e}",
                "disposition": "FAILED_TO_READ",
                "routed_to": "engineering",
            })

    return result


def run(path, version: str = "as-received") -> dict:
    """Pipeline-shaped wrapper, matching the other module contracts."""
    res = ingest_path(path, version)
    primary = res.primary
    return {
        "ingestion": res.to_dict(),
        "primary_document": primary.to_dict() if primary else None,
        "text": res.combined_text,
        "pages": primary.pages if primary else [],
        "explanation": res.summary,
        "evidence": [{
            "source": "M1 ingestion",
            "extractor": _extractor_version(),
            "note": ("Unsupported artefacts are named and routed to engineering rather "
                     "than guessed at. Pages without a text layer are reported as "
                     "unreviewed, not treated as empty."),
        }],
    }
