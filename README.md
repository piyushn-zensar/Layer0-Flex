# Layer0-Flex

Layer 0 proof of concept for SpinCo / Axiom Solutions: one bid opportunity from RFP to final response.
The RFP is read into requirement line items with exact sources. Each item is matched to a business unit's product
(EP² and the other units). Participation and go/no-go are recorded. Each unit gets one work package, answers it as a
checklist, and the bid manager validates and consolidates the answers, with three linked screens.

- Design and business context: [`Documents/`](Documents/) (source of truth; start with `project-overview.md`)
- Team plan, ownership and trackers: [`team/`](team/)
- Claude Code setup shared by the team (rules, agents, skills): [`.claude/`](.claude/)

**Just want to run the demo on a Windows laptop?** Follow [INSTALL.md](INSTALL.md): double-click `setup.cmd` once, then `start.cmd`.

## Run for development (Windows, Python 3.12)

```bash
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env                                   # LLM_PROVIDER=mock: no API key needed
.venv/Scripts/python -m scripts.seed_demo --reset      # demo opportunity from the Syracuse RFP
.venv/Scripts/python -m uvicorn app.main:app --reload    # API: http://127.0.0.1:8000/docs
cd web && npm install && npm run dev                     # second terminal: web on :3000
```

Open http://localhost:3000/opportunities/OPP-0001/trace for the three screens. Tests: `.venv/Scripts/python -m pytest -q`.

Next steps and ideas for later iterations: [SUGGESTIONS.md](SUGGESTIONS.md).

## Layout

```text
app/core/            config, database, append-only audit, model gateway, shared views
app/modules/<name>/  models.py · service.py (public contract) · controller.py (JSON /api)
web/                 Next.js views: one route folder per screen
data/RFP/            sample RFPs          data/knowledge_base/  business units, products, past responses
data/layout_cache/   frozen RFP parses    data/llm_cache/       frozen model answers (both committed)
reference/           earlier code lines, read-only, for porting
```
