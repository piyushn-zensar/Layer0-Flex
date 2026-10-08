# Tracker: Atharv

Only Atharv edits this file. Update it when a task starts, finishes or gets blocked, and commit it with the work
(`[A-xx] tracker: ...`). Status: `todo` · `doing` · `blocked` · `review` · `done`.
Task details and dependencies: [team/PLAN.md](../PLAN.md).

| ID | Task | Stage | Due | Status | Notes / commit |
|---|---|---|---|---|---|
| A-01 | Clone, `.venv`, seed, run; read `technical-architecture.md` §7 and the port table in `architecture-overview.md` | S0 | Thu 8 Oct | doing | cloned, `.venv`, pytest green; seed/run and reading still to do |
| A-02 | Refine `business_units.json` / `products.json` / `past_responses.json`: EP² products as first-class components, better retrieval keywords, keep "illustrative" labels | S2 | Fri 9 Oct | todo | |
| A-03 | Matcher agent: generate and commit `data/llm_cache/match_requirement/` for the Syracuse line items; tune prompt | S2 | Sat 10 Oct | todo | |
| A-04 | One requirement → several units (schema returns a list; dispatch creates one assignment per unit) | S2 | Sat 10 Oct | todo | |
| A-05 | Screen-3 actions: accept / reject / change unit-product-offering (`web/components/matching/MatchActions.tsx`, used by Janvia's trace page) | S2 | Sat 10 Oct | todo | |
| A-06 | Evidence: port scope detection + tiers (M3/M4) and validation rules (M5) from `reference/v0.3.0` into matching evidence; show in the decisions evidence pack | S3 | Sun 11 Oct | todo | |
| A-07 | Inbox: link to the main RFP and to each line item's highlighted source; returned items reopen; "submit all" for a unit | S3 | Sun 11 Oct | todo | |
| A-08 | Multi-unit sample: convert `data/RFP/samples/rfp_hyperscale_campus.txt` to PDF (`scripts/txt_to_pdf.py`) and add it as a second seeded opportunity | S3 | Mon 12 Oct AM | todo | |
| A-09 | Routing payloads (M8): per-unit hand-off JSON (CTO items → CPQ seed) as a download | S4 | after 12 Oct | todo | |
| A-10 | v1.1 bid / portfolio checks (`reference/v1.1/logic`) in the evidence pack, constants labelled placeholders | S4 | after 12 Oct | todo | |

## Blocked on / needs from others

| Date | Need | From | Status |
|---|---|---|---|

## Log

| Date | Done | Next |
|---|---|---|
| 8 Oct | Fixed in matching / decisions / workpackages: re-run matching no longer overwrites accepted, manual or rejected matches; a rejected match no longer brings back an older proposal; dispatch needs a "go" (409 otherwise); invalid actions, outcomes and compliance values get 422, unknown IDs 404. Regression test appended to `tests/test_smoke.py` | finish A-01 (seed, run, read §7), then A-02 |
