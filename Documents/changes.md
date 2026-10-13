# Layer 0: Changes from the 12 Oct 2026 Review

Status: **Expected (review meetings)** for what the review asked; **Proposed (inferred design)** for how the build answers it. Nothing in this document is built yet unless a change says so. Written 13 Oct 2026.

## 1. Purpose, Who This Is For, and Sources

**Purpose.** This document is the register of the changes decided after the review meeting of 12 Oct 2026. For each change it says what the system does today, what must change, and how the result is checked. It is the reference for the next build iteration (13 to 19 Oct 2026).

**Who this is for.** The Zensar point of contact, who reviews the direction, and the developers who build it.

**Sources.**
- The review meeting of 12 Oct 2026 (Flextronics CPQ review). Time references such as "40:14–44:46" point into the meeting recording.
- The project team's comparison of that review with the documented current system (13 Oct 2026).
- The documented current system at commit 4c6d866: [current-system/01-system-architecture.md](current-system/01-system-architecture.md), [current-system/02-technical-architecture.md](current-system/02-technical-architecture.md), [current-system/03-ui-view.md](current-system/03-ui-view.md), [current-system/04-api-view.md](current-system/04-api-view.md).

**How it relates to the other documents.** This document supersedes parts of the target workflow in [project-overview.md](project-overview.md) section 7 (marked there as history). Build details of the new design are in [technical-architecture.md](technical-architecture.md) section 16.

## 2. Summary

The review was positive about the progress and the depth of the build. Its main instruction was to make the system **business-ready**: accurate, using the business's own words, with realistic roles, and convincing for real Flex users. Five themes run through the changes:

1. **Every admitted requirement has verifiable source evidence.** Text that cannot be traced to its source stays visible as an exception, outside the requirement set (C-02, C-03).
2. **The first extraction becomes a stable reference.** It is preserved as it was produced; later corrections and customer changes are versioned on top of it and can be told apart (C-04).
3. **The bid manager coordinates; specialists assess.** The bid manager reads a summary, routes the work and consolidates. Product managers and design engineers assess the requirements. The go/no-go decision comes after their assessment, not before (C-05 to C-08).
4. **Real identities and business wording.** Users sign in with assigned roles, enforced by the server; the screens use the business's terms ("Bids", "Document type") (C-01, C-09).
5. **A usable, interactive compliance matrix** inside the application, with reasons, workarounds and clickable source references (C-12 to C-14).

Three questions are kept apart throughout, because they have different owners and different answers:

| Question | Answered by | Where it is recorded |
|---|---|---|
| Is this an accurately extracted customer obligation? | The extraction, with its source evidence; corrected by a named person when wrong | The requirement register and its extraction snapshot |
| Can a business unit satisfy it, and under what conditions? | The unit's product manager and design engineer | The unit's response (compliance, reason, workaround, next steps) |
| Should the business pursue the bid? | The bid manager, using the specialists' evidence | The go/no-go decision |

A requirement that a unit cannot meet stays in the register as **non-compliant**. It is never "rejected" in a way that removes it from coverage. A source-backed requirement with no product match is still a valid customer requirement: it is shown as a capability gap or a routing question.

## 3. Revised Target Workflow (revision 3)

Expected (review meetings), 12 Oct 2026, for the stages and owners. The exact approval sequence below is the **Proposed (inferred design)** default for the proof of concept; the review asked for workflows that can be configured per customer rather than one fixed hierarchy.

| # | Stage | Owner | What happens |
|---|---|---|---|
| 1 | Intake and extraction | System | Keep the documents unchanged. Read them into source-backed requirements. Preserve the first extraction as an immutable snapshot. Put text without verifiable evidence in the exception queue. Propose a business unit and product for each requirement |
| 2 | Initial understanding | Bid manager | Read a high-level summary: what the customer wants, the major sections, the suggested business units and the open questions. Drill into details when needed. No per-requirement approve or reject |
| 3 | Routing | Bid manager | Choose the participating units, send the requirements to the units and named specialists ("Send for assessment"), add questions or comments, and resolve requirements that have no owner |
| 4 | Product assessment | Unit product manager | Assess product fit and constraints; flag where engineering analysis or customization is needed |
| 5 | Engineering assessment | Unit design engineer | Assess technical compliance, deviations, modifications, feasibility and possible workarounds |
| 6 | Unit response | Product manager and design engineer | Return a supported assessment per requirement: fully compliant, partially compliant or non-compliant, with the reason, conditions, workaround and next steps. The unit's technical authority validates it |
| 7 | Consolidation | Bid manager | Assemble the unit responses in the compliance matrix, find missing answers and unresolved conflicts, prepare the decision summary |
| 8 | Go / no-go | Bid manager | Makes the final go/no-go call with the specialists' evidence in front of them. No separate approver role |
| — | Changes | Bid manager and specialists | Customer changes (addenda, clarifications, change requests) and extraction corrections are versioned against the stable reference and kept distinguishable |

**Decision authority (project-team decision, 13 Oct 2026).** The bid manager makes the final go/no-go call. There is no separate, configured bid-approver role; the configurable part of the workflow is limited to who responds and who validates inside a unit (C-07).

Example of a unit response the bid manager coordinates but does not certify: "The electrical specification can be met, but the requested three-week delivery cannot. Six weeks can be offered, subject to component availability."

**What this supersedes.** Revision 2 (project-overview.md section 7) placed participation and go/no-go before dispatch and had the bid manager approve every requirement before freezing and validate every unit answer. Those three points are replaced by stages 2, 3, 6 and 8 above. Revision 2 stays in project-overview.md as history.

**Scope focus.** The proof of concept covers the first stages of the business's RFP response process: intake, requirement understanding, assessment and qualification. It is not a pricing, quoting or ERP replacement; inventory, cost and other operational facts come from the business's existing systems (45:04–46:56).

## 4. Change Register

Priority 1 is needed before the next demonstration; priority 2 improves the compliance matrix and traceability; priority 3 items are selective improvements or investigations. Checkpoints: **CP1 Wed 14 Oct 2026**, **CP2 Fri 16 Oct 2026**, **Target Mon 19 Oct 2026** (the improved demonstration shown to real users).

| ID | Change | Priority | Checkpoint | Status |
|---|---|---|---|---|
| C-01 | Business terminology: Bids, New bid, Document type, no developer wording | 1 | CP1 | Expected (review meetings) |
| C-02 | Source-backed requirement register; exception queue for unverified text | 1 | CP1 (queue), CP2 (resolution) | Expected (review meetings) |
| C-03 | Stronger source anchoring; extraction coverage measured separately | 1 | Target | Proposed (inferred design) |
| C-04 | Immutable extraction snapshot; versioned corrections and customer changes | 1 | CP2 | Expected (review meetings) |
| C-05 | Bid manager: summary, routing and coordination, without per-requirement approval | 1 | CP2 | Expected (review meetings) |
| C-06 | Specialist assessment before the go/no-go decision | 1 | CP1 (backend), CP2 (screens) | Expected (review meetings) |
| C-07 | Distinct product-manager and design-engineer responsibilities; configurable validation | 1 | CP2 | Expected (review meetings) |
| C-08 | Explicit ownership: no silent fallback to the bid manager | 1 | CP2 | Proposed (inferred design) |
| C-09 | Sign-in with assigned roles, enforced by the server | 1 | CP2 | Expected (review meetings) |
| C-10 | Focused scope and corrected decision checks | 1 | CP1 | Expected (review meetings) |
| C-11 | Relevant demonstration data and an independent validation RFP | 1 | CP1 (remove), Target (new RFP) | Expected (review meetings) |
| C-12 | Unit responses with reasons, conditions, workarounds and next steps | 2 | CP2 | Expected (review meetings) |
| C-13 | Interactive compliance matrix inside the application | 2 | Target | Expected (review meetings) |
| C-14 | Clickable source references from the matrix | 2 | Target | Expected (review meetings) |
| C-15 | Three panes: enlarge a pane, lock or unlock linked navigation | 2 | Target | Expected (review meetings) |
| C-16 | Complete, read-only history of every requirement and response change | 2 | Target | Expected (review meetings) |
| C-17 | Questions and comments during routing and assessment | 2 | Target | Expected (review meetings) |
| C-18 | Word and Excel documents (CAD excluded) | 3 | Investigation | Expected (review meetings), priority not settled |
| C-19 | Past Flex RFP responses to support extraction | 3 | Investigation | Expected (review meetings) |
| C-20 | Drill-down from summary categories and offering types | 3 | Optional | Expected (review meetings), optional |
| C-21 | Spreadsheet tools for large compliance matrices | 3 | Investigation | Expected (review meetings), exploratory |
| C-22 | A walkthrough that never covers the application | 3 | Target | Expected (review meetings) |

## 5. Changes in Detail

Each change lists: what the review asked (with the recording time), the current behaviour (with the section of the current-system documents), the required change, how it is checked, and open points.

### C-01. Business terminology

- **Asked (03:40–04:12, 09:12–10:58, 28:22–28:44).** Use the business's words. A bid contains requirements, not more opportunities. "Role of a document" is the wrong term.
- **Today.** The screens say "Opportunities", "New opportunity" and "Role" with the values main, addendum, qa, change, other ([03-ui-view.md](current-system/03-ui-view.md) sections 4, 7, 8, 9). Several labels are developer wording (for example "provenance", "UNANCHORED", "bid desk", raw status values such as `not_met`).
- **Change.**
  - "Opportunities" becomes **Bids**; "New opportunity" becomes **New bid**; "Opportunity" in headings, messages and the walkthrough becomes **Bid**.
  - "Role" becomes **Document type**, with **Main RFP**, **Addendum**, **Clarification / Q&A**, **Change request** and **Other**. The exact list stays open for refinement.
  - Every visible label is reviewed against a shared glossary (technical-architecture.md section 16.2). Internal identifiers, stored values and API paths do not change in this iteration, so no data or interface breaks.
- **Checked by.** No visible "opportunity", "role", "provenance" or raw stored value on any screen, toast or export; the walkthrough uses the same words.
- **Open.** Whether the visible bid ID should change from `OPP-0001` to a bid prefix (Needs confirmation).

### C-02. Source-backed requirement register and exception queue

- **Asked (59:13–1:09:21).** Every requirement must trace to its original source, ideally page, paragraph and line. Requirements without a source mapping are kept apart from validated ones; other extraction techniques should be explored. Unverified requirements were described as a potential go/no-go issue.
- **Today.** A quote the anchoring cannot find is stored as `UNANCHORED` with no page. It can still be approved, frozen, matched, dispatched and exported (33 of 976 rows on the Syracuse demonstration; [01-system-architecture.md](current-system/01-system-architecture.md) section 10.3; [02-technical-architecture.md](current-system/02-technical-architecture.md) section 9).
- **Change.**
  - The **requirement register** (the authoritative set used for assessment, matrix and decision) admits only requirements with verified source evidence: document, page, line range and the verbatim text found there.
  - Text the extraction proposes without verifiable evidence goes to an **exception queue**, outside the register, never silently dropped. Each exception shows the proposed text, the page the extraction suggested and why it failed.
  - A person resolves an exception by **linking it to its lines** on the page (it then enters the register with an exact source) or by **dismissing** it with a reason. Both are recorded.
  - The server refuses to admit, publish, route or export a requirement without verified evidence.
- **Checked by.** Zero requirements without a source in the register, matrix, exports and decision summary; every exception visible on the Requirements screen and counted on the summary as an open question.
- **Open.** None.

### C-03. Stronger source anchoring; coverage measured separately

- **Why (project-team analysis, from the C-02 discussion).** A system can show 100% source-linked requirements while missing half of the document. Traceability and completeness are different measures. The present anchoring needs the whole quote on one page, matches an exact normalised substring, takes the first occurrence and fails on words broken across lines.
- **Today.** See [02-technical-architecture.md](current-system/02-technical-architecture.md) section 9 (anchoring) and section 8 (reading).
- **Change.**
  - The reader agent returns the **line references** it read the requirement from, as well as the quote; the system verifies the quote against those lines rather than searching the whole document.
  - A requirement may have **several source spans**, including spans across a page break.
  - Words hyphenated across a line break are joined before comparison; when the same wording appears twice, the occurrence nearest to the given lines is used.
  - The extraction reports **coverage**: pages read, pages not readable, chunks the agent failed on, candidates proposed, admitted, in the exception queue and duplicates. This is shown on the RFP step and in the bid summary.
- **Checked by.** On the Syracuse RFP: fewer exceptions than today's 33 unanchored rows, with no loss of recall against the golden list; the coverage figures add up to the pages and candidates of the document.
- **Note.** Changing the reader's answer format means its frozen answers are generated again with the live model.

### C-04. Immutable extraction snapshot; versioned corrections and customer changes

- **Asked (11:57–15:56).** The initial extracted interpretation must become a stable reference tied to the customer document. A temperature of zero was recommended for extraction.
- **Today.** Model answers are cached and replayed; baseline 1 freezes the approved requirements; addenda create new versions and baselines; the audit log is append-only. But a re-read before review discards the earlier agent drafts; edits before the freeze change the row in place; a requirement missed after the freeze can only come in through a change document, even when the customer changed nothing ([01-system-architecture.md](current-system/01-system-architecture.md) sections 10.3 and 10.4).
- **Change.**
  - The first extraction of each document is stored as **extraction snapshot E1**: every candidate with its source references, grouping, duplicates, exceptions and coverage, plus the model and pipeline versions. It is never modified. A later re-read creates E2 only when a named person asks for it with a reason; E1 stays readable.
  - The working register starts from E1. Every later difference is a **new version** with its **origin**:
    - **extraction correction**: a person fixes how the document was read (a missed obligation on page 12, a wrong split), with the page, the person and the reason. No change document is needed.
    - **customer change**: an addendum, clarification or change request from the customer, linked to that document (as today).
  - Freezing does not mean that the first extraction is right for ever; it means it cannot be silently rewritten. Temperature zero stays, but repeatability comes from the stored snapshot and versions, not from the model setting alone.
  - The register is kept in the versioned database. The retrieval (RAG) indexes only help to find passages; rebuilding them never changes which requirements exist.
- **Checked by.** E1 can be shown unchanged after corrections and addenda; every version names its origin; the history of a requirement distinguishes corrections from customer changes; a re-read without a reason is refused.

### C-05. The bid manager summarises, routes and coordinates

- **Asked (05:30–06:20, 40:14–44:46, 49:32–50:10, 1:10:36–1:11:28).** The bid manager is not a system administrator and does not approve technical requirements. The bid manager reads the high-level summary, routes the work to the right teams, consolidates their assessments and makes the final go/no-go call (project-team decision, 13 Oct 2026: no separate approver role). The initial view has no approve or disapprove controls.
- **Today.** The bid manager approves or rejects every line item before freezing, validates every unit answer and records participation and go/no-go before any unit sees the work ([03-ui-view.md](current-system/03-ui-view.md) sections 10 and 12).
- **Change.**
  - A **bid summary** for the bid manager: what the customer wants, the major sections, requirement counts by category and offering type, the suggested units, and the **open questions** (exceptions, requirements without an owner, rule warnings).
  - **Routing**: choose the participating units, see which requirement goes to which unit and specialist, fix requirements without an owner, add questions, then **Send for assessment**. This publishes the register as the working baseline and dispatches the work.
  - No per-requirement approve or reject on the initial view. Extraction mistakes are fixed as extraction corrections (C-04), by the bid manager or a specialist, with a reason.
- **Checked by.** A bid goes from read to routed without the bid manager approving a single technical requirement; the summary loads first and drills down into traceability.

### C-06. Specialist assessment before the go/no-go decision

- **Asked (40:14–44:46).** The RFP is analysed and distributed to the product managers and design engineers first; they assess feasibility, compliance, limits and workarounds. Only then does the bid manager receive the consolidated information for the decision.
- **Today.** Dispatch needs a recorded "go" ([04-api-view.md](current-system/04-api-view.md) sections 12 and 19), so the evidence the decision needs arrives after the decision.
- **Change.**
  - Dispatch needs only a published register; it no longer needs a go decision.
  - The go/no-go screen comes after consolidation and shows the assessment: per requirement and unit, fully, partially or non-compliant, with the reasons; missing answers and conflicts.
  - Recording go/no-go while assessments are missing is allowed but shows a warning. A no-go stops further dispatch and closes open work.
- **Checked by.** On a new bid: route → units answer → consolidate → decide, in that order, without a go decision before routing.

### C-07. Product manager and design engineer have distinct responsibilities

- **Asked (41:17–44:46, 04:26–05:55, 1:10:36–1:11:41).** The product manager brings broad product experience; the design engineer works through the design implications; together they decide whether and how the unit can respond. Workflow assignments must be configurable, not one customer's hierarchy built in.
- **Today.** Both may answer any item of their unit; only the bid manager validates answers ([03-ui-view.md](current-system/03-ui-view.md) section 16; [02-technical-architecture.md](current-system/02-technical-architecture.md) section 14).
- **Change.**
  - Default proof-of-concept sequence: the **design engineer** prepares the engineering assessment and response; the **product manager** reviews product fit and **validates** the unit's response. Either can return it within the unit with a note.
  - The bid manager checks completeness and coordinates (can return an answer with a question) but does not certify technical feasibility.
  - Who may respond and who may validate, per stage and per unit, is read from a **workflow configuration** file, so another customer's sequence is a configuration change.
- **Checked by.** A design engineer cannot validate; a product manager of another unit cannot answer; changing the configuration changes the rights without code changes.

### C-08. Explicit ownership

- **Why (project-team analysis).** Today a requirement with no matched unit, or whose match was rejected, falls back to the bid desk, which implies the bid manager can answer it.
- **Change.** The bid desk owns only non-product items (for example submission dates and administrative or commercial terms routed there by rule). A product requirement without a unit is shown as **Needs an owner** on the summary and in routing, and cannot be sent for assessment until a person assigns a unit or records why no unit can offer it (a capability gap, kept in the register).
- **Checked by.** No product requirement lands in the bid desk's work silently; capability gaps appear in the matrix as non-compliant with the reason.

### C-09. Sign-in with assigned roles

- **Asked (04:26–05:55, 1:11:28, 1:10:36–1:11:41).** Roles are assigned through a person's profile; the bid manager is not an administrator; later integration with IAM or an internal role model is expected; unrestricted role switching should go.
- **Today.** The application trusts an "Acting as" name sent by the browser and defaults to "Bid Manager"; there is no authenticated identity ([01-system-architecture.md](current-system/01-system-architecture.md) section 12; [02-technical-architecture.md](current-system/02-technical-architecture.md) section 22).
- **Change.**
  - Users **sign in** with an account and receive a signed **JSON Web Token (JWT)**, kept simple: no external identity service in the proof of concept. Each account has a role (bid manager, product manager, design engineer, administrator) and, for unit roles, a business unit; both are carried in the token.
  - The server checks role, unit and assignment on every write. Hiding buttons is not the control.
  - The "Acting as" picker is removed; the top bar shows the signed-in person and a Sign out button. Demonstrations switch roles by signing in as another demonstration account.
  - Everyone signed in can read the source and shared requirements of the bids they work on.
- **Checked by.** Requests without a session are refused; each forbidden action is refused by the server with a clear message, for each role.
- **Open.** Single sign-on with the enterprise identity provider is the pilot step (Needs confirmation); the proof of concept uses local demonstration accounts.

### C-10. Focused scope and corrected decision checks

- **Asked (37:12–39:17, 45:04–45:49, 58:41).** Remove the cost-against-budget check; review the other checks; "Delivery against…" must clearly mean assessment against the RFP schedule. Competitor information was proposed for removal and acknowledged. Stay within intake, requirement understanding and qualification.
- **Today.** Twelve go/no-go criteria including "Cost against budget", "Competitor information" and "Delivery against the RFP schedule", the first two shown as "data not yet available"; two criterion questions show internal references ([03-ui-view.md](current-system/03-ui-view.md) section 12).
- **Change.** Remove "Cost against budget" and "Competitor information". Rename the delivery criterion to **Schedule: can the units meet the RFP's dates?**, assessed from the unit responses to schedule requirements. Coverage and "matches reviewed" are computed from unit responses once the assessment has run. No internal references in visible text. Every remaining check is reviewed for whether it supports a real decision.
- **Checked by.** No unsupported pricing or competitor judgement appears as decision evidence.

### C-11. Relevant demonstration data and an independent validation RFP

- **Asked (01:24–02:15, 20:48–21:31).** Off-domain examples such as an AI training campus distract the audience. Validate with an outside RFP, not another document derived from the existing test RFP.
- **Today.** The bid list shows the Syracuse switchgear RFP and a fictional AI training campus sample ([03-ui-view.md](current-system/03-ui-view.md) section 7).
- **Change.** The demonstration seeds only domain-relevant bids (switchgear and electrical power). A second public switchgear or substation RFP from a different issuer is read, frozen and matched as an independent validation case.
- **Checked by.** The bid list contains only electrical-domain bids; the independent RFP runs end to end with its own frozen answers.
- **Open.** Which public RFP is used (the project team proposes candidates; Needs confirmation).

### C-12. Unit responses with reasons, conditions, workarounds and next steps

- **Asked (29:55–33:02, 50:10–51:48).** Each requirement's status is fully compliant, partially compliant or non-compliant, with the rationale, comments, a possible workaround or fix, and next steps. The technical teams enter their own assessment.
- **Today.** A compliance value (met, partial, not met, exception), a product reference and one short text ([03-ui-view.md](current-system/03-ui-view.md) section 16).
- **Change.** Compliance is **Fully compliant**, **Partially compliant** or **Non-compliant**. Each response records how it is met, the product or configuration, and, for anything less than fully compliant: what is not met and why, conditions, the workaround or fix, and next steps. These fields are required for partial and non-compliance. The earlier "exception" value is retired.
- **Checked by.** A partially compliant response cannot be submitted without its reason; every field reaches the matrix and the exports.

### C-13. Interactive compliance matrix inside the application

- **Asked (29:55–32:52, 52:28–53:06, 1:12:39–1:13:15).** Open the compliance matrix in the application, inspect a row's details, see the explanation of a partial status by hovering; keep the download.
- **Today.** The Final response screen lists coverage and blockers; the matrix exists only as a downloaded Excel or CSV file ([03-ui-view.md](current-system/03-ui-view.md) section 13).
- **Change.** A **Compliance matrix** screen: one row per requirement and unit with requirement, source, unit, product, compliance, reason, workaround, next steps and state; filters; a row opens a detail panel; hovering a partial or non-compliant status shows its explanation. Excel and CSV downloads stay, with the new columns.
- **Checked by.** The full Syracuse matrix opens in the browser and can be filtered and inspected without downloading.

### C-14. Clickable source references

- **Asked (56:15–56:55).** From the compliance matrix, clicking an RFP reference opens the original page, line or passage.
- **Change.** Every source reference in the matrix opens a preview of the page with the requirement's lines highlighted, beside the matrix, with a link to the full traceability view.
- **Checked by.** Any row's reference shows its highlighted lines in one click.

### C-15. Three panes: enlarge, lock and unlock

- **Asked (47:00–50:10).** Three active panes (original RFP, extracted requirements, product mapping); enlarge one; drill into a requirement; synchronised movement that can be locked or unlocked per pane. Actual responses only at the later stage.
- **Today.** The three panes are always linked and always show unit responses ([03-ui-view.md](current-system/03-ui-view.md) section 11).
- **Change.** Each pane can be enlarged and restored; a lock per pane controls whether it follows the selection; unit responses appear in pane 3 only once the bid has been sent for assessment.
- **Checked by.** With a pane unlocked, selecting elsewhere does not move it; enlarging keeps the selection.

### C-16. Complete, read-only history

- **Asked (1:11:48–1:12:13).** Record who changed any requirement or response, when, and what; keep the history read-only with full traceability.
- **Today.** Requirement history is rebuilt from the append-only audit log; unit responses have no history view; there is no bid-level view of the log ([03-ui-view.md](current-system/03-ui-view.md) section 10).
- **Change.** A history for every unit response (each submission, validation, return and change) and a read-only **activity log** per bid, filterable by requirement, unit and person. Requirement history labels each version's origin (C-04).
- **Checked by.** Every change to a requirement or response appears with person, time and before/after.

### C-17. Questions and comments

- **Asked (47:00–50:10).** The initial mapping view carries questions and comments; routing includes asking.
- **Change.** The bid manager and the specialists can add questions and comments to a requirement or a unit's assignment; open questions count on the summary and must be closed or answered before consolidation completes.
- **Checked by.** A question added during routing is visible to the unit and closes when answered.

### C-18. Word and Excel documents (CAD excluded)

- **Asked (1:07:03–1:08:30).** PDF, Word and spreadsheets are relevant; CAD is not needed for the proof of concept. The delivery priority is not settled.
- **Change.** Investigate reading Word and Excel documents into the same layout model (paragraphs and rows as numbered lines, sections and sheets as pages), so anchoring and traceability work unchanged. Build it if the investigation is short.

### C-19. Past Flex RFP responses to support extraction

- **Asked (17:16–17:52).** Use previously answered Flex RFPs to strengthen extraction, classification and credibility.
- **Change.** Investigation: what past material is needed and how it would help the reader and the matcher, using the existing long-term knowledge index. This is separate from preserving the current extraction (C-04). Needs real past responses from the business units (Needs confirmation).

### C-20. Drill-down from summary categories (optional)

- **Asked (24:06–26:01).** Clicking ETO, CTO, semi-custom, legal and other summary counts could lead straight to those requirements; not every suggested feature should be added at once.
- **Change.** Optional: summary counts link to the traceability view filtered by category or offering type.

### C-21. Spreadsheet tools for large matrices (exploratory)

- **Asked (55:05–56:15, 1:15:45–1:18:01).** Tools such as Row Zero, Quadratic or Gigasheet were mentioned; no product was selected; avoid building a complicated custom implementation if an existing tool solves the business problem.
- **Change.** A short evaluation against the built-in matrix (C-13); no integration in this iteration.

### C-22. A walkthrough that never covers the application

- **Asked (20:10–20:23, 26:29–27:12).** The walkthrough text must not obstruct the application; each stage should be easy to inspect.
- **Change.** The walkthrough bubble never covers the highlighted element and can be minimised; the chapters follow the new workflow, roles and words.

## 6. Delivery Plan

| Checkpoint | Date | Expected to show |
|---|---|---|
| CP1 | Wed 14 Oct 2026 | Business terminology (C-01); exception queue separating unverified text (C-02, first part); decision checks corrected (C-10); off-domain demonstration bid removed (C-11); dispatch no longer waits for go (C-06, backend) |
| CP2 | Fri 16 Oct 2026 | Bid summary and routing (C-05); assessment before go/no-go end to end (C-06); product-manager and design-engineer roles (C-07); explicit ownership (C-08); sign-in with roles (C-09); extraction snapshot and correction origins (C-04); extended unit responses (C-12) |
| Target | Mon 19 Oct 2026 | Interactive compliance matrix with clickable sources (C-13, C-14); three-pane controls (C-15); history and activity log (C-16); questions and comments (C-17); stronger anchoring with coverage figures (C-03); independent validation RFP (C-11); walkthrough and documents updated (C-22) |

Priority 3 items (C-18 to C-21) are investigated as time allows and do not block the target.

## 7. Open Questions (Needs confirmation)

| # | Question | For |
|---|---|---|
| 1 | Exact document types beyond Main RFP, Addendum, Clarification / Q&A, Change request | Zensar point of contact |
| 2 | Whether the visible bid ID changes from `OPP-0001` | Zensar point of contact |
| 3 | Settled (project-team decision, 13 Oct 2026): the bid manager makes the final go/no-go call; no separate approver role | — |
| 4 | The default validation sequence inside a unit (product manager validates the design engineer's response) | Zensar point of contact |
| 5 | Which public switchgear or substation RFP serves as the independent validation case | Zensar point of contact |
| 6 | Sign-in for a pilot: enterprise single sign-on or an internal role model | Zensar point of contact |
| 7 | Priority of Word and Excel documents | Zensar point of contact |

## 8. What Does Not Change

- The modular architecture and the module boundaries; the model gateway with frozen answers; the append-only audit log.
- Traceability to page and lines as the centre of the product; the three screens.
- Agents propose and named people decide; requirement identification never falls back to pattern matching.
- Change handling as a delta against the working baseline.
- API paths and stored identifiers, in this iteration (labels change, contracts do not, unless a change above says so).
