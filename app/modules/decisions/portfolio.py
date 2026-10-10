"""Bid and portfolio checks for the go/no-go evidence (task A-10), ported from the v1.1 demo onto real data.

v1.1 compared hand-made specification records with an invented "standard portfolio" and ran a portfolio check on
synthetic customers. Here:
- deviations: the RFP's own data sheet (ruled tables in the layout, P-07) against the standard ratings of the products
  the requirements are matched to (portfolio.json, PLACEHOLDERS). Severity as in v1.1: a rating above the standard
  for voltage, current or frequency is high, for impulse level or momentary rating medium.
- workload: each unit's open work across every opportunity in Layer 0, plus what this opportunity would add,
  against the unit's capacity (portfolio.json, PLACEHOLDERS). Lists the other opportunities competing for the unit.
Reading a value out of a data-sheet cell is value parsing, not requirement identification (rule R5 still holds).
"""
import re

from sqlalchemy.orm import Session

from app.modules.catalog import service as catalog
from app.modules.ingestion import service as ingestion
from app.modules.matching import service as matching
from app.modules.opportunities import service as opportunities

OPEN = {"assigned", "submitted", "returned"}


def numbers(text: str) -> list[float]:
    """Numbers in a data-sheet cell: "2000/1200" -> [2000, 1200]; "1.5 or higher" -> [1.5]."""
    return [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))]


def data_sheet(db: Session, opp_id: str) -> list[dict]:
    """Label / value / unit rows from every ruled table of the main RFP, with their source."""
    doc = opportunities.main_document(db, opp_id)
    if doc is None or doc.status != "ingested":
        return []
    rows = []
    for page in ingestion.layout(doc.id)["pages"]:
        for table in page.get("tables", []):
            for r, cells in enumerate(table["rows"]):
                texts = [(c or {}).get("text", "").replace("\n", " ").strip() for c in cells]
                if len(texts) >= 2 and texts[0] and texts[1]:
                    rows.append({"label": texts[0], "value": texts[1], "unit": texts[2] if len(texts) > 2 else "",
                                 "page": page["page"], "table": table["id"], "row": r})
    return rows


def deviations(db: Session, opp_id: str) -> dict:
    cfg = catalog.portfolio()
    in_play = sorted({u["product_id"] for m in matching.for_opportunity(db, opp_id).values() for u in (m.units or [])})
    sheet = data_sheet(db, opp_id)
    out, checked = [], 0
    for pid in in_play:
        standard = cfg["standards"].get(pid)
        if not standard:
            continue
        for f in cfg["fields"]:
            if f["field"] not in standard:
                continue
            row = next((r for r in sheet if any(r["label"].lower().startswith(l) for l in f["labels"]) and numbers(r["value"])), None)
            if row is None:
                continue
            checked += 1
            asked, std = max(numbers(row["value"])), standard[f["field"]]
            if (asked != std) if f.get("must_equal") else (asked > std):
                out.append({"product_id": pid, "field": f["name"], "rfp": f"{row['value']} {row['unit']}".strip(),
                            "standard": f"{std} {f['unit']}", "severity": f["severity"],
                            "source": f"p. {row['page']}, data sheet row {row['row']}"})
    return {"rows": out, "checked": checked, "products": in_play,
            "placeholder": True, "note": "Standard ratings are PLACEHOLDERS ported from the v1.1 demo; to be confirmed."}


def workload(db: Session, opp_id: str) -> dict:
    from app.modules.workpackages import service as workpackages  # imported here: workpackages imports decisions
    cfg = catalog.portfolio()["capacity_open_items"]
    adds: dict[str, int] = {}
    dispatched = {a.req_id for items in workpackages.by_requirement(db, opp_id).values() for a in items}
    for m in matching.for_opportunity(db, opp_id).values():
        if m.req_id not in dispatched:
            for bu in {u["bu"] for u in (m.units or [])} or ({"BID"} if m.status != "rejected" else set()):
                adds[bu] = adds.get(bu, 0) + 1
    units = sorted(set(adds) | {a.bu for items in workpackages.by_requirement(db, opp_id).values() for a in items})
    rows = []
    for bu in units:
        open_items = [a for a in workpackages.inbox(db, bu) if a.status in OPEN]
        others = sorted({a.opportunity_id for a in open_items if a.opportunity_id != opp_id})
        total = len(open_items) + adds.get(bu, 0)
        cap = cfg.get(bu)
        rows.append({"bu": bu, "open_here": sum(a.opportunity_id == opp_id for a in open_items) + adds.get(bu, 0),
                     "open_elsewhere": len(open_items) - sum(a.opportunity_id == opp_id for a in open_items),
                     "other_opportunities": others, "total": total, "capacity": cap,
                     "over": cap is not None and total > cap})
    return {"rows": rows, "placeholder": True,
            "note": "Capacity is a PLACEHOLDER count of open work items per unit; to be confirmed with each unit."}


if __name__ == "__main__":  # self-check: python -m app.modules.decisions.portfolio
    assert numbers("2000/1200") == [2000.0, 1200.0] and numbers("1.5 or higher") == [1.5] and numbers("VENDOR") == []
    assert numbers("1,200 A") == [1200.0]
    print("portfolio ok")
