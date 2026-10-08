"""Load the Syracuse demo opportunity through the real module services.

    .venv\\Scripts\\python -m scripts.seed_demo          # adds the demo opportunity
    .venv\\Scripts\\python -m scripts.seed_demo --reset  # deletes the local DB first

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


def main() -> None:
    seed = json.loads((config.SEED / "demo_syracuse.json").read_text("utf-8"))
    with SessionLocal() as db:
        o = seed["opportunity"]
        opp = opportunities.create(db, o["title"], o["customer"], o["customer_type"], BM)
        doc = opportunities.add_document(db, opp.id, "RFP-2023-20-Switchgear-Procurement-Final.pdf",
                                         (config.ROOT / seed["document"]).read_bytes(), "main", BM)
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
        print(f"done: open http://127.0.0.1:8000/opportunities/{opp.id}/trace")


if __name__ == "__main__":
    main()
