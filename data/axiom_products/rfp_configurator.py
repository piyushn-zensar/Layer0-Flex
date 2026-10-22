#!/usr/bin/env python3
"""
rfp_configurator.py - match RFP requirements to Flex / Axiom offerings.

Three layers:
  1. parse_requirements()   validate the JSON your LLM extracts from the RFP
  2. configure_system()     Axiom module / cooling / certification checks (config-driven)
  3. match_components()     board-level DC/DC module match against the Flex Power
                            Modules export (PowerModules-*.xlsx)

Design rules
  * Never guess. A value the RFP does not state stays None and is reported,
    not defaulted silently.
  * Every elimination is explainable: the funnel shows how many parts each
    filter removed, and when nothing matches, the relaxation table shows which
    single filter, if dropped, would have produced matches.
  * Anything not confirmed from a source document is flagged in the report.

Usage
  python rfp_configurator.py --catalog PowerModules.xlsx --rfp requirements.json --out result.json
  python rfp_configurator.py --catalog PowerModules.xlsx --selftest
"""
from __future__ import annotations

import argparse
import html
import json
import logging
import math
import re
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd

log = logging.getLogger("rfp_configurator")

# --------------------------------------------------------------------------
# Constants and source-tracked specs
# --------------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "Part Number", "Status", "Input Voltage (min) (V)", "Input Voltage (max) (V)",
    "Output Voltage (min) (V)", "Output Voltage (max) (V)", "Output Voltage (typical) (V)",
    "Output Power (W)", "Output Power (Peak) (W pk)", "Output Current (A)",
    "Typical Efficiency (%)", "Length (mm)", "Width (mm)", "Height (mm)",
    "Package Footprint", "Package Type", "Mounting Type", "Paralleling",
    "Isolation Voltage (V)", "Isolation", "Regulation", "Application", "Digital Interfaces",
]

NUMERIC_COLUMNS = [
    "Input Voltage (min) (V)", "Input Voltage (max) (V)", "Output Voltage (min) (V)",
    "Output Voltage (max) (V)", "Output Voltage (typical) (V)", "Output Power (W)",
    "Output Power (Peak) (W pk)", "Output Current (A)", "Typical Efficiency (%)",
    "Length (mm)", "Width (mm)", "Height (mm)", "Isolation Voltage (V)",
]

REDUNDANCY_FACTORS = {"N": lambda n: n, "N+1": lambda n: n + 1, "2N": lambda n: 2 * n}

# Axiom AI Module limits. Values come from the Axiom brochure as reviewed earlier
# in this project and are NOT confirmed by Axiom. Replace with Axiom's rules.
AXIOM_SPEC = {
    "module_capacity_mw": {"value": 4.0, "source": "Axiom brochure: up to 4 MW per module", "verified": False},
    "max_rack_density_kw": {"value": 1000.0, "source": "Axiom brochure: 250 kW to 1 MW per rack", "verified": False},
    "voltages": {"value": ["480VAC", "800VDC", "±400VDC"], "source": "Axiom brochure", "verified": False},
    "max_coolant_supply_c": {"value": 45.0, "source": "Axiom brochure: warm water, below about 45 C", "verified": False},
    "redundancy": {"value": ["N", "N+1", "4-TO-MAKE-3"], "source": "Axiom brochure: N+1, 4-to-make-3", "verified": False},
}

# Liquid cooling catalogue from JetCool datasheets. "firm" = redundant-pump capacity,
# "peak" = boost (all pumps running). Confirm approach temperature against the RFP.
CDU_CATALOG = [
    {"name": "SmartSense in-rack CDU (6U)", "firm_kw": 160.0, "peak_kw": 300.0,
     "source": "JetCool In-Rack CDU300 datasheet (redundant 160 kW at 4 C approach, boost 300 kW at 7 C)"},
    {"name": "Flex Modular Rack-Level CDU x4", "firm_kw": 800.0, "peak_kw": 1200.0,
     "source": "JetCool Modular CDU datasheet (column mapping inferred from text extraction)"},
    {"name": "Flex Modular Rack-Level CDU x6", "firm_kw": 1200.0, "peak_kw": 1800.0,
     "source": "JetCool Modular CDU datasheet (1.2 MW at 6 C, 1.8 MW at 9 C approach)"},
]

# Certifications found in the Flex / Anord Mardix documents reviewed so far.
# Absence here means "not found in what was reviewed", not "unsupported".
CERTIFICATIONS_FOUND = {
    "UL 67": "Anord Mardix Remote Power Panel datasheet",
    "UL 508A": "Anord Mardix Remote Power Panel datasheet",
    "UL 891": "Anord Mardix AMX switchboards (product page)",
    "IEC 61439": "Anord Mardix DATABAR / IBAR / MDX (BS EN/IEC 61439 family)",
    "BS EN 61439-6": "Anord Mardix IBAR busbar trunking",
}

LLM_EXTRACTION_PROMPT = """\
You are extracting requirements from an RFP. Return ONLY JSON with this shape:
{"system": {...}, "board": {...}}
Every field is either null (RFP is silent) or {"value": <number|string|list>, "source": "<verbatim RFP text>"}.
Never infer or default. Convert units: power in W (board) or MW (system), voltage in V, temperature in C.
system fields: total_it_load_mw, rack_density_kw, distribution_voltage ("480VAC"|"800VDC"|"±400VDC"|other),
  coolant_supply_temp_c, cooling_mode ("air"|"liquid"|"hybrid"), redundancy ("N"|"N+1"|"2N"|"4-to-make-3"),
  certifications (list of strings), deployment ("prefab"|"stick-built"), liquid_capture_fraction (0-1).
board fields: input_v_min, input_v_max, output_v_min, output_v_max, output_power_w, output_current_a,
  peak_power_w, isolation ("required"|"not_required"), isolation_v_min, regulation
  ("Regulated"|"Unregulated/Fixed Ratio"), digital ("PMBus"|"GCB"), applications (list), package_types (list),
  footprints (list), mountings (list), max_length_mm, max_width_mm, max_height_mm, min_efficiency_pct,
  redundancy ("N"|"N+1"|"2N"), design_margin_pct.
If the RFP gives only one voltage, put it in both min and max.
"""


class CatalogError(Exception):
    """Raised when the catalogue file is missing columns or unusable."""


@dataclass
class Issue:
    level: str          # "error" | "warning"
    field: str
    message: str


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _unwrap(raw: Any) -> tuple[Any, Optional[str]]:
    """Accept either a bare value or {"value":..., "source":...}."""
    if isinstance(raw, dict) and "value" in raw:
        return raw["value"], raw.get("source")
    return raw, None


def _to_float(value: Any, name: str, issues: list[Issue]) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        issues.append(Issue("error", name, f"expected a number, got boolean {value!r}"))
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        m = re.search(r"-?\d+(?:\.\d+)?", str(value))
        if m:
            issues.append(Issue("warning", name, f"parsed {m.group()} from {value!r}; confirm units"))
            out = float(m.group())
        else:
            issues.append(Issue("error", name, f"cannot read a number from {value!r}"))
            return None
    if not math.isfinite(out):
        issues.append(Issue("error", name, f"non-finite value {value!r}"))
        return None
    return out


def _to_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return [str(v).strip() for v in value if str(v).strip()]


def _canon(values: list[str], allowed: list[str], name: str, issues: list[Issue]) -> list[str]:
    lookup = {a.lower(): a for a in allowed}
    out = []
    for v in values:
        hit = lookup.get(v.lower())
        if hit is None:
            issues.append(Issue("error", name, f"{v!r} is not a catalogue value; allowed: {sorted(allowed)}"))
        else:
            out.append(hit)
    return out


def normalise_voltage(text: Optional[str]) -> Optional[str]:
    """'+/-400 VDC' -> '±400VDC', '480 vac' -> '480VAC'. Unrecognised text is returned upper-cased."""
    if not text:
        return None
    t = str(text).strip().upper().replace(" ", "")
    bipolar = any(tok in t for tok in ("±", "+/-", "+-", "PM"))
    m = re.search(r"(\d+(?:\.\d+)?)(VAC|VDC|V)", t)
    if not m:
        return t
    num = m.group(1).rstrip("0").rstrip(".") if "." in m.group(1) else m.group(1)
    return f"{'±' if bipolar else ''}{num}{m.group(2)}"


def _clean(obj: Any) -> Any:
    """Make numpy / NaN values JSON-safe."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if (isinstance(obj, float) and not math.isfinite(obj)) or (
            isinstance(obj, np.floating) and not np.isfinite(obj)) else float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


# --------------------------------------------------------------------------
# Requirement models
# --------------------------------------------------------------------------

@dataclass
class BoardRequirement:
    input_v_min: Optional[float] = None
    input_v_max: Optional[float] = None
    output_v_min: Optional[float] = None
    output_v_max: Optional[float] = None
    output_power_w: Optional[float] = None
    output_current_a: Optional[float] = None
    peak_power_w: Optional[float] = None
    isolation: Optional[str] = None            # "required" | "not_required"
    isolation_v_min: Optional[float] = None
    regulation: Optional[str] = None
    digital: Optional[str] = None              # "PMBus" | "GCB"
    applications: list[str] = field(default_factory=list)
    package_types: list[str] = field(default_factory=list)
    footprints: list[str] = field(default_factory=list)
    mountings: list[str] = field(default_factory=list)
    max_length_mm: Optional[float] = None
    max_width_mm: Optional[float] = None
    max_height_mm: Optional[float] = None
    min_efficiency_pct: Optional[float] = None
    redundancy: str = "N"
    design_margin_pct: float = 0.0
    allow_parallel: bool = True
    max_parallel_modules: int = 8              # assumption; datasheets set the real limit
    include_inactive: bool = False

    def stated_fields(self) -> list[str]:
        defaults = BoardRequirement()
        return [k for k, v in asdict(self).items() if v != getattr(defaults, k)]


@dataclass
class SystemRequirement:
    total_it_load_mw: Optional[float] = None
    rack_density_kw: Optional[float] = None
    distribution_voltage: Optional[str] = None
    coolant_supply_temp_c: Optional[float] = None
    cooling_mode: Optional[str] = None
    redundancy: Optional[str] = None
    certifications: list[str] = field(default_factory=list)
    deployment: Optional[str] = None
    liquid_capture_fraction: Optional[float] = None


# --------------------------------------------------------------------------
# Layer 1: parse and validate
# --------------------------------------------------------------------------

BOARD_NUMERIC = ["input_v_min", "input_v_max", "output_v_min", "output_v_max", "output_power_w",
                 "output_current_a", "peak_power_w", "isolation_v_min", "max_length_mm",
                 "max_width_mm", "max_height_mm", "min_efficiency_pct", "design_margin_pct"]
SYSTEM_NUMERIC = ["total_it_load_mw", "rack_density_kw", "coolant_supply_temp_c", "liquid_capture_fraction"]


def parse_requirements(raw: dict) -> tuple[SystemRequirement, BoardRequirement, dict, list[Issue]]:
    """Validate extracted JSON. Returns (system, board, provenance, issues)."""
    issues: list[Issue] = []
    provenance: dict[str, Optional[str]] = {}
    if not isinstance(raw, dict):
        raise ValueError("RFP requirements must be a JSON object")
    for key in raw:
        if key not in ("system", "board"):
            issues.append(Issue("warning", key, "unknown top-level key ignored"))

    # ---- system ----
    s_raw = raw.get("system") or {}
    sysreq = SystemRequirement()
    for k, v in s_raw.items():
        val, src = _unwrap(v)
        provenance[f"system.{k}"] = src
        if k in SYSTEM_NUMERIC:
            setattr(sysreq, k, _to_float(val, f"system.{k}", issues))
        elif k == "certifications":
            sysreq.certifications = _to_list(val)
        elif hasattr(sysreq, k):
            setattr(sysreq, k, str(val).strip() if val is not None else None)
        else:
            issues.append(Issue("warning", f"system.{k}", "unknown field ignored"))
    sysreq.distribution_voltage = normalise_voltage(sysreq.distribution_voltage)
    if sysreq.rack_density_kw is not None and sysreq.rack_density_kw > 2000:
        issues.append(Issue("warning", "system.rack_density_kw", "above 2000 kW per rack; check kW vs W"))
    if sysreq.total_it_load_mw is not None and sysreq.total_it_load_mw > 5000:
        issues.append(Issue("warning", "system.total_it_load_mw", "above 5000 MW; check MW vs kW"))
    f = sysreq.liquid_capture_fraction
    if f is not None and not 0 < f <= 1:
        issues.append(Issue("error", "system.liquid_capture_fraction", "must be between 0 and 1"))
        sysreq.liquid_capture_fraction = None

    # ---- board ----
    b_raw = raw.get("board") or {}
    board = BoardRequirement()
    for k, v in b_raw.items():
        val, src = _unwrap(v)
        provenance[f"board.{k}"] = src
        if val is None:
            continue
        if k in BOARD_NUMERIC:
            num = _to_float(val, f"board.{k}", issues)
            if num is not None:
                setattr(board, k, num)
        elif k in ("applications", "package_types", "footprints", "mountings"):
            setattr(board, k, _to_list(val))
        elif k in ("allow_parallel", "include_inactive"):
            setattr(board, k, bool(val))
        elif k == "max_parallel_modules":
            n = _to_float(val, f"board.{k}", issues)
            if n is not None:
                board.max_parallel_modules = int(n)
        elif hasattr(board, k):
            setattr(board, k, str(val).strip())
        else:
            issues.append(Issue("warning", f"board.{k}", "unknown field ignored"))

    # one stated voltage means a point requirement
    for lo, hi in (("input_v_min", "input_v_max"), ("output_v_min", "output_v_max")):
        a, b = getattr(board, lo), getattr(board, hi)
        if a is not None and b is None:
            setattr(board, hi, a)
            issues.append(Issue("warning", f"board.{hi}", f"only {lo} stated; treated as a point value"))
        elif b is not None and a is None:
            setattr(board, lo, b)
            issues.append(Issue("warning", f"board.{lo}", f"only {hi} stated; treated as a point value"))
        a, b = getattr(board, lo), getattr(board, hi)
        if a is not None and b is not None and a > b:
            issues.append(Issue("error", f"board.{lo}", f"{lo} ({a}) is greater than {hi} ({b})"))

    for name in ("output_power_w", "output_current_a", "peak_power_w", "input_v_min", "output_v_min"):
        v = getattr(board, name)
        if v is not None and v <= 0:
            issues.append(Issue("error", f"board.{name}", "must be greater than zero"))
    if board.min_efficiency_pct is not None and not 0 < board.min_efficiency_pct <= 100:
        issues.append(Issue("error", "board.min_efficiency_pct", "must be between 0 and 100"))
    if board.design_margin_pct < 0:
        issues.append(Issue("error", "board.design_margin_pct", "cannot be negative"))
    if board.redundancy not in REDUNDANCY_FACTORS:
        issues.append(Issue("error", "board.redundancy", f"must be one of {list(REDUNDANCY_FACTORS)}"))
    if board.isolation is not None:
        board.isolation = board.isolation.lower().replace(" ", "_")
        if board.isolation not in ("required", "not_required"):
            issues.append(Issue("error", "board.isolation", "must be 'required' or 'not_required'"))
    if board.isolation_v_min is not None and board.isolation == "not_required":
        issues.append(Issue("error", "board.isolation_v_min", "conflicts with isolation=not_required"))
    if board.digital is not None and board.digital.upper() not in ("PMBUS", "GCB"):
        issues.append(Issue("error", "board.digital", "must be 'PMBus' or 'GCB'"))
    # sanity: P ~ V*I when all three are stated
    if board.output_power_w and board.output_current_a and board.output_v_max:
        implied = board.output_current_a * board.output_v_max
        implied_lo = board.output_current_a * (board.output_v_min or board.output_v_max)
        if not (implied_lo * 0.75 <= board.output_power_w <= implied * 1.25):
            issues.append(Issue("warning", "board.output_power_w",
                                f"power {board.output_power_w} W is inconsistent with "
                                f"{board.output_current_a} A at {board.output_v_min}-{board.output_v_max} V; check units"))
    return sysreq, board, provenance, issues


# --------------------------------------------------------------------------
# Layer 3: catalogue loading and component matching
# --------------------------------------------------------------------------

def load_catalog(path: str) -> pd.DataFrame:
    """Load and normalise the Flex Power Modules export."""
    try:
        df = pd.read_csv(path) if path.lower().endswith(".csv") else pd.read_excel(path)
    except FileNotFoundError:
        raise CatalogError(f"catalogue file not found: {path}") from None
    except Exception as exc:  # pandas / openpyxl raise many types
        raise CatalogError(f"cannot read catalogue {path}: {exc}") from exc

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise CatalogError(f"catalogue is missing columns: {missing}")

    df = df.copy()
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ("Part Number", "Status", "Package Footprint", "Package Type", "Mounting Type",
                "Paralleling", "Isolation", "Regulation", "Application", "Digital Interfaces"):
        df[col] = df[col].astype("string").str.strip()
    df["Part Number"] = df["Part Number"].map(lambda s: html.unescape(s) if isinstance(s, str) else s)

    # pandas renames the duplicate 'Series' header to 'Series.1'; it holds the part family
    df["family"] = df["Series.1"] if "Series.1" in df.columns else pd.NA

    # Evaluation boards / test boards carry no electrical specs. Identify by missing
    # specs, not by name: two test boards do not contain the word "Evaluation".
    df["is_product"] = df["Output Power (W)"].notna() & df["Input Voltage (min) (V)"].notna()

    # Fixed-output modules have only a typical output voltage, no min/max.
    typ = df["Output Voltage (typical) (V)"]
    df["out_v_lo"] = df["Output Voltage (min) (V)"].fillna(typ)
    df["out_v_hi"] = df["Output Voltage (max) (V)"].fillna(typ)
    df["fixed_output"] = df["Output Voltage (min) (V)"].isna() & typ.notna()

    # 'None' paralleling is stored as a blank cell
    df["parallel_capable"] = df["Paralleling"].notna()
    df["volume_cm3"] = df["Length (mm)"] * df["Width (mm)"] * df["Height (mm)"] / 1000.0

    products = df[df["is_product"]]
    unusable = products[products["out_v_lo"].isna() | products["out_v_hi"].isna()]
    if len(unusable):
        log.warning("%d products have no usable output voltage and can never match", len(unusable))
    dupes = df["Part Number"].duplicated().sum()
    if dupes:
        log.warning("%d duplicate part numbers in catalogue", dupes)
    log.info("catalogue loaded: %d rows, %d products, %d non-product rows",
             len(df), len(products), len(df) - len(products))
    return df


def catalog_vocab(cat: pd.DataFrame) -> dict[str, list[str]]:
    p = cat[cat["is_product"]]
    apps = sorted({t.strip() for s in p["Application"].dropna() for t in str(s).split(",") if t.strip()})
    return {
        "package_types": sorted(p["Package Type"].dropna().unique()),
        "footprints": sorted(p["Package Footprint"].dropna().unique()),
        "mountings": sorted(p["Mounting Type"].dropna().unique()),
        "applications": apps,
        "regulation": sorted(p["Regulation"].dropna().unique()),
    }


@dataclass
class MatchResult:
    status: str                              # "ok" | "no_match" | "invalid_requirements" | "no_constraints"
    candidates: list[dict]
    funnel: list[dict]
    relaxation: dict[str, int]
    near_misses: list[dict]
    notes: list[str]
    issues: list[Issue]


def _app_mask(series: pd.Series, wanted: list[str]) -> pd.Series:
    wanted_l = {w.lower() for w in wanted}

    def hit(s: Any) -> bool:
        if s is None or s is pd.NA or (isinstance(s, float) and math.isnan(s)):
            return False
        return bool({t.strip().lower() for t in str(s).split(",")} & wanted_l)

    return series.map(hit).astype(bool)


def _modules_needed(base: pd.DataFrame, req: BoardRequirement) -> tuple[pd.Series, pd.Series]:
    """Return (modules for load, total modules incl. redundancy). inf means impossible."""
    margin = 1.0 + req.design_margin_pct / 100.0
    n = pd.Series(1.0, index=base.index)
    if req.output_power_w:
        n = np.maximum(n, np.ceil(req.output_power_w * margin / base["Output Power (W)"]))
    if req.output_current_a:
        n = np.maximum(n, np.ceil(req.output_current_a * margin / base["Output Current (A)"]))
    if req.peak_power_w:
        peak = base["Output Power (Peak) (W pk)"]
        n_peak = np.ceil(req.peak_power_w / peak).where(peak.notna(), np.inf)
        n = np.maximum(n, n_peak)
    n = pd.Series(n, index=base.index).astype(float)
    total = REDUNDANCY_FACTORS[req.redundancy](n)
    return n, total


def match_components(cat: pd.DataFrame, req: BoardRequirement, top_n: int = 15,
                     datasheet_template: Optional[str] = None) -> MatchResult:
    vocab = catalog_vocab(cat)
    issues: list[Issue] = []
    req.package_types = _canon(req.package_types, vocab["package_types"], "board.package_types", issues)
    req.footprints = _canon(req.footprints, vocab["footprints"], "board.footprints", issues)
    req.mountings = _canon(req.mountings, vocab["mountings"], "board.mountings", issues)
    if req.regulation:
        req.regulation = (_canon([req.regulation], vocab["regulation"], "board.regulation", issues) or [None])[0]
    unknown_apps = [a for a in req.applications if a.lower() not in {v.lower() for v in vocab["applications"]}]
    for a in unknown_apps:
        issues.append(Issue("error", "board.applications", f"{a!r} not a catalogue value; allowed: {vocab['applications']}"))
    if any(i.level == "error" for i in issues):
        return MatchResult("invalid_requirements", [], [], {}, [], [], issues)

    if not req.stated_fields():
        return MatchResult("no_constraints", [], [], {}, [],
                           ["No board-level requirements were stated; nothing to match."], issues)

    base = cat[cat["is_product"]].copy()
    if not req.include_inactive:
        base = base[base["Status"].str.lower() == "active"]
    n_load, n_total = _modules_needed(base, req)
    base["modules_for_load"] = n_load
    base["modules_total"] = n_total

    # Each requirement becomes a named boolean mask over `base`.
    masks: dict[str, pd.Series] = {}
    if req.input_v_min is not None:
        masks["input_range"] = (base["Input Voltage (min) (V)"] <= req.input_v_min) & \
                               (base["Input Voltage (max) (V)"] >= req.input_v_max)
    if req.output_v_min is not None:
        masks["output_voltage"] = (base["out_v_lo"] <= req.output_v_min) & (base["out_v_hi"] >= req.output_v_max)
    if req.output_power_w or req.output_current_a or req.peak_power_w or req.redundancy != "N":
        cap = base["modules_total"].replace([np.inf], np.nan)
        if req.allow_parallel:
            ok = np.where(base["parallel_capable"], cap <= req.max_parallel_modules, cap == 1)
        else:
            ok = cap == 1
        masks["capacity_and_paralleling"] = pd.Series(ok, index=base.index).fillna(False).astype(bool)
    if req.isolation == "required" or req.isolation_v_min is not None:
        m = base["Isolation"].str.lower().eq("isolated").fillna(False)
        if req.isolation_v_min is not None:
            m &= (base["Isolation Voltage (V)"] >= req.isolation_v_min).fillna(False)
        masks["isolation"] = m
    if req.regulation:
        masks["regulation"] = base["Regulation"].eq(req.regulation).fillna(False)
    if req.digital:
        masks["digital_interface"] = base["Digital Interfaces"].str.contains(
            req.digital, case=False, na=False, regex=False)
    if req.applications:
        masks["application"] = _app_mask(base["Application"], req.applications)
    if req.package_types:
        masks["package_type"] = base["Package Type"].isin(req.package_types).fillna(False)
    if req.footprints:
        masks["footprint"] = base["Package Footprint"].isin(req.footprints).fillna(False)
    if req.mountings:
        masks["mounting"] = base["Mounting Type"].isin(req.mountings).fillna(False)
    for col, lim, name in (("Length (mm)", req.max_length_mm, "max_length"),
                           ("Width (mm)", req.max_width_mm, "max_width"),
                           ("Height (mm)", req.max_height_mm, "max_height")):
        if lim is not None:
            masks[name] = (base[col] <= lim).fillna(False)
    if req.min_efficiency_pct is not None:
        masks["efficiency"] = (base["Typical Efficiency (%)"] >= req.min_efficiency_pct).fillna(False)

    # funnel (cumulative) and single-filter relaxation
    funnel = [{"stage": "active products", "remaining": int(len(base))}]
    running = pd.Series(True, index=base.index)
    for name, m in masks.items():
        running &= m
        funnel.append({"stage": name, "remaining": int(running.sum())})
    final = running
    relaxation = {}
    for name in masks:
        others = pd.Series(True, index=base.index)
        for other, m in masks.items():
            if other != name:
                others &= m
        relaxation[name] = int(others.sum())

    notes = [
        "design_margin_pct is %.0f%%; redundancy is %s." % (req.design_margin_pct, req.redundancy),
        "Module counts from paralleling are arithmetic only; confirm the maximum parallel count, "
        "current-sharing design rules and derating in each datasheet.",
        "Catalogue power ratings are per module at datasheet conditions; confirm thermal derating.",
    ]
    if req.input_v_max and req.input_v_max > cat.loc[cat["is_product"], "Input Voltage (max) (V)"].max():
        notes.append("Required input voltage exceeds every catalogue part; board-level modules cannot "
                     "take this bus directly. An upstream conversion stage is needed.")

    matched = base[final].copy()
    if matched.empty:
        best = max(relaxation, key=relaxation.get) if relaxation else None
        near = []
        if best and relaxation[best] > 0:
            others = pd.Series(True, index=base.index)
            for other, m in masks.items():
                if other != best:
                    others &= m
            near = _rows(base[others].sort_values("Output Power (W)", ascending=False).head(5), datasheet_template,
                         failing=best)
            notes.append(f"Dropping '{best}' alone would give {relaxation[best]} matches.")
        return MatchResult("no_match", [], funnel, relaxation, near, notes, issues)

    matched["eff_rank"] = -matched["Typical Efficiency (%)"].fillna(0)
    matched = matched.sort_values(["modules_total", "eff_rank", "volume_cm3"], na_position="last")
    return MatchResult("ok", _rows(matched.head(top_n), datasheet_template), funnel, relaxation, [], notes, issues)


def _rows(df: pd.DataFrame, template: Optional[str], failing: Optional[str] = None) -> list[dict]:
    out = []
    for _, r in df.iterrows():
        flags = []
        if str(r.get("Regulation")) == "Unregulated/Fixed Ratio":
            flags.append("unregulated: output tracks input; verify conversion ratio at the RFP bus voltage")
        if bool(r.get("fixed_output")):
            flags.append("fixed output voltage (typical value only in catalogue)")
        if r["modules_total"] > 1:
            flags.append(f"needs {int(r['modules_total'])} modules in parallel ({r.get('Paralleling')}); "
                         "verify parallel limit in datasheet")
        if failing:
            flags.append(f"fails: {failing}")
        fam = r.get("family")
        out.append({
            "part_number": r["Part Number"], "component_id": r.get("Component ID"), "family": fam,
            "modules_for_load": r["modules_for_load"], "modules_total": r["modules_total"],
            "input_v": [r["Input Voltage (min) (V)"], r["Input Voltage (max) (V)"]],
            "output_v": [r["out_v_lo"], r["out_v_hi"]],
            "power_w_per_module": r["Output Power (W)"], "peak_w_per_module": r["Output Power (Peak) (W pk)"],
            "current_a_per_module": r["Output Current (A)"], "efficiency_pct": r["Typical Efficiency (%)"],
            "isolation": r["Isolation"], "isolation_v": r["Isolation Voltage (V)"],
            "regulation": r["Regulation"], "digital": r["Digital Interfaces"],
            "package": [r["Package Type"], r["Package Footprint"], r["Mounting Type"]],
            "size_mm": [r["Length (mm)"], r["Width (mm)"], r["Height (mm)"]],
            "applications": r["Application"],
            "datasheet_url": (template.format(family=str(fam).lower(), part=r["Part Number"])
                              if template and isinstance(fam, str) else None),
            "review_flags": flags,
        })
    return out


# --------------------------------------------------------------------------
# Layer 2: system-level checks
# --------------------------------------------------------------------------

def _check(item: str, status: str, detail: str) -> dict:
    return {"item": item, "status": status, "detail": detail}


def configure_system(req: SystemRequirement) -> dict:
    checks, assumptions, gaps = [], [], []
    unverified = [k for k, v in AXIOM_SPEC.items() if not v["verified"]]
    assumptions.append("Axiom limits (" + ", ".join(unverified) + ") are from the brochure and not "
                       "confirmed by Axiom; treat every 'pass' below as provisional.")

    # module count
    cap = AXIOM_SPEC["module_capacity_mw"]["value"]
    modules = None
    if req.total_it_load_mw is None:
        checks.append(_check("module count", "unknown", "total IT load not stated in the RFP"))
    else:
        modules = math.ceil(req.total_it_load_mw / cap)
        checks.append(_check("module count", "review",
                             f"{req.total_it_load_mw} MW / {cap} MW per module = {modules} module(s); "
                             "confirm capacity and N+1 module policy with Axiom"))

    # rack density
    racks = None
    if req.rack_density_kw is not None:
        mx = AXIOM_SPEC["max_rack_density_kw"]["value"]
        if req.rack_density_kw > mx:
            checks.append(_check("rack density", "fail", f"{req.rack_density_kw} kW exceeds {mx} kW per rack"))
            gaps.append(f"rack density {req.rack_density_kw} kW above stated module range")
        else:
            checks.append(_check("rack density", "pass", f"{req.rack_density_kw} kW within up to {mx} kW per rack"))
        if req.total_it_load_mw:
            racks = math.ceil(req.total_it_load_mw * 1000 / req.rack_density_kw)

    # distribution voltage
    if req.distribution_voltage:
        ok = req.distribution_voltage in AXIOM_SPEC["voltages"]["value"]
        checks.append(_check("distribution voltage", "pass" if ok else "fail",
                             f"{req.distribution_voltage} " + ("is" if ok else "is not") +
                             f" in {AXIOM_SPEC['voltages']['value']}"))
        if not ok:
            gaps.append(f"distribution voltage {req.distribution_voltage} not in stated Axiom options")
        if req.distribution_voltage == "480VAC":
            checks.append(_check("RPP voltage", "review",
                                 "Anord Mardix RPP web page lists 400 VAC; confirm a 480 VAC variant exists"))
    # coolant temperature (ambiguous which loop; never hard-fail)
    if req.coolant_supply_temp_c is not None:
        lim = AXIOM_SPEC["max_coolant_supply_c"]["value"]
        status = "pass" if req.coolant_supply_temp_c <= lim else "review"
        checks.append(_check("coolant supply temperature", status,
                             f"{req.coolant_supply_temp_c} C vs about {lim} C; confirm which loop the RFP refers to"))
    # redundancy
    if req.redundancy:
        ok = req.redundancy.upper() in AXIOM_SPEC["redundancy"]["value"]
        checks.append(_check("redundancy", "pass" if ok else "fail",
                             f"{req.redundancy} " + ("is" if ok else "is not") +
                             f" in stated options {AXIOM_SPEC['redundancy']['value']}"))
        if not ok:
            gaps.append(f"redundancy {req.redundancy} not in stated Axiom options")

    # cooling
    cdu_options = []
    if req.cooling_mode and req.cooling_mode.lower() in ("liquid", "hybrid"):
        frac = req.liquid_capture_fraction
        if frac is None:
            frac = 1.0
            assumptions.append("liquid_capture_fraction not stated; assumed 1.0 (all IT heat to liquid), "
                               "which oversizes CDUs. State the real fraction.")
        if req.total_it_load_mw is None:
            checks.append(_check("CDU sizing", "unknown", "total IT load not stated"))
        else:
            heat_kw = req.total_it_load_mw * 1000 * frac
            extra = 1 if (req.redundancy or "").upper().startswith("N+1") else 0
            for c in CDU_CATALOG:
                if req.rack_density_kw and c["name"].startswith("SmartSense") and \
                        req.rack_density_kw * frac > c["firm_kw"]:
                    cdu_options.append({"cdu": c["name"], "feasible": False,
                                        "reason": f"rack heat {req.rack_density_kw * frac:.0f} kW exceeds "
                                                  f"firm capacity {c['firm_kw']:.0f} kW", "source": c["source"]})
                    continue
                units = math.ceil(heat_kw / c["firm_kw"]) + extra
                cdu_options.append({"cdu": c["name"], "feasible": True, "units": units,
                                    "heat_load_kw": round(heat_kw, 1), "firm_kw_each": c["firm_kw"],
                                    "set_redundancy_units_added": extra, "source": c["source"]})
            checks.append(_check("CDU sizing", "review",
                                 "options listed; capacities are quoted at a fixed approach temperature "
                                 "(4-9 C depending on model); confirm against the RFP's temperatures"))
    elif req.cooling_mode:
        checks.append(_check("cooling mode", "review", f"'{req.cooling_mode}' only; no liquid cooling sizing done"))

    # certifications
    cert_rows = []
    for c in req.certifications:
        key = c.strip().upper()
        hit = next((k for k in CERTIFICATIONS_FOUND if k.upper() in key or key in k.upper()), None)
        cert_rows.append({"requested": c, "found_in": CERTIFICATIONS_FOUND.get(hit) if hit else None,
                          "status": "found in reviewed docs" if hit else "not found in reviewed docs; ask Flex"})
        if not hit:
            gaps.append(f"certification '{c}' not found in reviewed documents")

    if req.deployment and req.deployment.lower() == "prefab":
        assumptions.append("Prefab deployment timing (about 39 weeks vs 78 for stick-built) is Flex's own "
                           "modelled comparison; do not cite as a commitment.")
    return {"modules": modules, "racks_estimated": racks, "checks": checks, "cdu_options": cdu_options,
            "certifications": cert_rows, "gaps": gaps, "assumptions": assumptions,
            "axiom_spec_used": AXIOM_SPEC}


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def configure(rfp: dict, catalog: pd.DataFrame, top_n: int = 15,
              datasheet_template: Optional[str] = None) -> dict:
    sysreq, board, provenance, issues = parse_requirements(rfp)
    report: dict[str, Any] = {
        "requirements": {"system": asdict(sysreq), "board": asdict(board)},
        "provenance": provenance, "issues": [asdict(i) for i in issues],
    }
    parse_errors = [i for i in issues if i.level == "error"]
    if parse_errors:
        report["status"] = "invalid_requirements"
        report["message"] = "Fix the listed errors in the extracted requirements, then rerun."
        return _clean(report)

    report["system"] = configure_system(sysreq)
    result = match_components(catalog, board, top_n, datasheet_template)
    report["board"] = {"status": result.status, "candidates": result.candidates, "funnel": result.funnel,
                       "relaxation": result.relaxation, "near_misses": result.near_misses,
                       "notes": result.notes, "issues": [asdict(i) for i in result.issues]}
    sys_fail = any(c["status"] == "fail" for c in report["system"]["checks"])
    review = (result.status in ("no_match", "invalid_requirements") or sys_fail
              or any(i.level == "warning" for i in issues) or bool(report["system"]["gaps"]))
    report["status"] = "needs_review" if review else "ok"
    return _clean(report)


# --------------------------------------------------------------------------
# Self-test and CLI
# --------------------------------------------------------------------------

def selftest(cat: pd.DataFrame) -> int:
    failures = []

    def expect(cond: bool, label: str) -> None:
        print(("PASS " if cond else "FAIL ") + label)
        if not cond:
            failures.append(label)

    products = cat[cat["is_product"]]
    expect(len(cat) - len(products) == 27, "27 non-product rows (panel: 27 evaluation boards)")
    expect(not products["out_v_lo"].isna().any(), "every product has a usable output voltage range")

    r = configure({"board": {"input_v_min": 40, "input_v_max": 60, "output_v_min": 12, "output_v_max": 12,
                              "output_power_w": 1500, "digital": "PMBus", "applications": ["Data Center and Cloud"]}}, cat)
    expect(r["board"]["status"] == "ok" and r["board"]["candidates"], "48V bus to 12V 1.5 kW PMBus returns matches")

    r = configure({"board": {"input_v_min": 40, "input_v_max": 60, "output_v_min": 12, "output_v_max": 12,
                              "output_power_w": 10000, "redundancy": "N+1"}}, cat)
    cands = r["board"]["candidates"]
    expect(bool(cands) and all(c["modules_total"] > 1 for c in cands), "10 kW N+1 needs parallel modules")

    r = configure({"board": {"input_v_min": 800, "input_v_max": 800, "output_v_min": 12, "output_v_max": 12,
                              "output_power_w": 1000}}, cat)
    expect(r["board"]["status"] == "no_match" and r["board"]["relaxation"]["input_range"] > 0,
           "800 V input: no match, input_range identified as the binding filter")

    r = configure({"board": {"input_v_min": 48, "input_v_max": 36}}, cat)
    expect(r["status"] == "invalid_requirements", "inverted input range rejected")

    r = configure({"board": {"input_v_min": 36, "input_v_max": 75, "output_v_min": 12, "output_v_max": 12,
                              "output_power_w": 300, "isolation_v_min": 4000}}, cat)
    expect(all((c["isolation_v"] or 0) >= 4000 for c in r["board"]["candidates"]), "isolation minimum respected")

    r = configure({"board": {"output_power_w": {"value": "300 W", "source": "RFP 3.2"}, "output_v_min": 12}}, cat)
    expect(any(i["field"] == "board.output_power_w" for i in r["issues"]), "string value with units is flagged")

    r = configure({"system": {"total_it_load_mw": 20, "rack_density_kw": 1200, "distribution_voltage": "+/-400 VDC",
                               "redundancy": "2N", "cooling_mode": "liquid", "certifications": ["UL 67", "ISO 9001"]}}, cat)
    st = {c["item"]: c["status"] for c in r["system"]["checks"]}
    expect(st.get("rack density") == "fail" and st.get("redundancy") == "fail", "system limits flagged")
    expect(st.get("distribution voltage") == "pass", "bipolar voltage normalised to ±400VDC")
    expect(any("ISO 9001" in g for g in r["system"]["gaps"]), "unknown certification reported as gap")
    print(f"\n{len(failures)} failure(s)")
    return 1 if failures else 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalog", required=True, help="Flex Power Modules export (.xlsx or .csv)")
    ap.add_argument("--rfp", help="JSON file with extracted RFP requirements")
    ap.add_argument("--out", help="write the report here (default: stdout)")
    ap.add_argument("--top", type=int, default=15, help="max candidates returned")
    ap.add_argument("--datasheet-template",
                    help="optional URL template using {family} and {part}; verify the links before use")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(message)s")

    try:
        cat = load_catalog(args.catalog)
        if args.selftest:
            return selftest(cat)
        if not args.rfp:
            ap.error("--rfp is required unless --selftest is given")
        with open(args.rfp, encoding="utf-8") as fh:
            rfp = json.load(fh)
        report = configure(rfp, cat, args.top, args.datasheet_template)
    except (CatalogError, ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        print(text)
    return 0 if report["status"] in ("ok", "needs_review") else 1


if __name__ == "__main__":
    sys.exit(main())
