"""Spec tables from the supplied product documents and the official product pages (23 Oct 2026, C-52 follow-up).

    LLM_PROVIDER=azure .venv/Scripts/python -m scripts.extract_product_specs     # first run: live model, answers frozen
    .venv/Scripts/python -m scripts.extract_product_specs                        # later runs replay the frozen answers

Reads data/axiom_products/documents.json (the supplied PDFs and the pages per family, J-21) and, when present,
data/axiom_products/web/web_sources.json (official pages and datasheets fetched for the PoC). For each family and
each chunk of its pages, the spec-table agent (catalog/agent.py) returns ratings with page, quote and conditions;
this script keeps a value only when its quote is on the cited page and its number is in that quote (the model never
converts or derives), converts the unit
to the attribute's base unit, and writes data/knowledge_base/product_specs.json. Every value is unverified until the
unit reviews it (catalog.review_specs). Re-running gives the same file.
"""
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import pymupdf

from app.core import config
from app.modules.catalog import agent

ROOT = config.ROOT
FOLDER = config.DATA / "axiom_products"
OUT = config.KB / "product_specs.json"
CHUNK_PAGES, CHUNK_CHARS = 4, 14000

from app.modules.catalog.units import convert  # noqa: E402  (shared with the configurator's range search)


def _digits(s: str) -> str:
    return re.sub(r"[^\d]", "", s)


def _on_page(quote: str, page: str) -> bool:
    """The quote's words are the page's own: at least 85 % of them occur on the page (a table row's cells may be read
    in another order than the model quotes them)."""
    words = re.findall(r"[a-z0-9]+", quote.lower())
    seen = set(re.findall(r"[a-z0-9]+", page.lower()))
    return bool(words) and sum(w in seen for w in words) >= 0.85 * len(words)


def _num(v: float) -> str:
    return f"{v:g}"


def pdf_pages(path: Path, pages: list[int] | None) -> dict[int, str]:
    doc = pymupdf.open(path)
    out = {}
    for n in pages or range(1, doc.page_count + 1):
        if 1 <= n <= doc.page_count:
            page = doc[n - 1]
            tables = "\n".join(t.to_markdown() for t in page.find_tables().tables)
            out[n] = page.get_text() + ("\nTables:\n" + tables if tables else "")
    return out


def html_pages(path: Path) -> dict[int, str]:
    from app.modules.knowledge import sources   # the knowledge reader renders a web page the same way as a source
    model, _ = sources.read(path, path.stem)
    return {p["page"]: "\n".join(line["text"] for line in p["lines"]) for p in model["pages"]}


def chunks(texts: dict[int, str], per: int = CHUNK_PAGES) -> list[list[int]]:
    out, cur, size = [], [], 0
    for n, t in sorted(texts.items()):
        if cur and (len(cur) == per or size + len(t) > CHUNK_CHARS):
            out.append(cur)
            cur, size = [], 0
        cur.append(n)
        size += len(t)
    return out + ([cur] if cur else [])


def jobs() -> list[dict]:
    """(source, family, its pages' text) for every family a document or a fetched page is tagged to."""
    names = {i["id"]: i["name"] for i in json.loads((config.KB / "catalog_items.json").read_text("utf-8"))["items"]}
    # families the Power Modules spreadsheet already rates part by part: brochure rows would only add weaker copies
    sheet = {p["family_key"] for p in json.loads((config.KB / "power_modules.json").read_text("utf-8"))["items"]}
    out = []
    for d in json.loads((FOLDER / "documents.json").read_text("utf-8")):
        texts = pdf_pages(FOLDER / d["file"], None)
        for key in [k for k in d["family_keys"] if k not in sheet]:
            pages = d["pages"].get(key) or sorted(texts)
            out.append({"file": d["file"], "url": None, "title": d["title"], "family_key": key,
                        "family": f"{key} ({names.get(key, key)})", "texts": {n: texts[n] for n in pages if n in texts},
                        "per": 1 if d["doc_type"] in ("datasheet", "one_pager") else CHUNK_PAGES})  # dense tables: a page a call
    web = FOLDER / "web" / "web_sources.json"
    for w in json.loads(web.read_text("utf-8")) if web.exists() else []:
        if not w.get("file") or not w.get("has_ratings") or w.get("duplicate_of"):
            continue
        path = FOLDER / w["file"]
        texts = pdf_pages(path, None) if path.suffix.lower() == ".pdf" else html_pages(path)
        for key in [k for k in w["family_keys"] if k not in sheet]:
            out.append({"file": w["file"], "url": w["url"], "title": w["title"], "family_key": key,
                        "family": f"{key} ({names.get(key, key)})", "texts": texts})
    return out


def run_job(job: dict) -> tuple[list[dict], list[dict]]:
    items, issues = [], []
    for pages in chunks(job["texts"], job.get("per", CHUNK_PAGES)):
        text = "\n\n".join(f"=== page {n} ===\n{job['texts'][n]}" for n in pages)
        answer = agent.extract(job["family"], job["title"], text)
        for it in answer["items"]:
            attrs = []
            for a in it["attributes"]:
                where = {"file": job["file"], "page": a["page"], "url": job["url"]}
                page_text = job["texts"].get(a["page"])
                kind, base = agent.ATTRIBUTES[a["name"]]
                if page_text is None or a["page"] not in pages:
                    issues.append({"family_key": job["family_key"], **where, "attribute": a["label"], "why": "page not in the chunk"})
                    continue
                if not _on_page(a["quote"], page_text):                # the quote must be the page's own words
                    issues.append({"family_key": job["family_key"], **where, "attribute": a["label"],
                                   "why": "quote not found on the page"})
                    continue
                if kind == "range":
                    unit = a["unit"] or (re.findall(r"[\[(]\s*([^\])\s]+)\s*[\])]", a["label"]) or [""])[-1]
                    a = a | {"unit": unit}                              # "Rated current In [A]": the unit is in the label
                    nums = [v for v in (a["min"], a["max"]) if v is not None]
                    missing = [v for v in nums if _digits(_num(v)) not in _digits(a["quote"])]   # in the quoted words
                    if missing or not nums:
                        issues.append({"family_key": job["family_key"], **where, "attribute": a["label"],
                                       "why": f"{', '.join(map(_num, missing))} not in the quote" if missing else "no number"})
                        continue
                    lo, why = convert(a["min"], a["unit"], base)
                    hi, why2 = convert(a["max"], a["unit"], base)
                    if why or why2:
                        issues.append({"family_key": job["family_key"], **where, "attribute": a["label"], "why": why or why2})
                        continue
                    a = a | {"min_base": lo, "max_base": hi, "base_unit": base}
                attrs.append(a | {"source": where})
            if attrs:
                items.append({"family_key": job["family_key"], "variant": it["variant"], "attributes": attrs,
                              "source_file": job["file"], "url": job["url"]})
    return items, issues


def main() -> dict:
    todo = jobs()
    with ThreadPoolExecutor(4) as pool:   # model calls in parallel; results kept in job order
        results = list(pool.map(run_job, todo))
    items = [i for its, _ in results for i in its]
    issues = [x for _, xs in results for x in xs]
    for it in items:   # a stable id: a re-run or a new source never moves a unit's review to another item
        key = json.dumps([it["family_key"], it["variant"], it["source_file"], [x["page"] for x in it["attributes"]]])
        it["spec_id"] = "SPEC-" + hashlib.sha1(key.encode()).hexdigest()[:10]
        it["verified"] = False
    old = json.loads(OUT.read_text("utf-8")) if OUT.exists() else {}
    out = {"_note": "Ratings read from the supplied product documents and the official product pages by "
                    "scripts/extract_product_specs.py (model-assisted, frozen answers; a value is kept only when its "
                    "quote is on the cited page and its number is in the quote; units converted by code to base_unit). Unverified until the unit "
                    "reviews it. Brochure values are ranges per family or variant, not orderable part numbers.",
           "extracted": old.get("extracted") if old.get("items") == items else date.today().isoformat(),
           "items": items, "dropped": issues}
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", "utf-8")
    fams = sorted({i["family_key"] for i in items})
    print(f"{len(items)} spec items, {sum(len(i['attributes']) for i in items)} values for {len(fams)} families; "
          f"{len(issues)} values dropped -> {OUT.relative_to(ROOT)}")
    return out


if __name__ == "__main__":
    main()
