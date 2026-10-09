# Tracker: Janvia

Only Janvia edits this file. Update it when a task starts, finishes or gets blocked, and commit it with the work
(`[J-xx] tracker: ...`). Status: `todo` · `doing` · `blocked` · `review` · `done`.
Task details and dependencies: [team/PLAN.md](../PLAN.md).

| ID | Task | Stage | Due | Status | Notes / commit |
|---|---|---|---|---|---|
| J-01 | Clone, `.venv`, seed, run; open the three screens; read `.claude/CLAUDE.md` | S0 | Thu 8 Oct | done | app run locally: walkthrough screenshots taken from it (60faf7a) |
| J-02 | Polish the three screens for the walkthrough: layout, legend (CTO / Semi-custom / ETO), selected-row and highlight styles, empty states | S1 | Fri 9 Oct AM | done | fed8c0a legend, selected row, status badges, empty states, a11y; follow-ups 0e7f3d8 client wording, bd946ed error message instead of endless loading |
| J-03 | Walkthrough document `Documents/walkthrough.md` with screenshots (`Documents/images/`), neutral voice | S1 | Fri 9 Oct | review | 60faf7a `Documents/walkthrough.md` + 12 screenshots, no names, unbuilt parts marked planned. To do: rename to the current screen names (Three screens → Traceability, Consolidation → Final response, Decisions → Bid decision) and retake affected screenshots |
| J-04 | Portfolio: per-unit progress bars, status chips, link to each unit's inbox | S2 | Sat 10 Oct | todo | |
| J-05 | Consolidation page: blocking items link to the three screens; compliance-matrix columns reviewed with the bid-manager view | S3 | Sun 11 Oct | todo | |
| J-06 | Monday demo click-path checklist (in the walkthrough) and a dry run with Piyush | S3 | Mon 12 Oct AM | todo | |
| J-07 | Response-outline view (uses P-10) | S4 | after 12 Oct | todo | |

## Blocked on / needs from others

| Date | Need | From | Status |
|---|---|---|---|

## Log

| Date | Done | Next |
|---|---|---|
| 8 Oct 2026 | J-01, J-02 done; client wording and loading-error follow-ups; J-03 walkthrough with 12 screenshots (tracker filled in on 9 Oct from the commits) | J-03 rename to current screen names |
| 9 Oct 2026 | Review fixes in trace / consolidation, applied by Piyush: compliance CSV safe in Excel (formula cells quoted, safe file name, offering type of the assigned unit); 404 for unknown opportunities; trace payload 2.4 → 1.3 MB (no match evidence); header status refreshes after actions; keyboard: BOM summary and page highlights reachable, rows no longer swallow inner keys; "met · " with no product fixed; consolidation shows load errors. Regression test added | J-03 rename, J-04 portfolio |
