# Tracker: Atharv

Only Atharv edits this file. Update it when a task starts, finishes or gets blocked, and commit it with the work
(`[A-xx] tracker: ...`). Status: `todo` · `doing` · `blocked` · `review` · `done`.
Task details and dependencies: [team/PLAN.md](../PLAN.md).

| ID | Task | Stage | Due | Status | Notes / commit |
|---|---|---|---|---|---|
| A-01 | Clone, `.venv`, seed, run; read `technical-architecture.md` §7 and the port table in `architecture-overview.md` | S0 | Thu 8 Oct | done | cloned, `.venv`, seeded, API :8000 + web :3000 up, pytest green; §7 + port table read |
| A-02 | Refine `business_units.json` / `products.json` / `past_responses.json`: EP² products as first-class components, better retrieval keywords, keep "illustrative" labels | S2 | Fri 9 Oct | done | EP² kept to the 3 documented families; keywords from sample-RFP wording + v0.3.0 rules; 8 past responses (all 6 units); catalog self-check: 15 product + 3 unit asserts |
| A-03 | Matcher agent: generate and commit `data/llm_cache/match_requirement/` for the Syracuse line items; tune prompt | S2 | Sat 10 Oct | done | 174 answers, live GPT-4o; page-header candidates + prompt rules + answer guard; runner `python -m app.modules.matching.service <pdf>`; re-run it when the reader adds items |
| A-04 | One requirement → several units (schema returns a list; dispatch creates one assignment per unit) | S2 | Sat 10 Oct | done | `Match.units` (main unit first, max 3, bu/product_id keep the main unit); dispatch one assignment per participating unit; stubbed test; matcher answers to regenerate (schema changed) |
| A-05 | Screen-3 actions: accept / reject / change unit-product-offering (`web/components/matching/MatchActions.tsx`, used by Janvia's trace page) | S2 | Sat 10 Oct | done | accept / reject / change (several units, or bid manager) on screen 3; route `POST /opportunities/{opp}/requirements/{req}/match`; 2 lines in Janvia's trace page ([contract] Janvia) |
| A-06 | Evidence: port scope detection + tiers (M3/M4) and validation rules (M5) from `reference/v0.3.0` into matching evidence; show in the decisions evidence pack | S3 | Sun 11 Oct | done | `matching/checks.py`: M3 scope (frozen requirements, REQ citations), M4 tier fail-safe (flags only), M5 R-001..R-004, M13 LV solver (included per port map / design 15); data `spinco_layers.json`, `engineering_rules.json`; evidence pack + decisions page. Known limit: v0.3.0 keyword "prefabricated" puts layer 3 in scope on Syracuse |
| A-07 | Inbox: link to the main RFP and to each line item's highlighted source; returned items reopen; "submit all" for a unit | S3 | Sun 11 Oct | done | "Open the RFP" per opportunity + "show highlighted source" per line (links, per plan); Return needs a note (design 7.5), returned items reopen with the note; "Submit all answered rows" |
| A-08 | Multi-unit sample: convert `data/RFP/samples/rfp_hyperscale_campus.txt` to PDF (`scripts/txt_to_pdf.py`) and add it as a second seeded opportunity | S3 | Mon 12 Oct AM | todo | |
| A-09 | Routing payloads (M8): per-unit hand-off JSON (CTO items → CPQ seed) as a download | S4 | after 12 Oct | todo | |
| A-10 | v1.1 bid / portfolio checks (`reference/v1.1/logic`) in the evidence pack, constants labelled placeholders | S4 | after 12 Oct | todo | |
| A-11 | Knowledge-base queue: "Send to knowledge base" on a requirement, response or decision rationale puts it in a review queue; a curator page approves items into `past_responses` (RAG). Show as planned on 12 Oct if not built | S4 | after 12 Oct | todo | from the 8 Oct call (plan §8) |
| A-12 | Go/no-go summary: requirements by category; how they are satisfied (fully / partly / not, from matches and unit responses); a system recommendation clearly labelled as advice (e.g. "8 of 10 criteria met"); structured decision criteria instead of only a free-text rationale; placeholders for cost vs budget, delivery vs the RFP schedule and competitor information, marked "data not yet available" | S3 | Sun 11 Oct | todo | from the 8 Oct call (plan §8) |

## Blocked on / needs from others

| Date | Need | From | Status |
|---|---|---|---|

## Log

| Date | Done | Next |
|---|---|---|
| 8 Oct | Fixed in matching / decisions / workpackages: re-run matching no longer overwrites accepted, manual or rejected matches; a rejected match no longer brings back an older proposal; dispatch needs a "go" (409 otherwise); invalid actions, outcomes and compliance values get 422, unknown IDs 404. Regression test appended to `tests/test_smoke.py` | finish A-01 (seed, run, read §7), then A-02 |
| 8 Oct | A-01 done. A-02 done: retrieval now ranks rack-mounted PDUs → Anord PDU, SEL-751 relay / relay programming → EP² relay panel; Syracuse demo matches unchanged | A-03 (needs Azure settings; depends on P-04) |
| 8 Oct | A-03 done: 174 Syracuse matches (134 bid manager, 39 Crown, 1 EP²; 0 wrong-unit, 0 invalid). Found reader gap: no items from spec pages 59–61, 63–67 | reader fix ([contract] Piyush), then re-run matcher for new items |
| 8 Oct | Reader gap fixed by Piyush (f2f81b2, 840 items). A-04 done: several units per requirement, one assignment per unit | matcher run over the settled list (~840 calls) before Mon 12 Oct; A-05 |
| 8 Oct | A-05 done. System test fixes (my modules): go/no-go and dispatch need a frozen baseline; dispatch sends only frozen approved items and withdraws work that no longer fits; only the unit answers (assigned/returned), only the Bid Manager validates submitted work; participation = active units, at least one; 404/403/409 instead of 500s; evidence shows unreviewed matches. Findings for Piyush and Janvia published | matcher run before Mon; A-06; A-07 (Return note per design 7.5) |
| 8 Oct | A-06 done: engineering checks in the evidence pack. On the 840-item list they flag Cloud / Flex / JetCool matches as outside the RFP's scope | matcher run before Mon; A-07 |
| 9 Oct | A-07 done: inbox links to the RFP and each highlighted source, Return with a required note, returned items reopen, Submit all | A-12 go/no-go summary; matcher run before Mon |
