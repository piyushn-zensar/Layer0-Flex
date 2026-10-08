---
name: run-app
description: Set up and run the Layer 0 app locally on Windows - venv, dependencies, .env, demo seed, server, tests - and open the three screens. Use when a teammate says "run the app", "set me up", "reset the demo", or something fails on start.
---

# Run Layer 0 locally

From the repo root (Git Bash paths; in PowerShell use `.venv\Scripts\python`):

1. Python 3.12: `py -3.12 -m venv .venv` (skip if `.venv/` exists).
2. `.venv/Scripts/python -m pip install -r requirements.txt`
   (parsing machine only: `requirements-parsing.txt`, plus Tesseract at `%LOCALAPPDATA%\Tesseract-OCR`).
3. `.env`: copy `.env.example` if missing. `LLM_PROVIDER=mock` runs on committed cached answers with no key.
   Generating new model answers needs `LLM_PROVIDER=azure` and the `AZURE_OPENAI_*` settings (task owners only).
4. Demo data: `.venv/Scripts/python -m scripts.seed_demo --reset` (recreates `data/store/layer0.db`;
   needed after any model/table change).
5. API: `.venv/Scripts/python -m uvicorn app.main:app --reload` → http://127.0.0.1:8000/docs
   Web (second terminal): `cd web && npm install && npm run dev` → http://localhost:3000
   - Three screens: http://localhost:3000/opportunities/OPP-0001/trace
   - Switch the acting user (bid manager, unit product manager or design engineer) in the header.
6. Tests: `.venv/Scripts/python -m pytest -q`.

Common problems:
- `no such column` / `no such table` → reseed with `--reset`.
- A page shows "needs OCR" → expected on machines without Tesseract unless the committed layout has OCR text.
- `No cached answer for ...` → that agent's answers are not generated yet; the owner runs it with `azure`.
