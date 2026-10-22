# Layer 0: Changes Requested in the Latest Review (Iteration 4)

Status: **Expected (written direction)** for what was asked; **Proposed (inferred design)** for how the build answers it. Each change is marked **Built** (in the code on 21 Oct 2026 and checked), **In progress** or **Later** (registered, not started). Numbers from the demonstration are **illustrative**: the unit answers behind them are placeholder responses written for the demonstration, not Flex positions. Written 21 Oct 2026.

## 1. Purpose, Who This Is For, and Sources

**Purpose.** This document registers the changes raised in the latest review (written notes received on 21 Oct 2026). For each change it says what was asked, what the system did before, what it does now and how the result is checked. It also describes the two demonstration scenarios, the known limits of the demonstration, the requests kept for later and the points that still need confirmation. The numbering continues from [changes-iteration3.md](changes-iteration3.md) (C-23 to C-34), so this register starts at C-35.

**Who this is for.** The Zensar point of contact, who reviews the direction and presents the demonstration, and the Flex team who may see it. The text avoids internal terms; where a stored value matters, it is named once in brackets.

**Sources.**
- The latest review and its written notes (received on 21 Oct 2026) (the direction this document registers).
- The code and the demonstration database as of 21 Oct 2026, including the go/no-go criteria (`data/knowledge_base/go_no_go.json`) and the workflow configuration (`data/knowledge_base/workflow.json`).
- The synthetic RFP RC-1 "Grid to Chip" (`data/RFP/samples/RC-1_Grid-to-Chip_RFP_Synthetic.docx`) and the public Syracuse switchgear RFP.
- [changes.md](changes.md) (C-01 to C-22), [changes-iteration3.md](changes-iteration3.md) (C-23 to C-34) and [technical-architecture.md](technical-architecture.md) sections 16 and 17.

**How it relates to the other documents.** The changes of iterations 2 and 3 that are still open continue. This document supersedes these earlier rules:

| Earlier rule | Replaced by |
|---|---|
| Four measures on the assessment panel: domain alignment, product-evidence coverage, specialist-review progress (counted per item) and preliminary feasibility (changes-iteration3 section 2 and C-23) | Three measures: technical requirement match, reviewed by design engineers, specialist review progress (counted per requirement); preliminary feasibility removed (C-38, C-39) |
| Domain alignment counts technical requirements and standards or regulatory compliance items together (iteration-3 build) | The percentage counts technical requirements only; standards and regulatory items are listed beside it (C-38) |
| Open question 10 of changes-iteration3: the preliminary-feasibility formula and its weights | Closed: the measure is no longer shown (C-39) |
| The bid manager accepts, rejects or changes the system's product matches (iteration-2 build) | The unit's designer / engineer does; the bid manager routes requirements to teams (C-41) |
| The bid manager approves the high-level compliance position on the Assessment step (C-24) | On the Bid decision page, once validated unit answers exist (C-41) |
| Each unit gives one estimated completion date (C-24) | The date plus five delivery factors; the bid manager accepts the teams' estimates and sets no date of their own (C-42) |
| Compliance is Fully compliant, Partially compliant or Non-compliant (changes.md C-12) | Four outcomes: Compliant, Partially compliant, Compliant with changes, Non-compliant (C-43) |
| A matched product shown per requirement on screens and in exports | A proposed solution per unit and solution area, with products as examples (C-40) |
| Step name "Assessment" (changes-iteration3 C-30) | "Assessment Summary" (C-36) |

## 2. Summary

Six themes run through the request:

1. **Cloud and power focus.** The demonstration uses RFPs from the cloud and power infrastructure domain: a synthetic 800 V "Grid to Chip" RFP covering a whole AI campus, and the public Syracuse switchgear RFP viewed through its power electronics requirements (C-35, C-37).
2. **A clear technical assessment.** The Assessment Summary shows three separate measures, each over technical requirements only; legal, commercial, schedule and standards items do not change the percentage (C-36, C-38, C-39). The matching assesses the complete solution a unit offers, not one product or part number per requirement (C-40).
3. **Clear roles.** The bid manager judges business relevance and routes the work; the units' designers and engineers confirm or correct the technical match and answer the technical requirements; the units' managers give delivery feasibility (people, skills, manufacturing capacity, materials, cost). The bid manager uses the teams' estimates and does not set the timeline (C-41, C-42).
4. **Compliance outcomes a customer recognises.** Compliant, Partially compliant, Compliant with changes (a deviation from the requested specification) and Non-compliant; the reviewed outcomes feed the go/no-go (C-43).
5. **Plain business terms.** Labels are understandable without the team explaining them (C-44).
6. **A standalone demonstration.** One HTML file, with no login and no live system, that the Zensar point of contact can open and navigate alone, delivered together with the corrected screens (C-45, C-46).

The three measures of the Assessment Summary answer different questions and are kept apart:

| Measure | Question it answers | Who produces it | It is not |
|---|---|---|---|
| **Technical requirement match** | For how many of the bid's technical requirements has the system found a solution from a participating unit? | The system (matching against the Flex catalog and unit domains) | A compliance answer or a chance of winning |
| **Reviewed by design engineers** | For how many technical requirements has the responsible unit's designer / engineer answered and the unit manager validated the answer? Shown as "n of N reviewed: x confirmed, y corrected" | The units' designers / engineers and unit managers | A quality score: "corrected" only means the engineer changed something |
| **Specialist review progress** | Of the requirements sent to the units, how many have all their answers validated? | The units, counted by the system | A measure of how good the answers are |

Each measure is a count of requirements and opens the requirements behind it. None is a probability.

The four compliance outcomes, used by every unit answer, the compliance matrix, the exports and the go/no-go:

| Outcome | Meaning | What the answer must include |
|---|---|---|
| **Compliant** | The requirement is met as written | How it is met |
| **Partially compliant** | Part of the requirement is met | What is not met and why |
| **Compliant with changes** | The requirement is met, but with a deviation from the requested specification (for example a different rating or a different arrangement that achieves the purpose) | The reason and the proposed change |
| **Non-compliant** | The requirement cannot be met | What is not met and why |

"Non-compliant" was kept in addition to the three outcomes named in the request, because a "cannot be met" answer is still needed, for example for a capability gap.

## 3. Revised Target Workflow (revision 5)

Expected (written direction) for the roles; the detailed sequence is the **Proposed (inferred design)** default, built on 21 Oct 2026.

| # | Stage | Owner | What happens |
|---|---|---|---|
| 1 | Intake and reading | System | The RFP is read into source-backed requirements and frozen automatically (unchanged from C-27). The system proposes a solution from the units for each technical requirement |
| 2 | Assessment Summary | Bid manager | Read what the customer wants and the three measures; judge business relevance. No approval of technical requirements here |
| 3 | Participation and routing | Bid manager | Record which units take part, route requirements to teams (changing the unit only, not the solution), record capability gaps with a reason, and send for assessment |
| 4 | Technical review | Unit designers / engineers | Confirm, reject or correct the proposed solution for their unit's technical requirements, and answer each with one of the four outcomes |
| 5 | Unit review and delivery feasibility | Unit manager | Answer the unit's non-technical requirements; validate the unit's technical answers; give the unit's estimated completion date and the five delivery factors (people, skills, manufacturing capacity, materials, cost), each "no constraint" or a constraint with a note |
| 6 | Consolidation | Bid manager | Validate the units' non-technical answers (so no one validates their own answer); accept the teams' estimates once every unit has given them; approve the compliance position on the Bid decision page |
| 7 | Go / no-go | Bid manager | Record the final call, reading the counts of the four outcomes and the teams' delivery feasibility |
| — | Changes | Bid manager and specialists | Customer changes and reading corrections are versioned on top of the frozen requirements (C-04, unchanged) |

## 4. Change Register

| ID | Change | Status |
|---|---|---|
| C-35 | Focus on cloud and power infrastructure; test and demonstrate with relevant RFPs | Built |
| C-36 | Headings: "Assessment" becomes **Assessment Summary**; "Domain alignment" becomes **Technical requirement match** | Built (walkthrough screenshots in progress) |
| C-37 | Two demonstration scenarios: the synthetic 800 V Grid-to-Chip RFP and the Syracuse switchgear RFP with its power electronics view | Built |
| C-38 | Technical requirement match over technical requirements only | Built |
| C-39 | Three separate measures, including the assessment reviewed by design engineers | Built |
| C-40 | Matching assesses the complete solution, not one product per requirement | Built |
| C-41 | The bid manager's first stage is business relevance and routing; engineers confirm technical matches | Built (walkthrough screenshots in progress) |
| C-42 | Delivery feasibility from the responsible teams; the bid manager uses their estimates | Built (walkthrough screenshots in progress) |
| C-43 | Compliance outcomes, including Compliant with changes; reviewed outcomes feed the go/no-go | Built (walkthrough screenshots in progress) |
| C-44 | Plain business terms throughout | Built (walkthrough screenshots in progress) |
| C-45 | Standalone HTML demonstration: static data, no login, no live system | In progress (source state built; the file is being produced) |
| C-46 | Corrected screens and the HTML demonstration delivered together | In progress |
| C-47 | Excel upload beside the compliance matrix export | Later |
| C-48 | Reassessment after an upload | Later |
| C-49 | Dependencies between teams on one requirement | Later |
| C-50 | Enterprise identity and access management for production | Later |
| C-51 | Evaluation of established workflow frameworks | Later |

## 5. Changes in Detail

Each change lists what was asked, what the system did before, what it does now and how it is checked.

### C-35. Cloud and power focus

- **Asked.** Focus the solution on cloud and power infrastructure, and test and demonstrate it with RFPs from that domain.
- **Before.** The demonstration bids were two public switchgear RFPs (Syracuse and Logan City) and a hyperscale sample.
- **Now.** The synthetic Grid-to-Chip RFP (RC-1), which spans the whole chain from the utility connection to the rack, is listed first among the sample RFPs and is the main demonstration bid; Syracuse is listed second (C-37). The units in the matching are those of the power and cooling portfolio and the in-house cloud unit.
- **Checked by.** A fresh demonstration database contains both bids; the model-change guard finds no missing frozen answer for RC-1 (it reads and matches offline, with no model key).

### C-36. Assessment Summary and Technical requirement match

- **Asked.** Rename the "Assessment" heading to **Assessment Summary** and "Domain alignment" to **Technical requirement match**.
- **Before.** The step, page heading and panel said "Assessment"; the first measure said "Domain alignment".
- **Now.** The step bar, page heading, panel and walkthrough say Assessment Summary; the first measure is Technical requirement match. Stored values and API paths are unchanged.
- **Checked by.** No screen, message or export shows the old words.

### C-37. Two demonstration scenarios

- **Asked.** Demonstrate two scenarios: the synthetic 800 V Grid-to-Chip RFP, and the Syracuse switchgear procurement RFP focused on its power electronics requirements.
- **Before.** The synthetic RFP was available but had not been read, matched or loaded; Syracuse was shown in full.
- **Now.** Both scenarios are loaded; section 6 describes them. RC-1 is read from its Word file (tables included, each requirement keeping its RFP identifier such as L2.04), matched, and taken through the complete workflow. Syracuse offers a saved view, **Power electronics requirements (Crown, EP², Anord Mardix)**, that opens Requirement Traceability filtered to the technical requirements of those three units.
- **Checked by.** An independent coverage check found every one of the 179 requirement identifiers of RC-1 in the register; three fresh demonstration databases gave the same end state; the Syracuse view opens the filtered list.

### C-38. Technical requirement match over technical requirements only

- **Asked.** Calculate the technical match percentage over technical requirements only; legal, commercial, schedule and other non-technical items are not in the denominator.
- **Before.** The measure counted technical requirements and standards or regulatory compliance items together, so, for example, a code-compliance clause lowered or raised the percentage.
- **Now.** Only requirements of the category *technical* are counted. Standards and regulatory items are listed beside the measure as "Standards and regulatory items (not in the percentage)". The evidence gaps use the same technical requirements: technical requirements with no unit's proposed solution, without reviewed product evidence, that need an owner, or with a validated non-compliant answer, plus text that needs a source check. Standards items are still sent to the units' engineers for an answer; only the percentage leaves them out.
- **Checked by.** An automated test adds a legal, a commercial and a schedule item to a bid and confirms that the percentage does not change.
- **Open.** Whether conformance to a standard (for example IEEE C37.20.2) should count as technical (open question 1).

### C-39. Three separate measures

- **Asked.** Show three clearly separate measures: the system-generated technical requirement match; the assessment reviewed by design engineers (in place of "product-evidence coverage"); and specialist review progress.
- **Before.** Four measures: domain alignment, product-evidence coverage (citations from the knowledge base), specialist-review progress over every item sent, and a preliminary feasibility score built from the others.
- **Now.** The three measures of section 2.
  - **Technical requirement match**: technical requirements with a solution from a participating unit. A requirement routed to a unit whose engineer has not yet set the solution does not count.
  - **Reviewed by design engineers**: a technical requirement counts once every responsible unit has answered it and the answer is validated. It is "confirmed" when the engineer kept the proposed solution and answered Compliant, and "corrected" when the engineer named another solution or answered Partially compliant, Compliant with changes or Non-compliant. The bid desk is not a specialist, so its items do not count here.
  - **Specialist review progress**: requirements (not individual unit items) sent to the units, and how many of them have all their answers validated.
  - Preliminary feasibility is removed from the panel and from the go/no-go criteria; the Bid decision reads the reviewed outcomes (C-43) and the teams' feasibility (C-42) instead. The product-evidence gap remains in the gap list.
- **Checked by.** Automated tests for the three counts and the confirmed / corrected split; every count opens the requirements it counts.

### C-40. The complete solution, not one product per requirement

- **Asked.** Matching should assess the complete solution a unit offers, not map one requirement to one product or part number.
- **Before.** Requirement Traceability, My work and the compliance matrix showed a matched product per requirement.
- **Now.** Screens and exports show a **Proposed solution: unit · solution area**, one line per unit, for example "Crown Technical Systems · Arc-resistant metal-clad MV switchgear". Up to three published models of that area are shown as examples, not as the answer; areas with no published models show none. A requirement routed to a unit before its engineer has chosen reads "solution to be set by the unit's designer / engineer". The export column "Product" is now "Proposed solution". The system's matching and the stored data are unchanged.
- **Checked by.** An automated test confirms that Requirement Traceability, My work, the compliance matrix and both exports never show a catalog identifier, while the hand-off to the units keeps it.
- **Open.** Whether the "solution area" should be the product family (built) or a layer of the grid-to-chip chain; My work no longer has a free-text product field (open question 4).

### C-41. The bid manager's first stage: business relevance and routing

- **Asked.** In the first stage the bid manager reviews business relevance and routes the work to the teams. The bid manager does not approve technical requirements there.
- **Before.** The bid manager accepted, rejected or changed the system's matches, and the Assessment step offered "Approve compliance position" before any unit had answered.
- **Now.**
  - On the Assessment Summary the bid manager records participation, routes requirements to teams and sends for assessment. Routing changes the unit only: a new unit's engineer then sets the solution.
  - Accepting, rejecting or correcting a technical match belongs to the designer / engineer of the matched unit. Each correction carries its reason as a comment. A rejected match returns to the bid manager to route again or to record as a capability gap.
  - "Approve compliance position" moves to the Bid decision page and appears once at least one validated unit answer exists. The server refuses it before then.
  - Validation follows the workflow configuration: the unit manager validates the unit's technical answers; the bid manager validates the non-technical answers the unit managers give.
- **Checked by.** An automated test confirms the server refuses the bid manager's attempt to accept a technical match, accepts the routing, and refuses the compliance approval until a validated answer exists.

### C-42. Delivery feasibility from the responsible teams

- **Asked.** Delivery feasibility comes from the responsible teams, considering people, skills, manufacturing capacity, materials and cost. The bid manager uses their inputs and does not set the timeline. No full resource planning.
- **Before.** Each unit manager entered one estimated completion date; nothing covered people, skills, capacity, materials or cost.
- **Now.**
  - In My work the unit manager gives the unit's estimated completion date and the five **delivery factors**, each "no constraint" or "constraint" with a note explaining it.
  - The engineers' technical feasibility is their compliance answers (C-43).
  - The Assessment Summary shows "Delivery feasibility from the teams": each unit's estimate and factors, the constraints, the latest estimate and the planned submission date. The bid manager can only **accept the teams' estimates**, and only once every participating unit has given its date and all five factors. The bid manager keeps the RFP due date and the consolidation time, but has no date of their own for the units' work. A changed estimate or factor reopens the acceptance.
  - The go/no-go criterion is now "Schedule and delivery feasibility": the dates decide whether it is met, and the constraints the teams report are listed with it.
- **Checked by.** An automated test confirms that a constraint without a note is refused, that acceptance is refused until every unit has given its date and five factors, and that a changed factor reopens it.

### C-43. Compliance outcomes

- **Asked.** Use the outcomes Compliant, Partially compliant and Compliant with changes (a deviation from the requested specification); reviewed outcomes feed the go/no-go.
- **Before.** Answers were Fully compliant, Partially compliant or Non-compliant, with no outcome for a deviation.
- **Now.**
  - The four outcomes of section 2 are used in My work, the compliance matrix, the Bid decision, both exports and the hand-off. The field "Workaround" is now "Proposed change"; it is required for Compliant with changes, together with the reason.
  - The Bid decision shows **Reviewed compliance outcomes**: the four counts, each opening the requirements behind it.
  - The go/no-go compliance criterion counts each outcome separately. Compliant with changes counts like Partially compliant toward the threshold, and a recorded capability gap counts as Non-compliant. The threshold (80%) is a placeholder to be agreed.
- **Checked by.** An automated test confirms that Compliant with changes is refused without a reason and a proposed change, and that the go/no-go counts the four outcomes.

### C-44. Plain business terms

- **Asked.** Use plain business terms throughout; labels must be understandable without the team explaining them.
- **Before.** Internal words remained on screens, for example domain alignment, product evidence, offering type, exception queue, baseline and the stored bid statuses.
- **Now.** One list of visible labels is used on every screen and in messages and exports. Examples: offering type becomes **Type of offer**; exception queue becomes **Needs a source check**; baseline becomes **Frozen version**; bid statuses read New, Reading the RFP, In review, Requirements frozen, Sent to units, Go, No-go and Submitted. Stored values and API paths are unchanged.
- **Checked by.** A search of the screens leaves the old words only in internal identifiers; the walkthrough text is updated. New walkthrough screenshots are in progress.

### C-45. Standalone HTML demonstration

- **Asked.** A standalone HTML demonstration with static data, no login and no live system, that the Zensar point of contact can navigate alone; optionally a toggle for explanatory guidance (not finalised).
- **Before.** The demonstration needed the API, the web server and a sign-in.
- **Now (in progress).**
  - The source state is built: the complete workflow has been run on RC-1 as the demonstration accounts, with every approval recorded (section 6.1).
  - The file is being produced from that state: one file with all its scripts and styles inside, the data and page images embedded, no network use, opened by double-click. It shows the last view of the RC-1 bid: the bids list, the RFP pages with highlighted sources, Requirement Traceability with its three panes, the Assessment Summary, My work for each role, the compliance matrix, the Bid decision and the activity log.
  - It is read-only: a role picker replaces the sign-in and no actions are offered. A "Show guidance" switch shows short notes per screen. Syracuse remains a scenario of the live system only.
- **Checked by (planned).** The file opens with no network; every screen matches the live screens at desktop (1440 px) and phone (390 px) widths.
- **Open.** The guidance toggle and its wording (open question 3).

### C-46. Delivered together

- **Asked.** Deliver the corrected screens and the HTML demonstration together, on 21 Oct 2026 before the morning meeting.
- **Now (in progress).** The corrected screens (C-35 to C-44) are built. The walkthrough and its screenshots are being updated, and the HTML file is produced last, from the final state, so that it shows exactly what the live system shows.

## 6. The Two Demonstration Scenarios

### 6.1 RC-1 "Grid to Chip" (synthetic)

**The RFP.** Written for the proof of concept: a 120 MW AI training campus bought in six lots, from the utility connection and 800 V DC power to the racks, liquid cooling and the compute systems. A Word file of about 6,400 words, 19 tables and 3 images; requirement identifiers by lot (for example L2.04).

**The run.** The whole workflow of section 3 has been run on this RFP as the demonstration accounts, each step by the role allowed to take it. All unit answers are **illustrative placeholder responses**, marked as such in their text, written to show every outcome; they are not Flex positions. The figures (21 Oct 2026, illustrative):

| Step | Result |
|---|---|
| Reading | 207 statements read and grouped into 115 requirements (36 groups) after corrections; all 179 RFP requirement identifiers covered |
| Corrections | 23, each with a reason: one missed sentence added, five texts cut at a page break completed (their split-off tails excluded), categories changed (for example evaluation rules moved to the bid desk, warranty moved to commercial) |
| Technical review | The units' engineers confirmed or corrected the proposed solutions, each correction with its reason |
| Units taking part | Seven: Flex Power Modules, Anord Mardix, Crown Technical Systems, EP², JetCool, Cloud, and Flex Design, Engineering and Manufacturing Services (test services). EPC Power is not offered while its acquisition is pending |
| Capability gaps | 18, recorded with a reason (for example the 800 V DC power blocks and campus storage, the substation above 100 kV, standby generation, the heat-rejection plant and the cluster software) |
| Answers | 316 of 316 validated; none needing an owner; no open question. One answer was returned with a question and answered again |
| Assessment Summary | Technical requirement match 38 of 61 (the system's own proposals); reviewed by design engineers 44 of 61; specialist review progress 80 of 80 |
| Outcomes | Per product requirement: 23 Compliant, 19 Partially compliant, 6 Compliant with changes, 18 Non-compliant (all 18 are capability gaps). Per unit answer: 223, 45, 29 and 19 |
| Delivery feasibility | Every unit gave its estimate and the five factors, with constraints and their mitigations; planned submission 25 Nov 2026 against an RFP due date of 1 Dec 2026 (a placeholder derived from the RFP's schedule chart); the bid manager accepted the teams' estimates |
| Decision | Compliance position approved; go/no-go recorded as **Go** with every criterion judged. The compliance criterion is below the placeholder threshold (73% against 80%, with the capability gaps counted as non-compliant); the bid manager judged it met with a note naming the gaps and the scope offered |
| Response | Compliance matrix and a first-draft response outline generated |

### 6.2 Syracuse switchgear RFP (power electronics view)

**The RFP.** The public Syracuse Regional Airport Authority RFP 2023-20 for switchgear procurement (101 pages; about 820 line items grouped into about 310 requirements, each anchored to its page and lines).

**The view.** The saved view **Power electronics requirements (Crown, EP², Anord Mardix)** opens Requirement Traceability filtered to the technical requirements matched to those three units. The rest of the bid is shown as before. This scenario is part of the live system only, not of the HTML file.

## 7. Known Limits of the Demonstration

- **Corrections stay on one page.** The corrected texts of the requirements cut at a page break (for example L3.11 and CT-02) are complete, but their quoted source and highlight still end at the page break; the continuation lines on the next page are not highlighted. A source spanning pages would need a change to how corrections are stored.
- **Images in Word files are not read.** The images of RC-1 (a diagram of the six lots and a schedule chart) are not part of the reading; the coverage check found every requirement identifier in the text.
- **The response outline is a first draft** from one model pass. Before it reaches a customer the bid manager would edit it: the executive summary is written from the opening requirements and overstates compliance; the technical chapter does not name the capability gaps (the outline lists them under "To add or confirm").
- **Placeholder data.** All unit answers, feasibility notes and the 80% threshold are illustrative.
- **Demonstration accounts** keep names of the form "<unit> Product Manager", while their role is shown as Unit manager. The activity log of the scripted run shows its steps within seconds of each other.
- **The HTML file is read-only.** It shows the final state; changing an answer or a decision needs the live system.

## 8. Later (registered, not started)

Expected (written direction). These are registered for a later iteration; nothing is built for them yet.

| ID | Ask | Note for when it starts |
|---|---|---|
| C-47 | Excel upload beside the compliance matrix export: export, share with people without access, collect and consolidate, upload the reviewed sheet | The export columns become the import format; each row keeps its assignment identifier |
| C-48 | Reassessment after an upload: reviewed responses update the affected assessments and the workflow continues; until then the recorded status stays | Follows the same path as a unit answer (history, validation) |
| C-49 | Dependencies between teams: some requirements need input or approval from several teams before the assessment is final | Today each unit's answer is judged alone; this needs an "all of" rule per requirement |
| C-50 | Enterprise identity and access management for production | The current simple signed-token sign-in stays for the proof of concept |
| C-51 | Evaluate established workflow frameworks (cloud or open source) that can be configured and integrated | Guidance only; no replacement of the current workflow now |

## 9. Open Questions (Needs confirmation)

| # | Question | Built default | For |
|---|---|---|---|
| 1 | Should conformance to a standard (for example IEEE C37.20.2) count as a technical requirement in the technical requirement match? | No: standards and regulatory items are listed beside the measure, not counted | Zensar point of contact |
| 2 | Which Syracuse requirements make up the power electronics list? | The technical requirements of Crown Technical Systems, EP² and Anord Mardix | Zensar point of contact |
| 3 | Is a guidance toggle wanted in the HTML demonstration, and what should it say? | A "Show guidance" switch with short notes per screen | Zensar point of contact |
| 4 | Is the "solution area" the product family (built) or a layer of the grid-to-chip chain, and may My work drop the free-text product field? | Product family; the field is dropped | Zensar point of contact |
| 5 | Should Compliant with changes count like Partially compliant toward the compliance threshold, and what is the threshold? | Counts like Partially compliant; 80% placeholder | Zensar point of contact |

## 10. What Does Not Change

- The modular architecture; the model gateway with frozen answers, so the demonstration runs offline; the append-only audit log.
- Traceability to page and lines as the centre of the product; the three panes.
- The automatic freeze of the requirements, the reading snapshot and versioned corrections and customer changes (C-04, C-27).
- Agents propose and named people decide; the bid manager makes the final go/no-go call.
- The system's matching answers, stored values, table names, identifiers and API paths (only visible labels change).
- Simple signed-token sign-in and role-based permissions (C-09, C-26).
