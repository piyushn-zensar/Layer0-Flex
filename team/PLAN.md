# Layer 0 — Team Plan (internal)

Internal working document for the build team (Piyush, Atharv, Janvia). **Not client-facing**: client documents live in `Documents/` and follow the neutral-voice rule.

## 1. Goal and dates

| When | What the client sees | Stage |
|---|---|---|
| **Fri 9 Oct 2026** | Walkthrough of the **three screens** on the Syracuse RFP (seeded data is acceptable) + walkthrough document | S0 done, S1 started |
| **Fri 9 Oct 2026, evening IST** | 30-minute demo with the Zensar point of contact (agreed on the 8 Oct evening call) | S1–S2 |
| **Mon 12 Oct 2026** | A **functioning** run: real RFP → agentic reading → line items → product matching (EP² and the other units) → decisions → dispatch → unit responses → consolidation | S1–S3 |
| After 12 Oct | Consolidation drafting, knowledge-base feedback loop, change handling; a package the Zensar point of contact can install and run on a laptop once the build is robust (P-14) | S4–S5 |

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
| P-13 | Requirement history: every change kept and shown (who, when, original vs changed, all versions) from the audit log; a History view per line item on the Requirements page | S2 | Sat 10 Oct | P-06 |
| P-14 | Laptop package for the Zensar point of contact: one Windows setup script (venv, npm install, production build, demo seed) and one run script; works without Tesseract (committed layouts) and without an API key (`mock`); short install guide; walk the Zensar point of contact through it | S3 | Mon 12 Oct | P-08 |
| P-15 | Add a missed requirement by selecting lines on the RFP page (link it to its source without pasting the quote) | S4 | after 12 Oct | P-06 |
| P-16 | Group related line items into requirements with sub-requirements (grouping agent per page) and mark duplicates; review page and Traceability show groups | S2 | Fri 9 Oct | P-04 |
| P-17 | RAG indexes: long-term (knowledge base) and short-term per RFP (rebuilt on load); RFP search | S3 | Sat 10 Oct | P-07 |
| P-18 | Token cuts: rule-based bid-desk items, batched matcher per page with the catalog in a cached prefix, reader line-budget batching; regenerate answers | S3 | Sat 10 Oct | P-17 |
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
| A-11 | Knowledge-base queue: "Send to knowledge base" on a requirement, response or decision rationale puts it in a review queue; a curator page approves items into `past_responses` (RAG). Show as planned on 12 Oct if not built | S4 | after 12 Oct | A-02 |
| A-12 | Go/no-go summary: requirements by category; how they are satisfied (fully / partly / not, from matches and unit responses); a system recommendation clearly labelled as advice (e.g. "8 of 10 criteria met"); structured decision criteria instead of only a free-text rationale; placeholders for cost vs budget, delivery vs the RFP schedule and competitor information, marked "data not yet available" | S3 | Sun 11 Oct | A-06 |

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
| J-08 | Compliance matrix as a professional Excel file (.xlsx), generated deterministically (openpyxl, no model): title block, frozen header row, filters, column widths, wrapped text, offering-type colours, source page and lines; keep the CSV | S3 | Sun 11 Oct | — |

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

## 8. Call with the Zensar point of contact, 8 Oct 2026 evening: suggestions and where they go

Source: the call recording of 8 Oct (internal). The Zensar point of contact was positive about the progress and asked for a short demo on 9 Oct evening.

| # | Suggestion | Where it goes |
|---|---|---|
| 1 | Demo story: the RFP arrives, the tool breaks it into requirements with traceability, people review them side by side with the RFP, split one into sub-requirements, and add a requirement the tool missed (new technology areas), linked to its source | Built (P-06). Linking a new requirement by selecting lines on the page: P-15 |
| 2 | The system is the source of truth: every edit goes through change management on the requirement; who edited it, when, the original and every later version are kept | P-13 (history view); later changes after freeze: P-11 |
| 3 | Continuous improvement: while reviewing or writing a response, send an item to the knowledge base; it waits in a queue until the person who maintains the knowledge base includes it | A-11 |
| 4 | Build the knowledge base from prior proposals and their responses, so the system learns from both | A-02 (seed), A-11 (feedback), real past bids needed from the business units |
| 5 | Go/no-go must rest on a summary: the RFP, the requirements, how each is satisfied (fully, partly, not), a system recommendation; and later customer expectations (delivery date), internal budget, product cost and competitor information. Think through what the decider looks for, not only a rationale field | A-12 now; cost, budget and competitor data are roadmap (assume the data will exist later) |
| 6 | One professional-looking Excel file of all requirements (CSV is not enough) | J-08, generated deterministically, not by a model |
| 7 | Bid data must not go to a public model: non-public bids need a model running inside the enterprise (for example a small language model); the PoC may keep using the hosted API | Roadmap; open decision 1 in technical-architecture §14 |
| 8 | Ship a package the Zensar point of contact can run alone on a laptop, including the OCR dependency, and walk him through it once it is robust | P-14 (Tesseract is only needed on the parsing machine: the layouts are committed) |

**Positioning to keep in every document and demo:** Layer 0 is neither a CRM nor a CPQ tool; it is the bridge between them. People stay in charge: a company will not trust the tool alone until it is proven, so every agent output is reviewed.

**Roadmap (not in the PoC):**
- an enterprise-hosted model for non-public bids;
- cost, budget, delivery and competitor data feeding the go/no-go summary;
- model-assisted parsing of difficult pages inside the enterprise;
- learning from the business units' real prior proposals.


## 9. Iteration 2: changes from the 12 Oct review

Source of truth: [Documents/changes.md](../Documents/changes.md) (C-01 to C-22, client-facing) and the target design with all interface contracts in [Documents/technical-architecture.md](../Documents/technical-architecture.md) **section 16**. The as-built baseline is in `Documents/current-system/`.

Two team decisions on 13 Oct 2026 (Piyush): **the bid manager makes the final go/no-go call** (no configured approver role); **auth is simple JWT** (PyJWT, HS256, `JWT_SECRET`, 8 h, HttpOnly cookie `layer0_token` or `Authorization: Bearer`; no refresh tokens, no external identity service).

### 9.1 Order of work

There are no dates or checkpoints. Tasks are done one at a time, in the order of the tables in section 9.4; a task starts when the tasks it depends on are done. The repository owner may complete a teammate's task and mark it done in that teammate's tracker.

### 9.2 How to work in parallel this iteration

1. **Contracts first (technical-architecture §16.9).** Build against the contract, not against a teammate's unfinished code. Until a contract lands, use the stated fallback (for example `requirements.exceptions()` returns `[]`, missing response fields show as empty cells, `actor()` keeps returning a name).
2. **Stored values and API paths stay** (`/api/opportunities/...`, `approved`, `met` / `partial` / `not_met`). Change **labels**, not data, unless your task says otherwise. This keeps frozen answers, tests and the other modules green.
3. **New columns are nullable; there are no migrations.** After pulling a model change, run `reset-demo.cmd` (or `python -m scripts.seed_demo --reset`).
4. **Tests use a login helper** (`tests/conftest.py`, Piyush, P-20); `X-Actor` is gone.
5. Same rules as section 2: own files only, `[contract]` commits for unavoidable cross-module additions, `pytest -q` before every push, tracker updated with the commit.

### 9.3 New paths and owners (also in `.claude/rules/ownership.md`)

| Path | Owner |
|---|---|
| `app/core/auth.py`, `data/accounts.json`, `web/app/login/**`, `web/components/tour/TourProvider.tsx` (sign-in switching) | Piyush |
| `web/app/opportunities/[id]/assessment/**`, `data/knowledge_base/workflow.json`, the `comment` table (in `workpackages`) | Atharv |
| `web/tour/chapters/**`, `web/components/tour/TourOverlay.tsx`, `web/components/tour/TourLauncher.tsx`, `team/independent-rfp-candidates.md`, `team/spreadsheet-tools.md` | Janvia |

### 9.4 Tasks

One task at a time, top to bottom.

#### Piyush (core, auth, requirements, changes, ingestion)

| ID | Task | Changes | Depends on |
|---|---|---|---|
| P-19 | Terminology on own screens and messages: New bid, RFP step (**Document type** select: Main RFP, Addendum, Clarification / Q&A, Change request, Other; stored values unchanged), Requirements, Changes; "Bid … not found." in own modules' messages; label helpers in `web/lib/types.ts` | C-01 | — |
| P-20 | JWT auth backend: `app/core/auth.py` (PyJWT HS256, claims `sub`, `name`, `role`, `bu`, `exp`), `data/accounts.json` (section 9.5), `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, 401 on every other `/api` route, `web.user()` and `web.require()`; `actor()` returns the token's name; remove `X-Actor` and the "Bid Manager" default; `.env.example` (`JWT_SECRET`, `DEMO_PASSWORD`); `requirements.txt` (PyJWT); `tests/conftest.py` login helper | C-09 | — |
| P-21 | Web auth: `web/lib/api.ts` (no `X-Actor`, cookie sent, 401 goes to `/login`), sign-in page `web/app/login/page.tsx`, the walkthrough engine switches roles by signing in as a demo account (`ctx.signInAs`) | C-09 | P-20 |
| P-22 | Register and exception queue: reader items without verified source get status `exception` (never `approved`); the service refuses `approved` without `EXTRACTED`; `requirements.exceptions()`; `POST /api/requirements/{id}/resolve` (lines) and `/dismiss` (reason); anchored extraction items enter the register directly; Requirements page with Register and Exceptions tabs, no Approve / Reject buttons, "Exclude: not a requirement" with a reason | C-02, C-05 | — |
| P-23 | Snapshot and origins: `extraction_snapshot` table (append-only trigger), E1 on the first extract, a re-read only with a reason (E2); `requirement.origin`; corrections after publish create versions and the next baseline and return affected answers (`workpackages.return_for_change`); `POST /api/opportunities/{id}/corrections`; `GET …/extraction` and `…/extraction/{n}`; `POST …/baselines` = publish (no "every item decided" rule); change documents set `customer_change` and ask for the document type | C-04, C-05 | P-22 |
| P-25 | Enforce permissions in opportunities, ingestion, requirements and changes (technical-architecture §16.6 matrix) | C-09 | P-20 |
| P-27 | `GET /api/opportunities/{id}/activity`: the bid's audit log, filters entity / requirement / unit / person, read-only | C-16 | — |
| P-24 | Anchoring: the reader schema adds line references; verify against them; multi-span (`requirement.spans`), cross-page, hyphenation join, nearest occurrence; regenerate `read_requirements` (Azure) and score against the golden list; `coverage` in the extract result and on the RFP step | C-03 | P-22 |
| P-26 | Seed: drop the hyperscale bid; seed accounts; read and freeze the independent RFP (layout and reader answers) once chosen | C-11 | J-14 |
| P-28 | Investigations (priority 3): Word / Excel into the layout model (spike); past Flex responses for extraction (note) | C-18, C-19 | — |
| P-29 | Docs: mark built parts in technical-architecture §16 and changes.md; refresh `Documents/current-system/` at the end | all | everything |

#### Atharv (catalog, matching, decisions, work packages)

| ID | Task | Changes | Depends on |
|---|---|---|---|
| A-13 | Terminology on own screens and messages (Bid decision, My work, Product catalog); compliance shown as Fully / Partially / Non-compliant | C-01 | — |
| A-14 | Dispatch without go: needs a published baseline and participation only; a no-go stops dispatch and withdraws open work; tests | C-06 | — |
| A-15 | Criteria: `go_no_go.json` drops `cost_budget` and `competitors`; `delivery` becomes `schedule` ("Schedule: can the units meet the RFP's dates?") from unit responses; no "A-10" text in questions; coverage and matches-reviewed from validated responses; Bid decision page = go/no-go only, after assessment, warning when incomplete, **the bid manager decides** | C-10, C-06 | — |
| A-16 | Assessment screen `/opportunities/[id]/assessment`: bid summary (counts by category and offering, major sections, suggested units, open questions = `requirements.exceptions()` + needs-owner + rule warnings), participation, routing table, **Send for assessment** (`POST …/baselines` then `POST …/dispatch`), unit progress | C-05 | `exceptions()` returns `[]` until P-22 |
| A-17 | `data/knowledge_base/workflow.json` (respond: DE and PM; validate: PM; bid desk: BM; return with a question: BM); validation by the unit's configured role; inbox actions per role | C-07 | P-20 (roles); names until then |
| A-18 | Response fields on `assignment`: `reason`, `conditions`, `workaround`, `next_steps` (nullable); `reason` required for partial and non-compliant; `exception` no longer offered; inbox form; the fields in every assignment row (contract for J-11) | C-12 | — |
| A-19 | Needs an owner: product requirements without a unit are not dispatched and are listed; the bid desk only for rule-routed non-product items; capability gap = non-compliant with a reason | C-08 | — |
| A-20 | Enforce permissions in matching, decisions, workpackages and catalog | C-09 | P-20 |
| A-21 | `GET /api/assignments/{id}/history` and the history in the inbox | C-16 | — |
| A-22 | Questions and comments: `comment` table, `GET` / `POST /api/opportunities/{id}/comments`, `POST /api/comments/{id}/close`; on Assessment and in the inbox; open questions block consolidation | C-17 | — |
| A-23 | Matcher answers for the independent RFP | C-11 | P-26 |
| A-24 | Optional: summary counts link to Traceability filtered (`?category=`, `?offering=`) | C-20 | J-12 |

#### Janvia (shell, portfolio, trace, consolidation, walkthrough): lighter load, Sonnet

| ID | Task | Changes | Depends on |
|---|---|---|---|
| J-09 | Terminology in the shell (Bids, New bid), the portfolio (Bids list), trace and consolidation; stepper per technical-architecture §16.2 (RFP · Requirements · Traceability · Assessment · Compliance matrix · Bid decision; Changes separate) | C-01 | — |
| J-14 | Demo data: remove the hyperscale bid from `data/seed` (with P-26); find 2–3 independent public switchgear or substation RFPs (issuer, link, pages, why it is public) in `team/independent-rfp-candidates.md` | C-11 | — |
| J-10 | Shell: signed-in name, role and unit; **Sign out**; remove the Acting as picker (`GET /api/auth/me`) | C-09 | P-20 |
| J-11 | Compliance matrix screen (consolidation route): `GET /api/opportunities/{id}/compliance-matrix`, table, filters, row detail panel, hover reason on partial / non-compliant, source preview (page PNG and highlight boxes), Excel and CSV with the new columns | C-13, C-14 | A-18 fields (empty until) |
| J-12 | Three panes: enlarge / restore, a lock per pane, unit responses only after Send for assessment | C-15 | — |
| J-13 | Activity view (uses P-27) and links from matrix rows to response history (A-21) | C-16 | P-27, A-21 |
| J-15 | Walkthrough: chapters for the new words, steps and roles (sign-in instead of Acting as); the bubble never covers its target and can be minimised; `Documents/walkthrough.md` and screenshots | C-22, C-01 | everything |
| J-16 | Priority 3 note: spreadsheet tools (Row Zero, Quadratic, Gigasheet) against the built-in matrix, `team/spreadsheet-tools.md` | C-21 | — |

### 9.5 Demo accounts (contract for P-20, J-10, J-15, A-17)

`data/accounts.json` holds one account per person in today's people list (`bid.manager`; `ep2.pm`, `ep2.de`, `crown.pm`, `crown.de`, `anord.pm`, `anord.de`, `fpm.pm`, `fpm.de`, `jetcool.pm`, `jetcool.de`, `cloud.pm`, `cloud.de`, `ems.pm`, `ems.de`, `afs.pm`, `afs.de`) with `name` equal to today's display name, so stored actor names and frozen data stay valid, plus `admin`. The file is the roster: the accounts live in the table `user_account` (username, name, role, bu, password_hash) of a MySQL database (`MYSQL_*` in `.env`; the local SQLite store without `MYSQL_HOST`, as in the tests). On every start the API adds any account the table does not have yet, with `DEMO_PASSWORD` from `.env` as its starting password; an existing password is never overwritten. Passwords are stored as salted PBKDF2-SHA256 hashes; `.venv\Scripts\python -m scripts.set_password <username>` changes one.


## 10. Iteration 3: changes requested on 15 Oct 2026

Source of truth: [Documents/changes-iteration3.md](../Documents/changes-iteration3.md) (C-23 to C-34, client-facing): for each change what was asked, today's behaviour, the change, **integration feasibility**, checks and open questions. Section 6 there is the quick feasibility analysis; section 7 lists the open questions for the Zensar point of contact. Iteration-2 tasks still open on 15 Oct 2026 (A-17 blocked, A-23, A-24 in review, J-15, P-29) continue; section 10.5 says how they and the finished A-16 and A-20 fold in.

**Decisions of 15 Oct 2026 (Piyush):** the unit manager is the unit's product manager; sign-up lets the person choose any role except administrator (the administrator is seeded by the server); the Document ID and Instance ID are the IDs embedded in the file (PDF trailer `/ID` or XMP `xmpMM:DocumentID` / `xmpMM:InstanceID`; Word settings document ID), SHA-256 when absent; the catalog is read from `https://flex.com/products` and the official pages it links to, with every product-name version kept; the same document instance arriving for a different bid opens the existing bid. **Routing (16 Oct 2026):** only high-level, consolidated non-technical requirements stay with the bid desk; all other non-technical requirements go to the unit managers; technical requirements go to the designers and engineers.

### 10.1 Order of work

Same as 9.1: no dates or checkpoints, one task at a time in table order, a task starts when the tasks it depends on are done. Across the team, follow the order in 10.6. A task whose change has an open question uses the **proposed default** written in the change document unless the answer arrives first; note the default in the tracker.

### 10.2 Rules that change this iteration

1. **API paths change once (A-25, C-31).** A-25 goes first. Announce it in chat; everyone pushes and stops; A-25 lands as one commit (routes, web calls, tests, walkthrough); everyone pulls. From then on use `/api/bids/...`. Page addresses (`/opportunities/...`) stay unless open question 11 says otherwise.
2. **New tables, not new columns.** A new column on an existing table stops the server (`SchemaOutOfDate`) until `reset-demo.cmd`. Put new data in new tables where possible; after pulling a model change, run `reset-demo.cmd`. Accounts are in their own table and survive a reset.
3. **Frozen answers.** The matcher's prompt contains the product list; the catalog refresh (P-34) and evidence in prompts (P-37) change it. Pin the catalog and evidence versions per bid; only the task owner regenerates answers (section 2, rule 7).
4. **One permission model.** Role and unit from the token (`web.user`), never display-name comparisons (`workpackages._may_answer`, `validate`, the knowledge curator). P-30 provides the helpers; every module uses them.
5. Same as 9.2 otherwise: own files, `[contract]` commits for unavoidable cross-module additions, `pytest -q` before every push, tracker updated with the commit.

### 10.3 Ownership for iteration 3 (also in `.claude/rules/ownership.md`)

Several requested tasks touch another person's files. These moves hold for this iteration only.

| Path | Owner in iteration 3 | Task |
|---|---|---|
| Route decorators in every module, `/api/opportunities` calls in `web/**`, `tests/**`, `web/tour/**` (paths only) | Atharv, one announced commit | A-25 |
| `web/app/opportunities/[id]/requirements/**` (removed), `web/components/requirements/**`, the requirement controls in pane 2 of `web/app/opportunities/[id]/trace/**` | Atharv ([contract] Piyush, Janvia) | A-26, A-27 |
| **All RAG work** (C-28, C-29, C-33 and the assessment score of C-23): `app/modules/knowledge/**`, `app/modules/catalog/**`, the retrieval and evidence parts of `app/modules/matching/**` and the assessment score in `app/modules/decisions/**`, `data/knowledge_base/{products,catalog_items,past_responses}.json`, `data/llm_cache/{match_requirement,annotate_passages}/**`, `data/references/**`, `web/app/catalog/**`, `web/app/knowledge/**`, `web/components/knowledge/**`, the Knowledge review list in `web/app/inbox/`, `web/tour/chapters/knowledge.ts` | Piyush (decided 16 Oct 2026: RAG is entirely Piyush's; no RAG task or contract with Atharv or Janvia) | P-34 to P-39, P-41 |
| `web/app/signup/**`, `web/middleware.ts` | Piyush | P-31 |
| Pane components and pane addresses under `web/app/opportunities/[id]/trace/**` | Janvia | J-18 |

### 10.4 Tasks

One task at a time, top to bottom. Size: S hours, M one to two days, L several days, XL more than a week (rough, for comparison only).

#### Piyush (roles, auth, freeze, schedule, and all of RAG: catalog, knowledge, retrieval, score, Knowledge base page)

| ID | Task | Changes | Size | Depends on |
|---|---|---|---|---|
| P-30 | Unit roles in core: **Unit manager** and **Unit designer / engineer** (decided: the unit manager is the unit's product manager, so labels for the stored `product_manager` and `design_engineer`, accounts unchanged); role and unit helpers in `web.py` (`UNIT_MANAGER`, `UNIT_ENGINEER`, `same_unit(user, bu)`); labels in `web/lib/types.ts` and the user menu; the routing and validation rules themselves are A-17 | C-25 | S | — (routing decided 16 Oct) |
| P-31 | Sign-up and complete auth: `POST /api/auth/signup` (username, name, password of at least 10 characters, **role chosen by the person** except `admin`, unit required for unit roles); the `admin` account is seeded by the server (roster / `.env`), never by sign-up; `auth.init()` syncs roster accounts only; limit on repeated failed sign-in and sign-up attempts; web: `/signup` (linked from `/login`, role and unit selects), `web/middleware.ts` (no cookie → `/login?next=`), actions shown by role via `useMe()`; test: every write route × every role (403 where not allowed) | C-26 | M | P-30 |
| P-32 | Automatic freeze per document instance: Document ID and Instance ID read from the file (PDF trailer `/ID` via PyMuPDF `xref_get_key(-1, "ID")` or XMP `xmpMM:DocumentID` / `xmpMM:InstanceID`; `.docx` `word/settings.xml` document ID; SHA-256 when absent) into a new `document_identity` table (no new column on `document`); upload and from-sample look both up across bids: same pair already read → return the existing bid (web redirects to Requirement Traceability with a message); same Document ID with a new Instance ID → name the bid that holds the earlier instance and offer to add it there as a change document; a successful `extract` (read main RFP, at least one verified requirement, no failed page) calls `freeze` at once, otherwise nothing is frozen; Publish button and `POST …/baselines` route removed (the service stays); Send for assessment on the Assessment screen only dispatches ([contract] Atharv); re-read after the freeze refused (open question 7 default); test: knowledge approval, re-match and catalog refresh leave requirement rows and baselines unchanged; seed and walkthrough intake checked (a sample file now opens its seeded bid) | C-27 | M | P-31 (order); open question 7 |
| P-33 | Bid schedule and bid-manager approvals: new tables in `opportunities` (`bid_schedule`: due date, consolidation days; `unit_schedule`: bid, unit, estimated completion, note; `bid_approval`: bid, kind schedule / compliance, version, by, at, snapshot); unit manager sets the unit's date; `GET …/schedule` gives each unit, the latest date, the planned submission date and a warning after the due date; `POST …/approvals {kind}` bid manager only, schedule refused until every participating unit has a date, reopened by a later change; `schedule` criterion reads the dates ([contract] Atharv); cards on the Assessment screen and in My work ([contract] Atharv) | C-24 | M–L | P-30, A-17; open questions 3, 4 |
| P-34 | Catalog refresh: `catalog/scrape.py` reads `https://flex.com/products`, `/products/power-and-cooling`, `/products/power-modules` and the product pages of Anord Mardix, Crown Technical Systems, EP² and JetCool (automotive and components left out) with `httpx` and the standard-library HTML parser, one small parser per site that fails loudly on a layout change, robots.txt checked with `urllib.robotparser` (name, category, key features, link; menu links de-duplicated); tables `catalog_source`, `catalog_product` (stable key from the link) and `catalog_product_version` (name, features, link, valid from / to: a renamed product keeps every earlier name), `catalog_refresh`, `catalog_version`; FastAPI lifespan in `app/main.py`: refresh on start without blocking and every 24 h (`CATALOG_REFRESH_HOURS`, off in tests); a failure keeps the last good catalog; the matcher reads the catalog version pinned to the bid, so frozen answers keep working; Product catalog page shows source and last refresh | C-28 | M–L | — |
| P-35 | RAG R1, sources and passages: tables `kb_source` (collection, publisher, revision, scope, permissions, sha256, lifecycle, version) and `kb_passage` (source, page, lines, heading path, table, text, annotations); ingestion through the existing layout model (PDF, Word, Excel); model annotations through the gateway (frozen), stored beside the passage; document-level review by role; bid evidence filtered by bid inside the service; registration and review on a Sources tab of the Product catalog page | C-29 (1–4) | L | open question 9 (start with documents already in the repository) |
| P-36 | RAG R2, reviewed examples and feedback loop: `kb_item` (kind, example type, conditions, limits, sources, illustrative flag, review state, version) replaces `knowledge_learned.json`; "Nominate as a reviewed example" from corrections and validated answers (replaces Send to knowledge base); item-level review list in My work for the reviewing roles; seeded past responses marked illustrative and kept out of verified evidence | C-29 (3, 6), C-33 | M–L | P-35 |
| P-37 | RAG R3–R4, retrieval and explainable assessments: retrieval profiles per task (`data/knowledge_base/retrieval.json`); semantic and keyword results combined (rank fusion) with filters (collection, bid, review state, applicability, access); per-document vectors; cited evidence into the matcher and outline prompts, uncited claims dropped; `assessment_record` table (bid, task, evidence versions, citations, model, prompt hash, catalog version, conclusion, unresolved questions); `POST …/reassessments {reason}` keeps earlier records and never touches requirements; frozen matcher and outline answers regenerated once (Azure); rule R2 updated in technical-architecture | C-29 (5, 7) | XL | P-36, P-34 |
| P-38 | Executive summary with the assessment score: domain alignment, product-evidence coverage, specialist-review progress and preliminary feasibility (formula in `go_no_go.json`, labelled "not a probability"), evidence gaps, each count opening its requirements; summary records its evidence versions (in `decisions`, on the Assessment screen). If it is needed earlier, build it on today's matches and label it so | C-23 | L | P-37; open question 10 |
| P-39 | RAG R5, evaluation: `data/golden/rag_eval.json` reviewed by someone other than its author (coverage, interpretation, retrieval relevance, citation support, numerical comparisons, unknowns, isolation between bids); `scripts/eval_rag.py` reusing the model-guard record hook and the reader golden list; report | C-29 (8) | M | P-37; open question 9 (reviewers) |
| P-41 | Remove the Knowledge base page (moved from J-17, 16 Oct 2026): `web/app/knowledge/**`, the top-bar link in `TopNav.tsx`, the walkthrough chapter `knowledge.ts` and its mentions in other chapters; the knowledge API and its test stay | C-33 | S | P-36 (review list in My work: done) |
| P-40 | Docs: mark built parts in `Documents/changes-iteration3.md` and technical-architecture (new section 17); refresh `Documents/current-system/` (together with P-29 if it is still open) | all | M | everything |

#### Atharv (API rename, Requirement Traceability)

| ID | Task | Changes | Size | Depends on |
|---|---|---|---|---|
| A-25 | API paths: `/opportunities` → `/bids` in the 38 route decorators (10 modules), the `/api/opportunities` calls in 20 web files, about 318 uses in 19 test files and 5 walkthrough chapters; page addresses unchanged; one announced commit, `pytest -q`, `npm run build` and a walkthrough run before the push | C-31 | S–M | — (goes first; announce) |
| A-26 | Requirements into **Requirement Traceability**: Register / Exceptions, corrections with a reason (add, edit, split, merge, exclude), restore, link to lines and dismiss, line picker and history move into pane 2; step and page renamed; `/requirements` redirects to `/trace`; page removed; links updated (Changes, Bid decision, Compliance matrix pages, `OppSteps.tsx`, `TopNav.tsx`); walkthrough chapters `requirements`, `recap`, `navigation` updated with Janvia | C-30 | M | P-32 (Publish gone) |
| A-27 | Filtering and sorting on Requirement Traceability: filters category, offering type, unit, response state and compliance, source verified or exception, origin, page range, text search; sort by RFP order (default), ID, category, unit, compliance, last change; all in the page address (`?category=`, `?offering=` etc.), so A-24's links work | C-32, C-20 | S | A-26 |

#### Janvia (flexible workspace)

| ID | Task | Changes | Size | Depends on |
|---|---|---|---|---|
| J-18 | Flexible workspace (no dependency from 16 Oct: coordinate the edits to `trace/page.tsx` with A-26 in chat): the three panes become components that can also show alone at their own address; drag to reorder and resize in the main window (native drag and drop, CSS); **Open in new window** per pane; selection and Linked state shared through `BroadcastChannel` per bid; closing a window returns its pane; layout remembered in `localStorage`; walkthrough targets stay in the main window; checked with three windows | C-34 | M | — |

### 10.5 How open iteration-2 tasks fold in

| Task | Change from iteration 3 |
|---|---|
| A-16 Assessment screen (done) | Becomes the executive summary and routing: "Send for assessment" (publish, then dispatch) only dispatches after P-32; P-33 adds the schedule card and P-38 the assessment panel |
| A-17 workflow.json (unblocked 16 Oct) | Piyush cleared the blocker and built the validation part: `workflow.json`, `workpackages.validator(bu)`, `validate()` by the unit's configured validator (the bid manager may still return any answer with a question), seed and `test_poc_pass` validate as the unit's product manager, My work shows Validate to the unit manager only. Left for A-17: routing as decided on 16 Oct (technical items to designers / engineers; non-technical items to the unit managers of the participating units; only high-level, consolidated non-technical items on the bid desk) and the remaining inbox actions per role |
| A-20 permissions (done) | Its role checks switch to the unit roles with P-30 and A-17 (validation moves from the bid manager to the unit manager); P-31's role test covers these routes |
| A-24 drill-down (review) | The links exist; the Traceability side that applies `?category=` and `?offering=` is delivered by A-27 |
| J-15 walkthrough | Also waits for iteration 3 (pages removed, roles renamed, sign-up, automatic freeze, detachable panes) |
| P-29 docs | Can be combined with P-40 |

### 10.6 Order across the team

**Priority change (Piyush, 15 Oct 2026): RAG first.** Piyush starts with RAG; the others keep their order.

1. **RAG (Piyush only, 16 Oct 2026):** P-35 sources and passages (done), P-36 reviewed examples (done), P-41 Knowledge base page removed, P-34 catalog refresh (before P-37, so the frozen matcher answers are regenerated only once), P-37 retrieval in prompts, P-38 executive summary, P-39 evaluation. RAG routes live under `/api/knowledge/...` (or `/api/bids/...` when a route belongs to one bid), so A-25 does not touch them.
2. A-25 API rename (everyone pauses for it; Piyush pauses RAG for that commit).
3. P-30 roles, then A-17 on them (clears its blocker), then P-31 sign-up and authorization.
4. P-32 automatic freeze (Send for assessment becomes dispatch only).
5. A-26 Requirement Traceability, A-27 filters, J-18 detachable panes.
6. P-33 schedule and approvals.
7. J-15 walkthrough, P-40 (with P-29) docs.

### 10.7 Integration feasibility (internal summary)

No change is blocked technically (details in the change document, section 6). Internal points to watch:

- **Biggest rework:** RAG (P-37) reverses design rule R2 and regenerates the frozen matcher and outline answers; the catalog refresh (P-34) has the same effect unless the bid pins its catalog version.
- **Widest change:** the API rename (A-25) touches every module, 20 web files, 19 test files and the walkthrough; doing it first avoids conflicts with everything else.
- **Lost review window:** with the automatic freeze (P-32) every fix after extraction is a versioned correction and a new baseline; a re-read is no longer possible (open question 7).
- **Demo impact:** the one-click samples upload the seeded bids' files, so after P-32 they open the seeded bids; the walkthrough intake chapter changes (J-15).
- **Content, not code:** RAG needs real engineering references and verified datasheets from the business; published standards are licensed. The catalog page has names, key features and links but no datasheets.
- **Decided 15 Oct 2026:** unit manager = product manager (P-30); sign-up chooses the role, admin seeded (P-31; a known PoC limit: anyone can sign up as bid manager); embedded Document / Instance IDs with SHA-256 fallback (P-32; some tools omit or reuse the IDs); flex.com/products plus official unit product pages with name versions (P-34). Same instance for another bid opens the existing bid. Still open: re-reads after the freeze, references and reviewers, score formula.


## 11. Iteration 4: cloud and power focus, clearer assessment, standalone demo

Source: the latest review with the Zensar point of contact (notes added to the plan on 21 Oct 2026). No client-facing change document yet; the request items are numbered here C-35 to C-51 so that one can follow (P-52). Iteration-3 tasks still open (P-40, P-29) fold into P-52.

**One sequence, one person (decided 21 Oct 2026):** every iteration-4 change is made in one go, in the order of section 11.4, not divided across the team. The ownership map (sections 3 and 10.3) does not apply to these tasks, so no `[contract]` commits are needed; one commit per task.

**Delivery:** the corrected UI and the standalone HTML demo are delivered **together**, target **Wed 21 Oct 2026, before the Zensar point of contact's morning meeting**; an interim version only if it does not delay the final one. The HTML file is built **last**, from the system's final state after every current change (C-35 to C-46) is done and the whole workflow has been run on the RC-1 RFP (P-49, P-51). C-47 to C-51 are later (section 11.5): no tasks yet.

### 11.1 What was asked (now)

| ID | Ask | Today's behaviour | Task |
|---|---|---|---|
| C-35 | Focus on cloud and power infrastructure; test and demonstrate with relevant RFPs | Demo bids: Syracuse (switchgear), Logan (switchgear), the hyperscale sample | P-48 |
| C-36 | Headings: "Assessment" → **Assessment Summary**; "Domain Alignment" → **Technical Requirement Match** | Step, page heading and panel say Assessment; the measure says Domain alignment | P-42 |
| C-37 | Two demo scenarios: the synthetic 800 V "Grid to Chip" RFP, and the Syracuse switchgear procurement RFP focused on its power electronics requirements | The synthetic RFP is now in the repository: `data/RFP/samples/RC-1_Grid-to-Chip_RFP_Synthetic.docx` (RC-1, a 120 MW AI campus in six lots from the utility connection to the rack; about 6,400 words, 19 tables, 3 images; requirement IDs by lot, for example L2.04). It is not read, matched or seeded yet. Syracuse is shown in full | P-48 |
| C-38 | Technical match % over technical requirements only; legal, commercial, schedule and other non-technical items out of the denominator | `decisions.assessment_score` counts `matching.PRODUCT_CATEGORIES` = {technical, **compliance**}, so regulatory / legal compliance items sit in the denominator | P-43 |
| C-39 | Three clearly separate metrics: system-generated technical requirement match; **design engineer–reviewed** assessment (replaces "Product-evidence coverage"); specialist review progress | Four measures: domain alignment, product-evidence coverage (RAG citations), specialist-review progress (all items, not only technical), preliminary feasibility | P-43 |
| C-40 | Matching assesses the complete solution, not one requirement → one product / part number | Pane 3, My work and the compliance matrix show a matched product per requirement | P-46 |
| C-41 | Bid manager's first stage: review business relevance and route to teams; no approval of technical requirements there | The bid manager accepts / rejects / changes matches (A-20) and sees Approve compliance position on the Assessment step before any unit answer (P-33) | P-44 |
| C-42 | Delivery feasibility from the responsible teams (people, skills, manufacturing capacity, materials, cost); the bid manager uses their inputs and does not set the timeline; no full resource planning | The unit manager enters one estimated completion date per unit (P-33); nothing on people, skills, capacity, materials or cost | P-47 |
| C-43 | Compliance outcomes: **Compliant**, **Partially compliant**, **Compliant with changes** (a deviation from the requested specification); reviewed outcomes feed the go/no-go | Answers are met / partial / not_met (Fully / Partially / Non-compliant); no deviation outcome | P-45 |
| C-44 | Plain business terms throughout; labels understandable without the team explaining them | Internal words remain (domain alignment, product evidence, offering type, baseline, origin, exception queue, …) | P-42 (and each later task for its own screens) |
| C-45 | Standalone HTML demo: static data, no login, no live system, navigable by the Zensar point of contact alone; optional toggle for explanatory guidance (not finalised) | The demo needs the API, the web server and a sign-in | P-49, P-51 |
| C-46 | Corrected UI and HTML demo delivered together, 21 Oct before the morning meeting | — | all; order in 11.4 |

**Clarification (no new architecture):** real RFPs hold requirements in diagrams and tables, so processing must keep them; no new OCR architecture was asked. Word tables already become lines (cells joined with " | ", `ingestion/office.py`), and PDF ruled tables are in the layout (P-07). Images in a Word file are **not** read: P-48 checks RC-1's 3 images and, if one holds a requirement, records it as a known limit (or adds it as a correction with a reason).

### 11.2 Decisions and proposed defaults

Use the default unless an answer arrives first; note it in the tracker.

1. **Technical requirement (C-38):** default = category `technical` only. `compliance` items are listed beside the measure as "Standards and regulatory items (not in the percentage)". One definition, `matching.TECHNICAL_CATEGORIES`, used by the score and the summary counts. Open: should standards conformance (for example IEEE C37.20.2) count as technical?
2. **Design engineer–reviewed (C-39):** a technical requirement counts once the unit's designer / engineer has answered it and the unit manager has validated it. Shown as "n of N reviewed: x confirmed, y corrected" (corrected = the engineer changed the unit or solution, or answered Partially compliant, Compliant with changes or Non-compliant).
3. **Specialist review progress (C-39):** requirements (not items) sent to the units whose answers are all validated, out of requirements sent.
4. **Preliminary feasibility** leaves the Assessment Summary panel; the Bid decision reads the reviewed compliance outcomes (C-43) and the teams' feasibility inputs (C-42).
5. **Compliant with changes (C-43):** new stored value `deviation`; needs a reason and the proposed change (the existing `workaround` field, labelled "Proposed change"). Labels: Compliant (`met`), Partially compliant (`partial`), Compliant with changes (`deviation`), Non-compliant (`not_met`). Non-compliant stays: the request names three outcomes, but a "cannot be met" answer is still needed.
6. **Power electronics focus on Syracuse (C-37):** default = a saved Traceability filter link (technical; units CROWN, EP2, ANORD) on the demo bid. Open: the exact list of power electronics requirements.
7. **HTML demo (C-45, decided 21 Oct 2026):** one file `demo/layer0-demo.html` with all JavaScript and CSS inside it and no network use, built **after** every current change is done. It shows the **last view of the system** for the RC-1 bid once the whole workflow has run (P-49): every approval recorded and placeholder responses from the demo accounts. It is read-only: a role picker replaces sign-in (each role sees its own My work as it stands at the end); actions are not offered. Show guidance toggles short notes per screen. Syracuse stays a demo scenario in the live system only.

### 11.3 Paths added this iteration

`demo/layer0-demo.html` (generated, committed), `scripts/run_demo_workflow.py`, `scripts/export_demo_html.py`, `data/seed/demo_grid_to_chip.json`, the RC-1 entry in `SAMPLES` (`app/modules/opportunities/service.py`), its `data/layout_cache/` file and its frozen reader and matcher answers in `data/llm_cache/`.

### 11.4 Tasks (one at a time, top to bottom)

Size: S hours, M one to two days, L several days (rough, for comparison only).

| ID | Task | Changes | Size | Depends on |
|---|---|---|---|---|
| P-42 | Headings and plain terms: stepper, page heading, panel and walkthrough say **Assessment Summary**; one glossary of visible labels in `web/lib/types.ts` (internal word → plain word, for example domain alignment → technical requirement match, offering type → type of offer, exception queue → needs a source check, baseline → frozen version), applied on every screen and message; stored values and API paths unchanged | C-36, C-44 | M | — |
| P-43 | Assessment Summary measures: `matching.TECHNICAL_CATEGORIES` (default {technical}); `decisions.assessment_score` returns three measures: `technical_match` "Technical requirement match" (system-generated, technical only), `engineer_reviewed` "Reviewed by design engineers" (confirmed / corrected, decision 2), `review_progress` "Specialist review progress" (requirements, decision 3); preliminary feasibility off the panel; compliance items listed beside, not counted; gaps use the same denominator; `AssessmentPanel.tsx` updated; test: adding a legal, a commercial and a schedule item leaves the percentage unchanged | C-36, C-38, C-39 | S–M | P-42 |
| P-44 | Bid manager's first stage = business relevance and routing: on the Assessment Summary the bid manager records participation, routes requirements to teams (changes the unit only) and sends; accepting / rejecting / correcting a technical match moves to the unit's designer / engineer (`web.require` in matching, buttons by role); Approve compliance position leaves the Assessment step and appears on the Bid decision once validated answers exist (`ScheduleCard.tsx`); test: the bid manager gets 403 on accepting a technical match | C-41 | M | — |
| P-45 | Compliance outcomes: `deviation` in `COMPLIANCE` and `OFFERED`, `NEEDS_REASON` += deviation, `workaround` required for it and labelled "Proposed change"; labels Compliant / Partially compliant / Compliant with changes / Non-compliant in My work, Bid decision, compliance matrix, exports and hand-off; the `go_no_go.json` `compliance` criterion counts each outcome separately and the Bid decision shows the four counts with links; test | C-43 | M | — |
| P-46 | Solution-level wording: pane 3, My work, compliance matrix and hand-off show "Proposed solution: unit · solution area" with products as examples, not a matched product or part number; matcher answers and stored data unchanged | C-40 | S | P-42 |
| P-47 | Delivery feasibility from the teams: new table `unit_feasibility` (bid, unit, factor people / skills / manufacturing capacity / materials / cost, status ok / constraint, note, by, at) beside `unit_schedule`; the unit manager enters the unit's estimate and the five factors; engineers' technical feasibility = their answers (P-45); the Schedule card shows each unit's estimate, constraints and the latest date; the bid manager **accepts the teams' estimates** (no date field for the bid manager); the `schedule` criterion reads them; no resource planning; test | C-42 | M | P-45 |
| P-48 | Demo scenarios, cloud and power: RC-1 (`RC-1_Grid-to-Chip_RFP_Synthetic.docx`) added to `SAMPLES` and listed first; layout frozen (`scripts.freeze_layout`), read and matched (live Azure, answers frozen; RC-1 lots map to EP2, CROWN, ANORD, FPM, JetCool and the cloud unit), table rows checked against the 19 tables (requirement IDs such as L2.04 kept in the text), the 3 images checked (clarification above); Syracuse: the power electronics filter link (decision 6) and listed second; model guard 0 misses | C-35, C-37 | M | P-42 to P-47 (so the frozen answers and screens are final) |
| P-49 | Full workflow run on RC-1, the HTML's source state: `scripts/run_demo_workflow.py` drives the API as the demo accounts (section 9.5) on a fresh seed: upload and automatic freeze; bid manager reviews the summary, records participation, routes and sends; each unit's designer / engineer answers its technical items and each unit manager its non-technical items with **placeholder responses** (marked illustrative; all four outcomes used, with reasons and proposed changes where required); unit managers enter delivery estimates and the five factors, then validate; bid desk items answered; bid manager accepts the schedule, approves the compliance position, records the go/no-go with criteria; compliance matrix and response outline generated (frozen); every approval recorded; the script is repeatable (same result on a fresh seed) and leaves no open item | C-45 | M | P-48 |
| P-50 | Walkthrough and screenshots for the new labels, outcomes, bid manager flow and feasibility inputs (`web/tour/chapters`, `Documents/walkthrough.md`, `Documents/images/`) | C-36, C-41, C-42, C-43, C-44 | S–M | P-42 to P-47 |
| P-51 | Final HTML (decision 7): `scripts/export_demo_html.py` reads the API after P-49 (bids list, RC-1 RFP pages with highlighted sources, Requirement Traceability with the three panes, Assessment Summary, My work per role, compliance matrix, Bid decision, Activity) and writes `demo/layer0-demo.html`: internal JS and CSS (`globals.css` inlined), data embedded as JSON, page images embedded, no login (role picker), Show guidance toggle, no network; opens by double-click from `file://`; checked at 1440 and 390 px against the live screens | C-45, C-46 | M–L | P-49, P-50 (built last) |
| P-52 | Docs: `Documents/changes-iteration4.md` (client-facing register of C-35 to C-51, neutral voice), built parts marked; P-40 and P-29 folded in | all | M | everything |

**Known limits of the RC-1 demo state (P-48, P-49; 21 Oct 2026):**
- A correction keeps its source on one page: the corrected texts of the requirements cut at a page break (L3.11, CT-02, L2.09, L4.11, IF-09) are complete, but their verbatim quote and highlight still end at the page break; the continuation lines are not highlighted, and the split-off tails are excluded from the register. A source span across pages would need a change to the correction API.
- The response outline is a first draft from one live model pass (frozen, replayed in mock mode). Points for the bid manager to edit before it goes to a customer: the executive summary is written from the opening requirements and overstates compliance; the technical chapter does not name the capability gaps (the outline lists them under "To add or confirm").
- The RFP due date (1 Dec 2026) is a placeholder derived from the RFP's schedule chart (an image the reader does not read). The outline drafts were regenerated once (live, 6 calls) on the final state and replay in mock mode.
- Demo account names stay "<unit> Product Manager" (the role is shown as Unit manager); the seeded activity log stamps the scripted steps within seconds of each other.

### 11.5 Later (no tasks yet)

| ID | Ask | Note for when it starts |
|---|---|---|
| C-47 | Excel upload beside the compliance matrix export: export, share with people without access, collect and consolidate, upload the reviewed sheet | The export columns become the import contract; each row keeps its assignment ID |
| C-48 | Reassess after an upload: reviewed responses update the affected assessments and the workflow continues; until then the recorded status stays | Same path as a unit answer (history, validation) |
| C-49 | Dependencies between teams: some requirements need input or approval from several teams before the assessment is final | Today one assignment per unit, each judged alone; needs an "all of" rule per requirement |
| C-50 | Enterprise identity and access management for production | The current JWT sign-in stays for the PoC |
| C-51 | Evaluate established workflow frameworks (cloud or open-source) that can be configured and integrated | Guidance only, no replacement now; candidates go in `team/investigations.md` |

## 12. Iteration 5: real product selection from the spreadsheet and the configurator

Source: written direction from the Zensar point of contact, added to the plan on 22 Oct 2026, with the supplied files: the Flex Power Modules export `PowerModules-1791937030.xlsx` (721 parts, all Active, exported 14 Oct 2026), the configurator `rfp_configurator.py`, and 15 datasheets / brochures (Anord Mardix, Crown, JetCool CDUs, IBAR, Databar, MCMS, the 2026 power brochure). All copied unchanged to `data/axiom_products/`. Request items are numbered C-52 to C-66.

**Priority:** the spreadsheet and the supplied script must drive real product selection in the demo (C-52 to C-62). Catalog merging and the all-products table are part of that. Document linking, RAG and images support it; full image extraction and a visual redesign come after the working demo.

**Two people, two lanes (decided 22 Oct 2026):** Piyush = data, configurator, matching, assessment (P-53 to P-59). Janvia = Product Catalog page, documents, images (J-19 to J-23). Atharv has no tasks this iteration. The lanes meet only through the contract in 12.3, committed **before** either starts; after that neither waits for the other (Janvia builds against the sample file; Piyush reads Janvia's manifests when they exist). Neither edits the other's paths (12.4); a contract change is agreed in chat first and committed by Piyush with `[contract]`.

### 12.1 What was asked

| ID | Ask | Today | Task |
|---|---|---|---|
| C-52 | Merge the spreadsheet into the catalog: exact part numbers, enrich, add missing, keep web data / images / links, variants separate, evaluation boards apart from power modules | Catalog = web pages (`catalog_items.json`, scraped versions); FPM has 32 entries at **series** level (BMR491 …), the spreadsheet is at **part** level (BMR3141011/001 …): **0 exact part matches** | P-53 |
| C-53 | Normalise and validate: resolve the two Series columns; numeric voltage, power, current, efficiency, dimensions in one unit each; empty = unknown; keep interfaces, isolation, regulation, mounting, paralleling, multiple outputs | Free-text `specs` string per item | P-53 |
| C-54 | Sources and conflicts: source and import date per value; flag spreadsheet / web disagreements; an empty import never overwrites; repeat imports create no duplicates | Web versions only | P-53 |
| C-55 | RFP requirements → the configurator's input (keep requirement text and document reference, normalise units, list missing inputs); match on the merged catalog | The matcher picks a unit / product by model judgement | P-54 |
| C-56 | Group requirements by component or subsystem; evaluate related constraints together; one search per component; system-level checks separate | One requirement at a time | P-55 |
| C-57 | Real recommendations: part numbers with relevant specs, linked to the catalog, module quantities where the configurator supports it, with assumptions and review flags | Solution area per requirement (P-46) | P-56 |
| C-58 | Explain outcomes: satisfied / failed / cannot assess per requirement; match, near match, insufficient information; explain no-match; never relax silently | — | P-56 |
| C-59 | Screens: "Assessment Summary" (done in P-42); "Domain Alignment" → **Technical Requirement Matching** (P-42 said "Technical requirement match"); requirement-to-product comparison in the technical view; coverage, gaps, assumptions, pending reviews in the summary; a script run is not proof of feasibility | Three measures (P-43) | P-57 |
| C-60 | Product Catalog: table of **all** products (part number, family, type, status, input / output voltage, power, current, efficiency, interface, source); search, filter, sort, pages; a row opens full specs, images, documents; extra spreadsheet fields by column picker or details view | Product cards by unit, Published tab | J-19, J-20 |
| C-61 | Assumptions and limits visible: RFP-stated vs defaults (redundancy, design margin, module count); unverified specs and open checks flagged; fixed-ratio output, paralleling, thermal derating, peak power, certification checked before suitability; unsupported checks named (multiple outputs) | — | P-56 |
| C-62 | Validate the whole flow on a power and a cloud RFP: extraction → configurator → products → catalog details; one match and one no-match / missing-information case; recommendations checked against the supplied data | RC-1 and Syracuse seeded | P-59 |
| C-63 | Link datasheets, brochures and other documents to the right part or family, applicability clear | The Sources tab lists reference documents, not per product | J-21 |
| C-64 | Index the supporting documents into RAG with document / page references (operating conditions, compatibility, certifications); numeric filtering stays the basis of matching | RAG over `data/references/` (P-35, P-37) | P-58 |
| C-65 | Verified product images per product or family, source kept, placeholder when uncertain | None | J-22 |
| C-66 | Catalog presentation: specs, match explanations, datasheet access, navigation; image and layout polish after the core works | — | J-23 |

### 12.2 Decisions and proposed defaults

Use the default unless an answer arrives first; note it in the tracker.

1. **The two Series columns (C-53):** column C "Series" is the same for all 721 rows ("Power Modules") → `product_line`. Column E "Series" is the series code for modules (BMR314) and an ordering code for evaluation boards (ROA170259) → `series`; for boards, "Compatibility" (BMR314) → `evaluates`. To confirm with the Zensar point of contact.
2. **Matching to the web catalog (C-52):** exact part number first (0 hits today). A part whose `series` equals a web FPM model (BMR316, BMR491 …) becomes a **variant** under that web entry (`family_key`, for example `FPM/BMR316`); the web entry stays as it is. Parts with no web series are added as new products. The 25 evaluation boards are `product_type = evaluation_board` and are never recommended as a power module.
3. **Units (C-53):** V, W, A, %, mm, as in the spreadsheet headers; `null` = unknown, never 0. A spreadsheet value's source is `{source: "spreadsheet", row, imported: "<date>"}`.
4. **Conflicts (C-54):** compared only where the web text gives a number for the same field and series (voltage range, power, current, efficiency); a disagreement is stored on the product for review and both values are kept. The spreadsheet does not replace web text.
5. **Configurator (C-55):** vendored as `app/modules/configurator/rfp_configurator.py` with the smallest changes (load from the merged catalog instead of the .xlsx; return data, not files). Its own defaults (redundancy, design margin, Axiom limits, CDU table, certifications found) are shown as **assumptions / unverified**, as the script itself marks them. `pandas` goes into `requirements.txt` (the script needs it; `numpy` comes with it).
6. **Requirement input for the script:** the bid's frozen requirements are mapped to the script's `system` / `board` fields by one model call per component group (frozen in `data/llm_cache/configurator_inputs/`), each value kept with its requirement ID and verbatim text; the script's own `parse_requirements` validates it. No regex extraction.
7. **Outcome words (C-58):** Match (every stated constraint met), Near match (fails one constraint, from the script's relaxation table; **never presented as a match**), Insufficient information (a needed input is missing), No match (with the reason). Per requirement: Satisfied / Not satisfied / Cannot assess yet.
8. **Feasibility wording (C-59):** the summary always says "configurator result, pending engineering review"; the go/no-go never treats a run as proof.
9. **Scope of numeric matching:** board-level DC/DC modules (FPM) from the spreadsheet; system level (Axiom module, cooling, certifications) from the script's `configure_system` checks, shown separately. Switchgear, busbar and CDU documents are evidence only (no numeric table was supplied for them).

### 12.3 Contract between the two lanes (committed first, P-53a)

**`data/knowledge_base/power_modules.json`** (written by `scripts/import_power_modules.py`, Piyush), and `data/knowledge_base/power_modules.sample.json` (20 real rows: modules with and without a web family, multiple outputs, evaluation boards, one conflict):

```json
{"_note": "...", "imported": "2026-10-22", "source_file": "data/axiom_products/PowerModules-1791937030.xlsx",
 "items": [{
  "part_number": "BMR3141011/001", "component_id": 3, "product_line": "Power Modules", "series": "BMR314",
  "evaluates": null, "product_type": "power_module", "family_key": "FPM/BMR314", "status": "Active",
  "application": ["Data Center and Cloud"], "interfaces": ["PMBus"], "attributes": ["Unregulated", "PMBus", "Peak Power"],
  "isolation": "Non-Isolated", "isolation_v": null, "regulation": "Unregulated/Fixed Ratio",
  "mounting": "LGA", "package_type": "Baseplate", "footprint": "Other", "paralleling": "None", "multi_output": null,
  "vin_min_v": 38, "vin_max_v": 60, "vout_min_v": 9.5, "vout_max_v": 15, "vout_typ_v": null,
  "power_w": 800, "power_peak_w": 1500, "current_a": 62, "current_peak_a": null, "efficiency_pct": 97.5,
  "length_mm": 28, "width_mm": 17.8, "height_mm": 9.65,
  "outputs": [{"n": 2, "v_min": null, "v_nom": null, "v_max": null, "power_w": null, "current_a": null}],
  "sources": {"power_w": {"source": "spreadsheet", "row": 3, "imported": "2026-10-22"}},
  "web": {"source_url": "https://...", "specs": "..."},
  "conflicts": [{"field": "power_w", "spreadsheet": 800, "web": 750, "web_url": "https://..."}],
  "verified": false}]}
```

**API (Piyush, in `app/modules/catalog/`):**
- `GET /api/catalog/products?q=&type=&family=&status=&interface=&application=&sort=&dir=asc|desc&page=1&size=50` → `{total, page, size, items: [row]}`; a row = part_number, family_key, product_type, status, vin_min_v, vin_max_v, vout_min_v, vout_max_v, power_w, current_a, efficiency_pct, interfaces, source ("spreadsheet", "web", "both"), has_conflict. Web-only catalog items are rows too (numbers null).
- `GET /api/catalog/product?part=<part number>` (query parameter: part numbers contain "/") → the full item plus `documents` and `images` joined from Janvia's manifests (empty lists while the files are missing).

**Manifests (Janvia):**
- `data/axiom_products/documents.json`: `[{file, title, doc_type: datasheet|brochure|catalogue|one_pager, family_keys: [], part_numbers: [], applies: part|family|general, pages: {"<family_key or part>": [page, …]}, publisher, note}]`; `family_keys` use the existing catalog IDs (`ANORD-LVSB/MDX`, `FPM/BMR316`, …).
- `data/axiom_products/images.json` and `data/axiom_products/images/`: `[{file, family_key, part_numbers: [], source_file, page, kind: photo|illustration, verified: true|false}]`; `verified: false` → the page shows a placeholder.

### 12.4 Paths per lane (iteration 5 only; also in `.claude/rules/ownership.md`)

| Piyush | Janvia |
|---|---|
| `scripts/import_power_modules.py`, `data/knowledge_base/power_modules*.json` | `data/axiom_products/documents.json`, `images.json`, `images/**` |
| `app/modules/configurator/**` (new), `app/modules/catalog/**` (product API), `matching/**`, `decisions/**` | `scripts/extract_product_images.py` |
| `web/components/assessment/**`, Traceability pane 3 technical comparison (`.../trace/`, this iteration only), `web/lib/**` (contract types) | `web/app/catalog/**` (moves from Piyush to Janvia), `web/components/catalog/**` (new) |
| `data/llm_cache/configurator_inputs/`, RAG index of `data/axiom_products/*.pdf`, `requirements.txt`, `tests/test_configurator*.py`, `tests/test_power_modules*.py` | `tests/test_catalog_manifests.py` |
| `Documents/changes-iteration5.md`, walkthrough assessment chapters | `web/tour/chapters/catalog.ts`, walkthrough catalog chapter |

`data/axiom_products/` (the supplied files) is read-only for both.

### 12.5 Tasks

Size: S hours, M one to two days, L several days.

**Piyush (top to bottom)**

| ID | Task | Changes | Size | Depends on |
|---|---|---|---|---|
| P-53a | Contract first: the 12.3 shapes as `power_modules.sample.json` (20 real rows) and TypeScript types in `web/lib/types.ts`; tell Janvia | C-52, C-60 | S | — |
| P-53 | Spreadsheet import `scripts/import_power_modules.py` → `power_modules.json`: two Series columns split (decision 1), numbers and units (3), empty = unknown, evaluation boards typed, variants under the web series (2), per-value sources and import date, conflicts against web numbers (4), empty never overwrites, re-run gives the same file (keyed by part number); the catalog product API (12.3); tests: idempotent re-run, empty cell, board vs module, a conflict | C-52, C-53, C-54 | M | P-53a |
| P-54 | Configurator in the app: vendor the script (decision 5), `pandas` in requirements, `load_catalog` reads the merged catalog (power modules only), map frozen requirements to its `system` / `board` input with requirement ID, verbatim text and document reference (decision 6), units normalised, missing inputs listed; its self-test passes on the merged catalog | C-55 | M | P-53 |
| P-55 | Component groups: requirements grouped by requested component / subsystem (one model call per bid, frozen, with the requirement IDs); one configurator search per board-level group; system-level checks (`configure_system`) run once and shown apart | C-56 | M | P-54 |
| P-56 | Recommendations and explanations: per group, candidate parts with their relevant specs and links to the catalog row (`/catalog/product?part=…`); module quantity and redundancy where the script computes them, each default marked "assumption, not in the RFP"; per requirement Satisfied / Not satisfied / Cannot assess yet; Match / Near match / Insufficient information / No match with reason (decision 7); unverified specs, conflicts and the checks the script cannot do (fixed-ratio output, paralleling, thermal derating, peak power conditions, certification applicability, multiple outputs) listed as open engineering checks; stored per bid (new table `component_match`) | C-57, C-58, C-61 | L | P-55 |
| P-57 | Assessment screens: "Technical requirement match" → **Technical Requirement Matching** (`web/lib/types.ts`, panel, tour, walkthrough); Traceability pane 3 shows the requirement ↔ product comparison; the Assessment Summary shows coverage, gaps, assumptions and pending engineering reviews with decision 8's wording; the go/no-go reads none of it as proof | C-59 | M | P-56 |
| P-58 | RAG over the supplied documents: the 15 PDFs as a new collection `product_documents` (page references), tagged with families / parts from Janvia's `documents.json` when present (untagged otherwise, re-tagged on the next index run); evidence for operating conditions, compatibility and certifications in the explanations; numeric filtering unchanged | C-64 | M | P-53 (soft: J-21) |
| P-59 | Validate end to end on RC-1 (cloud, 800 V) and Syracuse (power): extraction → groups → configurator → recommendations → catalog details; at least one match and one no-match or missing-information case, written down with the parts checked by hand against the spreadsheet; seed and frozen answers refreshed; `Documents/changes-iteration5.md` (C-52 to C-66, neutral voice); HTML demo re-exported if still used | C-62 | M | P-57, P-58 |

**Janvia (top to bottom; Sonnet; no live model calls needed)**

| ID | Task | Changes | Size | Depends on |
|---|---|---|---|---|
| J-19 | All-products table on the Product Catalog page (new tab "All products", the default): the C-60 columns, search, filters (type, family, status, interface, application), sort on every column, pages of 50, column picker for the extra spreadsheet fields (dimensions, isolation, regulation, mounting, paralleling, peak values, outputs 2 and 3), source and conflict badges; reads `GET /api/catalog/products`; until P-53 lands, a small local loader serves `power_modules.sample.json` (removed afterwards) | C-60 | M | P-53a only |
| J-20 | Product details (row → side panel, deep link `/catalog/product?part=`): all fields grouped (input, output, mechanical, interfaces, isolation, multiple outputs), each value with its source and date, conflicts with both values, "Unknown" for nulls, evaluation board ↔ module links, family link to the web entry, documents (open at the right page) and images from the manifests | C-60, C-66 | M | J-19 |
| J-21 | Documents manifest `data/axiom_products/documents.json`: each of the 15 PDFs read and tied to family / part with applicability and the pages per product (12.3); unclear ones `general` with a note; `tests/test_catalog_manifests.py` checks every file exists and every key is a real catalog ID or part number | C-63 | M | — |
| J-22 | Images: `scripts/extract_product_images.py` (PyMuPDF, already installed) pulls images from the PDFs into `data/axiom_products/images/`; `images.json` with source file and page; `verified: true` only when the page names the product beside the image, else `false` (placeholder) | C-65 | M | — |
| J-23 | Catalog presentation and guidance: polish of table and details, navigation family ↔ variants ↔ boards, catalog tour chapter and walkthrough catalog chapter; screenshots after P-59 | C-66 | S–M | J-20 (screenshots after P-59) |

### 12.6 How the lanes meet

- First: P-53a (contract and sample) is committed before anything else. From then on J-19 to J-22 need nothing from Piyush, and P-53 to P-57 need nothing from Janvia.
- Soft links, no waiting: the product API returns empty `documents` / `images` until J-21 / J-22 land; P-58 tags documents once `documents.json` exists; P-56 links to `/catalog/product?part=…`, which J-20 serves; J-23's screenshots come after P-59.
- Ask early: decisions 1 and 2 (Series meaning, series-level linking) with the Zensar point of contact.
