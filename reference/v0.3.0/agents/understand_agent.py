"""
Stage 1 — Understand.

Reads raw RFP text and extracts structured requirements. Grounds itself
against the list of fields the engineering rulebook actually requires
(completeness_requirements in engineering_rules.json), rather than
inventing its own idea of "complete" — so the completeness check in
Stage 3 and the extraction here are checking against the same source
of truth.
"""
import re

from agents.base_agent import call_llm_json
from rag.retriever import get_full_rules


def _build_prompt(rfp_text: str, required_fields: list) -> str:
    return f"""You are the "Understand" stage of an engineering RFP-intake system for SpinCo (Flex's Cloud & Power Infrastructure spinout). Read the RFP below and extract structured requirements.

RFP:
\"\"\"
{rfp_text}
\"\"\"

The engineering rulebook requires these fields to be present for the design stage to proceed: {required_fields}.

Respond with ONLY compact JSON, no markdown fences, no commentary, matching exactly this shape:
{{"capacity_mw": <number or null>, "redundancy": "<string>", "voltage_arch": "<string>", "site": "<string>", "timeline": "<string>", "compliance": "<string>", "rack_density_kw": <number or null>, "deployment_preference": "<string>", "completeness_score": <integer 0-100>, "missing_fields": ["..."]}}"""


# Minimum keyword hits required before a layer is considered in scope.
# A single incidental mention is not evidence of scope.
#
# Discovered by testing against the real 101-page Syracuse RFP: the word
# "cooling" appeared exactly once, inside a list of lightning-conductor
# attachment points ("...METAL COOLING TOWERS, HVAC UNITS, LADDERS..."),
# and that one mention put the entire Thermal Management layer in scope.
# It was then classified CTO_AUTOMATE — a false-automation result on a
# layer the RFP never asked about. For comparison, "switchgear" appeared
# 163 times and "breaker" 101 times: what a document is actually about
# announces itself by repetition.
MIN_SCOPE_HITS = 3
# Alternatively, several DISTINCT specific terms is itself evidence, even at
# low counts. A fixed hit count alone cannot span a two-page summary and a
# 101-page specification: the Ft. Lauderdale RFQ names "power distribution
# cabinet" and "power whips" once each, which is genuine distribution scope,
# while Syracuse's single stray "cooling" is not. Distinct terms discriminate
# between the two; raw frequency does not.
MIN_DISTINCT_TERMS = 2

# Terms so specific that one occurrence is genuinely decisive.
DECISIVE_SCOPE_TERMS = {
    "metal clad switchgear", "arc-resistant", "arc resistant",
    "vacuum circuit breaker", "direct-to-chip", "coolant distribution unit",
    "grid-forming", "uninterruptible power supply", "modular power pod",
}


def _count_hits(text: str, keywords: list) -> tuple:
    """Returns (total_hits, matched_terms) for a keyword set."""
    total, matched = 0, []
    for kw in keywords:
        n = text.count(kw)
        if n:
            total += n
            matched.append((kw, n))
    return total, matched


def _detect_layers_in_scope(rfp_text: str, return_evidence: bool = False):
    """Which of the six grid-to-chip layers does this RFP actually cover?

    Scope is decided on WEIGHT OF EVIDENCE, not on the presence of a single
    keyword. A layer qualifies if either:
      (a) its keywords appear at least MIN_SCOPE_HITS times in total, or
      (b) a decisive, unambiguous term appears at all.

    This matters because over-broad scope is not a cosmetic problem: a layer
    wrongly placed in scope gets tiered, and a layer tiered CTO_AUTOMATE is
    routed toward automation. Over-detection therefore manufactures exactly
    the false-CTO outcome the tiering fail-safe exists to prevent.
    """
    t = rfp_text.lower()

    # Strip explicit negation sections before matching. Real RFPs say what
    # they are NOT asking for, and those statements must not be read as
    # inclusions.
    for marker in ("--- not specified", "not specified in this rfp",
                   "not specified in this rfq", "--- not applicable"):
        idx = t.find(marker)
        if idx != -1:
            t = t[:idx]

    layer_keywords = {
        1: ["onsite energy generation", "onsite generation", "microgrid",
            "battery energy storage", "grid-forming", "grid outage",
            "utility interconnection", "small modular reactor",
            "grid interface", "utility feeder", "interconnect"],
        2: ["switchgear", "substation", "protective relay", "protection panel",
            "circuit breaker position", "vacuum circuit breaker", "e-house",
            "medium voltage", "arc-resistant", "arc resistant", "metal clad switchgear"],
        3: ["busway", "power distribution cabinet", "power distribution unit",
            "distribution infrastructure", "power whip", "rpp",
            "modular power pod", "prefabricated", "modular systems"],
        4: ["uninterruptible power supply", "rack-mounted pdu", "rack mounted pdu",
            "power shelf", "dc-dc", "rack power", "equipment rack",
            "rack-level", "rack level", "vpd", "800vdc", "48vdc"],
        5: ["liquid cooling", "liquid cooled", "liquid-cooled", "cdu", "cold plate",
            "direct-to-chip", "coolant distribution unit", "chiller",
            "cooling capacity", "rack cooling"],
        6: ["compute tray", "rack-scale integration", "rack scale integration",
            "gpu", "ai inference", "ai training"],
    }

    scope, evidence = [], {}
    for n, kws in layer_keywords.items():
        total, matched = _count_hits(t, kws)
        decisive = [k for k, _ in matched if k in DECISIVE_SCOPE_TERMS]
        distinct = len(matched)
        in_scope = (total >= MIN_SCOPE_HITS
                    or distinct >= MIN_DISTINCT_TERMS
                    or bool(decisive))
        if in_scope:
            scope.append(n)
        evidence[n] = {
            "hits": total,
            "matched_terms": sorted(matched, key=lambda x: -x[1])[:5],
            "decisive_terms": decisive,
            "in_scope": in_scope,
            "distinct_terms": distinct,
            "basis": ("decisive term" if decisive
                      else f"{distinct} distinct terms" if distinct >= MIN_DISTINCT_TERMS
                      else f"{total} hits (threshold {MIN_SCOPE_HITS})"),
        }

    if not scope:
        scope = [1, 2, 3, 4, 5, 6]
        for n in evidence:
            evidence[n]["basis"] = "no layer met threshold; defaulting to full scope"

    return (scope, evidence) if return_evidence else scope


def _mock_extract(rfp_text: str, required_fields: list) -> dict:
    """Deterministic, input-driven extraction used when LLM_MODE=mock.

    Vocabulary was deliberately broadened after testing against real public
    RFPs. The original patterns only recognised data-centre phrasing
    ("IT capacity: 48 MW", "Rack density: 120kW"); a real MV switchgear
    procurement speaks a different language entirely (15kV, 13.2 kV feeders,
    vacuum circuit breaker positions, 750 MCM, arc-resistant Type 2B), and
    every field came back empty. Both vocabularies are now handled.
    """

    def find(pattern, text=rfp_text, group=1, cast=str, default=None):
        m = re.search(pattern, text, re.IGNORECASE)
        if not m:
            return default
        try:
            return cast(m.group(group))
        except (ValueError, IndexError):
            return default

    # --- capacity: "48 MW", "greater than 100 megawatts", "500 MW+" ---
    capacity_mw = find(r"([\d.]+)\s*MW", cast=float)
    if capacity_mw is None:
        capacity_mw = find(r"([\d.]+)\s*megawatt", cast=float)

    # --- redundancy: 2N / N+1, plus prose forms ---
    redundancy_matches = re.findall(r"(2N|N\+1|N\+2)", rfp_text, re.IGNORECASE)
    redundancy = " / ".join(sorted(set(m.upper() for m in redundancy_matches))) or None
    if redundancy is None and re.search(r"redundant backup power|redundant", rfp_text, re.IGNORECASE):
        redundancy = "redundant (class not specified)"

    # --- voltage architecture: data-centre AND electrical-equipment forms ---
    voltage_arch = find(r"(800\s*VDC|415\s*VAC|48\s*VDC)")
    voltage_class_kv = find(r"([\d.]+)\s*kV", cast=float)
    voltage_low_v = find(r"([\d]{3})\s*V\b", cast=float)
    if voltage_arch is None:
        if voltage_class_kv is not None:
            voltage_arch = f"{voltage_class_kv}kV medium voltage"
        elif voltage_low_v is not None:
            voltage_arch = f"{int(voltage_low_v)}V low voltage"

    # --- equipment-specific fields ---
    # A bare kVA figure is NOT a UPS rating. On the real Syracuse RFP this
    # matched "112.5KVA 13200V -208/120V" from a single-line diagram — a
    # distribution transformer, not a UPS. A false UPS rating would feed the
    # solver and produce a confident wrong answer, so UPS context is required
    # within a short window of the figure.
    ups_kva = None
    for m in re.finditer(r"([\d.]+)\s*[-\s]?kVA", rfp_text, re.IGNORECASE):
        window = rfp_text[max(0, m.start() - 120): m.end() + 120].lower()
        if "ups" in window or "uninterruptible" in window:
            try:
                ups_kva = float(m.group(1))
            except ValueError:
                ups_kva = None
            break
    # Real documents write this as "eighteen (18) 15kV vacuum circuit breaker".
    # The parenthesised digits are the reliable signal; the spelled-out word
    # varies. Discovered on the real Syracuse RFP, where the original pattern
    # matched nothing at all.
    breaker_positions = find(r"\((\d+)\)\s*[\d.]*\s*kV\s+vacuum circuit breaker", cast=int)
    if breaker_positions is None:
        breaker_positions = find(r"(\d+)\s*x?\s*[\d.]*\s*kV\s+vacuum circuit breaker positions", cast=int)
    if breaker_positions is None:
        breaker_positions = find(r"Breaker positions:\s*(\d+)", cast=int)
    arc_resistant = find(r"(Arc[- ]resistant\s+Type\s+\w+)")
    rack_count = find(r"\((\d+)\)\s*data center equipment racks", cast=int)
    if rack_count is None:
        rack_count = find(r"(\d+)\s*data center equipment racks", cast=int)
    if rack_count is None and re.search(r"ten\s*\(?10?\)?\s*data center equipment racks", rfp_text, re.IGNORECASE):
        rack_count = 10

    onsite_generation = bool(re.search(r"onsite energy generation|onsite generation|microgrid|battery energy storage",
                                       rfp_text, re.IGNORECASE)) or None

    # Branch circuit provision — needed by the solver (M13) for LV
    # distribution arithmetic. Written to match phrasing seen in real
    # public RFQs, e.g. "twenty-four (24) 208V power whips".
    branch_circuits = find(r"\((\d+)\)\s*\d*\s*V?\s*power whips", cast=int)
    if branch_circuits is None:
        branch_circuits = find(r"(\d+)\s*(?:x\s*)?\d*\s*V?\s*(?:power whips|branch circuits)", cast=int)
    branch_circuit_voltage = find(r"(\d{3})\s*V\s*power whips", cast=float)
    if branch_circuit_voltage is None:
        branch_circuit_voltage = find(r"branch circuits?.*?(\d{3})\s*V", cast=float)

    # --- rack density: only meaningful for data-hall scopes ---
    rack_density = find(r"(\d+)\s*[-\u2013]?\s*\d*\s*kW per rack", cast=float)

    site = find(r"Site:\s*(.+)")
    timeline = find(r"Timeline:\s*(.+)")
    compliance = find(r"Compliance:\s*(.+)")
    if compliance is None:
        std_hits = re.findall(r"(IEEE\s+C?[\d.]+|NFPA\s+\d+|NEC|ANSI|NEMA\s+[A-Z]{2}[- ]?\d*|UL\s+\d+|IEC\s+\d+)",
                              rfp_text)
        if std_hits:
            seen, ordered = set(), []
            for s in std_hits:
                k = s.upper()
                if k not in seen:
                    seen.add(k); ordered.append(s)
            compliance = ", ".join(ordered[:8])

    deployment_preference = find(r"Deployment preference:\s*(.+)")

    layers_in_scope, scope_evidence = _detect_layers_in_scope(rfp_text, return_evidence=True)

    # Completeness is judged only against fields RELEVANT to the detected
    # scope. Penalising a switchgear RFP for omitting rack density would be
    # meaningless — it was never in scope.
    scope_relevant = {
        "capacity_mw": bool({1, 6} & set(layers_in_scope)),
        "redundancy": True,
        "voltage_arch": True,
        "site": True,
        "timeline": True,
        "rack_density_kw": 5 in layers_in_scope and 6 in layers_in_scope,
    }
    values = {
        "capacity_mw": capacity_mw, "redundancy": redundancy, "voltage_arch": voltage_arch,
        "site": site, "timeline": timeline, "rack_density_kw": rack_density,
    }
    applicable = [f for f in required_fields if scope_relevant.get(f, True)]
    missing = [f for f in applicable if not values.get(f)]
    completeness_score = round(100 * (len(applicable) - len(missing)) / max(len(applicable), 1))

    return {
        "capacity_mw": capacity_mw,
        "redundancy": redundancy,
        "voltage_arch": voltage_arch,
        "site": site,
        "timeline": timeline,
        "compliance": compliance,
        "rack_density_kw": rack_density,
        "deployment_preference": deployment_preference,
        "voltage_class_kv": voltage_class_kv,
        "ups_kva": ups_kva,
        "breaker_positions": breaker_positions,
        "arc_resistant": arc_resistant,
        "rack_count": rack_count,
        "onsite_generation": onsite_generation,
        "branch_circuits": branch_circuits,
        "branch_circuit_voltage": branch_circuit_voltage,
        "layers_in_scope": layers_in_scope,
        "scope_evidence": scope_evidence,
        "completeness_score": completeness_score,
        "missing_fields": missing,
        "fields_out_of_scope": [f for f in required_fields if f not in applicable],
    }


def run(rfp_text: str) -> dict:
    rules = get_full_rules()
    required_fields = rules["completeness_requirements"]

    result = call_llm_json(
        _build_prompt(rfp_text, required_fields),
        _mock_extract, rfp_text, required_fields,
    )

    missing_note = (
        f"Flagged {len(result['missing_fields'])} missing/ambiguous field(s): {', '.join(result['missing_fields'])}."
        if result.get("missing_fields") else "All required fields were found in the RFP."
    )
    result["explanation"] = (
        f"Extracted requirements against the engineering rulebook's required-field list "
        f"({', '.join(required_fields)}). {missing_note} "
        f"Completeness score: {result['completeness_score']}%."
    )
    result["evidence"] = [
        {"source": "engineering_rules.json:completeness_requirements", "detail": required_fields}
    ]
    return result
