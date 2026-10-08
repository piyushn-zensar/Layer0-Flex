"""Parse a PDF on the parsing machine and commit the result as a frozen layout.

    .venv\\Scripts\\python -m scripts.freeze_layout data/RFP/RFP-2023-20-Switchgear-Procurement-Final.pdf

Writes data/layout_cache/<sha256>.json. Commit it: teammates then get the same pages, line numbers
and highlights without Tesseract or other parsing-only dependencies. Re-run after every parser change.
"""
import hashlib
import json
import sys
from pathlib import Path

from app.modules.ingestion.service import LAYOUT_CACHE, parse

for arg in sys.argv[1:]:
    sha = hashlib.sha256(Path(arg).read_bytes()).hexdigest()
    model = parse(arg, sha)
    LAYOUT_CACHE.mkdir(parents=True, exist_ok=True)
    (LAYOUT_CACHE / f"{sha}.json").write_text(json.dumps(model, sort_keys=True, ensure_ascii=False), "utf-8")
    unreviewed = [p["page"] for p in model["pages"] if p["unreviewed"]]
    print(f"{arg}: {model['page_count']} pages, pipeline {model['pipeline_version']}, unreviewed {unreviewed}")
