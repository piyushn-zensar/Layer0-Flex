"""Score the reader agent against a golden requirement list (task P-05).

    .venv\\Scripts\\python -m scripts.score_reader data/RFP/RFP-2023-20-Switchgear-Procurement-Final.pdf

Uses the frozen answers in data/llm_cache (no API call) and data/golden/<pdf name>.json.
A reader item matches a golden item when both are on the same page and their line ranges overlap.
Recall = golden items found; precision = reader items that are real requirements.
Uncertain golden items count for precision (finding them is not wrong) but not against recall.
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from app.core import config
from app.modules.ingestion.service import LAYOUT_CACHE
from app.modules.requirements import agent, anchoring

config.LLM_PROVIDER = "mock"  # score the frozen answers; never call the model here


def overlaps(a: dict, b: dict) -> bool:
    return a["page"] == b["page"] and a["line_start"] <= b["line_end"] and b["line_start"] <= a["line_end"]


def score(pdf: str) -> dict:
    sha = hashlib.sha256(Path(pdf).read_bytes()).hexdigest()
    layout = json.loads((LAYOUT_CACHE / f"{sha}.json").read_text("utf-8"))
    golden = json.loads((config.DATA / "golden" / f"{Path(pdf).stem}.json").read_text("utf-8"))["requirements"]
    found, problems = agent.read(layout)
    reader = [h | r for r in found if (h := anchoring.find(r["quote"], layout["pages"], r["page"]))]
    unanchored = len(found) - len(reader)

    sure = [g for g in golden if not g.get("uncertain")]
    hit_golden = [g for g in sure if any(overlaps(g, r) for r in reader)]
    real = [r for r in reader if any(overlaps(r, g) for g in golden)]
    by_cat = {c: f"{sum(any(overlaps(g, r) for r in reader) for g in sure if g['category'] == c)}/{n}"
              for c, n in sorted(Counter(g["category"] for g in sure).items())}
    return {
        "golden": len(golden), "golden_certain": len(sure), "reader_proposed": len(found),
        "reader_anchored": len(reader), "reader_unanchored": unanchored,
        "recall": round(len(hit_golden) / max(len(sure), 1), 3),
        "precision": round(len(real) / max(len(reader), 1), 3),
        "recall_by_category": by_cat, "problems": problems,
        "missed": [f"p{g['page']} L{g['line_start']}-{g['line_end']} [{g['category']}] {g['quote'][:90]}"
                   for g in sure if g not in hit_golden],
        "extra": [f"p{r['page']} L{r['line_start']}-{r['line_end']} [{r['category']}] {r['quote'][:90]}"
                  for r in reader if r not in real],
    }


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        s = score(arg)
        print(json.dumps({k: v for k, v in s.items() if k not in ("missed", "extra")}, indent=1))
        print(f"\nMISSED ({len(s['missed'])}):", *s["missed"], sep="\n  ")
        print(f"\nEXTRA, not in the golden list ({len(s['extra'])}):", *s["extra"], sep="\n  ")
