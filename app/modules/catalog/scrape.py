"""Published catalog (C-28, P-34): read the official Flex product pages, store what they publish with its source and
time, keep every version of a product's name and features, and refresh on server start and every 24 hours.
Re-exported by catalog/service.py.

What this is: evidence that a product exists and what is published about it (name, category, key features, link).
It is not compliance evidence (C-29 point 3), and it does not change the matcher's prompt (the curated catalog files
do), so frozen matcher answers stay valid.

Pages (decided 15 Oct 2026): flex.com/products and the official pages it links to for the units in scope. Flex
pages publish each product as an <h3> with its key features and a "View ..." link; the unit sites are read for
their product links only (ep2.com and jetcool.com publish no /products/ links: their products come from the
flex.com pages; a page-specific reader is the upgrade). Each site's robots.txt is honoured on every run. A page that fails keeps its last good
records; a product missing from a page that was read is marked inactive (its versions stay).
"""
import hashlib
import ssl
import threading
import urllib.robotparser
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import audit
from app.core.db import utcnow
from app.modules.catalog.models import CatalogProduct, CatalogProductVersion, CatalogRefresh

AGENT = "Layer0-PoC catalog reader (internal proof of concept; one request per page per day)"
# page, how to read it, the unit when the page belongs to one
PAGES = [
    ("https://flex.com/products", "flex", None),
    ("https://flex.com/products/power-and-cooling", "flex", None),
    ("https://flex.com/products/power-modules", "flex", "FPM"),
    ("https://anordmardix.com/products/", "links", "ANORD"),
    ("https://crowntechnicalsystems.com/products/", "links", "CROWN"),
    ("https://ep2.com/", "links", "EP2"),
    ("https://jetcool.com/", "links", "JETCOOL"),
]
UNIT_BY_HOST = {"anordmardix.com": "ANORD", "crowntechnicalsystems.com": "CROWN", "ep2.com": "EP2", "jetcool.com": "JETCOOL"}
_lock = threading.Lock()  # ponytail: one refresh at a time in this process; a database lock if the API runs several workers


def fetch(url: str) -> str:
    """One page. The system certificate store is used (it trusts the corporate proxy; certifi does not)."""
    r = httpx.get(url, headers={"User-Agent": AGENT}, verify=ssl.create_default_context(), follow_redirects=True, timeout=30)
    r.raise_for_status()
    return r.text


def allowed(url: str) -> bool:
    parts = urlparse(url)
    robots = urllib.robotparser.RobotFileParser()
    try:
        robots.parse(fetch(f"{parts.scheme}://{parts.netloc}/robots.txt").splitlines())
    except httpx.HTTPStatusError:
        return True  # no robots.txt: allowed
    return robots.can_fetch(AGENT, url)


class _Flex(HTMLParser):
    """Flex product pages: <h2> = category, <h3> = product, <li> under it = key features, first link after it = its page."""
    def __init__(self, base: str):
        super().__init__(convert_charrefs=True)
        self.base, self.category, self.products, self.tag, self.text = base, "", [], None, []

    def handle_starttag(self, tag, attrs):
        if tag in ("h2", "h3", "li"):
            self.tag, self.text = tag, []
        elif tag == "a" and self.products and not self.products[-1]["link"]:
            href = dict(attrs).get("href") or ""
            if href and not href.startswith("#") and not href.startswith("mailto:"):
                self.products[-1]["link"] = urljoin(self.base, href)

    def handle_endtag(self, tag):
        if tag != self.tag:
            return
        text = " ".join(" ".join(self.text).split())
        if tag == "h2" and text:
            self.category = text
        elif tag == "h3" and text:
            self.products.append({"name": text, "category": self.category, "features": [], "link": ""})
        elif tag == "li" and text and self.products and not self.products[-1]["link"]:
            self.products[-1]["features"].append(text)
        self.tag = None

    def handle_data(self, data):
        if self.tag:
            self.text.append(data.strip())


class _Links(HTMLParser):
    """Unit sites: links on the same site whose path contains /products/, named by their text."""
    def __init__(self, base: str):
        super().__init__(convert_charrefs=True)
        self.base, self.host, self.href, self.text, self.found = base, urlparse(base).netloc.removeprefix("www."), None, [], {}

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href, self.text = dict(attrs).get("href") or "", []

    def handle_endtag(self, tag):
        if tag != "a" or self.href is None:
            return
        url = urljoin(self.base, self.href).split("#")[0]
        name = " ".join(" ".join(self.text).split())
        path = urlparse(url).path.rstrip("/")
        if (urlparse(url).netloc.removeprefix("www.") == self.host and "/products/" in path + "/" and path != "/products"
                and name and len(name) <= 120):
            self.found.setdefault(url, name)
        self.href = None

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data.strip())


def _unit(link: str) -> str | None:
    if "/products/power-modules" in link:
        return "FPM"
    return UNIT_BY_HOST.get(urlparse(link).netloc.removeprefix("www.")) if link else None


def parse(html: str, url: str, kind: str, bu: str | None) -> list[dict]:
    """A page -> products [{key, name, category, features, link, bu}] (no network, no database)."""
    if kind == "flex":
        p = _Flex(url)
        p.feed(html)
        found = [x for x in p.products if x["features"] or x["link"]]  # menus and page titles have neither
    else:
        p = _Links(url)
        p.feed(html)
        found = [{"name": n, "category": "", "features": [], "link": link} for link, n in p.found.items()]
    out = {}
    for x in found:
        unit = bu or _unit(x["link"])
        key = x["link"].rstrip("/") or f"{url}#{x['name']}"
        out.setdefault(key, x | {"key": key, "bu": unit})
    return list(out.values())


def _hash(p: dict) -> tuple:
    return (p["name"], tuple(p["features"]), p["link"])


def refresh(db: Session, trigger: str = "schedule", pages: list[tuple] | None = None) -> CatalogRefresh:
    """Read every page and store what changed. Never raises for a page: its failure is recorded on the run."""
    with _lock:
        run = CatalogRefresh(trigger=trigger)
        db.add(run)
        db.commit()
        now, seen, ok_pages = utcnow(), set(), set()
        for url, kind, bu in pages or PAGES:
            entry = {"url": url, "status": "ok", "sha256": None, "products": 0, "error": ""}
            try:
                if not allowed(url):
                    entry |= {"status": "skipped", "error": "robots.txt does not allow this page"}
                else:
                    html = fetch(url)
                    entry["sha256"] = hashlib.sha256(html.encode()).hexdigest()
                    products = parse(html, url, kind, bu)
                    entry["products"] = len(products)
                    for p in products:
                        if p["key"] not in seen:  # a product listed on two pages: the first page read wins
                            _store(db, run, p, url, now)
                            seen.add(p["key"])
                    ok_pages.add(url)
            except (httpx.HTTPError, ssl.SSLError, OSError) as exc:  # network, TLS or HTTP status: keep the last good data
                entry |= {"status": "failed", "error": f"{type(exc).__name__}: {exc}"[:300]}
            run.sources = run.sources + [entry]
        for gone in db.scalars(select(CatalogProduct).where(CatalogProduct.active.is_(True),
                                                            CatalogProduct.source_url.in_(ok_pages))):
            if gone.key not in seen:
                gone.active = False
                _close(db, gone.key, now)
                run.removed += 1
        statuses = {s["status"] for s in run.sources}
        run.status = "ok" if statuses <= {"ok", "skipped"} else "failed" if "ok" not in statuses else "partial"
        run.finished_at = utcnow()
        audit.record(db, trigger, "catalog_refreshed", "catalog", str(run.id), None, status=run.status,
                     added=run.added, changed=run.changed, removed=run.removed)
        db.commit()
        return run


def _close(db: Session, key: str, now: datetime) -> None:
    cur = _current(db, key)
    if cur:
        cur.valid_to = now


def _current(db: Session, key: str) -> CatalogProductVersion | None:
    return db.scalar(select(CatalogProductVersion).where(CatalogProductVersion.key == key,
                                                         CatalogProductVersion.valid_to.is_(None)))


def _store(db: Session, run: CatalogRefresh, p: dict, url: str, now: datetime) -> None:
    prod = db.get(CatalogProduct, p["key"])
    if prod is None:
        db.add(CatalogProduct(key=p["key"], bu=p["bu"], category=p["category"], source_url=url, first_seen=now, last_seen=now))
        db.flush()
        db.add(CatalogProductVersion(key=p["key"], name=p["name"], features=p["features"], link=p["link"],
                                     refresh_id=run.id, valid_from=now))
        run.added += 1
        return
    prod.last_seen, prod.category = now, p["category"] or prod.category
    reactivated, prod.active = not prod.active, True
    cur = _current(db, p["key"])
    if cur and _hash({"name": cur.name, "features": cur.features, "link": cur.link}) == _hash(p) and not reactivated:
        return
    if cur:
        cur.valid_to = now
    n = db.scalar(select(CatalogProductVersion.version).where(CatalogProductVersion.key == p["key"])
                  .order_by(CatalogProductVersion.version.desc()).limit(1)) or 0
    db.add(CatalogProductVersion(key=p["key"], version=n + 1, name=p["name"], features=p["features"], link=p["link"],
                                 refresh_id=run.id, valid_from=now))
    run.changed += 1


def published(db: Session) -> dict:
    """The current published catalog with each product's earlier names, and the last runs."""
    rows = []
    for prod in db.scalars(select(CatalogProduct).order_by(CatalogProduct.bu, CatalogProduct.key)):
        versions = list(db.scalars(select(CatalogProductVersion).where(CatalogProductVersion.key == prod.key)
                                   .order_by(CatalogProductVersion.version)))
        cur = versions[-1]
        rows.append({"key": prod.key, "bu": prod.bu, "category": prod.category, "source_url": prod.source_url,
                     "active": prod.active, "first_seen": prod.first_seen, "last_seen": prod.last_seen,
                     "name": cur.name, "features": cur.features, "link": cur.link, "version": cur.version,
                     "earlier_names": [v.name for v in versions[:-1] if v.name != cur.name]})
    runs = list(db.scalars(select(CatalogRefresh).order_by(CatalogRefresh.id.desc()).limit(10)))
    version = db.scalar(select(CatalogRefresh.id).where((CatalogRefresh.added + CatalogRefresh.changed
                                                         + CatalogRefresh.removed) > 0).order_by(CatalogRefresh.id.desc()).limit(1))
    return {"products": rows, "runs": runs, "catalog_version": version}


def versions(db: Session, key: str) -> list[CatalogProductVersion]:
    if db.get(CatalogProduct, key) is None:
        raise LookupError("Product not found in the published catalog.")
    return list(db.scalars(select(CatalogProductVersion).where(CatalogProductVersion.key == key)
                           .order_by(CatalogProductVersion.version)))
