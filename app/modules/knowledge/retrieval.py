"""Task-specific retrieval and explainable assessment records (P-37 part 1, C-29 points 5 and 7). Re-exported by
knowledge/service.py.

retrieve(db, task, query, opp_id) draws only from the collections of the task's profile (retrieval.json), only from
published sources and approved, non-illustrative reviewed examples (sources.evidence), and current bid evidence only
for its own bid (the bid's registered sources and its main RFP's passages). Each source has its own index, so a new
source never re-embeds the others; semantic and keyword results are fused (core/vectors.Index.hybrid).

reassess(db, opp_id, reason, actor) is an explicit, numbered run: one append-only record per register requirement
with the evidence cited, every source version, the catalog version and the profile it ran with, and what is
unresolved (for example no reviewed product evidence). It never calls a model and never changes a requirement; the
model-written conclusions come with the cited prompts (P-37 part 2).
"""
import hashlib
import json
from functools import lru_cache

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import audit, config
from app.core.vectors import Index
from app.modules.catalog import service as catalog
from app.modules.ingestion import service as ingestion
from app.modules.knowledge.models import AssessmentRecord
from app.modules.knowledge.sources import evidence
from app.modules.matching import service as matching
from app.modules.opportunities import service as opportunities
from app.modules.requirements import service as requirements

_indexes: dict[tuple, Index] = {}  # (source id, version, passages) -> its index; versions never change their text


@lru_cache
def profiles() -> dict:
    data = json.loads((config.KB / "retrieval.json").read_text("utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def profile_hash(task: str) -> str:
    return hashlib.sha256(json.dumps(profiles()[task], sort_keys=True).encode()).hexdigest()[:12]


def _citation(e: dict) -> str:
    where = f", p. {e['page']}, lines {e['line_start']}-{e['line_end']}" if e.get("page") else ""
    return f"{e['ks_id']} v{e['version']}{where}"


def _index(key: tuple, items: list[dict], embed: bool = True) -> Index:
    if key not in _indexes:
        _indexes[key] = Index(items, embed=embed)
    return _indexes[key]


def retrieve(db: Session, task: str, query: str, opp_id: str | None = None, k: int | None = None) -> list[dict]:
    """The evidence for one task and question, best first, each with its citation. ValueError: unknown task.
    One keyword ranking over every eligible passage, one semantic ranking from each source's own frozen vectors
    (cosine scores compare across sources), fused by reciprocal rank (score orders results; it is no probability)."""
    if task not in profiles():
        raise ValueError(f"Unknown task {task!r}; one of {', '.join(profiles())}.")
    prof = profiles()[task]
    k, depth = k or prof["k"], 50
    items = [e for e in evidence(db, prof["collections"], opp_id)
             if not prof.get("values_only") or (e.get("annotations") or {}).get("attributes")]
    rfp = None
    if "bid_evidence" in prof["collections"] and opp_id:
        doc = opportunities.main_document(db, opp_id)
        if doc is not None and doc.status == "ingested":
            rfp = (doc, ingestion.rfp_index(doc.id))
            items += [p | {"ks_id": doc.id, "version": 1, "collection": "bid_evidence", "title": doc.filename,
                           "passage_id": None, "heading": "", "table": None, "annotations": None} for p in rfp[1].items]
    if not items or not query.strip():
        return []
    where = {(e["ks_id"], e.get("page"), e.get("line_start"), e.get("passage_id")): i for i, e in enumerate(items)}
    pos = lambda e: where[(e["ks_id"], e.get("page"), e.get("line_start"), e.get("passage_id"))]
    rankings = [_index(("keywords", tuple(where)), items, embed=False).hybrid(query, depth)]
    semantic, complete = [], True
    groups: dict[tuple, list[dict]] = {}
    for e in items:
        if e["collection"] != "bid_evidence" or e.get("passage_id"):
            groups.setdefault((e["ks_id"], e["version"]), []).append(e)
    for (ks, version), group in groups.items():
        idx = _index((ks, version, len(group)), group)
        complete = complete and idx.vectors is not None
        semantic += idx.search(query, depth) if idx.vectors is not None else []
    if rfp:
        complete = complete and rfp[1].vectors is not None
        semantic += [p | {"ks_id": rfp[0].id, "passage_id": None} for p in rfp[1].search(query, depth)] if rfp[1].vectors is not None else []
    # semantic ranking only when every candidate has vectors: otherwise the embedded ones would be favoured
    if complete and semantic:
        rankings.append(sorted(semantic, key=lambda h: -h["score"])[:depth])
    fused: dict[int, float] = {}
    for ranked in rankings:
        for rank, hit in enumerate(ranked):
            fused[pos(hit)] = fused.get(pos(hit), 0.0) + 1.0 / (60 + rank)
    best = sorted(fused, key=lambda i: (-fused[i], i))[:k]
    return [items[i] | {"score": round(fused[i], 4), "citation": _citation(items[i])} for i in best]


def reassess(db: Session, opp_id: str, reason: str, actor: str) -> dict:
    """A new, numbered assessment run over the bid's register (see the module note). ValueError without a reason."""
    opportunities.require(db, opp_id)
    if not reason.strip():
        raise ValueError("Say why the bid is assessed again (for example: new reviewed evidence).")
    run = (db.scalar(select(func.max(AssessmentRecord.run)).where(AssessmentRecord.opportunity_id == opp_id)) or 0) + 1
    version = catalog.published(db)["catalog_version"]
    missing = 0
    reqs = requirements.current(db, opp_id)
    for req in reqs:
        task = "product_matching" if req.category in matching.PRODUCT_CATEGORIES else "requirement_interpretation"
        hits = retrieve(db, task, req.text, opp_id)
        unresolved = []
        if task == "product_matching" and not any(h["collection"] == "product_evidence" for h in hits):
            unresolved.append("No reviewed product evidence for this requirement.")
            missing += 1
        if not hits:
            unresolved.append("No published evidence found.")
        db.add(AssessmentRecord(
            opportunity_id=opp_id, run=run, reason=reason.strip(), task=task, subject=req.req_id, query=req.text,
            citations=[{"citation": h["citation"], "ks_id": h["ks_id"], "version": h["version"], "collection": h["collection"],
                        "passage_id": h.get("passage_id"), "page": h.get("page"), "line_start": h.get("line_start"),
                        "line_end": h.get("line_end"), "score": h["score"]} for h in hits],
            evidence_versions={h["ks_id"]: h["version"] for h in hits}, catalog_version=version,
            model="retrieval only", prompt_hash=profile_hash(task), conclusion=None, unresolved=unresolved,
            created_by=actor))
    audit.record(db, actor, "reassessed", "assessment", str(run), opp_id, reason=reason.strip(), records=len(reqs),
                 without_product_evidence=missing)
    db.commit()
    return {"run": run, "records": len(reqs), "without_product_evidence": missing, "catalog_version": version}


def assessments(db: Session, opp_id: str, run: int | None = None, subject: str | None = None) -> dict:
    """The records of one run (default: the latest), and the run numbers that exist."""
    runs = list(db.scalars(select(AssessmentRecord.run).where(AssessmentRecord.opportunity_id == opp_id)
                           .distinct().order_by(AssessmentRecord.run)))
    run = run or (runs[-1] if runs else None)
    q = select(AssessmentRecord).where(AssessmentRecord.opportunity_id == opp_id, AssessmentRecord.run == run)
    if subject:
        q = q.where(AssessmentRecord.subject == subject)
    return {"runs": runs, "run": run, "records": list(db.scalars(q.order_by(AssessmentRecord.id)))}
