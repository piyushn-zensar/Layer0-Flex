"""RAG evaluation (P-39, C-29 point 8): runs data/golden/rag_eval.json against the knowledge base in a throwaway store.

    .venv\\Scripts\\python -m scripts.eval_rag                      # report on the console
    .venv\\Scripts\\python -m scripts.eval_rag --json               # the report as JSON (tests)
    .venv\\Scripts\\python -m scripts.eval_rag --report team/rag-eval-report.md

Measures: retrieval relevance (a passage of the expected source with the case's phrase in the top k), citation
support (every cited passage's words are on the cited page of its file), numerical values (an annotated value in the
top k), unknowns (nothing for an unrelated question; unresolved when no product evidence), isolation between bids,
and extraction coverage (the reader against its golden list, scripts/score_reader). Offline the ranking is keyword
only; with the embedding service the semantic ranking joins it. The set is a draft until someone who did not write it
has reviewed it (reviewed_by in the file).
"""
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

if __name__ == "__main__":
    os.environ["STORE_DIR"] = tempfile.mkdtemp(prefix="eval_rag-")  # before app.core.config reads it
    os.environ.setdefault("CATALOG_REFRESH_HOURS", "0")

from app.core import config  # noqa: E402

EVAL = config.DATA / "golden" / "rag_eval.json"
EVALUATOR = "RAG evaluation (not a review)"


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _supported(db, hit: dict) -> bool:
    """Where the cited passage's first words are on the cited page of the source's file (its rendering for non-PDF):
    "exact" (in order), "words" (all on the page, another order: table cells), "" (not found)."""
    import pymupdf

    from app.modules.knowledge import service as k
    from app.modules.knowledge.sources import FILES
    src = k.get(db, hit["ks_id"])
    path = Path(src.path) if src.path.endswith(".pdf") else FILES / f"{Path(src.path).stem}.rendered.pdf"
    with pymupdf.open(path) as pdf:
        page = " ".join(_words(pdf[hit["page"] - 1].get_text(sort=True)))  # the reading order the layout uses
    words = _words(hit["text"])[:8]
    if words and " ".join(words) in page:
        return "exact"
    # a table (ruled or not) is read cell by cell: its words are on the page, not always in running order
    return "words" if words and set(words) <= set(page.split()) else ""


def run() -> dict:
    from app.main import app  # noqa: F401  (creates the tables)
    from app.core.db import SessionLocal
    from app.modules.knowledge import service as k
    from app.modules.opportunities import service as opportunities

    spec = json.loads(EVAL.read_text("utf-8"))
    out = {"status": spec["status"], "reviewed_by": spec["reviewed_by"], "cases": [], "not_measured": spec["not_measured"],
           "ranking": "keyword and semantic" if config.LLM_PROVIDER == "azure" else "keyword only (no embedding service)"}
    add = lambda case, measure, ok, detail: out["cases"].append({"id": case, "measure": measure, "ok": bool(ok), "detail": detail})
    with SessionLocal() as db:
        k.register_references(db, EVALUATOR)
        titles = {}
        for s in k.sources(db):
            titles[s.title] = s.ks_id
            if s.collection == "engineering_reference" and s.status == "draft":
                k.review_source(db, s.ks_id, True, "evaluation run", EVALUATOR, "design_engineer")
        cited = []
        for c in spec["retrieval"]:
            hits = k.retrieve(db, c["task"], c["query"], None, c["k"])
            cited += [h for h in hits if h.get("page")]
            want = titles.get(c["source"])
            exists = any(c["contains"].lower() in p.text.lower() for p in k.source_passages(db, want)) if want else False
            ok = exists and any(h["ks_id"] == want and c["contains"].lower() in h["text"].lower() for h in hits)
            add(c["id"], "retrieval relevance", ok, f"{c['query']!r}: " + ("expected passage not in the source (invalid case)"
                if not exists else f"top {c['k']}: " + ", ".join(h["citation"] for h in hits)))
        support = [(h["citation"], _supported(db, h)) for h in cited]
        add("C-01", "citation support", all(ok for _, ok in support),
            f"{len(support)} cited passages: {sum(ok == 'exact' for _, ok in support)} found in order on their cited page, "
            f"{sum(ok == 'words' for _, ok in support)} with every word on the page in another order (table cells)"
            + "".join(f"; not found: {c}" for c, ok in support if not ok))
        for c in spec["numerical"]:
            hits = k.retrieve(db, "numerical_assessment", c["query"], None, c["k"])
            values = [a["value"] for h in hits for a in (h.get("annotations") or {}).get("attributes", [])]
            add(c["id"], "numerical values", any(c["value"] in v for v in values), f"{c['query']!r}: values {values[:8]}")
        u1 = next(c for c in spec["unknowns"] if c["id"] == "U-01")
        hits = k.retrieve(db, u1["task"], u1["query"])
        add("U-01", "unknowns", not hits, f"{u1['query']!r}: {len(hits)} hit(s)")
        opp_a = opportunities.create(db, "Evaluation bid A", "", "", EVALUATOR).id
        opp_b = opportunities.create(db, "Evaluation bid B", "", "", EVALUATOR).id
        note = Path(tempfile.mkdtemp()) / "site.md"
        note.write_text("# Site\nThe site busway must carry 4000 A.\n", "utf-8")
        ev, _ = k.register(db, note, EVALUATOR, "bid_evidence", "Bid A site notes", opp_id=opp_a)
        k.review_source(db, ev.ks_id, True, "evaluation run", EVALUATOR, "bid_manager")
        q = spec["isolation"][0]["query"]
        own = {h["ks_id"] for h in k.retrieve(db, "requirement_interpretation", q, opp_a)}
        other = {h["ks_id"] for h in k.retrieve(db, "requirement_interpretation", q, opp_b)}
        add("I-01", "isolation between bids", ev.ks_id in own and ev.ks_id not in other,
            f"bid A sees its evidence: {ev.ks_id in own}; bid B sees it: {ev.ks_id in other}")
    provider = config.LLM_PROVIDER
    from scripts import score_reader  # here: it switches the gateway to frozen answers only (mock)
    for c in spec["extraction"]:
        s = score_reader.score(str(config.ROOT / c["rfp"]))
        add(c["id"], "extraction coverage", s["recall"] >= c["min_recall"],
            f"recall {s['recall']} (min {c['min_recall']}), precision {s['precision']}, {s['reader_proposed']} proposed")
    config.LLM_PROVIDER = provider
    from app.core.db import SessionLocal as S2
    from scripts import seed_demo
    seed_demo.main()  # a bid with technical requirements and no reviewed product evidence
    with S2() as db:
        opp = max(o.id for o in opportunities.list_all(db))
        k.reassess(db, opp, "evaluation run", EVALUATOR)
        recs = [r for r in k.assessments(db, opp)["records"] if r.task == "product_matching"]
        ok = bool(recs) and all(any("product evidence" in u for u in r.unresolved) for r in recs)
        add("U-02", "unknowns", ok, f"{len(recs)} technical record(s), all marked 'no reviewed product evidence': {ok}")
    out["passed"] = sum(c["ok"] for c in out["cases"])
    out["total"] = len(out["cases"])
    return out


def markdown(r: dict) -> str:
    lines = ["# RAG evaluation report (P-39)", "",
             f"Evaluation set: data/golden/rag_eval.json, status **{r['status']}**, reviewed by: {r['reviewed_by'] or 'nobody yet'}.",
             f"Result: **{r['passed']} of {r['total']}** checks passed. Ranking: {r['ranking']}.", "",
             "| Case | Measure | Result | Detail |", "|---|---|---|---|"]
    lines += [f"| {c['id']} | {c['measure']} | {'pass' if c['ok'] else 'FAIL'} | {c['detail'].replace('|', '/')} |" for c in r["cases"]]
    lines += ["", "Not measured: " + "; ".join(r["not_measured"]), ""]
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--report")
    a = ap.parse_args()
    result = run()
    if a.report:
        Path(a.report).write_text(markdown(result), "utf-8")
    print(json.dumps(result, indent=1, default=str) if a.json else markdown(result))
    sys.exit(0 if result["passed"] == result["total"] else 1)
