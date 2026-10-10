"""Load the demo opportunities through the real module services.

    .venv\\Scripts\\python -m scripts.seed_demo          # Syracuse from the REAL extraction (P-08), then the hyperscale sample
    .venv\\Scripts\\python -m scripts.seed_demo --reset  # deletes the local DB first
main() alone (as the tests call it) seeds only Syracuse, with its 13 hand-picked line items (quick and stable).

The real Syracuse demo runs the reader agent and the grouping agent from their frozen answers (no model call, no
API key): about 810 line items become about 350 requirements. Every requirement is approved and frozen, matched, the
bid decision is recorded, the work is dispatched, and the sample answers from the seed file are attached to the
real requirements that cover the same RFP lines. Every step calls the same service a user action would call,
so the seed doubles as an end-to-end check.
"""
import json
import sys

from app.core import config

if "--reset" in sys.argv:
    (config.STORE / "layer0.db").unlink(missing_ok=True)

from app.main import app  # noqa: E402,F401  (imports every module and creates tables)
from app.core.db import SessionLocal  # noqa: E402
from app.modules.decisions import service as decisions  # noqa: E402
from app.modules.ingestion import service as ingestion  # noqa: E402
from app.modules.matching import service as matching  # noqa: E402
from app.modules.opportunities import service as opportunities  # noqa: E402
from app.modules.requirements import anchoring  # noqa: E402  (a pure helper: quote -> lines on the page)
from app.modules.requirements import service as requirements  # noqa: E402
from app.modules.workpackages import service as workpackages  # noqa: E402

BM = "Bid Manager"


def main(seed_file: str = "demo_syracuse.json", real: bool = False) -> None:
    seed = json.loads((config.SEED / seed_file).read_text("utf-8"))
    with SessionLocal() as db:
        o = seed["opportunity"]
        opp = opportunities.create(db, o["title"], o["customer"], o["customer_type"], BM)
        pdf = config.ROOT / seed["document"]
        doc = opportunities.add_document(db, opp.id, pdf.name, pdf.read_bytes(), "main", BM)
        print("ingested:", ingestion.ingest(db, doc.id))

        if real:
            responses = _read_and_review(db, opp.id, doc.id, seed)
        else:
            responses = {}
            for item in seed["requirements"]:
                req = requirements.add(db, opp.id, doc.id, item["quote"], item["text"], item["category"],
                                       "reader agent (seed)", item["section"], item["page"])
                requirements.review(db, req.req_id, "approve", BM)
                if "response" in item:
                    responses[req.req_id] = item["response"]
                print(f"  {req.req_id} {req.provenance:10} {req.source}")
        requirements.freeze(db, opp.id, BM)

        print("matching:", matching.match(db, opp.id, "matching agent (seed)"))
        units = list(matching.suggested_units(db, opp.id))
        decisions.record(db, opp.id, "participation", "units", units, "Suggested by matching; confirmed.", BM)
        decisions.record(db, opp.id, "go_no_go", "go", units, "In scope for the participating units.", BM)
        print("dispatched:", workpackages.dispatch(db, opp.id, BM))

        for req_id, items in workpackages.by_requirement(db, opp.id).items():
            r = responses.get(req_id)
            for a in items if r else []:
                workpackages.respond(db, a.id, r["compliance"], None, r["response"], a.owner)
                if r["validated"]:
                    workpackages.validate(db, a.id, True, "", BM)
        print(f"done: open http://localhost:3000/opportunities/{opp.id}/trace (web) - API on :8000")


def _read_and_review(db, opp_id: str, doc_id: str, seed: dict) -> dict:
    """Reader + grouping from frozen answers, every requirement approved. Returns {req_id: sample response}."""
    result = requirements.extract(db, opp_id, BM)
    print("read:", {k: v for k, v in result.items() if k != "problems"}, "problems:", len(result["problems"]))
    reqs = requirements.current(db, opp_id)
    for r in reqs:
        requirements.review(db, r.req_id, "approve", BM)
    print(f"approved: {len(reqs)} requirements")
    # attach each sample answer to the real requirement that covers the same lines (first one wins)
    pages = ingestion.layout(doc_id)["pages"]
    responses = {}
    for item in seed["requirements"]:
        if "response" not in item:
            continue
        hit = anchoring.find(item["quote"], pages, item["page"])
        req = next((r for r in reqs if hit and r.page == hit["page"] and r.line_start is not None
                    and r.line_start <= hit["line_end"] and hit["line_start"] <= r.line_end), None)
        if req and req.req_id not in responses:
            responses[req.req_id] = item["response"]
    print(f"sample answers attached to {len(responses)} requirements")
    return responses


if __name__ == "__main__":
    main(real=True)  # P-08: the demo runs on the real extraction
    main("demo_hyperscale.json")  # A-08: multi-unit sample, added by Atharv ([contract] Piyush)
