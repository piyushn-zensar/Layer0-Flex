"""Changes: addenda, Q&A answers and change requests processed as a delta against the frozen baseline (P-11,
technical-architecture.md section 8).  Owner: Piyush.

A change document is stored with the role "change" and read like the RFP (same layout model, same anchoring).
The change agent lists its statements and classifies each one against the frozen baseline; a person confirms
every classification. Applying the confirmed set makes the next baseline (new versions, new IDs, removals),
returns the answers of changed requirements to their units, and matches and dispatches what is new. A large
share of modified or removed requirements is flagged as drastic, so a person can decide on a new linked
opportunity; Layer 0 never decides that.

Public contract:
    DRASTIC_SHARE                                 0.25, placeholder (Needs confirmation, section 8)
    upload(db, opp_id, filename, data, actor) -> ChangeSet   store, read and classify a change PDF. LookupError:
        unknown opportunity; ValueError: no frozen baseline, a set still in review, not a PDF, the file is the
        main RFP or already applied, or no model answer (mock mode): then no change set is created
    overview(db, opp_id) -> dict                  {"baseline": {number, count} | None, "drastic_threshold",
                                                  "sets": [view], newest first}; LookupError
    sets(db, opp_id) -> list[ChangeSet]           newest first; LookupError
    get(db, set_id) -> ChangeSet                  LookupError
    decide(db, set_id, item_id, kind, target, text, actor) -> ChangeItem   a person confirms or overrides one
        classification; target (modified / removed / unchanged) must be an approved line item of the baseline;
        text replaces the new wording. Only in review. LookupError / ValueError
    confirm_all(db, set_id, actor) -> ChangeSet   every still-proposed item confirmed as proposed
    apply(db, set_id, actor) -> ChangeSet         Bid Manager only (PermissionError); every item confirmed, no
        requirement changed by two items, and the baseline unchanged since the upload (ValueError). result:
        {baseline, added, modified, removed, returned, dispatched, note}; a failure after the new baseline is
        committed (returns, matching, dispatch) is reported in note, not raised. Of two applies / discards of one
        set at once only the first goes through
    discard(db, set_id, actor) -> ChangeSet       Bid Manager only; only from review
    Anyone may upload, decide and confirm items (agents propose, a person confirms); applying is the Bid Manager's.
    view(db, change_set) -> dict / item_view(db, item) -> dict   the API shape (counts, share, drastic, pages,
        items with the target's wording in the baseline the set was compared with)
"""
from collections import defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core import audit
from app.core.db import utcnow
from app.modules.changes import agent
from app.modules.changes.models import KINDS, NEEDS_TARGET, ChangeItem, ChangeSet
from app.modules.decisions import service as decisions
from app.modules.ingestion import service as ingestion
from app.modules.matching import service as matching
from app.modules.opportunities import service as opportunities
from app.modules.requirements import service as requirements
from app.modules.workpackages import service as workpackages

BID_MANAGER = "Bid Manager"  # ponytail: PoC actor name from the header picker; real roles come with sign-in
DRASTIC_SHARE = 0.25  # ponytail: placeholder; the drastic-change threshold Needs confirmation (section 8)
CANDIDATES = 5        # baseline line items shown to the agent per statement (letters A-E)
VERB = {"modified": "changes", "removed": "removes", "unchanged": "leaves unchanged"}


def _baseline_items(db: Session, opp_id: str) -> list:
    """Every approved line item of the frozen baseline: groups, stand-alone items and sub-requirements."""
    return [r for r in requirements.current(db, opp_id, include_children=True)
            if r.status == "approved" and r.baseline is not None]


def rank(statements: list[dict], items: list) -> list[list[int]]:
    """Up to CANDIDATES baseline items per statement (indexes into items), by TF-IDF cosine of the statement's text
    and quote against each item's text and quote. Deterministic and the same online and offline (never the
    embedding index), so the classify prompt and its frozen answer do not depend on the search mode.
    Ties keep document order."""
    if not items or not statements:
        return [[] for _ in statements]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        matrix = vectorizer.fit_transform([f"{r.text} {r.quote}" for r in items])
    except ValueError:  # nothing but stop words
        return [[] for _ in statements]
    scores = np.round(linear_kernel(vectorizer.transform([f"{s['text']} {s['quote']}" for s in statements]), matrix), 6)
    return [[int(i) for i in np.argsort(-row, kind="stable") if row[i] > 0][:CANDIDATES] for row in scores]


def _no_set_in_review(db: Session, opp_id: str, besides: int | None = None) -> None:
    q = select(ChangeSet).where(ChangeSet.opportunity_id == opp_id, ChangeSet.status == "review")
    pending = db.scalar(q.where(ChangeSet.id != besides) if besides else q)
    if pending:
        raise ValueError(f"{pending.filename} (change set {pending.id}) is still in review: apply or discard it first.")


def _claim(db: Session, s: ChangeSet, status: str) -> None:
    """Sets the status in the caller's transaction, only if the set is still in review in the database (status
    "review" just holds it until the caller commits): of two applies or discards of one set at once (double click,
    two tabs) only the first goes through, and no decision lands on a set that was applied meanwhile."""
    if db.execute(update(ChangeSet).where(ChangeSet.id == s.id, ChangeSet.status == "review")
                  .values(status=status)).rowcount != 1:
        db.rollback()
        raise ValueError(f"Change set {s.id} was applied or discarded meanwhile; refresh the page.")


def _unavailable(filename: str) -> ValueError:
    return ValueError(f"{filename} has no frozen answers from the change agent (mock mode): "
                      "set LLM_PROVIDER=azure to read it.")


def upload(db: Session, opp_id: str, filename: str, data: bytes, actor: str) -> ChangeSet:
    opportunities.require(db, opp_id)
    b = requirements.baseline(db, opp_id)
    if b is None:
        raise ValueError("Freeze the requirements first: a change document is compared with the frozen baseline.")
    _no_set_in_review(db, opp_id)
    if not filename.lower().endswith(".pdf"):
        raise ValueError("Upload the change document as a PDF.")
    doc = opportunities.add_document(db, opp_id, filename, data, "change", actor)
    if doc.role == "main":  # the same file uploaded earlier as an addendum or Q&A is fine: it keeps that role
        raise ValueError(f"This file is the main RFP of {opp_id}, not a change document.")
    done = db.scalar(select(ChangeSet).where(ChangeSet.document_id == doc.id, ChangeSet.status == "applied"))
    if done:
        raise ValueError(f"{doc.filename} was already applied (change set {done.id}, baseline {done.baseline_to}).")
    if doc.status != "ingested":
        read = ingestion.ingest(db, doc.id)
        if "error" in read:
            raise ValueError(f"{doc.filename} could not be read: {read['error']}")
    layout = ingestion.layout(doc.id)
    try:
        statements = agent.read(layout)
    except agent.LLMUnavailable:
        raise _unavailable(doc.filename)
    if not statements:
        raise ValueError(f"The change agent found no statements in {doc.filename}.")
    items = _baseline_items(db, opp_id)
    for s, idx in zip(statements, rank(statements, items)):
        s["found"] = [items[i] for i in idx]
    try:
        answers = agent.classify([s | {"candidates": [{"text": r.text, "quote": r.quote} for r in s["found"]]}
                                  for s in statements])
    except agent.LLMUnavailable:
        raise _unavailable(doc.filename)

    change = ChangeSet(opportunity_id=opp_id, document_id=doc.id, filename=doc.filename, baseline_from=b.number,
                       baseline_count=b.count, created_by=actor)
    db.add(change)
    db.flush()  # holds the database write lock from here, so a set uploaded meanwhile (reading takes long) is seen
    try:
        _no_set_in_review(db, opp_id, change.id)
    except ValueError:
        db.rollback()
        raise
    for n, (s, a) in enumerate(zip(statements, answers), 1):
        hit = requirements.locate(s["quote"], layout["pages"], s["page"]) or {}  # never the model's own page claim
        target = s["found"][a["target"]].req_id if a["target"] is not None else None
        db.add(ChangeItem(
            set_id=change.id, n=n, page=hit.get("page"), line_start=hit.get("line_start"), line_end=hit.get("line_end"),
            bboxes=hit.get("bboxes", []), quote=s["quote"], text=a["new_text"],
            category=s["category"] if s["category"] in requirements.CATEGORIES else "technical", action=s["action"],
            candidates=[{"req_id": r.req_id, "text": r.text, "source": r.source} for r in s["found"]],
            proposed_kind=a["change"], proposed_target=target, rationale=a["rationale"], confidence=a["confidence"]))
    counts = defaultdict(int)
    for a in answers:
        counts[a["change"]] += 1
    audit.record(db, actor, "read", "change", str(change.id), opp_id, document=doc.id, filename=doc.filename,
                 baseline=b.number, statements=len(statements), proposed=dict(counts))
    db.commit()
    return change


def sets(db: Session, opp_id: str) -> list[ChangeSet]:
    opportunities.require(db, opp_id)
    return list(db.scalars(select(ChangeSet).where(ChangeSet.opportunity_id == opp_id).order_by(ChangeSet.id.desc())))


def get(db: Session, set_id: int) -> ChangeSet:
    s = db.get(ChangeSet, set_id)
    if s is None:
        raise LookupError(f"Change set {set_id} not found.")
    return s


def _items(db: Session, set_id: int) -> list[ChangeItem]:
    return list(db.scalars(select(ChangeItem).where(ChangeItem.set_id == set_id).order_by(ChangeItem.n)))


def _in_review(s: ChangeSet) -> None:
    if s.status != "review":
        raise ValueError(f"Change set {s.id} is {s.status}; only a set in review can be changed.")


def decide(db: Session, set_id: int, item_id: int, kind: str, target: str | None, text: str | None,
           actor: str) -> ChangeItem:
    s = get(db, set_id)
    item = db.get(ChangeItem, item_id)
    if item is None or item.set_id != s.id:
        raise LookupError(f"Item {item_id} is not in change set {set_id}.")
    _in_review(s)
    if kind not in KINDS:
        raise ValueError(f"Unknown classification {kind!r}; expected one of {KINDS}.")
    if kind in NEEDS_TARGET:
        if not target:
            raise ValueError(f"Name the baseline requirement this statement {VERB[kind]}.")
        if target not in {r.req_id for r in _baseline_items(db, s.opportunity_id)}:
            raise ValueError(f"{target} is not an approved requirement of baseline {s.baseline_from}.")
    else:
        target = None
    _claim(db, s, "review")
    before = {"kind": item.kind or item.proposed_kind, "target": item.target if item.kind else item.proposed_target,
              "text": item.text}
    item.kind, item.target, item.status, item.decided_by = kind, target, "confirmed", actor
    if text and text.strip():
        item.text = text.strip()
    same = (kind, target) == (item.proposed_kind, item.proposed_target)
    audit.record(db, actor, "confirmed" if same else "overridden", "change", str(s.id), s.opportunity_id,
                 item=item.n, kind=kind, target=target, before=before, after_text=item.text)
    db.commit()
    return item


def confirm_all(db: Session, set_id: int, actor: str) -> ChangeSet:
    s = get(db, set_id)
    _in_review(s)
    _claim(db, s, "review")
    open_ = [i for i in _items(db, s.id) if i.status == "proposed"]
    for i in open_:
        i.kind, i.target, i.status, i.decided_by = i.proposed_kind, i.proposed_target, "confirmed", actor
    audit.record(db, actor, "confirmed_all", "change", str(s.id), s.opportunity_id, items=[i.n for i in open_])
    db.commit()
    return s


def apply(db: Session, set_id: int, actor: str) -> ChangeSet:
    """The confirmed set becomes the next baseline, in one transaction with the set's own "applied" record.
    Then: answers of changed requirements go back to their units, new and changed requirements are matched, and
    after a "go" (and if work was dispatched before) dispatch runs, which also withdraws removed work."""
    s = get(db, set_id)
    if actor != BID_MANAGER:
        raise PermissionError("Only the Bid Manager applies a change set.")
    _in_review(s)
    opp_id = s.opportunity_id
    _claim(db, s, "applied")  # first, so the items and the baseline read below cannot change before this set commits
    try:
        items = _items(db, s.id)
        open_ = [i.n for i in items if i.status != "confirmed"]
        if open_:
            raise ValueError(f"{len(open_)} classification(s) still need a person's confirmation (items {open_[:10]}).")
        same = defaultdict(list)  # a later version would silently replace an earlier one's wording in the new baseline
        for i in items:
            if i.kind in ("modified", "removed"):
                same[i.target].append(i.n)
        for target, ns in same.items():
            if len(ns) > 1:
                raise ValueError(f"Items {ns} all change {target}: put the combined new wording in one of them and "
                                 "mark the others unchanged.")
        b = requirements.baseline(db, opp_id)
        if b is None or b.number != s.baseline_from:
            raise ValueError(f"This set was read against baseline {s.baseline_from}, which is no longer the latest; "
                             "discard it and upload the document again.")
    except ValueError:
        db.rollback()  # the set stays in review
        raise
    changes = [{"kind": i.kind, "target": i.target, "quote": i.quote, "text": i.text, "category": i.category,
                "page": i.page} for i in items if i.kind in ("added", "modified", "removed")]
    dispatched_before = bool(workpackages.by_requirement(db, opp_id))
    reason = f"{s.filename} (change set {s.id})"
    if changes:  # raises (and stores nothing) if a target is no longer valid
        out = requirements.apply_change(db, opp_id, s.document_id, changes, actor, reason, commit=False)
    else:
        out = {"baseline": s.baseline_from, "added": [], "modified": [], "removed": [], "affected": []}
    s.status, s.applied_by, s.applied_at, s.baseline_to = "applied", actor, utcnow(), out["baseline"]
    result = {k: out[k] for k in ("baseline", "added", "modified", "removed")} | {"returned": 0, "dispatched": 0, "note": ""}
    s.result = dict(result)  # a copy, so the update below is seen as a change of the JSON column
    audit.record(db, actor, "applied", "change", str(s.id), opp_id, document=s.document_id, **result)
    db.commit()

    try:  # the baseline is committed: a failure from here on (e.g. the model service) is reported, not raised
        notes = defaultdict(list)  # what changed, per requirement whose answers are returned
        for i in items:
            if i.kind in ("modified", "removed"):
                parent = requirements.get(db, i.target).parent_id
                what = f"now reads: {i.text[:200]}" if i.kind == "modified" else "removed"
                notes[parent or i.target].append(f"sub-requirement {i.target} {what}" if parent else what)
        for req_id in out["affected"]:
            note = f"Changed by {s.filename}: {'; '.join(notes.get(req_id) or ['changed'])}"
            result["returned"] += workpackages.return_for_change(db, opp_id, [req_id], note, actor)
        if out["added"] or out["modified"]:
            # only what changed: re-matching everything would change the frozen page batches of untouched requirements
            matching.match(db, opp_id, f"matching agent ({actor})", req_ids=out["added"] + out["modified"])
        go = decisions.latest(db, opp_id, "go_no_go")
        if not changes:
            result["note"] = f"Nothing changed: the baseline stays {s.baseline_from}."
        elif not dispatched_before:
            result["note"] = "Not dispatched: no work was dispatched before this change; dispatch from the decisions page."
        elif not go or go.outcome != "go":
            result["note"] = ("Not dispatched: the latest go/no-go is not 'go'. New work is created and removed work "
                              "withdrawn at the next dispatch.")
        else:
            try:
                result["dispatched"] = workpackages.dispatch(db, opp_id, actor)
            except ValueError as exc:
                result["note"] = f"Not dispatched: {exc}"
    except Exception as exc:
        db.rollback()
        result["note"] = (f"Baseline {out['baseline']} is applied, but the follow-up stopped ({type(exc).__name__}: "
                          f"{exc}); new and changed requirements may still need matching and dispatch.")
        audit.record(db, actor, "follow_up_failed", "change", str(s.id), opp_id, error=str(exc)[:500])
    s.result = dict(result)
    db.commit()
    return s


def discard(db: Session, set_id: int, actor: str) -> ChangeSet:
    s = get(db, set_id)
    if actor != BID_MANAGER:
        raise PermissionError("Only the Bid Manager discards a change set.")
    _in_review(s)
    _claim(db, s, "discarded")
    s.status = "discarded"
    audit.record(db, actor, "discarded", "change", str(s.id), s.opportunity_id, document=s.document_id)
    db.commit()
    return s


def item_view(db: Session, i: ChangeItem) -> dict:
    t = i.target or i.proposed_target
    # the wording it was compared with, also after this set (or a later one) revised the requirement
    req = requirements.get(db, t, get(db, i.set_id).baseline_from) if t else None
    return {"id": i.id, "n": i.n, "page": i.page, "line_start": i.line_start, "line_end": i.line_end,
            "bboxes": i.bboxes, "source": i.source, "quote": i.quote, "text": i.text, "category": i.category,
            "action": i.action, "proposed_kind": i.proposed_kind, "proposed_target": i.proposed_target,
            "rationale": i.rationale, "confidence": i.confidence, "kind": i.kind, "target": i.target,
            "status": i.status, "decided_by": i.decided_by, "target_text": req.text if req else None,
            "target_source": req.source if req else None, "candidates": i.candidates}


def view(db: Session, s: ChangeSet) -> dict:
    items = _items(db, s.id)
    counts = {k: 0 for k in KINDS}
    for i in items:
        counts[i.kind or i.proposed_kind] += 1
    share = round((counts["modified"] + counts["removed"]) / s.baseline_count, 3) if s.baseline_count else 0.0
    try:
        pages = [{"page": p["page"], "width": p["width"], "height": p["height"]} for p in ingestion.layout(s.document_id)["pages"]]
    except LookupError:  # the layout file is gone (local store cleared): the set still shows its text
        pages = []
    return {"id": s.id, "opportunity_id": s.opportunity_id, "document_id": s.document_id, "filename": s.filename,
            "status": s.status, "created_by": s.created_by, "created_at": s.created_at, "applied_by": s.applied_by,
            "applied_at": s.applied_at, "baseline_from": s.baseline_from, "baseline_to": s.baseline_to,
            "counts": counts, "confirmed": sum(i.status == "confirmed" for i in items), "total": len(items),
            "share": share, "drastic": share > DRASTIC_SHARE, "pages": pages, "result": s.result,
            "items": [item_view(db, i) for i in items]}


def overview(db: Session, opp_id: str) -> dict:
    found = sets(db, opp_id)
    b = requirements.baseline(db, opp_id)
    return {"baseline": {"number": b.number, "count": b.count} if b else None, "drastic_threshold": DRASTIC_SHARE,
            "sets": [view(db, s) for s in found]}
