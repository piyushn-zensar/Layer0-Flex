"""J-21 (C-63): the documents manifest `data/axiom_products/documents.json` ties each supplied PDF to the catalog.

Shape (PLAN 12.3): a list of {file, title, doc_type, family_keys, part_numbers, applies, pages, publisher, note}.

How a document is classified (decided by reading each file, not from its name):
- doc_type: datasheet = one product, specification tables, 1-2 pages; one_pager = a single sheet of pitch and
  ratings; catalogue = one range with technical overview, parts or ordering; brochure = marketing or portfolio text.
- family_keys: catalog item IDs (catalog_items.json) that the document is about or specifies by name. A brand or
  category word without a model (DATABAR, IBAR, "MV switchgear") or a passing mention is not linked; it goes in `note`.
- part_numbers: real part numbers named in the document. The supplied PDFs name series only (BMR316), no part
  number, so the lists are empty; they are checked against power_modules.json once it exists.
- applies: part = tied to named part numbers; family = about the listed catalog items; general = company or
  portfolio level (listed items are only where it names them).
- pages: for each key, the pages that carry that product's content (page 1 numbering); cover, contact and company
  text pages are left out.
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "data" / "axiom_products"
MANIFEST = FOLDER / "documents.json"
CATALOG = ROOT / "data" / "knowledge_base" / "catalog_items.json"
POWER_MODULES = ROOT / "data" / "knowledge_base" / "power_modules.json"
POWER_MODULES_SAMPLE = ROOT / "data" / "knowledge_base" / "power_modules.sample.json"

REQUIRED = {"file": str, "title": str, "doc_type": str, "family_keys": list, "part_numbers": list,
            "applies": str, "pages": dict, "publisher": str, "note": str}
DOC_TYPES = {"datasheet", "brochure", "catalogue", "one_pager"}
APPLIES = {"part", "family", "general"}


def _load():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _catalog_ids() -> set[str]:
    d = json.loads(CATALOG.read_text(encoding="utf-8"))
    return {i["id"] for i in (d["items"] if isinstance(d, dict) else d)}


def _known_part_numbers() -> set[str] | None:
    """Part numbers of the merged catalog; None while neither Piyush's import nor his sample is committed."""
    for path in (POWER_MODULES, POWER_MODULES_SAMPLE):
        if path.exists():
            return {i["part_number"] for i in json.loads(path.read_text(encoding="utf-8"))["items"]}
    return None


def _page_count(name: str) -> int:
    import pymupdf
    with pymupdf.open(FOLDER / name) as pdf:
        return pdf.page_count


@pytest.fixture(scope="module")
def docs():
    assert MANIFEST.exists(), f"{MANIFEST} is missing"
    data = _load()
    assert isinstance(data, list) and data, "documents.json must be a non-empty list of document entries"
    return data


def test_manifest_loads_and_every_entry_has_the_required_fields(docs):
    for n, d in enumerate(docs):
        assert isinstance(d, dict), f"entry {n} is not an object"
        label = d.get("file", f"entry {n}")
        missing = [k for k in REQUIRED if k not in d]
        assert not missing, f"{label}: missing fields {missing}"
        for k, kind in REQUIRED.items():
            assert isinstance(d[k], kind), f"{label}: {k} must be a {kind.__name__}, not {type(d[k]).__name__}"
        for k in ("file", "title", "publisher", "note"):
            assert d[k].strip(), f"{label}: {k} is empty"
        extra = set(d) - set(REQUIRED)
        assert not extra, f"{label}: unknown fields {sorted(extra)} (PLAN 12.3 fixes the shape)"
        assert d["doc_type"] in DOC_TYPES, f"{label}: doc_type {d['doc_type']!r} not in {sorted(DOC_TYPES)}"
        assert d["applies"] in APPLIES, f"{label}: applies {d['applies']!r} not in {sorted(APPLIES)}"


def test_every_referenced_file_exists_and_every_pdf_is_listed(docs):
    for d in docs:
        assert (FOLDER / d["file"]).is_file(), f"{d['file']}: not found in data/axiom_products/"
        assert d["file"].lower().endswith(".pdf"), f"{d['file']}: the manifest lists PDFs only"
    listed = {d["file"] for d in docs}
    unlisted = sorted(p.name for p in FOLDER.glob("*.pdf") if p.name not in listed)
    assert not unlisted, f"PDFs in data/axiom_products/ with no manifest entry: {unlisted}"


def test_no_duplicates(docs):
    files = [d["file"] for d in docs]
    assert len(files) == len(set(files)), f"duplicate file entries: {sorted({f for f in files if files.count(f) > 1})}"
    titles = [d["title"] for d in docs]
    assert len(titles) == len(set(titles)), f"duplicate titles: {sorted({t for t in titles if titles.count(t) > 1})}"
    for d in docs:
        for k in ("family_keys", "part_numbers"):
            assert len(d[k]) == len(set(d[k])), f"{d['file']}: duplicate values in {k}: {d[k]}"


def test_family_keys_are_real_catalog_ids(docs):
    ids = _catalog_ids()
    for d in docs:
        unknown = [k for k in d["family_keys"] if k not in ids]
        assert not unknown, f"{d['file']}: family_keys that are not catalog IDs (catalog_items.json): {unknown}"
        if d["applies"] in ("family", "part"):
            assert d["family_keys"] or d["part_numbers"], \
                f"{d['file']}: applies={d['applies']} needs at least one family key or part number (else use general)"


def test_part_numbers_are_real_and_tied_to_part_documents(docs):
    known = _known_part_numbers()
    for d in docs:
        if d["applies"] == "part":
            assert d["part_numbers"], f"{d['file']}: applies=part but part_numbers is empty"
        if known is not None:
            unknown = [p for p in d["part_numbers"] if p not in known]
            assert not unknown, f"{d['file']}: part numbers not in the merged catalog: {unknown}"
        for p in d["part_numbers"]:
            assert isinstance(p, str) and p.strip(), f"{d['file']}: empty part number"


def test_pages_are_valid_and_consistent_with_the_keys(docs):
    for d in docs:
        total = _page_count(d["file"])
        keys = set(d["family_keys"]) | set(d["part_numbers"])
        assert set(d["pages"]) == keys, \
            f"{d['file']}: pages must have one entry per family key / part number; differs by {sorted(set(d['pages']) ^ keys)}"
        for key, pages in d["pages"].items():
            assert isinstance(pages, list) and pages, f"{d['file']}: {key}: pages must be a non-empty list"
            assert all(isinstance(p, int) and not isinstance(p, bool) for p in pages), f"{d['file']}: {key}: page numbers must be integers: {pages}"
            assert pages == sorted(set(pages)), f"{d['file']}: {key}: pages must be ascending with no repeats: {pages}"
            bad = [p for p in pages if not 1 <= p <= total]
            assert not bad, f"{d['file']}: {key}: pages {bad} outside 1..{total} (the PDF has {total} pages)"


def test_general_documents_are_marked_in_the_note(docs):
    for d in docs:
        if d["applies"] == "general":
            assert len(d["note"]) >= 40, f"{d['file']}: a general document needs a note saying why it is not tied to one product"
