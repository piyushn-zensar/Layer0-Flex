# Layer 0 guided walkthrough: guide

An in-app, step-by-step tour of every screen of Layer 0. It dims the page, highlights one element at a time, explains what it is, why it exists and what to do, and for the main actions lets the person perform them on a real opportunity. The app works unchanged with the walkthrough closed.

## 1. Purpose and how to start it

- **Auto-offer.** After each server start the first page load opens a welcome dialog (four-line summary, a 25 to 30 minute estimate, the chapter list, **Start** or **Not now**). It is offered once per server start: a browser refresh or hot reload does not offer it again.
- **Walkthrough button** in the top bar (always available). Depending on state it shows Start, Resume, Restart, and a chapter list for jumping straight to a chapter. Chapters already finished carry a tick.
- **Controls in the bubble.** Next / Previous (also the right and left arrow keys), Skip step, Exit (also Esc), a Chapters menu, step and chapter counters. Action steps keep Next disabled ("Waiting") until the condition is met; **Continue anyway** is always offered. **Use example** applies a ready-made input with one click.
- On screens under 700 px wide the bubble docks at the bottom.
- All text is neutral and refers to roles (Bid Manager, unit product manager, unit design engineer), not to people.

## 2. Chapters

219 steps in 12 chapters (the catalogue is `CHAPTERS` / `STEPS` in `web/tour/index.ts`). The step id prefix is the chapter id, except where noted.

| # | Chapter id | Title | Steps | Starts on |
|---|---|---|---|---|
| 1 | welcome | Welcome and overview | 5 | centred, any page |
| 2 | portfolio | The Opportunities screen | 9 | /portfolio |
| 3 | navigation | Navigation, roles and the workflow stepper | 12 | /portfolio, then the opportunity |
| 4 | intake | New opportunity and the RFP | 16 | /opportunities/new |
| 5 | requirements | Requirements review and freezing | 34 | /opportunities/{opp}/requirements |
| 6 | trace | Traceability and product matching | 29 | /opportunities/{opp}/trace |
| 7 | decisions | The bid decision and dispatch | 32 | /opportunities/{opp}/decisions |
| 8 | inbox | Unit inboxes, answers and validation | 16 | /inbox/BID |
| 9 | consolidation | Final response, exports and the outline (11 steps `consolidation-*` plus 12 steps `outline-*`) | 23 | /opportunities/{opp}/consolidation |
| 10 | knowledge | Knowledge base and catalog (10 steps `knowledge-*` plus 5 steps `catalog-*`) | 15 | /knowledge |
| 11 | changes | Addenda and change handling | 22 | /opportunities/OPP-0001/changes |
| 12 | recap | Recap and completion | 6 | /opportunities/{opp} |

Total: 5+9+12+16+34+29+32+16+23+15+22+6 = 219.

## 3. Screens covered

Every page under `web/app` has steps.

| Screen (route) | Chapter(s) |
|---|---|
| Any page (centred bubble) | welcome, recap |
| `/` (redirect to /portfolio) | not a screen; no steps |
| `/portfolio` Opportunities | portfolio |
| Top bar (every page) | navigation |
| `/opportunities/new` | intake (intake-intro .. intake-create) |
| `/opportunities/{id}` RFP documents, header, stepper | navigation, intake (intake-rfp-intro .. intake-result), recap |
| `/opportunities/{id}/requirements` incl. History and the line picker | requirements |
| `/opportunities/{id}/trace` | trace |
| `/opportunities/{id}/decisions` | decisions |
| `/inbox` (redirects to /inbox/BID) and `/inbox/{unit}` | inbox |
| `/opportunities/{id}/consolidation` | consolidation-* |
| `/opportunities/{id}/consolidation/outline` | outline-* |
| `/knowledge` | knowledge-* |
| `/catalog` | catalog-* |
| `/opportunities/{id}/changes` | changes (always OPP-0001) |

## 4. Interactive actions and their completion conditions

Action steps (kind `action`) and wait steps (kind `wait`) are finished by `done(ctx)`, polled every 500 ms and re-checked on DOM changes. The person may press Continue anyway. A step with `skipIf` is skipped when it does not apply (for example the opportunity is already frozen); this works in both directions (Next and Previous).

| Step | What the person does | Done when | Skipped when |
|---|---|---|---|
| intake-create | Press Create | pathname is /opportunities/OPP-xxxx; the id is stored as the walkthrough opportunity | demo opportunity chosen |
| intake-use-example | Press Use example (attach the Syracuse RFP) or upload a file | a main document exists | demo chosen, or a main document exists |
| intake-wait-read | Wait about a minute (Refresh status pressed once automatically) | main document status is ingested | demo chosen |
| intake-extract | Press Run the reader agent | opportunity status is review or later | demo chosen, or already read |
| requirements-approve | Approve the first line item | Approved count grows | frozen or later |
| requirements-reject | Reject it | Rejected count grows | frozen or later |
| requirements-restore | Approve it again from the Rejected view | Rejected count falls | frozen or later |
| requirements-edit | Edit the short text (example given) | first row text differs from the remembered one | frozen or later |
| requirements-history-open | Open History | History panel present | not skipped when frozen |
| requirements-lp-add | Add p. 55, lines 52-53 from the line picker (example fills the form) | the new REQ id is stored | frozen or later |
| requirements-reject-added | Reject the added item again | its History has a reject event | frozen or later |
| requirements-approve-all | Tick Select all, press Approve | To review reads 0 | frozen or later |
| requirements-freeze | Press Freeze baseline and confirm | baseline line present | frozen or later |
| trace-match-run | Press Match products | match results present in pane 3 | already decided/dispatched |
| trace-match-accept | Accept the selected match | match badge reads accepted | none |
| trace-match-change / trace-match-cancel | Open then cancel the Change form | form present / form gone | none |
| trace-sync | Click a highlight or a row | URL hash changed | none |
| decisions-part-record | Record participation (example rationale) | participation record present | already decided |
| decisions-go | Record go (example rationale) | go record present | decided or not frozen |
| decisions-dispatch-run | Press Dispatch | status is dispatched | no-go, dispatched or later |
| inbox-switch-crown | Switch Acting as to the Crown product manager (example does it) | actor is Crown Product Manager | none |
| inbox-submit | Submit the example answer | the remembered assignment is no longer assigned/returned | none |
| inbox-switch-bm | Switch back to Bid Manager | actor is Bid Manager | none |
| inbox-validate | Validate the answer | the remembered assignment is validated | none |
| consolidation-filter | Click Open | Open chip pressed | filter absent |
| consolidation-to-outline | Open the Response outline | pathname is the outline | none |
| knowledge-send | Queue a validated answer (example posts to /api/knowledge) | a queue item exists | queue already has items |
| knowledge-curator | Act as Bid Manager | actor is Bid Manager | already Bid Manager |
| knowledge-approve | Approve with a tidied response (example) | an approved item exists | none |
| knowledge-reject | Reject with a note (example queues and fills) | a rejected item exists | none |
| catalog-search | Search the knowledge base (example query) | results table present | none |
| changes-read-example | Read Addendum No. 1 (example) | a change set exists | a set already exists |
| changes-override | Override one wording and confirm (example) | a confirmed row is shown | set not in review, or no decision form |
| changes-confirm-all | Confirm all proposals | the Confirm all button is disabled or gone | set not in review, or all confirmed |
| changes-apply | Apply to requirements as Bid Manager (example sets the actor) | the change-set result is shown | set not in review |

Exact conditions are in the chapter files; the table summarises them. Reject on a match, split, merge, ungroup and no-go are explained but never performed by an action step.

## 5. Sample inputs and sample routes

"Use example" fills forms or calls a whitelisted backend route; no file path ever comes from the browser.

| Example | What it does | Expected result (demo numbers) |
|---|---|---|
| `GET /api/samples` | Lists syracuse_rfp (101 pages), hyperscale_rfp (1 page) and syracuse_addendum_1 (1 page) without paths | three entries with name, filename, kind, pages, description |
| `POST /api/opportunities/{id}/documents/from-sample {"name":"syracuse_rfp"}` | Attaches the Syracuse RFP as the main document through the same helper as an upload; reading runs in the background | 101 pages, ingested in a few seconds from the cached layout; 409 on unknown sample, wrong kind or a second main RFP |
| `POST .../requirements/extract` (button Run the reader agent) | Reader and grouping agents in mock mode replay frozen answers | 814 line items, 21 duplicates, 162 groups, 348 requirements, status review |
| `POST /api/opportunities/OPP-0001/changes/from-sample {"name":"syracuse_addendum_1"}` | Reads the addendum against the frozen baseline like a file upload | change set in review: modified, added and removed items; after apply: Baseline 2, added REQ-0001-0977 and -0978, modified REQ-0001-0039 and -0332, removed REQ-0001-0130 |
| Intake example | Fills title, customer, customer type | "Walkthrough: Syracuse switchgear" |
| Requirements examples | Edit text; add page 55 lines 52-53; paste form (page 55 line 37) | green "REQ-... added (p. 55, lines 52-53)"; the pasted example must be rejected again if added |
| Decisions examples | Participation and go/no-go rationale and judgements | fields filled; Record enabled |
| Inbox examples | Switch actor; fill compliance, product, response | row submitted, then validated by the Bid Manager |
| Knowledge example | Queues a validated Crown answer via `POST /api/knowledge`; tidies the response; pre-fills a rejection note | item appears under Waiting, then Approved or Rejected |
| Catalog example | Query in the search box | ranked results with score, kind, unit |

Constraints in mock mode: answers are frozen replays keyed to the exact requirement set. The Syracuse RFP read and extract work offline on any new opportunity. The matcher replays frozen answers only for the Syracuse requirement set. The addendum has frozen change answers for OPP-0001's requirement set only, so the changes chapter always runs on OPP-0001. The hyperscale sample ingests (1 page) but extraction returns 0 proposed in mock mode.

Opportunity choice: Create your own in chapter 4, or choose "Use the demo opportunity instead" (the context stores demo=true and the opportunity OPP-0001; creation, upload and extraction steps are then skipped). Chapters 5 to 10 run on the walkthrough opportunity (`ctx.oppId`), chapter 11 on OPP-0001. The seeded OPP-0001 is already frozen, dispatched and has one validated answer, so its action steps are skipped and explain steps use fallback text where an element is not present.

## 6. Session and persistence

- `GET /tour-session` (`web/app/tour-session/route.ts`, `force-dynamic`) returns `{id}`: a random UUID created when the server module loads, so it changes on every server start and is stable across refreshes and hot reloads.
- Progress is stored in localStorage key `layer0.tour`: `{session, status, chapter, step, ctx: {oppId, data}}`. Status is one of `offered`, `running`, `skipped`, `done` (plus `loading` before the first read).
- On each page load the launcher fetches the session id and compares it with the stored one. Different id: stored progress is reset and the welcome dialog opens. Same id: `skipped` or `done` stay closed; `running` resumes at the saved step.
- A browser refresh keeps the position; a hot reload keeps React state (and the same stored data). Exit (Esc) keeps the position; the button then offers Resume. Storage failures (private window) are caught, and the app still works.
- `ctx.setActor(name)` writes the actor cookie, saves progress and reloads the page, then the walkthrough resumes.

## 7. Engine behaviour

- **State machine** (`TourProvider`): current step, chapter and counters over `STEPS`; navigates to the step route (client-side), then polls for the target up to 10 s. Not found: the bubble shows the step's `fallback` text without a spotlight. `onEnter` runs after the target appears.
- **Overlay** (`TourOverlay`): four-rectangle dimmed backdrop with a hole around the target (clickable on action steps, blocked otherwise), repositioned by requestAnimationFrame and ResizeObserver; automatic placement; light markup (`**bold**`, `` `code` ``); aria-live announcements and focus management.
- **Launcher** (`TourLauncher`): welcome dialog and top-bar button, raised above the backdrop while running.
- **ctx** helpers: `api`, `post`, `el`, `set`, `get`, `go`, `setActor`, and a persisting `oppId` setter.

## 8. Adding or changing a step

1. **Step fields** (`web/tour/types.ts`): `id` (unique, `<chapter>-<name>`), `title`, `body` (string or paragraphs), optional `route` (`{opp}` allowed), `target` (a `data-tour` id), `placement` (auto, top, bottom, left, right), `instruction`, `example {label, apply}`, `kind` (explain, action, wait), `done`, `skipIf`, `onEnter`, `fallback`, `allowInteraction`.
2. **Helpers** (`web/tour/helpers.ts`): `present(id)`, `onRoute(route, prefix?)`, `textIn(id, words)`, `opportunity(ctx)`, `statusIn(...statuses)`, `openDetails(id)`.
3. **Target**: add `data-tour="your-id"` to the element on the page (attributes only). Keep ids unique on the page; for repeated rows target the first or newest one. The target must be a static string (no `{opp}` substitution in targets).
4. **Chapter file**: edit the step list in `web/tour/chapters/<chapter>.ts` (some files define small local `explain()` / `action()` wrappers).
5. **Register**: a new chapter file is imported and added to the array in `web/tour/index.ts`, with a unique `order`.
6. **Check**: `cd web && npx tsc --noEmit && npm run build`, then run the walkthrough on the real seed.

## 9. Known limitations and not covered

- Chapter 11 always uses OPP-0001 because the frozen change answers match only its requirement set.
- Matcher and reader answers in mock mode are frozen replays; a different RFP needs live Azure answers.
- The Freeze, merge and no-go confirm dialogs are explained in text but not spotlighted (the shared ConfirmDialog has no `data-tour` hook).
- Merge, Split, Ungroup, restoring a duplicate, Reject on a match, saving a manual match and No-go are explained but not performed, because they alter the approved set or the demo state.
- Toast messages are mentioned but not targeted.
- No send-to-knowledge button exists on the Opportunities, Intake, Requirements or Inbox pages, so the knowledge chapter queues an item through `POST /api/knowledge`.
- Per-opportunity inbox ids (`inbox-handoff-<OPP id>`, `inbox-open-rfp-<OPP id>`) exist but steps spotlight the container, because targets are static. Inbox row targets land on the first open row of the whole package, which can be an OPP-0001 row.
- The unanchored badge in the inbox has no target; the source-link fallback covers it.
- The unreviewed-page warning (Traceability, line picker) cannot be shown on the Syracuse RFP, which has a text layer on every page.
- Portfolio empty state ("No opportunities yet") is not targeted. Opportunity status `reading` is in the vocabulary but is never set by the current code, so the status step lists only statuses that occur.
- The document-switch chips in Traceability exist only after an addendum is applied; the step targets the "Showing" line.
- Mobile: the bubble docks under 700 px and was verified at 390 px for the engine chapters only; the other chapters were checked on desktop.
- `ctx.setActor` was exercised through the inbox and knowledge chapters' flows in Playwright runs, but not every action-step path was driven end to end in a browser.
- Coverage statement: every page under `web/app` has walkthrough steps (section 3), and every UI row below is a step in the chapter files. This is not a claim that every individual control on every page is explained; filters, buttons and fields not listed in the map have no step.

## 10. Final coverage map

| Screen / Section | UI Component | Purpose | User Action | Expected Behavior | Walkthrough Step |
|---|---|---|---|---|---|
| Any (centred) | Application purpose | Layer 0 as the bridge between CRM and CPQ | Read | Centred bubble | welcome-purpose |
| Any (centred) | Six steps and statuses | Workflow and forward-only status chain | Read | Centred bubble | welcome-steps |
| Any (centred) | Agents and frozen answers | Agents propose, people decide; audit | Read | Centred bubble | welcome-agents |
| Any (centred) | What the person will do | Plan, demo alternative, time | Read | Centred bubble | welcome-you |
| Any (centred) | Walkthrough controls | Next, Previous, Esc, Chapters, Use example | Read, Next | Moves to the next chapter | welcome-controls |
| /portfolio | Table | What an opportunity is; read-only overview | Read | Spotlight on table | portfolio-intro |
| /portfolio | ID, Title, Customer columns | Id allocation and links | Read | Spotlight on ID column | portfolio-columns |
| /portfolio | Status chip | Forward-only lifecycle, tones | Read | Spotlight on the dispatched chip | portfolio-status |
| /portfolio | Requirements column | Count of current requirements (348) | Read | Spotlight on the count | portfolio-requirements |
| /portfolio | Unit progress bars and links | validated/total, BID desk, inbox links | Read | Spotlight on bars | portfolio-units |
| /portfolio | Row OPP-0001 | The Syracuse demo | Read | Spotlight on row | portfolio-syracuse |
| /portfolio | Row OPP-0002 | Fictional hyperscale sample | Read | Spotlight on row | portfolio-hyperscale |
| /portfolio | Open button | Where Open and the ID lead | Read | Spotlight on Open | portfolio-open |
| /portfolio | New opportunity button | Hand-over to intake | Read | Spotlight on button | portfolio-new |
| Top bar | Brand link | Bar on every page; no sign-in | Read | Spotlight on mark | navigation-brand |
| Top bar | Main navigation | Four destinations | Read | Spotlight on nav | navigation-nav |
| Top bar | New opportunity button | Form, id allocation, status new | Read | Spotlight on button | navigation-new |
| Top bar | Acting as picker | Actor cookie, X-Actor, role rules | Read | Spotlight on picker | navigation-actor |
| Top bar | Walkthrough button | Resume, Restart, chapters | Read | Spotlight on button | navigation-help |
| /opportunities/{opp} | Header | Breadcrumb, title, status, stepper | Read (engine navigates) | Spotlight on header | navigation-opp-head |
| /opportunities/{opp} | Status badge | Nine statuses, forward-only | Read | Spotlight, fallback if not loaded | navigation-status |
| /opportunities/{opp} | Stepper | Current vs done, thresholds | Read | Spotlight on stepper | navigation-stepper |
| /opportunities/{opp} | Stepper: RFP, Requirements | Steps 1 and 2 | Read | Spotlight on entry | navigation-step-rfp |
| /opportunities/{opp} | Stepper: Traceability, Bid decision | Steps 3 and 4 | Read | Spotlight on entry | navigation-step-trace |
| /opportunities/{opp} | Stepper: Final response | Consolidation, tick at submitted | Read | Spotlight on entry | navigation-step-final |
| /opportunities/{opp} | Changes link | Addenda, change sets | Read | Spotlight, placement left | navigation-changes |
| /opportunities/new | Form | POST /api/opportunities, status new | Read | Spotlight on form | intake-intro |
| /opportunities/new | Create vs demo choice | Alternative path | Read, Use example | demo=true, later steps skipped | intake-choose |
| /opportunities/new | Title field | Required; example fills all fields | Read, Use example | Fields filled | intake-title |
| /opportunities/new | Customer field | Optional, display only | Read | Spotlight on field | intake-customer |
| /opportunities/new | Customer type select | Six values, no agent behaviour | Read | Spotlight on select | intake-customer-type |
| /opportunities/new | Create button | Create and capture the id | Press Create | Pathname /opportunities/OPP-xxxx; id persisted | intake-create |
| /opportunities/{opp} | RFP documents table (intro) | Step 1 of the stepper | Read | Spotlight on table | intake-rfp-intro |
| /opportunities/{opp} | Documents table | Role, pages, statuses, SHA-256 | Read | Spotlight on table | intake-docs-table |
| /opportunities/{opp} | Upload form | Manual path, background read | Read | Spotlight on form (details opened) | intake-upload-form |
| /opportunities/{opp} | Add another document | Addenda, Changes page | Read | Spotlight on demo, fallback on new | intake-add-another |
| /opportunities/{opp} | Use example (sample route) | Attach the Syracuse RFP | Press Use example | Main document exists | intake-use-example |
| /opportunities/{opp} | Status cell while reading | Layout, OCR, tables, frozen parse | Wait | Done at status ingested | intake-wait-read |
| /opportunities/{opp} | Main document row | 101 pages, ingested, fingerprint | Read | Spotlight on row | intake-doc-ingested |
| /opportunities/{opp} | Search this RFP | Short-term index, page and lines | Read, Use example | Results on p. 63 and 64 | intake-search |
| /opportunities/{opp} | Run the reader agent | Reader and grouping, status review | Press button | Status review or later | intake-extract |
| RFP documents to Requirements | Result summary | 814 items, 21 duplicates, 162 groups, 348 requirements | Read | Centred bubble | intake-result |
| Requirements | Screen introduction | Numbers' origin; what to finish | Read | Centred bubble | requirements-intro |
| Requirements | Header, Freeze button | Active count, still to decide | Read | Spotlight on help line | requirements-head |
| Requirements | Filter chips and search | Chip meanings, search scope | Read | Spotlight on filters | requirements-filters |
| Requirements | Table | Document order, columns | Read | Spotlight on table | requirements-table |
| Requirements | ID cell and category | Id format, seven categories | Read | Spotlight on first row ID | requirements-col-id |
| Requirements | Source column | Anchoring rule, link to Traceability | Read | Spotlight on source | requirements-col-source |
| Requirements | Short text vs quote | Which text is editable | Read | Spotlight on text | requirements-col-text |
| Requirements | Groups and sub-requirements | Grouping agent, ungroup | Read | Group expanded | requirements-groups |
| Requirements | Unanchored badge and filter | Causes and handling | Read | Unanchored chip selected | requirements-unanchored |
| Requirements | Duplicates filter and note | Detection, restore | Read | Duplicates chip selected | requirements-duplicates |
| Requirements | Status badges | Seven statuses, audited | Read | Spotlight on badge | requirements-status |
| Requirements | Per-row actions | Approve, Reject, Edit, Split, Ungroup | Read | Spotlight on actions | requirements-actions |
| Requirements | Approve button | Approve the first item | Press Approve | Approved count grows | requirements-approve |
| Requirements | Reject button | Reject for the exercise | Press Reject | Rejected count grows | requirements-reject |
| Requirements | Approve on a rejected row | Restore a decision | Press Approve in Rejected | Rejected count falls | requirements-restore |
| Requirements | Edit form | Edit short text only | Edit, Use example | First row text changes | requirements-edit |
| Requirements | Split button and form | One quote per line, re-anchoring | Read | Spotlight on Split | requirements-split |
| Requirements | Checkboxes, Select all | Selection over the current view | Read | Spotlight on header checkbox | requirements-select |
| Requirements | Bulk bar | Approve, reject, merge | Read | Bar shown | requirements-bulkbar |
| Requirements | History link | Open the audit panel | Press History | History present | requirements-history-open |
| Requirements | History: Versions | Who changed the wording | Read | Spotlight on versions | requirements-history-versions |
| Requirements | History: Timeline | Every audit event | Read | Spotlight on timeline | requirements-history-timeline |
| Requirements | Add a requirement section | Two ways to add | Read | Details opened | requirements-add-intro |
| Requirements, line picker | Pager | Choosing the page | Read | Spotlight on pager | requirements-lp-pager |
| Requirements, line picker | Page image and lines | Click and shift-click, legend | Read | Spotlight on page | requirements-lp-lines |
| Requirements, line picker | From and To line | Keyboard selection, 40-line limit | Read | Spotlight on range | requirements-lp-range |
| Requirements, line picker | Quote preview | Exact quote stored | Read | Spotlight on preview | requirements-lp-preview |
| Requirements, line picker | Add requirement (p. 55, lines 52-53) | Add a missed item | Use example, Add | Green "REQ-... added" message | requirements-lp-add |
| Requirements, line picker | Success message | What the new item looks like | Read | Spotlight on message | requirements-lp-result |
| Requirements | Reject on the added row | Keep the approved set as proposed | Press Reject | Reject event in History | requirements-reject-added |
| Requirements | Paste form | Other way to add; unanchored fallback | Read, Use example | Form filled | requirements-paste |
| Requirements | Select all and bulk Approve | Approve the remaining items | Tick, Approve | To review reads 0 | requirements-approve-all |
| Requirements | Freeze baseline and dialog | Preconditions, what the freeze writes | Press Freeze, confirm | Baseline line present | requirements-freeze |
| Requirements | Frozen state | Baseline line, controls removed | Read | Spotlight on baseline | requirements-frozen |
| Traceability | Three linked panes | What the screen is | Read | Panes spotlighted | trace-intro |
| Traceability | Pane 1 page image | Anchoring, highlights | Read | Spotlight on pane 1 | trace-pane-1 |
| Traceability | Pager | Valid pages, clamping | Read | Spotlight on pager | trace-pager |
| Traceability | Unreviewed-page warning | No text layer, needs OCR | Read | Fallback on Syracuse | trace-unreviewed |
| Traceability | Document line and switch | RFP vs change documents | Read | Spotlight on Showing line | trace-docs |
| Traceability | Pane 2 table | Columns, row selection | Read | Spotlight on pane 2 | trace-pane-2 |
| Traceability | ID and category | Stable ids, matching effect | Read | Spotlight on ID cell | trace-sel-id |
| Traceability | Source column | Page and lines | Read | Spotlight on source | trace-sel-source |
| Traceability | Unanchored badge | Meaning, 32 in the demo | Read | Spotlight on badge | trace-unanchored |
| Traceability | Short text and quote | Reader text vs quote | Read | Spotlight on text | trace-sel-text |
| Traceability | Groups | 162 groups, union highlight | Read | Spotlight on group | trace-group |
| Traceability | Send to knowledge base | Curator queue | Read | Spotlight on link | trace-send-knowledge |
| Traceability | Pane 3 table | Unit and product, response | Read | Spotlight on pane 3 | trace-pane-3 |
| Traceability | Offering type legend | CTO, Semi-custom, ETO | Read | Spotlight on legend | trace-legend |
| Traceability | Toolbar unit responses | validated/total badges | Read | Spotlight on toolbar | trace-unit-responses |
| Traceability | Match products (explain) | One call per page, bid-desk rule | Read | Spotlight on button | trace-match-explain |
| Traceability | Match products (run) | Run the matcher | Press button | Toast "348 requirement(s) matched" | trace-match-run |
| Traceability | Match result | Statuses, methods, counts | Read | Spotlight on pane 3 | trace-match-result |
| Traceability | Unit, product, offering badge | Unit from product | Read | Spotlight on unit | trace-sel-unit |
| Traceability | Rationale and method | Agent citation | Read | Spotlight on rationale | trace-sel-rationale |
| Traceability | Bill of materials | Catalog BOM | Read | Details opened | trace-sel-bom |
| Traceability | Accept, Reject, Change buttons | Match semantics | Read | Spotlight on buttons | trace-match-actions |
| Traceability | Accept | Accept the proposal | Press Accept | Badge reads accepted | trace-match-accept |
| Traceability | Change (open) | Open the form | Press Change | Form shown | trace-match-change |
| Traceability | Change form | Units, products, offering types | Read | Spotlight on form | trace-match-form |
| Traceability | Cancel | Close without saving | Press Cancel | Form closed | trace-match-cancel |
| Traceability | Selection sync | Panes follow, URL hash | Click highlight or row | Hash changes | trace-sync |
| Traceability | Response column | Assignment statuses | Read | Spotlight on response | trace-sel-response |
| Traceability | Leave checklist | What to finish before the decision | Read | Centred bubble | trace-done |
| Bid decision | Introduction | Evidence first, then a person decides | Read | Centred bubble | decisions-intro |
| Bid decision | Evidence counts | Counts by category | Read | Spotlight on card head | decisions-evidence |
| Bid decision | Offering mix | ETO, CTO, Semi-custom, NONE | Read | Spotlight on line | decisions-offering-mix |
| Bid decision | Suggested units | CROWN (96), EP2 (7) | Read | Spotlight on line | decisions-suggested-units |
| Bid decision | Unanchored | 32 open questions | Read | Details opened | decisions-unanchored |
| Bid decision | Not yet matched | When it appears | Read | Fallback when none | decisions-unmatched |
| Bid decision | Matches not reviewed | 103 in the demo | Read | Line or fallback | decisions-not-reviewed |
| Bid decision | Not-frozen alert | Freeze before go/no-go | Read | Only before freeze | decisions-not-frozen |
| Bid decision | Engineering checks card | Ported, keyword-based, illustrative | Read | Spotlight on card | decisions-eng |
| Bid decision | Scope layers | Six layers, thresholds | Read | Spotlight on list | decisions-eng-scope |
| Bid decision | Rules R-001 to R-004 | Meaning and demo statuses | Read | Spotlight on table | decisions-eng-rules |
| Bid decision | Tier flags | Default tiers per unit | Read | Details opened | decisions-eng-tiers |
| Bid decision | Low-voltage solver | Working steps and refusal | Read | Spotlight on block | decisions-eng-solver |
| Bid decision | Bid and portfolio checks | Ported from v1.1 | Read | Spotlight on card | decisions-portfolio |
| Bid decision | Deviations | Data sheet vs standard ratings | Read | Spotlight on table | decisions-deviations |
| Bid decision | Workload | Open work vs capacity | Read | Spotlight on table | decisions-workload |
| Bid decision | Participation card | What is recorded | Read | Spotlight on card | decisions-participation |
| Bid decision | Unit checkboxes | Active units, at least one | Read | Spotlight on fieldset | decisions-units |
| Bid decision | Participation rationale | Example input | Use example | Rationale filled | decisions-part-rationale |
| Bid decision | Record participation | Record it | Press button | Recorded-by line | decisions-part-record |
| Bid decision | Go / no-go card | Contents and effect | Read | Spotlight on card | decisions-gonogo |
| Bid decision | Advice line | A person decides; 6 of 9 | Read | Spotlight on alert | decisions-advice |
| Bid decision | By-category table | Satisfaction levels, coverage | Read | Spotlight on table | decisions-by-category |
| Bid decision | Per requirement list | Basis and links | Read | Details opened | decisions-per-req |
| Bid decision | Criteria table | 12 criteria | Read | Spotlight on table | decisions-criteria |
| Bid decision | Go/no-go rationale | Rationale, judgement, note | Use example | Fields filled | decisions-gng-rationale |
| Bid decision | No-go and confirm dialog | Dialog text, disabled states | Read | Spotlight on No-go | decisions-no-go |
| Bid decision | Go | Record go | Press Go | Status go; dispatch card appears | decisions-go |
| Bid decision | Recorded decision line | Live summary vs stored evidence | Read | Spotlight on line | decisions-gng-recorded |
| Bid decision | Dispatch card | Assignments per unit | Read | Card or fallback | decisions-dispatch |
| Bid decision | Dispatch button | Dispatch | Press button | Status dispatched | decisions-dispatch-run |
| Bid decision | Dispatch result | Toast, status, next chapter | Read | Spotlight on card | decisions-dispatch-result |
| /inbox to /inbox/BID | Redirect and bid desk | People lookup, BID pseudo-unit | Read | Spotlight on table | inbox-mywork |
| /inbox/CROWN | Bid manager view | Permissions, read-only banner | Read | Spotlight on table | inbox-bm-view |
| /inbox/CROWN | Open the RFP, hand-off links | Trace links, hand-off | Read | Spotlight on links | inbox-links |
| /inbox/CROWN | Table columns | Opportunity, requirement, response, status | Read | Spotlight on table | inbox-columns |
| /inbox/CROWN | Acting as | Cookie and X-Actor | Switch, Use example | Actor Crown Product Manager | inbox-switch-crown |
| /inbox/CROWN | Open rows line | Open count | Read | Spotlight on count | inbox-open-count |
| /inbox/CROWN | Row form | Compliance, product, response | Read, Use example | Fields filled | inbox-row-form |
| /inbox/CROWN | Submit | POST /respond | Press Submit | Assignment submitted | inbox-submit |
| /inbox/CROWN | Submitted row | Effects downstream | Read | Spotlight on row | inbox-submitted |
| /inbox/CROWN | Submit all | Bulk semantics | Read | Spotlight on button | inbox-submit-all |
| /inbox/CROWN | Source link, unanchored | Highlighted source | Read | Link or fallback | inbox-source-link |
| /inbox/CROWN | Acting as (back) | Validation is the Bid Manager's | Switch, Use example | Actor Bid Manager | inbox-switch-bm |
| /inbox/CROWN | Validate | What validated enables | Press Validate | Assignment validated | inbox-validate |
| /inbox/CROWN | Return with note | Required note | Read | Form or fallback | inbox-return |
| /inbox/CROWN | Validated result | Effects and audit | Read | Spotlight on links | inbox-validated |
| /inbox/CROWN | Hand-off JSON | Routes A, B, C | Read | Spotlight on links | inbox-handoff |
| Final response | Introduction | Coverage check, answered rule | Read | Centred bubble | consolidation-intro |
| Final response | Answered count | answered / total (1 / 348 in the demo) | Read | Spotlight on summary | consolidation-count |
| Final response | Needs an answer panel | Blockers by reason | Read | Groups with links | consolidation-blockers |
| Final response | All / Open filter | Filter chips with counts | Press Open | Only open rows | consolidation-filter |
| Final response | Coverage table | One row per requirement | Read | Spotlight on table | consolidation-table |
| Final response | Units and responses column | Unit, compliance, product | Read | Spotlight on column | consolidation-units |
| Final response | State and reason column | Why a row blocks | Read | Spotlight on column | consolidation-state |
| Final response | Compliance matrix (Excel) | Download | Read | Spotlight on link | consolidation-xlsx |
| Final response | CSV export | Download | Read | Spotlight on link | consolidation-csv |
| Final response | Empty state | Nothing frozen yet | Read | Shown only when empty | consolidation-empty |
| Final response | Response outline link | Open the outline | Press link | Pathname is the outline | consolidation-to-outline |
| Response outline | Introduction | First draft with sources | Read | Spotlight | outline-intro |
| Response outline | Executive summary | Generated summary | Read | Spotlight | outline-exec |
| Response outline | Paragraphs and citations | Sources per paragraph | Read | Spotlight | outline-drafted |
| Response outline | To add or confirm | Gaps | Read | Spotlight | outline-gaps |
| Response outline | Not drafted | Nothing is guessed | Read | Spotlight | outline-not-drafted |
| Response outline | Chapters | Follow requirement categories | Read | Spotlight | outline-chapter |
| Response outline | Not full compliance | Exceptions | Read | Spotlight | outline-exceptions |
| Response outline | Validated answers | Answers used | Read | Spotlight | outline-answers |
| Response outline | Still open | Unanswered items | Read | Spotlight | outline-open |
| Response outline | Related passages | Both indexes | Read | Spotlight | outline-refs |
| Response outline | Download (Markdown) | Export | Read | Spotlight | outline-download |
| Response outline | Where this leads | Next chapter | Read | Spotlight | outline-back |
| Knowledge base | Introduction | Curator queue, long-term index | Read | Spotlight on tabs | knowledge-intro |
| Knowledge base | Learned count | Approved items in the index | Read | Spotlight on line | knowledge-learned |
| Knowledge base | Waiting, Approved, Rejected tabs | Statuses, resend rules | Read | Spotlight on tabs | knowledge-tabs |
| Knowledge base | Where items come from | Three kinds, validated-only | Use example | Queue has an item | knowledge-send |
| Knowledge base | Item card | Card anatomy | Read | Spotlight on first card | knowledge-item |
| Knowledge base | Curator note, Acting as | Who curates | Switch actor | Actor Bid Manager | knowledge-curator |
| Knowledge base | Review form | Response, note, buttons | Read | Spotlight on form | knowledge-review-form |
| Knowledge base | Approve | Writes to the index, not the matcher prompt | Press Approve | Approved item exists | knowledge-approve |
| Knowledge base | Approved tab | Result | Read | Spotlight on tab | knowledge-approved |
| Knowledge base | Reject | Required note | Press Reject | Rejected item exists | knowledge-reject |
| Product catalog | Introduction, search | Rules as data, illustrative seed | Read | Spotlight on search | catalog-intro |
| Product catalog | Unit card | Code, pillar, people | Read | Spotlight on head | catalog-unit |
| Product catalog | Products list | Offering badges, hand-off routes | Read | Spotlight on list | catalog-products |
| Product catalog | Search box | Long-term index ranking | Search, Use example | Results table present | catalog-search |
| Product catalog | Results table | Score, kind, unit, text | Read | Spotlight on results | catalog-results |
| Changes (OPP-0001) | Introduction | Why addenda matter | Read | Centred bubble | changes-intro |
| Changes | Baseline | Current frozen baseline | Read | Spotlight | changes-baseline |
| Changes | Upload form | Read a change document | Read | Spotlight | changes-upload-form |
| Changes | Read Addendum No. 1 | Sample route | Use example, press button | Change set exists | changes-read-example |
| Changes | Change set card | Header of the newest set | Read | Spotlight | changes-set-card |
| Changes | Set meta | Who read it, against what | Read | Spotlight | changes-set-meta |
| Changes | Share bar | Drastic rule | Read | Spotlight | changes-share |
| Changes | Filters | Counts by kind | Read | Spotlight | changes-filters |
| Changes | Change document | Highlights | Read | Spotlight | changes-document |
| Changes | Items table | One row per statement | Read | Spotlight | changes-table |
| Changes | Source and Quote column | Anchoring | Read | Spotlight | changes-col-quote |
| Changes | Proposed column | Kind, confidence, rationale | Read | Spotlight | changes-col-proposed |
| Changes | Target column | Baseline item | Read | Spotlight | changes-col-target |
| Changes | New wording column | Wording and category | Read | Spotlight | changes-col-wording |
| Changes | Decision form | A person confirms every row | Read | Spotlight | changes-decision-form |
| Changes | Override and confirm | Edit wording, confirm | Use example, confirm | Row decided | changes-override |
| Changes | Confirmed row | Result of a decision | Read | Spotlight | changes-decided |
| Changes | Confirm all | Accept every proposal | Press button | No undecided rows | changes-confirm-all |
| Changes | Apply | Bid Manager applies | Use example, press Apply | Baseline 2 frozen | changes-apply |
| Changes | Apply result | Added, modified, removed; returned, dispatched | Read | Spotlight | changes-result |
| Changes | Discard | Drop the set | Read | Spotlight | changes-discard |
| Changes to Traceability | Revised requirement | Follow into the addendum highlight | Click added row | Pane 1 shows the addendum | changes-trace |
| Stepper (recap) | Flow | RFP to final response chain | Read | Spotlight on stepper | recap-flow |
| Any (centred) | Change handling | Baselines, stable ids | Read | Centred bubble | recap-changes |
| Any (centred) | Audit trail | audit.record, History | Read | Centred bubble | recap-audit |
| Any (centred) | Placeholder data | Illustrative content | Read | Centred bubble | recap-placeholders |
| Any (centred) | Explore on your own | Second opportunity, actor switching | Read | Centred bubble | recap-explore |
| Any (centred) | Finish | Close, status done | Press Finish | Overlay closes, no auto-open | recap-finish |
