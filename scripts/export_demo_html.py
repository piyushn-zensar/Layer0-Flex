"""P-51: record one bid from the real API and write the static, offline demo page demo/layer0-demo.html.

Runs the FastAPI app in-process (TestClient), signs in as every roster account (data/accounts.json, DEMO_PASSWORD from .env),
GETs every endpoint the demo screens read, embeds the RFP page images as JPEG data URIs and the web app's own CSS, and fills
demo/template.html. Any endpoint error stops the export. No model calls: LLM_PROVIDER is forced to mock.

  .venv\\Scripts\\python -m scripts.export_demo_html --bid OPP-0003                     # the demo database (data/store): RC-1
  .venv\\Scripts\\python -m scripts.export_demo_html --bid OPP-0001 --store C:\\tmp\\copy  # a throwaway copy (accounts in its SQLite)

The store can also come from DEMO_STORE. A store other than data/store keeps its sign-in accounts in its own SQLite file
(MYSQL_HOST cleared), so a development copy never touches the MySQL accounts.
Note: importing app.main runs db.init_db() and auth.init() (create missing tables, add missing roster accounts) on that store.
"""
import argparse
import base64
import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_QUERY = "what short-circuit rating is required?"  # the RFP step's search placeholder
CSS = ["globals.css", "styles/overview.css", "styles/requirements.css", "styles/trace.css", "styles/workspace.css", "styles/consolidation.css"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bid", required=True, help="bid id, e.g. OPP-0003 (RC-1)")
    ap.add_argument("--store", default=os.getenv("DEMO_STORE") or str(ROOT / "data" / "store"), help="store directory (layer0.db, pages/, layouts/)")
    ap.add_argument("--out", default=str(ROOT / "demo" / "layer0-demo.html"))
    ap.add_argument("--template", default=str(ROOT / "demo" / "template.html"))
    ap.add_argument("--width", type=int, default=1000, help="page image width in px")
    ap.add_argument("--quality", type=int, default=70, help="JPEG quality")
    a = ap.parse_args()

    store = Path(a.store).resolve()
    local_auth = store != (ROOT / "data" / "store").resolve()
    # config reads the environment on import and load_dotenv never overrides it: set everything before any app import
    os.environ.update(STORE_DIR=str(store), LLM_PROVIDER="mock", MODEL_PROVIDER="mock", CATALOG_REFRESH_HOURS="0")
    if local_auth:
        os.environ["MYSQL_HOST"] = ""
        for k in ("AUTH_DATABASE_URL", "DATABASE_URL"):
            os.environ.pop(k, None)
    sys.path.insert(0, str(ROOT))
    from fastapi.testclient import TestClient
    from app.core import config
    from app.main import app
    assert config.LLM_PROVIDER == "mock", config.LLM_PROVIDER
    print(f"store {store} (accounts: {'local SQLite' if local_auth else 'configured auth database'})")

    data = record(TestClient, app, config, a)
    page = Path(a.template).read_text("utf-8")
    css = "\n".join(f"/* ---- web/app/{n} ---- */\n" + (ROOT / "web" / "app" / n).read_text("utf-8") for n in CSS)
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").replace("<!--", "<\\!--")
    for mark in ("/*__APP_CSS__*/", "__DEMO_DATA__"):
        if page.count(mark) != 1:
            raise SystemExit(f"template: expected one {mark}")
    page = page.replace("/*__APP_CSS__*/", css).replace("__DEMO_DATA__", blob)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, "utf-8")
    mb = out.stat().st_size / 1e6
    print(f"wrote {out} ({mb:.1f} MB)")
    if mb > 15:
        raise SystemExit("output over 15 MB: lower --width or --quality")


def record(TestClient, app, config, a) -> dict:
    accounts = [x for x in json.loads((config.DATA / "accounts.json").read_text("utf-8")) if x["role"] != "admin"]
    oid = a.bid
    t0 = time.time()
    with TestClient(app) as c:
        tokens: dict[str, dict] = {}

        def ok(r):
            if r.status_code >= 400:
                raise SystemExit(f"{r.request.method} {r.request.url.path}?{r.request.url.query} -> {r.status_code}: {r.text[:400]}")
            return r.json() if r.headers.get("content-type", "").startswith("application/json") else r.content

        def as_(u: str) -> dict:
            if u not in tokens:
                tok = ok(c.post("/api/auth/login", json={"username": u, "password": config.DEMO_PASSWORD}))["token"]
                tokens[u] = {"Authorization": f"Bearer {tok}"}
            return tokens[u]

        bm = as_("bid.manager")
        get = lambda path, who=bm: ok(c.get(path, headers=who))  # noqa: E731
        B = f"/api/bids/{oid}"

        detail = get(B)
        bid = {k: get(f"{B}/{p}") for k, p in {
            "extraction": "extraction", "requirements": "requirements", "exceptions": "requirements/exceptions",
            "knowledge": "knowledge", "decisions": "decisions", "assessment": "assessment", "assessment_score": "assessment-score",
            "schedule": "schedule", "matrix": "compliance-matrix", "outline": "response-outline",
            "changes": "changes", "comments": "comments", "needs_owner": "needs-owner", "assessments": "assessments",
            "components": "components"}.items()}  # P-57: Technical Requirement Matching
        bid["detail"] = detail
        bid["search"] = {"q": SAMPLE_QUERY, **get(f"{B}/rfp-search?k=8&q={SAMPLE_QUERY}")}  # one recorded RFP search
        events, before = [], None  # activity: every page, newest first
        while True:
            act = get(f"{B}/activity?limit=200" + (f"&before={before}" if before else ""))
            events += act["events"]
            before = act.get("next_before")
            if not before:
                break
        bid["activity"] = {"events": events, "total": act["total"], "filters": act["filters"]}
        bid["snapshots"] = {s["number"]: get(f"{B}/extraction/{s['number']}") for s in bid["extraction"]}

        trace = get(f"{B}/trace")
        units = sorted(set(trace["progress"]) | {"BID"})
        can_change, inbox, may, kb_review, me = {}, {}, {}, {}, {}
        for acct in accounts:
            u = acct["username"]
            h = as_(u)
            me[u] = get("/api/auth/me", h)
            rows = get(f"{B}/trace", h)["rows"]
            can_change[u] = [r["req"]["req_id"] for r in rows if r.get("can_change")]
            kb_review[u] = get("/api/knowledge?status=queued&reviewable=true", h)
            # My work: the bid manager may act in every unit's package (commercial validation, return with a question)
            for bu in (units if acct["role"] == "bid_manager" else [acct["bu"]] if acct["bu"] in units else []):
                box = get(f"/api/inbox/{bu}", h)
                items = [i for i in box["items"] if i["opportunity_id"] == oid]
                may.setdefault(u, {})[bu] = {str(i["id"]): "".join(f for f, k in (("a", "answer"), ("v", "validate"), ("r", "return")) if i["may"].get(k)) for i in items}
                if bu not in inbox:
                    inbox[bu] = {**box, "items": [{k: v for k, v in i.items() if k != "may"} for i in items]}
        asg_ids = sorted({x["id"] for r in trace["rows"] for x in r["assignments"]})
        check(trace, bid["schedule"])
        asg_history = {str(i): get(f"/api/assignments/{i}/history") for i in asg_ids}
        req_history = {r["req_id"]: get(f"/api/requirements/{r['req_id']}/history") for r in bid["requirements"]["requirements"]}

        images = {}
        for d in detail["documents"]:
            for n in range(1, (d.get("page_count") or 0) + 1):
                images[f"{d['id']}/{n}"] = jpeg(get(f"/api/documents/{d['id']}/pages/{n}.png"), a.width, a.quality)

        portfolio = [p for p in get("/api/portfolio") if p["opp"]["id"] == oid]
        glob = {"portfolio": portfolio, "catalog": get("/api/catalog?q="), "published": get("/api/catalog/published"),
                "sources": get("/api/knowledge/sources"), "people": get("/api/people"), "unit_names": get("/api/auth/units"),
                "samples": get("/api/samples")}  # saved Traceability views of a bundled sample RFP (RFP step "Focus")
    print(f"recorded {oid} in {time.time() - t0:.0f} s: {len(trace['rows'])} trace rows, {len(asg_ids)} assignments, "
          f"{len(events)} events, {len(images)} page images, {len(accounts)} accounts")
    return {"meta": {"bid": oid, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
            "accounts": [{**x, "me": me[x["username"]]} for x in accounts], **glob, "bid": bid, "trace": trace,
            "can_change": can_change, "inbox": inbox, "may": may, "kb_review": kb_review,
            "asg_history": asg_history, "req_history": req_history, "images": images}


def check(trace: dict, schedule: dict) -> None:
    """Stop on a store where the workflow was not run (scripts/run_demo_workflow.py): identical stub answers, no unit estimates."""
    answers = [x.get("response") for r in trace["rows"] for x in r["assignments"] if x.get("response")]
    if answers and (len(set(answers)) == 1 or "Demo answer." in answers):
        raise SystemExit(f"store has placeholder unit answers ({len(answers)} x {answers[0]!r}): run scripts/run_demo_workflow.py first")
    if not any(u.get("estimated_completion") for u in schedule.get("units", [])):
        raise SystemExit("schedule has no unit estimates: run scripts/run_demo_workflow.py first")


def jpeg(png: bytes, width: int, quality: int) -> str:
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    if im.width > width:  # highlight boxes are percentages of the page, so resizing never moves them
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


if __name__ == "__main__":
    main()
