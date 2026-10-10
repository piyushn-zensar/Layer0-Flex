# Tracker: Piyush

Only Piyush edits this file. Update it when a task starts, finishes or gets blocked, and commit it with the work
(`[P-xx] tracker: ...`). Status: `todo` · `doing` · `blocked` · `review` · `done`.
Task details and dependencies: [team/PLAN.md](../PLAN.md).

| ID | Task | Stage | Due | Status | Notes / commit |
|---|---|---|---|---|---|
| P-01 | Push skeleton, docs, plan, trackers, `.claude/`; confirm both teammates can run it | S0 | Thu 8 Oct | done | pushed ea5b26e |
| P-12 | Finish the Next.js switch: `npm run build` clean, all pages checked against the API | S0 | Fri 9 Oct AM | done | build clean; all 12 pages + API via proxy 200; fixed per-opportunity document IDs; check trace screen in a browser |
| P-02 | OCR for pages with no text layer (Tesseract TSV via `subprocess`, `config.TESSERACT_CMD`, optional when missing); page 83 test; re-freeze layout | S1 | Fri 9 Oct | done | whole-page OCR (Tesseract TSV, optional when missing); p.83 now 106 lines; layout re-frozen, byte-identical on re-run |
| P-03 | Contents-page and header/footer detection; exclude from the reader's input | S1 | Fri 9 Oct | done | furniture (repeated band lines) + contents pages marked; reader skips them; Syracuse: p.54 contents, 346 furniture lines, no known requirement hidden |
| P-04 | Run reader agent on the full Syracuse PDF (`LLM_PROVIDER=azure`, GPT-4o), tune prompt/chunking, commit `data/llm_cache/read_requirements/` | S1 | Fri 9 Oct | done | re-run one page per call: 840 proposed, 808 anchored (96%); 100 answers cached; `scripts/freeze_reader.py` |
| P-05 | Golden requirement list for Syracuse (`rfp-golden` agent) + recall/precision check script | S1 | Sat 10 Oct | review | golden list 361 items (78 uncertain), AI-drafted, needs a person's review; reader recall 26% -> 92% after one page per call; precision 54% (granularity) |
| P-06 | Review actions: inline edit, split, merge, add a missed requirement (by quote) | S2 | Sat 10 Oct | done | edit (text+category), split (re-anchored parts), merge (keeps all boxes), add missed (anchored), bulk approve/reject, filters + search; freeze needs every item decided; regression test |
| P-07 | Ruled tables via pdfplumber in the layout model; re-freeze layout | S2 | Sun 11 Oct | done | 34 ruled tables (data sheet p72-74 linked), kept beside the lines; lines unchanged so all frozen answers still match; drawing sheets skipped; byte-identical re-run. Next: show table rows to the reader (needs re-generating answers for table pages) |
| P-08 | Switch the demo from seed to real extraction; end-to-end dry run; fix integration bugs | S3 | Mon 12 Oct AM | review | `seed_demo` builds Syracuse from the real extraction (840 → 353 requirements, all approved and frozen, decided, dispatched); dry run: all pages 200, Traceability 0.84 MB in 0.4 s. Blocked on matcher answers for the 353 (retrieval-only matches are poor) |
| P-09 | Port model-change guard (M16) as a golden test over `llm_cache` | S4 | after 12 Oct | todo | |
| P-10 | Response-outline drafting agent (`consolidation/agent.py`, called by Janvia's page) | S4 | after 12 Oct | done | executive summary + chapters by category; drafts only from validated answers (numbered, no IDs in the prompt), every paragraph cites them (guard drops the rest), gaps to add or confirm; both RAG indexes shown as references, kept out of the prompt; mock fallback shows the answers as they are; 8 frozen drafts (Syracuse real + quick seed, hyperscale); JSON + Markdown routes; test |
| P-11 | Changes module: addendum → delta vs. baseline → new versions → responses returned | S5 | after 12 Oct | todo | |
| P-13 | Requirement history: every change kept and shown (who, when, original vs changed, all versions) from the audit log; a History view per line item on the Requirements page | S2 | Sat 10 Oct | done | History link per line item: every version (original + each edit, who, when, reason) and a timeline (proposed, edits, approve/reject, split, merge, freeze) from the audit log; regression test |
| P-14 | Laptop package for the Zensar point of contact: one Windows setup script (venv, npm install, production build, demo seed) and one run script; works without Tesseract (committed layouts) and without an API key (`mock`); short install guide; walk the Zensar point of contact through it | S3 | Mon 12 Oct | review | setup.cmd / start.cmd / reset-demo.cmd + INSTALL.md; no OCR engine or API key needed for the demo; clean-copy install tested; walk-through with the Zensar point of contact still to do |
| P-15 | Add a missed requirement by selecting lines on the RFP page (link it to its source without pasting the quote) | S4 | after 12 Oct | todo | from the 8 Oct call (plan §8) |
| P-16 | Group related line items into requirements with sub-requirements; mark duplicates (from the 9 Oct run: 840 items, many near-duplicates) | S2 | Fri 9 Oct | review | grouping agent + text-based duplicates; Syracuse 840 → 353 requirements (167 groups / 631 sub-requirements) + 23 duplicates; review page shows groups, Ungroup; Traceability lists sub-requirements |
| P-17 | RAG: long-term index (products, past responses) and a short-term index per RFP (rebuilt on every load); frozen Azure embeddings with offline keyword fallback; "Search this RFP" | S3 | Sat 10 Oct | review | semantic search finds e.g. the 25 kA momentary rating (p.62) for "short-circuit rating"; 300 KB frozen vectors; test added |
| P-18 | Token cuts: rule-based bid-desk items, matcher one call per page with the catalog as a cached prefix, reader packs short pages | S3 | Sat 10 Oct | review | calls 518 → 208, input 464k → 251k tokens, ~$2.14 → ~$1.44 per new RFP; reader recall unchanged (91.9%); stale answers removed; offline demo rebuilt (Crown 96, EP² 7, bid desk 245) |

## Blocked on / needs from others

| Date | Need | From | Status |
|---|---|---|---|

## Log

| Date | Done | Next |
|---|---|---|
| 8 Oct 2026 | P-01 pushed; P-12 build verified + per-opportunity document IDs; P-02 OCR; P-03 contents/furniture; layout re-frozen; config accepts the team .env names | P-04 reader agent on Azure GPT-4o (needs the saved .env) |
| 8 Oct 2026 | Azure GPT-4o live call OK (structured output, 4.8 s); reader strips copied L-labels from quotes; reviewed A-01 + J-02/J-03, all checks green; legend wording aligned to agreed offering definitions | P-04 reader agent on the full Syracuse RFP |
| 8 Oct 2026 | P-04 done (reader agent on Azure, answers frozen; anchoring tolerates an added final full stop); navigation simplified (3 top-level destinations, 5-step workflow stepper, Traceability naming); UI layout pass (one container, spacing scale, calmer tables) | P-05 golden list; P-06 review actions |
| 8 Oct 2026 | P-06 review actions; P-05 golden list + scorer; reader changed to one page per call (recall 26% -> 92%) | decide line-item granularity (840 vs 361) with the bid-manager view; P-07 tables |
| 9 Oct 2026 | Review fixes (core, opportunities, ingestion, requirements, web lib + 2 pages): path traversal closed; freeze once, needs read RFP + approved items, nothing editable after; 404 for unknown opportunities; parallel-safe IDs; requirement IDs never reused; re-read refused once review starts; forward-only status; extract 39 s -> 6 s; one main RFP; no server path in responses; actor header capped; readable API errors; reading problems shown. Regression test added; 15 of 17 repro findings gone (2 are Janvia's) | P-07 tables; P-08 demo on real extraction |
| 9 Oct 2026 | P-13 requirement history (versions + timeline, from the audit log) | P-08 needs the line-item granularity decision; P-14 laptop package |
| 9 Oct 2026 | P-14 laptop package (double-click setup and start; offline demo) | walk-through with the Zensar point of contact; P-08 after the line-item decision |
| 9 Oct 2026 | P-16 grouping (840 → 353 requirements), duplicates marked | Atharv: re-run the matcher on the 353 requirements; P-08 demo on the real extraction |
| 9 Oct 2026 | P-08 demo on the real extraction + dry run | matcher answers for the 353 requirements (A-03 re-run) |
| 9 Oct 2026 | P-07 ruled tables in the layout, re-frozen | P-14 walk-through; P-09 model-change guard |
| 10 Oct 2026 | P-17 RAG indexes (long-term + per-RFP), RFP search; stale-page fix | token cuts: rule-based bid-desk items, batched matcher per page, reader line-budget batching |
| 10 Oct 2026 | P-18 token cuts (−60% calls, −46% input tokens) | J-06 demo checklist + dry run; remaining team tasks |
| 10 Oct 2026 | A-10 bid and portfolio checks in the go/no-go evidence; demo checklist refreshed after the P-18 renumbering; P-10 + J-07 response outline (agent + view) | A-11 knowledge-base queue |
| 10 Oct 2026 | A-11 knowledge-base queue (module, buttons, curator page) | P-11 changes module |
