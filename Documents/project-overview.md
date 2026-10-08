# Layer 0: Project Overview

## 1. Purpose, Who This Is For, and Scope

**Purpose.** This document explains the Layer 0 project: what it is meant to do, why it exists, what has actually been built, and what is proposed or still undecided. It is the entry point to the documentation set. Earlier framings of the idea and the chronology are kept in one place, section 11 ("How the idea evolved: history").

**Who this is for.** Developers who have just joined the project, and the client point of contact who reviews the documents. You do not need electrical-engineering or Flex business knowledge. Terms are explained where they first appear.

**Scope.** Project description, status and history. It does not repeat three topics that have their own documents:
- the customer's business, products and how a bid works today: [business-and-domain-background.md](business-and-domain-background.md);
- each problem in detail, with impact and success criteria: [problem-mapping.md](problem-mapping.md);
- how the software is built: [architecture-overview.md](architecture-overview.md).

**How to read the labels.**
- **Intended** is the business direction described in the review meetings (22 Sep and 5 Oct 2026). It is the working baseline for purpose and workflow. It has not been formally signed off, and the meetings are not evidence that anything is built.
- **Expected (review meetings)** marks an explicit expectation stated in those meetings.
- **Proposed (inferred design)** marks a design recommendation inferred from the direction. It is not an approved technical design.
- **Implemented (by code line)** describes only what a code line actually does, with its caveats.
- **Needs confirmation** marks a point that remains open.

## 2. What Layer 0 is

Layer 0 is a proof of concept (PoC: a small build that tests whether an idea works; it is not a product) for SpinCo, the existing Flex business being spun off as Axiom Solutions. Its intended purpose is to help the business manage an incoming bid opportunity, from the moment a request for proposal (RFP: a long customer document that says what the customer wants to buy) arrives until the final bid response is assembled.

It should:
- help understand the RFP;
- determine which business units need to take part;
- support a human go/no-go decision;
- set up the workflow for that opportunity;
- break the RFP into requirements and work packages owned by the right teams;
- track each team's response;
- bring the responses together into a final response that traces back to every original requirement.

This workflow is the business direction described in the review meetings and is used as the working baseline. It has not been formally signed off, and no existing build implements it end to end.

**What this does not mean.** Layer 0 is not a general-purpose collaboration platform. It does not write proposals autonomously: people write the team responses. It does not give the language model (LLM: a program that reads and writes text) any decision authority: a named person decides, and the decision is recorded. It is not a pricing engine, an ERP replacement or an autonomous engineering-design tool. See section 5 for the scope boundaries.

**Terms used throughout** (kept distinct; never treated as equal):

| Term | Meaning |
|---|---|
| Opportunity | An incoming bid (from an RFP, request for quotation RFQ, or request for information RFI) that the business considers pursuing |
| Business unit | An organisational unit of SpinCo / Axiom Solutions that sells and delivers. The review meetings spoke of "six companies"; how these map to brands, pillars and teams is Needs confirmation |
| Brand | An acquired company name, for example Anord Mardix, Crown, EP2, Flex Power Modules, JetCool, EPC Power (pending), Cloud |
| Product pillar | Critical Power, Embedded Power, Thermal Management, Cloud |
| Product layer | One of the six grid-to-chip layers, L1 to L6. "Six layers" is not the same as "six companies"; there is no one-to-one mapping |
| Team | The delivery or engineering team that owns and answers requirements. The v0.3.0 knowledge base uses four: Critical Power, Embedded Power, Thermal (JetCool), Cloud |
| Requirement, sub-requirement, work package, assignment, team response, final bid response | The items tracked through the workflow. A work package is a group of requirements assigned to a team |
| Go/no-go decision | A human decision on whether to bid; Layer 0 supports it |

## 3. Why it exists

Detail is in [problem-mapping.md](problem-mapping.md). The core problem is how a multi-unit business manages one opportunity; reading effort is one part of it.

**3.1 The opportunity-management problem (core).** A large bid, such as an AI data-centre campus, can touch several SpinCo business units at once. Today the steps between "an RFP arrives" and "one coherent response goes out" are largely manual and hard to see:
1. Nobody has a systematic way to decide which business units should take part (PM-006: No systematic way to decide which business units should participate).
2. Go/no-go decisions rest on judgment, with little structured evidence and unclear accountability (PM-008: Go/no-go decisions lack structured evidence and clear accountability).
3. When a bid goes ahead, no workflow specific to that opportunity is set up; customers and product combinations differ, so one fixed process does not fit (PM-015: No opportunity-specific workflow is set up when a bid goes ahead).
4. Requirements are not broken down into work owned by named teams (PM-004: Requirements are not broken down into team-owned work).
5. Team responses are not coordinated or tracked against the requirements assigned to them (PM-016: Team responses are not coordinated or tracked against assigned requirements).
6. The link from a source requirement to its assignment, its response and the final bid is not preserved (PM-017: The link from source requirement to assignment, response and final bid is not preserved).
7. There is no final check that every requirement is answered (PM-007: No final check that every requirement is answered).

**3.2 Supporting problems.**
- **Reading is manual.** RFPs often run past 100 pages and mix standard items with items that need new engineering. A few experienced engineers decide line by line which is which; the decision is not recorded (PM-001: Reading and understanding each RFP is manual, slow and unrecorded).
- **Quoting software starts too late.** CPQ (Configure, Price, Quote: software that lets a salesperson pick options from a fixed menu and get a valid price) works for configurable products but starts only after a human has read the RFP and typed in structured requirements. Flex already uses a CPQ capability, Logik.io, alongside Salesforce (PM-002: Existing CPQ cannot decide "configure or engineer", and starts only after a human has read the RFP).
- **Requirements are not tied to their source**, so a miss can surface after award as a change order, a paid change to the contract (PM-003: Requirements are not tied to their exact source, so misses surface after award).
- **Clarifications, addenda and change requests** are not captured against requirements (PM-005: Clarifications, addenda and change requests are not captured against requirements).
- **Traceability stops at the RFP** (PM-012: Traceability stops at the RFP (drawings, vendor specs, test reports and email are not linked)).
- **AI output is not trusted** without anchoring, repeatability, human authority and an audit trail (PM-013: AI output cannot be trusted without source anchoring, repeatability, human authority and an audit trail).

**3.3 Commitments, capacity and volume.**
- Specification changes between contract phases are caught late (PM-009: Specification changes between contract phases are caught late).
- Commitments across customers are compared by judgment alone (PM-010: Commitments across customers are compared by judgment alone (capacity, specification and timeline)).
- Concurrent bids by overlapping teams risk crossed wires, with no workload view (PM-011: Concurrent bids by overlapping teams risk crossed wires; there is no workload view).
- Flex guides growth of +65 to +75% for FY27 and +80% for FY28, and engineering headcount cannot keep pace (PM-014: Bid volume is growing faster than engineering headcount). The review meetings raised three- to four-fold business growth and about one proposal in three converting (Needs confirmation).

## 4. Goals

1. Give each incoming opportunity one managed path from RFP to final response, with a clear owner at every step.
2. Understand the RFP: extract requirements, each with an exact source reference (document, page and quoted text).
3. Help decide which business units take part, and support a human go/no-go decision with assembled evidence (scope fit, deviations, capacity or portfolio conflicts, open questions).
4. Break the RFP into requirements and work packages owned by the right teams, and track each team's response.
5. Assemble the responses into a final bid response that traces back to every original requirement, and check that each is answered or explicitly excluded.
6. Keep humans accountable: human approval at every consequential step and an audit history of decisions and changes.
7. Handle clarifications (Q&A), addenda and change requests against the affected requirements.

## 5. Scope and boundaries

**In scope (Intended).** The seven workflow steps in section 7, with human approval, an audit history and change handling running across them.

**Boundaries.**
- **Tracking team work is part of Layer 0.** It does not require Layer 0 to be a general-purpose collaboration platform.
- **Linking and consolidating team responses is not autonomous proposal writing.** People write the responses.
- **Supporting go/no-go does not give the model decision authority.** A person decides and is recorded. The working baseline is that bid/no-bid output is decision support, not a Layer 0 decision.
- **Language-model rule.** The model reads; it does not decide anything that carries liability. Classification, validation and calculation are repeatable rules. In every code line the default run uses no language model; the intended design uses one only for reading.
- **Downstream systems.** CPQ (Logik.io with Salesforce), costing (aPriori), quoting (QuoteWin), enterprise resource planning (ERP: SAP, Infor LN), product-data systems and engineering teams may support downstream work. The integration boundaries are uncertain and open: what is handed off, what is read back, and whether opportunities are created in a customer-relationship management (CRM) system.
- **Open scope question.** Whether per-team estimation sheets, or any price or margin figures, belong inside Layer 0. Earlier documents say Layer 0 never produces a price; the review meetings mention estimation tables; v1.1 produced margin estimates on synthetic data. This is not resolved.
- **Not in scope:** configuration engine; pricing engine; generator of quotes or bills of materials (BOMs); replacement for Logik.io, Salesforce, QuoteWin, SAP or aPriori; CAD or design tool; autonomous engineering design.
- **Input type.** The review meetings used the phrase "pre-RFI bid response system", but every build reads RFPs or RFQs. RFIs, RFPs and RFQs are all treated as possible inputs (Needs confirmation).

## 6. Users, stakeholders and roles

- **Flex**: parent company and ultimate customer of the work.
- **SpinCo (to become Axiom Solutions)**: the business whose bids Layer 0 would support. It sells to utilities, hyperscalers (very large cloud providers), neoclouds (new AI-infrastructure entrants), silicon providers and colocation operators; details are in the business background document. The exact separation date is Needs confirmation.
- **Zensar**: builds the PoC.
- **Client point of contact**: the business-side point of contact for the PoC; the review meetings of 22 Sep and 5 Oct 2026 were held with this role.
- **The Zensar team**: takes the PoC forward. The PoC code was produced with AI coding tools and has no version history.
- **Intended end users (Proposed, inferred design):** bid managers and application engineers who read RFPs; the people who make go/no-go decisions; and the owners of teams who receive and answer work packages. Titles and named individuals at SpinCo are Needs confirmation.

## 7. Target workflow (Intended)

This is the business direction described in the review meetings. No code line implements it end to end.

1. **Read and understand** the incoming RFP. Every extracted item keeps an exact source reference: document, page and quoted text.
2. **Determine participation.** Decide whether one, several or all relevant business units need to take part. Not every data-centre bid needs every unit.
3. **Support a human go/no-go decision.** Layer 0 assembles the evidence (scope fit, deviations, capacity or portfolio conflicts, open questions). A named person decides, and the decision is recorded.
4. **If go, establish the workflow** for that opportunity. Different customers and product combinations need different workflows: some steps are mandatory, some configurable.
5. **Break the RFP into requirements and work packages** assigned to the appropriate teams. One requirement may involve several teams.
6. **Track each team's response** against its assigned requirements.
7. **Bring the responses together** into the final bid response with complete traceability, and check that every requirement is answered or explicitly excluded.

**Cross-cutting, at every step:**
- human approval and accountability;
- an audit history of decisions and changes;
- handling of clarifications (Q&A), addenda and change requests against the affected requirements. The review meetings described incremental handling of change requests, with a drastically changed RFP treated as a new opportunity (how changes are applied incrementally is Needs confirmation).

### 7.1 Traceability chain and three views

The chain is: **Original RFP requirement → breakdown and team assignment → team response → final bid response.**

The review meetings described three connected views that must all connect in the final response (Expected (review meetings)):
1. the original RFP;
2. how its requirements were broken up and assigned;
3. how the teams responded.

The **requirement** is the main tracked item. It keeps its source reference, its sub-requirements, the participating team or teams, each team's response, and the parts of the final response that answer it. The missing three-way view is PM-105 (The expected three-way traceability view is missing).

### 7.2 Illustrative examples (illustrative, not a recorded SpinCo bid)

**Single-unit opportunity.** A standalone medium-voltage switchgear RFP, like the public Syracuse airport switchgear RFP used in the PoC.
- Likely one business unit (critical power) participates.
- A light workflow: engineering review of requirements such as arc-resistant Type 2B, plus commercial and compliance items.
- Go/no-go turns on scope fit and deviations.
- Every requirement still traces to its owning team and its answer in the final response.

**Multi-unit opportunity.** An AI data-centre campus RFP, like the synthetic 48 MW hyperscale-campus sample.
- It may need facility power and switchgear, rack and board power, liquid cooling, and possibly compute integration.
- That means several business units and teams. One requirement, such as rack power plus cooling at a given density, may involve two teams.
- The workflow is heavier and must coordinate responses across units before consolidation.
- Not every data-centre bid needs every unit; the synthetic modular inference-pod sample may need fewer.

## 8. Capabilities: intended, proposed and implemented

Status labels: **Intended** is the workflow step or capability from the business direction. **Proposed design** is inferred design to support it (Proposed (inferred design)); it is not an approved technical design. **Implemented** is by code line only, and the claims have not been re-run for this documentation. The code lines are separate; they do not form one working system (section 10).

### 8.1 Workflow steps

| Workflow step or capability | Intended | Proposed design | Implemented, by code line |
|---|---|---|---|
| 1. Read and understand the RFP | Any format and length; every item keeps document, page and quoted text; unsupported files (CAD, macro spreadsheets) named and sent to engineering | Read-only ingestion with the language model used only for reading; scanned pages need OCR (optical character recognition) | v0.3.0: reads a real PDF or text; regex (pattern matching) by default; language-model path untested; clause splitting unreliable on the full 101-page PDF; no OCR. v1.0: anchored extraction shown on one synthetic case; plain text only. v1.1: reads no RFP |
| 2. Determine participation of business units | One, several or all units; not every bid needs every unit | A mapping of layers, brands and units to teams, producing a suggested participation list for a person to confirm | None. v0.3.0 scope detection (which product layers a bid touches, mapped to brands and teams) is a partial precursor only |
| 3. Support a human go/no-go decision | Evidence assembled; a named person decides; decision recorded | An evidence pack (scope fit, deviations, conflicts, open questions) and a decision record | None as defined. v1.1 gives BID/HOLD/NO_BID with a margin estimate over synthetic data (partial, different intent) |
| 4. Establish the opportunity workflow | Per customer and product mix; some steps mandatory, some configurable | Workflow templates selected per opportunity | None |
| 5. Break into requirements and work packages by team | Requirement-level assignment; one requirement may involve several teams | Requirement as the unit of work; work packages per team | v0.3.0: routes per layer (not per requirement) to four teams; payload adapters not wired; requirement registry (M17) not connected. v1.0, v1.1: none |
| 6. Track each team's response | Responses tracked against assigned requirements | A response record per requirement and team (form is open: narrative, estimation sheet, price?) | None. No estimation sheets in any line |
| 7. Consolidate into the final bid response | Complete traceability; every requirement answered or excluded | Links from each requirement to the parts of the final response | v0.3.0: coverage map built and connected (weak on full PDFs); proposal checker built but not connected. No consolidation in any line |
| Cross-cutting: Q&A, addenda, change requests | Captured against affected requirements; incremental change handling | Clarification entries linked to requirement IDs | Not built in any line |
| Cross-cutting: human review and audit | Approve, change, split or merge; immutable history | Side-by-side review; append-only audit log; frozen first-pass facts | v0.3.0: approve or reject only; reject ends the run; no edit; approvals editable, no immutable log. v1.0: edit, split, merge and a case-scoped event log in the data layer (unverified); three-panel UI never compiled. v1.1: none |

### 8.2 Supporting capabilities

| Workflow step or capability | Intended | Proposed design | Implemented, by code line |
|---|---|---|---|
| Source anchoring (provenance states) | Every value shows where it came from: `EXTRACTED` (verbatim), `DERIVED` (calculated), `UNANCHORED` (not found, never given an invented location). Serves steps 1, 5, 7 | Carried through assignment and response records | v0.3.0 and v1.0: built |
| Scope detection across six grid-to-chip layers | Input to steps 2 and 5 | Layer-to-brand-to-team map, to be reconciled with the business-unit list | v0.3.0: built; out-of-scope layers are wrongly drafted as `ETO_EXCEPTION` (defect). v1.0: not built (Phase 2) |
| Automation tiers | `CTO_AUTOMATE` (standard, can go to configuration and pricing tools), `ETO_GUIDED` (mostly bespoke: standard sub-parts handled, rest written up for a design engineer), `ETO_EXCEPTION` (fully bespoke: captured with a placeholder and sent to a specialist). CTO is configure-to-order; ETO is engineered-to-order. Input to steps 3 and 5 | Tier shown per requirement as evidence | v0.3.0: built, deterministic rules. v1.0: not built. v1.1: not applicable |
| Specification and engineering checks; solve or refuse | Simple standard items solved with cited references; bespoke items refused with a reason. Input to steps 3 and 5 | Same | v0.3.0: low-voltage arithmetic only |
| Deviation detection against past bids | What a new RFP requires that an earlier bid did not quote. Input to step 3 | Same | v1.0: built, tested on one synthetic case |
| Bid, execution and portfolio checks | Capacity, specification and timeline conflicts across customers; phase-to-phase changes needing an ECN (engineering change notice: formal approval of a design change). Input to step 3; later phases | Same | v1.1: three-stage demo, deterministic rules over synthetic, pre-structured data |
| Coverage map and proposal checker | Step 7 | Same | v0.3.0: see step 7 above |
| Isolation of concurrent bids | Two teams on unrelated RFPs cannot cross-contaminate | Case ID on every record | v1.0: case ID on every specification and event, not stress-tested. v1.1: case IDs per scenario |
| Pointer links to artefacts in other systems | Drawings, vendor specs, test reports linked from requirements; steps 5 to 7 | A read-only pointer index to the systems that own the files | None |
| Connectors to QuoteWin, SAP / Infor LN, aPriori | Boundaries open (section 5) | Read-only lookups and payload hand-off | Stubs only (PM-111: Integrations with downstream systems exist only as stubs) |

## 9. Expected value (hypotheses to measure)

**Nothing is measured.** The following are hypotheses, with no figures:
- fewer coordination delays between units and teams;
- fewer missed hand-offs;
- fewer unanswered requirements at submission;
- less rework from late-discovered requirements or changes;
- faster, more consistent and more accountable go/no-go decisions;
- clearer ownership;
- less time spent reading RFPs.

Testing them needs SpinCo historical bids (access is not yet agreed). Reading effort is one hypothesis among several. An earlier document held that the business case "rests on one unmeasured assumption": that reading and triage is a meaningful share of bid cycle time. That remains unmeasured; the idea of checking 20 to 30 past RFQs was proposed in the earlier documents.

**Superseded claims (do not use as results).** Earlier documents claimed a 100% catch rate, 928% return on investment (ROI) and $900K to $1.5M a year. These are retracted. On 23 September 2026 the demo script was run for the first time: it first failed to run and, once fixed, produced a 0% catch rate, $0 margin protected and -93% ROI on its one synthetic case. The release then dropped all catch-rate and ROI claims until they are measured on real SpinCo history (PM-108: Value is unproven: metrics were inflated then retracted; the business-case assumption is unmeasured). The only supported statement is that the mechanism caught the one deviation in the one synthetic case it was tested on.

## 10. Current status, by code line

These are separate code lines. They do not form one working system, none is a finished product, and all are proofs of concept. "Production Release" appears only as a package name. No line implements unit participation as a decision, workflow creation, team-response tracking, the three-view traceability, or final-response consolidation (PM-101: Layer 0's purpose was framed differently in each iteration, and the working direction is not yet formally signed off).

### 10.1 v0.3.0 bid-triage pipeline (`layer0-delivery/`)

- **Closest relation to the workflow.** Step 1: reads a real RFP. Partial precursor to step 2: scope detection maps product layers to brands and teams. Partial step 5: routes per layer to four teams. Partial step 7: coverage map; proposal checker built but not wired. Approve/reject gates only.
- **Not implemented.** Step 3 (no go/no-go output), step 4, step 6, consolidation into the final response, Q&A and addenda.
- **Package claim:** built, wired and tested, "verified end to end on the genuine 101-page Syracuse procurement PDF"; 78 tests passing. Syracuse is a real, public airport-authority RFP for 15 kV (15,000-volt) switchgear (electrical equipment that distributes and protects power).
- **Contradictory test and verification statements (flagged, not reconciled).** Different documents state 6, 21, 27, 37, 68 or 78 tests. "Verified end to end on the 101-page PDF" contradicts the code-level finding that clause splitting on that PDF is unreliable. Whether the 78-test suite passes on the team's machines is unconfirmed.
- **Code-level reading** (written after reading the code; it prevails where it differs from the package claim):
  - The default mode is "mock": no language model, regex and keyword counting, identical output on every run. A local-model path exists but has not been tested end to end (PM-103: Extraction runs on pattern matching (regex) by default; the language-model path is incomplete and untested).
  - Clause splitting on the full 101-page PDF is unreliable: table-of-contents headings become requirements (PM-107: Requirement extraction is incomplete (commercial, legal and staffing missed; clause splitting unreliable; no OCR)).
  - Built and wired: ingestion, extraction, scope detection, tiering, validation, solver, provenance, coverage map, six-stage pipeline with approval gate, frontend. Built but not connected: requirement registry (M17), proposal checker (M15), routing payloads (M8). Connectors are stubs (PM-102: v0.3.0 build status is overstated and several modules are not wired in; PM-111).
  - Not built: OCR; live connectors; addenda handling; human edit, split or merge; side-by-side review; team estimation sheets; an immutable audit log (PM-106: Reviewers cannot edit, split or merge results; first-pass facts are not frozen; there is no immutable audit log).
  - Known defect: out-of-scope layers are drafted as `ETO_EXCEPTION`.
  - Provenance of the code: built with AI coding tools; some modules were reported as disconnected in the review meetings (Needs confirmation); one git commit and no real version control (PM-110: Code versions and documents are fragmented and contradictory (no version control)).
- **Demo:** three acts in mock mode: a solvable bid (a 45 kVA, or kilovolt-ampere, power-supply installation), a refused bid (the Syracuse switchgear) and a 47-clause coverage map. Sources give different tier results for Syracuse: the demo runbook expects layer 2 `ETO_GUIDED` and layer 3 `CTO_AUTOMATE`; the pre-brief deck shows layers 1 to 2 only; the code review says the 22 Sep run put only layer 2 in scope. Flagged as a contradiction (Needs confirmation).
- **Risks not retired:** volume; real connectors; whether the tier split is economically correct; whether physical checks catch what an engineer would; local-model inference.

### 10.2 22 Sep fresh codebase and v1.0 extraction-and-governance release (`Scatttered Documents/`)

- **Closest relation to the workflow.** Step 1: anchored extraction, shown on one synthetic case. Deviation check against a past bid (input to step 3). Case-scoped event log, override tracking and correction learning (cross-cutting; built but unverified). Edit, split and merge in the data layer (unverified). The three-panel UI was never compiled.
- **Not implemented.** Steps 2, 4, 5, 6 and 7.
- Mechanism "verified by actually running it", "tested against one detailed case", "not validated against real SpinCo data". The v1.0 talking points tell presenters to say exactly that: "one detailed synthetic case built on a real public RFP". The demo ran clean on 23 Sep 2026.
- Not in the package: scope detection, tier classification, validation rules and production PDF ingestion (Phase 2); any measured catch rate or ROI; traceability to CAD files, vendor specifications, test reports or email; a portfolio view.
- The Syracuse story in the sales material (a 2024 bid that missed an arc-resistance requirement and a "$300,000" change order) is **illustrative**: the RFP is real and public, while the past bid, the miss and the dollar figure are constructed. Whether SpinCo or any brand ever bid on it is not stated.

### 10.3 v1.1 three-stage decision demo (`CPQ/`)

- **Closest relation to the workflow.** Partial step 3: BID/HOLD/NO_BID with a margin estimate. Execution-stage change check (ECN); portfolio conflict check. All deterministic rules over synthetic, pre-structured data; no RFP is read (PM-104: The v1.1 demo reads no RFP and runs on synthetic, placeholder data).
- **Not implemented.** Steps 1, 2, 4, 5, 6 and 7.
- One command runs three scenarios in about a millisecond: a utility bid (BID, 92% confidence, 18% margin), a hyperscaler phase change (ECN required, phase 3 locked) and a cross-customer portfolio conflict (recommendation: decline the neocloud). The review meeting of 5 Oct described the backend as one endpoint reading JSON (structured data) files from a folder (Needs confirmation).
- Several constants (a 32-week lead time, per-customer margins, decision deadlines, risk ratings) were invented to make the data resolve to the expected outputs; they await calibration. Scenario figures are inconsistent across sources and are not facts.
- **Contradictory statements (flagged).** Claimed: 6 of 6 QA tests pass; success criteria 7 of 9 fully met, 2 with caveats (frontend click-through not verified in a browser; some documents not produced). The sign-off calls it "production-ready"; this documentation treats it as a proof of concept. The package says it was built fresh with "no prior v1.0 codebase", although the plan assumed 90% reuse.
- Whether the synthetic customer and product pairings match SpinCo's real segments is unconfirmed (PM-109: The demo cases are illustrative and do not match SpinCo's customer types).

### 10.4 Documents and code baseline

Documents and code are fragmented and contradict each other, with no version control (PM-110). A consolidation was decided on 5 October (section 13). Which code line is the base for further work is not yet decided.

## 11. How the idea evolved: history

**These sections describe earlier iterations and existing builds. They are not the current direction.** The current direction is the opportunity-management workflow in sections 2 and 7. Earlier framings are kept so that developers can understand the existing code and documents, each of which was written under one of them.

### 11.1 Earlier framings

| Dated | Framing | What it described | Status |
|---|---|---|---|
| Early Sep 2026 | **Agentic CPQ** | An LLM reads the RFP, drafts a design across SpinCo's six-layer product stack, validates cost and margin, routes to teams and assembles the proposal | Explicitly superseded when the system was "repositioned from 'a CPQ' to 'the layer in front of one'" |
| 21 to 22 Sep 2026 | **Bid intake, triage and routing** (v0.3.0) | "The layer before" CPQ: read, classify into three tiers, solve or refuse, route; never a price or quote | Documented and partly built |
| 22 to 23 Sep 2026 | **Intake and specification anchoring in front of the customer's CPQ** (v1.0) | Anchored extraction plus a check against the customer's past bid; flag deviations before submission | Documented; one synthetic case demonstrated |
| 23 Sep 2026 onward | **Portfolio-risk intake** (v1.1) | Bid-stage, execution-stage and portfolio-stage decision support, so that simultaneous commitments across customers do not conflict | Demo over synthetic data |

The opportunity-management workflow described in the review meetings (22 Sep and 5 Oct 2026) is the working baseline and succeeds these framings for purpose and workflow. Formal sign-off has not been given. How much of the v1.1 portfolio and execution-stage checks stays in Layer 0 is open (they are input to step 3 and later phases).

**Common core** shared by all framings, and still valid: read the bid; identify requirements with their source; decide what can be automated or committed; route the work to the right people; keep humans accountable.

### 11.2 Why the framing changed

- 22 September: an alignment audit found that documents promised a six-stage pipeline while the code delivered about half (self-assessed). The team rewrote the documents to match the code instead of building the missing stages.
- 23 September: research found that hyperscalers sign direct framework contracts with a single vendor instead of competitive RFPs, so a tool that only handled bid intake missed execution-stage and portfolio-stage risk. The figures offered ("$100M" at risk; contracts of "$115M to $720M" with named companies) are unverified claims.
- Value claims were withdrawn the same day (section 9).
- 5 October: the review meeting described the opportunity-management workflow and found the three-way traceability view missing from the demo.

### 11.3 Code lines and precursors

1. **v0.3.0 bid-triage pipeline** (`layer0-delivery/`): committed 21 Sep 2026; a 0.3.1 documentation pass followed on 22 Sep. Six-stage pipeline, modules M1 to M17 (no M12), 78 tests claimed.
2. **22 Sep fresh codebase**: a clean-slate restart after four requests (focus on problem and solution; fresh code; use an LLM, not regex; restore the Google datacentre sample RFP). It began as data models plus LLM extraction and grew the same day into governance, requirement lifecycle, a three-panel UI and a backtest. It is smaller and different from line 1 and should not be merged with it.
3. **v1.0 extraction-and-governance release** (23 Sep 2026): the packaged result of line 2.
4. **v1.1 three-stage decision demo** (`CPQ/`, release folder dated 24 Sep, parent folder 28 Sep): says it was built fresh with "no prior v1.0 codebase".

Whether `layer0-delivery/` is the newest "enhanced" 17-module version is also unconfirmed.

### 11.4 Chronology

| Date (2026) | Event |
|---|---|
| Early Sep | "Agentic CPQ" framing and alpha |
| 21 Sep | v0.3.0 committed |
| 22 Sep | v0.3.1 documentation pass; documents v1 archived, v2 and v3 active; Logik.io research corrected; "78 tests" and "6 stages" replace "27" and "5"; the code was packaged twice, as a full "Original Track" development kit (v0.3.0, with source and sample RFPs) and a lean "Complete Delivery" reference package (v0.3.1) |
| 22 Sep | Fresh restart; alignment audit; four gaps built (governance, lifecycle, three-panel UI, backtest); internal archive separated from a team-facing release |
| 22 Sep | Review meeting 1: no working demo; opportunity-management workflow direction described |
| 23 Sep | v1.0 packaged; first real demo run; all catch-rate and ROI claims withdrawn; revision log declared the source of truth for "which file is current" |
| 23 Sep | Pivot to portfolio-risk intake; v1.1 rewrite planned (about 22 hours estimated) |
| 24 and 28 Sep | v1.1 release folder and parent folder dates |
| 5 Oct | Review meeting 2: v1.1 reviewed; three-way traceability screen missing; decision to consolidate documents before more code |

## 12. Roadmap and next steps (Proposed, per code line)

Every item below is **Proposed**, and it is organised **per code line**. The roadmaps were written under earlier framings and the sources define "Phase 2" and the version after each package differently, so no single roadmap is declared current. No roadmap yet targets the workflow in section 7 as a whole; which code line is the base, and which roadmap the team follows, needs confirmation. A Proposed (inferred design) direction for workflow work is stated at the end.

### 12.1 v1.0 line: Phase 2 (4 weeks, "assuming access to real SpinCo historical RFP data")

1. Weeks 1 to 2, scope detection: decide which of six infrastructure layers an RFP touches so the system does not draft requirements for layers the customer never asked about. The two sources list different six-item taxonomies (one: Grid, HV, MV, LV, Distribution, Load, where HV, MV and LV mean high, medium and low voltage; the other: power distribution, cooling, enclosure, controls, grounding, logistics); neither is the grid-to-chip product stack in the business background document.
2. Weeks 2 to 3, tier classification into the three tiers using per-brand defaults and keyword overrides; when several brands could apply, the most conservative tier wins.
3. Weeks 3 to 4, a validation rules engine (voltage consistency, cooling capacity, redundancy, standards bounds) and a production PDF pipeline that keeps page and character positions.
4. Also Phase 2 but unscheduled: a real backtest ("the highest-priority item, not a nice-to-have"); a traceability index with read-only links to the product-lifecycle, document and quality systems that own CAD files, specifications and test reports (whether this is in Phase 2 is inconsistent across sources); a concurrency stress test and a policy for two people editing one requirement; a portfolio and workload view.
5. Excluded from Phase 2: CAD, vendor-specification, test-report and email traceability beyond the index; live QuoteWin, SAP and aPriori integrations (need credentials); OCR for scanned pages.

### 12.2 v1.1 line: v1.2, v1.3, later "Phase 2"

1. **v1.2 (about 4 weeks):** backtest on 5 to 10 real SpinCo historical RFPs across the three scenario types; calibrate every placeholder constant; refine conflict detection; measure catch rate and margin protection on real data. Preceded by sharing v1.1 with SpinCo and requesting the historical RFPs.
2. **v1.3 (about 4 to 6 weeks):** production PDF ingestion; connection to SpinCo ERP and CRM systems; alerts and a dashboard for portfolio risk. (One v1.1 source places PDF ingestion in v1.2.)
3. **"Phase 2 (to be decided)":** integrate with the bid process (go and no-go automation); extend to other product lines (Embedded Power, Thermal Management); plan with SpinCo executives.

### 12.3 v0.3.0 line: steps suggested in the team's code review (priority needs confirmation)

1. Rebuild a clean Windows baseline, run the tests and the three demo acts in mock mode, and put the code under version control.
2. Connect a real language model (a local one or a cloud one), temperature 0, keeping mock mode for demos.
3. Fix the first-stage prompt so it returns all regex fields.
4. Build the side-by-side review (source left, extraction right, approve, edit or reject, with edits recorded).
5. Make the requirement the unit of work (connect the requirement registry; extend extraction beyond technical fields).
6. Fix the out-of-scope drafting defect; add an append-only audit log separate from editable state; freeze the first-pass extraction.
7. Later: a second language-model check, addenda handling, routing payloads, connect the proposal checker.

### 12.4 Workflow steps not covered by any roadmap (Proposed (inferred design))

Steps 2, 3 (as a recorded human decision), 4, 6 and the final-response consolidation in step 7 appear in no existing roadmap. Once the baseline and the remaining decisions are settled, the next demo could be scoped around one opportunity carried through steps 1 to 7 on a single code line. Its acceptance criteria are an open decision (section 14, item 1).

### 12.5 Exit criteria for a pilot and for production (from earlier plans)

- **Pilot may proceed when:** the system can take in 5 to 10 real historical RFPs as plain text; extraction with source anchors is spot-checked by a SpinCo engineer; case isolation holds (not yet stress-tested); and a catch rate is measured on real data, as the pilot's first deliverable, "measured, not assumed".
- **Production may proceed when:** scope detection, tiering and rules are wired end to end; a backtest on 10 or more real cases gives a catch rate that SpinCo leadership "is willing to stand behind"; production PDF ingestion replaces plain text; and a documented answer exists for two people editing one case.
- **Not required for the pilot:** CAD and email traceability; live integrations; a portfolio dashboard.
- Everything is gated on real data. Pilot size differs by source: 5 to 10 RFPs, 5 or more, 10 to 20.
- Older pilot conditions with cost and ROI figures are superseded.

## 13. Decisions

### 13.1 Confirmed decisions (the only two confirmed in the meetings)

1. **Call it a PoC or pilot, not a product.** Agreed in the 22 Sep and 5 Oct 2026 reviews: calling it a product implies a finished solution. Consistent with the written sources.
2. **Consolidate the documents before more coding.** The team uses an LLM to go through all existing documentation in batches and produce one reviewed final version. This documentation set is that consolidation.

Smaller meeting agreements (22 Sep): use the sample RFP already in the app instead of pasting the PDF; share the "enhanced version" of the build through Teams; meet again the next day.

### 13.2 Decisions recorded in the written sources (earlier iterations)

- 22 Sep: rewrite the documents to match the code instead of building the missing stages.
- Build a fresh codebase covering all six gaps an expert panel found, instead of patching.
- Isolate every RFP as its own case so concurrent bids cannot contaminate each other.
- 23 Sep: withdraw all catch-rate and ROI claims until measured on real data; present Syracuse as illustrative.
- Keep a revision log of current and superseded files; never silently overwrite or delete a superseded file.
- Reframe from bid intake to portfolio-risk intake. This was a recorded decision under an earlier framing; the working baseline now is the workflow in section 7.

### 13.3 Review-meeting expectations (Expected (review meetings); formal sign-off pending)

- Layer 0 is not a collaboration tool.
- Each requirement gets an ID, is classified and routed, and each team responds, possibly on an estimation sheet (form open).
- A final check confirms every customer requirement was answered; clarifications update requirements.
- Humans review changes side by side: the language model has no authority to change a result, but a person does. Approval is step by step. Fine-tuning a model is rejected as too expensive; the system is to be trained through rules, not the model, and not through retrieval-augmented generation (RAG). Temperature 0 and an immutable first-pass fact set.
- Decide which of "six companies" respond, go or no-go, create the workflow, keep three-way traceability, handle changes incrementally with a fixed plan and a new opportunity for a drastically changed RFP.
- The PoC does not yet meet these expectations: v0.3.0 triages per layer with no editing or estimation sheets; v1.1 runs over synthetic data.

### 13.4 Ambiguities in the review-meeting content

- "Six companies" (one passage transcribed as "76"), and how these map to brands, pillars and teams (four pillars and seven brands appear in written sources).
- "$7 billion", against $6.6B FY26 revenue in written sources.
- A "January 4" start, with no year given.
- The phrase "pre-RFI bid response system", against the RFPs actually processed.
- Whether estimation sheets or prices are in scope.
- How change requests are applied incrementally.
- Whether bid/no-bid output is a deliverable or only decision support (working baseline: support).

## 14. How the documents relate

- This document gives the project view.
- [business-and-domain-background.md](business-and-domain-background.md) explains Flex, SpinCo, how engineered products are sold, what CPQ does and a worked RFP example. Read it first if terms such as ETO, CPQ or switchgear are new.
- [problem-mapping.md](problem-mapping.md) lists each business problem (PM-001 to PM-017, grouped as core workflow, supporting capabilities, and commitments, capacity and volume) and each PoC or project problem (PM-101 to PM-111) with impact, solution options and success criteria. The identifiers were created for documentation traceability only.
- [architecture-overview.md](architecture-overview.md) explains the modules, stages and data flow of each code line and where Layer 0 sits next to existing systems.
- [technical-architecture.md](technical-architecture.md) is the build design for the next version: how an RFP is read into anchored requirements (PyMuPDF, pdfplumber, Tesseract OCR), the data model, the workflow modules, change handling, the views and the build order.
- Original files are kept unchanged. Where a source is superseded (earlier "agentic CPQ" documents, all catch-rate and ROI figures, the original problem and solution documents), this document describes it only as history (section 11).
