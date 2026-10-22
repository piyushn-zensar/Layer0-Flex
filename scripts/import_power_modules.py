"""Import the Flex Power Modules spreadsheet into the catalog (P-53, C-52 to C-54).

    .venv/Scripts/python -m scripts.import_power_modules [--file X.xlsx] [--date YYYY-MM-DD]

Writes data/knowledge_base/power_modules.json (contract: team/PLAN.md section 12.3), keyed by part number:
- the two "Series" columns are split: column C (the same for every row) -> product_line, column E -> series
  (an ordering code for evaluation and test boards, whose "Compatibility" goes to evaluates);
- numbers keep the header unit (V, W, A, %, mm); an empty cell is null = unknown, never 0;
- a part whose series is a model on the published web catalog (catalog_items.json) becomes a variant of it
  (family_key = that catalog ID) and carries the web text; numbers the web text states for that series are
  compared, and a disagreement is stored in "conflicts" (both values kept, nothing replaced);
- a repeat import updates parts in place: an empty cell never overwrites an earlier value, and "imported"
  records, per field, the date of the import that last changed it.
"""
import argparse
import html
import json
import re
from datetime import date
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "data/axiom_products/PowerModules-1791937030.xlsx"
OUT = ROOT / "data/knowledge_base/power_modules.json"
WEB = ROOT / "data/knowledge_base/catalog_items.json"

# spreadsheet column (0-based) -> field; the headers name the units
NUM = {8: "vin_min_v", 9: "vin_max_v", 10: "vout_min_v", 11: "vout_max_v", 24: "vout_typ_v", 12: "power_w",
       13: "power_peak_w", 14: "current_a", 23: "current_peak_a", 15: "efficiency_pct", 16: "length_mm",
       17: "width_mm", 18: "height_mm", 25: "isolation_v"}
TEXT = {3: "status", 19: "footprint", 20: "package_type", 21: "mounting", 22: "paralleling", 30: "isolation",
        31: "regulation", 29: "multi_output"}
LISTS = {32: "application", 7: "interfaces", 6: "attributes"}
OUTPUTS = {2: {33: "v_min", 26: "v_nom", 34: "v_max", 27: "power_w", 28: "current_a"},
           3: {35: "v_min", 36: "v_nom", 37: "v_max", 38: "power_w", 39: "current_a"}}
HEADERS = {0: "Component ID", 1: "Part Number", 2: "Series", 4: "Series", 5: "Compatibility", 8: "Input Voltage (min) (V)",
           12: "Output Power (W)", 39: "Output 3 Current (max) (A)"}


def _list(v, sep=r",") -> list[str]:
    return [t.strip() for t in re.split(sep, str(v)) if t.strip()] if v not in (None, "") else []


def _num(v):
    if v in (None, ""):
        return None
    f = float(v)
    return int(f) if f.is_integer() else f


def parse_row(r: tuple, n: int) -> dict:
    """One spreadsheet row -> the spreadsheet's fields of a catalog item (no merge, no web)."""
    pn = html.unescape(str(r[1]).strip())
    board = r[12] is None or r[8] is None          # boards carry no electrical ratings (two lack "Evaluation")
    it = {"part_number": pn, "component_id": r[0], "product_line": r[2], "series": r[4],
          "evaluates": _list(r[5]) if board else [], "product_type": "evaluation_board" if board else "power_module",
          "row": n}
    it |= {f: _num(r[c]) for c, f in NUM.items()}
    it |= {f: r[c] for c, f in TEXT.items()}
    it |= {f: _list(r[c], r",| and " if f == "interfaces" else r",") for c, f in LISTS.items()}  # "PMBus and GCB"
    it["outputs"] = [{"n": k} | {f: _num(r[c]) for c, f in cols.items()}
                     for k, cols in OUTPUTS.items() if any(r[c] is not None for c in cols)]
    return it


def web_envelope(specs: str) -> dict:
    """Numbers the web text states for a series: input range (first clause naming "in"), largest W and %.
    ponytail: a few patterns over the catalog's own short text, not requirement identification; a value
    the patterns miss is simply not compared."""
    out = {}
    clause = next((c for c in specs.split(";") if re.search(r"\bin\b", c)), "")
    rng = [(float(a), float(b)) for a, b in re.findall(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*V\b", clause)]
    if rng:
        out["vin_min_v"], out["vin_max_v"] = min(a for a, _ in rng), max(b for _, b in rng)
    watts = [float(w.replace(",", "")) * (1000 if k else 1)
             for w, k in re.findall(r"(\d[\d,]*(?:\.\d+)?)\s*(k)?W\b", specs)]
    if watts:
        out["power_peak_w"] = max(watts)
    eff = [float(e) for e in re.findall(r"(\d{2}(?:\.\d+)?)\s*%", specs)]
    if eff:
        out["efficiency_pct"] = max(eff)
    return out


def conflicts(it: dict, env: dict, url: str) -> list[dict]:
    """A part outside the range its series' web page states (input range, power, efficiency)."""
    out = []
    for f, lo in (("vin_min_v", True), ("vin_max_v", False)):
        if it.get(f) is not None and f in env and (it[f] < env[f] if lo else it[f] > env[f]):
            out.append({"field": f, "spreadsheet": it[f], "web": env[f], "web_url": url})
    peak = max((v for v in (it.get("power_w"), it.get("power_peak_w")) if v is not None), default=None)
    if peak is not None and "power_peak_w" in env and peak > env["power_peak_w"]:
        out.append({"field": "power_w", "spreadsheet": peak, "web": env["power_peak_w"], "web_url": url})
    if it.get("efficiency_pct") is not None and "efficiency_pct" in env and it["efficiency_pct"] > env["efficiency_pct"]:
        out.append({"field": "efficiency_pct", "spreadsheet": it["efficiency_pct"], "web": env["efficiency_pct"], "web_url": url})
    return out


FIELDS = ["component_id", "product_line", "series", "evaluates", "product_type", *NUM.values(), *TEXT.values(),
          *LISTS.values(), "outputs"]


def merge(old: dict | None, new: dict, today: str) -> dict:
    """New spreadsheet values over the old item; an empty value never overwrites a known one."""
    it = dict(old or {"part_number": new["part_number"], "imported": {}})
    it["imported"] = dict(it.get("imported", {}))
    for f in FIELDS:
        v = new[f]
        if v is None or v == []:
            it.setdefault(f, v)
        elif it.get(f) != v:
            it[f], it["imported"][f] = v, today
    it["sheet"] = {"file": XLSX.relative_to(ROOT).as_posix(), "row": new["row"]}
    return it


def build(rows: list[tuple], old: dict, web: list[dict], today: str) -> dict:
    fpm = {i["model"]: i for i in web if i["bu"] == "FPM"}
    items = {}
    for n, r in enumerate(rows, start=2):           # spreadsheet row number (header is row 1)
        new = parse_row(r, n)
        it = merge(old.get(new["part_number"]), new, today)
        fam = fpm.get(it["series"]) or next((fpm[s] for s in it["evaluates"] if s in fpm), None)
        it["family_key"] = fam["id"] if fam else None
        it["web"] = {"id": fam["id"], "source_url": fam.get("source_url"), "specs": fam["specs"],
                     "retrieved": "2026-10-12"} if fam else None
        it["conflicts"] = conflicts(it, web_envelope(fam["specs"]), fam.get("source_url")) \
            if fam and it["product_type"] == "power_module" else []
        it["verified"] = False                     # spreadsheet values are not confirmed by the unit
        items[it["part_number"]] = it
    kept = [v for k, v in old.items() if k not in items]   # parts no longer in the file stay, marked
    for v in kept:
        v["status"] = v.get("status") or "Unknown"
        v["in_last_import"] = False
    for v in items.values():
        v["in_last_import"] = True
    return {"_note": "Flex Power Modules export merged into the catalog by scripts/import_power_modules.py (P-53). "
                     "Units as named in the field (V, W, A, %, mm); null = unknown. imported = date of the import "
                     "that last set each field. Values are as exported, not confirmed by the unit (verified false). "
                     "Contract: team/PLAN.md section 12.3.",
            "last_import": today, "source_file": XLSX.relative_to(ROOT).as_posix(),
            "items": sorted([*items.values(), *kept], key=lambda i: i["part_number"])}


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=Path, default=XLSX)
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    ws = openpyxl.load_workbook(a.file, read_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    for c, h in HEADERS.items():                    # the column positions this importer relies on
        if rows[0][c] != h:
            raise SystemExit(f"unexpected spreadsheet layout: column {c + 1} is {rows[0][c]!r}, expected {h!r}")
    old = {i["part_number"]: i for i in json.loads(a.out.read_text("utf-8"))["items"]} if a.out.exists() else {}
    web = json.loads(WEB.read_text("utf-8"))["items"]
    out = build([r for r in rows[1:] if r[1]], old, web, a.date)
    a.out.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", "utf-8")
    n = out["items"]
    print(f"{len(n)} parts ({sum(i['product_type'] == 'evaluation_board' for i in n)} boards), "
          f"{sum(bool(i['family_key']) for i in n)} linked to a web series, "
          f"{sum(bool(i['conflicts']) for i in n)} with conflicts -> {a.out}")
    return out


if __name__ == "__main__":
    main()
