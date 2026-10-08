# Ownership — edit only what the current teammate owns

Identify the teammate with `git config user.name`. If it does not clearly map to one of the three, ask.

| Owner | Paths |
|---|---|
| **Piyush** | `app/core/**`, `app/main.py`, `app/modules/{opportunities,ingestion,requirements,changes}/**`, `web/lib/**`, `web/package.json`, `web/next.config.ts`, `web/app/opportunities/new/**`, `web/app/opportunities/[id]/page.tsx`, `web/app/opportunities/[id]/{requirements,changes}/**`, `data/layout_cache/**`, `data/golden/**`, `data/llm_cache/read_requirements/**`, `scripts/**` (except seed data), `requirements*.txt`, `tests/test_smoke.py`, `Documents/**` (except `walkthrough.md`), `.claude/**` |
| **Atharv** | `app/modules/{catalog,matching,decisions,workpackages}/**`, `web/app/{inbox,catalog}/**`, `web/app/opportunities/[id]/decisions/**`, `web/components/matching/**`, `data/knowledge_base/**`, `data/llm_cache/match_requirement/**` |
| **Janvia** | `app/modules/{trace,consolidation}/**` (except `consolidation/agent.py`, which is Piyush's), `web/app/layout.tsx`, `web/app/globals.css`, `web/components/shell/**`, `web/app/portfolio/**`, `web/app/opportunities/[id]/layout.tsx`, `web/app/opportunities/[id]/{trace,consolidation}/**`, `data/seed/**`, `Documents/walkthrough.md`, `Documents/images/**` |
| **Each person** | only their own `team/tracker/<name>.md` |

Shared files (`tests/test_smoke.py`, `requirements.txt`, `app/main.py`, `web/lib/types.ts`): non-owners may only append, and must say so in chat.

If the task needs a change in a file the teammate does not own, **stop and use the `contract-change` skill**: it
drafts the request for the owner. Do not edit the file.
