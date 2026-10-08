# Problem Mapping

## Purpose, who this is for, and how to read an entry

**Purpose.** This document lists, one entry at a time, the problems that Layer 0 is meant to solve (Part A) and the problems found in the current proof of concept and project (Part B). Each entry explains the problem first, then the expected solution. Layer 0 is the name of the project and system. A PoC (proof of concept: a small build that tests whether an idea works; it is not a product) is the current build.

**What Layer 0 is for.** Layer 0 is a PoC for SpinCo, the existing Flex business being spun off as Axiom Solutions. Its intended purpose is to help the business manage an incoming bid opportunity (a request that the business considers answering), from the moment a request for proposal (RFP: the customer's formal document describing what it wants to buy and asking suppliers how they would supply it and at what price) arrives until the final bid response is assembled. It should help understand the RFP; determine which business units need to take part; support a human go/no-go decision; set up the workflow for that opportunity; break the RFP into requirements and work packages owned by the right teams; track each team's response; and bring the responses together into a final response that traces back to every original requirement. This workflow is the business direction described in the review meetings (22 Sep and 5 Oct 2026) and is used here as the working baseline. It has not been formally signed off, and no existing build implements it end to end.

**Who this is for.** Developers who have just joined the project and have no electrical-engineering, Flex or bid-management background. Technical terms are explained where they first appear. For the project itself see [project-overview.md](project-overview.md); for company and domain background see [business-and-domain-background.md](business-and-domain-background.md); for how the system is built see [architecture-overview.md](architecture-overview.md).

**Scope.** Problems, their evidence and the outcomes expected. Implementation detail (field schemas, interface lists, configuration switches, commands) is out of scope here and belongs to the architecture material.

**Identifiers.** The identifiers PM-001 to PM-017 and PM-101 to PM-111 were created for documentation traceability only. PM-015, PM-016 and PM-017 were added when the workflow became the working baseline. The older written sources number their own gaps as "GAP 1-4" and "GAP 1-6", and those two lists disagree with each other.

**How to read an entry.** Every entry has eight parts in the same order: Problem; Context and current behavior; Evidence or symptoms; Impact; Cause; Expected solution; Success criteria; Dependencies and constraints.

- **Current state** describes what exists or happens today. **Expected (review meetings)** marks an expectation stated in the review meetings. **Proposed (inferred design)** marks a design idea inferred from the sources; it is a proposal, never a fact about the system.
- The review meetings are not evidence that anything is built. Every documented defect, limitation and missing integration is kept in the entries.
- **Needs confirmation** marks anything no source settles. Where no cause is supported the entry says "Cause not confirmed", and any guess is labelled a hypothesis.
- Each Part A entry states which workflow step it affects (steps 1 to 7 are listed in the next section). Part B entries state the step that the defect blocks or weakens.
- **Success criteria** are observable acceptance checks. They contain no numeric targets, because none has been agreed or measured. Where measurement on real bids is needed, the entry says so.
- Two abbreviations appear in many titles: **RFP** (see above) and **CPQ** (Configure, Price, Quote: software that lets a salesperson pick options from a fixed menu and get a valid price).
- Value statements (fewer coordination delays, fewer missed hand-offs, fewer unanswered requirements, less rework, faster and more accountable go/no-go decisions, clearer ownership, less time reading RFPs) are hypotheses to be measured. None has been measured, and measuring them needs SpinCo historical bids.
- Some earlier documents quoted results such as a 100% catch rate and a 928% return on investment. Those numbers were retracted. They appear only inside PM-108, as superseded history, and must not be used as results.
- Some documents state test results that contradict each other. PM-102 flags this and does not reconcile it.
- The Syracuse airport switchgear RFP used in the PoC is a real public document used as an illustration. It is not a recorded SpinCo bid.

## How the problems map to the workflow

The intended workflow (status: Intended; not signed off; not implemented end to end) has seven steps plus cross-cutting concerns. The core chain it must preserve is: **Original RFP requirement → breakdown and team assignment → team response → final bid response.**

| Workflow step | Problems that affect it |
|---|---|
| 1. Read and understand the incoming RFP, keeping an exact source reference (document, page, quoted text) for every extracted item | PM-001, PM-003, PM-013; defects in PM-103, PM-107 |
| 2. Determine which business units need to take part | PM-006; input from PM-002 |
| 3. Support a human go/no-go decision | PM-008; inputs from PM-002, PM-009, PM-010, PM-011 |
| 4. Establish the workflow for the opportunity (mandatory and configurable steps) | PM-015 |
| 5. Break the RFP into requirements and work packages assigned to teams | PM-004; PM-002, PM-012; defects in PM-107, PM-111 |
| 6. Track each team's response against its assigned requirements | PM-016; PM-011 |
| 7. Bring the responses together into the final bid response and check that every requirement is answered or explicitly excluded | PM-007, PM-017; PM-012 |
| Cross-cutting: human approval, audit history, clarifications, addenda and change requests | PM-005, PM-013, PM-017; PM-009 (later contract phases); defects in PM-106 |
| Volume pressure on all steps | PM-014 |
| Project and PoC problems that block or weaken the steps above | PM-101 to PM-111 (see Part B for the step each one affects) |

## Problem index

Part A is grouped for prominence. A1 is the core workflow; A2 holds supporting capabilities; A3 holds commitments, capacity and volume problems; Part B holds PoC and project problems.

**A1. Opportunity-management workflow (core)**

| ID | Title |
|---|---|
| PM-006 | [No systematic way to decide which business units should participate](#pm-006-no-systematic-way-to-decide-which-business-units-should-participate) |
| PM-008 | [Go/no-go decisions lack structured evidence and clear accountability](#pm-008-gono-go-decisions-lack-structured-evidence-and-clear-accountability) |
| PM-015 | [No opportunity-specific workflow is set up when a bid goes ahead](#pm-015-no-opportunity-specific-workflow-is-set-up-when-a-bid-goes-ahead) |
| PM-004 | [Requirements are not broken down into team-owned work](#pm-004-requirements-are-not-broken-down-into-team-owned-work) |
| PM-016 | [Team responses are not coordinated or tracked against assigned requirements](#pm-016-team-responses-are-not-coordinated-or-tracked-against-assigned-requirements) |
| PM-017 | [The link from source requirement to assignment, response and final bid is not preserved](#pm-017-the-link-from-source-requirement-to-assignment-response-and-final-bid-is-not-preserved) |
| PM-007 | [No final check that every requirement is answered](#pm-007-no-final-check-that-every-requirement-is-answered) |

**A2. Supporting capabilities**

| ID | Title |
|---|---|
| PM-001 | [Reading and understanding each RFP is manual, slow and unrecorded](#pm-001-reading-and-understanding-each-rfp-is-manual-slow-and-unrecorded) |
| PM-002 | [Existing CPQ cannot decide "configure or engineer", and starts only after a human has read the RFP](#pm-002-existing-cpq-cannot-decide-configure-or-engineer-and-starts-only-after-a-human-has-read-the-rfp) |
| PM-003 | [Requirements are not tied to their exact source, so misses surface after award](#pm-003-requirements-are-not-tied-to-their-exact-source-so-misses-surface-after-award) |
| PM-005 | [Clarifications, addenda and change requests are not captured against requirements](#pm-005-clarifications-addenda-and-change-requests-are-not-captured-against-requirements) |
| PM-012 | [Traceability stops at the RFP (drawings, vendor specs, test reports and email are not linked)](#pm-012-traceability-stops-at-the-rfp-drawings-vendor-specs-test-reports-and-email-are-not-linked) |
| PM-013 | [AI output cannot be trusted without source anchoring, repeatability, human authority and an audit trail](#pm-013-ai-output-cannot-be-trusted-without-source-anchoring-repeatability-human-authority-and-an-audit-trail) |

**A3. Commitments, capacity and volume**

| ID | Title |
|---|---|
| PM-009 | [Specification changes between contract phases are caught late](#pm-009-specification-changes-between-contract-phases-are-caught-late) |
| PM-010 | [Commitments across customers are compared by judgment alone (capacity, specification and timeline)](#pm-010-commitments-across-customers-are-compared-by-judgment-alone-capacity-specification-and-timeline) |
| PM-011 | [Concurrent bids by overlapping teams risk crossed wires; there is no workload view](#pm-011-concurrent-bids-by-overlapping-teams-risk-crossed-wires-there-is-no-workload-view) |
| PM-014 | [Bid volume is growing faster than engineering headcount](#pm-014-bid-volume-is-growing-faster-than-engineering-headcount) |

**Part B: PoC and project problems**

| ID | Title |
|---|---|
| PM-101 | [Layer 0's purpose was framed differently in each iteration, and the working direction is not yet formally signed off](#pm-101-layer-0s-purpose-was-framed-differently-in-each-iteration-and-the-working-direction-is-not-yet-formally-signed-off) |
| PM-102 | [v0.3.0 build status is overstated and several modules are not wired in](#pm-102-v030-build-status-is-overstated-and-several-modules-are-not-wired-in) |
| PM-103 | [Extraction runs on pattern matching (regex) by default; the language-model path is incomplete and untested](#pm-103-extraction-runs-on-pattern-matching-regex-by-default-the-language-model-path-is-incomplete-and-untested) |
| PM-104 | [The v1.1 demo reads no RFP and runs on synthetic, placeholder data](#pm-104-the-v11-demo-reads-no-rfp-and-runs-on-synthetic-placeholder-data) |
| PM-105 | [The expected three-way traceability view is missing](#pm-105-the-expected-three-way-traceability-view-is-missing) |
| PM-106 | [Reviewers cannot edit, split or merge results; first-pass facts are not frozen; there is no immutable audit log](#pm-106-reviewers-cannot-edit-split-or-merge-results-first-pass-facts-are-not-frozen-there-is-no-immutable-audit-log) |
| PM-107 | [Requirement extraction is incomplete (commercial, legal and staffing missed; clause splitting unreliable; no OCR)](#pm-107-requirement-extraction-is-incomplete-commercial-legal-and-staffing-missed-clause-splitting-unreliable-no-ocr) |
| PM-108 | [Value is unproven: metrics were inflated then retracted; the business-case assumption is unmeasured](#pm-108-value-is-unproven-metrics-were-inflated-then-retracted-the-business-case-assumption-is-unmeasured) |
| PM-109 | [The demo cases are illustrative and do not match SpinCo's customer types](#pm-109-the-demo-cases-are-illustrative-and-do-not-match-spincos-customer-types) |
| PM-110 | [Code versions and documents are fragmented and contradictory (no version control)](#pm-110-code-versions-and-documents-are-fragmented-and-contradictory-no-version-control) |
| PM-111 | [Integrations with downstream systems exist only as stubs](#pm-111-integrations-with-downstream-systems-exist-only-as-stubs) |

The worked examples are near the end of the document.

---

# Part A: Business problems Layer 0 addresses

These are problems in how bids are read, decided, assigned, answered and checked, as described by the project documents and the review meetings. Where only the review meetings support a problem, the entry says so.

## A1. Opportunity-management workflow (core)

## PM-006: No systematic way to decide which business units should participate

### Problem
A data-centre RFP can need products from several of the business units that make up SpinCo. Someone must decide whether one, several or all of them take part. There is no systematic way to make that decision. Not every data-centre bid needs every unit, and a bid is sometimes answered by one unit alone.

### Context and current behavior
**Workflow step affected: 2 (determine participation).**

- The review meetings described SpinCo as a group of six companies that each used to target different segments (for example only power electronics, or only cooling) and could bid alone. Selling one power unit to a factory can be a CPQ-style sale; selling to a data centre combines products from several units, so the RFP process, decision-making and time all differ. The companies are coming together, and operating together, for the first time.
- The written sources describe four product pillars (Critical Power, Embedded Power, Thermal Management, Cloud) and several brands (a brand is an acquired company name, such as Anord Mardix, Crown, EP², Flex Power Modules, JetCool, EPC Power (pending) and Cloud). The mapping from brands to business units is inferred until the Form 10 (the US securities filing for the spin-off) is filed.
- "Six companies" (one passage of the meeting record reads "76"), "six product layers" (the grid-to-chip layers L1 to L6) and "four teams" (the v0.3.0 knowledge base uses Critical Power, Embedded Power, Thermal (JetCool) and Cloud) are three different counts. There is no one-to-one mapping between them.
- Back-end systems are fragmented across brands (two ERPs, separate IT).
- Closest existing code: the v0.3.0 scope detection maps product layers to brands and teams. This is a partial precursor only. It detects layers present in a document; it does not decide participation, and it does not record a decision.

### Evidence or symptoms
No current decision process is described in any source. The review meetings expected the first decisions on an RFP's arrival (whether a bid is possible, whether one unit or several should respond, and how to split the requirements) to be taken with the help of a rules-based logic engine. No build contains such an engine (see PM-104). The v0.3.0 scope detection is tuned to medium-voltage electrical and direct-current vocabulary and defects exist in how out-of-scope layers are handled (see PM-102).

### Impact
Not quantified. Hypotheses to measure: fewer coordination delays between units; fewer missed hand-offs (a unit that should have been asked is not). A unit left out of a bid it should join produces an incomplete response; a unit pulled in needlessly adds cost and delay.

### Cause
Newly combined companies with separate histories, systems and bid habits. Cause not confirmed beyond that.

### Expected solution
**Expected (review meetings):** on arrival of an RFP, Layer 0 helps decide which business units must respond, and does not assume every data-centre bid needs every unit.

**Proposed (inferred design):** for each opportunity Layer 0 presents a proposed list of participating units, each with the RFP passages that justify it and an explicit "not needed" state for units judged out of scope. A named person confirms or changes the list, and the confirmation is recorded.

### Success criteria
- For a sample RFP, Layer 0 shows a proposed participation list in which every unit is either "participating" or "not needed", each with the source passages that led to the proposal.
- A person can confirm or change the list, and the change and the person are recorded.
- A single-unit RFP yields a list with one participating unit; a multi-unit RFP yields several. Whether the proposals agree with what experienced staff would decide must be measured on real or historical bids; no target is set here.

### Dependencies and constraints
Needs agreed definitions of the business units and their mapping to brands, pillars, layers and teams (a SpinCo decision). Whether SpinCo bids directly or as a subcontractor, and who owns specification risk, is unknown.

---

## PM-008: Go/no-go decisions lack structured evidence and clear accountability

### Problem
Whether to bid at all is the first commitment decision. The business must judge whether the request fits the standard portfolio, what deviations it introduces, whether capacity or other bids conflict, and which questions remain open. Done by hand, the evidence varies between reviewers and it is often unclear who decided and on what basis.

### Context and current behavior
**Workflow step affected: 3 (support a human go/no-go decision).**

- A deviation is a requirement that conflicts with the standard product offering, such as a custom arc-resistant design that may need engineering-to-order, or a lead time shorter than the standard. The decision is described as "done manually and inconsistently".
- **Scope boundary.** Layer 0 supports the decision; it does not make it. A named person decides, and the decision is recorded. The model has no decision authority. Whether a bid/no-bid output is a Layer 0 deliverable or only decision support is flagged as an ambiguity in the review meetings; the working baseline is support.
- Closest existing code: the v1.1 demo returns BID, HOLD or NO_BID with a confidence, a margin estimate and the deviations found, using fixed rules over synthetic, pre-structured data. No RFP is read (see PM-104). The 22 Sep line (v1.0) can flag a deviation against a past bid for the same customer, shown on one synthetic case. The v0.3.0 line has no go/no-go output.

### Evidence or symptoms
The documents list outcomes, with no measured cases:

- bids won that quietly erode margin because a deviation was not priced in;
- straightforward jobs declined from excess caution;
- inconsistent go/no-go logic between bid reviewers.

The v1.1 margin and lead-time constants are placeholders. The margin appears as 16% in one document and 18% in another, so no figure is quoted.

### Impact
Possible margin loss and lost business. Hypotheses to measure: faster, more consistent and more accountable go/no-go decisions. Not quantified.

### Cause
Stated only as manual, inconsistent decision-making. Deeper cause not confirmed.

### Expected solution
**Expected (review meetings):** after the RFP is understood, Layer 0 helps decide go or no-go.

**Proposed (inferred design):** an evidence pack per opportunity containing scope fit against the portfolio, deviations with their source passages, capacity or portfolio conflicts, open questions, and the proposed participating units (PM-006). A named decision-maker records go, no-go or hold, with a reason. The pack is assembled from the exact source references of step 1, and the record is part of the audit history.

The v1.1 margin estimate conflicts with the earlier "Layer 0 never produces a price" boundary; whether any margin or price figure belongs in Layer 0 is an open scope question (see PM-101).

### Success criteria
- For a sample RFP, the evidence pack lists scope fit, deviations (each linked to its source passage), conflicts and open questions, and states plainly which items could not be assessed.
- The go/no-go outcome is entered by a named person, with a reason and a timestamp, and cannot be entered by the system.
- Two reviewers looking at the same pack see the same evidence. Whether decisions become more consistent must be measured on historical bids; no target is set here.

### Dependencies and constraints
Real standard lead times, margins and a definition of the "standard portfolio" ("Critical Power Products" is used without definition). Depends on PM-001 and PM-003 (anchored extraction) for the evidence. The decision criteria and decision-maker are not defined.

---

## PM-015: No opportunity-specific workflow is set up when a bid goes ahead

### Problem
When a go decision is made, nothing sets up the work for that opportunity: which steps apply, in what order, who is responsible, and which are mandatory or optional. Different customers and product combinations need different workflows, and today each is arranged informally.

### Context and current behavior
**Workflow step affected: 4 (establish the workflow for the opportunity).**

- **Expected (review meetings):** after a go decision, Layer 0 creates the workflow for the opportunity. Some steps are mandatory and some configurable, because the process differs by company, customer type and product mix. The review meetings described this variation as the main challenge.
- No workflow system exists today. The review meetings described the current practice as an assumption: the salesperson reads the RFP for a few days and sends the same document to every team, and each team builds its own response its own way. This is an assumption and Needs confirmation.
- No code line implements workflow creation. v0.3.0 runs one fixed six-stage pipeline with an approve/reject gate after each stage; that is a processing sequence for one document, not a workflow for an opportunity. v0.3.0 routes per layer only (see PM-004). Neither the v1.0 nor the v1.1 line creates workflows.
- The review meetings said Layer 0 is not meant to be a general collaboration platform. Setting up the workflow means defining and tracking steps and ownership, not hosting discussion or document editing.

### Evidence or symptoms
Only the assumption above, raised in the review meetings and not yet checked with SpinCo. There is no documented example of a workflow template for any customer type.

### Impact
Not quantified. Hypotheses to measure: fewer missed hand-offs; clearer ownership. Without a defined workflow, ownership and sequence depend on whoever happens to coordinate.

### Cause
Cause not confirmed. Hypothesis: the units were separate until now and each had its own habits, so no shared template exists.

### Expected solution
**Expected (review meetings):** a workflow created per opportunity, with mandatory steps and configurable steps.

**Proposed (inferred design):** a small set of workflow templates chosen by customer type and product mix (for example, a light template for a single-unit bid and a heavier one for a multi-unit bid), which a person can adjust for the opportunity. The chosen template, the adjustments and the person responsible are recorded.

### Success criteria
- After a go decision on a sample opportunity, a workflow exists that lists its steps, the owner of each step, and which steps are mandatory.
- A single-unit sample and a multi-unit sample produce visibly different workflows.
- A person can change a configurable step; a mandatory step cannot be skipped without a recorded reason.
- Setting up the workflow does not require Layer 0 to host messaging or document editing.

### Dependencies and constraints
Depends on PM-008 (a recorded go decision) and PM-006 (participating units). The templates need input from the business: which steps are mandatory and which configurable.

---

## PM-004: Requirements are not broken down into team-owned work

### Problem
Nobody breaks an RFP into numbered requirements and work packages (a work package is a group of requirements assigned to one team) and assigns each to the right team. The review meetings described the assumption that the whole RFP goes to everyone and each group works out for itself which parts concern it. One requirement may involve several teams, and nothing records that.

### Context and current behavior
**Workflow step affected: 5 (break the RFP into requirements and work packages).**

- **Expected (review meetings):** the system takes an RFP, understands it at a high level, creates requirement IDs (unique numbers), classifies each requirement (the analogy given: database, cloud, developer or QA work) and assigns it to a team. For SpinCo, assignment goes to different business units and teams, and design engineers do the work. A requirement may have sub-requirements and more than one owning team.
- Neither review meeting described the current step-by-step process, volumes, cycle times or roles. The "no workflow" picture is an assumption and Needs confirmation.
- The review meetings raised that CPQ fits only configurable products; data-centre power is often custom or semi-custom, as each cloud provider does much of its own design.
- Closest existing code: v0.3.0 routes per **layer** (not per requirement) to four teams, and the payload adapters that would carry the work are not wired. A requirement registry (a stable REQ number for each clause) exists but is not connected. Split and merge are not built (see PM-102, PM-106). The v0.3.0 automation tiers (`CTO_AUTOMATE`: can be configured from standard options; `ETO_GUIDED`: standard sub-items plus engineering guidance; `ETO_EXCEPTION`: custom, sent to a specialist) show which items could go to standard tools and which need engineering; they are an input to the breakdown, not the breakdown.

### Evidence or symptoms
The assumption raised in the review meetings that there is no workflow or system-based way of working. It has not been checked with SpinCo. The v0.3.0 limitations above are documented.

### Impact
Not quantified. Hypotheses to measure: fewer unanswered requirements at submission; clearer ownership; fewer missed hand-offs. The meetings implied duplicated effort, inconsistent responses and no single view of who answered what.

### Cause
Cause not confirmed.

### Expected solution
**Expected (review meetings):** requirement IDs, classification and assignment to teams, with sub-requirements and multiple owning teams where needed.

**Proposed (inferred design):** the requirement is the main tracked item. It keeps its source reference, its sub-requirements, its owning team or teams, each team's response and the parts of the final response that answer it. A person reviews and can edit, split or merge the proposed breakdown and assignment (see PM-106). Pointers to artefacts held in other systems may be attached (see PM-012).

### Success criteria
- For a sample RFP, every extracted requirement has a unique ID and its source location (document, page, quoted text).
- Every requirement shows at least one owning team or an explicit "unassigned" state; a requirement involving two teams shows both.
- A reviewer can split a requirement into sub-requirements and reassign it, and the change is recorded.
- A team can list the requirements assigned to it.
- Whether the breakdown matches what experienced staff would do must be measured on real or historical bids.

### Dependencies and constraints
Depends on complete extraction (PM-107), exact source anchoring (PM-003), reviewer editing (PM-106), a definition of the teams (PM-006) and the workflow (PM-015). Whether commercial, legal and staffing requirements are included is open.

---

## PM-016: Team responses are not coordinated or tracked against assigned requirements

### Problem
Once requirements are assigned, nothing tracks whether each team has responded, what it said, or whether a response is complete. Coordination depends on email and individual follow-up. There is no view of response status per requirement.

### Context and current behavior
**Workflow step affected: 6 (track each team's response).**

- **Expected (review meetings):** Layer 0 tracks each team's response against its assigned requirements. The meetings mentioned generic estimation tables, with each team filling its own worksheet per requirement ID (duration, resources, hours, description). Whether the response is a narrative, an estimation sheet or a price is open.
- **Scope boundary.** Tracking team work is part of Layer 0. It does not require Layer 0 to be a general-purpose collaboration platform. People write the responses; Layer 0 does not write them autonomously.
- No code line implements response tracking. v0.3.0 stops at a coverage map and manual routing. The v1.0 line has a case-scoped event log, but no per-team response. The v1.1 line has none. The estimation sheets are listed as not built (see PM-102).
- The v1.0 documents also note the lack of a workload view and of tests for simultaneous editing (see PM-011).

### Evidence or symptoms
No failures are described in a source; the meetings stated this as a gap. Documented limitations: no response record, no status, no reminder, no concurrent-editing policy ("last write wins" is the default).

### Impact
Not quantified. Hypotheses to measure: fewer coordination delays; fewer unanswered requirements at submission; clearer ownership.

### Cause
Cause not confirmed. Hypothesis: there was no shared system for the units to work in.

### Expected solution
**Expected (review meetings):** tracking of each team's response per requirement.

**Proposed (inferred design):** each requirement carries per-team response states (for example: not started, in progress, responded, excluded with reason), the response content or a pointer to where it is held, who submitted it and when. A person can see, per opportunity, which requirements and which teams are still outstanding. Responses can be returned for correction and the exchange is kept in the audit history.

### Success criteria
- For a sample opportunity, each requirement shows its owning team or teams and each team's response status.
- A user can list all requirements with no response yet, grouped by team.
- A team response is visibly linked to the requirement it answers, with the author and time.
- If one requirement is assigned to two teams, both responses are shown and a missing one is visible.
- Whether coordination delays fall must be measured on real bids; no target is set here.

### Dependencies and constraints
Depends on PM-004 (assignments with IDs), PM-015 (workflow) and PM-106 (edit history). Integration boundaries with CPQ (Logik.io with Salesforce), costing (aPriori), quoting (QuoteWin) and ERP (SAP, Infor LN) are uncertain (see PM-111). Whether estimation sheets, prices or margins belong in Layer 0 is an open scope question: earlier documents say Layer 0 never produces a price, the meetings mention estimation tables, and v1.1 produced margin estimates on synthetic data.

---

## PM-017: The link from source requirement to assignment, response and final bid is not preserved

### Problem
No place keeps the whole chain: original RFP requirement, then breakdown and team assignment, then team response, then the section of the final bid response that answers it. Without that chain, nobody can show where a requirement came from, who owned it, what they said, and where it was answered.

### Context and current behavior
**Workflow steps affected: 5, 6 and 7, and the cross-cutting audit history.**

- **Expected (review meetings):** three connected views that all connect in the final response: (1) the original RFP, (2) how its requirements were broken up and assigned, (3) how the teams responded.
- Existing pieces cover only fragments. v0.3.0 has clause-to-source links and a coverage map (a list of every clause with what was done to it). Its requirement registry is not connected, its proposal checker is not wired, and routing is per layer. The v1.0 line has a three-panel screen (inbound RFP, past proposal, requirement list) that was never compiled. No code line preserves assignment, response and final-answer links.
- The three-view screen set that the review meetings expected is itself reported missing (see PM-105).
- The traceability chain must survive clarifications, addenda and change requests (see PM-005).

### Evidence or symptoms
The 5 Oct 2026 review saw no such screen. The 22 Sep demonstration lacked the side-by-side screen of an earlier build that had been overwritten. Documented defects: unreliable clause splitting on the full 101-page PDF (PM-107), and a proposal checker that is not connected (PM-102).

### Impact
The central expectation of the review meetings cannot be shown. A disputed commitment cannot be traced to a clause, an owner and an answer. Hypotheses to measure: fewer unanswered requirements; clearer ownership; less rework. Not quantified.

### Cause
Cause not confirmed. Hypotheses: overwritten files without version control (PM-110) and changing framings of Layer 0 (PM-101).

### Expected solution
**Expected (review meetings):** every original requirement traces forward through assignment and team response to the final bid response, and back again.

**Proposed (inferred design):** a requirement record that holds its source reference, its sub-requirements, the participating team or teams, each team's response and the final-response sections that answer it, with views for the RFP, the breakdown and the responses. Each link is created by a person or confirmed by a person, and each is logged.

### Success criteria
- For a sample RFP, selecting any requirement shows its source location, its assignment, each team's response and the final-response section that answers it; selecting a final-response section shows the requirements it answers.
- A requirement with no assignment, no response or no answering section is shown explicitly as such.
- The chain remains correct after a requirement is split, merged, reassigned or changed by an addendum, and the history shows the change.
- A reviewer who did not build the system can follow the chain for one requirement without help.

### Dependencies and constraints
Depends on PM-003, PM-004, PM-016, PM-106 and PM-107. Needs an agreed definition of a requirement and of the final-response structure.

---

## PM-007: No final check that every requirement is answered

### Problem
Before the final bid response is submitted there is no systematic check that every customer requirement, including non-technical ones such as a geography, night-hours support or a team based in the customer's office, has been answered or explicitly excluded.

### Context and current behavior
**Workflow step affected: 7 (bring the responses together and check completeness).**

- **Expected (review meetings):** such requirements also become requirement IDs and trace to the response, with a quality-control step (for example, 25 requirements and 25 answered) before the final response is sent.
- Closest existing code: the v0.3.0 coverage map and proposal checker. The coverage map is connected and tested but its figures are unreliable on the full 101-page PDF (PM-107). The proposal checker, which compares a proposal against the RFP, is built and tested but not wired into the screen (PM-102). Both are limited to technical fields. Neither checks a team response, because none is tracked (PM-016).

### Evidence or symptoms
No failure is described; this is stated as a goal. The documented limitations above apply.

### Impact
A requirement missing from the response is the same failure as in PM-003. Hypothesis to measure: fewer unanswered requirements at submission. Not quantified.

### Cause
Cause not confirmed.

### Expected solution
**Expected (review meetings):** a check of the RFP against the final response so that every requirement is answered.

**Proposed (inferred design):** a completeness check that lists, for every requirement, whether it is answered, excluded with a recorded reason, or open, and blocks sign-off of the final response while any is open unless a named person accepts the gap.

### Success criteria
- For a sample opportunity, the check lists every requirement with one of: answered (with the answering section), excluded (with reason and person), or open.
- A requirement that was never extracted cannot silently pass: the check states how complete the extraction is, or flags when it cannot.
- Open requirements are visible at the point of sign-off, and acceptance of a gap is recorded with a name.

### Dependencies and constraints
Depends on PM-004 (IDs), PM-005 (addenda), PM-016 (responses) and PM-017 (traceability).

---

## A2. Supporting capabilities

## PM-001: Reading and understanding each RFP is manual, slow and unrecorded

### Problem
When a customer sends an RFP, experienced application engineers (engineers who match customer needs to products) read it by hand. They decide, line by line, which parts are standard products and which need custom engineering. The documents describe this decision as made "constantly, by a handful of experienced people, with no system behind it".

### Context and current behavior
**Workflow step affected: 1 (read and understand the RFP); it also feeds steps 3 and 5.**

The process described by the documents:

1. A customer sends an RFP. Customers include hyperscalers (very large cloud operators), data-centre developers, utilities and public bodies. An RFP can exceed 100 pages of prose, tables, drawings, standards lists, legal and commercial terms.
2. An application engineer reads it. The documents estimate 5-10 days for a complex bid; another says 2-5 days of manual extraction. Neither is measured.
3. For each line the engineer decides: a standard product that can be configured, or custom engineering.
4. Standard parts go to configuration software and pricing. Custom parts go to design engineers.
5. Team responses are gathered into one proposal and sent.

**Expected (review meetings):** every item extracted from the RFP keeps an exact source reference (document, page and quoted text). Closest existing code: the v0.3.0 pipeline reads a real RFP, with regex (fixed text-matching patterns) by default; the language-model path is untested, and clause splitting is unreliable on the full 101-page PDF (PM-103, PM-107).

### Evidence or symptoms
The documents name three consequences. None appears in any financial report:

- **Inconsistent under load.** When engineers are saturated, some bids are read thoroughly and others are skimmed, priced conservatively or declined. No record is kept when a bid is declined because a specialist was busy.
- **Judgment not written down.** The rules for "standard or custom" live in a few people's heads and leave when those people leave.
- **Not auditable.** When an under-scoped bid becomes an expensive field modification, nobody can say which clause was missed or who decided it was standard.

No measured SpinCo data exists for any of this. The 5-10 day figure is an expert estimate, not measured data.

### Impact
Bids are lost, delayed or priced conservatively without anyone recording why, knowledge stays with a few people, and no one is accountable when a clause is missed. Hypothesis to measure: less time spent reading RFPs. Not measured.

### Cause
The documents' explanation is that, until recently, software could not reliably extract engineering requirements from a noisy long specification, so existing tools start only after a human has done that reading. This is a hypothesis supported only by those documents.

### Expected solution
**Expected (review meetings):** Layer 0 reads and understands the incoming RFP as the first step of opportunity management.

**Proposed (inferred design):** a reading step that produces an inspectable list of extracted items, each with document, page and quoted text, and an explicit marker for anything it could not anchor (see PM-003). A person reviews the result. The reading step does not decide go/no-go and does not price.

To test the premise before investing, one document proposes auditing 20-30 historical quote requests across at least two brands, timing each stage (reading, clarification, configuration, costing, approval, issue). This is proposed, not scheduled.

### Success criteria
- For a sample RFP, Layer 0 produces a list of extracted items, each showing document, page and quoted text, and each can be checked against the original.
- Items the system could not read (for example scanned pages) are reported, not silently skipped.
- The time spent reading is measured on real bids before and after, which needs SpinCo historical bids; no target is set here.
- Where the decision-rule from earlier documents is used (reading is worth automating only if it is a large share of the cycle), the share must be measured first.

### Dependencies and constraints
Needs real quote history from SpinCo commercial operations, one nominated business unit and one live RFP for a pilot. The sources treat RFPs, RFQs (requests for quotation) and RFIs (requests for information) differently; see PM-101.

---

## PM-002: Existing CPQ cannot decide "configure or engineer", and starts only after a human has read the RFP

### Problem
CPQ answers the question "which valid combination of options does the customer want, and what does it cost?" It cannot answer the earlier question: whether a line of the bid can be configured from standard options or must be engineered. Every CPQ product assumes a human has already read the RFP and typed in structured requirements.

### Context and current behavior
**Workflow steps affected: input to 3 (go/no-go) and 5 (breakdown and assignment).**

- **A spectrum of how products are made**: MTS (make-to-stock: built before any order exists), ATO (assemble-to-order: assembled from stocked modular parts after the order), CTO (configure-to-order: built from a fixed option menu using rules) and ETO (engineer-to-order: the design is created for each order). CPQ sits at the quoting stage.
- **SpinCo spans both ends.** EP² is labelled "Engineered-to-order" on Flex's product site; Anord Mardix describes custom built modular solutions; EPC Power builds 800 VDC (volts direct current) grid-forming systems, some first-of-kind. Every inbound bid mixes configurable and custom lines.
- **Flex already licenses Logik.io**, a headless configuration engine used with Salesforce. Earlier documents wrongly stated Flex had no CPQ. Which brands it serves, and whether SpinCo keeps it after the spin-off, is not known.
- **Systems are fragmented.** Two ERPs (enterprise resource planning: the system of record for orders and inventory), SAP and Infor LN, run in parallel, and each brand keeps IT autonomy.
- **Where the gap sits.** The path from request to delivery has 12 steps. CPQ covers configure, cost, price, approve, quote document and negotiate (steps 3-8 of that path). The unstructured RFP arriving and the qualify-and-triage step (standard versus custom, scope, complexity) are covered by no vendor product.

### Evidence or symptoms
| Standard CPQ assumes | SpinCo reality |
|---|---|
| A finite option menu | EP² is engineer-to-order with no menu |
| Rules fully determine a valid configuration | EPC Power's first-of-kind topologies have no prior rule |
| One catalogue, one system of record | Two ERPs and brand-level IT |
| Quoting is a sales activity | Quoting is an engineering activity |

Quote churn is the clearest symptom: design, parts list and costing need an engineer even for quotes that may not win. The documents give an illustration of many quote requests with few wins; they say it is an illustration, not SpinCo data. An outside expert review is quoted: where much of the mix is bespoke, "CPQ cannot be a one-size-fits-all automation engine".

### Impact
A single uniform tool either produces wrong quotes for the custom brands or captures no value at the standard brand. An engineer will not sign a quote whose thermal headroom, busbar sizing or short-circuit rating went unchecked.

### Cause
The mix of configurable and custom products inside one company, plus fragmented back-end systems. Whether any single brand already has an internal quoting automation is not known.

### Expected solution
**Proposed (inferred design, from the v0.3.0 documents):** a front layer that sorts each requirement into automation tiers and hands standard lines to the configurator instead of replacing it. The tiers are `CTO_AUTOMATE` (can be configured automatically), `ETO_GUIDED` (standard sub-items plus a basis of design for an engineer) and `ETO_EXCEPTION` (custom; captured and sent to a specialist). The name `ETO_ESCALATE` in one document is an alias for the last tier. The tier is an input to go/no-go (step 3) and to assignment (step 5); it is not itself a pricing or design step.

Earlier documents proposed an "agentic CPQ" that also drafts a design and a price. That framing was marked superseded and is history only. Layer 0 as described in the review meetings does not include autonomous engineering design or pricing engines.

### Success criteria
- For a sample RFP, each requirement shows a tier and the source passage behind it, and a person can override the tier with a recorded reason.
- Any item the system cannot tier is shown as unresolved, not forced into a tier.
- The accuracy of tiering against experienced engineers' judgment must be measured on real or historical bids; no target is set here.

### Dependencies and constraints
- Which brands and lines Logik.io is configured for; whether SpinCo keeps it.
- Real interface contracts for QuoteWin (sales quoting software), SAP / Infor LN and aPriori (a should-cost tool). Integration boundaries are uncertain: what is handed off, what is read back, and whether opportunities are created in a CRM.
- Tier by company is a weak rule: a repeated custom design can later become standard.

---

## PM-003: Requirements are not tied to their exact source, so misses surface after award

### Problem
A critical requirement can sit in an ordinary section, an appendix or a question-and-answer addendum (an official change issued after the RFP is published). If it is missed, nobody can show where each specification came from, so the miss is found only after the contract is won and becomes a change order (a priced post-award change to scope).

### Context and current behavior
**Workflow steps affected: 1 (source references) and 7 (completeness); also cross-cutting.**

The failure sequence described by the documents (illustrative):

1. An RFP of 100-300 pages in mixed formats arrives. A critical line such as "15 kV (kilovolt) switchgear, arc-resistant Type 2B per IEEE C37.20.7" sits in a section, an appendix or an addendum. Switchgear is the assembly of switches and circuit breakers that controls and protects electrical circuits; "arc-resistant Type 2B" is a safety rating for equipment built to contain an internal electrical arc (a short-circuit flash).
2. Engineers read it manually and write notes into a proposal template. There is no permanent record of where each specification came from, no comparison with past bids and no flag for what is new or different.
3. The quote wins.
4. About 12 weeks later post-award engineering finds the mismatch: standard metal-clad switchgear was quoted but the RFP required Type 2B. The item is not in the catalogue, custom design is needed, and the unrecovered cost erodes the margin.

### Evidence or symptoms
- **The Syracuse example is illustrative.** The RFP of the Syracuse Regional Airport Authority (RFP #2023-20) is real and public. The 2024 past bid that missed the requirement, and the cost of the miss, are constructed for the demonstration; the release describes one synthetic case modelled on a real public RFP. Earlier pitch material told the story as a real SpinCo loss; that was incorrect. Whether SpinCo or any brand ever bid on this RFP is not stated (Needs confirmation).
- Figures in one problem statement on the share of bids with post-award mismatches and the margin lost per bid have no stated basis and are not used.
- Questions the business cannot answer today: before award, whether the whole RFP was read and what differs from the past bid; after award, why a requirement was missed; and who reviewed and approved each decision.

### Impact
Margin loss after award, and finger-pointing and litigation risk when a disputed change order cannot be traced to a clause and a decision. The size of the loss at SpinCo is unknown. Hypothesis to measure: less rework from late-discovered requirements.

### Cause
The documents point to manual reading under fatigue, volume and time pressure; to CPQ tools that need already-structured input; and to AI tools that read unstructured text but invent facts, cannot be audited and give different answers on re-runs. How often missed specifications occur at SpinCo: Cause not confirmed.

### Expected solution
**Expected (review meetings):** every extracted item keeps an exact source reference: document, page and quoted text.

**Proposed (inferred design, from the 22 Sep documents):**

1. Read unstructured RFPs.
2. Anchor every extracted specification to its exact source location (page and character position).
3. Mark a value `UNANCHORED` instead of inventing a location when it cannot be found. The three provenance classes are `EXTRACTED` (taken directly from the source), `DERIVED` (computed from extracted values) and `UNANCHORED` (no verified location).
4. Flag deviations against a past bid for the same customer.
5. Keep a permanent record of who extracted, reviewed and approved.

A three-panel screen (RFP, past bid, specifications) and deviation risk levels are proposals, not confirmed solutions. An expert panel ranked source-anchored traceability first.

### Success criteria
- For a sample RFP, every extracted requirement shows document, page and quoted text, and the quote can be found at that place in the original.
- A value that cannot be anchored is shown as `UNANCHORED`, never given an invented location.
- The share of historical change orders that the system would have flagged is measured on historical RFPs with known outcomes. This needs SpinCo data; no target is set here.

### Dependencies and constraints
Historical RFPs, past bids and change-order records from SpinCo. Retrievable past proposals per customer are implied by the comparison requirement.

---

## PM-005: Clarifications, addenda and change requests are not captured against requirements

### Problem
Customers answer clarification questions (Q&A), issue addenda and send change requests after the RFP is published. If those are not tied to the requirements they change, a specification can be missed even after a careful first reading, and the traceability chain goes stale.

### Context and current behavior
**Workflow steps affected: cross-cutting, at every step; most visibly 5 to 7.**

- **Expected (review meetings):** customer answers become new requirement IDs or update existing ones, so that all data and Q&A for an opportunity are kept in one place. Change requests are handled incrementally once the plan is fixed. A change large enough to alter the whole RFP is treated as a new opportunity.
- How change requests are applied incrementally is not defined (flagged as an ambiguity in the review meetings).
- How SpinCo handles addenda today is not stated. The v0.3.0 build does not handle addenda or clarifications. The 22 Sep line has a case-scoped event log but no addenda handling. The "new opportunity" restart case cannot yet be done by any build.
- One document names addenda as a place where critical specifications hide.

### Evidence or symptoms
The earlier problem statement gives an example of a critical specification placed "in Section 4.2, Appendix C, or a Q&A addendum". No actual incident is described.

### Impact
A missed addendum leads to the failure described in PM-003; an unrecorded change leaves teams answering outdated requirements. Hypothesis to measure: less rework from late changes. Not quantified.

### Cause
Cause not confirmed.

### Expected solution
**Expected (review meetings):** addendum, Q&A and change-request text creates or updates requirement IDs inside the same opportunity, and a drastically changed RFP starts as a new opportunity.

**Proposed (inferred design):** each change is attached to the requirements it affects, shown to the owning teams as a changed requirement with its history, and its effect on responses already given is flagged for the owner to review. A person decides whether a change is incremental or large enough to restart.

### Success criteria
- For a sample opportunity with an addendum, the affected requirements show the change, its source location and date, and the previous wording remains visible.
- The owning teams see which of their responses are affected by the change.
- A change that adds a requirement creates a new requirement ID that goes through assignment and response tracking.
- The rule for "incremental" versus "new opportunity" is written down and applied by a named person; the decision is recorded.

### Dependencies and constraints
Needs requirement IDs first (PM-004) and traceability (PM-017).

---

## PM-012: Traceability stops at the RFP (drawings, vendor specs, test reports and email are not linked)

### Problem
A requirement cannot be traced across RFPs, spreadsheets, documents, emails, vendor specifications, CAD files (computer-aided design drawings) and test-equipment reports. Today nothing is read except the RFP itself.

### Context and current behavior
**Workflow steps affected: 5 to 7 (artefacts supporting the assignment, response and final answer). Proposed only.**

- By design, unsupported files are named, given a reason and routed to engineering rather than guessed at. Examples are DWG drawings (an AutoCAD file format) and spreadsheets with macros.
- SpinCo almost certainly already has systems that hold these files: product data management for CAD, a document system, an email archive, a quality system for test reports, an ERP or vendor portal. None has been named.

### Evidence or symptoms
There is zero traceability today into CAD, test reports, vendor specifications or email.

### Impact
The audit chain ends at the RFP, so a specification change that comes from a drawing or vendor sheet is invisible to Layer 0. Not quantified.

### Cause
A deliberate scope choice ("never fabricate, never guess"), not a defect.

### Expected solution
**Proposed (inferred design):** pointer links. For each requirement, store the system name, artefact ID or link and who attached it, instead of building a reader for each file type. Where a read-only lookup exists, the link can be checked; where no integration exists (email is the likely case), a person attaches a reference and the event is logged. One document says this is "a few weeks of wiring"; that is unverified, and another document says it could be "a much larger integration project" depending on whether those systems have interfaces other programs can call. Excluded from the v1.0 pilot exit criteria.

### Success criteria
- For a sample requirement, a person can attach a pointer to an artefact in another system, and the pointer shows the system, the artefact reference and who added it.
- Layer 0 never presents the content of a pointed-to artefact as if it had read it.
- Which systems can be queried read-only is documented for each artefact type.

### Dependencies and constraints
Four answers from SpinCo: where CAD files, vendor specifications, test reports and email live, and whether each can be queried. Depends on the requirement record (PM-004, PM-017).

---

## PM-013: AI output cannot be trusted without source anchoring, repeatability, human authority and an audit trail

### Problem
A large language model (LLM: software that predicts text and can read a long document) can read an unstructured RFP, but it can state things that are not in the source, give different answers on re-runs and leave no audit trail. A bid worth $10M or more cannot rest on that without controls.

### Context and current behavior
**Workflow steps affected: cross-cutting (human approval and accountability, audit history); step 1 most directly.**

- **Expected (review meetings):** it is very hard to trust an LLM because every stage must be re-validated, and a requirement can sit inside a sentence, so the model needs a framework in which to operate to decide what counts as a requirement. The model has no authority to change a result; a person does. Fine-tuning was ruled out as too expensive; the preference was to train the system rather than the model (a set of rules the model uses, rather than RAG: retrieval-augmented generation, giving the model relevant reference text to read).
- The v0.3.0 documents set these rules: the model reads and "does not decide anything that carries liability"; classification, validation and arithmetic are repeatable rules; every value carries provenance; human approval is enforced between stages in code.
- Human accountability and an audit trail are central to every workflow step. The v0.3.0 approvals are stored in an editable database, not an immutable log (PM-106).

### Evidence or symptoms
- A full answer for a custom 15 kV switchgear bid would be checked by an application engineer "within ninety seconds", found wrong, "and the meeting would be over".
- A wrong anchor "looks authoritative and is worse than an absent one".

### Impact
Without these controls an engineer will not sign off and the tool is abandoned. A custom item could be routed into a standard configurator as if it were standard.

### Cause
This is inherent to how language models work. Cause for the current build: not confirmed (see PM-103).

### Expected solution
**Proposed (inferred design, from the documents; not confirmed as the target):**

1. Anchor every value to its source location.
2. Use temperature 0 (a setting that makes output as repeatable as possible) and freeze first-pass facts so re-runs read them instead of re-asking the model.
3. Let humans, not the model, change results, side by side.
4. Keep a set of known-correct examples so a model upgrade cannot silently change answers.
5. Keep an immutable log of every step.

How far the build meets this is in PM-103 and PM-106.

### Success criteria
- Any decision shown by Layer 0 can be followed to its source passage by a person who knows the document.
- Re-running on the same RFP gives the same extracted facts unless a person has changed them.
- Every approval, edit and decision shows who did it and when, and the record cannot be edited by ordinary users.
- A known-answer check exists and is run before any model change is accepted.

### Dependencies and constraints
Which model and where it runs; what the immutable log must contain and who may read it; what "the framework in which the model operates" means.

---

## A3. Commitments, capacity and volume

## PM-009: Specification changes between contract phases are caught late

### Problem
Large commitments, such as a hyperscaler's framework agreement with Phase 1, 2 and 3, change as they proceed: a material is substituted for cost, a thicker part compensates. Someone must catch the change, decide whether it needs an ECN (Engineering Change Notice: a formal record that a design is changing, which triggers engineering review), and decide whether the next phase can go ahead.

### Context and current behavior
**Workflow step affected: cross-cutting change handling after award, and input to step 3 (earlier commitments that a new bid must respect). It sits later than the bid workflow of steps 1 to 7.**

- Deviation types: scope (the customer asked for it), design (supply-chain or design evolution) and conflict (clashes with an existing commitment, for example units already built to the old specification). Each change is rated on technical, supply-chain and field risk.
- Illustration from the synthetic demo data: a supplier-suggested change from copper to aluminium busbar (the thick metal bar that carries current inside switchgear), with a thicker bar to compensate, triggers an ECN and locks Phase 3 until engineering approves. The documents give different reasons for the rating, so the reason is not quoted as fact.
- **Expected (review meetings):** a change request is handled on its own once the plan is fixed, and a change big enough to alter the whole RFP restarts as a new opportunity. No build can do the restart case.
- Closest existing code: the v1.1 execution-stage check (ECN and phase lock), a deterministic rule over synthetic, pre-structured data (PM-104).

### Evidence or symptoms
The document names consequences, with no measured cases: drift not caught until production; ECN requirements found late and expensive; later phases designed against an assumption that stopped being true.

### Impact
Late rework and cost. Hypothesis to measure: less rework from late changes. Not quantified.

### Cause
Missed or informal tracking of changes.

### Expected solution
**Proposed (inferred design):** compare each phase to the committed specification, rate the risk, require an ECN above a severity threshold and lock the next phase until it is resolved. The demo rule ("ECN if any deviation is medium or higher") is an assumption encoded in synthetic data, not a confirmed SpinCo rule.

### Success criteria
- For a sample contract with a changed phase, the change is shown against the committed requirement it affects, with its source.
- A change that needs an ECN is flagged, the next phase shows as blocked, and a named person records the release.
- The ECN trigger is defined by SpinCo, not by the demo constants.

### Dependencies and constraints
The real ECN process at SpinCo is not described anywhere. Needs the committed requirement record (PM-017) and change handling (PM-005).

---

## PM-010: Commitments across customers are compared by judgment alone (capacity, specification and timeline)

### Problem
Several customers' opportunities can land in the same window with different specifications, quantities and deadlines. The business needs to know whether it can serve all of them without a capacity crunch, a specification conflict or a timeline collision, and without damaging a relationship by prioritising the wrong customer. The document calls this the "highest-stakes decision and the one most often made on gut feel".

### Context and current behavior
**Workflow step affected: input to step 3 (go/no-go evidence on capacity or portfolio conflicts).**

- Conflict types: specification incompatibility (different designs cannot share tooling, fixtures and assembly procedures), manufacturing capacity overcommitment and compressed decision timelines.
- Each realistic combination of wins is meant to be compared on capacity, specification, timeline and relationship risk, with escalation to the COO (chief operating officer) if the business is forced to take everything.
- The customer mix is diversifying (utilities, hyperscalers, new AI-infrastructure entrants called neoclouds), so these conflicts increasingly occur together.
- **Expected (review meetings):** the portfolio level sits above the individual bid, showing all bids and how many are being handled.
- Closest existing code: the v1.1 portfolio conflict check, deterministic rules over synthetic data (PM-104).

### Evidence or symptoms
No real incident is described. The demo scenario (a neocloud RFP clashing with a hyperscaler framework and a utility bid) is synthetic and its figures conflict between documents, so none is quoted.

### Impact
Possible capacity shortfall and relationship damage. Not quantified.

### Cause
Comparison by judgment rather than by structured options.

### Expected solution
**Proposed (inferred design):** a feasibility comparison across options with a primary recommendation, presented as evidence for the go/no-go decision (PM-008) and not as a decision. Plant capacity, deadlines and per-customer margins in the demo are placeholders.

### Success criteria
- For a sample set of concurrent opportunities, the comparison shows capacity, specification and timeline conflicts and names the evidence for each.
- The recommendation is presented with its assumptions and a person decides; the decision is recorded.
- Calibration against real historical cases is needed; no target is set here.

### Dependencies and constraints
Real capacity, standard lead times and decision deadlines; historical cases for calibration.

---

## PM-011: Concurrent bids by overlapping teams risk crossed wires; there is no workload view

### Problem
The same two or three engineering teams may work several live RFPs at once. Without separation, one bid's specification, override or edit could leak into another. Managers also cannot see who is working on what, for example which of many open RFPs a team is working on and whether that team is overloaded.

### Context and current behavior
**Workflow steps affected: 3 (capacity evidence) and 6 (tracking responses across opportunities).**

- The v1.0 documents say each unit of state carries a case ID (an identifier for one bid), so two RFPs cannot be confused; this is a property of the data design, not a separate feature. Reading across cases is deliberate, so a correction made by five engineers on five bids can surface as a candidate rule.
- Not provided: a test of concurrent editing; handling of two people editing the same requirement ("last write wins" is the default); a view of all bids and their workload. The three-panel screen works one case at a time and was never compiled.
- **Expected (review meetings):** SpinCo can receive RFPs from many customers at once, and the portfolio view should show all bids and how many are being handled.

### Evidence or symptoms
Whether this happens often enough to matter is unknown: "If rare, concurrent-case isolation is a nice-to-have, not a differentiator". No incident has been reported.

### Impact
Not established. Hypothesis to measure: fewer missed hand-offs and clearer ownership.

### Cause
Cause not confirmed.

### Expected solution
**Proposed (inferred design):** keep all data per opportunity so bids cannot mix, add a workload view across opportunities built from the assignments and response states (PM-004, PM-016), and decide how simultaneous edits to one requirement are handled. The v1.0 roadmap lists a concurrency test and a workload view as unscheduled items.

### Success criteria
- Two sample opportunities handled at the same time show no requirement, edit or override from one appearing in the other.
- A manager can list, per team, the open requirements across all live opportunities.
- A written policy for simultaneous edits exists and is demonstrated.

### Dependencies and constraints
Real frequency and incident data from SpinCo; assignments and response states from PM-004 and PM-016.

---

## PM-014: Bid volume is growing faster than engineering headcount

### Problem
Bid and engineering workload scales with revenue, but the number of application engineers cannot grow as quickly.

### Context and current behavior
**Workflow steps affected: all (volume pressure); most on step 1, where reading is labour-intensive.**

- Flex investor material, as cited by the documents: FY26 revenue of about $6.6 billion, guidance of +65-75% in FY27 and about +80% in FY28. Separation is targeted for the first quarter of calendar 2027.
- The review meetings described the business as growing three to four times, with about one proposal in three won, and teams that cannot be multiplied at the same rate. A figure of "$7 billion" was also spoken, against the written $6.6B; this is flagged as unresolved. These meeting figures are verbal and unsourced.

### Evidence or symptoms
The documents infer that engineer-hours, not factory capacity, are the binding constraint. No headcount source is given; this Needs confirmation.

### Impact
Quote capacity limits how much of the AI-infrastructure market SpinCo can bid for, and the cost is invisible on the profit and loss statement. Timing matters: before separation a new front end is part of standing up the company; after separation it becomes a migration project competing for budget.

### Cause
Demand growth against a fixed supply of design engineers, plus fragmented systems. The limits on hiring are not described.

### Expected solution
**Proposed (inferred design):** handle more bids with the same teams by reducing routine reading, assignment and chasing effort. No confirmed design. Earlier claimed time savings are unmeasured and not used.

### Success criteria
- Bid-handling effort and the number of bids declined, delayed or priced conservatively because engineers were committed are measured on real bids before and after any Layer 0 use. This needs SpinCo historical data; no target is set here.

### Dependencies and constraints
The measured share of cycle time spent reading (PM-001) and access to historical bids.

---

# Part B: Problems in the current PoC and project

These problems concern what has been built so far and how the project is documented and run. The code lines are separate and must not be read as one working system: the **v0.3.0 bid-triage pipeline** (folder `layer0-delivery/`), the **22 Sep fresh codebase** that led to the **v1.0 extraction-and-governance release** (23 Sep), and the **v1.1 three-stage decision demo** (folder `CPQ/`). No code line implements unit participation as a decision, workflow creation, team-response tracking, the three-view traceability, or final-response consolidation.

## PM-101: Layer 0's purpose was framed differently in each iteration, and the working direction is not yet formally signed off

### Problem
Four earlier framings of Layer 0 exist. The opportunity-management workflow described in the review meetings is now the working baseline, but it has not been formally confirmed, and no build delivers it end to end.

### Context and current behavior
**Workflow steps affected: all (this is the definition on which every step depends).**

The framings, in date order:

1. **"Agentic CPQ":** reads the RFP, drafts a design, routes to teams and assembles the proposal. Earlier documents; marked superseded.
2. **"Bid intake, triage and routing: the layer before CPQ":** the v0.3.0 line (workflow step 1, partial steps 2 and 5, partial step 7).
3. **"The intake layer in front of your CPQ":** extract specifications with source anchors, compare with past bids, flag deviations; the 22 Sep and v1.0 line (step 1 and an input to step 3).
4. **"Portfolio-risk-intake":** decision support at the bid, execution and portfolio stages; the v1.1 line (partial step 3).

The **working baseline** is the workflow in the review meetings (22 Sep and 5 Oct 2026): understand the RFP; determine which business units take part; support a human go/no-go; set up the workflow; break the RFP into requirements and work packages owned by teams; track each team's response; consolidate into a final response that traces back to every requirement. All four framings share a core with it: read the bid, identify requirements with their source, decide what can be automated or committed, route work to the right people and keep humans accountable.

Scope boundaries stated in the working baseline: tracking team work does not make Layer 0 a collaboration platform; consolidating responses is not autonomous proposal writing; supporting go/no-go gives the model no decision authority; and the integration boundaries with CPQ (Logik.io with Salesforce), aPriori, QuoteWin and ERP are uncertain.

### Evidence or symptoms
- The review meetings said the purpose of the project had not been stated clearly and had to be explained again.
- Whether Layer 0 produces prices or estimates is answered differently: never (v0.3.0 documents), estimation tables and a preliminary quote (22 Sep review meeting), a margin estimate (v1.1), cost and margin validation (agentic CPQ). This is an open scope question.
- The phrase "pre-RFI bid response system" was used in the review meetings, but every build reads RFPs or RFQs. It is flagged as an ambiguity.
- Ambiguities in the review meetings that need confirmation: "six companies" (and how they map to brands, pillars and teams); a "$7 billion" figure against the written $6.6B; a "January 4" start with no year; how change requests are applied incrementally; and whether bid/no-bid output is a deliverable (the working baseline is support).

### Impact
Teams build different things. The v1.1 demo misses the central expectation (PM-105), and effort goes to features that may be dropped.

### Cause
The idea changed across iterations: the v1.0 to v1.1 pivot is recorded in the revision log, and the description in the review meetings kept evolving. Why no single definition was written down: Cause not confirmed.

### Expected solution
**Expected (review meetings):** one purpose, the workflow above, recorded in the consolidated document that the 5 Oct meeting asked for.

**Proposed (inferred design):** the client point of contact formally confirms the workflow direction (or amends it), records the in-scope capabilities and states the acceptance criteria for the next demo. Until then, the documents describe the workflow as the working baseline and the direction as not signed off.

### Success criteria
- One written definition exists, reviewed and approved by the client point of contact, with a list of in-scope and out-of-scope capabilities.
- The definition states where estimation sheets and any price or margin figure stand.
- Each of the later documents (project overview, domain background, architecture) uses that definition.

### Dependencies and constraints
The two confirmed decisions from the meetings: call it a PoC or pilot, not a product; and consolidate all documentation into one reviewed document before more code is written.

---

## PM-102: v0.3.0 build status is overstated and several modules are not wired in

### Problem
The entry page of the v0.3.0 package says the main pipeline is "built, wired and tested" and "verified end to end on the genuine 101-page Syracuse procurement PDF", with 78 tests passing. A comparison of the documents with the code finds that several modules exist but are not connected, the default reader is a simple pattern matcher, and coverage numbers on a full document are unreliable.

### Context and current behavior
**Workflow steps affected: 1 (reading), partial 5 (routing per layer) and partial 7 (coverage, proposal checker); the build implements none of steps 3, 4 and 6.**

The build is a six-stage pipeline (Understand; Tier; Draft Design; Validate; Solve or Refuse; Coverage Map and Routing) with a human approval after every stage. Status from the component inventory:

1. Built, tested and connected: reading and file-type checks, extraction, scope detection, tier classification, validation, the six-stage control flow, source anchoring, the arithmetic solver, the coverage map and the screen.
2. Built and tested but not connected: the proposal checker; the requirement registry; three of four routing adapters (the one for the custom-engineering route is not written).
3. Stubs only: connectors to external systems (see PM-111).
4. Not built: OCR (optical character recognition, turning scanned images into text), addenda handling, a case ledger, human edit / split / merge, layout-aware clause splitting, a payload inspector, estimation sheets, an immutable audit log.
5. The model-change guard (a check that blocks a language-model change if it worsens known-good answers) exists but is a developer pre-release check, not part of a run.

As a result, end-to-end submission stops at the coverage map, and routing to teams is manual.

### Evidence or symptoms
- The entry page lists fewer "not built" items than the analysis, and treats the routing adapters as tested while the component list says written but not connected.
- **Contradiction, not reconciled:** test counts vary (6, 21, 27, 37, 68, 78); one file gives both 78 and "68 tests, about 70 seconds". The claim "verified end to end" contradicts the finding that clause splitting is unreliable on the full 101-page PDF.
- Component numbers skip M12 without explanation.
- A defect in Stage 3: layers that are out of scope are drafted as custom-engineering items, so screens say "drafted across all six layers" and "attempted 6 layers, solved 0" when only one layer is in scope.
- A clean demo could not be run in the 22 Sep 2026 review: the upload failed, the system was in mock mode and the earlier side-by-side view was missing.
- Components were rebuilt because nobody knew they existed: the model-change guard was rewritten from scratch.

### Impact
A team receiving the package may assume capabilities exist that do not, and a presenter can be challenged live. Effort is duplicated.

### Cause
Not stated. The analysis notes that the code was built with AI coding tools, that one tool "disconnected some modules", and that there is one version-control commit (see PM-110). That is a hypothesis; Cause not confirmed.

### Expected solution
**Proposed (inferred design, from the delivery notes), in order:** connect the proposal checker; finish the routing adapters and add a payload inspector; broaden extraction for clause types still unhandled; confirm which design standards each SpinCo product line uses and replace generic values; obtain real interface contracts before building connectors. The analysis suggests first a clean baseline on the team's machines. Priority Needs confirmation. Until then, state status exactly as in the component inventory.

### Success criteria
- The documented status of each module matches what the code does.
- The test count and result are reproduced on a clean machine, and the document states one number with its source; the contradictory counts are retired.
- A run on the full 101-page PDF shows coverage figures that a reviewer can check against the original.

### Dependencies and constraints
Real connector contracts need Flex or SpinCo IT. Tests on the real PDF are slow.

---

## PM-103: Extraction runs on pattern matching (regex) by default; the language-model path is incomplete and untested

### Problem
The first step, reading the RFP, uses regex (fixed text-matching patterns) and keyword counting by default. The language-model mode is optional, needs a local model server and has an incomplete prompt. Everything downstream depends on this step.

### Context and current behavior
**Workflow step affected: 1 (read and understand), and through it every later step.**

- The default `mock` mode needs no model and gives the same output on every run. An optional local model (Llama 3.1 8B at temperature 0.1) is reached through a single adapter file.
- Regex extraction targets about 20 fields; the model prompt asks for 10.
- The intended design is that the model only reads, and all consequential decisions are fixed rules.

### Evidence or symptoms
- The 22 Sep 2026 review meeting took the extraction to be language-model based. The screen showed "mock", no credentials file existed, and changing "voltage class 15" to "16" changed the output. The review identified the reader as a simple regex, which picks up the table of contents and misses requirements inside sentences.
- The entry page's "verified end to end" claim is stronger than the analysis, which says the "reader works" risk was retired only with regex tuned to these documents, and that "has real local LLM inference been run end to end?" is unretired.
- If the model mode is switched on, the code reading predicts: all layers treated as in scope; Syracuse falling back to the wrong brand; the solver unable to solve the UPS (uninterruptible power supply) example; coverage losing fields. This is untested.
- Documents for other code lines disagree: the fresh codebase says extraction is model-based; the v1.0 release documents a hybrid; no model is bundled with v1.0.

### Impact
Real RFPs, worded differently from the tuned samples, may be misread, and a misread propagates through every later stage. Confidence in the demo suffers.

### Cause
The default is a design choice so the demo runs without a model download. The reason the prompt is incomplete is not stated.

### Expected solution
**Proposed (inferred design, from the analysis):** connect a real model (local, or Azure OpenAI if keys exist) at temperature 0 behind the single adapter; extend the prompt to return all fields; keep scope detection as deterministic code; keep mock mode for demos; require the model-change guard to pass before any model demo. A second model that checks the extraction is an idea only. The choice of model and hosting Needs confirmation, including whether RFP text may leave the machine.

### Success criteria
- Model-mode output on the real 101-page PDF matches the known-good answers the guard holds, and a reviewer can see which mode produced a result.
- A change to a value in the input changes the output in the expected way in model mode, and the mode is shown on screen.
- Each extracted item still shows document, page and quoted text.

### Dependencies and constraints
Choice of model and hosting. The review meetings ruled out fine-tuning.

---

## PM-104: The v1.1 demo reads no RFP and runs on synthetic, placeholder data

### Problem
The v1.1 demo shows bid, execution and portfolio screens, but no RFP is read. Pre-built JSON scenario files (a plain-text data format) are shown through one backend endpoint.

### Context and current behavior
**Workflow step affected: partial step 3 only (the demo is decision-support rules over synthetic data); it implements none of steps 1, 2, 4, 5, 6 and 7.**

Three fixed-rule evaluators compute BID / HOLD / NO_BID, ECN and phase lock, and a conflict comparison from structured scenario data. There is no PDF reading, ERP link or alerting.

### Evidence or symptoms
- The 5 Oct 2026 review observed that the demo has no actual RFP input, the data is pre-built and there is no live logic.
- Placeholders in the written documents: standard lead time (inferred from test data), plant capacity (user-provided, with unclear framing), busbar risk ratings (domain assumptions), decision deadlines (synthetic) and per-customer margins (derived backwards from a total). Lifecycle risk rules are "encoded domain reasoning, not a sourced risk matrix".
- Scenario values contradict each other across documents, so none is quoted.
- The aggregate "highest risk factor" uses an alphabetical maximum instead of a severity ranking, a known defect left in place.
- The browser click-through was not done, and the "production-ready" sign-off has blank reviewer and approval fields.

### Impact
The output shows a screen, not decision quality. Presenting it as evidence of value would repeat the mistake described in PM-108.

### Cause
It was built quickly to show the structure on test data; reading and calibration were deferred.

### Expected solution
**Proposed (inferred design):** a backtest on historical SpinCo cases to replace the placeholders and measure how often problems are caught; PDF ingestion and an ERP link later. The documents disagree on the version numbers for those later steps. The rules-plus-retrieval engine discussed in the review meetings is not shown by the demo.

### Success criteria
- A demo of the decision support starts from an RFP that is actually read, with the evidence traced to its source passages.
- Every constant used in the demo is labelled as placeholder or replaced by a sourced value.
- The nine demo criteria in the delivery summary (seven met, two with caveats) are not presented as measures of value.

### Dependencies and constraints
Real SpinCo historical cases and real constants.

---

## PM-105: The expected three-way traceability view is missing

### Problem
The review meetings expected one set of screens showing (1) the RFP or bid that came in, (2) how its requirements were broken up and assigned across teams, and (3) how each team responded, all converging in the final response. No build shows it.

### Context and current behavior
**Workflow steps affected: 5, 6 and 7 (the three views of the traceability chain; see PM-017).**

- The 5 Oct 2026 review repeatedly noted that one more screen was expected but not visible, and that it may have been lost along the way.
- The v0.3.0 build has clause-to-source links and a coverage map, but routing is per layer, not per requirement, and the requirement registry is not connected.
- The 22 Sep demo lacked the side-by-side screen of an earlier build; that build had been overwritten in the same folder.
- An expert panel had asked for a three-panel workspace (inbound RFP, past SpinCo proposal, requirement graph). The v1.0 line has a three-panel prototype that was never compiled or verified.

### Evidence or symptoms
Unresolved: whether the view was lost in the project moves or never built. The 22 Sep review meeting raised the question of what value is being delivered to the client.

### Impact
The central expectation raised in the review meetings cannot be demonstrated.

### Cause
Cause not confirmed. Hypotheses: overwritten files without version control (PM-110) and changing framings (PM-101).

### Expected solution
**Proposed (inferred design):** make the requirement the unit of work, with a stable ID, source, tier, owning team, response and final-answer link, and build a screen set linking RFP, breakdown and team responses (see PM-017).

### Success criteria
- For a sample RFP, a reviewer can move between the three views and follow a requirement from its source clause through its assignment and team response to the final-response section.
- The three views show the same requirement state at the same time.

### Dependencies and constraints
Needs PM-101 (a definition), PM-106 (editing and an audit log), PM-107 (complete extraction) and PM-016 (responses).

---

## PM-106: Reviewers cannot edit, split or merge results; first-pass facts are not frozen; there is no immutable audit log

### Problem
Reviewers can only approve or reject each stage, and a rejection ends the run. They cannot change, split or merge a result. The first extraction is not frozen against re-runs, and there is no tamper-proof record of who did what.

### Context and current behavior
**Workflow steps affected: 5 (editing the breakdown) and the cross-cutting audit history and human accountability.**

- In v0.3.0 each stage ends with approve or reject. A rejection needs a reason and stops the run for good. There is no skip and no modify.
- Approvals sit in a database that can be edited, so it is not an audit log.
- The registry design supports split and merge, but the operations are not built.
- The v1.0 design (a different code line) has an event log, override tracking, a correction ledger and an edit / split / merge lifecycle with versions; those claims were not verified.
- An expert panel expected: engineers can add, edit, split and merge requirements with a version and reason; repeated overrides surface as candidate rules a human approves; an automatic rule from one override was rejected; downward tier overrides are gated; an immutable event ledger exists.

### Evidence or symptoms
The review meetings asked whether a result can be modified, and the answer was no. **Expected (review meetings):** the LLM has no authority to change a result, but a person does. Freezing the first extraction is designed but not built, and temperature is 0.1 where 0 is wanted.

### Impact
A wrong extraction cannot be corrected inside the tool, so reviewers work outside it. A decision cannot be reconstructed later, which weakens the trust case in PM-013.

### Cause
Cause not confirmed; the sources describe these as deliberately deferred ("schema supports it, operations not built").

### Expected solution
**Proposed (inferred design):**

1. A side-by-side review with approve, change or reject for each requirement, recording the editor and time.
2. Freeze the first-pass extraction so re-runs read it and only human edits change it.
3. An append-only audit log of stage outputs, approvals, edits and model version, kept apart from editable state.

The required review actions and log contents Need confirmation.

### Success criteria
- A reviewer can change, split, merge or reject a requirement, with a reason, and the earlier version remains visible.
- Re-running the extraction does not overwrite a human edit.
- The audit log shows who did what and when, and an ordinary user cannot edit or delete an entry.

### Dependencies and constraints
Needs a decision on what the log contains and who may read it; depends on requirement IDs (PM-004).

---

## PM-107: Requirement extraction is incomplete (commercial, legal and staffing missed; clause splitting unreliable; no OCR)

### Problem
The build extracts only technical specification fields. Commercial terms (pricing basis, lump sum), legal terms and staffing items are not extracted. Clause splitting on a full PDF treats table-of-contents lines as requirements, and scanned pages are not read.

### Context and current behavior
**Workflow steps affected: 1 (reading) and 5 (the breakdown relies on complete requirements); also 7 (completeness check).**

- Extraction targets about 20 technical fields: capacity, redundancy, voltage, UPS size, breaker positions, arc-resistant type, rack count, rack density, timeline and standards. Scope detection is tuned to medium-voltage electrical and direct-current (DC) vocabulary.
- The coverage map splits text into clauses by a pattern matcher that matches document shape, not meaning.
- Reading handles text PDFs page by page. Pages with no text are reported as unreviewed, and ZIP files are listed, not opened.

### Evidence or symptoms
- In the 22 Sep demo: "17 identified requirements, 0 extracted". Commercial clauses were not extracted, and coverage did not span the whole document.
- On the 101-page PDF the coverage denominator is unreliable, though a clean sample works. Page 83 of that PDF is scanned. This contradicts the "verified end to end" statement (PM-102).
- **Expected (review meetings):** non-technical requirements (a geography, night support, a team location) become requirements.

### Impact
Coverage percentages cannot be trusted on real documents, and non-technical requirements are invisible and have no route.

### Cause
Pattern-matched splitting reads shape, not meaning. The technical-only scope is a design choice of this line.

### Expected solution
**Proposed (inferred design, from the delivery notes):** layout-aware parsing plus model line-classification (requirement, administrative or noise) at temperature 0, frozen after the first pass and confirmed by a human; extend extraction beyond technical fields using a written requirement definition and example RFPs. The delivery notes call this "real work, not a regex tweak". OCR is not scheduled. Whether commercial, legal and staffing items should be extracted at all Needs confirmation.

### Success criteria
- On the full 101-page PDF, table-of-contents lines are not counted as requirements, and an engineer's spot check finds the coverage list consistent with the document.
- Scanned pages are reported as unread, not skipped silently.
- If commercial, legal and staffing items are in scope, a sample RFP shows them as requirements with source references.

### Dependencies and constraints
Needs a written definition of what counts as a requirement.

---

## PM-108: Value is unproven: metrics were inflated then retracted; the business-case assumption is unmeasured

### Problem
No benefit of Layer 0 has been measured on real SpinCo data. Earlier pitch material claimed precise results that the code never computed, and the central assumption (that reading and triage take a large share of the bid cycle) has not been tested.

### Context and current behavior
**Workflow steps affected: all (the value hypotheses are unmeasured).**

- **Retracted claims (superseded history; never to be used as results).** Earlier pitch material stated a 100% catch rate (on one case), 4 hours saved per RFP, $300K protected, annual savings of $900K-$1.5M, a 928% return on investment and a payback of 1.2 months, with a demo output of "47 specs extracted". All are superseded.
- **What happened.** On 23 Sep the demo script was run for the first time instead of being trusted. It failed to run. Once running it produced a 0% catch rate, $0 protected and a -93% return. Two deviation-matching bugs were fixed. A later list names five QA fixes and gives the origin of the earlier numbers: a hardcoded summary block printed regardless of results.
- **Current evidence.** One synthetic case modelled on a real public RFP: 2 specifications extracted and anchored, the arc-resistance deviation flagged with 67% deviation confidence (the basis is not explained), and a case-study assumption for the cost of the miss.
- **Business-case assumption.** The 5-10 day reading estimate is an unmeasured expert judgment, and "the entire business case rests on it".
- **Hypotheses to be measured (none measured):** fewer coordination delays; fewer missed hand-offs; fewer unanswered requirements at submission; less rework; faster, more consistent and more accountable go/no-go decisions; clearer ownership; less time reading RFPs.

### Evidence or symptoms
- Status sheet: catch rate "not measured, n=1"; return on investment not measured; case isolation not stress-tested.
- Planned pilot size differs: 5-10 historical RFPs in most documents, 10-20 in one. The expert panel asked for 20 quote requests with won quotes, production parts lists and change orders.
- The frequency of real change orders, needed for any return figure, is unknown. The v1.0 line was built against "a described process, not an observed one".

### Impact
All earlier external numbers are invalid. Without measured data there is no credible go/no-go decision and no pilot business case.

### Cause
The figures came from an unverified demo summary and assumed volumes. Measurement has not happened because SpinCo historical data has not been supplied.

### Expected solution
**Proposed (inferred design):**

1. Run historical SpinCo RFPs with known outcomes (original bid plus any change order) through a fixed backtest.
2. Report the measured catch rate whatever it is.
3. Compute any return from measured change-order frequency.
4. Audit past quote requests for the share of cycle time spent reading and triaging.

Release rule from the revision log: no catch-rate or return figure goes outside until measured on real data.

### Success criteria
- Pilot proceed: real RFPs ingested as plain text; extraction spot-checked by a SpinCo engineer; case isolation holds; a measured catch rate is obtained and reported whatever it is.
- Business case: the share of the cycle spent reading and triage is measured on real bids; whether it is large enough to justify Layer 0 is decided from that measurement.
- Which set of criteria applies to the current PoC Needs confirmation. No catch-rate, savings or return figure is quoted until measured.

### Dependencies and constraints
SpinCo must supply historical RFPs, past bids and change-order records. The "Phase 2" of about four weeks is an estimate that depends on that data. Phase and version names differ between code lines.

---

## PM-109: The demo cases are illustrative and do not match SpinCo's customer types

### Problem
The demo case, a switchgear RFP from the Syracuse Regional Airport Authority, comes from a customer type SpinCo does not list. The v1.1 scenarios pair hyperscalers and neoclouds with 15 kV switchgear, a pairing that is also unconfirmed.

### Context and current behavior
**Workflow steps affected: 1 and 3 (the cases used to show them); the examples are illustrative.**

- Syracuse was chosen because it is public and uncontroversial, technically specific and in SpinCo's product category: medium- and low-voltage switchgear belong to Critical Power Products, one of SpinCo's four product pillars.
- The RFP is real. The past bid and the gap are constructed. The case is "not a claim that SpinCo bid on Syracuse".
- Customer types by pillar: power products to utilities; thermal management and cloud to silicon providers, colocation providers, hyperscalers and neoclouds. The two largest customers are about 64% of revenue, inferred but not confirmed to be hyperscale or cloud-adjacent.
- SpinCo's role is unknown: manufacturer, integrator, distributor or design-build contractor; direct bidder or subcontractor; who owns specification risk. The v1.1 documents assume a direct bidder.

### Evidence or symptoms
The grounding document concludes that the product-category match "is strong and verifiable", but the customer-type match "is not established". Early materials risked implying Syracuse was a SpinCo case. Scenario figures conflict between documents.

### Impact
Presenting Syracuse as typical, or its numbers as SpinCo's, would mislead and cost credibility. A single-unit switchgear case also does not exercise the multi-unit workflow (see Worked examples).

### Cause
The public example was chosen for open-record availability, and SpinCo's own cases were not available.

### Expected solution
**Proposed (inferred design):** keep Syracuse with precise framing ("a real public medium-voltage switchgear RFP used to show the mechanism on your product category, not your typical customer") and add a second illustrative case for the multi-unit workflow, such as a hyperscale data-centre campus RFP; that needs its own research. Disclose the public provenance on a slide and in the demo script. One document lists this as pending and another says it was clarified later, so its status Needs confirmation.

### Success criteria
- Demo materials state that the cases are public or synthetic and illustrative.
- A demonstration covers at least one single-unit and one multi-unit opportunity.
- Validation uses SpinCo's own historical cases, once available.

### Dependencies and constraints
Research for a second case; SpinCo's input on its bid process and product-line names ("Critical Power Products" is adopted from public material; whether it is SpinCo's internal name is unconfirmed).

---

## PM-110: Code versions and documents are fragmented and contradictory (no version control)

### Problem
Several code lines and many overlapping documents exist, they contradict each other, and the code has no version history, so nobody can say which version is current.

### Context and current behavior
**Workflow steps affected: all (the baseline for building any step is unclear).**

- Code lines in date order: v0.3.0 (21 Sep) and v0.3.1 (22 Sep) in `layer0-delivery/`; a 22 Sep fresh codebase; the v1.0 release (23 Sep); the v1.1 release (folder dated 24 Sep, parent folder 28 Sep). v1.1 says it has "no prior v1.0 codebase", and v1.0 documents describe modules v1.1 never built.
- Two different documents share each of the names `MODULE_STATUS.md` and `ARCHITECTURE.md`.
- "v1.1" means a small documentation correction in one memo and a code rewrite in later documents.
- Roadmaps differ between code lines, and the gap lists "GAP 1-4" and "GAP 1-6" differ.
- The revision log introduced a rule (every file carries `_vN`, nothing silently overwritten), which many files do not follow.

### Evidence or symptoms
- The review meetings raised that there is no version control and everything sits in one folder, that an AI coding tool disconnected modules, and that a downloaded zip may lose track of which file is latest. The analysis confirms one version-control commit for the whole folder.
- An earlier AI project setup hit memory limits, was moved twice and could not be shared across accounts.
- The analysis asks whether `layer0-delivery` is the newest "enhanced" 17-module version.

### Impact
Time is lost (about 40 minutes of the 22 Sep session went on environment trouble), the team risks building on the wrong baseline, and documents still quote retracted figures (PM-108).

### Cause
Iterative AI-assisted building across several sessions and tools without version control; this comes from the review meetings and is not independently confirmed.

### Expected solution
**Expected (review meetings):** use an LLM to merge all documentation, in batches, into one final document that the client point of contact reviews, and fix issues in that document before writing more code. **Proposed (inferred design):** a clean baseline committed to version control. Which code line is the baseline Needs confirmation.

### Success criteria
- One reviewed consolidated document exists.
- One baseline is under version control, with a history that shows what changed.
- Each document states which code line it describes.

### Dependencies and constraints
Client point of contact review of the consolidated document; batching because of model context limits.

---

## PM-111: Integrations with downstream systems exist only as stubs

### Problem
Connectors to the systems that hold prices, costs and orders (QuoteWin, SAP / Infor LN and aPriori) are interface stubs and none is live. Layer 0 cannot pull prices or parts lists from them or hand work to them.

### Context and current behavior
**Workflow steps affected: 5 to 7 (hand-off of assigned work and read-back of responses); the boundaries are uncertain.**

- The systems: QuoteWin (sales quoting software), SAP and Infor LN (two ERPs), aPriori (a should-cost tool) and Logik.io (the configurator Flex licenses, used with Salesforce). Stubs are disabled by default.
- The design is that Layer 0 stays in front of these systems and does not replace them. An expert panel wanted checked JSON contracts rather than live database links.
- Three of four routing adapters exist but are not connected (PM-102).
- It is open what is handed off, what is read back, and whether opportunities are created in a CRM (customer relationship management system).

### Evidence or symptoms
No real interface contracts or credentials exist. The v1.0 line also has stubs only.

### Impact
There is no automated hand-off. Routing is manual copying, and there is no real pricing or parts list. Value beyond triage and tracking cannot be shown.

### Cause
An external dependency: contracts and credentials are held by Flex or SpinCo IT.

### Expected solution
**Proposed (inferred design):** obtain real contracts first, then build connectors one at a time, starting with aPriori, which Flex already uses. Connectors are not required for the pilot exit. Whether Layer 0 should connect to these systems at all depends on the open scope question (PM-101).

### Success criteria
- For each downstream system, a written statement of what Layer 0 hands off and what it reads back.
- Any connector that is claimed to work is demonstrated against the real system or a checked contract.

### Dependencies and constraints
Contracts and credentials from Flex IT; whether SpinCo keeps Logik.io after separation.

---

## Worked examples

**These examples are illustrative. They are not recorded SpinCo bids.** Each walks one opportunity through the seven workflow steps as the workflow is intended to work, then names the problems from this document that would show up today. The intended workflow is not implemented end to end by any build.

### Example 1: single-unit opportunity (standalone medium-voltage switchgear RFP)

An RFP like the public Syracuse airport switchgear RFP used in the PoC (a real public document, not a SpinCo bid).

| Step | What would happen | Problems that would show up |
|---|---|---|
| 1. Read and understand | The RFP is read; each extracted item (for example "arc-resistant Type 2B") keeps document, page and quoted text. | PM-001, PM-003; PM-103 and PM-107 (regex reader; unreliable clause splitting on the full 101-page PDF; a scanned page) |
| 2. Participation | One business unit (critical power) is likely to participate; other units are marked "not needed". | PM-006 (no systematic way to decide; unit mapping to be confirmed) |
| 3. Go/no-go | A person decides on scope fit and deviations such as arc resistance against the standard offer. The decision is recorded. | PM-008; PM-002 (configure or engineer); PM-104 (v1.1 uses synthetic data) |
| 4. Workflow | A light workflow: engineering review of requirements, plus commercial and compliance items. | PM-015 (no workflow system exists) |
| 5. Break down and assign | Requirements are numbered and assigned to the owning team, or marked "unassigned". | PM-004; PM-106 (no edit, split or merge); PM-012 (drawings and vendor specs not linked) |
| 6. Track responses | The owning team responds; status is visible per requirement. | PM-016 |
| 7. Consolidate | The final response is assembled; every requirement is shown as answered or excluded. | PM-007, PM-017, PM-105 (no three-view screen) |
| Cross-cutting | An addendum or Q&A answer updates the affected requirement. | PM-005; PM-013; PM-106 |

### Example 2: multi-unit opportunity (AI data-centre campus RFP)

An RFP like the synthetic 48 MW hyperscale-campus sample (a synthetic case, not a SpinCo bid).

| Step | What would happen | Problems that would show up |
|---|---|---|
| 1. Read and understand | A long RFP with facility power, rack power, cooling and compute sections is read; items are anchored to source. | PM-001, PM-003; PM-107 (commercial, legal and staffing missed) |
| 2. Participation | Several units may be needed: facility power and switchgear, rack and board power, liquid cooling, possibly compute integration. Not every data-centre bid needs every unit; a synthetic modular inference-pod sample may need fewer. | PM-006 ("six companies" versus layers versus teams) |
| 3. Go/no-go | A person decides with evidence of scope fit, deviations, and capacity or portfolio conflicts across customers. | PM-008, PM-010, PM-011 (no workload view) |
| 4. Workflow | A heavier workflow that coordinates responses across units before consolidation. | PM-015 |
| 5. Break down and assign | Requirements are split into sub-requirements. One requirement, such as rack power plus cooling at a given density, may involve two teams. | PM-004 (v0.3.0 routes per layer, not per requirement); PM-017 |
| 6. Track responses | Each team's response is tracked; a missing second team on a shared requirement is visible. | PM-016, PM-011 |
| 7. Consolidate | Responses are brought together into the final response and every requirement is checked as answered or excluded. | PM-007, PM-017, PM-111 (downstream systems are stubs) |
| Cross-cutting | A change request arrives mid-process; a drastic change would restart as a new opportunity. | PM-005; PM-009 (later contract phases) |
