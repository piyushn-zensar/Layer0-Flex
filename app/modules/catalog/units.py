"""Units of the spec tables (product_specs.json): a value as written -> its attribute's base unit. Used by
scripts/extract_product_specs.py and, through catalog.service.convert_unit, by the configurator's range search,
so a requirement and a rating are converted the same way."""
import re

# unit as written (spaces and degree signs removed) -> (quantity, factor to the quantity's base unit)
UNITS = {"A": ("A", 1), "kA": ("A", 1e3), "V": ("V", 1), "kV": ("V", 1e3), "Hz": ("Hz", 1), "W": ("W", 1e-3),
         "kW": ("W", 1), "MW": ("W", 1e3), "C": ("C", 1), "LPM": ("L/min", 1), "L/min": ("L/min", 1),
         "l/min": ("L/min", 1), "lpm": ("L/min", 1), "GPM": ("L/min", 3.785), "gpm": ("L/min", 3.785),
         "m3/h": ("L/min", 16.667), "m": ("m", 1), "mm": ("mm", 1), "cm": ("mm", 10), "in": ("mm", 25.4),
         "amperes": ("A", 1), "amps": ("A", 1), "amp": ("A", 1), "volts": ("V", 1), "kilovolts": ("V", 1e3),
         "cycles": ("Hz", 1), "hertz": ("Hz", 1), "kg": ("kg", 1), "KG": ("kg", 1), "lb": ("kg", 0.4536), "lbs": ("kg", 0.4536), "%": ("%", 1)}
BASE = {"A": "A", "V": "V", "kA": "A", "Hz": "Hz", "kW": "W", "C": "C", "L/min": "L/min", "m": "m", "mm": "mm",
        "kg": "kg", "%": "%"}   # attribute base unit -> its quantity (kA is a current; kW a power)


def _unit(u: str) -> str:
    u = u.replace(" ", "").replace("º", "").replace("°", "").replace("³", "3").rstrip(",.;:)")
    u = re.sub(r"-?class$", "", u)                                   # "15 kV-class" is a 15 kV rating
    u = u.lower() if u.lower() in UNITS and u not in UNITS else u     # "Amperes", "Volts"
    for suffix in ("AC", "DC", "ac", "dc", "rms", "pk"):      # VAC, kVDC: the same quantity
        if u.endswith(suffix) and u[: -len(suffix)] in UNITS:
            return u[: -len(suffix)]
    return u


def convert(value: float | None, unit: str, base: str) -> tuple[float | None, str | None]:
    """A value as written -> the attribute's base unit; (None, why) when the unit does not fit."""
    if value is None:
        return None, None
    u = _unit(unit)
    if base == "C" and u in ("F", "degF"):
        return round((value - 32) * 5 / 9, 2), None
    if base == "mm" and u == "m":                              # a length in metres, for a dimension in mm
        return round(value * 1000, 3), None
    if u not in UNITS or UNITS[u][0] != BASE[base]:
        return None, f"unit {unit!r} is not a {base} quantity"
    factor = UNITS[u][1] / (1e3 if base == "kA" else 1)      # kA is stored in kA, the others in their base unit
    return round(value * factor, 6), None
