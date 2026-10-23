"""Catalog: business units, products, past responses and the long-term retrieval (RAG) index.  Owner: Atharv.

Rules as data (rule R7): everything here is read from data/knowledge_base/*.json.

Public contract:
    units(include_pending=False) -> list[dict]
    unit(code) -> dict | None
    products(bu=None) -> list[dict]
    product(product_id) -> dict | None
    items(family=None) -> list[dict]            models/series of the families (catalog_items.json); not in the matcher prompt
    solution(bu, product_id) -> dict            {"unit", "area", "examples"}: the proposed solution as shown (C-40)
    past_responses() -> list[dict]              past answers of the active units (the matcher's fixed prompt part)
    learned() -> list[dict]                     knowledge approved by the curator in this installation (A-11)
    learn(entry)                                add an approved entry to the long-term index (knowledge module)
    search(query, k=5, bu=None) -> list[dict]   ranked products, past responses and catalog items (kind
                                                "catalog_item", with "family"), each with "score"
    search_many(queries, k=5) -> list[list[dict]]   search() for many queries at once (one embedding call)
    index_mode() -> str                         "embeddings" (semantic) or "keywords" (offline fallback)
    bom(product_id) -> list[dict]               BOM lines from the BOM source system (stub: catalog JSON)
    layers() -> dict                            grid-to-chip layers, scope keywords, unit tiers (spinco_layers.json)
    engineering_rules() -> dict                 rules R-001..R-004 and generic NEC/IEC values (engineering_rules.json)
    go_no_go() -> dict                          go/no-go criteria and placeholder thresholds (go_no_go.json)
    portfolio() -> dict                         standard product ratings and unit capacity (portfolio.json, placeholders)
    people() -> list[str]                       actors for the PoC user picker
    unit_of(actor) -> str | None                business-unit code of a product manager / design engineer
    power_modules() -> list[dict]               the spreadsheet parts merged into the catalog (P-53, power_modules.json)
    power_modules_import() -> str               its last import date
    documents() -> list[dict]                   the supplied product documents with family keys, parts, pages (J-21)
    product_rows(q, type, family, status, interface, application, sort, dir, page, size) -> dict
                                                all products as table rows, spreadsheet parts and web items (C-60)
    product_detail(key) -> dict | None          one product by part number or catalog ID, with variants, documents, images

Published catalog (P-34, C-28; scrape.py, re-exported): refresh(db, trigger) -> CatalogRefresh, published(db) -> dict,
    versions(db, key), refresh_forever() (the start-up and 24-hour job). It never changes the matcher's prompt.
"""
import json
from functools import lru_cache

from app.core import config
from app.core.vectors import Index
from app.modules.catalog.scrape import published, refresh, versions  # noqa: F401  (public contract)


@lru_cache
def _load(name: str) -> dict:
    return json.loads((config.KB / f"{name}.json").read_text("utf-8"))


def units(include_pending: bool = False) -> list[dict]:
    return [u for u in _load("business_units")["units"] if include_pending or u["status"] == "active"]


def unit(code: str) -> dict | None:
    return next((u for u in units(include_pending=True) if u["code"] == code), None)


def products(bu: str | None = None) -> list[dict]:
    active = {u["code"] for u in units()}
    return [p for p in _load("products")["products"] if p["bu"] in active and (bu is None or p["bu"] == bu)]


def past_responses() -> list[dict]:
    """Past RFP answers of the active units (long-term knowledge; evidence for matching and drafting)."""
    active = {u["code"] for u in units()}
    return [r for r in _load("past_responses")["responses"] if r["bu"] in active]


def product(product_id: str) -> dict | None:
    return next((p for p in _load("products")["products"] if p["id"] == product_id), None)


def items(family: str | None = None) -> list[dict]:
    active = {u["code"] for u in units()}
    return [i for i in _load("catalog_items")["items"] if i["bu"] in active and (family is None or i["family"] == family)]


def solution(bu: str, product_id: str | None) -> dict:
    """C-40: a unit's proposed solution, worded at solution level: the unit's name, the solution area (the product
    family's name) and up to three published models of the family as examples. A reference that is not a catalog
    family (a unit's own text) is the area as written; no reference: area None."""
    p = product(product_id) if product_id else None
    return {"unit": (unit(bu) or {}).get("name") or bu, "area": p["name"] if p else (product_id or None),
            "examples": [i["name"] for i in items(p["id"])][:3] if p else []}


def learned() -> list[dict]:
    """Approved reviewed examples, read from the knowledge module's database records (P-36; they replaced
    knowledge_learned.json). Empty before the tables exist (this module's self-check)."""
    from sqlalchemy.exc import OperationalError

    from app.core.db import SessionLocal
    from app.modules.knowledge import service as knowledge  # here, not at the top: knowledge imports this module
    try:
        with SessionLocal() as db:
            return knowledge.learned(db)
    except OperationalError:
        return []


def learn(entry: dict | None = None) -> None:
    """A reviewed example was approved: rebuild the search index from learned(). Approved knowledge joins the search
    index only, never past_responses(): the matcher's fixed prompt part stays the same, so its frozen answers stay valid."""
    _index.cache_clear()


@lru_cache
def _index() -> Index:
    """The long-term index: products, past responses and catalog items (the knowledge the system learns into, A-11).
    Semantic (embeddings, frozen in data/vector_cache) with a keyword fallback offline; see app/core/vectors.py."""
    docs = [{"kind": "product", "id": p["id"], "bu": p["bu"], "offering_type": p["offering_type"],
             "text": f"{p['name']}. {p['description']} {p['keywords']}"} for p in products()]
    docs += [{"kind": "past_response", "id": r["id"], "bu": r["bu"], "illustrative": True,  # sample format, never verified
              "text": f"{r['requirement']} {r['response']}"} for r in _load("past_responses")["responses"]]
    docs += [{"kind": "past_response", "id": r["id"], "bu": r["bu"], "learned": True,
              "text": f"{r['requirement']} {r['response']}"} for r in learned()]
    offering = {p["id"]: p["offering_type"] for p in products()}
    docs += [{"kind": "catalog_item", "id": i["id"], "bu": i["bu"], "family": i["family"],
              "offering_type": offering[i["family"]], "text": f"{i['name']} {i['model']} {i['specs']}"} for i in items()]
    return Index(docs)


def search(query: str, k: int = 5, bu: str | None = None) -> list[dict]:
    return _index().search(query, k, where=(lambda d: d["bu"] == bu) if bu else None)


def search_many(queries: list[str], k: int = 5) -> list[list[dict]]:
    return _index().search_many(queries, k)


def index_mode() -> str:
    return _index().mode


def bom(product_id: str) -> list[dict]:
    """ponytail: reads the catalog JSON; replace with the real BOM system connector (Needs confirmation which one)."""
    p = product(product_id)
    return p["bom"] if p else []


def layers() -> dict:
    return _load("spinco_layers")


def engineering_rules() -> dict:
    return _load("engineering_rules")


def portfolio() -> dict:
    """Standard product ratings and unit capacity for the go/no-go evidence (portfolio.json, PLACEHOLDERS, A-10)."""
    return _load("portfolio")


def go_no_go() -> dict:
    return _load("go_no_go")


def people() -> list[str]:
    return ["Bid Manager"] + [name for u in units() for name in (u["product_manager"], u["design_engineer"])]


def unit_of(actor: str) -> str | None:
    return next((u["code"] for u in units() if actor in (u["product_manager"], u["design_engineer"])), None)


ROW = ("key", "part_number", "family_key", "family", "series", "product_type", "status", "vin_min_v", "vin_max_v",
       "vout_min_v", "vout_max_v", "power_w", "current_a", "efficiency_pct", "interfaces", "source", "has_conflict")


def power_modules() -> list[dict]:
    """The Flex Power Modules spreadsheet merged into the catalog (P-53; scripts/import_power_modules.py)."""
    return _load("power_modules")["items"]


def documents() -> list[dict]:
    """The supplied product documents and the families / parts they apply to (data/axiom_products/documents.json)."""
    return _manifest("documents.json")


def power_modules_import() -> str:
    """The date of the last spreadsheet import that changed power_modules.json."""
    return _load("power_modules")["last_import"]


def _manifest(name: str) -> list[dict]:
    """Janvia's documents / images manifests (J-21, J-22); empty while a file is missing."""
    path = config.DATA / "axiom_products" / name
    return json.loads(path.read_text("utf-8")) if path.exists() else []


@lru_cache
def _catalog() -> tuple[dict, dict]:
    """key -> full entry, key -> table row: spreadsheet parts and every web catalog item (web_listing)."""
    names = {p["id"]: p["name"] for p in _load("products")["products"]}
    web = {i["id"]: i for i in _load("catalog_items")["items"]}
    full, rows = {}, {}
    for p in power_modules():
        w = web.get(p["family_key"] or "")
        full[p["part_number"]] = p | {"key": p["part_number"], "name": p["part_number"],
                                      "family": names.get(w["family"]) if w else p["product_line"],
                                      "source": "both" if p["web"] else "spreadsheet"}
    for i in web.values():
        full[i["id"]] = {"key": i["id"], "part_number": i["model"], "name": i["name"], "family_key": i["id"],
                         "family": names.get(i["family"]), "series": i["model"], "product_type": "web_listing",
                         "status": "Published", "interfaces": [], "application": [], "specs": i["specs"],
                         "source_url": i.get("source_url"), "bu": i["bu"], "conflicts": [], "source": "web"}
    for k, f in full.items():
        rows[k] = {c: f.get(c) for c in ROW} | {"has_conflict": bool(f["conflicts"])}
    return full, rows


def product_rows(q: str = "", type: str | None = None, family: str | None = None, status: str | None = None,
                 interface: str | None = None, application: str | None = None, sort: str = "part_number",
                 dir: str = "asc", page: int = 1, size: int = 50) -> dict:
    """All products as table rows (C-60): search, filters, sort (unknown values last either way), pages."""
    full, rows = _catalog()
    q = q.strip().lower()

    def keep(k: str) -> bool:
        f, r = full[k], rows[k]
        text = " ".join(str(x) for x in (r["part_number"], r["series"], r["family"], r["family_key"], f.get("name"))).lower()
        return ((not q or q in text) and (not type or r["product_type"] == type)
                and (not family or family in (r["family_key"], r["family"])) and (not status or r["status"] == status)
                and (not interface or interface in r["interfaces"]) and (not application or application in f["application"]))

    hits = [rows[k] for k in rows if keep(k)]
    if sort not in ROW:
        raise ValueError(f"cannot sort by {sort!r}")
    known = sorted((r for r in hits if r[sort] not in (None, [])), key=lambda r: (r[sort], r["key"]) if not isinstance(r[sort], list)
                   else (", ".join(r[sort]), r["key"]), reverse=dir == "desc")
    ordered = known + [r for r in hits if r[sort] in (None, [])]
    return {"total": len(hits), "page": page, "size": size, "items": ordered[(page - 1) * size: page * size]}


def product_detail(key: str) -> dict | None:
    """One product (part number or catalog ID) with its variants and the documents / images that apply (C-60, C-63)."""
    full, rows = _catalog()
    f = full.get(key)
    if f is None:
        return None
    if f["product_type"] == "web_listing":           # a web series: its spreadsheet parts
        variants = [rows[p["part_number"]] for p in power_modules() if p["family_key"] == key]
    elif f["product_type"] == "power_module":         # a part: the boards that evaluate its series
        variants = [rows[p["part_number"]] for p in power_modules() if f["series"] in p["evaluates"]]
    else:                                             # a board: the parts of the series it evaluates
        variants = [rows[p["part_number"]] for p in power_modules()
                    if p["product_type"] == "power_module" and p["series"] in f["evaluates"]]
    keys = ({f["family_key"]} | ({f["part_number"]} if f["product_type"] != "web_listing" else set())) - {None}

    def applies(m: dict) -> bool:
        return bool(keys & {*m.get("family_keys", []), m.get("family_key"), *m.get("part_numbers", [])})

    return f | {"variants": variants, "documents": [d for d in _manifest("documents.json") if applies(d)],
                "images": [i for i in _manifest("images.json") if applies(i)]}


if __name__ == "__main__":  # self-check: python -m app.modules.catalog.service
    def top(q: str) -> dict:
        return next(h for h in search(q, k=10) if h["kind"] == "product")

    # Syracuse demo items (data/seed) and spec lines: the product retrieval should rank first
    for q, want in [
        ("One (1) 15kV two (2) section Metal Clad Switchgear lineup.", "CROWN-ARMV"),
        ("Protective Relays and Controls.", "EP2-RPP"),
        ("Metal Clad Switchgear shall have eighteen (18) 15kV vacuum circuit breaker positions", "CROWN-ARMV"),
        ("Switchgear shall be Arc-resistant Type 2B", "CROWN-ARMV"),
        ("Separate utility incoming Cable termination compartment is required, that allows the utility to lock.", "CROWN-ACC"),
        ("Each phase shall have 1 inch diameter ground ball.", "CROWN-ACC"),
        ("The MANUFACTURER shall provide a NEMA four-hole pad and insulating boots", "CROWN-ACC"),
        ("Furnish two (2) bus Sections with tie breaker", "CROWN-ARMV"),
        ("Furnish relays, controls and associated accessories and hardware", "EP2-RPP"),
        ("The 13.2kV breakers shall be equipped with a SEL-751 (with touchscreen) overcurrent relay trip device.", "EP2-RPP"),
        ("Nominal voltage supplies: 125 volts DC for close and trip", "EP2-AUX"),
        # data/RFP/samples: data-centre wording
        ("Deployment preference: prefabricated / modular systems preferred to compress on-site schedule", "ANORD-POD"),
        ("Rack power: rack-mounted PDUs", "ANORD-PDU"),
        ("Branch circuits: twenty-four (24) 208V power whips", "ANORD-PDU"),
    ]:
        assert top(q)["id"] == want, (q, top(q)["id"], want)
    # unit only, where two products of the unit are both fair
    # by others: the documents give Syracuse to Crown (+ EP² relays only); scope is the matcher's call. The line does
    # not say arc-resistant, so Crown's non-arc metal-clad family (CROWN-MCSG) is as fair as CROWN-ARMV in keyword mode
    assert top("Metal Clad Switchgear shall be mounted within a fully enclosed Equipment Building (by others).")["bu"] == "CROWN"
    assert top("Rack density: minimum 120kW per rack, liquid cooling required at rack and chip level")["bu"] == "JETCOOL"
    assert top("Distribution: one dedicated power distribution cabinet")["bu"] == "ANORD"
    assert top("48 V DC rack power shelf with N+1 power supply units")["bu"] == "FPM"
    assert unit_of("EP² Design Engineer") == "EP2"
    hit = next(h for h in search("BMR491 quarter brick 1,300 W", k=10) if h["kind"] == "catalog_item")
    assert hit["family"] == "FPM-DCDC" and all(i["family"] == "FPM-DCDC" for i in items("FPM-DCDC"))
    print("catalog ok")


def refresh_forever() -> None:
    """The scheduled job (P-34): refresh now (server start), then every CATALOG_REFRESH_HOURS, in a background thread.
    A failed run is recorded on the run and the last good catalog stays."""
    import time

    from app.core.db import SessionLocal
    trigger = "start"
    import logging
    while True:
        try:
            with SessionLocal() as db:
                refresh(db, trigger)
        except Exception:  # noqa: BLE001 - one failed run never stops the 24-hour schedule (19 Oct review)
            logging.getLogger(__name__).exception("catalog refresh failed; the last good catalog stays")
        trigger = "schedule"
        time.sleep(config.CATALOG_REFRESH_HOURS * 3600)
