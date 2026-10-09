# Tracker: Janvia

Only Janvia edits this file. Update it when a task starts, finishes or gets blocked, and commit it with the work
(`[J-xx] tracker: ...`). Status: `todo` · `doing` · `blocked` · `review` · `done`.
Task details and dependencies: [team/PLAN.md](../PLAN.md).

| ID | Task | Stage | Due | Status | Notes / commit |
|---|---|---|---|---|---|
| J-01 | Clone, `.venv`, seed, run; open the three screens; read `.claude/CLAUDE.md` | S0 | Thu 8 Oct | done | app run locally: walkthrough screenshots taken from it (60faf7a) |
| J-02 | Polish the three screens for the walkthrough: layout, legend (CTO / Semi-custom / ETO), selected-row and highlight styles, empty states | S1 | Fri 9 Oct AM | done | fed8c0a legend, selected row, status badges, empty states, a11y; follow-ups 0e7f3d8 client wording, bd946ed error message instead of endless loading |
| J-03 | Walkthrough document `Documents/walkthrough.md` with screenshots (`Documents/images/`), neutral voice | S1 | Fri 9 Oct | review | 60faf7a walkthrough + 12 screenshots. Review 9 Oct: not client-ready yet; checklist below. Refresh: 10 screenshots from the current UI, text on current names, checklist 1, 3, 4, 10, 11 done; items 2, 5-9 open; 93e695a |
| J-04 | Portfolio: per-unit progress bars, status chips, link to each unit's inbox | S2 | Sat 10 Oct | done | per-unit two-segment bars (validated, awaiting validation), status chips, unit names link to `/inbox/<unit>`, "not dispatched" when empty; `web/app/portfolio/page.tsx` + `globals.css` only; build and pytest green; cb08a93 |
| J-05 | Consolidation page: blocking items link to the three screens; compliance-matrix columns reviewed with the bid-manager view | S3 | Sun 11 Oct | done | parts A+B 3827902 (blockers panel by reason, All/Open filter, links to Traceability, coloured badges); part C: compliance matrix CSV gets Assignment status and Responded by (appended, earlier columns unchanged) and a UTF-8 byte order mark for Excel; self-check and smoke test added; hash after push |
| J-06 | Monday demo click-path checklist (in the walkthrough) and a dry run with Piyush | S3 | Mon 12 Oct AM | todo | |
| J-07 | Response-outline view (uses P-10) | S4 | after 12 Oct | todo | |
| J-08 | Compliance matrix as a professional Excel file (.xlsx), generated deterministically (openpyxl, no model): title block, frozen header row, filters, column widths, wrapped text, offering-type colours, source page and lines; keep the CSV | S3 | Sun 11 Oct | todo | from the 8 Oct call (plan §8) |

## J-03 walkthrough: review checklist (9 Oct 2026)

Voice, structure and the "Planned" labels are good. Fix the items below before the client sees the document.

**Now (text only, about an hour):**
- [x] 1. §2: "13 requirements have been extracted" is not accurate. The 13 are hand-picked seed items; the reader agent extracts 840 from this RFP. Write "13 requirements selected for the demonstration" (or describe the real extraction after P-08).
- [x] 3. Current names everywhere (§3 table, §4, §6, §8, §9, §11): steps **RFP, Requirements, Traceability, Bid decision, Final response**; top bar **Opportunities, My work, Product catalog**. §4 "Open enters the opportunity at the RFP step". Done 9 Oct. §4 says "Open enters the opportunity at its Traceability step": the Open button links to the Traceability page (checked in the page), not to the RFP step.
- [x] 4. §8 offering types, the agreed definitions (as in the on-screen legend):
  - CTO: configure-to-order, a catalog product with options (CPQ).
  - Semi-custom: a configured product plus workshop work for this customer.
  - ETO: engineered-to-order, designed for this requirement.
- [x] 10. In prose, use unit names instead of codes: "Crown Technical Systems and EP²", not "CROWN and EP2".
- [x] 11. Add a date line at the top: "Walkthrough as of <date>", naming the build it describes.

**After P-08 (the demo runs on the real extraction):**
- [ ] 2. Retake all 12 screenshots. They show the old navigation, the old legend and the Next.js development badge (the "N" bottom left). Take them from a production build (`cd web && npm run build && npm start`). 9 Oct: 10 screenshots refreshed from the current UI (Requirements, Bid decision and Final response each joined from two captures). Still open: retake from a production build (no "N" badge).
- [ ] 5. §7 Requirements: 9 Oct: filters and search are described; review actions, freeze rule and the seven categories are still open.
  - the review actions: edit, split, merge, add a missed requirement, bulk approve/reject;
  - filters and search;
  - freezing needs every item decided;
  - list all seven categories.
- [ ] 6. §8 Traceability: accept, reject or change a match on screen 3 (A-05); a requirement can go to several units. 9 Oct: accept / reject / change is described; several units per requirement is still open.
- [ ] 7. §9 Bid decision: the engineering checks in the evidence (A-06). Order: go/no-go only after freeze; dispatch only after "go". 9 Oct: freeze-before-decision and the dispatch note are described; the engineering checks are still open.
- [ ] 8. Bill of materials: read from the separate BOM system, illustrative for now (not "optional"). 9 Oct: "optional" removed; the BOM-system wording is still open.
- [ ] 9. One line on how requirements are produced: the model reads each page, every quote is checked against the page, answers are frozen (the agentic process the client asked for).

The Monday click-path checklist is J-06, a separate task.

## Blocked on / needs from others

| Date | Need | From | Status |
|---|---|---|---|
| 9 Oct 2026 | `Documents/technical-architecture.md` section 7.6 lists the compliance-matrix columns: add "assignment status" and "responded by" (appended after "state") and the UTF-8 byte order mark | Piyush | to ask (not blocking) |

## Log

| Date | Done | Next |
|---|---|---|
| 8 Oct 2026 | J-01, J-02 done; client wording and loading-error follow-ups; J-03 walkthrough with 12 screenshots (tracker filled in on 9 Oct from the commits) | J-03 rename to current screen names |
| 9 Oct 2026 | Review fixes in trace / consolidation, applied by Piyush: compliance CSV safe in Excel (formula cells quoted, safe file name, offering type of the assigned unit); 404 for unknown opportunities; trace payload 2.4 → 1.3 MB (no match evidence); header status refreshes after actions; keyboard: BOM summary and page highlights reachable, rows no longer swallow inner keys; "met · " with no product fixed; consolidation shows load errors. Regression test added | J-03 rename, J-04 portfolio |
| 9 Oct 2026 | J-04 done: Portfolio shows a progress bar per unit (green validated, blue awaiting validation, grey not answered) with the count and a link to the unit's inbox; status chips coloured by stage; "not dispatched" when a unit list is empty | J-05 consolidation (blocking items list, matrix columns with the bid manager), then J-03 rename |
| 9 Oct 2026 | J-03 refresh: 10 screenshots from the current UI (Requirements, Bid decision and Final response each joined from two captures), walkthrough text on current names and definitions, "as of" date line; checklist items 1, 3, 4, 10, 11 done; the Open button opens Traceability (not the RFP step) | J-03 items 2, 5-9 after P-08; J-05 |
| 9 Oct 2026 | J-05 parts A+B: Final response lists what blocks completion by reason (waiting for validation / for the unit / returned / not assigned) with links to Traceability, All/Open filter, marked rows, coloured state and status badges; checked on the 13-item data (4/13, 3 + 6) and on the real extraction (1/353) | J-05 part C (matrix columns with the bid manager); J-03 items 2, 5-9 |
| 9 Oct 2026 | J-05 done: compliance matrix CSV with Assignment status and Responded by (appended) and a UTF-8 BOM so Excel reads non-ASCII text; checked on the real 353-requirement export (14 columns, 353 rows, first 12 columns identical to before); self-check and a smoke test; pytest 15 passed | J-03 items 2, 5-9; ask Piyush to update the design document column list |
