# Layer 0 (Layer0-Flex) — project guide for Claude

Layer 0 is a proof of concept for SpinCo / Axiom Solutions (the Flex business being spun off). It manages one bid
opportunity from RFP to final response: read the RFP into requirement line items with exact sources, match each to
a business unit's product (EP² is one of the units), record participation and go/no-go, dispatch one work package
per unit, collect checklist responses, validate, consolidate. Three linked screens are the centre of the demo.

## Sources of truth

- Design: `Documents/technical-architecture.md` (do NOT redesign; wire in, port, test).
- Business and problems: the other files in `Documents/`.
- Who does what, task IDs, dates, ownership: `team/PLAN.md`. Status: `team/tracker/<name>.md`.
- Earlier code to port from: `reference/` (read-only, never import from it).

## Who am I working for?

Run `git config user.name` at the start of a task and map it to a teammate: Piyush, Atharv or Janvia. Their owned
paths are in `team/PLAN.md` section 3 and in `.claude/rules/ownership.md`. **Only edit files the current teammate
owns.** If the task needs a change elsewhere, use the `contract-change` skill instead of editing.

## Commands (Windows, from the repo root)

```bash
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt     # parsing machine: requirements-parsing.txt
cp .env.example .env                                        # LLM_PROVIDER=mock needs no key
.venv/Scripts/python -m scripts.seed_demo --reset           # demo opportunity OPP-0001 (Syracuse RFP)
.venv/Scripts/python -m uvicorn app.main:app --reload       # API on :8000 (docs at /docs)
cd web && npm install && npm run dev                        # web on http://localhost:3000 (proxies /api)
.venv/Scripts/python -m pytest -q                           # must pass before every push
.venv/Scripts/python -m app.modules.<module>.<file>         # a module's self-check, where it has one
```

## Skills and agents in this repo

- Skills: `/start-task <ID>`, `/sync`, `/run-app`, `/contract-change`.
- Agents: `module-builder` (implements a task inside one module), `boundary-reviewer` (checks a diff against
  ownership and module rules, read-only), `doc-keeper` (updates `Documents/` in the client-facing voice),
  `rfp-golden` (builds the hand-checked requirement list for an RFP).
- On the Pro plan (Janvia): prefer doing the work directly with Sonnet; use agents sparingly.

## Ground rules (details in `.claude/rules/`)

- Back end: FastAPI modular monolith; modules talk only through `service.py`; controllers return JSON under `/api`.
- Front end: Next.js in `web/`; one route folder per screen, owned by the module owner; it calls only `/api`.
- The model (Azure OpenAI GPT-4o) is called only through `app/core/llm.py`; answers are cached in `data/llm_cache/` and committed.
- No regex or keyword rules for identifying requirements. Never invent a source location.
- Agents propose; named people decide. Every write records an audit event.
- Small commits on `main`, `git pull --rebase` and tests before every push, never force-push.
