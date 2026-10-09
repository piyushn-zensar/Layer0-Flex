"""Load the Syracuse demo opportunity (and the multi-unit hyperscale sample) through the real module services.

    .venv\\Scripts\\python -m scripts.seed_demo          # adds OPP Syracuse, then the hyperscale sample (A-08)
    .venv\\Scripts\\python -m scripts.seed_demo --reset  # deletes the local DB first
main() alone (as the tests call it) seeds only Syracuse.

Every step calls the same service a user action would call, so the seed doubles as an end-to-end check.
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
from app.modules.requirements import service as requirements  # noqa: E402
from app.modules.workpackages import service as workpackages  # noqa: E402

BM = "Bid Manager"


def main(seed_file: str = "demo_syracuse.json") -> None:
    seed = json.loads((config.SEED / seed_file).read_text("utf-8"))
    with SessionLocal() as db:
        o = seed["opportunity"]
        opp = opportunities.create(db, o["title"], o["customer"], o["customer_type"], BM)
        pdf = config.ROOT / seed["document"]
        doc = opportunities.add_document(db, opp.id, pdf.name, pdf.read_bytes(), "main", BM)
        print("ingested:", ingestion.ingest(db, doc.id))

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


if __name__ == "__main__":
    main()
    main("demo_hyperscale.json")  # A-08: multi-unit sample, added by Atharv ([contract] Piyush)
