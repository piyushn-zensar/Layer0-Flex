"""Requirements: the requirement register (verified sources only), the exception queue, frozen baselines.  Owner: Piyush.

Register rule (C-02, technical-architecture section 16.3): a requirement is in the register (status "approved") only
with a verified source (provenance EXTRACTED: document, page, lines, verbatim text). Text whose quote cannot be found
gets status "exception": outside the register, listed by exceptions(), resolved by linking it to its lines or
dismissed with a reason. There is no per-requirement approve step: add() admits or queues by the anchoring result.

Snapshot and origins (C-04): every reading is stored as an extraction snapshot (E1, E2, ...; append-only). Every row
names its origin: extraction (the reader), correction (a person fixed the reading) or customer_change (a change
document). Before publishing, corrections change the working rows; after publishing, each correction is a new
version in the next baseline, like a customer change but without a change document (apply_correction).

Public contract:
    extract(db, opp_id, actor, reason="") -> dict   reader agent on the main RFP, then duplicates marked and related
                                                 items grouped into requirements with sub-requirements; anchored
                                                 items enter the register, the others the exception queue; writes
                                                 snapshot E1, or E2... when read again, which needs a reason
    snapshots(db, opp_id) -> list[ExtractionSnapshot]   newest first
    snapshot(db, opp_id, number) -> ExtractionSnapshot  LookupError
    add(db, opp_id, document_id, quote, text, category, actor, section="", hint_page=None, origin="extraction")
                                                 -> Requirement; status "approved" when the quote is found, else
                                                 "exception"
    current(db, opp_id, include_inactive=False, include_children=False) -> list[Requirement]
                                                 the register, in document order: groups and stand-alone items, not
                                                 their sub-requirements (inactive = rejected, duplicate, exception,
                                                 dismissed, or replaced by a split / merge)
    exceptions(db, opp_id) -> list[dict]         the exception queue: rows (as stored, plus "source") with
                                                 suggested_page (the page the reader named), location_hint
                                                 and reason
    resolve(db, req_id, page, line_start, line_end, actor, text="", category=None) -> Requirement
                                                 link an exception to its lines (add_from_lines rules): it enters the
                                                 register with those lines as its quote
    dismiss(db, req_id, reason, actor) -> Requirement   an exception that is not a requirement; reason required;
                                                 also after publishing (an exception is outside the register)
    children(db, req_id) -> list[Requirement]    the sub-requirements of a group
    ungroup(db, req_id, actor, reason="") -> list[Requirement]   a group's sub-requirements become requirements again
    get(db, req_id, baseline=None) -> Requirement | None   latest version; with baseline: the version in that baseline
    review(db, req_id, action, actor, text=None, reason="", category=None)   action: approve | reject | edit;
                                                 reject = "exclude: not a requirement", reason required; approve
                                                 only restores an excluded or duplicate item with a verified source
                                                 (an excluded group with its excluded sub-requirements); a group's
                                                 exclusion covers its sub-requirements; a review that changes
                                                 nothing (the same action twice) records no event
    split(db, req_id, parts, actor, reason="") -> list[Requirement]   parts: [{"quote", "text"}], >= 2
    merge(db, opp_id, req_ids, text, actor, reason="") -> Requirement  >= 2 line items into one
    add_missed(db, opp_id, quote, text, category, actor, page=None) -> Requirement   a person adds what the agent missed
    add_from_lines(db, opp_id, page, line_start, line_end, text, category, actor) -> Requirement
                                                 the same, by selecting lines of the main RFP: the quote is those
                                                 lines verbatim (headers / footers left out), so the source is exact
    freeze(db, opp_id, actor) -> Baseline        publish: the register becomes baseline 1; needs a read main RFP
                                                 and at least one requirement in it; open exceptions do not block
                                                 it; once only (later: apply_correction, apply_change)
    apply_correction(db, opp_id, kind, body, actor, reason, commit=True) -> dict
                                                 after publishing: a person corrects the reading, reason required.
                                                 kind: add {page, line_start, line_end, text?, category} | edit
                                                 {req_id, text?, category?} | split {req_id, parts} | merge {req_ids,
                                                 text} | exclude {req_id} | resolve {req_id, page, line_start,
                                                 line_end, text?, category?}. New versions (origin correction) in
                                                 the next baseline. Returns as apply_change. Atomic
    apply_change(db, opp_id, change_doc_id, items, actor, reason, commit=True) -> dict
                                                 a customer change (changes module): items = confirmed
                                                 [{"kind": added | modified | removed, "target", "quote", "text",
                                                 "category", "page"}]; modified -> a new version anchored in the
                                                 change document, removed -> a new version "removed" (a group's
                                                 sub-requirements too), added -> a new ID (an exception when its quote
                                                 is not found in the change document); all in the next baseline.
                                                 Returns {"baseline", "added", "modified", "removed", "affected"}
                                                 (affected: requirements whose answers must be revisited). Atomic.
                                                 LookupError unknown opportunity; ValueError no baseline, bad target
Every other write (except dismiss) refuses once the register is published, and LookupError for an unknown
opportunity or item.
Requirement IDs are never reused: the next number is taken over every ID ever issued, including discarded drafts.
    baseline(db, opp_id) -> Baseline | None      latest frozen baseline
    history(db, req_id) -> dict                  every version (who, when, text, category, origin) and every event;
                                                 LookupError
    locate(quote, pages, hint_page=None) -> dict | None   a quote's page, lines and boxes in layout pages (rule R1)
    CATEGORIES                                   the requirement categories
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import hashlib

from app.core import audit, config
from app.core.audit import AuditEvent
from app.modules.ingestion import service as ingestion
from app.modules.opportunities import service as opportunities
from app.modules.requirements import agent, anchoring, grouping
from app.modules.requirements.models import CATEGORIES, Baseline, ExtractionSnapshot, Requirement

# removed: deleted by a change document; exception: source not verified (the queue); dismissed: an exception that is
# not a requirement
INACTIVE = {"rejected", "split", "merged", "duplicate", "removed", "exception", "dismissed"}
AGENTS = ("reader agent", "grouping agent")
# the reader's and the grouping agent's instructions: a snapshot names the pipeline that produced it
PIPELINE_VERSION = hashlib.sha256((agent.SYSTEM + grouping.SYSTEM).encode()).hexdigest()[:12]


def _next_req_id(db: Session, opp_id: str) -> str:
    """Highest number ever issued for this opportunity + 1. Discarded drafts live on in the append-only audit log,
    so their IDs are never handed out again (a unit's answer can never land on a different requirement)."""
    prefix = f"REQ-{opp_id.split('-')[1]}-"
    issued = set(db.scalars(select(Requirement.req_id).where(Requirement.opportunity_id == opp_id)))
    issued |= set(db.scalars(select(AuditEvent.entity_id).where(AuditEvent.opportunity_id == opp_id,
                                                                AuditEvent.entity == "requirement")))
    last = max((int(i.rsplit("-", 1)[1]) for i in issued if i.startswith(prefix)), default=0)
    return f"{prefix}{last + 1:04d}"


def _writable(db: Session, opp_id: str) -> None:
    """Every write before publishing calls this: after it, requirements change only by corrections (with a reason)
    and change documents, each a new version in the next baseline."""
    opportunities.require(db, opp_id)
    b = baseline(db, opp_id)
    if b:
        raise ValueError(f"The register is published (baseline {b.number}); correct it with a reason, or through a "
                         "change document.")


def add(db: Session, opp_id: str, document_id: str, quote: str, text: str, category: str, actor: str,
        section: str = "", hint_page: int | None = None, derived_from: list[str] | None = None,
        commit: bool = True, pages: list[dict] | None = None, origin: str = "extraction",
        lines: list[dict] | None = None) -> Requirement:
    if not quote.strip():
        raise ValueError("A requirement needs a quote copied from the RFP.")
    pages = pages if pages is not None else ingestion.layout(document_id)["pages"]
    hit = _anchor(anchoring.find(quote, pages, hint_page, lines), document_id)
    req = Requirement(req_id=_next_req_id(db, opp_id), opportunity_id=opp_id, document_id=document_id,
                      text=text, quote=quote, category=category, section=section, created_by=actor,
                      derived_from=derived_from or [], provenance="EXTRACTED" if hit else "UNANCHORED",
                      status="approved" if hit else "exception", origin=origin,
                      location_hint=None if hit else anchoring.hint(quote, pages, hint_page, lines), **(hit or {}))
    db.add(req)
    db.flush()  # the next _next_req_id sees this one
    audit.record(db, actor, "proposed", "requirement", req.req_id, opp_id, provenance=req.provenance, status=req.status,
                 hint_page=hint_page, derived_from=req.derived_from, text=req.text, category=req.category, quote=req.quote,
                 origin=origin)
    if commit:
        db.commit()
    return req


def _anchor(hit: dict | None, document_id: str) -> dict | None:
    """An anchoring hit as Requirement fields: the first span in page, line_start, line_end, bboxes; every span (with
    its document) in spans."""
    return hit and hit | {"spans": [s | {"document_id": document_id} for s in hit["spans"]]}


def _draft(db: Session, req_id: str) -> Requirement:
    req = get(db, req_id)
    if req is None:
        raise LookupError(f"{req_id} not found.")
    _writable(db, req.opportunity_id)
    if req.status in INACTIVE:
        raise ValueError(f"{req_id} is {req.status}; it can no longer be changed.")
    return req


def split(db: Session, req_id: str, parts: list[dict], actor: str, reason: str = "") -> list[Requirement]:
    """One line item that holds several obligations becomes one item per part. Each part is anchored again."""
    req = _draft(db, req_id)
    if req.kind == "group":
        raise ValueError(f"{req_id} is a group; use Ungroup to release its sub-requirements.")
    parts = [p for p in parts if p.get("quote", "").strip()]
    if len(parts) < 2:
        raise ValueError("A split needs at least two parts.")
    children = [add(db, req.opportunity_id, req.document_id, p["quote"], p.get("text") or p["quote"][:200],
                    req.category, actor, req.section, req.page, [req.req_id], commit=False, origin="correction")
                for p in parts]
    req.status = "split"
    audit.record(db, actor, "split", "requirement", req_id, req.opportunity_id,
                 into=[c.req_id for c in children], reason=reason)
    db.commit()
    return children


def merge(db: Session, opp_id: str, req_ids: list[str], text: str, actor: str, reason: str = "") -> Requirement:
    """Several line items that are really one obligation become one. Sources are kept (all boxes, joined quote)."""
    if not text.strip():
        raise ValueError("Give the merged requirement a short text.")
    reqs = [_draft(db, r) for r in dict.fromkeys(req_ids)]
    if len(reqs) < 2:
        raise ValueError("A merge needs at least two line items.")
    if any(r.opportunity_id != opp_id for r in reqs):
        raise ValueError("Line items from another bid cannot be merged.")
    if any(r.kind == "group" or r.parent_id for r in reqs):
        raise ValueError("Groups and sub-requirements cannot be merged; ungroup first.")
    if len({r.page for r in reqs}) > 1:
        # ponytail: one requirement = one page, so its highlight is complete; multi-page anchors if ever needed
        raise ValueError("Only line items on the same page can be merged; keep cross-page items separate.")
    reqs.sort(key=lambda r: r.line_start or 0)
    first = reqs[0]
    merged = Requirement(
        req_id=_next_req_id(db, opp_id), opportunity_id=opp_id, document_id=first.document_id, text=text.strip(),
        quote=" … ".join(r.quote for r in reqs), category=first.category, section=first.section, created_by=actor,
        derived_from=[r.req_id for r in reqs], page=first.page,
        line_start=first.line_start, line_end=max(r.line_end or 0 for r in reqs),
        bboxes=[b for r in reqs for b in r.bboxes], spans=[s for r in reqs for s in r.spans], origin="correction",
        provenance="EXTRACTED" if all(r.provenance == "EXTRACTED" for r in reqs) else "UNANCHORED")
    merged.status = "approved" if merged.provenance == "EXTRACTED" else "exception"
    db.add(merged)
    for r in reqs:
        r.status = "merged"
    db.flush()
    audit.record(db, actor, "merged", "requirement", merged.req_id, opp_id,
                 merged_from=[r.req_id for r in reqs], reason=reason)
    for r in reqs:  # the originals' own history shows where they went
        audit.record(db, actor, "merged_into", "requirement", r.req_id, opp_id, into=merged.req_id, reason=reason)
    db.commit()
    return merged


def add_missed(db: Session, opp_id: str, quote: str, text: str, category: str, actor: str,
               page: int | None = None) -> Requirement:
    _writable(db, opp_id)
    if category not in CATEGORIES:
        raise ValueError(f"Unknown category {category!r}.")
    doc = _read_main_document(db, opp_id)
    return add(db, opp_id, doc.id, quote, (text.strip() or quote.strip())[:200], category, actor, hint_page=page,
               origin="correction")


MAX_SELECTED_LINES = 40  # a requirement is a sentence or a paragraph, not a page


def add_from_lines(db: Session, opp_id: str, page: int, line_start: int, line_end: int, text: str, category: str,
                   actor: str) -> Requirement:
    """P-15: the person selects the lines on the RFP page instead of retyping the quote."""
    try:
        _writable(db, opp_id)
    except ValueError as exc:
        raise ValueError(f"{exc} A requirement missed before the freeze now comes in through the Changes page.") from exc
    if category not in CATEGORIES:
        raise ValueError(f"Unknown category {category!r}.")
    doc, chosen = _selected_lines(db, opp_id, page, line_start, line_end)
    quote = " ".join(line["text"] for line in chosen)
    # anchored in the selected lines only, so the source is the selection itself (never the same words elsewhere)
    return add(db, opp_id, doc.id, quote, (text.strip() or quote.strip())[:200], category, actor, hint_page=page,
               pages=[{"page": page, "lines": chosen}], origin="correction")


def _selected_lines(db: Session, opp_id: str, page: int, line_start: int, line_end: int):
    """The main RFP and the lines a person selected on one page (headers and footers left out), or ValueError."""
    doc = _read_main_document(db, opp_id)
    pages = ingestion.layout(doc.id)["pages"]
    if not 1 <= page <= len(pages):
        raise ValueError(f"Page {page} not found; the RFP has {len(pages)} pages.")
    lines = pages[page - 1]["lines"]
    if not lines:
        raise ValueError(f"Page {page} has no readable lines (not read; it needs OCR).")
    last = max(line["n"] for line in lines)
    if not 1 <= line_start <= line_end <= last:
        raise ValueError(f"Choose lines between 1 and {last} on page {page}, the first line before the last.")
    if line_end - line_start + 1 > MAX_SELECTED_LINES:
        raise ValueError(f"Select at most {MAX_SELECTED_LINES} lines; split a longer passage into several requirements.")
    # headers and footers are left out, as the reader leaves them out; the line numbers stay those of the page
    chosen = [line for line in lines if line_start <= line["n"] <= line_end
              and not line.get("furniture") and anchoring.normalise(line["text"])]
    if not chosen:
        raise ValueError("Only header or footer lines are selected; select the requirement's own lines.")
    return doc, chosen


def _read_main_document(db: Session, opp_id: str):
    doc = opportunities.main_document(db, opp_id)
    if doc is None or doc.status != "ingested":
        raise ValueError("Upload the main RFP and wait until it has been read.")
    return doc


def extract(db: Session, opp_id: str, actor: str, reason: str = "") -> dict:
    _writable(db, opp_id)
    doc = _read_main_document(db, opp_id)
    earlier = snapshots(db, opp_id)
    if earlier and not reason.strip():
        e = earlier[0]
        raise ValueError(f"The RFP was read before (E{e.number}, {e.created_by}); give a reason to read it again. "
                         f"E{e.number} stays readable.")
    reviewed = db.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.opportunity_id == opp_id, AuditEvent.entity == "requirement",
        AuditEvent.action.in_(["approve", "reject", "edit", "split", "merged", "resolved", "dismissed"])))
    if reviewed:
        raise ValueError(f"Corrections were made ({reviewed}); reading again would lose them. "
                         "Add what is missing with 'Add a requirement' instead.")
    layout = ingestion.layout(doc.id)
    proposed, problems, read = agent.read(layout)
    for old in db.scalars(select(Requirement).where(Requirement.opportunity_id == opp_id,
                                                    Requirement.status.in_(["proposed", "approved", "exception",
                                                                            "duplicate"]))):
        if old.created_by.startswith(AGENTS):  # a re-run replaces the agents' unreviewed proposals; people's stay
            audit.record(db, actor, "discarded", "requirement", old.req_id, opp_id, reason="re-read replaced the draft")
            db.delete(old)
    db.commit()
    items = [add(db, opp_id, doc.id, item["quote"], item["text"], item["category"], f"reader agent ({actor})",
                 item["section"], item["page"], commit=False, pages=layout["pages"], lines=item.get("lines"))
             for item in proposed]
    dups = grouping.duplicates([{"quote": r.quote} for r in items])
    # of each repeated text, the first copy with a verified source is kept (the first copy when none has one)
    kept = {}
    for i, first in sorted(dups.items()):
        kept.setdefault(first, first)
        if items[kept[first]].status != "approved" and items[i].status == "approved":
            kept[first] = i
    for i in sorted({*dups, *kept} - set(kept.values())):
        keep = items[kept[dups.get(i, i)]]
        items[i].status, items[i].derived_from = "duplicate", [keep.req_id]
        audit.record(db, actor, "duplicate_of", "requirement", items[i].req_id, opp_id, of=keep.req_id)
    # the grouping agent sees the same items as before the register rule, so its frozen answers still apply;
    # exceptions and duplicates are then left out of the groups
    unique = [r for i, r in enumerate(items) if i not in dups]
    groups, group_problems = grouping.group([{"page": r.page, "text": r.text, "category": r.category} for r in unique])
    made = []
    for g in groups:
        members = [unique[i] for i in g["members"] if unique[i].status == "approved"]
        if len(members) >= 2:
            made.append(_create_group(db, opp_id, members, g["title"], g["category"], f"grouping agent ({actor})"))
    # candidates = admitted + exceptions + duplicates; pages = read + failed + skipped + unreadable (C-03)
    coverage = read | {"candidates": len(proposed), "admitted": sum(r.status == "approved" for r in items),
                       "exceptions": sum(r.status == "exception" for r in items),
                       "duplicates": sum(r.status == "duplicate" for r in items), "groups": len(made),
                       "problems": len(problems + group_problems)}
    snap = ExtractionSnapshot(opportunity_id=opp_id, document_id=doc.id, number=len(earlier) + 1, reason=reason.strip(),
                              created_by=actor, model=config.LLM_MODEL, pipeline_version=PIPELINE_VERSION,
                              coverage=coverage, items=[_snapshot_item(r) for r in items + made])
    db.add(snap)
    db.flush()
    audit.record(db, actor, "read", "extraction_snapshot", str(snap.number), opp_id, document=doc.id,
                 reason=snap.reason, coverage=coverage)
    db.commit()
    opportunities.set_status(db, opp_id, "review", actor)
    return {"proposed": len(proposed), "duplicates": len(dups), "groups": len(made),
            "requirements": len(current(db, opp_id)), "exceptions": coverage["exceptions"], "snapshot": snap.number,
            "coverage": coverage, "problems": problems + group_problems}


def _snapshot_item(r: Requirement) -> dict:
    return {"req_id": r.req_id, "kind": r.kind, "text": r.text, "quote": r.quote, "category": r.category,
            "section": r.section, "page": r.page, "line_start": r.line_start, "line_end": r.line_end,
            "spans": r.spans, "status": r.status, "group": r.parent_id,
            "duplicate_of": r.derived_from[0] if r.status == "duplicate" and r.derived_from else None}


def snapshots(db: Session, opp_id: str) -> list[ExtractionSnapshot]:
    return list(db.scalars(select(ExtractionSnapshot).where(ExtractionSnapshot.opportunity_id == opp_id)
                           .order_by(ExtractionSnapshot.number.desc())))


def snapshot(db: Session, opp_id: str, number: int) -> ExtractionSnapshot:
    s = db.scalar(select(ExtractionSnapshot).where(ExtractionSnapshot.opportunity_id == opp_id,
                                                   ExtractionSnapshot.number == number))
    if s is None:
        raise LookupError(f"Extraction snapshot E{number} not found.")
    return s


def _create_group(db: Session, opp_id: str, members: list[Requirement], title: str, category: str,
                  actor: str) -> Requirement:
    """One requirement made of sub-requirements on the same page. It keeps all their highlights and quotes."""
    members = sorted(members, key=lambda r: r.line_start or 0)
    anchored = [r for r in members if r.page]
    first = anchored[0] if anchored else members[0]
    g = Requirement(req_id=_next_req_id(db, opp_id), opportunity_id=opp_id, document_id=first.document_id,
                    kind="group", text=title, category=category, section=first.section, created_by=actor,
                    quote=" … ".join(r.quote for r in members), page=first.page,
                    line_start=min((r.line_start for r in anchored), default=None),
                    line_end=max((r.line_end for r in anchored), default=None),
                    bboxes=[b for r in anchored for b in r.bboxes], spans=[s for r in anchored for s in r.spans],
                    origin="extraction",
                    provenance="EXTRACTED" if len(anchored) == len(members) else "UNANCHORED")
    g.status = "approved" if g.provenance == "EXTRACTED" else "exception"
    db.add(g)
    db.flush()
    for r in members:
        r.parent_id = g.req_id
    audit.record(db, actor, "grouped", "requirement", g.req_id, opp_id, text=title, category=category,
                 members=[r.req_id for r in members])
    return g


def children(db: Session, req_id: str) -> list[Requirement]:
    req = get(db, req_id)
    if req is None:
        return []
    rows = [r for r in current(db, req.opportunity_id, include_inactive=True, include_children=True) if r.parent_id == req_id]
    return rows


def ungroup(db: Session, req_id: str, actor: str, reason: str = "") -> list[Requirement]:
    req = _draft(db, req_id)
    if req.kind != "group":
        raise ValueError(f"{req_id} is not a group.")
    kids = children(db, req_id)
    for r in kids:
        r.parent_id = None
    req.status = "split"
    audit.record(db, actor, "ungrouped", "requirement", req_id, req.opportunity_id,
                 into=[r.req_id for r in kids], reason=reason)
    db.commit()
    return kids


def exceptions(db: Session, opp_id: str) -> list[dict]:
    """The exception queue, in the order the reader proposed them: each row with the page the reader suggested and
    why its source could not be verified."""
    rows = [r for r in current(db, opp_id, include_inactive=True, include_children=True) if r.status == "exception"]
    proposed = {e.entity_id: e.data for e in db.scalars(select(AuditEvent).where(
        AuditEvent.opportunity_id == opp_id, AuditEvent.entity == "requirement", AuditEvent.action == "proposed",
        AuditEvent.entity_id.in_([r.req_id for r in rows])))}
    out = []
    for r in sorted(rows, key=lambda r: r.req_id):
        page = proposed.get(r.req_id, {}).get("hint_page")
        where = f"on page {page} or anywhere else in the document" if page else "anywhere in the document"
        reason = f"The quoted text was not found {where}, so its source cannot be verified."
        if h := r.location_hint:
            lines = f", lines {h['line_start']}-{h['line_end']}" if h["line_start"] else ""
            reason = (f"The quoted wording was not found word for word, so its source cannot be verified; "
                      f"{round(h['share'] * 100)}% of its words are on page {h['page']}{lines}, where the reader says it is.")
        out.append({c.key: getattr(r, c.key) for c in Requirement.__table__.columns} | {
            "source": r.source, "suggested_page": page, "reason": reason})
    return out


def _exception(db: Session, req_id: str, published_ok: bool = False) -> Requirement:
    req = get(db, req_id)
    if req is None:
        raise LookupError(f"{req_id} not found.")
    if not published_ok:
        _writable(db, req.opportunity_id)
    if req.status != "exception":
        raise ValueError(f"{req_id} is not in the exception queue.")
    return req


def resolve(db: Session, req_id: str, page: int, line_start: int, line_end: int, actor: str, text: str = "",
            category: str | None = None) -> Requirement:
    """An exception linked to its lines on the main RFP page: those lines become its quote and it enters the register."""
    req = _exception(db, req_id)
    if category and category not in CATEGORIES:
        raise ValueError(f"Unknown category {category!r}.")
    doc, chosen = _selected_lines(db, req.opportunity_id, page, line_start, line_end)
    quote = " ".join(line["text"] for line in chosen)
    hit = _anchor(anchoring.find(quote, [{"page": page, "lines": chosen}], page), doc.id)
    if not hit:
        raise ValueError("The selected lines have no text to link; select the requirement's own lines.")
    before = {"quote": req.quote, "document_id": req.document_id}
    req.document_id, req.quote, req.provenance, req.status, req.origin = doc.id, quote, "EXTRACTED", "approved", "correction"
    req.page, req.line_start, req.line_end, req.bboxes, req.spans = (hit["page"], hit["line_start"], hit["line_end"],
                                                                     hit["bboxes"], hit["spans"])
    req.location_hint = None  # a verified source now
    req.text, req.category = (text.strip() or req.text), (category or req.category)
    audit.record(db, actor, "resolved", "requirement", req_id, req.opportunity_id, before=before,
                 after={"quote": req.quote, "source": req.source, "text": req.text, "category": req.category})
    db.commit()
    return req


def dismiss(db: Session, req_id: str, reason: str, actor: str) -> Requirement:
    """An exception that is not a requirement leaves the queue; it stays readable with its reason."""
    if not reason.strip():
        raise ValueError("Give a reason for dismissing it.")
    req = _exception(db, req_id, published_ok=True)
    req.status = "dismissed"
    audit.record(db, actor, "dismissed", "requirement", req_id, req.opportunity_id, reason=reason.strip())
    db.commit()
    return req


def current(db: Session, opp_id: str, include_inactive: bool = False,
            include_children: bool = False) -> list[Requirement]:
    latest = (select(Requirement.req_id, func.max(Requirement.version).label("v"))
              .where(Requirement.opportunity_id == opp_id).group_by(Requirement.req_id).subquery())
    rows = db.scalars(select(Requirement).join(latest, (Requirement.req_id == latest.c.req_id)
                                               & (Requirement.version == latest.c.v)))
    keep = [r for r in rows if (include_inactive or r.status not in INACTIVE) and (include_children or not r.parent_id)]
    docs = opportunities.documents(db, opp_id)  # upload order
    main = next((d.id for d in docs if d.role == "main"), None)
    order = {d.id: n for n, d in enumerate(docs)}
    # document order: the main RFP, then change documents in the order they came in (P-11); page, then line; items
    # not found in the source last; a group before its own sub-requirements
    return sorted(keep, key=lambda r: (r.page is None, r.document_id != main, order.get(r.document_id, len(order)),
                                       r.page or 0, r.line_start or 0, r.kind != "group", r.req_id))


def get(db: Session, req_id: str, baseline: int | None = None) -> Requirement | None:
    q = select(Requirement).where(Requirement.req_id == req_id)
    if baseline is not None:  # the version that baseline holds (a later change document may have revised it)
        q = q.where(Requirement.baseline <= baseline)
    return db.scalar(q.order_by(Requirement.version.desc()).limit(1))


def review(db: Session, req_id: str, action: str, actor: str, text: str | None = None, reason: str = "",
           category: str | None = None) -> None:
    req = get(db, req_id)
    if req is None:
        raise LookupError(f"{req_id} not found.")
    _writable(db, req.opportunity_id)
    if req.status in ("split", "merged"):
        raise ValueError(f"{req_id} is {req.status}; review its replacement instead.")
    if action in ("approve", "reject") and req.status in ("exception", "dismissed"):
        raise ValueError(f"{req_id} is in the exception queue: link it to its lines or dismiss it with a reason.")
    if action == "approve" and req.provenance != "EXTRACTED":
        raise ValueError(f"{req_id} has no verified source, so it cannot enter the register.")
    if action == "reject" and not reason.strip():
        raise ValueError("Give a reason for excluding it as not a requirement.")
    before = {"status": req.status, "text": req.text, "category": req.category}
    kids_changed = 0
    if action == "edit":
        if category and category not in CATEGORIES:
            raise ValueError(f"Unknown category {category!r}.")
        req.text, req.category = ((text or "").strip() or req.text), (category or req.category)
    elif action in ("approve", "reject"):
        req.status = {"approve": "approved", "reject": "rejected"}[action]
        if req.kind == "group":  # the decision covers the sub-requirements
            # approve: the undecided ones (and the rejected ones when the group itself is restored from rejected);
            # reject: every active one
            restore = {"proposed", "rejected"} if before["status"] == "rejected" else {"proposed"}
            for kid in children(db, req_id):
                if (kid.status in restore and req.status == "approved") or \
                        (req.status == "rejected" and kid.status not in INACTIVE):
                    kid.status = req.status
                    kids_changed += 1
    else:
        raise ValueError(f"Unknown action {action!r}.")
    after = {"status": req.status, "text": req.text, "category": req.category}
    if after == before and not kids_changed:  # a repeated click: nothing changed, so no history event
        return
    audit.record(db, actor, action, "requirement", req_id, req.opportunity_id, before=before, after=after, reason=reason)
    db.commit()


def freeze(db: Session, opp_id: str, actor: str) -> Baseline:
    _writable(db, opp_id)
    _read_main_document(db, opp_id)
    items = [r for r in current(db, opp_id) if r.status == "approved"]
    if not items:
        raise ValueError("The register is empty; a baseline needs at least one requirement.")
    unverified = [r.req_id for r in items if r.provenance != "EXTRACTED"]
    if unverified:  # data from before the register rule (14 Oct 2026); a fresh read puts them in the exception queue
        raise ValueError(f"{len(unverified)} requirements in the register have no verified source "
                         f"({', '.join(unverified[:5])}); re-read the RFP.")
    number = 1
    for r in items + [k for r in items if r.kind == "group" for k in children(db, r.req_id) if k.status == "approved"]:
        r.baseline = number
    b = Baseline(opportunity_id=opp_id, number=number, count=len(items), frozen_by=actor)
    db.add(b)
    audit.record(db, actor, "frozen", "baseline", str(number), opp_id, count=len(items))
    db.commit()
    opportunities.set_status(db, opp_id, "frozen", actor)
    return b


def _version(db: Session, old: Requirement, number: int, actor: str, **changes) -> Requirement:
    """The next version of a requirement: a copy of its latest version with `changes`, in baseline `number`."""
    fields = {c.key: getattr(old, c.key) for c in Requirement.__table__.columns if c.key not in ("id", "created_at")}
    new = Requirement(**fields | {"version": old.version + 1, "baseline": number, "created_by": actor,
                                  "bboxes": list(old.bboxes), "spans": list(old.spans),
                                  "derived_from": list(old.derived_from)} | changes)
    db.add(new)
    return new


def apply_change(db: Session, opp_id: str, change_doc_id: str, items: list[dict], actor: str, reason: str,
                 commit: bool = True) -> dict:
    """A confirmed change set becomes the next baseline (technical-architecture.md section 8). Items in document
    order; unchanged / not_a_requirement items are not passed. Nothing is edited in place: every change is a new
    version (or a new ID), so baseline 1 stays readable in the history. On any error nothing is stored."""
    opportunities.require(db, opp_id)
    b = baseline(db, opp_id)
    if b is None:
        raise ValueError("Nothing is frozen yet: a change document is compared with a frozen baseline.")
    number = b.number + 1
    out = {"baseline": number, "added": [], "modified": [], "removed": [], "affected": []}
    try:
        pages = ingestion.layout(change_doc_id)["pages"]
        live = {r.req_id: r for r in current(db, opp_id, include_children=True)}  # active latest versions
        targets = []
        for item in items:
            kind = item["kind"]
            if kind in ("added", "modified") and item["category"] not in CATEGORIES:
                raise ValueError(f"Unknown category {item['category']!r}.")
            if kind == "added":
                req = add(db, opp_id, change_doc_id, item["quote"], item["text"], item["category"], actor,
                          hint_page=item.get("page"), commit=False, pages=pages, origin="customer_change")
                if req.status == "exception":  # outside the register, listed in the exception queue
                    out.setdefault("exceptions", []).append(req.req_id)
                    continue
                req.baseline = number
                audit.record(db, actor, "approve", "requirement", req.req_id, opp_id, reason=reason, document=change_doc_id)
                live[req.req_id] = req
                out["added"].append(req.req_id)
                continue
            old = live.get(item.get("target") or "")
            if old is None or old.status != "approved" or old.baseline is None:
                raise ValueError(f"{item.get('target')} is not an approved requirement of baseline {b.number}.")
            if kind == "modified":
                hit = _anchor(anchoring.find(item["quote"], pages, item.get("page")), change_doc_id)
                if not hit:
                    raise ValueError(f"The new wording of {old.req_id} is not in the change document, so it cannot "
                                     "enter the register; correct the item's quote or mark it unchanged.")
                new = _version(db, old, number, actor, document_id=change_doc_id, text=item["text"], quote=item["quote"],
                               category=item["category"], provenance="EXTRACTED", origin="customer_change", **hit)
                db.flush()
                audit.record(db, actor, "revised", "requirement", old.req_id, opp_id, reason=reason, document=change_doc_id,
                             version=new.version, baseline=number, before={"text": old.text, "category": old.category,
                             "quote": old.quote, "source": old.source}, after={"text": new.text, "category": new.category,
                             "quote": new.quote, "source": new.source})
                live[old.req_id] = new
                out["modified"].append(old.req_id)
            elif kind == "removed":
                kids = [k for k in live.values() if k.parent_id == old.req_id] if old.kind == "group" else []
                for r in [old] + kids:  # removing a group removes its sub-requirements
                    live[r.req_id] = _version(db, r, number, actor, status="removed", origin="customer_change")
                    audit.record(db, actor, "removed", "requirement", r.req_id, opp_id, reason=reason,
                                 document=change_doc_id, version=r.version + 1, baseline=number, quote=item["quote"])
                out["removed"].append(old.req_id)
            else:
                raise ValueError(f"Unknown change {kind!r}; expected added, modified or removed.")
            targets.append(old.req_id)
        _close_baseline(db, opp_id, out, targets, live, actor, reason, document=change_doc_id)
        if commit:
            db.commit()
        else:  # the caller commits, together with its own record of the change (changes module)
            db.flush()
    except Exception:
        db.rollback()
        raise
    return out


def _close_baseline(db: Session, opp_id: str, out: dict, targets: list[str], live: dict, actor: str, reason: str,
                    **details) -> None:
    """The answers to revisit (affected) and the next baseline row with its audit event: shared by change documents
    and corrections."""
    for t in targets:  # answers to revisit: the requirement itself, or the group a sub-requirement belongs to
        r = live[t]
        top = r.parent_id if r.parent_id in live else r.req_id
        if live[top].status not in INACTIVE and top not in out["affected"]:  # removed work is withdrawn at dispatch
            out["affected"].append(top)
    db.flush()
    count = sum(r.status == "approved" for r in current(db, opp_id))
    db.add(Baseline(opportunity_id=opp_id, number=out["baseline"], count=count, frozen_by=actor))
    audit.record(db, actor, "frozen", "baseline", str(out["baseline"]), opp_id, count=count, reason=reason,
                 added=out["added"], modified=out["modified"], removed=out["removed"], **details)


CORRECTIONS = ("add", "edit", "split", "merge", "exclude", "resolve")


def apply_correction(db: Session, opp_id: str, kind: str, body: dict, actor: str, reason: str,
                     commit: bool = True) -> dict:
    """After publishing, a person corrects how the RFP was read (C-04): never in place, always a new version (origin
    correction) or a new ID in the next baseline, with the person and the reason. On any error nothing is stored."""
    opportunities.require(db, opp_id)
    b = baseline(db, opp_id)
    if b is None:
        raise ValueError("The register is not published yet: correct it directly on the Requirements page.")
    if not reason.strip():
        raise ValueError("Give a reason for the correction.")
    if kind not in CORRECTIONS:
        raise ValueError(f"Unknown correction {kind!r}; expected one of {', '.join(CORRECTIONS)}.")
    reason, number = reason.strip(), b.number + 1
    out = {"baseline": number, "added": [], "modified": [], "removed": [], "affected": []}
    category = body.get("category")
    if category and category not in CATEGORIES:
        raise ValueError(f"Unknown category {category!r}.")
    try:
        live = {r.req_id: r for r in current(db, opp_id, include_children=True)}  # active latest versions
        targets = []

        def published(req_id: str) -> Requirement:
            r = live.get(req_id or "")
            if r is None or r.status != "approved" or r.baseline is None:
                raise ValueError(f"{req_id} is not a requirement of baseline {b.number}.")
            return r

        def lines() -> tuple:
            doc, chosen = _selected_lines(db, opp_id, int(body.get("page") or 0), int(body.get("line_start") or 0),
                                          int(body.get("line_end") or 0))
            quote = " ".join(line["text"] for line in chosen)
            return doc, quote, [{"page": body["page"], "lines": chosen}]

        def event(action: str, req_id: str, **data):
            audit.record(db, actor, action, "requirement", req_id, opp_id, reason=reason, baseline=number,
                         correction=kind, **data)

        if kind == "add":
            if category is None:
                raise ValueError("Choose a category.")
            doc, quote, pages = lines()
            req = add(db, opp_id, doc.id, quote, (body.get("text") or "").strip()[:200] or quote[:200], category, actor,
                      hint_page=body["page"], commit=False, pages=pages, origin="correction")
            req.baseline = number
            event("corrected", req.req_id, before={}, after={"text": req.text, "category": req.category,
                                                            "source": req.source})
            live[req.req_id] = req
            out["added"].append(req.req_id)
        elif kind == "resolve":
            req = get(db, body.get("req_id") or "")
            if req is None or req.opportunity_id != opp_id or req.status != "exception":
                raise ValueError(f"{body.get('req_id')} is not in the exception queue.")
            doc, quote, pages = lines()
            hit = _anchor(anchoring.find(quote, pages, body["page"]), doc.id)
            if not hit:
                raise ValueError("The selected lines have no text to link; select the requirement's own lines.")
            new = _version(db, req, number, actor, document_id=doc.id, quote=quote, provenance="EXTRACTED",
                           status="approved", origin="correction", location_hint=None, text=(body.get("text") or "").strip() or req.text,
                           category=category or req.category, **hit)
            db.flush()
            event("resolved", req.req_id, version=new.version, before={"quote": req.quote},
                  after={"quote": new.quote, "source": new.source, "text": new.text, "category": new.category})
            live[req.req_id] = new
            out["added"].append(req.req_id)
        elif kind == "edit":
            old = published(body.get("req_id"))
            text = (body.get("text") or "").strip()[:200] or old.text
            if (text, category or old.category) == (old.text, old.category):
                raise ValueError("Nothing to correct: the text and the category are unchanged.")
            new = _version(db, old, number, actor, text=text, category=category or old.category, origin="correction")
            db.flush()
            event("corrected", old.req_id, version=new.version, before={"text": old.text, "category": old.category},
                  after={"text": new.text, "category": new.category})
            live[old.req_id] = new
            out["modified"].append(old.req_id)
            targets.append(old.req_id)
        elif kind == "exclude":
            old = published(body.get("req_id"))
            kids = [k for k in live.values() if k.parent_id == old.req_id] if old.kind == "group" else []
            for r in [old] + kids:  # excluding a group excludes its sub-requirements
                live[r.req_id] = _version(db, r, number, actor, status="rejected", origin="correction")
                event("reject", r.req_id, version=r.version + 1)
            out["removed"].append(old.req_id)
            targets.append(old.req_id)
        elif kind == "split":
            old = published(body.get("req_id"))
            if old.kind == "group" or old.parent_id:
                raise ValueError(f"{old.req_id} is a group or a sub-requirement; exclude it and add its parts from lines.")
            parts = [p for p in body.get("parts") or [] if (p.get("quote") or "").strip()]
            if len(parts) < 2:
                raise ValueError("A split needs at least two parts.")
            pages = ingestion.layout(old.document_id)["pages"]
            for n, p in enumerate(parts, 1):
                part = add(db, opp_id, old.document_id, p["quote"], (p.get("text") or p["quote"])[:200], old.category,
                           actor, old.section, old.page, [old.req_id], commit=False, pages=pages, origin="correction")
                if part.status != "approved":
                    raise ValueError(f"Part {n} is not found in the source; copy it exactly from the document.")
                part.baseline = number
                live[part.req_id] = part
                out["added"].append(part.req_id)
            live[old.req_id] = _version(db, old, number, actor, status="split", origin="correction")
            event("split", old.req_id, into=out["added"])
            out["removed"].append(old.req_id)
            targets.append(old.req_id)
        elif kind == "merge":
            olds = [published(r) for r in dict.fromkeys(body.get("req_ids") or [])]
            text = (body.get("text") or "").strip()[:200]
            if len(olds) < 2 or not text:
                raise ValueError("A merge needs at least two requirements and a short text.")
            if any(r.kind == "group" or r.parent_id for r in olds):
                raise ValueError("Groups and sub-requirements cannot be merged.")
            if len({(r.document_id, r.page) for r in olds}) > 1:
                raise ValueError("Only requirements on the same page can be merged.")
            olds.sort(key=lambda r: r.line_start or 0)
            first = olds[0]
            merged = Requirement(
                req_id=_next_req_id(db, opp_id), opportunity_id=opp_id, document_id=first.document_id, text=text,
                quote=" … ".join(r.quote for r in olds), category=category or first.category, section=first.section,
                created_by=actor, derived_from=[r.req_id for r in olds], page=first.page, line_start=first.line_start,
                line_end=max(r.line_end or 0 for r in olds), bboxes=[x for r in olds for x in r.bboxes],
                spans=[x for r in olds for x in r.spans],
                provenance="EXTRACTED", status="approved", origin="correction", baseline=number)
            db.add(merged)
            db.flush()
            event("merged", merged.req_id, merged_from=merged.derived_from)
            for r in olds:
                live[r.req_id] = _version(db, r, number, actor, status="merged", origin="correction")
                event("merged_into", r.req_id, into=merged.req_id)
                out["removed"].append(r.req_id)
                targets.append(r.req_id)
            live[merged.req_id] = merged
            out["added"].append(merged.req_id)
        _close_baseline(db, opp_id, out, targets, live, actor, reason, correction=kind)
        if commit:
            db.commit()
        else:  # the caller commits, together with its follow-up (changes module)
            db.flush()
    except Exception:
        db.rollback()
        raise
    return out


def locate(quote: str, pages: list[dict], hint_page: int | None = None) -> dict | None:
    return anchoring.find(quote, pages, hint_page)


def baseline(db: Session, opp_id: str) -> Baseline | None:
    return db.scalar(select(Baseline).where(Baseline.opportunity_id == opp_id)
                     .order_by(Baseline.number.desc()).limit(1))


def history(db: Session, req_id: str) -> dict:
    """The change history of one line item, rebuilt from the append-only audit log (it is the source of truth).

    versions: the original wording, then one entry per edit that changed text or category, one per correction
              after publishing or exception linked to its lines (label "corrected") and one per revision by a change
              document (label "revised", reason = the change document); each with its origin.
    events:   everything that happened to it (proposed, edits, approve / reject, split, merge, each baseline it is in,
              revised / removed by a change document).
    """
    req = get(db, req_id)
    if req is None:
        raise LookupError(f"{req_id} not found.")
    events = list(db.scalars(select(AuditEvent).where(
        AuditEvent.opportunity_id == req.opportunity_id, AuditEvent.entity == "requirement",
        AuditEvent.entity_id == req_id).order_by(AuditEvent.id)))
    numbers = {str(n) for n in db.scalars(select(Requirement.baseline).where(Requirement.req_id == req_id)) if n is not None}
    events = sorted(events + list(db.scalars(select(AuditEvent).where(
        AuditEvent.opportunity_id == req.opportunity_id, AuditEvent.entity == "baseline",
        AuditEvent.entity_id.in_(numbers)))), key=lambda e: e.id)

    def wording(d: dict) -> dict:
        return {"text": d.get("text"), "category": d.get("category")}

    edits = [e for e in events if e.action == "edit" and wording(e.data.get("before", {})) != wording(e.data.get("after", {}))]
    proposed = next((e for e in events if e.action == "proposed"), None)
    if proposed and "text" in proposed.data:
        first = wording(proposed.data)
    elif edits:  # line items read before 9 Oct: the first edit's "before" is the original wording
        first = wording(edits[0].data["before"])
    else:
        first = {"text": req.text, "category": req.category}
    v1 = db.scalar(select(Requirement.origin).where(Requirement.req_id == req_id).order_by(Requirement.version).limit(1))
    versions = [{"n": 1, "at": proposed.at if proposed else req.created_at, "by": proposed.actor if proposed else req.created_by,
                 "label": "original", "origin": (proposed.data.get("origin") if proposed else None) or v1 or "extraction",
                 **first}]
    labels = {"edit": ("edited", "correction"), "corrected": ("corrected", "correction"),
              "resolved": ("corrected", "correction"), "revised": ("revised", "customer_change")}
    for e in [e for e in events if e in edits or e.action in ("corrected", "resolved", "revised")]:
        label, origin = labels[e.action]
        versions.append({"n": len(versions) + 1, "at": e.at, "by": e.actor, "label": label, "origin": origin,
                         "reason": e.data.get("reason", ""), **wording(e.data["after"])})
    return {"req_id": req_id, "quote": req.quote, "source": req.source, "derived_from": req.derived_from,
            "versions": versions,
            "events": [{"at": e.at, "by": e.actor, "action": e.action,
                        "details": {k: v for k, v in e.data.items() if k not in ("text", "quote", "before", "after")}}
                       for e in events]}
