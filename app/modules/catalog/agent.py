"""Spec-table agent (C-52 follow-up, 23 Oct 2026): the rating tables of a supplied product document -> structured
attributes per product family or variant. The model reads; it never converts or computes: numbers come back as the
page writes them, with the page, a verbatim quote and the conditions, and scripts/extract_product_specs.py keeps a
value only when its digits are on that page, then converts the unit. Answers are frozen in
data/llm_cache/extract_product_specs/ (rule R2). Everything extracted is unverified until the unit reviews it."""
from app.core import llm

TASK = "extract_product_specs"

# attribute -> (kind, base unit); the vocabulary later matching uses. kind "range" = numbers (min / max), "text" = words.
ATTRIBUTES = {
    "rated_current": ("range", "A"), "tap_off_current": ("range", "A"), "rated_voltage_ac": ("range", "V"),
    "rated_voltage_dc": ("range", "V"), "insulation_voltage": ("range", "V"), "impulse_withstand_voltage": ("range", "V"),
    "short_time_withstand": ("range", "kA"), "peak_withstand": ("range", "kA"), "breaking_capacity": ("range", "kA"),
    "frequency": ("range", "Hz"), "ip_rating": ("text", None), "form_of_separation": ("text", None),
    "conductor_material": ("text", None), "conductors_or_poles": ("text", None), "standards": ("text", None),
    "seismic_or_arc": ("text", None), "cooling_capacity": ("range", "kW"), "approach_temperature": ("range", "C"),
    "supply_temperature": ("range", "C"), "return_temperature": ("range", "C"), "flow_rate": ("range", "L/min"),
    "output_power": ("range", "kW"), "output_voltage": ("range", "V"), "power_consumption": ("range", "kW"), "operating_temperature": ("range", "C"), "altitude": ("range", "m"),
    "height": ("range", "mm"), "width": ("range", "mm"), "depth": ("range", "mm"), "weight": ("range", "kg"),
    "efficiency": ("range", "%"), "communication": ("text", None), "other": ("text", None),
}

SYSTEM = """You turn the technical ratings in pages of a product catalogue, brochure or datasheet into a structured table.
You get the product family the pages are about, and the pages' text (each page starts with "=== page N ===";
tables read from the page follow as markdown). Return the items the pages give ratings for: one item per variant or
rating row the pages distinguish (for example "DATABAR DX 800 A" or "HXC 1000 A aluminium"), or one item for the whole
range when the pages give only ranges ("up to 6300 A"). Only values that apply to the named product family; leave
out other products the pages mention.
Each attribute: name from the list given, label (the page's own words for it), min and max (numbers exactly as the
page writes them; one stated value goes in both; "up to 6300 A" is min null, max 6300), text (the value as written,
for words such as "IP54" or "Form 4b Type 7", and for any value with conditions), unit exactly as written ("kA",
"A", "VAC", "kW", "MW", "ºC", "LPM", "mm"), conditions (for example "1 s", "at 6 ºC approach", "redundant pumps",
"per IEC 61439-6"; "" when none), page (the page number it is on) and quote (the verbatim words from that page, at
most 25 words, that state it, and that contain the number itself). Copy each number with the unit printed next to it:
"1.2 MW" is min 1.2, max 1.2, unit "MW" (never 1200 kW); "2,800 W" is 2800 with unit "W"; a table cell's number with
the unit in its column or row header takes that header's unit, and the quote then includes the header and the cell.
output_power is what a converter or supply delivers (put "peak" or "continuous" in conditions); power_consumption is
what a unit draws itself (pumps, controls). Never convert units, compute, combine pages into a new value or guess; leave out a rating the pages do not state; a
size in rack units ("6U") is "other", not a height in mm. Marketing claims without a number or a named standard are
not ratings."""


def _attr() -> dict:
    return {"type": "object", "additionalProperties": False,
            "required": ["name", "label", "min", "max", "text", "unit", "conditions", "page", "quote"],
            "properties": {"name": {"type": "string", "enum": list(ATTRIBUTES)}, "label": {"type": "string"},
                           "min": {"type": ["number", "null"]}, "max": {"type": ["number", "null"]},
                           "text": {"type": "string"}, "unit": {"type": "string"}, "conditions": {"type": "string"},
                           "page": {"type": "integer"}, "quote": {"type": "string"}}}


SCHEMA = {"type": "object", "additionalProperties": False, "required": ["items"], "properties": {"items": {
    "type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["variant", "attributes"],
                               "properties": {"variant": {"type": "string"},
                                              "attributes": {"type": "array", "items": _attr()}}}}}}


def extract(family: str, document: str, pages_text: str) -> dict:
    """family: "ANORD-LVSB/MDX (MDX Switchgear (IEC 61439-2))"; pages_text: the pages as described in SYSTEM."""
    prompt = (f"Product family: {family}\nDocument: {document}\nAttribute names: {', '.join(ATTRIBUTES)}\n\n{pages_text}")
    return llm.complete_json(TASK, SYSTEM, prompt, SCHEMA)
