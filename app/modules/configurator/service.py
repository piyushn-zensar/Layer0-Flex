"""Configurator: the supplied rfp_configurator.py run on the merged catalog, fed from frozen RFP requirements.  Owner: Piyush.

P-54 (C-55, PLAN 12.2 decisions 5 and 6). The script is vendored unchanged except for prepare_catalog()
(rfp_configurator.py). Its catalogue is the merged catalog (catalog.power_modules(), P-53), rebuilt with the export's
column names, so the script matches on the same validated values the Product Catalog shows.

Public contract:
    catalog_frame() -> DataFrame                 the merged catalog as the script's catalogue (cached)
    requirement_refs(db, opp_id, req_ids=None) -> list[dict]   {req_id, text, quote, section, category, document,
                                                 page}: the requirements as the agents see them, with their source;
                                                 None = every technical and compliance item
    normalise(raw, items=()) -> dict             the agent's answer -> {"input" (the script's JSON, target units),
                                                 "provenance" {"board.x": {req_ids, source, stated, unit, interpreted}},
                                                 "unit_issues" [...]}; numbers are parsed from the text as written
                                                 and converted by code; a number not in its requirements' text is
                                                 dropped with an issue (the model never converts)
    missing(cfg_input) -> list[dict]             inputs the script needs that the requirements do not state:
                                                 {scope, field, needed_for}
    inputs(db, opp_id, req_ids, scope=None, component="") -> dict   requirement_refs + agent (frozen) + normalise +
                                                 missing; scope "board" or "system" keeps that part of the input
                                                 only; component tells the agent what the items were grouped under
    run(prepared) -> dict                        the script's report (configure) on the merged catalog, with the
                                                 provenance, the requirement refs and the missing inputs beside it
    components(db, opp_id) -> dict               P-55 (C-56): the bid's technical and compliance items grouped by
                                                 requested component (one frozen model call); one configurator search
                                                 per DC/DC group (board input only), the system checks once (system
                                                 input only), other components listed without a numeric search:
                                                 {"groups": [{name, kind, req_ids, run|None}], "system": run|None,
                                                  "ungrouped": [req_id] (no component, or not answered),
                                                  "unassigned": [req_id] (the model gave no answer), "unknown_ids"}
    prepare(items, scope, component), plan(items)   inputs() and components() on refs already read (no database)
"""
import re
from functools import lru_cache

import pandas as pd
from sqlalchemy.orm import Session

from app.core import config
from app.modules.catalog import service as catalog
from app.modules.configurator import agent
from app.modules.configurator import rfp_configurator as rc
from app.modules.opportunities import service as opportunities
from app.modules.requirements import service as requirements

COLUMNS = {"component_id": "Component ID", "part_number": "Part Number", "product_line": "Series", "status": "Status",
           "series": "Series.1", "vin_min_v": "Input Voltage (min) (V)", "vin_max_v": "Input Voltage (max) (V)",
           "vout_min_v": "Output Voltage (min) (V)", "vout_max_v": "Output Voltage (max) (V)",
           "vout_typ_v": "Output Voltage (typical) (V)", "power_w": "Output Power (W)",
           "power_peak_w": "Output Power (Peak) (W pk)", "current_a": "Output Current (A)",
           "efficiency_pct": "Typical Efficiency (%)", "length_mm": "Length (mm)", "width_mm": "Width (mm)",
           "height_mm": "Height (mm)", "footprint": "Package Footprint", "package_type": "Package Type",
           "mounting": "Mounting Type", "isolation_v": "Isolation Voltage (V)", "isolation": "Isolation",
           "regulation": "Regulation"}


PRODUCT_CATEGORIES = {"technical", "compliance"}   # as matching.PRODUCT_CATEGORIES: what a product can answer


@lru_cache
def catalog_frame() -> pd.DataFrame:
    rows = []
    for p in catalog.power_modules():
        r = {col: p[f] for f, col in COLUMNS.items()}
        r["Paralleling"] = None if p["paralleling"] in (None, "None") else p["paralleling"]  # the export's blank
        r["Application"] = ",".join(p["application"]) or None
        r["Digital Interfaces"] = " and ".join(p["interfaces"]) or None
        rows.append(r)
    return rc.prepare_catalog(pd.DataFrame(rows))


def requirement_refs(db: Session, opp_id: str, req_ids: list[str] | None = None) -> list[dict]:
    """None: every technical and compliance item of the register (leaf items, document order)."""
    docs = {d.id: d.filename for d in opportunities.documents(db, opp_id)}
    rows = [r for r in requirements.current(db, opp_id, include_children=True) if r.kind == "item"]
    by_id = {r.req_id: r for r in rows}
    if req_ids is None:
        picked = [r for r in rows if r.category in PRODUCT_CATEGORIES]
    else:
        picked = [by_id[i] for i in req_ids if i in by_id]
    return [{"req_id": r.req_id, "text": r.text, "quote": r.quote, "section": r.section, "category": r.category,
             "document": docs.get(r.document_id), "page": r.page} for r in picked]


# unit as written -> (quantity, factor to the base unit). Case matters: MW is megawatt, mW milliwatt.
UNITS = {"V": ("V", 1), "kV": ("V", 1e3), "mV": ("V", 1e-3), "W": ("W", 1), "kW": ("W", 1e3), "MW": ("W", 1e6),
         "GW": ("W", 1e9), "mW": ("W", 1e-3), "A": ("A", 1), "kA": ("A", 1e3), "mA": ("A", 1e-3), "mm": ("mm", 1),
         "cm": ("mm", 10), "m": ("mm", 1e3), "in": ("mm", 25.4), "inch": ("mm", 25.4), "inches": ("mm", 25.4),
         "%": ("%", 1), "percent": ("%", 1)}


def _unit(u: str | None) -> str | None:
    if u is None:
        return None
    u = u.replace("°", "").replace(" ", "")
    for suffix in ("DC", "AC", "dc", "ac", "pk", "peak"):       # VDC, kVAC, Wpk: same quantity
        if u.endswith(suffix) and u[: -len(suffix)] in UNITS:
            return u[: -len(suffix)]
    return u


def _convert(value: float, unit: str | None, target: str) -> tuple[float | None, str | None]:
    """value in `unit` -> value in `target`, or (None, why)."""
    u = _unit(unit)
    if target == "C":
        if u in (None, "C", "degC", "celsius"):
            return value, None if u else f"unit not stated; read as {target}"
        if u in ("F", "degF", "fahrenheit"):
            return round((value - 32) * 5 / 9, 2), None
        return None, f"unit {unit!r} is not a temperature"
    if target == "fraction":
        return (value / 100, None) if u in ("%", "percent") or value > 1 else (value, None)
    if u is None:
        return value, f"unit not stated; read as {target}"
    if u not in UNITS or UNITS[u][0] != UNITS[target][0]:
        return None, f"unit {unit!r} cannot be converted to {target}"
    return round(value * UNITS[u][1] / UNITS[target][1], 6), None


NUMBER = re.compile(r"^\s*[~≈]?\s*(\d[\d,]*(?:\.\d+)?)\s*(\S*)")   # "15 kW", "1,200 J", "45 °C", "97.5%"


def _digits(s: str) -> str:
    return re.sub(r"[,\s]", "", s)


def normalise(raw: dict, items: list[dict] = ()) -> dict:
    """items: the requirement refs the answer was given; a number is kept only if its digits are in their text.
    ponytail: a digit-substring check, so "15" passes inside "150"; enough to stop converted or added-up numbers."""
    out, prov, issues = {"system": {}, "board": {}}, {}, []
    texts = {i["req_id"]: _digits(i["text"] + " " + i["quote"]) for i in items}
    for scope, fields in (("system", agent.SYSTEM), ("board", agent.BOARD)):
        for f, (kind, target) in fields.items():
            v = (raw.get(scope) or {}).get(f)
            stated = None if v is None else v.get("as_written", v.get("value"))
            if stated in (None, "", []):
                continue
            value, unit = stated, None
            if kind == "number":
                m = NUMBER.match(str(stated))
                why = None if m else f"no number in {stated!r}"
                if m and texts and not any(_digits(m.group(1)) in texts.get(r, "") for r in v["req_ids"]):
                    why = f"{stated!r} is not in the text of {', '.join(v['req_ids'])}"
                if why:
                    issues.append({"field": f"{scope}.{f}", "message": why, "req_ids": v["req_ids"]})
                    continue
                unit = m.group(2) or None
                value, why = _convert(float(m.group(1).replace(",", "")), unit, target)
                if why:
                    issues.append({"field": f"{scope}.{f}", "message": why, "req_ids": v["req_ids"]})
                if value is None:
                    continue
            out[scope][f] = {"value": value, "source": "; ".join(v["req_ids"]) + ": " + v["source"]}
            prov[f"{scope}.{f}"] = {"req_ids": v["req_ids"], "source": v["source"], "stated": stated, "unit": unit,
                                   # a category the model chose (N+1 for "four blocks plus a catcher"): confirm it
                                   "interpreted": kind != "number" and not all(
                                       str(x).lower() in v["source"].lower() for x in (stated if kind == "list" else [stated]))}
    return {"input": out, "provenance": prov, "unit_issues": issues}


SYSTEM_NEEDS = {"total_it_load_mw": "module count and CDU sizing", "rack_density_kw": "rack density check",
                "distribution_voltage": "distribution voltage check", "redundancy": "redundancy check",
                "cooling_mode": "cooling check", "coolant_supply_temp_c": "coolant temperature check"}
BOARD_NEEDS = {("input_v_min",): "input range filter", ("output_v_min",): "output voltage filter",
               ("output_power_w", "output_current_a", "peak_power_w"): "module count (power or current)"}


def missing(cfg_input: dict) -> list[dict]:
    """What the script needs and the requirements do not state; only for a scope the requirements touch."""
    out = []
    s, b = cfg_input.get("system") or {}, cfg_input.get("board") or {}
    if s:
        out += [{"scope": "system", "field": f, "needed_for": why} for f, why in SYSTEM_NEEDS.items() if f not in s]
    if b:
        out += [{"scope": "board", "field": " or ".join(fs), "needed_for": why}
                for fs, why in BOARD_NEEDS.items() if not any(f in b for f in fs)]
    return out


def inputs(db: Session, opp_id: str, req_ids: list[str], scope: str | None = None, component: str = "") -> dict:
    return prepare(requirement_refs(db, opp_id, req_ids), scope, component)


def prepare(items: list[dict], scope: str | None = None, component: str = "") -> dict:
    """inputs() on requirement refs already read (no database)."""
    prepared = normalise(agent.extract(items, rc.catalog_vocab(catalog_frame()), component), items)
    if scope:   # a component search sees board fields only, the system checks system fields only (C-56)
        prepared["input"] = {scope: prepared["input"][scope]}
        prepared["provenance"] = {k: v for k, v in prepared["provenance"].items() if k.startswith(scope + ".")}
        prepared["unit_issues"] = [i for i in prepared["unit_issues"] if i["field"].startswith(scope + ".")]
    return {"requirements": items, **prepared, "missing": missing(prepared["input"])}


def run(prepared: dict) -> dict:
    report = rc.configure(prepared["input"], catalog_frame())
    for scope in ("system", "board"):     # a scoped run (inputs(..., scope)) reports its own part only
        if scope not in prepared["input"]:
            report.pop(scope, None)
    return report | {"inputs": prepared["provenance"], "requirements": prepared.get("requirements", []),
                     "unit_issues": prepared.get("unit_issues", []), "missing": missing(prepared["input"])}


DATA_CENTRE = {"total_it_load_mw", "rack_density_kw", "cooling_mode", "coolant_supply_temp_c", "liquid_capture_fraction"}


def components(db: Session, opp_id: str) -> dict:
    return plan(requirement_refs(db, opp_id))


def plan(items: list[dict]) -> dict:
    """components() on requirement refs already read (no database)."""
    known = {i["req_id"]: i for i in items}
    grouped_ = agent.group(items)
    groups = grouped_["groups"]
    unknown = sorted({i for g in groups for i in g["req_ids"]} - set(known))     # an ID the model made up: reported, dropped
    out, system = [], None
    for g in groups:
        ids = [i for i in dict.fromkeys(g["req_ids"]) if i in known]
        if not ids:
            continue
        run_, refs = None, [known[i] for i in ids]
        if g["kind"] == "dc_dc":
            run_ = run(prepare(refs, "board", f"dc_dc: {g['name']} (fill the board fields for this conversion)"))
        elif g["kind"] == "system":
            prepared = prepare(refs, "system", "system: installation-wide parameters")
            if DATA_CENTRE & set(prepared["input"]["system"]):
                run_ = run(prepared)
            else:   # the script's system checks are Axiom AI-module limits: not for, say, a switchgear lineup
                run_ = {"status": "not_applicable", "inputs": prepared["provenance"], "requirements": prepared["requirements"],
                        "reason": "The RFP states no IT load, rack density or cooling for a data-centre installation, so "
                                  "the configurator's system checks (Axiom AI module limits) do not apply."}
            system = run_
        out.append({"name": g["name"], "kind": g["kind"], "req_ids": ids, "run": run_})
    grouped = {i for g in out for i in g["req_ids"]}
    return {"groups": out, "system": system, "ungrouped": [i for i in known if i not in grouped],
            "unknown_ids": unknown, "unassigned": grouped_["unassigned"]}


if __name__ == "__main__":  # self-check: python -m app.modules.configurator.service
    cat = catalog_frame()
    assert rc.selftest(cat) == 0                                    # the supplied self-test, on the merged catalog
    xlsx = rc.load_catalog(str(config.DATA / "axiom_products/PowerModules-1791937030.xlsx"))
    probe = {"board": {"input_v_min": 40, "input_v_max": 60, "output_v_min": 12, "output_v_max": 12,
                       "output_power_w": 1500, "digital": "PMBus", "applications": ["Data Center and Cloud"]}}
    same = lambda r: [(c["part_number"], c["modules_total"]) for c in r["board"]["candidates"]]  # noqa: E731
    assert same(rc.configure(probe, cat)) == same(rc.configure(probe, xlsx))  # same answer as on the supplied file
    n = normalise({"system": {"total_it_load_mw": {"as_written": "120,000 kW", "req_ids": ["R1"], "source": "120,000 kW"}},
                   "board": {"input_v_min": {"as_written": "0.8 kVDC", "req_ids": ["R2"], "source": "0.8 kVDC"},
                             "max_height_mm": {"as_written": "0.5 in", "req_ids": ["R3"], "source": "0.5 in"},
                             "output_power_w": {"as_written": "3 furlongs", "req_ids": ["R4"], "source": "3 furlongs"},
                             "peak_power_w": {"as_written": "90 kW", "req_ids": ["R4"], "source": "six 15 kW"}}},
                  [{"req_id": "R1", "text": "", "quote": "IT load 120,000 kW"}, {"req_id": "R2", "text": "", "quote": "0.8 kVDC"},
                   {"req_id": "R3", "text": "", "quote": "at most 0.5 in high"}, {"req_id": "R4", "text": "", "quote": "six 15 kW, 3 furlongs"}])
    assert "peak_power_w" not in n["input"]["board"] and "not in the text" in n["unit_issues"][-1]["message"]  # added up
    assert n["input"]["system"]["total_it_load_mw"]["value"] == 120 and n["input"]["board"]["input_v_min"]["value"] == 800
    assert n["input"]["board"]["max_height_mm"]["value"] == 12.7 and "output_power_w" not in n["input"]["board"]
    assert [m["needed_for"] for m in missing(n["input"]) if m["scope"] == "board"] == ["output voltage filter", "module count (power or current)"]
    print("configurator ok")
