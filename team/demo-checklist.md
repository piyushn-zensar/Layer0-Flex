# Demo checklist: Monday 12 Oct 2026 (J-06)

Internal. For the two presenters (Piyush, Janvia). The quoted lines are for the client audience; everything else is for us.
Written on 10 Oct 2026 from the running app and `Documents/walkthrough.md`; numbers and hero IDs refreshed on 10 Oct 2026 after the P-18 reader re-run (it renumbered the requirements). The Changes step (13) was added on 10 Oct 2026 (P-11) and checked on a fresh reseed in mock mode. Re-check the numbers and IDs after any pull or reseed.

## 1. The demo data today

| Fact | Value |
|---|---|
| Opportunities | **OPP-0001** Syracuse switchgear (101-page RFP) and **OPP-0002** AI training campus (10 requirements, 6 units) |
| OPP-0001 | 814 line items grouped into **348 requirements** (162 groups, 607 sub-requirements, 21 duplicates) |
| Units | BID 245, CROWN 96, EP2 7 |
| Answers | **1 of 348 validated**, 1 submitted and waiting for validation |
| Open flags | 32 unanchored, 103 product matches nobody has accepted, rule R-003 warning, one data-sheet rating above the standard product (continuous current, p. 74) |
| Bid decision | Evidence, engineering checks, bid and portfolio checks, "Advice from Layer 0: 6 of 9 assessable criteria met; 3 cannot be assessed yet (data not available). A person decides." |
| Changes | Baseline 1 (348 requirements). The sample addendum `data/RFP/samples/rfp_syracuse_addendum_1.pdf` is **illustrative** (written for the demo, not issued by the customer). It reads from frozen answers in about a second and applies in under a second, with no model |

Navigation: top bar **Opportunities, My work, Product catalog**, a **New opportunity** button, **Acting as**. Stepper: RFP, Requirements, Traceability, Bid decision, Final response, and a **Changes** link beside it.

**Hero requirements** (checked in the live data):

| ID | Page | Use it for |
|---|---|---|
| REQ-0001-0887 | 55 | Validated Crown answer, four sub-requirements: the traceability story |
| REQ-0001-0889 | 56 | Submitted: the bid manager validates it live |
| REQ-0001-0336 | 55 | Crown item (13.2 kV feeders), assigned and unanswered: answer it live |
| REQ-0001-0893 | 57 | Relays: matched to the EP² relay and protection panel (ETO) |
| REQ-0001-0815 | 1 | Group with three sub-requirements (submission requirements) |
| REQ-0001-0141 | none | Unanchored: shows the tool says so when it cannot find the source |
| REQ-0001-0001 | 1 | Bid desk item (the deadline) |

## 2. Before the session (T minus 30 minutes)

1. Close both "Layer 0" windows. Double-click `reset-demo.cmd`, then `start.cmd` (production build: no development badge).
2. The browser opens on Traceability. Zoom 100%, notifications off, **Acting as: Bid Manager**.
3. Warm up: open Traceability, Bid decision, Final response and `/inbox/CROWN` once (first loads are slow).
4. Have the compliance matrix from the dry run saved on the desktop.
5. After the warm-up, reset again if you answered or accepted anything.

## 3. Click-path checklist (about 20 minutes; the 10-minute cut is marked **cut**)

| # | Open | Do | The audience sees | Done |
|---|---|---|---|---|
| 1 | Opportunities (**cut**) | Point at both rows | 348 and 10 requirements, unit bars, status chips | ☐ |
| 2 | OPP-0001, **RFP** | Show the file row | 101 pages, "ingested", fingerprint | ☐ |
| 3 | **Requirements** | Filters (Unanchored 32, Duplicates 21); expand REQ-0001-0815; click **History** on one | Groups, sub-requirements, exact quotes, who changed what | ☐ |
| 4 | **Traceability** (**cut**) | Select **REQ-0001-0887** | Page 55 highlighted, three panels follow | ☐ |
| 5 | Traceability | Select **REQ-0001-0893** | EP² relay panel, ETO | ☐ |
| 6 | Traceability (**cut**) | **Accept** the match on 0887 | Match status changes; the unaccepted count drops by one | ☐ |
| 7 | **Bid decision** | Evidence, the bid and portfolio checks card, participation, go decision, the advice box, one criterion's judgement | Advice, flags, the continuous-current deviation (p. 74), "a person decides" | ☐ |
| 8 | Acting as **Crown Product Manager**, then **My work** (**cut**) | Answer **REQ-0001-0336**: met, product, how it is met, **Submit** | Status changes to "submitted" | ☐ |
| 9 | Acting as **Bid Manager**, Opportunities, unit code **CROWN** (**cut**) | **Validate** REQ-0001-0889 and REQ-0001-0336 | Status changes to "validated" | ☐ |
| 10 | **Final response** (**cut**) | Show the count and the blocker panel, click a blocker link, then the Open filter | Count moves from 1 to 3 of 348; groups by reason; the link lands in Traceability | ☐ |
| 11 | Final response | **Download compliance matrix (Excel)**; the CSV link is beside it | Customer sheet (validated answers only, Comply / Open, RFP order) and an internal Tracking sheet | ☐ |
| 12 | CROWN work package | Open "Hand-off for this unit's systems" | JSON download: starting points, not a design | ☐ |
| 13 | **Changes** (**cut**). Do it last: it changes the demo data | Acting as **Bid Manager**. Upload the sample addendum, show the eight statements, **Confirm all proposals**, **Apply to requirements** (details below) | Eight classified statements (2 modified, 2 added, 1 removed, 1 unchanged, 2 not a requirement); baseline 2; REQ-0001-0887 back with Crown; two new requirements | ☐ |
| 14 | Product catalog | Scroll the units and products | Illustrative data, to be confirmed | ☐ |

**Step 13 in detail (about 3 minutes; reset afterwards).** Say first that the addendum is an illustration written for the demo, not a customer document.

1. Click **Changes** beside the stepper. It shows "Current baseline 1: 348 requirements".
2. Choose `data/RFP/samples/rfp_syracuse_addendum_1.pdf`, then **Read the change document**. A card opens, in review, "0 / 8 confirmed", with 0.9% of the baseline modified or removed (not drastic; the threshold, 25%, is a placeholder).
3. Point at the chips: Modified 2, Added 2, Removed 1, Unchanged 1, Not a requirement 2. Open **Change document** and click a source link: the statement is highlighted on the addendum page.
4. Walk four rows. Row 1: the proposal due date, 09/15 to 09/29/2023, pointing at **REQ-0001-0039**. Row 2: breaker positions 18 to 20, pointing at **REQ-0001-0332**, a sub-requirement of REQ-0001-0887. Row 5: the AutoCAD drawings sentence is deleted, pointing at **REQ-0001-0130**. Row 6: the Q&A answer confirms the RFP, so it is "unchanged". Say that a person can override any row (kind, target, wording); do not do it live.
5. **Confirm all proposals**, then **Apply to requirements** (only the Bid Manager can). The result box starts "Baseline 2 frozen with the changes": added **REQ-0001-0977** (seismic qualification, matched to Crown) and **REQ-0001-0978** (60-month warranty, bid desk); modified REQ-0001-0039 and REQ-0001-0332; removed REQ-0001-0130; "2 unit answer(s) returned for review; 2 new assignment(s) sent to the units".
6. Open `/inbox/CROWN`. REQ-0001-0887 (validated before) is **returned**: "Changed by rfp_syracuse_addendum_1.pdf: sub-requirement REQ-0001-0332 now reads: ...". Say: "A changed sub-requirement sends its group's answer back to the unit. Nothing else moved."
7. In the result box click **REQ-0001-0977**. Traceability opens with pane 1 on the addendum (page 1, lines highlighted), its source column naming the file, and Crown as the unit (ETO). The changed sub-requirements appear under their groups (REQ-0001-0887, REQ-0001-0824) with the addendum's page and lines but no file name and no highlight: do not select them for this point. On the Requirements page, **History** on REQ-0001-0332 shows the original and the revised wording, with the addendum as the reason.
8. Numbers after applying (they no longer match section 1 until you reset): 349 requirements; the Final response count drops by one (REQ-0001-0887 is open again); baseline 2.

**From scratch (optional).** Create a **New opportunity**, upload the same RFP and let it read from the frozen answers, then stop and say "here is one that has already been through the process". `INSTALL.md` says new line items get keyword matching, labelled as such. Time it in the dry run before committing to it.

## 4. Presenter script

1. **Opportunities.** "One place for every bid. For the Syracuse RFP, 348 requirements and how far each unit has answered. The bar is validated work first, then work awaiting validation."
2. **RFP.** "The customer's 101-page PDF is the starting point. Everything we show traces back to this file."
3. **Requirements.** "The reader turned 814 raw line items into 348 requirements by grouping related ones and flagging duplicates. Each has its exact quote and page, and nothing is invented. When the source cannot be found it says so: 32 are unanchored, and a person decides." On History: "Every change is kept: who, when, original and changed."
4. **Traceability.** "Pick a requirement. The RFP page jumps to it, the breakdown follows, and the proposed unit and product appear. This one goes to Crown." On 0893: "Relays go to Electrical Power Products." On Accept: "The system proposes, a person accepts."
5. **Bid decision.** "Evidence first: categories, the mix of offering types, the suggested units. The engineering checks flag open points. The bid and portfolio checks compare the RFP's data sheet with our standard products: here the continuous current asked is above the standard rating. Those standards are placeholders for now. The advice says how many criteria are met, and the bid manager records their own judgement. A person decides."
6. **My work.** "Each unit sees only its own lines. The Crown product manager answers: met, with which product and how." As bid manager: "The bid manager validates, or returns it with a note."
7. **Final response.** "Every requirement must be answered and validated. What is still open is listed by reason, with links back to the source. Nothing disappears."
8. **Matrix.** "The Excel workbook has a customer sheet with validated answers only, and an internal sheet that carries the unit, product, offering type, answer, who answered, who validated and the status."
9. **Changes.** "An addendum arrives after the baseline is frozen. This one is an illustration we wrote for the demo, not a customer document. The change agent reads it and compares each statement with the frozen requirements: two modified, two added, one removed, one that only confirms the RFP, and two that are not requirements. A person confirms each one, and only the bid manager applies them. Only what changed gets a new version and a new baseline. Here the changed breaker count sends the group's validated answer back to Crown with a note. Everything else stays as it was." On Traceability: "The new requirement points at the addendum page it came from."

## 5. Business value messages

- **Traceability:** every response can be followed back to the exact RFP page and quote.
- **People decide:** Layer 0 proposes and flags. Every decision is recorded with who made it. The advice is labelled as advice.
- **Honest about gaps:** unanchored items, unaccepted matches and deviations from the standard product are flagged, never hidden.
- **Several units, one view:** work is split by unit and consolidated, with a live count of what blocks completion.
- **Neither CRM nor CPQ:** the bridge between them. CTO items produce a CPQ seed in the hand-off file.
- **Proof of concept:** say it plainly. Everything on screen runs from frozen model answers for this RFP.

## 6. Backup navigation

| If this fails | Do this |
|---|---|
| A page shows an error or loads forever | Refresh. Check both "Layer 0" windows are open. If the API is stale, run `reset-demo.cmd` then `start.cmd` (about a minute). |
| Traceability is slow | Open it first as a warm-up. Fall back to Final response: its IDs link to the same requirement. |
| Acting as does not switch | Open `/inbox/CROWN` directly. The unit codes on Opportunities link there. |
| Live submit or validate fails | Use REQ-0001-0887, which is already validated, and show the Final response count. |
| The download fails | Show the workbook saved on the desktop. |
| A full reset is needed | Close both windows, `reset-demo.cmd`, `start.cmd`. The opportunity opens in Traceability. |
| The Changes upload is refused | "is still in review": the Bid Manager discards the open set, then upload again. "no frozen answers": only `rfp_syracuse_addendum_1.pdf` can be read offline; check the file. "was already applied": the step was done once, so reset. If it still fails, say Changes is built and tested, and move on. |

## 7. Likely client questions

| Question | Suggested answer |
|---|---|
| Does the AI decide? | No. It proposes and flags. Participation, go/no-go and validation are made and recorded by a named person. |
| How accurate is the reading? | We measure against a hand-checked list. Early recall is high (about 92%), precision is lower because of how line items are grouped, and the list is still being reviewed. **Agree beforehand whether to quote the numbers.** |
| Where does our bid data go? | The proof of concept can use a hosted model, and this demo replays frozen answers. An enterprise-hosted model for non-public bids is on the roadmap. |
| What about addenda and changes? | A first version is built. An addendum is read, each statement is compared with the frozen baseline and a person confirms each one. Only the bid manager applies it: changed requirements get a new version, new ones get new IDs, removed ones leave, and the affected unit answers go back for review. Everything else, including its match, stays as it was. The sample addendum is illustrative, not from the customer. The share of change that counts as drastic (a new opportunity) is a placeholder, and the customer's own change process is still to be confirmed. |
| Excel output? | Yes: a formatted workbook with a customer sheet and an internal tracking sheet, plus the CSV. |
| Knowledge base and past bids? | The catalog holds illustrative past responses. A feedback queue is planned. |
| Where do the standard ratings and capacities come from? | They are placeholders until each unit confirms them. The check itself is real: it reads the RFP's data sheet. |
| Can it run on our laptop? | Yes: `setup.cmd` and `start.cmd`. It needs no API key for the demo. |
| What about licences? | One component's licence needs a decision before any pilot. Do not volunteer this. |
| Is it production-ready? | No, it is a proof of concept. |

## 8. Dry-run checklist (Piyush and Janvia)

- ☐ **Run 1, Piyush driving, Janvia watching:** the full path from a reset, timed (note the Traceability load and each action).
- ☐ **Run 2, Janvia driving:** from a reset, without help.
- ☐ **Failure drills:** stop the API mid-demo and recover with section 6. Switch roles twice. Submit and validate.
- ☐ **Changes step (13):** upload the sample addendum, confirm all, apply, check REQ-0001-0887 in `/inbox/CROWN` and REQ-0001-0977 in Traceability (pane 1 shows the addendum page). Then `reset-demo.cmd`. Time the upload and the apply.
- ☐ **Demo laptop:** `setup.cmd` and `start.cmd` on the laptop used on Monday, or on a clean copy.
- ☐ **Checks:** production build shows no "N" badge, 100% zoom, notifications off.
- ☐ **Measure:** the first Traceability load; the upload-and-read time for the optional from-scratch path; the workbook in real Excel.
- ☐ **Decide:** whether to quote the reading accuracy numbers; whether to phrase around, or ask owners to change, the wording listed in section 9.
- ☐ **Sign-off:** one clean run with no manual fixes, then `reset-demo.cmd` right before the session.

## 9. Known risks and open items

1. **`Documents/walkthrough.md` is stale:** it says 13 requirements and 4 of 13 answered. Do not hand it out until the J-03 retake is done.
2. **Wording on screen:** the RFP help text says "reader agent"; Traceability shows "retrieval score" and "(no agent answer)"; the catalog shows `SEMI_CUSTOM`. Phrase around it or ask the owners to change it.
3. **The demo is mutable:** every live action changes the data. Reset before each rehearsal and before the real session. **Applying the addendum (step 13) changes the data for good:** baseline 2, 349 requirements, REQ-0001-0887 returned, two new assignments, and there is no undo. Do it last, then `reset-demo.cmd`. Section 1 numbers no longer hold until you reset.
4. **The flags are real:** the deviation check flags continuous current against a placeholder standard; say so. Changing participation triggers a new dispatch, so talk about it and do not do it live.
5. **Not verified yet:** the live Accept, answer and validate clicks; Traceability timing; Excel behaviour; the from-scratch upload path. They are in the dry run for that reason.
6. **After a pull:** a stale API breaks Traceability. Restart the API and reseed (`reset-demo.cmd`) before every rehearsal.
7. **Open tasks that touch the demo:** J-03 retake (screenshots, items 2 and 5-9), P-05 golden list review.
8. **The addendum is illustrative:** `rfp_syracuse_addendum_1.pdf` was written for the demo and is not a customer document. Say so to the audience (its first lines say so too). Never present it as the real Syracuse addendum.
9. **Changes limits to know:** REQ-0001-0039 and REQ-0001-0332 are sub-requirements, so Traceability lists them under their groups with the addendum's page and lines but no file name and no highlight. Show REQ-0001-0977 there instead. The compliance matrix and the response outline also give a change document's page without naming it. Only this addendum can be read offline; any other file needs a live model.
