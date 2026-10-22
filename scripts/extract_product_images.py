"""J-22 (C-65): pull product images out of the supplied PDFs and write data/axiom_products/images.json.

    .venv\\Scripts\\python -m scripts.extract_product_images          # extract and write (re-run gives the same files)
    .venv\\Scripts\\python -m scripts.extract_product_images --check  # only check images.json against the files and the catalog

What it does, per document in documents.json and per family key on the pages that document lists for it:
1. Candidates: images placed on those pages, at least 300 x 200 px, that are not a banner or table strip (wider
   than 3:1, or taller than 4:1), a background (over 70% of the page), page furniture (a small image in the top or bottom margin,
   such as a logo) or the same image on three or more pages of one file.
2. Verified: an image is `verified: true` only when the text within 36 pt of it names that family and no other
   catalog family ("beside the image"), or when the document is about that one family and its page names no other
   (a datasheet). Anything else, such as a photo on a page that names two products or none, is `verified: false`.
3. Placeholder rule: a family keeps up to two different verified images. With none, it keeps its best unverified
   image from a document that is about the family, flagged `verified: false`; the catalog page shows that as a
   placeholder. Unverified images from portfolio documents (applies: general) are dropped, because a shared photo
   there belongs to no particular product. A family with no candidate has no entry; the page shows the same
   placeholder.
4. Files go to data/axiom_products/images/ (JPEG; PNG when the picture has transparency), at most 1200 px on the
   longer side, named from the family key.

images.json (PLAN 12.3): [{file, family_key, part_numbers, source_file, page, kind, verified}]; `file` is relative
to data/axiom_products/. The supplied PDFs name no part numbers, so `part_numbers` is empty.
"""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "data" / "axiom_products"
OUT = FOLDER / "images"
MANIFEST = FOLDER / "images.json"
DOCUMENTS = FOLDER / "documents.json"
CATALOG = ROOT / "data" / "knowledge_base" / "catalog_items.json"

MIN_W, MIN_H = 300, 200          # source pixels
MAX_WIDE, MAX_TALL = 3.0, 4.0    # wider than 3:1 is a banner or table strip; a rack or cabinet may be taller
MAX_PAGE_SHARE = 0.7             # more of the page than this is a background
LOGO_PAGES = 3                   # the same image on this many pages of one file is a logo or furniture
MARGIN_TOP, MARGIN_BOTTOM = 0.15, 0.92   # a small image wholly above / below these page fractions is furniture
FURNITURE_SHARE = 0.12           # ... when it covers less of the page than this
NEAR_PT = 36                     # "beside": text within this distance of the image
MAX_SIDE = 1200                  # longer side of the exported file, px
PER_FAMILY = 2                   # verified images kept per family
SAME_PICTURE = 6                 # two pictures this close in a 64-bit average hash are the same artwork

# Names that identify a family in text, beyond its catalog `model`. Matching is case-sensitive; the longest name
# wins, so "DATABAR DX+" is never read as "DX". Brand words alone (DATABAR, IBAR, RESINBAR) name no family.
# ponytail: names are kept here, not in the knowledge base, because only this script reads them; move them to
# data/axiom_products/ if another module needs them.
ALIASES = {
    "ANORD-BUSWAY/DATABAR DX": ["DATABAR DX", "DX"],
    "ANORD-BUSWAY/DATABAR DX+": ["DATABAR DX+", "DATABAR DX Plus", "DX+", "DX Plus"],
    "ANORD-BUSWAY/IBAR HXC": ["IBAR HXC", "HXC"],
    "ANORD-BUSWAY/IBAR HXA": ["IBAR HXA", "HXA"],
    "ANORD-BUSWAY/RESINBAR CXC": ["RESINBAR CXC", "CXC"],
    "ANORD-BUSWAY/RESINBAR CXA": ["RESINBAR CXA", "CXA"],
    "ANORD-LVSB/SEN Plus": ["SEN Plus", "SEN PLUS"],
    "ANORD-PDU/RPP": ["Remote Power Panel", "RPP"],
    "ANORD-PMS/MCMS": ["Modular Circuit Monitoring System", "MCMS"],
    "ANORD-PMS/EMS": ["Energy Management System", "Energy Management Systems"],
    "CROWN-ARMV/Arc-Resistant Switchgear": ["Arc-Resistant", "arc-resistant"],
    "CROWN-EHOUSE/E-House": ["E-house", "E-House", "e-house", "E-houses"],
    "JETCOOL-CDU/SmartSense CDU": ["SmartSense CDU", "SmartSense", "CDU300"],
    "JETCOOL-CDU/Modular CDU": ["Modular CDU", "Modular Rack-Level CDU"],
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.casefold().replace("+", " plus")).strip("-")


def _norm(text: str) -> str:
    """Hyphen variants to '-', non-breaking spaces to ' ', whitespace collapsed (the PDFs use U+2011 in 'e-house')."""
    text = re.sub(r"[‐-―−]", "-", text).replace(" ", " ")
    return re.sub(r"\s+", " ", text)


def _catalog_names() -> dict[str, list[str]]:
    d = json.loads(CATALOG.read_text(encoding="utf-8"))
    return {i["id"]: ALIASES.get(i["id"], [i["model"]]) for i in (d["items"] if isinstance(d, dict) else d)}


def _name_pattern(names: dict[str, list[str]]):
    """One alternation of every family name, longest first, plus the name -> families map."""
    owner = {}
    for fam, terms in names.items():
        for t in terms:
            owner.setdefault(t, set()).add(fam)
    alt = "|".join(re.escape(t) for t in sorted(owner, key=len, reverse=True))
    return re.compile(r"(?<![A-Za-z0-9+])(?:" + alt + r")(?![A-Za-z0-9]|\+)"), owner


def _families_named(text: str, pattern, owner) -> set[str]:
    found = set()
    for m in pattern.finditer(_norm(text)):
        found |= owner[m.group(0)]
    return found


def _pixmap(doc, xref: int, smask: int):
    pix = pymupdf.Pixmap(doc, xref)
    if pix.colorspace is None or pix.colorspace.n != 3:       # grey, CMYK, mask-only: bring to RGB
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    if smask:                                                  # RGBA: the cut-out keeps its transparency
        mask = pymupdf.Pixmap(doc, smask)
        if (mask.width, mask.height) != (pix.width, pix.height):   # some PDFs store the mask at another size
            mask = pymupdf.Pixmap(mask, pix.width, pix.height)
        pix = pymupdf.Pixmap(pix, mask)
    return pix


def _small(pix, side: int):
    return pymupdf.Pixmap(pix, side, side) if max(pix.width, pix.height) > side else pix


def _kind(pix) -> str:
    """photo or illustration (drawing, rendering, diagram): photographs use many more colours than flat artwork.
    ponytail: a colour count, not a classifier; a flat-shaded rendering reads as an illustration, a noisy scan as a
    photo. J-20 shows both the same way, so a wrong guess costs a label only."""
    small = _small(pix, 64)
    n, data = small.n, small.samples
    colours = Counter((data[i] >> 4, data[i + 1] >> 4, data[i + 2] >> 4) for i in range(0, len(data) - n + 1, n))
    top = sum(c for _, c in colours.most_common(12)) / max(1, sum(colours.values()))
    return "illustration" if top > 0.8 else "photo"


def _hash(pix) -> int:
    """64-bit average hash of the picture on a white ground: same artwork at another size or crop-free scale."""
    small = pymupdf.Pixmap(pix, 8, 8)
    n, data = small.n, small.samples
    grey = []
    for i in range(0, 64 * n, n):
        a = data[i + 3] if n == 4 else 255
        grey.append((data[i] + data[i + 1] + data[i + 2]) // 3 * a // 255 + 255 * (255 - a) // 255)
    mean = sum(grey) / 64
    return sum(1 << k for k, g in enumerate(grey) if g > mean)


def _export(pix, stem: str) -> Path:
    longest = max(pix.width, pix.height)
    if longest > MAX_SIDE:
        scale = MAX_SIDE / longest
        pix = pymupdf.Pixmap(pix, max(1, round(pix.width * scale)), max(1, round(pix.height * scale)))
    OUT.mkdir(parents=True, exist_ok=True)
    if pix.alpha:
        path = OUT / f"{stem}.png"
        pix.save(path)
    else:
        path = OUT / f"{stem}.jpg"
        pix.save(path, jpg_quality=85)
    return path


def _candidates(doc, doc_entry, pattern, owner) -> list[dict]:
    """Every usable image on the pages the manifest lists for each family key of this document."""
    pages_of = {}
    for fam, pages in doc_entry["pages"].items():
        for p in pages:
            pages_of.setdefault(p, []).append(fam)
    uses = Counter()                                           # how many pages show the same image
    for page in doc:
        for xref in {i["xref"] for i in page.get_image_info(xrefs=True)}:
            uses[xref] += 1
    smasks = {im[0]: im[1] for page in doc for im in page.get_images(full=True)}
    own = doc_entry["applies"] == "family"
    single = doc_entry["family_keys"][0] if own and len(doc_entry["family_keys"]) == 1 else None
    out = []
    for pno in sorted(pages_of):
        page = doc[pno - 1]
        area = page.rect.width * page.rect.height
        blocks = page.get_text("blocks")
        page_named = _families_named(page.get_text(), pattern, owner)
        seen = set()
        for info in page.get_image_info(xrefs=True):
            xref, w, h, box = info["xref"], info["width"], info["height"], pymupdf.Rect(info["bbox"])
            if not xref or xref in seen or w < MIN_W or h < MIN_H or uses[xref] >= LOGO_PAGES:
                continue
            share = box.width * box.height / area
            margin = box.y1 < MARGIN_TOP * page.rect.height or box.y0 > MARGIN_BOTTOM * page.rect.height
            if w / h > MAX_WIDE or h / w > MAX_TALL or share > MAX_PAGE_SHARE or (margin and share < FURNITURE_SHARE):
                continue
            seen.add(xref)
            near = pymupdf.Rect(box.x0 - NEAR_PT, box.y0 - NEAR_PT, box.x1 + NEAR_PT, box.y1 + NEAR_PT)
            text = " ".join(b[4] for b in blocks if b[6] == 0 and pymupdf.Rect(b[:4]).intersects(near))
            out.append({"page": pno, "xref": xref, "smask": smasks.get(xref, 0), "area": box.width * box.height, "own": own,
                        "named": _families_named(text, pattern, owner),
                        "sole": single if single and page_named == {single} else None, "families": pages_of[pno]})
    return out


def build() -> list[dict]:
    names = _catalog_names()
    pattern, owner = _name_pattern(names)
    documents = json.loads(DOCUMENTS.read_text(encoding="utf-8"))
    per_family: dict[str, list[dict]] = {}
    for d in documents:
        with pymupdf.open(FOLDER / d["file"]) as doc:
            for c in _candidates(doc, d, pattern, owner):
                for fam in c["families"]:
                    verified = c["named"] == {fam} or c["sole"] == fam
                    if verified or c["own"]:                   # a portfolio document's unverified photo is dropped
                        per_family.setdefault(fam, []).append({**c, "file": d["file"], "verified": verified})
    decoded: dict[tuple, tuple] = {}                           # (file, xref) -> (pixmap, hash), decoded once

    def decode(c):
        key = (c["file"], c["xref"])
        if key not in decoded:
            with pymupdf.open(FOLDER / c["file"]) as doc:
                pix = _pixmap(doc, c["xref"], c["smask"])
            decoded[key] = (pix, _hash(pix))
        return decoded[key]

    entries = []
    for fam in sorted(per_family):
        cands = sorted(per_family[fam], key=lambda c: (not c["verified"], not c["own"], -c["area"], c["file"], c["page"]))
        keep, hashes = [], []
        for c in cands:
            if keep and (not c["verified"] or len(keep) >= PER_FAMILY):
                break
            pix, h = decode(c)
            if any(bin(h ^ other).count("1") <= SAME_PICTURE for other in hashes):
                continue                                       # the same artwork again, from another page or file
            hashes.append(h)
            keep.append((c, pix))
        if not keep[0][0]["verified"]:
            keep = keep[:1]
        for n, (c, pix) in enumerate(keep, 1):
            path = _export(pix, f"{_slug(fam)}-{n}")
            entries.append({"file": path.relative_to(FOLDER).as_posix(), "family_key": fam, "part_numbers": [],
                            "source_file": c["file"], "page": c["page"], "kind": _kind(pix), "verified": c["verified"]})
    return entries


def check(entries: list[dict]) -> list[str]:
    """Problems with an images.json: a missing file, an unknown family, a bad page, a repeated file."""
    problems, ids = [], set(_catalog_names())
    files = [e["file"] for e in entries]
    for dup in sorted({f for f in files if files.count(f) > 1}):
        problems.append(f"{dup}: listed twice")
    for e in entries:
        if not (FOLDER / e["file"]).is_file():
            problems.append(f"{e['file']}: image file missing")
        if e["family_key"] not in ids:
            problems.append(f"{e['file']}: {e['family_key']} is not a catalog ID")
        src = FOLDER / e["source_file"]
        if not src.is_file():
            problems.append(f"{e['file']}: source {e['source_file']} missing")
        else:
            with pymupdf.open(src) as doc:
                if not 1 <= e["page"] <= doc.page_count:
                    problems.append(f"{e['file']}: page {e['page']} outside 1..{doc.page_count} of {e['source_file']}")
    return problems


def report(entries: list[dict]) -> None:
    documents = json.loads(DOCUMENTS.read_text(encoding="utf-8"))
    linked = sorted({k for d in documents for k in d["family_keys"]})
    have = {e["family_key"] for e in entries if e["verified"]}
    weak = {e["family_key"] for e in entries} - have
    none = [k for k in linked if k not in have | weak]
    print(f"{len(entries)} images for {len(have | weak)} families: {sum(e['verified'] for e in entries)} verified, "
          f"{sum(not e['verified'] for e in entries)} unverified (placeholder)")
    print(f"verified ({len(have)}): {sorted(have)}")
    print(f"placeholder, unverified image only ({len(weak)}): {sorted(weak)}")
    print(f"placeholder, no image found ({len(none)}): {none}")


if __name__ == "__main__":
    if "--check" in sys.argv:
        loaded = json.loads(MANIFEST.read_text(encoding="utf-8"))
        bad = check(loaded)
        print("\n".join(bad) if bad else f"images.json OK: {len(loaded)} entries")
        sys.exit(1 if bad else 0)
    for old in OUT.glob("*") if OUT.exists() else []:
        old.unlink()                                            # a re-run replaces the set, never adds to it
    result = build()
    MANIFEST.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    problems = check(result)
    assert not problems, problems
    report(result)
    print(f"wrote {MANIFEST.relative_to(ROOT)} (sha256 {hashlib.sha256(MANIFEST.read_bytes()).hexdigest()[:12]})")
