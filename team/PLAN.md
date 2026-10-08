# Layer 0 — Team Plan (internal)

Internal working document for the build team (Piyush, Atharv, Janvia). **Not client-facing**: client documents live in `Documents/` and follow the neutral-voice rule.

## 1. Goal and dates

| When | What the client sees | Stage |
|---|---|---|
| **Fri 9 Oct 2026** | Walkthrough of the **three screens** on the Syracuse RFP (seeded data is acceptable) + walkthrough document | S0 done, S1 started |
| **Mon 12 Oct 2026** | A **functioning** run: real RFP → agentic reading → line items → product matching (EP² and the other units) → decisions → dispatch → unit responses → consolidation | S1–S3 |
| After 12 Oct | Consolidation drafting, knowledge-base feedback loop, change handling | S4–S5 |

The design is fixed: [Documents/technical-architecture.md](../Documents/technical-architecture.md). Do **not** redesign. Wire in, port, test.

## 2. How we work (avoid merge conflicts)

1. **Trunk-based on `main`.** Small commits, pushed often (at least every 1–2 hours of work).
2. **Before every push:** `git pull --rebase` → `.venv\Scripts\python -m pytest -q` → push. Never `--force`.
3. **Only edit files you own** (section 3). Need something from another module? Ask its owner in chat; they add it to their `service.py`. If you are blocked and the owner is offline, add the smallest function yourself and put `[contract]` + the owner's name in the commit message.
4. **Modules talk only through `service.py`.** The smoke test fails otherwise.
5. **Update your own tracker** (`team/tracker/<you>.md`) when a task starts, finishes or is blocked. Never edit someone else's tracker.
6. **Sync points (IST):** 10:00, 14:00, 18:00 — two lines in chat: done / next / blocked.
7. **Model answers are code.** `data/llm_cache/` is committed. Only the owner of a task generates answers for that task (`read_requirements` → Piyush, `match_requirement` → Atharv). Never hand-edit cache files.
8. **Parsing runs on one machine.** Piyush's machine is the parsing machine (Tesseract OCR and any parsing-only packages from `requirements-parsing.txt`). After every parser change he runs `python -m scripts.freeze_layout <pdf>` and commits `data/layout_cache/`. Everyone else installs only `requirements.txt` and gets identical pages, line numbers and highlights from the committed layout. OCR code must stay optional: without Tesseract a page is flagged, never a crash.
9. **Commit messages:** `[P-04] requirements: cache reader answers for Syracuse` (task ID, module, what).

## 3. Ownership map

| Path | Owner | Notes |
|---|---|---|
| `app/core/**`, `app/main.py` | Piyush | Shared foundation. Ask before changing a signature |
| `data/layout_cache/**`, `requirements-parsing.txt`, `scripts/freeze_layout.py` | Piyush | frozen parses; parsing-only dependencies |
| `app/modules/opportunities/**`, `ingestion/**`, `requirements/**`, `changes/**` | Piyush | |
| `app/modules/catalog/**`, `matching/**`, `decisions/**`, `workpackages/**` | Atharv | |
| `web/app/opportunities/[id]/decisions/`, `web/app/inbox/`, `web/app/catalog/`, `web/components/matching/` | Atharv | Next.js pages for his modules |
| `web/app/opportunities/new/`, `web/app/opportunities/[id]/page.tsx`, `.../requirements/`, `.../changes/`, `web/lib/**`, `web/package.json`, `web/next.config.ts` | Piyush | Next.js pages for his modules; API client |
| `app/modules/trace/**`, `consolidation/**` | Janvia | three screens, portfolio, coverage, compliance matrix |
| `web/app/layout.tsx`, `web/app/globals.css`, `web/components/shell/**`, `web/app/portfolio/`, `web/app/opportunities/[id]/layout.tsx`, `.../trace/`, `.../consolidation/` | Janvia | shell, CSS, three screens, portfolio, consolidation |
| `data/knowledge_base/**` | Atharv | business units, products (EP² first), past responses |
| `data/seed/**`, `scripts/seed_demo.py` | Janvia (seed data) / Piyush (script) | |
| `data/llm_cache/<task>/` | owner of that task | see rule 7 |
| `Documents/**` | Piyush | Janvia writes `Documents/walkthrough.md` |
| `tests/test_smoke.py`, `requirements.txt`, `.claude/**` | Piyush | others: append-only, announce in chat |
| `team/tracker/<name>.md` | that person | |

## 4. Stages (each one leaves the app runnable)

| Stage | Done when | Owner(s) |
|---|---|---|
| **S0 Skeleton** ✅ | All modules run; seeded demo; three screens; smoke test green | Piyush |
| **S1 Reading** | OCR + contents/furniture detection; reader agent run on the full Syracuse PDF with answers cached; golden list | Piyush |
| **S2 Matching** | Matcher answers cached; EP² + unit catalogs refined; multi-unit per requirement; manual override on screen 3 | Atharv (+ Janvia UI) |
| **S3 Workflow** | Decisions evidence, dispatch, inbox, checklist responses, validation work on the real extraction; multi-unit sample | Atharv, Janvia |
| **S4 Consolidation** | Coverage, compliance matrix, response outline agent, validated answers into the knowledge base | Janvia, Piyush, Atharv |
| **S5 Changes** | Addendum → delta → only affected requirements re-versioned, responses returned | Piyush |

## 5. Tasks

Status lives in each person's tracker; this table is the master list. Janvia's load is deliberately lighter (Pro plan: use Sonnet; avoid long agent runs).

### Piyush — RFP parsing (ingestion + reader agent), requirements, core, integration

| ID | Task | Stage | Due | Depends on |
|---|---|---|---|---|
| P-01 | Push skeleton, docs, plan, trackers, `.claude/`; confirm both teammates can run it | S0 | Thu 8 Oct | — |
| P-12 | Finish the Next.js switch: `npm run build` clean, all pages checked against the API | S0 | Fri 9 Oct AM | — |
| P-02 | OCR for pages with no text layer (Tesseract TSV via `subprocess`, `config.TESSERACT_CMD`, optional when missing); page 83 test; re-freeze layout | S1 | Fri 9 Oct | — |
| P-03 | Contents-page and header/footer detection; exclude from the reader's input | S1 | Fri 9 Oct | — |
| P-04 | Run reader agent on the full Syracuse PDF (`LLM_PROVIDER=azure`, GPT-4o), tune prompt/chunking, commit `data/llm_cache/read_requirements/` | S1 | Fri 9 Oct | P-03, API key |
| P-05 | Golden requirement list for Syracuse (`rfp-golden` agent) + recall/precision check script | S1 | Sat 10 Oct | P-04 |
| P-06 | Review actions: inline edit, split, merge, add a missed requirement (by quote) | S2 | Sat 10 Oct | — |
| P-07 | Ruled tables via pdfplumber in the layout model; re-freeze layout | S2 | Sun 11 Oct | — |
| P-08 | Switch the demo from seed to real extraction; end-to-end dry run; fix integration bugs | S3 | Mon 12 Oct AM | P-04, A-03 |
| P-09 | Port model-change guard (M16) as a golden test over `llm_cache` | S4 | after 12 Oct | P-05 |
| P-10 | Response-outline drafting agent (`consolidation/agent.py`, called by Janvia's page) | S4 | after 12 Oct | J-05 |
| P-11 | Changes module: addendum → delta vs. baseline → new versions → responses returned | S5 | after 12 Oct | — |

### Atharv — knowledge base, matching, decisions, work packages

| ID | Task | Stage | Due | Depends on |
|---|---|---|---|---|
| A-01 | Clone, `.venv`, seed, run; read `technical-architecture.md` §7 and the port table in `architecture-overview.md` | S0 | Thu 8 Oct | P-01 |
| A-02 | Refine `business_units.json` / `products.json` / `past_responses.json`: EP² products as first-class components, better retrieval keywords, keep "illustrative" labels | S2 | Fri 9 Oct | — |
| A-03 | Matcher agent: generate and commit `data/llm_cache/match_requirement/` for the Syracuse line items; tune prompt | S2 | Sat 10 Oct | P-04, API key |
| A-04 | One requirement → several units (schema returns a list; dispatch creates one assignment per unit) | S2 | Sat 10 Oct | — |
| A-05 | Screen-3 actions: accept / reject / change unit-product-offering (`web/components/matching/MatchActions.tsx`, used by Janvia's trace page) | S2 | Sat 10 Oct | — |
| A-06 | Evidence: port scope detection + tiers (M3/M4) and validation rules (M5) from `reference/v0.3.0` into matching evidence; show in the decisions evidence pack | S3 | Sun 11 Oct | — |
| A-07 | Inbox: link to the main RFP and to each line item's highlighted source; returned items reopen; "submit all" for a unit | S3 | Sun 11 Oct | — |
| A-08 | Multi-unit sample: convert `data/RFP/samples/rfp_hyperscale_campus.txt` to PDF (`scripts/txt_to_pdf.py`) and add it as a second seeded opportunity | S3 | Mon 12 Oct AM | A-04 |
| A-09 | Routing payloads (M8): per-unit hand-off JSON (CTO items → CPQ seed) as a download | S4 | after 12 Oct | — |
| A-10 | v1.1 bid / portfolio checks (`reference/v1.1/logic`) in the evidence pack, constants labelled placeholders | S4 | after 12 Oct | — |

### Janvia — three screens, portfolio, consolidation, walkthrough (lighter load)

| ID | Task | Stage | Due | Depends on |
|---|---|---|---|---|
| J-01 | Clone, `.venv`, seed, run; open the three screens; read `.claude/CLAUDE.md` | S0 | Thu 8 Oct | P-01 |
| J-02 | Polish the three screens for the walkthrough: layout, legend (CTO / Semi-custom / ETO), selected-row and highlight styles, empty states | S1 | Fri 9 Oct AM | — |
| J-03 | Walkthrough document `Documents/walkthrough.md` with screenshots (`Documents/images/`), neutral voice | S1 | Fri 9 Oct | J-02 |
| J-04 | Portfolio: per-unit progress bars, status chips, link to each unit's inbox | S2 | Sat 10 Oct | — |
| J-05 | Consolidation page: blocking items link to the three screens; compliance-matrix columns reviewed with the bid-manager view | S3 | Sun 11 Oct | — |
| J-06 | Monday demo click-path checklist (in the walkthrough) and a dry run with Piyush | S3 | Mon 12 Oct AM | P-08 |
| J-07 | Response-outline view (uses P-10) | S4 | after 12 Oct | P-10 |

## 6. Port map (existing modules → where they go)

All earlier code is in `reference/` (read-only). Full table with known defects: `Documents/architecture-overview.md`.

| v0.3.0 module | New home | Task |
|---|---|---|
| M1 ingestion | `ingestion` | P-02, P-07 |
| M2 extraction (regex) | **replaced** by the reader agent | P-04 |
| M3 scope, M4 tiers, M5 validation, M13 solver | `matching` evidence | A-06 |
| M6 evidence contract | every agent returns rationale + evidence | all |
| M7 approval gates | named-person decisions (`decisions`, `requirements.freeze`) | done in S0 |
| M8 routing payloads | `workpackages` | A-09 |
| M9 connectors | `catalog.bom()` → BOM source connector | A-09 |
| M10 model seam | `core/llm.py` | done in S0 |
| M11 provenance, M17 registry | `requirements` (anchoring, record) | done in S0 |
| M14 coverage, M15 proposal checker | `consolidation` | J-05, P-10 |
| M16 model-change guard | golden test over `llm_cache` | P-09 |

## 7. Risks

| Risk | Mitigation |
|---|---|
| No API key on Fri → no agent answers | Seeded demo already runs on cached/seed data; generate answers as soon as a key is available |
| Reader agent misses or over-splits requirements | Golden list (P-05) + human review screen; contents pages excluded before the model sees them |
| Merge conflicts | Ownership map, small commits, `pull --rebase` before push |
| Atharv's health / availability | A-tasks ordered so S2 (matching) lands first; Piyush picks up A-07/A-08 if needed |
| Janvia's Pro limits | UI and writing tasks; Sonnet only; no long agent runs |
