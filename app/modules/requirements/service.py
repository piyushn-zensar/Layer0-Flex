"""Requirements: line items with exact sources, human review, frozen baseline.  Owner: Piyush.

Public contract:
    extract(db, opp_id, actor) -> dict           reader agent on the main RFP, then duplicates marked and related
                                                 items grouped into requirements with sub-requirements (drafts only)
    add(db, opp_id, document_id, quote, text, category, actor, section="", hint_page=None) -> Requirement
    current(db, opp_id, include_inactive=False, include_children=False) -> list[Requirement]
                                                 the requirements the workflow works on, in document order: groups and
                                                 stand-alone items, not their sub-requirements (inactive = rejected,
                                                 duplicate, or replaced by a split / merge)
    children(db, req_id) -> list[Requirement]    the sub-requirements of a group
    ungroup(db, req_id, actor, reason="") -> list[Requirement]   a group's sub-requirements become requirements again
    get(db, req_id, baseline=None) -> Requirement | None   latest version; with baseline: the version in that baseline
    review(db, req_id, action, actor, text=None, reason="", category=None)   action: approve | reject | edit;
                                                 approve / reject of a group applies to its sub-requirements;
                                                 approving a duplicate restores it
    split(db, req_id, parts, actor, reason="") -> list[Requirement]   parts: [{"quote", "text"}], >= 2
    merge(db, opp_id, req_ids, text, actor, reason="") -> Requirement  >= 2 line items into one
    add_missed(db, opp_id, quote, text, category, actor, page=None) -> Requirement   a person adds what the agent missed
    add_from_lines(db, opp_id, page, line_start, line_end, text, category, actor) -> Requirement
                                                 the same, by selecting lines of the main RFP: the quote is those
                                                 lines verbatim (headers / footers left out), so the source is exact
    freeze(db, opp_id, actor) -> Baseline        approved items become baseline 1; needs a read main RFP, every item
                                                 decided and at least one approved; once only (later: apply_change)
    apply_change(db, opp_id, change_doc_id, items, actor, reason, commit=True) -> dict
                                                 the ONLY write after a freeze (changes module): items = confirmed
                                                 [{"kind": added | modified | removed, "target", "quote", "text",
                                                 "category", "page"}]; modified -> a new version anchored in the
                                                 change document, removed -> a new version "removed" (a group's
                                                 sub-requirements too), added -> a new ID; all in the next baseline.
                                                 Returns {"baseline", "added", "modified", "removed", "affected"}
                                                 (affected: requirements whose answers must be revisited). Atomic.
                                                 LookupError unknown opportunity; ValueError no baseline, bad target
Every other write refuses once the opportunity has a baseline, and LookupError for an unknown opportunity or item.
Requirement IDs are never reused: the next number is taken over every ID ever issued, including discarded drafts.
    baseline(db, opp_id) -> Baseline | None      latest frozen baseline
    history(db, req_id) -> dict                  every version (who, when, text, category) and every event; LookupError
    locate(quote, pages, hint_page=None) -> dict | None   a quote's page, lines and boxes in layout pages (rule R1)
    CATEGORIES                                   the requirement categories
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import audit
from app.core.audit import AuditEvent
from app.modules.ingestion import service as ingestion
from app.modules.opportunities import service as opportunities
from app.modules.requirements import agent, anchoring, grouping
from app.modules.requirements.models import CATEGORIES, Baseline, Requirement

INACTIVE = {"rejected", "split", "merged", "duplicate", "removed"}  # removed: deleted by a change document
AGENTS = ("reader agent", "grouping agent")


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
    """Every write except apply_change() calls this: after a freeze, requirements change only by change documents."""
    opportunities.require(db, opp_id)
    b = baseline(db, opp_id)
    if b:
        raise ValueError(f"Requirements are frozen in baseline {b.number}; later changes go through the changes module.")


def add(db: Session, opp_id: str, document_id: str, quote: str, text: str, category: str, actor: str,
        section: str = "", hint_page: int | None = None, derived_from: list[str] | None = None,
        commit: bool = True, pages: list[dict] | None = None) -> Requirement:
    if not quote.strip():
        raise ValueError("A requirement needs a quote copied from the RFP.")
    hit = anchoring.find(quote, pages if pages is not None else ingestion.layout(document_id)["pages"], hint_page)
    req = Requirement(req_id=_next_req_id(db, opp_id), opportunity_id=opp_id, document_id=document_id,
                      text=text, quote=quote, category=category, section=section, created_by=actor,
                      derived_from=derived_from or [], provenance="EXTRACTED" if hit else "UNANCHORED", **(hit or {}))
    db.add(req)
    db.flush()  # the next _next_req_id sees this one
    audit.record(db, actor, "proposed", "requirement", req.req_id, opp_id, provenance=req.provenance,
                 derived_from=req.derived_from, text=req.text, category=req.category, quote=req.quote)
    if commit:
        db.commit()
    return req


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
                    req.category, actor, req.section, req.page, [req.req_id], commit=False) for p in parts]
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
        raise ValueError("Line items from another opportunity cannot be merged.")
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
        bboxes=[b for r in reqs for b in r.bboxes],
        provenance="EXTRACTED" if all(r.provenance == "EXTRACTED" for r in reqs) else "UNANCHORED")
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
    return add(db, opp_id, doc.id, quote, (text.strip() or quote.strip())[:200], category, actor, hint_page=page)


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
    quote = " ".join(line["text"] for line in chosen)
    # anchored in the selected lines only, so the source is the selection itself (never the same words elsewhere)
    return add(db, opp_id, doc.id, quote, (text.strip() or quote.strip())[:200], category, actor, hint_page=page,
               pages=[{"page": page, "lines": chosen}])


def _read_main_document(db: Session, opp_id: str):
    doc = opportunities.main_document(db, opp_id)
    if doc is None or doc.status != "ingested":
        raise ValueError("Upload the main RFP and wait until it has been read.")
    return doc


def extract(db: Session, opp_id: str, actor: str) -> dict:
    _writable(db, opp_id)
    doc = _read_main_document(db, opp_id)
    reviewed = db.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.opportunity_id == opp_id, AuditEvent.entity == "requirement",
        AuditEvent.action.in_(["approve", "reject", "edit", "split", "merged"])))
    if reviewed:
        raise ValueError(f"Review has started ({reviewed} review actions); re-reading would lose that work. "
                         "Add what is missing with 'Add a requirement' instead.")
    layout = ingestion.layout(doc.id)
    proposed, problems = agent.read(layout)
    for old in db.scalars(select(Requirement).where(Requirement.opportunity_id == opp_id,
                                                    Requirement.status.in_(["proposed", "duplicate"]))):
        if old.created_by.startswith(AGENTS):  # a re-run replaces the agents' unreviewed proposals; people's stay
            audit.record(db, actor, "discarded", "requirement", old.req_id, opp_id, reason="re-read replaced the draft")
            db.delete(old)
    db.commit()
    items = [add(db, opp_id, doc.id, item["quote"], item["text"], item["category"], f"reader agent ({actor})",
                 item["section"], item["page"], commit=False, pages=layout["pages"]) for item in proposed]
    dups = grouping.duplicates([{"quote": r.quote} for r in items])
    for i, first in dups.items():
        items[i].status, items[i].derived_from = "duplicate", [items[first].req_id]
        audit.record(db, actor, "duplicate_of", "requirement", items[i].req_id, opp_id, of=items[first].req_id)
    unique = [r for i, r in enumerate(items) if i not in dups]
    groups, group_problems = grouping.group([{"page": r.page, "text": r.text, "category": r.category} for r in unique])
    for g in groups:
        _create_group(db, opp_id, [unique[i] for i in g["members"]], g["title"], g["category"], f"grouping agent ({actor})")
    db.commit()
    opportunities.set_status(db, opp_id, "review", actor)
    return {"proposed": len(proposed), "duplicates": len(dups), "groups": len(groups),
            "requirements": len(current(db, opp_id)), "problems": problems + group_problems}


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
                    bboxes=[b for r in anchored for b in r.bboxes],
                    provenance="EXTRACTED" if len(anchored) == len(members) else "UNANCHORED")
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
    before = {"status": req.status, "text": req.text, "category": req.category}
    if action == "edit":
        if category and category not in CATEGORIES:
            raise ValueError(f"Unknown category {category!r}.")
        req.text, req.category = ((text or "").strip() or req.text), (category or req.category)
    elif action in ("approve", "reject"):
        req.status = {"approve": "approved", "reject": "rejected"}[action]
        if req.kind == "group":  # the decision covers the sub-requirements
            for kid in children(db, req_id):  # approve: the undecided ones; reject: every active one
                if kid.status == "proposed" or (req.status == "rejected" and kid.status not in INACTIVE):
                    kid.status = req.status
    else:
        raise ValueError(f"Unknown action {action!r}.")
    audit.record(db, actor, action, "requirement", req_id, req.opportunity_id, before=before,
                 after={"status": req.status, "text": req.text, "category": req.category}, reason=reason)
    db.commit()


def freeze(db: Session, opp_id: str, actor: str) -> Baseline:
    _writable(db, opp_id)
    _read_main_document(db, opp_id)
    undecided = [r.req_id for r in current(db, opp_id) if r.status == "proposed"]
    if undecided:
        raise ValueError(f"{len(undecided)} line items still need approve or reject before freezing.")
    items = [r for r in current(db, opp_id) if r.status == "approved"]
    if not items:
        raise ValueError("Nothing is approved; a baseline needs at least one requirement.")
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
                                  "bboxes": list(old.bboxes), "derived_from": list(old.derived_from)} | changes)
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
                          hint_page=item.get("page"), commit=False, pages=pages)
                req.status, req.baseline = "approved", number
                audit.record(db, actor, "approve", "requirement", req.req_id, opp_id, reason=reason, document=change_doc_id)
                live[req.req_id] = req
                out["added"].append(req.req_id)
                continue
            old = live.get(item.get("target") or "")
            if old is None or old.status != "approved" or old.baseline is None:
                raise ValueError(f"{item.get('target')} is not an approved requirement of baseline {b.number}.")
            if kind == "modified":
                hit = anchoring.find(item["quote"], pages, item.get("page"))
                new = _version(db, old, number, actor, document_id=change_doc_id, text=item["text"], quote=item["quote"],
                               category=item["category"], provenance="EXTRACTED" if hit else "UNANCHORED",
                               **(hit or {"page": None, "line_start": None, "line_end": None, "bboxes": []}))
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
                    live[r.req_id] = _version(db, r, number, actor, status="removed")
                    audit.record(db, actor, "removed", "requirement", r.req_id, opp_id, reason=reason,
                                 document=change_doc_id, version=r.version + 1, baseline=number, quote=item["quote"])
                out["removed"].append(old.req_id)
            else:
                raise ValueError(f"Unknown change {kind!r}; expected added, modified or removed.")
            targets.append(old.req_id)
        for t in targets:  # answers to revisit: the requirement itself, or the group a sub-requirement belongs to
            r = live[t]
            top = r.parent_id if r.parent_id in live else r.req_id
            if live[top].status != "removed" and top not in out["affected"]:  # removed work is withdrawn at dispatch
                out["affected"].append(top)
        db.flush()
        count = sum(r.status == "approved" for r in current(db, opp_id))
        db.add(Baseline(opportunity_id=opp_id, number=number, count=count, frozen_by=actor))
        audit.record(db, actor, "frozen", "baseline", str(number), opp_id, count=count, document=change_doc_id,
                     reason=reason, added=out["added"], modified=out["modified"], removed=out["removed"])
        if commit:
            db.commit()
        else:  # the caller commits, together with its own record of the change (changes module)
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

    versions: the original wording, then one entry per edit that changed text or category, and one per revision
              by a change document (label "revised", reason = the change document).
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
    versions = [{"n": 1, "at": proposed.at if proposed else req.created_at, "by": proposed.actor if proposed else req.created_by,
                 "label": "original", **first}]
    for e in [e for e in events if e in edits or e.action == "revised"]:
        versions.append({"n": len(versions) + 1, "at": e.at, "by": e.actor, "label": "edited" if e.action == "edit" else "revised",
                         "reason": e.data.get("reason", ""), **wording(e.data["after"])})
    return {"req_id": req_id, "quote": req.quote, "source": req.source, "derived_from": req.derived_from,
            "versions": versions,
            "events": [{"at": e.at, "by": e.actor, "action": e.action,
                        "details": {k: v for k, v in e.data.items() if k not in ("text", "quote", "before", "after")}}
                       for e in events]}
