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
| P-07 | Ruled tables via pdfplumber in the layout model; re-freeze layout | S2 | Sun 11 Oct | todo | |
| P-08 | Switch the demo from seed to real extraction; end-to-end dry run; fix integration bugs | S3 | Mon 12 Oct AM | todo | |
| P-09 | Port model-change guard (M16) as a golden test over `llm_cache` | S4 | after 12 Oct | todo | |
| P-10 | Response-outline drafting agent (`consolidation/agent.py`, called by Janvia's page) | S4 | after 12 Oct | todo | |
| P-11 | Changes module: addendum → delta vs. baseline → new versions → responses returned | S5 | after 12 Oct | todo | |

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
