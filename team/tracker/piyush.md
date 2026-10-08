# Tracker: Piyush

Only Piyush edits this file. Update it when a task starts, finishes or gets blocked, and commit it with the work
(`[P-xx] tracker: ...`). Status: `todo` · `doing` · `blocked` · `review` · `done`.
Task details and dependencies: [team/PLAN.md](../PLAN.md).

| ID | Task | Stage | Due | Status | Notes / commit |
|---|---|---|---|---|---|
| P-01 | Push skeleton, docs, plan, trackers, `.claude/`; confirm both teammates can run it | S0 | Thu 8 Oct | done | pushed ea5b26e |
| P-12 | Finish the Next.js switch: `npm run build` clean, all pages checked against the API | S0 | Fri 9 Oct AM | done | build clean; all 12 pages + API via proxy 200; fixed per-opportunity document IDs; check trace screen in a browser |
| P-02 | OCR for pages with no text layer (Tesseract TSV via `subprocess`, `config.TESSERACT_CMD`, optional when missing); page 83 test; re-freeze layout | S1 | Fri 9 Oct | done | whole-page OCR (Tesseract TSV, optional when missing); p.83 now 106 lines; layout re-frozen, byte-identical on re-run |
| P-03 | Contents-page and header/footer detection; exclude from the reader's input | S1 | Fri 9 Oct | todo | |
| P-04 | Run reader agent on the full Syracuse PDF (`LLM_PROVIDER=azure`, GPT-4o), tune prompt/chunking, commit `data/llm_cache/read_requirements/` | S1 | Fri 9 Oct | todo | |
| P-05 | Golden requirement list for Syracuse (`rfp-golden` agent) + recall/precision check script | S1 | Sat 10 Oct | todo | |
| P-06 | Review actions: inline edit, split, merge, add a missed requirement (by quote) | S2 | Sat 10 Oct | todo | |
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
| 8 Oct 2026 | P-01 pushed; P-12 build verified + per-opportunity document IDs; P-02 OCR, layout re-frozen | P-03 contents and header/footer detection |
