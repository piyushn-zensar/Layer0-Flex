"""
Stage 2 — Draft System Design, branching by automation tier.

Tier classification (agents/tier_classifier.py) has already run by the
time this module executes, and its result decides which of three
execution paths a given layer takes:

- CTO_AUTOMATE: the model (or, in mock mode, deterministic logic)
  drafts a spec + justification. Catalog-style BOM line items are
  attached as a stand-in for a real aPriori/QuoteWin catalog lookup
  (clearly labeled as pending that connection — see connectors/).
- ETO_GUIDED: NO model call for the bespoke portion. Standard
  sub-items are auto-priced deterministically; the bespoke remainder
  is captured as a basis-of-design wrapper and routed to the relevant
  brand's design engineers. The system never claims to have designed
  the bespoke part.
- ETO_EXCEPTION: NO model call at all. A deterministic margin-
  protected price placeholder is applied and an intake ticket is
  constructed for direct routing to specialist engineers.

This is a deliberate architectural choice, not just an implementation
detail: only CTO_AUTOMATE layers ever ask a model to draft a design.
ETO_GUIDED and ETO_EXCEPTION are handled entirely by deterministic
templating, so there is no path by which the system can hallucinate a
bespoke design for genuinely novel or margin-protected work — directly
answering the panel's "margin risk on high-complexity grid interfaces"
concern.

Brand selection is delegated entirely to
tier_classifier.run()'s hinted_brands per layer — this module no
longer duplicates that logic. That consolidation was flagged as the
intended next step in tier_classifier.py's original docstring; it is
done as of this change.

KNOWN FRAGILITY, carried forward (not introduced here): validation_agent.py's
R-002 cooling check does a literal substring match for "direct-to-chip"
against a layer's brand/spec text. This mock path preserves that exact
phrase for Layer 5 at high density, matching the pre-tiering behavior.
This substring-matching approach is fragile — a structured field (e.g.
a `cooling_type` key) would be more robust — and is worth hardening
when validation_agent.py is next updated for the sourced NEC/IEC rules
(the next step in the agreed sequence), not fixed here to keep this
change scoped to design_agent.py.
"""
from agents.base_agent import call_llm_json
from agents.tier_classifier import run as classify_tiers
from rag.retriever import retrieve

# Deterministic, catalog-style BOM line item templates per layer —
# a placeholder pending a real aPriori/QuoteWin catalog connection.
BOM_TEMPLATES = {
    1: ["Grid interface conversion unit", "Control & monitoring module"],
    2: ["Switchgear frame", "Circuit breaker set", "Protection relay panel"],
    3: ["Busway run", "PDU unit", "RPP panel"],
    4: ["Power shelf", "DC-DC converter module", "Rack power distribution unit"],
    5: ["Cold plate assembly", "Coolant distribution unit (CDU)", "Coolant manifold kit"],
    6: ["Compute tray", "Rack integration hardware", "Cable management kit"],
}

# Deterministic "standard, auto-priceable" sub-items within an
# otherwise bespoke ETO_GUIDED layer — mirrors the component_overrides
# keywords in spinco_layers.json (standard enclosure, busbar, breaker).
STANDARD_SUBITEM_TEMPLATES = {
    2: ["Standard enclosure", "Standard busbar", "Standard breaker"],
    3: ["Standard busbar"],
}

_CAPTURE_FIELDS = ("capacity_mw", "redundancy", "voltage_arch", "site", "timeline", "compliance")


def _build_retrieval_queries(req: dict) -> list:
    queries = []
    if req.get("voltage_arch"):
        queries.append(f"voltage architecture {req['voltage_arch']}")
    if req.get("rack_density_kw"):
        queries.append(f"rack density {req['rack_density_kw']} kW cooling")
    if req.get("redundancy"):
        queries.append(f"redundancy {req['redundancy']} utility protection")
    if req.get("deployment_preference"):
        queries.append(f"deployment {req['deployment_preference']} modular")
    return queries or ["general SpinCo layer selection"]


def _build_auto_prompt(req: dict, auto_layers: list, retrieved: list) -> str:
    return f"""You are the "Draft System Design" stage, drafting ONLY the layers already tier-classified as CTO_AUTOMATE (standardized, catalog-configurable). Other layers are handled deterministically elsewhere and are not your concern — do not draft them.

Requirements: {req}

Layers to draft: {auto_layers}

Retrieved context: {retrieved}

Respond with ONLY compact JSON, no markdown fences, no commentary, matching exactly this shape:
{{"layers": [{{"n": <n>, "spec": "<one short sentence, under 20 words, containing the literal phrase 'direct-to-chip' if this is Layer 5 and rack density is 100kW or above>", "justification": "<which requirement drove this, under 20 words>"}}, ... one entry per layer listed above]}}"""


def _mock_auto_layers(req: dict, auto_layers: list, retrieved: list) -> dict:
    """Deterministic drafting for CTO_AUTOMATE layers only — used when
    LLM_MODE=mock. Mirrors the pre-tiering mock logic for these layers."""
    density = req.get("rack_density_kw") or 0
    out = []
    for layer in auto_layers:
        n = layer["n"]
        if n == 2:
            spec, just = "Standard MV/LV switchgear per facility electrical requirement", "No utility-grade 2N redundancy flagged"
        elif n == 3:
            spec, just = "Prefabricated modular power pod distribution", "Standardized SpinCo product line"
        elif n == 4:
            spec, just = "Standard rack power shelves and board-level DC-DC", "No 800VDC requirement at rack level"
        elif n == 5:
            if density >= 100:
                spec, just = "Direct-to-chip liquid cooling, mandatory above 100kW/rack", f"Rack density {density}kW exceeds 100kW threshold"
            elif density >= 35:
                spec, just = "Hybrid air/liquid cooling acceptable at this density", f"Rack density {density}kW is in the 35-100kW hybrid-acceptable range"
            else:
                spec, just = "Air cooling may suffice; confirm with thermal engineering", f"Rack density {density}kW is below the 35kW hybrid threshold"
        elif n == 6:
            spec, just = "Rack-scale integration of compute, power, and cooling", "Scope includes rack-scale integration"
        else:
            spec, just = f"Standard {layer['name']} configuration", "Tiered CTO_AUTOMATE"
        out.append({"n": n, "spec": spec, "justification": just})
    return {"layers": out}


def _cto_automate_layer(n: int, name: str, brand_str: str, spec: str, justification: str) -> dict:
    return {
        "n": n, "name": name, "tier": "CTO_AUTOMATE", "brand": brand_str,
        "spec": spec, "justification": justification,
        "bom_line_items": [
            {"item": item, "qty": 1, "pricing_status": "auto_priced_pending_aPriori_connection"}
            for item in BOM_TEMPLATES.get(n, [f"{name} component"])
        ],
    }


def _eto_guided_layer(n: int, name: str, brand_str: str, tier_reason: str, req: dict) -> dict:
    standard_items = STANDARD_SUBITEM_TEMPLATES.get(n, [])
    return {
        "n": n, "name": name, "tier": "ETO_GUIDED", "brand": brand_str,
        "spec": (
            f"Standard sub-items auto-priced; bespoke {name} design captured for {brand_str} "
            f"engineering — requirement architecture: {req.get('voltage_arch') or 'not specified'}"
        ),
        "justification": tier_reason,
        "standard_subitems": [
            {"item": item, "qty": 1, "pricing_status": "auto_priced_pending_aPriori_connection"}
            for item in standard_items
        ],
        "basis_of_design_capture": {
            "summary": f"Bespoke {name} design required — not auto-drafted by this system.",
            "routed_to": f"{brand_str} design engineers",
            "captured_requirements": {k: v for k, v in req.items() if k in _CAPTURE_FIELDS},
        },
    }


def _eto_exception_layer(n: int, name: str, brand_str: str, tier_reason: str, req: dict) -> dict:
    return {
        "n": n, "name": name, "tier": "ETO_EXCEPTION", "brand": brand_str,
        "spec": (
            f"No auto-draft attempted; requirement captured for specialist design — "
            f"requirement architecture: {req.get('voltage_arch') or 'not specified'}"
        ),
        "justification": tier_reason,
        "price_placeholder": {
            "note": "Margin-protected placeholder pending specialist design — not a final price.",
            "status": "pending_specialist_design",
        },
        "intake_ticket": {
            "routed_to": f"{brand_str} lead engineering",
            "summary": f"{name} requires first-principles engineering design — no standardized template applies.",
            "requirement_snapshot": {k: v for k, v in req.items() if k in _CAPTURE_FIELDS},
        },
    }


def run(req: dict, rfp_text: str = "") -> dict:
    tier_result = classify_tiers(req, rfp_text)

    auto_layer_inputs = [
        {"n": t["n"], "name": t["name"]} for t in tier_result["tiers"] if t["tier"] == "CTO_AUTOMATE"
    ]

    retrieved = []
    auto_specs = {}
    if auto_layer_inputs:
        queries = _build_retrieval_queries(req)
        for q in queries:
            retrieved.extend(retrieve(q, k=3))
        best = {}
        for r in retrieved:
            if r["doc_id"] not in best or r["score"] > best[r["doc_id"]]["score"]:
                best[r["doc_id"]] = r
        retrieved = sorted(best.values(), key=lambda r: r["score"], reverse=True)[:8]

        auto_result = call_llm_json(
            _build_auto_prompt(req, auto_layer_inputs, retrieved),
            _mock_auto_layers, req, auto_layer_inputs, retrieved,
        )
        auto_specs = {l["n"]: l for l in auto_result["layers"]}

    layers_out = []
    for t in tier_result["tiers"]:
        n, name = t["n"], t["name"]
        brand_str = " + ".join(t["hinted_brands"])

        if t["tier"] == "CTO_AUTOMATE":
            spec_info = auto_specs.get(n, {"spec": f"Standard {name} configuration", "justification": t["reason"]})
            layer_out = _cto_automate_layer(n, name, brand_str, spec_info["spec"], spec_info["justification"])
        elif t["tier"] == "ETO_GUIDED":
            layer_out = _eto_guided_layer(n, name, brand_str, t["reason"], req)
        else:
            layer_out = _eto_exception_layer(n, name, brand_str, t["reason"], req)

        layer_out["tier_source"] = t["source"]
        layer_out["matched_override_keyword"] = t["matched_override_keyword"]
        layers_out.append(layer_out)

    tier_counts = {
        "CTO_AUTOMATE": sum(1 for t in tier_result["tiers"] if t["tier"] == "CTO_AUTOMATE"),
        "ETO_GUIDED": sum(1 for t in tier_result["tiers"] if t["tier"] == "ETO_GUIDED"),
        "ETO_EXCEPTION": sum(1 for t in tier_result["tiers"] if t["tier"] == "ETO_EXCEPTION"),
    }
    combination_type = "fully automated" if (tier_counts["ETO_GUIDED"] == 0 and tier_counts["ETO_EXCEPTION"] == 0) else "hybrid tiered design"

    return {
        "layers": layers_out,
        "combination_type": combination_type,
        "tier_counts": tier_counts,
        "rationale": (
            f"{tier_counts['CTO_AUTOMATE']} layer(s) fully auto-drafted, {tier_counts['ETO_GUIDED']} guided with "
            f"bespoke capture, {tier_counts['ETO_EXCEPTION']} routed as exceptions with no auto-draft attempt."
        ),
        "explanation": (
            f"Drafted a {combination_type} across all six stack layers, branching by tier: only "
            f"{tier_counts['CTO_AUTOMATE']} layer(s) tiered CTO_AUTOMATE were sent to the model for spec drafting; "
            f"the remaining {tier_counts['ETO_GUIDED'] + tier_counts['ETO_EXCEPTION']} layer(s) were handled entirely "
            f"by deterministic templating, with no model involvement, per the tier classification above."
        ),
        "evidence": retrieved + [{"source": "agents/tier_classifier.py", "tier_counts": tier_counts}],
    }
