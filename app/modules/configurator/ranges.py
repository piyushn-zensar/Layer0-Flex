"""Published-ratings search (P-62): a requested component's stated values against the spec tables of the product
families proposed for it (catalog.specs: busway, LV switchgear and switchboards, PDU and RPP, CDUs, MV switchgear).
Code only, after one frozen model call that reads the values (agent.range_inputs; numbers as written, checked in the
requirement text, units converted by catalog.convert_unit).

Rules per rating (RULE): at_least (the product's highest published value must reach the requirement: current, kA,
capacity, flow), within (the requirement must sit inside the product's published range: voltage, frequency,
temperatures), at_most (the product's value must not exceed it: size, weight, own power draw, approach temperature),
and parsed text (IP rating: both digits at least; form of separation: at least the form asked; standards: the same
standard or a more specific part). Any other text rating is shown, not judged. A short-time withstand stated for
fewer seconds than asked does not count.

Each variant of a family is checked; a variant that publishes none of the asked ratings is not a candidate. Outcome
(as the DC/DC search): match (a variant meets every stated value, at least two compared), insufficient_information (none fails, but the
published data do not state some values), near_match (the best fails one; shown for review, never a match),
no_match (with the reason). Brochure ratings are ranges per family or variant, unverified until the unit confirms
them: a match here is a candidate family, not an orderable configuration.
"""
import re
from urllib.parse import quote

from app.modules.catalog import service as catalog

AT_LEAST = {"rated_current", "tap_off_current", "short_time_withstand", "peak_withstand", "breaking_capacity",
            "cooling_capacity", "flow_rate", "insulation_voltage", "impulse_withstand_voltage", "output_power", "altitude"}
WITHIN = {"rated_voltage_ac", "rated_voltage_dc", "frequency", "supply_temperature", "return_temperature",
          "operating_temperature", "output_voltage"}
AT_MOST = {"height", "width", "depth", "weight", "power_consumption", "approach_temperature"}
JUDGED_TEXT = {"ip_rating", "form_of_separation", "standards"}
RULE_WORDS = {"at_least": "at least", "within": "within the published range", "at_most": "at most"}
FORMS = ["1", "2a", "2b", "3a", "3b", "4a", "4b"]
NUMBER = re.compile(r"(\d[\d,]*(?:\.\d+)?)")
PAIR = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*([A-Za-zº°%/³-]*[A-Za-z%])?")   # a number and the unit right after it


def rule(attribute: str) -> str:
    return "at_least" if attribute in AT_LEAST else "within" if attribute in WITHIN else \
        "at_most" if attribute in AT_MOST else "text"


def _digits(s: str) -> str:
    return re.sub(r"[^\d]", "", s)


def parse(raw: dict, items: list[dict]) -> tuple[list[dict], dict, list[dict]]:
    """The agent's constraints -> (constraints in base units, provenance, issues). A number not in its requirements'
    text is dropped (the model never converts); a unit that does not fit the rating is dropped with the reason."""
    attrs = catalog.spec_attributes()
    texts = {i["req_id"]: (i["text"] + " " + i["quote"]).replace(",", "") for i in items}
    out, prov, issues = [], {}, []
    for n, c in enumerate(raw.get("constraints", [])):
        name, stated = c["attribute"], c["as_written"]
        if name not in attrs:
            issues.append({"field": name, "message": "not a rating name", "req_ids": c["req_ids"]})
            continue
        kind, base = attrs[name]
        entry = {"attribute": name, "rule": rule(name), "stated": stated, "req_ids": c["req_ids"], "source": c["source"]}
        if kind == "range":
            # each number with the unit written after it ("30 to 45 °C": the range's unit); "65 kA for 1 s" keeps 65 kA
            pairs = PAIR.findall(stated)
            fits = lambda u: bool(u) and catalog.convert_unit(1.0, u, base)[0] is not None  # noqa: E731
            pairs = [(x, u if fits(u) else next((v for _, v in pairs[k + 1:] if fits(v)), u)) for k, (x, u) in enumerate(pairs)]
            vals = [(x, catalog.convert_unit(float(x.replace(",", "")), u, base)) for x, u in pairs]
            good = [(x, v) for x, (v, _) in vals if v is not None][:2]
            said = " ".join(texts.get(r, "") for r in c["req_ids"])
            if not pairs or not all(_written(x, said) for x, _ in good or pairs):
                issues.append({"field": name, "message": f"{stated!r} is not in the text of {', '.join(c['req_ids'])}",
                               "req_ids": c["req_ids"]})
                continue
            if not good:
                issues.append({"field": name, "message": next(w for _, (_, w) in vals if w), "req_ids": c["req_ids"]})
                continue
            vals = [(v, None) for _, v in good]
            entry |= {"lo": min(v for v, _ in vals), "hi": max(v for v, _ in vals), "unit": base,
                      "seconds": _seconds(stated)}
        out.append(entry)
        prov[f"spec.{name}.{n}"] = {"req_ids": c["req_ids"], "source": c["source"], "stated": stated, "unit": None,
                                    "interpreted": False}
    return out, prov, issues


def _written(number: str, text: str) -> bool:
    """The number itself is in the text ("2500" for "2,500 A"; "2.5" is not in "2500 A")."""
    return re.search(rf"(?<![\d.]){re.escape(number.replace(',', ''))}(?![\d])", text) is not None


def _seconds(text: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:s\b|sec|second)", text or "")
    return float(m.group(1)) if m else None


def _ip(text: str) -> tuple[int, int] | None:
    m = re.search(r"IP\s*(\d)(\d)", text or "", re.I)
    return (int(m.group(1)), int(m.group(2))) if m else None


def _form(text: str) -> int | None:
    m = re.search(r"form\s*(\d[ab]?)", text or "", re.I)
    if not m:
        return None
    f = m.group(1).lower()
    return FORMS.index(f) if f in FORMS else FORMS.index(f + "a") if f + "a" in FORMS else None


def _std(text: str) -> list[str]:
    return [" ".join(s.upper().split()) for s in re.findall(r"(?:UL|IEC|EN|BS EN|IEEE|NEMA|ANSI)\s*[\d.\-]+[A-Z]?", text or "", re.I)]


def check(c: dict, values: list[dict]) -> tuple[str, str, dict | None]:
    """One stated value against an item's published values of that rating -> (met | not_met | unknown | shown, note,
    the published value used)."""
    if not values:
        return "unknown", "not in the published data", None
    r = c["rule"]
    if r == "text":
        name = c["attribute"]
        for v in values:
            pub = v["text"] or v["quote"]
            if name == "ip_rating":
                need, have = _ip(c["stated"]), _ip(pub)
                if need and have:
                    ok = have[0] >= need[0] and have[1] >= need[1]
                    return ("met" if ok else "not_met"), f"published {pub}", v
            elif name == "form_of_separation":
                need, have = _form(c["stated"]), _form(pub)
                if need is not None and have is not None:
                    return ("met" if have >= need else "not_met"), f"published {pub}", v
            elif name == "standards":
                need = _std(c["stated"])
                have = _std(pub)
                if need and have:
                    ok = all(any(n == h or n.startswith(h + "-") or n.startswith(h + " ") for h in have) for n in need)
                    return ("met" if ok else "not_met"), f"published {pub}", v
        return "shown", "compare by hand: " + "; ".join(v["text"] or v["quote"] for v in values), values[0]
    best, note = None, ""
    for v in values:
        lo = v.get("min_base")
        hi = v.get("max_base")
        if lo is None and hi is None:
            continue
        top = hi if hi is not None else lo
        bottom = lo if lo is not None else (0.0 if r == "within" else hi)
        if r == "at_least":
            ok = top >= c["hi"] - 1e-9
            secs = c.get("seconds")
            pub_secs = _seconds(v["conditions"]) or _seconds(v["text"])
            if ok and c["attribute"] == "short_time_withstand" and secs and pub_secs and pub_secs < secs:
                ok, note = False, f"rated for {pub_secs:g} s, the RFP asks {secs:g} s"
        elif r == "within":
            ok = bottom <= c["lo"] + 1e-9 and top >= c["hi"] - 1e-9
        else:
            ok = bottom <= c["hi"] + 1e-9
        if ok:
            return "met", _value(v), v
        best = best or v
    return ("not_met", note or _value(best), best) if best else ("unknown", "not in the published data", None)


def _value(v: dict) -> str:
    lo, hi = v.get("min"), v.get("max")
    num = f"{hi:g}" if lo is None or lo == hi else f"{lo:g} to {hi:g}" if hi is not None else f"{lo:g}"
    return f"{num} {v['unit']}".strip() + (f" ({v['conditions']})" if v.get("conditions") else "")


def search(constraints: list[dict], families: list[str], specs: list[dict]) -> list[dict]:
    """The spec items of the proposed families, best first. Each stated value is compared only with the families the
    matcher proposed for that value's own requirements (constraint["families"], else all `families`); an item is a
    candidate when it publishes at least half of the values compared with it (a busway that publishes one of six
    power-block ratings is no candidate). Results for values not compared with the item read "not compared"."""
    out = []
    for item in specs:
        fam = item["family_key"].split("/", 1)[0]
        if fam not in families:
            continue
        by = {}
        for a in item["attributes"]:
            by.setdefault(a["name"], []).append(a)
        results = []
        for c in constraints:
            if fam not in (c.get("families") or families):
                results.append({"attribute": c["attribute"], "stated": c["stated"], "status": "not_compared",
                                "published": "not proposed for this requirement", "citation": None})
                continue
            status, note, used = check(c, by.get(c["attribute"], []))
            results.append({"attribute": c["attribute"], "stated": c["stated"], "status": status, "published": note,
                            "citation": f"{used['source']['file']}, p. {used['page']}" if used else None})
        compared = [r for r in results if r["status"] != "not_compared"]
        known = [r for r in compared if r["status"] in ("met", "not_met")]
        if not known or len(known) * 2 < len(compared):
            continue
        out.append({"spec_id": item["spec_id"], "family_key": item["family_key"], "variant": item["variant"],
                    "verified": item.get("verified", False), "link": "/catalog/product?part=" + quote(item["family_key"], safe=""),
                    "results": results, "compared": len(compared), "fails": sum(r["status"] == "not_met" for r in results),
                    "unknowns": sum(r["status"] == "unknown" for r in results)})
    return sorted(out, key=lambda x: (x["fails"], x["unknowns"], -x["compared"], x["family_key"], x["variant"]))


def dedupe(constraints: list[dict]) -> list[dict]:
    """The same value stated by several requirements counts once, with all their IDs."""
    out: dict[tuple, dict] = {}
    for c in constraints:
        key = (c["attribute"], c.get("lo"), c.get("hi"), c["stated"].strip().lower() if c["rule"] == "text" else None)
        if key in out:
            out[key]["req_ids"] = list(dict.fromkeys(out[key]["req_ids"] + c["req_ids"]))
        else:
            out[key] = dict(c)
    return list(out.values())


def explain(group: dict) -> dict:
    """A spec_range component's run (service.plan) -> the same shape as explain.explain for the DC/DC search."""
    run, refs = group["run"], group["requirements"]
    cs, cands = run["constraints"], run["candidates"]
    label = lambda a: a.replace("_", " ")  # noqa: E731
    met_all = [x for x in cands if x["fails"] == 0 and x["unknowns"] == 0]
    if not cs:
        outcome, reason = "insufficient_information", ("The requirements state no rating the published data cover for "
                                                       f"{', '.join(run['families'])}.")
    elif met_all and met_all[0]["compared"] < 2:   # one rating does not select a product
        x = met_all[0]
        r = next(r for r in x["results"] if r["status"] == "met")
        outcome = "insufficient_information"
        reason = (f"Only one stated value could be compared: {label(r['attribute'])} {r['stated']}, which {x['family_key']} "
                  f"meets ({r['published']}). One rating does not select a product; the unit confirms the rest.")
    elif met_all:
        outcome = "match"
        n = met_all[0]["compared"]
        reason = (f"{len(met_all)} published variant(s) meet every stated value compared ({n} value{'s' if n != 1 else ''}; "
                  f"{', '.join(sorted({x['family_key'] for x in met_all}))}). "
                  "Brochure ratings, unverified until the unit confirms them; a candidate family, not an orderable configuration.")
    elif not cands:
        outcome = "insufficient_information"
        reason = (f"No published variant of the proposed families ({', '.join(run['families'])}) states enough of the asked "
                  f"ratings ({', '.join(sorted({label(c['attribute']) for c in cs}))}); the unit confirms them.")
    elif cands[0]["fails"] == 0:
        best = cands[0]
        gaps = [label(r["attribute"]) for r in best["results"] if r["status"] == "unknown"]
        outcome = "insufficient_information"
        reason = (f"No stated value fails for {best['family_key']} ({best['variant']}), but the published data do not state: "
                  f"{', '.join(gaps)}. The unit confirms these.")
    elif cands[0]["fails"] == 1:
        best = cands[0]
        fail = next(r for r in best["results"] if r["status"] == "not_met")
        outcome = "near_match"
        reason = (f"No published variant meets every stated value. Closest: {best['family_key']} ({best['variant']}), which "
                  f"fails the {label(fail['attribute'])} ({fail['stated']} asked, {fail['published']}). Shown for review, not a match.")
    else:
        outcome = "no_match"
        reason = (f"No published variant of {', '.join(run['families'])} meets the stated values"
                  + f"; the closest fails {cands[0]['fails']}.")
    best = (met_all or cands or [None])[0]
    per_req = []
    for r in refs:
        mine = [x for x in (best["results"] if best else []) if any(c["req_ids"] and r["req_id"] in c["req_ids"]
                                                                     for c in cs if c["stated"] == x["stated"])]
        base = {"req_id": r["req_id"], "parent": r.get("parent"), "text": r["text"], "document": r.get("document"),
                "page": r.get("page"), "fields": [x["attribute"] for x in mine], "interpreted": []}
        if not mine:
            per_req.append(base | {"status": "cannot_assess", "why": "Not a published-rating input; for engineering review."})
        elif any(x["status"] == "not_met" for x in mine):
            bad = [x for x in mine if x["status"] == "not_met"]
            per_req.append(base | {"status": "not_satisfied", "why": "; ".join(
                f"{label(x['attribute'])}: {x['stated']} asked, {best['family_key']} {x['published']}" for x in bad)})
        elif all(x["status"] == "met" for x in mine):
            per_req.append(base | {"status": "satisfied", "why": "; ".join(
                f"{label(x['attribute'])}: {x['stated']} asked, {best['family_key']} {x['published']}" for x in mine)
                + ". Published rating, unverified."})
        else:
            per_req.append(base | {"status": "cannot_assess", "why": "; ".join(
                f"{label(x['attribute'])}: {x['published']}" for x in mine if x["status"] != "met")})
    top = cands[:3]
    name = lambda x: x["family_key"].split("/", 1)[1] + ("" if x["variant"] in x["family_key"] else f" · {x['variant']}")  # noqa: E731
    comparison = {"parts": [name(x)[:60] for x in top],
                  "links": [x["link"] for x in top],
                  "rows": [{"constraint": f"{label(c['attribute'])} ({RULE_WORDS.get(c['rule'], 'compared by hand')})",
                            "required": c["stated"], "req_ids": c["req_ids"],
                            "values": [f"{r['status'].replace('_', ' ')}: {r['published']}" for r in
                                       (next(y for y in x["results"] if y["stated"] == c["stated"] and y["attribute"] == c["attribute"]) for x in top)]}
                           for c in cs]} if top else None
    unverified = sorted({x["family_key"] for x in top if not x["verified"]})
    checks = [{"check": "Published ratings unverified", "status": "open",
               "detail": "Values read from brochures and product pages by a model pass, kept only when quoted on the page; "
                         f"not yet confirmed by the unit: {', '.join(unverified) or 'none'}."}] if unverified else []
    checks.append({"check": "Configuration", "status": "open", "detail": "Brochure ratings are ranges per family or variant; "
                   "the unit confirms an orderable configuration (ratings together, options, conditions)."})
    checks += [{"check": f"{label(r['attribute'])} compared by hand", "status": "not_supported", "detail": r["published"]}
               for r in (best["results"] if best else []) if r["status"] == "shown"]
    checks += [{"check": "Unit or value issue", "status": "open", "detail": f"{i['field']}: {i['message']}"} for i in run["issues"]]
    return {"outcome": outcome, "reason": reason, "requirements": per_req, "spec_candidates": cands[:10], "constraints": cs,
            "comparison": comparison, "inputs": run["inputs"], "missing": [], "unit_issues": run["issues"],
            "assumptions": [{"item": "Rule", "value": f"{label(c['attribute'])}: {RULE_WORDS.get(c['rule'], 'compared by hand')}",
                             "basis": "configurator rule for published ratings"} for c in cs],
            "checks": checks, "families": run["families"]}
