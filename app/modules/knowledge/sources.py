"""Knowledge sources (P-35, C-29 points 1-4): register a source document, read it into passages with their exact
location, let the model annotate them, and admit the document by review. Re-exported by knowledge/service.py.

Collections keep evidence apart (COLLECTIONS). A source is evidence only once published by a reviewer of its
collection; current bid evidence is only ever returned for its own bid (passages(..., opp_id)).

Reading reuses the RFP layout model, so a passage is "p. 12, lines 4-9" exactly as in the three panes: PDF as is,
Word and Excel through office.py, web pages and text files rendered the same deterministic way. Headings come from
the PDF's outline (or each section's first line for rendered files); table passages keep their table id.
Annotations are model proposals stored beside the passage (task annotate_passages, frozen like every answer).
"""
import hashlib
import json
import re
import shutil
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path

import pymupdf
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import audit, config, llm
from app.core.auth import ROLES
from app.core.db import utcnow
from app.modules.ingestion import office
from app.modules.ingestion import service as ingestion
from app.modules.knowledge.models import KbItem, KbPassage, KbSource
from app.modules.opportunities import service as opportunities

COLLECTIONS = {
    "engineering_reference": "Engineering references",
    "product_evidence": "Product capability evidence",
    "reviewed_example": "Reviewed examples and experience",
    "bid_evidence": "Current bid evidence",
    "market_context": "Market and vendor context (never verified evidence)",
}
# Who may admit a document of each collection (qualified specialists, C-29 point 3).
REVIEWERS = {
    "engineering_reference": ["design_engineer", "product_manager"],
    "product_evidence": ["product_manager"],
    "reviewed_example": ["product_manager", "design_engineer"],
    "bid_evidence": ["bid_manager"],
    "market_context": ["bid_manager", "product_manager"],
}
STATUSES = ["draft", "published", "rejected", "retired"]
SUFFIXES = (".pdf", ".docx", ".xlsx", ".html", ".htm", ".md", ".txt")
FILES = config.STORE / "kb_files"
PASSAGE_CHARS = 900  # references are dense: about two paragraphs per passage


# --- identity --------------------------------------------------------------------------------------------------

# --- reading ---------------------------------------------------------------------------------------------------

class _Html(HTMLParser):
    """Visible text of a web page as sections of lines; h1 and h2 start a section. Scripts, menus and forms are left out."""
    SKIP = {"script", "style", "noscript", "nav", "header", "footer", "svg", "form", "button", "template", "aside"}
    BLOCK = {"p", "li", "div", "section", "article", "tr", "br", "pre", "blockquote", "dt", "dd", "figcaption",
             "caption", "h3", "h4", "h5", "h6", "table", "ul", "ol"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[list[str]] = [[]]
        self.buf: list[str] = []
        self.skip = 0

    def _flush(self):
        text = " ".join(" ".join(self.buf).split())
        if text:
            self.parts[-1].append(text)
        self.buf = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in ("h1", "h2"):
            self._flush()
            if self.parts[-1]:
                self.parts.append([])
        elif tag in ("td", "th"):
            self.buf.append("|" if self.buf else "")
        elif tag in self.BLOCK:
            self._flush()

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK or tag in ("h1", "h2"):
            self._flush()

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.buf.append(data.strip())


def _sections(path: Path) -> list[list[str]]:
    """Web pages and text files as sections of lines (a Markdown '#' / '##' heading starts a section)."""
    text = path.read_text("utf-8", "replace")
    if path.suffix.lower() in (".html", ".htm"):
        parser = _Html()
        parser.feed(text)
        parser._flush()
        parts = parser.parts
    else:
        parts = [[]]
        for line in text.splitlines():
            if re.match(r"#{1,2} ", line) and parts[-1]:
                parts.append([])
            if line.strip():
                parts[-1].append(line.lstrip("#> ").strip())
    return [p for p in parts if p]


def read(path: Path, title: str) -> tuple[dict, list[tuple[int, str, int]]]:
    """A file -> (layout model, outline [(level, heading, page)]). Same parser and line numbers as an RFP."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        with pymupdf.open(path) as pdf:
            outline = [(lvl, title_, page) for lvl, title_, page in pdf.get_toc(simple=True) if page >= 1]
        frozen = ingestion.LAYOUT_CACHE / f"{path.stem}.json"  # stored files are named by their sha256
        model = json.loads(frozen.read_text("utf-8")) if frozen.exists() else ingestion.parse(str(path), path.stem)
        return model, outline
    parts = office.sections(path) if suffix in office.SUFFIXES else _sections(path)
    data, starts = office.render(parts, title)
    rendered = FILES / f"{path.stem}.rendered.pdf"
    rendered.write_bytes(data)
    return ingestion.parse(str(rendered), path.stem), [(1, part[0], page) for part, page in zip(parts, starts)]


def _norm(text: str) -> str:
    return " ".join(re.sub(r"[^\w]+", " ", text.lower()).split())


def passages(model: dict, outline: list[tuple[int, str, int]]) -> list[dict]:
    """Passages that never cross a page, a heading or a table edge, about PASSAGE_CHARS long, each with its heading
    path. Headers, footers and contents pages are left out."""
    heads: dict[tuple[int, int], tuple[int, str]] = {}
    for level, heading, page_no in outline:
        if page_no > len(model["pages"]):
            continue
        key = _norm(heading)[:60]
        for line in model["pages"][page_no - 1]["lines"]:
            text = _norm(line["text"])
            if key and text and (text.startswith(key) or key.startswith(text)) and not line.get("furniture"):
                heads.setdefault((page_no, line["n"]), (level, heading.strip()))
                break
    out, stack = [], []
    for page in model["pages"]:
        if page.get("toc"):
            continue
        chunk, start_path, table = [], "", None

        def flush():
            if chunk:
                out.append({"page": page["page"], "line_start": chunk[0]["n"], "line_end": chunk[-1]["n"],
                            "heading": start_path, "table": table, "text": " ".join(l["text"] for l in chunk)})

        for line in page["lines"]:
            if line.get("furniture"):
                continue
            head = heads.get((page["page"], line["n"]))
            cell = (line.get("cell") or [None])[0]
            size = sum(len(l["text"]) for l in chunk) + len(line["text"])
            if chunk and (head or cell != table or size > PASSAGE_CHARS):
                flush()
                chunk = []
            if head:
                level, heading = head
                stack[level - 1:] = [heading]
            if not chunk:
                start_path, table = " > ".join(stack), cell
            chunk.append(line)
        flush()
    return out


# --- register, review, read ------------------------------------------------------------------------------------

def _next_id(db: Session) -> str:
    return f"KS-{(db.scalar(select(func.max(KbSource.id))) or 0) + 1:04d}"


def register(db: Session, path: str | Path, actor: str, collection: str, title: str = "", publisher: str = "",
             revision: str = "", scope: str = "", permissions: str = "public", url: str = "",
             opp_id: str | None = None, file_name: str | None = None) -> tuple[KbSource, bool]:
    """Register a file as a draft source and read it into passages. Returns (source, existing): the same document
    instance registered before (and not rejected) is returned as it is, never read twice (C-27).
    ValueError: unknown collection, unsupported file, or bid evidence without its bid (or other evidence with one)."""
    path = Path(path)
    if collection not in COLLECTIONS:
        raise ValueError(f"Unknown collection {collection!r}; one of {', '.join(COLLECTIONS)}.")
    if (collection == "bid_evidence") != bool(opp_id):
        raise ValueError("Current bid evidence belongs to one bid; other collections belong to none.")
    if path.suffix.lower() not in SUFFIXES:
        raise ValueError(f"Unsupported file type {path.suffix!r}; use {', '.join(SUFFIXES)}.")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    ids = opportunities.identity(path.name, path.read_bytes())  # the bids' reader of the embedded IDs (P-32, C-27)
    document_id, instance_id = ids["doc_uid"], ids["instance_uid"]
    id_source = "fingerprint" if ids["source"] == "sha256" else "embedded"
    same = db.scalar(select(KbSource).where(KbSource.document_id == document_id, KbSource.instance_id == instance_id,
                                            KbSource.status != "rejected"))
    if same:
        return same, True
    FILES.mkdir(parents=True, exist_ok=True)
    stored = FILES / f"{sha}{path.suffix.lower()}"
    if not stored.exists():
        shutil.copyfile(path, stored)
    model, outline = read(stored, title or path.stem)
    found = passages(model, outline)
    if not found:
        raise ValueError("No readable text found in the file.")
    earlier = db.scalar(select(func.max(KbSource.version)).where(KbSource.document_id == document_id)) or 0
    src = KbSource(ks_id=_next_id(db), collection=collection, title=title or path.stem, publisher=publisher,
                   revision=revision, scope=scope, permissions=permissions, url=url, file_name=file_name or path.name,
                   path=str(stored), sha256=sha, document_id=document_id, instance_id=instance_id, id_source=id_source,
                   version=earlier + 1, opportunity_id=opp_id, pages=model["page_count"],
                   pipeline_version=model["pipeline_version"], registered_by=actor)
    db.add(src)
    db.flush()
    db.add_all(KbPassage(source_id=src.id, **p) for p in found)
    audit.record(db, actor, "registered", "kb_source", src.ks_id, opp_id, collection=collection, title=src.title,
                 version=src.version, passages=len(found))
    db.commit()
    return src, False


def get(db: Session, ks_id: str) -> KbSource:
    src = db.scalar(select(KbSource).where(KbSource.ks_id == ks_id))
    if src is None:
        raise LookupError(f"Source {ks_id} not found.")
    return src


def sources(db: Session, collection: str | None = None, status: str | None = None) -> list[KbSource]:
    q = select(KbSource).order_by(KbSource.id.desc())
    if collection:
        q = q.where(KbSource.collection == collection)
    if status:
        q = q.where(KbSource.status == status)
    return list(db.scalars(q))


def counts(db: Session) -> dict[int, tuple[int, int]]:
    """source id -> (passages, annotated passages)."""
    rows = db.execute(select(KbPassage.source_id, func.count(), func.count(KbPassage.annotations))
                      .group_by(KbPassage.source_id))
    return {sid: (n, a) for sid, n, a in rows}


def source_passages(db: Session, ks_id: str) -> list[KbPassage]:
    src = get(db, ks_id)
    return list(db.scalars(select(KbPassage).where(KbPassage.source_id == src.id).order_by(KbPassage.id)))


def review(db: Session, ks_id: str, approve: bool, note: str, actor: str, role: str) -> KbSource:
    """Document-level review: a reviewer of the collection publishes or rejects a draft (a rejection needs a note).
    Publishing retires the earlier published version of the same document."""
    src = get(db, ks_id)
    if role not in REVIEWERS[src.collection]:
        allowed = " or ".join(ROLES[r].lower() for r in REVIEWERS[src.collection])
        raise PermissionError(f"Only a {allowed} reviews {COLLECTIONS[src.collection].lower()}.")
    if src.status != "draft":
        raise ValueError(f"{ks_id} is {src.status}; only a draft is reviewed.")
    if not approve and not note.strip():
        raise ValueError("A rejection needs a note.")
    src.status, src.reviewed_by, src.reviewed_at, src.review_note = ("published" if approve else "rejected"), actor, utcnow(), note
    if approve:
        for old in db.scalars(select(KbSource).where(KbSource.document_id == src.document_id, KbSource.id != src.id,
                                                     KbSource.status == "published")):
            old.status = "retired"
            audit.record(db, actor, "retired", "kb_source", old.ks_id, old.opportunity_id, replaced_by=src.ks_id)
    audit.record(db, actor, "published" if approve else "rejected", "kb_source", src.ks_id, src.opportunity_id, note=note)
    db.commit()
    return src


def evidence(db: Session, collections: list[str] | None = None, opp_id: str | None = None) -> list[dict]:
    """Published passages to retrieve from (P-37 builds on this). Current bid evidence only for `opp_id`, never
    another bid's; nothing in draft, rejected or retired. Each passage carries its citation."""
    q = (select(KbPassage, KbSource).join(KbSource, KbPassage.source_id == KbSource.id)
         .where(KbSource.status == "published"))
    if collections:
        q = q.where(KbSource.collection.in_(collections))
    q = q.where((KbSource.collection != "bid_evidence") | (KbSource.opportunity_id == (opp_id or "")))
    out = [{"passage_id": p.id, "ks_id": s.ks_id, "collection": s.collection, "title": s.title, "version": s.version,
            "file_name": s.file_name,
            "page": p.page, "line_start": p.line_start, "line_end": p.line_end, "heading": p.heading,
            "table": p.table, "text": p.text, "annotations": p.annotations}
           for p, s in db.execute(q.order_by(KbPassage.id))]
    if not collections or "reviewed_example" in collections:  # approved reviewed examples (P-36), never illustrative ones
        items = db.scalars(select(KbItem).where(KbItem.status == "approved", KbItem.illustrative.is_(False))
                           .order_by(KbItem.id))
        out += [{"passage_id": None, "ks_id": i.kb_id, "collection": "reviewed_example",
                 "title": f"{i.kind} example from {i.opportunity_id}", "version": i.version, "page": None,
                 "line_start": None, "line_end": None, "heading": i.example_type, "table": None,
                 "text": " ".join(x for x in (i.requirement, f"-> {i.response}" if i.response else "",
                                              f"Conditions: {i.conditions}" if i.conditions else "",
                                              f"Limits: {i.limits}" if i.limits else "") if x),
                 "annotations": None, "source": i.source} for i in items]
    return out


# --- annotations (model proposals beside the passage) ---------------------------------------------------------

ANNOTATE_SYSTEM = """You annotate passages of an engineering reference document for an electrical power, cooling and
data-centre bid team. For each numbered passage propose:
- topics: 1-5 short topic labels (for example "800 VDC distribution", "arc-flash protection");
- content_type: what the passage is;
- attributes: technical values stated in the passage itself (name, value, unit, the operating conditions under which
  the value holds); none when the passage states no value; never invent or convert a value;
- applicability: where the passage applies (equipment, voltage class, site type), or "" when not stated;
- ambiguities: statements a specialist should check (undefined terms, conflicting values, missing conditions).
Use only the passage text. Return one entry per passage, with its number."""
CONTENT_TYPES = ["requirement_or_rule", "rating_or_limit", "definition", "test_or_compliance", "design_guidance",
                 "architecture_description", "background", "other"]
ANNOTATE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["passages"],
    "properties": {"passages": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["n", "topics", "content_type", "attributes", "applicability", "ambiguities"],
        "properties": {
            "n": {"type": "integer"},
            "topics": {"type": "array", "items": {"type": "string"}},
            "content_type": {"type": "string", "enum": CONTENT_TYPES},
            "attributes": {"type": "array", "items": {
                "type": "object", "additionalProperties": False, "required": ["name", "value", "unit", "conditions"],
                "properties": {k: {"type": "string"} for k in ("name", "value", "unit", "conditions")}}},
            "applicability": {"type": "string"},
            "ambiguities": {"type": "array", "items": {"type": "string"}},
        }}}},
}


def annotate(db: Session, ks_id: str, actor: str) -> int:
    """Annotate every passage not yet annotated, one model call per page (answers frozen in llm_cache/annotate_passages).
    llm.LLMUnavailable when an answer is neither frozen nor obtainable; pages done before that are kept."""
    src = get(db, ks_id)
    todo = [p for p in source_passages(db, ks_id) if p.annotations is None]
    by_page: dict[int, list[KbPassage]] = {}
    for p in todo:
        by_page.setdefault(p.page, []).append(p)
    def ask(items: list[KbPassage]) -> dict | None:
        prompt = f"Document: {src.title} ({src.publisher}, {src.revision})\n\n" + "\n\n".join(
            f"[{i}] {(p.heading + ': ') if p.heading else ''}{p.text}" for i, p in enumerate(items, 1))
        try:
            return llm.complete_json("annotate_passages", ANNOTATE_SYSTEM, prompt, ANNOTATE_SCHEMA)
        except llm.LLMUnavailable:
            return None

    pages = [items for _, items in sorted(by_page.items())]
    with ThreadPoolExecutor(4) as pool:  # independent pages, as in matching; the session stays on this thread
        answers = list(pool.map(ask, pages))
    done = 0
    for items, answer in zip(pages, answers):
        for a in (answer or {"passages": []})["passages"]:
            if 1 <= a["n"] <= len(items):
                items[a["n"] - 1].annotations = {k: a[k] for k in ("topics", "content_type", "attributes",
                                                                   "applicability", "ambiguities")}
                done += 1
    missing = sum(a is None for a in answers)
    audit.record(db, actor, "annotated", "kb_source", ks_id, src.opportunity_id, passages=done)
    db.commit()
    if missing:
        raise llm.LLMUnavailable(f"{missing} page(s) have no model answer yet; {done} passages annotated and kept.")
    return done


# --- the public references in the repository --------------------------------------------------------------------

def register_references(db: Session, actor: str = "Layer 0 setup") -> list[str]:
    """Register the public references listed in data/references/sources.json (engineering references and market
    context; test RFPs are bids, not knowledge) as drafts, with their frozen annotations when they exist.
    Idempotent: a registered instance is skipped."""
    manifest = json.loads((config.DATA / "references" / "sources.json").read_text("utf-8"))
    out = []
    for e in manifest["sources"]:
        if e["collection"] not in COLLECTIONS:
            continue
        src, _ = register(db, config.ROOT / e["file"], actor, e["collection"], e["title"], e["publisher"],
                          e["revision"], e["note"], "public", e["url"])
        try:
            annotate(db, src.ks_id, actor)
        except llm.LLMUnavailable:
            pass  # not generated yet (mock mode): the passages stand without annotations
        out.append(src.ks_id)
    return out


def register_product_documents(db: Session, actor: str = "Layer 0 setup") -> list[str]:
    """Register the supplied product datasheets and brochures (data/axiom_products, listed in documents.json) as draft
    product capability evidence (P-58, C-64): read into passages with page and lines, published only by a unit
    manager's review. Which families or parts a document applies to stays in documents.json (catalog.documents()), so a
    corrected manifest re-tags them without registering again. Idempotent."""
    from app.modules.catalog import service as catalog  # here: catalog's retrieval index imports this module's caller
    out = []
    for d in catalog.documents():
        path = config.DATA / "axiom_products" / d["file"]
        if not path.exists():
            continue
        src, _ = register(db, path, actor, "product_evidence", d["title"], d["publisher"], "", d.get("note", ""),
                          "supplied for the PoC", "")
        out.append(src.ks_id)
    return out
