"""Run the reader agent on a PDF's frozen layout and freeze its answers (task P-04).

    .venv\\Scripts\\python -m scripts.freeze_reader data/RFP/RFP-2023-20-Switchgear-Procurement-Final.pdf

Needs LLM_PROVIDER=azure for chunks that have no cached answer. Every answer is written to
data/llm_cache/read_requirements/ (commit it): from then on everyone gets the same requirement list
with LLM_PROVIDER=mock. Prints how many quotes were found on their page (EXTRACTED) versus not (UNANCHORED).
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from app.core import config
from app.modules.ingestion.service import LAYOUT_CACHE
from app.modules.requirements import agent, anchoring

for arg in sys.argv[1:]:
    sha = hashlib.sha256(Path(arg).read_bytes()).hexdigest()
    layout = json.loads((LAYOUT_CACHE / f"{sha}.json").read_text("utf-8"))  # run scripts.freeze_layout first
    print(f"{arg}: provider={config.LLM_PROVIDER} model={config.LLM_MODEL}", flush=True)
    found, problems, coverage = agent.read(layout)
    hits = [anchoring.find(r["quote"], layout["pages"], r["page"], r.get("lines")) for r in found]
    print(f"requirements proposed: {len(found)}")
    print(f"anchored: {sum(bool(h) for h in hits)} (several spans: {sum(bool(h) and len(h['spans']) > 1 for h in hits)})"
          f"   unanchored: {sum(not h for h in hits)}")
    print("coverage:", coverage)
    print("by category:", dict(Counter(r["category"] for r in found)))
    print("by page (top 10):", Counter(r["page"] for r in found).most_common(10))
    for r, h in zip(found, hits):
        if not h:
            print(f"  UNANCHORED p{r['page']}: {r['quote'][:110]}")
    for p in problems:
        print("  PROBLEM", p)
