"""Configurator input agent (P-54, C-55): one model call maps a set of frozen requirements to the supplied
configurator's input fields. Each value names the requirement(s) it comes from and the verbatim text; the unit is
returned as written ("15 kW") and parsed and converted by code (service.normalise), never by the model. Answers are frozen in
data/llm_cache/configurator_inputs/ (rule R2)."""
import json

from app.core import llm

TASK = "configurator_inputs"

# field -> (kind, target unit); kinds: number, text, list. Mirrors rfp_configurator.SystemRequirement / BoardRequirement.
SYSTEM = {"total_it_load_mw": ("number", "MW"), "rack_density_kw": ("number", "kW"), "distribution_voltage": ("text", None),
          "coolant_supply_temp_c": ("number", "C"), "cooling_mode": ("text", None), "redundancy": ("text", None),
          "certifications": ("list", None), "deployment": ("text", None), "liquid_capture_fraction": ("number", "fraction")}
BOARD = {"input_v_min": ("number", "V"), "input_v_max": ("number", "V"), "output_v_min": ("number", "V"),
         "output_v_max": ("number", "V"), "output_power_w": ("number", "W"), "output_current_a": ("number", "A"),
         "peak_power_w": ("number", "W"), "isolation": ("text", None), "isolation_v_min": ("number", "V"),
         "regulation": ("text", None), "digital": ("text", None), "applications": ("list", None),
         "package_types": ("list", None), "footprints": ("list", None), "mountings": ("list", None),
         "max_length_mm": ("number", "mm"), "max_width_mm": ("number", "mm"), "max_height_mm": ("number", "mm"),
         "min_efficiency_pct": ("number", "%"), "redundancy": ("text", None), "design_margin_pct": ("number", "%")}

SYSTEM_PROMPT = """You map RFP requirements to the input of a product configurator for Flex / Axiom power products.
You get requirement items (ID, text, verbatim quote) and return, for each configurator field, either null (the items
do not state it) or an object:
- numeric fields: {"as_written", "req_ids", "source"}. as_written = one number with its unit exactly as the item
  writes it, for example "15 kW", "800 VDC", "120 MW", "45 °C", "97.5%". Copy the digits as written: never convert,
  multiply or add up (six 15 kW converters is "15 kW" per converter, not "90 kW").
- text and list fields: {"value", "req_ids", "source"}.
- req_ids: the IDs of the items that state it; source: the verbatim words from those items that state it.
Never infer, default or compute a value the items do not state. A range "40 to 60 V" fills min ("40 V") and max ("60 V"); a
single voltage fills only min (the configurator treats it as a point value). Any other one-value field stated as a
range (rack density "198 to 330 kW") takes the highest value with its unit ("330 kW"). Redundancy, design margin, isolation and
certifications only when the items say so.
system = the whole installation (IT load, rack density = power per rack, also written as rack or cabinet TDP or
kW per rack, distribution voltage such as "800VDC", "±400VDC", "480VAC",
coolant supply temperature, cooling_mode air|liquid|hybrid (liquid when the items require liquid cooling, cold
plates or CDUs for the IT load), redundancy N|N+1|2N|4-to-make-3, certifications,
deployment prefab|stick-built, liquid_capture_fraction). System redundancy is the power redundancy of the installation
(for example blocks plus a catcher); the redundancy of one subsystem such as the CDUs is not the system's. N units plus
one spare or catcher is N+1 ("four blocks plus one catcher" and "4+1" are N+1 with N = 4); 4-to-make-3 only when
the item says four units of which three carry the load (distributed redundancy).
board = one board-level DC/DC power module function (input and output voltage, power, current, peak power,
isolation required|not_required, isolation voltage, regulation, digital interface PMBus|GCB, applications, package
types, footprints, mountings, maximum size, minimum efficiency, redundancy N|N+1|2N, design margin). Only fill board
fields for a DC/DC conversion on a board or in a rack shelf, not for switchgear, busway, UPS or cooling. Board input
and output voltages are DC: an AC voltage (VAC, three-phase) is never a board voltage. Board power, current and
efficiency are those of the DC/DC converter, not of a rack, a block or the end-to-end chain.
For applications, package_types, footprints, mountings and regulation use only the catalogue values listed in the
prompt; leave a field null when no listed value fits."""


def _field(kind: str) -> dict:
    first = {"number": ("as_written", {"type": "string"}), "text": ("value", {"type": "string"}),
             "list": ("value", {"type": "array", "items": {"type": "string"}})}[kind]
    obj = {"type": "object", "additionalProperties": False, "required": [first[0], "req_ids", "source"],
           "properties": {first[0]: first[1], "req_ids": {"type": "array", "items": {"type": "string"}},
                          "source": {"type": "string"}}}
    return {"anyOf": [obj, {"type": "null"}]}


def _scope(fields: dict) -> dict:
    return {"type": "object", "additionalProperties": False, "required": list(fields),
            "properties": {k: _field(kind) for k, (kind, _) in fields.items()}}


SCHEMA = {"type": "object", "additionalProperties": False, "required": ["system", "board"],
          "properties": {"system": _scope(SYSTEM), "board": _scope(BOARD)}}


def extract(items: list[dict], vocab: dict, component: str = "") -> dict:
    """items: [{req_id, text, quote}] -> {"system": {...}, "board": {...}} as stated (numbers as written).
    component: what the items were grouped under (P-55), for example "dc_dc: 800 VDC to 54 VDC rack power shelf"
    (fill the board fields for that conversion) or "system: installation-wide parameters"."""
    prompt = ((f"The items are about: {component}\n\n" if component else "")
              + f"Catalogue values: {json.dumps(vocab, ensure_ascii=False)}\n\nRequirement items:\n"
              + "\n".join(json.dumps({"req_id": i["req_id"], "text": i["text"], "quote": i["quote"]}, ensure_ascii=False)
                          for i in items))
    return llm.complete_json(TASK, SYSTEM_PROMPT, prompt, SCHEMA)


GROUP_TASK = "configurator_groups"
GROUP_KINDS = ("dc_dc", "other")     # the system group is the items marked "system", not a component
ASSIGN_TASK = "configurator_assign"
CHUNK = 50                            # items per assignment call: every item gets an answer within max_tokens

KINDS_TEXT = """- dc_dc: a DC-input, DC-output converter: board-mounted DC/DC modules (bricks, point-of-load, intermediate bus
  converters) or the DC/DC converters of a rack power shelf. One component per distinct conversion (a different input
  or output voltage is a different component). An AC-input stage (rectifier, solid-state transformer, MV AC to DC
  power block, UPS) is NOT dc_dc: it is other.
- other: every other component, subsystem or delivered service (for example medium-voltage equipment, power
  conversion blocks, DC distribution and protection, energy storage, racks, compute and storage systems, networks,
  cooling plant, CDUs, controls and monitoring, testing and acceptance, site works)."""

GROUP_PROMPT = """You list the components and subsystems one RFP asks for, so that its requirements can be grouped by the
component they ask for and related constraints (voltage, power, current, isolation, interface, size) evaluated
together. You get the technical and compliance items (ID, RFP section, verbatim text). Return every distinct
component or subsystem the items ask for, each with an id (G1, G2, ...), a short name in the RFP's own words and a kind:
""" + KINDS_TEXT + """
Keep components apart: an RFP in lots or chapters usually asks for several components per lot. Do not merge
different equipment into one component because it sits in the same chain. Every DC/DC conversion an item names (for
example a shelf converting one DC voltage to another inside a rack) is its own dc_dc component, even when it is part
of a larger assembly such as a rack."""

ASSIGN_PROMPT = """You assign RFP requirement items to the components of the RFP. You get the component list (id, name, kind)
and a batch of items (ID, RFP section, verbatim text). Return every item of the batch, in the order given, with:
- component: the id of the one component the item is about. An item goes to a dc_dc component only when it is about
  that DC/DC conversion itself; an item about an AC-input rack, a variant with another voltage, protection or storage
  next to it goes to that other component. "" only when the item asks for nothing a product, a subsystem or the
  delivery could answer (scoring rules, evaluation criteria, how tenders are compared).
- system: true when the item states a value for an installation-wide parameter (total IT load, rack density,
  distribution voltage to the rack, installation power redundancy, cooling mode, coolant supply temperature,
  certifications the whole delivery needs, prefabricated or stick-built delivery); usually few items.
Component kinds:
""" + KINDS_TEXT

GROUP_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["components"], "properties": {
    "components": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["id", "name", "kind"],
        "properties": {"id": {"type": "string"}, "name": {"type": "string"}, "kind": {"type": "string", "enum": list(GROUP_KINDS)}}}}}}
ASSIGN_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["items"], "properties": {
    "items": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["req_id", "component", "system"],
        "properties": {"req_id": {"type": "string"}, "component": {"type": "string"}, "system": {"type": "boolean"}}}}}}


def _lines(items: list[dict]) -> str:
    return "\n".join(json.dumps({k: i[k] for k in ("req_id", "section", "quote")}, ensure_ascii=False) for i in items)


def group(items: list[dict]) -> dict:
    """items: [{req_id, section, quote}] of one bid -> {"groups": [{name, kind, req_ids}], "unassigned": [req_id]}:
    the components in the model's order, then "System parameters" (kind "system") when any item states one.
    One call lists the components; items are assigned in batches of CHUNK (all frozen)."""
    comps = llm.complete_json(GROUP_TASK, GROUP_PROMPT, "Requirement items:\n" + _lines(items), GROUP_SCHEMA)["components"]
    listing = json.dumps(comps, ensure_ascii=False, sort_keys=True)   # as a frozen answer replays: same key live or not
    answers = {}
    for n in range(0, len(items), CHUNK):
        batch = items[n:n + CHUNK]
        out = llm.complete_json(ASSIGN_TASK, ASSIGN_PROMPT, f"Components: {listing}\n\nItems:\n{_lines(batch)}", ASSIGN_SCHEMA)
        asked = {i["req_id"] for i in batch}
        answers |= {a["req_id"]: a for a in out["items"] if a["req_id"] in asked}
    groups = [{"name": c["name"], "kind": c["kind"], "req_ids": [i for i, a in answers.items() if a["component"] == c["id"]]}
              for c in comps]
    system = [i for i, a in answers.items() if a["system"]]
    return {"groups": groups + ([{"name": "System parameters", "kind": "system", "req_ids": system}] if system else []),
            "unassigned": [i["req_id"] for i in items if i["req_id"] not in answers]}
