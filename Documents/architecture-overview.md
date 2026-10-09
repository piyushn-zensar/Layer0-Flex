# Layer 0 Architecture Overview

## Purpose

This document gives a newly joined developer one conceptual picture of the Layer 0 architecture. It covers the workflow Layer 0 is meant to support, the architecture proposed to support it, what the four existing code lines actually do today, the external systems involved, how the earlier framings relate, and what remains open. It describes components, responsibilities, flow and status. It does not describe code.

Layer 0 is a proof of concept (PoC: a small build that tests whether an idea works; it is not a product) for SpinCo, the existing Flex business being spun off as Axiom Solutions. Its intended purpose is to help the business manage an incoming bid opportunity, from the moment a request for proposal (RFP) arrives until the final bid response is assembled. It should:

- help understand the RFP;
- determine which business units need to take part;
- support a human go/no-go decision;
- set up the workflow for that opportunity;
- break the RFP into requirements and work packages owned by the right teams;
- track each team's response;
- bring the responses together into a final response that traces back to every original requirement.

This workflow is the business direction described in the review meetings (22 Sep, 5 Oct and 8 Oct 2026) and is used as the working baseline. It has not been formally signed off, and no existing build implements it end to end. The review of 8 Oct 2026 added concrete direction (three screens, roles, an agentic process, retrieval) and made the Git repository **Layer0-Flex** the single code base; it is a skeleton only on that date. The architecture assumes that EP² (Electrical Power Products) is already part of SpinCo / Axiom Solutions (written direction from the Zensar point of contact), and the design includes solution components coming from EP².

## Who This Is For

Developers who have just joined the Layer 0 PoC and who have no electrical-engineering or Flex background. Business background is in [business-and-domain-background.md](business-and-domain-background.md); the project story is in [project-overview.md](project-overview.md); the problems this architecture must address are in [problem-mapping.md](problem-mapping.md).

## Scope

- Included: the system boundary, the intended workflow, the proposed architecture for it, shared design principles, an inventory of what each existing code line does, external systems, history and constraints.
- Not included (deferred to the Technical Architecture documents): field-level data schemas, programming-interface (API) endpoint lists, configuration switches, commands, code sketches, build and reuse plans, runbooks, changelogs.

Four status categories separate the content of this document. They are never mixed within a statement.

| Category | Meaning | Where it appears |
|---|---|---|
| **Intended workflow** | The business direction from the review meetings; the working baseline. Individual points are labelled **Expected (review meetings)** | Purpose, system boundary, the traceability chain |
| **Proposed design** | Architecture to support the workflow. Not established by any source unless stated. Labelled **Proposed (inferred design)** | "Proposed Architecture for the Intended Workflow" |
| **Implemented (by code line)** | Only what a code line actually does, with its caveats. The lines are separate and are never one working system | "Implemented Today" |
| **Open decisions and gaps** | What is not decided, contested or unverified; includes **Needs confirmation** items | Throughout |

The review meetings are not evidence that anything is built. Hypothesised benefits (fewer coordination delays and missed hand-offs, fewer unanswered requirements at submission, less rework from late-discovered requirements or changes, faster and more accountable go/no-go decisions, clearer ownership, less time spent reading RFPs) are hypotheses to measure. None has been measured; earlier catch-rate, savings and return-on-investment figures were retracted and are not used. Measuring the hypotheses needs SpinCo's historical bids.

Four code lines exist, named by version and folder: the **v0.3.0 bid-triage pipeline** (`layer0-delivery/`), the **22 Sep fresh codebase**, the **v1.0 extraction-and-governance release** (23 Sep, the release of the fresh codebase), and the **v1.1 three-stage decision demo** (`CPQ/`). In `Scatttered Documents/` the 22 Sep codebase and v1.0 form one line.

## Terms Used in This Document

| Term | Meaning |
|---|---|
| **Opportunity** | An incoming bid (from an RFP, RFQ or RFI) that the business considers pursuing |
| **Business unit** | An organisational unit of SpinCo / Axiom Solutions that sells and delivers products. The review of 8 Oct 2026 spoke of six business units and named EP² as one. The working list is Anord Mardix, Crown Technical Systems, EP², Flex Power Modules, JetCool and Cloud (in-house); the exact list is Needs confirmation. EPC Power stays "pending acquisition" and is not active. Business units are data in the system, so the list can change without code changes |
| **Bid manager** | The one person with a general idea of all the business units, who receives the RFP and owns the opportunity (8 Oct 2026) |
| **Product manager** | The person in a business unit who knows its product offerings; each unit has one (8 Oct 2026) |
| **Design engineer** | The person in a business unit who states, per requirement, whether it is met and with what; each unit has one (8 Oct 2026) |
| **Line item** | One requirement from the RFP as one row, with a unique requirement ID that traces back to its source, for example "page 5, lines 6 to 8" |
| **Offering type** | How a unit would meet a requirement. **CTO** (configure-to-order): a base model with options chosen, handled by CPQ. **Semi-custom**: a configured product plus extra workshop work. **ETO** (engineered-to-order): no existing product, designed to the customer's requirements. Earlier tiers: `CTO_AUTOMATE` is CTO; `ETO_GUIDED` is semi-custom (guided ETO); `ETO_EXCEPTION` is ETO |
| **BOM reference** | A pointer to the bill of materials (BOM: the parts list of a product) held in a separate system. Layer 0 reads and shows it on screen 3; it does not construct it. The BOM source system is Needs confirmation |
| **Brand** | An acquired company name, for example Anord Mardix, Crown, EP², Flex Power Modules, JetCool, EPC Power (acquisition pending), Cloud. EP² is part of SpinCo (written direction from the Zensar point of contact); brand assignment of the others stays inferred until the Form 10 |
| **Product pillar** | Critical Power, Embedded Power, Thermal Management, Cloud |
| **Product layer** | One of the six grid-to-chip layers, L1 to L6. "Six layers" is not the same as the six business units; there is no one-to-one mapping |
| **Team** | The group that owns and answers requirements. The v0.3.0 knowledge base uses four: Critical Power, Embedded Power, Thermal (JetCool), Cloud |
| **Requirement, sub-requirement, work package, assignment, team response, final bid response** | The items tracked through the workflow. A work package is a group of requirements assigned to a team |
| **Go/no-go decision** | A human decision on whether to bid. Layer 0 supports it; it does not make it |

The word "layer" has two meanings. The six-layer **grid-to-chip stack** (L1 grid interface, L2 facility electrical, L3 power distribution, L4 rack and board power, L5 thermal management, L6 compute and integration) describes SpinCo's products. "Layer 0" names the system placed in front of all of that. One older document uses "Layer 0 / 2 / 3" for architecture tiers; another lists the six layers as "Grid, HV, MV, LV, Distribution, Load" (HV, MV and LV: high, medium and low voltage) (Needs confirmation).

## Where Layer 0 Sits (System Boundary)

### The opportunity, from RFP arrival to final bid response

An RFP is the customer's formal document asking suppliers how they would meet a need and at what cost. Layer 0 is intended to cover the life of one opportunity from the moment the RFP arrives until the final bid response is assembled: understand it, decide who participates, support the go/no-go decision, set up the opportunity's workflow, split the RFP into team-owned work, track the responses, and consolidate them with full traceability.

The intended workflow has seven steps (status: Intended). Since 8 Oct 2026 it is deliberately simple: the bid manager sends each participating business unit its part (the main RFP plus its requirement line items) in one dispatch step; the unit's product manager and design engineer complete it; responses flow back to the bid manager, who assembles the comprehensive response. The idea is different groups writing different chapters of one proposal.

1. **Read and understand** the RFP. Every extracted item keeps an exact source reference: document, page and quoted text.
2. **Determine participation**: whether one, several or all relevant business units need to take part. Not every data-centre bid needs every unit.
3. **Support a human go/no-go decision.** Layer 0 assembles the evidence (scope fit, deviations, capacity or portfolio conflicts, open questions). A named person decides, and the decision is recorded.
4. **If go, establish the workflow** for that opportunity. Different customers and product combinations need different workflows; some steps are mandatory, some configurable.
5. **Break the RFP into requirements (line items) and work packages** assigned to the appropriate business units. One requirement may involve several units. Dispatch is one step.
6. **Track each unit's response** against its assigned requirements. The response is a checklist per requirement (the design engineer states that it is met, and with what), followed by validation. The system tracks which units have responded.
7. **Bring the responses together** into the final bid response with complete traceability, and check that every requirement is answered or explicitly excluded.

Cross-cutting at every step: human approval and accountability; an audit history of decisions and changes; handling of clarifications (customer questions and answers), addenda and change requests against the affected requirements; concurrency (several RFPs and people at once; requirement IDs unique across opportunities; a workspace per engagement); and append-only retention of all opportunity data for the life of the project and beyond, because warranty clauses apply (8 Oct 2026). The review meetings described incremental handling of change requests, with a drastically changed RFP treated as a new opportunity (Expected (review meetings)).

### The traceability chain and three screens

The chain is: **Original RFP requirement → line item with requirement ID → product mapping → business-unit response → final bid response.** The review meetings described three connected views, and the review of 8 Oct 2026 made them three screens that are central to the demo (Expected (review meetings)): (1) the original RFP; (2) the requirement breakdown, with spreadsheet-like line items, each with a unique requirement ID tracing back to its source; (3) the requirement-to-product mapping, showing against each requirement ID the product or configuration that will meet it, with BOM-level detail and the offering type. The BOM itself is read from a separate system. The **requirement** is the main tracked item. It keeps its source reference, its sub-requirements, the participating team or teams, each team's response, and the parts of the final response that answer it.

### Downstream systems: boundaries are uncertain

Other systems may support work after or alongside Layer 0: configure, price, quote (CPQ: software that lets a salesperson pick valid options and get a price; Logik.io with Salesforce), costing (aPriori), quoting (QuoteWin), business systems (ERP: core systems for orders, inventory and finance; SAP and Infor LN), product-data systems, and engineering teams. The integration boundaries are **uncertain and open**: what Layer 0 hands off, what it reads back, and whether opportunities are created in a customer-relationship-management (CRM) system.

Background: a traditional CPQ starts "at the moment a human has finished reading the RFP and decided what kind of job it is. That moment is the gap." In the 12-step quote-to-cash process (first customer request through delivery), CPQ covers steps 3 to 8; the earlier steps (capture and qualify the demand) are where Layer 0 sits. Steps after that (order entry, engineering release, manufacture, delivery) belong to other systems.

```text
  Customer RFP (PDF, spreadsheets, drawings, email)
        |
        v
+--------------------------------------------------------------+
| LAYER 0 (intended): understand the RFP, decide participation, |
| support go/no-go, set up workflow, assign requirements to     |
| teams, track responses, consolidate with traceability         |
+--------------------------------------------------------------+
        |  hand-offs and read-backs: boundaries UNCERTAIN
        v
  CPQ / configurator (Logik.io with Salesforce)   <- configure, price, quote
  Costing (aPriori)                               <- should-cost
  Quoting (QuoteWin)                              <- quote record
  Business systems (SAP, Infor LN), CRM, product data, design vaults
  Design engineers and specialist teams           <- bespoke work
```

### What Layer 0 is and is not

- It is: an opportunity-management workflow for incoming bids; an ingestion and understanding layer for unstructured RFPs; a requirement tracker that ties every requirement to its exact source, its owners, their responses and its place in the final response; decision support; an evidence layer.
- It is not: a configuration engine, a pricing engine, a bill-of-materials (BOM: the parts list of a product) generator (the finished BOM lives in a separate system and Layer 0 only reads and shows it), a quote generator, a CAD (computer-aided design) tool, an ERP replacement, a replacement for Logik.io, Salesforce, QuoteWin, SAP or aPriori, or an autonomous engineering designer or proposal writer. It is not required to be a general-purpose collaboration platform.
- Whether per-team estimation sheets or any price or margin figures belong inside Layer 0 is an **open scope question**. Earlier documents say Layer 0 never produces a price; the review meetings mention estimation tables; v1.1 produced margin estimates on synthetic data.

### Illustrative examples (not recorded SpinCo bids)

- **Single-unit opportunity.** A standalone medium-voltage switchgear RFP, like the public Syracuse airport switchgear RFP used in the PoC. Likely Crown Technical Systems participates (arc-resistant medium-voltage switchgear), and possibly EP² (relay and protection panels); the matcher proposes this and a person confirms. A light workflow: engineering review of requirements such as arc-resistant Type 2B, plus commercial and compliance items. Go/no-go turns on scope fit and deviations. Every requirement still traces to its owning team and its answer in the final response.
- **Multi-unit opportunity.** An AI data-centre campus RFP, like the synthetic 48 MW hyperscale-campus sample. It may need Anord Mardix (facility power and switchgear), Flex Power Modules (rack and board power), JetCool (liquid cooling), Cloud (compute integration) and possibly EP² for substation control, so several business units. One requirement, such as rack power plus cooling at a given density, may involve two teams. The workflow is heavier and must coordinate responses across units before consolidation. The synthetic modular inference-pod sample may need fewer units.

## Scope Boundaries

1. Tracking team work is part of Layer 0. It does not require Layer 0 to be a general-purpose collaboration platform.
2. Linking and consolidating team responses does not mean autonomous proposal writing. People write the responses.
3. Supporting go/no-go does not give the model decision authority. A person decides and is recorded.
4. CPQ, costing, quoting, ERP, product-data systems and engineering teams may support downstream work, but the integration boundaries are uncertain: what is handed off, what is read back, and whether opportunities are created in a CRM.

Open scope question (not a boundary): whether estimation sheets or price or margin figures belong in Layer 0.

## Proposed Architecture for the Intended Workflow

Everything in this section is **Proposed (inferred design)** unless stated. It is architecture to support the intended workflow. No source establishes it, and nothing here exists as one working system. Where a component has a partial precedent in an existing code line, that is noted; the precedents live in different, separate code lines and do not work together.

### Model gateway principle

**Agents propose; people decide; the first pass is frozen; later runs handle only the delta.** A language model (LLM: software that generates text from text) is called from one place only (a gateway), and agents (steps run by a model) use it. Agents may read RFP text, identify requirements, propose product matches, route work, track responses and draft consolidations for human review. They never decide participation, decide go/no-go, change a requirement, freeze a baseline or accept a response; named people do those and are recorded. Agentic runs give different answers each time, so the control is: the first run is reviewed by a person, then **frozen** as the specification baseline, and later runs process only the delta (change requests). Expected (review meetings): the model has no authority to change a requirement; a person does.

### Flow

```text
 (a) RFP intake + source references
          |

 (b) requirement identification + decomposition  <--- model gateway; model-based,
          |                                           anchors verified (no regex)
 (c) product matching against business-unit offerings (RAG)
          |        -> business unit, product, offering type; BOM reference
          |
 (d) go/no-go decision record  <--- named person decides; evidence assembled
          |  (go)
 (e) opportunity workflow creation + work assignment
          |
 (f) team-response tracking
          |

 (g) coverage check + traceability into final response
          |
     final bid response (people write; Layer 0 links and checks)

 Three screens (Expected, 8 Oct 2026): (1) original RFP; (2) requirement
 breakdown (line items with IDs); (3) requirement-to-product mapping
 (offering type, BOM detail read from the BOM source).

 (j) product and past-response knowledge base (RAG) --- feeds (c)

 Cross-cutting, at every step:
 (h) audit history of decisions and changes
 (i) clarification / addendum / change-request handling
     (feeds back into (b), (c), (e), (f), (g))
```

### Components

**(a) RFP intake and source references.** Accepts the RFP package (PDF, spreadsheets, drawings, email) page by page and keeps an exact source reference for everything later derived: document, page and quoted text. Reports unreviewed regions (for example pages with no text layer) instead of silently skipping them. Partial precedent: v0.3.0 ingestion (reads a real 101-page PDF) and v1.0 anchored extraction (shown on one synthetic case).

**(b) Requirement identification and decomposition.** Identification is model-based, on top of deterministic layout reading, with every anchor verified against the page text. Regex (pattern matching) is rejected: it turned table-of-contents entries into requirements and used about 100,000 model tokens. The choice of PDF tooling is not the client's concern; the quality of the result is. Each requirement becomes a line item with a unique requirement ID. It turns RFP text into individually identified requirements and, where needed, sub-requirements, each linked to its source reference and carrying a provenance class: `EXTRACTED` (found verbatim), `DERIVED` (calculated by a rule from other values), `UNANCHORED` (could not be located; always shown with a warning). Includes the first-pass fact set, which is frozen so later runs refer to it. Commercial, legal and staffing requirements are in the target granularity only if that decision (granularity) is confirmed. Partial precedent: v0.3.0 extraction and requirement registry (M17, built but not wired); v1.0 specification model and edit, split and merge in the data layer (unverified). Both have documented weaknesses (see the inventory).

**(c) Product matching against business-unit offerings.** Maps each requirement against the product offerings each business unit carries, using retrieval (RAG: supplying the model with retrieved reference text) over component (j). The result per requirement is a business unit, a product or configuration, and an **offering type**: CTO, semi-custom or ETO (the earlier tiers `CTO_AUTOMATE`, `ETO_GUIDED` and `ETO_EXCEPTION` map to these in that order). An RFP may involve one or more business units, and a requirement may map to more than one. The business-unit list is data, so it can change without code changes. Where a BOM exists, a BOM reference is attached from the BOM source system. Matching proposes; a person confirms. Evidence checks (for example low-voltage arithmetic) are reused from earlier lines. Partial precedent: v0.3.0 scope detection and tiers, which route per layer to four teams, not per requirement and not per business unit.

**(d) Human-reviewed go/no-go.** Assembles the evidence a person needs: scope fit, deviations against past bids, specification and engineering check results, capacity, specification or timeline conflicts with other opportunities, open questions. Records a **decision record**: who decided, when, the outcome, the evidence shown and any stated rationale. The model has no authority here; output is decision support, not a decision. Partial precedent: v1.0 deviation check against a past bid; v1.1 bid, hold or no-bid recommendation with a margin estimate on synthetic, pre-structured data. Neither reads an RFP in the v1.1 case, and neither records a named human decision.

**(e) Workflow creation and work assignment.** Dispatch is one step: the bid manager sends each participating unit the main RFP plus the requirement line items assigned to it. On a go decision, creates an opportunity-specific workflow from templates chosen by customer type and product mix. Some steps are mandatory, some configurable. Creates assignments: requirements and work packages to one or more teams, with owners and due points. Open: which templates exist, which steps are mandatory. Partial precedent: v0.3.0 routing groups layers into work packages for four teams (adapters not wired). No line creates a workflow.

**(f) Team-response tracking.** The response works as a checklist per requirement: the unit's design engineer states that it is met, and with what, and someone then validates it. The system tracks which units have responded. Records, for each assignment, the responsible team's response (whether a narrative, estimation sheet or price is also needed is not decided), its state (not started, in progress, submitted, accepted, rejected or excluded with reason), and who responded. Keeps a view of outstanding items per team. It tracks and links; people write the responses. No line implements this.

**(g) Coverage checking and traceability into the final response.** Builds the three connected views (original RFP, breakdown and assignment, team responses) and links each requirement to the parts of the final response that answer it. Checks that every requirement is answered or explicitly excluded, and flags requirements with no response, no assignment or no final-response reference. Compares a returned proposal with the RFP. Partial precedent: v0.3.0 coverage map (weak on full PDFs) and proposal checker (built, not wired). Consolidation of responses into a final response has no precedent.

**(h) Audit history.** An immutable, case-scoped record of decisions and changes across all steps: extraction results, edits, participation, go/no-go, assignments, responses, approvals, change requests. It answers who changed what, when and why. Partial precedent: v1.0 event log (unverified). v0.3.0 stores approvals in editable state, not an immutable log.

**(i) Clarification, addendum and change-request handling.** Customer questions and answers, addenda and change requests are captured as new or updated requirements linked to the requirements they affect, and the affected assignments, responses and final-response parts are flagged for re-review. Changes are applied incrementally; the model does not regenerate everything. If a change is so large that the RFP changes completely, the opportunity restarts as a new opportunity. The first run is frozen as the baseline and later runs process only the delta. How the delta is applied in detail is unresolved. No line implements this.

**(j) Product and past-response knowledge base (RAG).** All product details of the business units, and their past RFP responses (each unit has answered dozens of RFPs), are placed in a retrieval knowledge base. The data is also saved in a database, with a connector that feeds the knowledge base. It serves component (c). This updates the 5 Oct statement that the system is trained through rules and not RAG: RAG is now expected for product knowledge and past responses. Fine-tuning is still not used.

### The requirement as the main tracked item

```text
 REQUIREMENT  (unique identifier across all opportunities, status, audit history)
 |
 +-- source reference: document, page, quoted text (exact)
 |
 +-- sub-requirements (optional, each with its own source reference)
 |
 +-- product mapping: business unit, product or configuration,
 |   offering type (CTO / semi-custom / ETO), BOM reference
 |
 +-- assignments (one or MORE teams per requirement)
 |      +-- Team A: owner, due point, assignment status
 |      |      +-- team response (narrative / estimation sheet / price: open)
 |      +-- Team B: owner, due point, assignment status
 |             +-- team response
 |
 +-- final-response references: the parts of the final bid
 |   response that answer this requirement (or an explicit exclusion
 |   with reason, approved by a named person)
 |
 +-- change links: clarifications, addenda, change requests affecting it
 |
 +-- status: extracted -> reviewed -> assigned -> responded
 |           -> consolidated -> answered | excluded
 |
 +-- audit history: every decision and change, who and when (immutable)
```

Partial precedents sit in different code lines and do not form one record: the requirement registry (M17) and the coverage map in v0.3.0; the event log, override tracking and edit, split and merge in v1.0. The assignment, team-response, final-response-reference and change-link parts have no precedent in any line.

## Design Principles

These principles recur across the code lines and the review meetings. Each line implements some of them and not others. Each is connected below to the workflow step it protects.

1. **Agents propose; people decide.** The model gateway principle (steps 1, 5; protects 3). Validation and arithmetic are fixed rules; a model never decides anything that carries liability.
2. **A human approves every consequential step**, with a named person recorded (steps 3, 4, 5, 7). In v0.3.0 this is enforced in code between stages. Expected (review meetings): the model cannot change a requirement; an individual can.
3. **Prove where every value came from.** Every extracted value carries a source anchor (document, page, quoted text) and a provenance class: `EXTRACTED`, `DERIVED` or `UNANCHORED`. A location is never invented. Traceability points back to the exact row or column in the RFP so a reviewer can detect invented content (steps 1, 5, 7).
4. **Unknown never passes.** Missing information is reported, never defaulted. An early bug turned a missing rack density into zero and passed a cooling check (steps 3, 5).
5. **Refusal is a first-class output.** Where the system cannot responsibly answer, it says so and routes to an engineer (steps 3, 5).
6. **Fail safe on tiers.** The most conservative tier wins; a move toward more automation waits for a human (step 5).
7. **Do not claim coverage over text that was not read.** Unreviewed regions are reported (steps 1, 7).
8. **Replaceable parts, rules as data.** The model is called from one place only; domain rules, such as the brand-layer-team map and workflow templates, live as data rather than code (steps 2, 4, 5).
9. **Every case is separate.** The case identifier is a required part of every record, so concurrent opportunities cannot contaminate each other (all steps; cross-cutting).
10. **Local-first model use.** The intent in v0.3.0, 22 Sep and v1.0 is a self-hosted model so RFP content stays on the machine. Whether a local or cloud model will be used, and whether RFP text may leave the machine, is not decided.
11. **Keep generation narrow and repeatable.** Raised in the review meetings (Expected): rules plus retrieved reference text first; freeze first-pass facts as an immutable set; run the model at temperature 0 (the setting that makes output as repeatable as possible); supply product knowledge and past responses through retrieval (RAG, updated 8 Oct 2026) and rules, not by fine-tuning; use a second checker and a golden data set (known-correct examples) when the model version changes. A change request is handled on its own, not by regenerating everything (step 7; cross-cutting).
12. **Configurable process with an immutable log.** Some steps mandatory, some configurable, because processes differ by customer; every step logged as the source of truth (steps 4 to 7; cross-cutting).

## Implemented Today: Inventory of Existing Code Lines

This section says only what each code line actually does, with its caveats. **These are separate code lines, not one working system and not increments of each other.** No line is confirmed as the baseline for further work. No line is a finished product; the sources' "production-ready" labels are not supported by their own status tables.

**Layer0-Flex is the new baseline (8 Oct 2026); stage 0 is built (see below).** The four older code lines below are history and precursors; their modules are being ported into Layer0-Flex.

**No code line implements step 2 (participation as a decision), step 4 (workflow creation), step 6 (team-response tracking) or consolidation into the final response.** No line implements the three-view traceability, per-requirement assignment to multiple teams, or the handling of clarifications and addenda. Whether to extend one of these lines or rebuild is open.

### Layer0-Flex new baseline (from 8 Oct 2026)

Layer0-Flex is a Git repository and the single code base. It is a modular monolith: one Python service whose modules each have a model, a view and a controller. Modularity is deliberate, so one module can change without touching the others. The architecture is not redesigned. The existing v0.3.0 modules are ported rather than rewritten; the v1.0 and v1.1 rule pieces are reused as evidence checks. All modules are treated as important: the work is to wire them in, test them and use them in the PoC (written direction from the Zensar point of contact). The documents in Layer0-Flex/Documents are the source of truth; build details are in [technical-architecture.md](technical-architecture.md).

**Status on 8 Oct 2026: stage 0 is built: a running skeleton with a demonstration seeded from the Syracuse RFP; the reader and matcher agents have not yet been run on the full RFP.** Build stages are in [technical-architecture.md](technical-architecture.md) section 13.

New-baseline modules: opportunities, ingestion, requirements, catalog (business units, products, past responses, retrieval index), matching, decisions (participation, go/no-go), workpackages (dispatch, responses, validation), consolidation (coverage, compliance matrix, final response), changes (delta), and trace (three screens, portfolio).

The sample RFP for development is Layer0-Flex/data/RFP/RFP-2023-20-Switchgear-Procurement-Final.pdf (the public Syracuse switchgear RFP).

| v0.3.0 module | New module | What must be done |
|---|---|---|
| M1 Ingestion and boundary classifier | ingestion | Port, wire, test |
| M2 Extraction | requirements | Port; make model-based and remove regex; wire, test |
| M3 Scope detection | matching | Port; adapt to matching against business-unit offerings; wire, test |
| M4 Tier classification | matching | Port; tiers become offering types (CTO, semi-custom, ETO); wire, test |
| M5 Validation | matching and consolidation (evidence) | Port as evidence checks; wire, test |
| M6 Evidence contract | all agents | Port; every agent output carries evidence; wire, test |
| M7 Orchestration and approval gate | workpackages workflow | Port; approval gates become named-person decisions; wire, test |
| M8 Routing adapters | workpackages dispatch payloads | Port; now to be wired (not wired in v0.3.0); test |
| M9 Connectors | catalog connectors | Port; BOM source, QuoteWin, SAP and aPriori stubs; now to be wired; test |
| M10 Model runtime adapter | core model gateway | Port; the single place a model is called; wire, test |
| M11 Provenance | requirements anchors | Port; anchors verified against page text; wire, test |
| M12 | (does not exist) | None |
| M13 Solver | matching evidence (low-voltage arithmetic) | Port as an evidence check; wire, test |
| M14 Coverage map | consolidation coverage | Port; wire, test |
| M15 Proposal checker | consolidation proposal checker | Port; now to be wired (not wired in v0.3.0); test |
| M16 Model-change guard | core model-change guard (golden tests) | Port; wire into the build, test |
| M17 Requirement registry | requirements registry | Port; now to be wired (not wired in v0.3.0); test |

### Mapping of each code line to the workflow steps

| Code line | Closest relation to the workflow | Not implemented |
|---|---|---|
| v0.3.0 bid-triage pipeline (`layer0-delivery/`) | Step 1: reads a real RFP; regex or mock extraction by default; the language-model path is untested; clause splitting is unreliable on the full 101-page PDF. Partial precursor to step 2: scope detection maps product layers to brands and teams. Partial step 5: routes per layer (not per requirement) to four teams; payload adapters are not wired. Partial step 7: coverage map; proposal checker built but not wired. Approve or reject gates; no edit; no immutable log | Step 3 (no go/no-go output), step 4, step 6, consolidation into the final response, Q&A and addenda |
| 22 Sep fresh codebase, then v1.0 extraction-and-governance release (`Scatttered Documents/`) | Step 1: anchored extraction, shown on one synthetic case. Deviation check against a past bid (input to step 3). Case-scoped event log, override tracking and correction learning (cross-cutting; built but unverified). Edit, split and merge in the data layer (unverified). Three-panel UI never compiled | Steps 2, 4, 5, 6, 7 |
| v1.1 three-stage decision demo (`CPQ/`) | Partial step 3: BID, HOLD or NO_BID with a margin estimate. Execution-stage change check (engineering change notice); portfolio conflict check. All deterministic rules over synthetic, pre-structured data; no RFP is read | Steps 1, 2, 4, 5, 6, 7 |

### v0.3.0 bid-triage pipeline (`layer0-delivery/`)

**What it is.** A six-stage pipeline that reads an RFP, decides line by line what is automatable, solves a narrow part, refuses the rest, and links each decision to its source clause. Its tagline is "bid intake, triage and routing".

**Flow.** A named human approves between every pair of stages.

```text
RFP (PDF or text)
  -> [1 Understand]             ingestion + extraction + scope detection
  -> [2 Scope and Tier]         out-of-scope layers marked; tier per in-scope layer
  -> [3 Draft System Design]    per tier
  -> [4 Validation]             deterministic checks + confidence note
  -> [5 Solve or Refuse]        arithmetic for the simple part, reasoned refusal otherwise
  -> [6 Coverage Map & Routing] clause table + work packages for four teams
```

1. **Understand.** Reads the PDF page by page, extracts values (capacity, voltage, redundancy, power equipment ratings, standards), and decides from keyword evidence which of the six layers the bid touches. Pages with no text layer are reported as unreviewed; CAD files and macro-enabled spreadsheets are named and routed to engineering.
2. **Scope and tier.** No model is used. Sections that say what is not specified are removed first, so they cannot trigger a layer. Brand defaults give a tier per layer and the most bespoke wins.
3. **Draft system design.** Standard layers get a short specification; guided layers get standard sub-items plus a "basis of design" with no design claimed; exception layers get a margin-protected placeholder and an intake ticket. Known defect: out-of-scope layers fall through to the exception branch.
4. **Validation.** Fixed engineering checks (completeness, voltage consistency, cooling versus rack density, redundancy match, supply-timeline dependency). Physical limits are generic standards values, not SpinCo-specific.
5. **Solve or refuse.** Only low-voltage power-distribution arithmetic is solved. Medium-voltage switchgear, thermal design and similar work is refused with a reason and routed to engineering.
6. **Coverage map and routing.** Every clause receives a disposition (extracted and routed, captured but not designed, out of scope by design, not handled, unreviewed). Routing groups layers into work packages for four teams (Critical Power, Embedded Power, Thermal, Cloud). Routing is per layer, not per requirement; commercial and legal requirements have no route.

**Components.** Status as in the component manifest, read against the code. "Wired" means part of the running demo.

| Component | Responsibility | Built | Wired |
|---|---|---|---|
| Ingestion and boundary classifier (M1) | Documents to page-anchored text; refuse and route unsupported files | Yes, tested on a real 101-page PDF | Yes |
| Extraction (M2) | Text to structured values | Yes; pattern matching by default, model path incomplete | Yes |
| Scope detection (M3), tier classification (M4) | Which layers, which tier | Yes | Yes |
| Validation (M5) | Deterministic rule checks | Yes; generic standards values | Yes |
| Evidence contract (M6) | Each stage explains itself and carries evidence | Yes | Yes |
| Orchestration and approval gate (M7) | Run stages, enforce approvals, keep run state | Yes | Yes |
| Routing adapters (M8) | One hand-off payload per destination | 3 of 4 written | No |
| Connectors (M9) | One contract per external system | Interface stubs only, disabled | No |
| Model runtime adapter (M10) | The only place a model is called | Yes | Yes |
| Provenance (M11) | Source anchors, three classes | Yes | Yes |
| Solver (M13) | Low-voltage arithmetic; refuses the rest | Yes | Yes |
| Coverage map (M14) | Clause-by-clause table | Yes; weak on full PDFs | Yes |
| Proposal checker (M15) | Compare a returned proposal with the RFP | Yes | No |
| Model-change guard (M16) | Developer gate blocking a model change that breaks known-correct answers | Yes | Standalone |
| Requirement registry (M17) | One canonical record per clause, intended as the unit for comparison and human correction | Yes | No |
| Front end | Upload, tier badges, scope evidence, anchors, approve or reject | Yes | Yes |

There is no component M12 (unexplained). Eleven modules are wired; a stale proposal-assembly module remains imported but is never called.

**Contradictory statements (flagged, not reconciled).** Module numbering and stage counts differ between documents (five or six stages). Test-result statements contradict each other: 6, 21, 27, 37, 68 and 78 tests are each stated somewhere. This document uses six stages and mentions the latest claim of 78 tests, but it is Needs confirmation whether any of these pass on the team's machines. The package claims the pipeline was "verified end to end" on the genuine 101-page PDF; the team's code review states that clause splitting treats table-of-contents headings as requirements on that document. These two statements are not reconciled here.

**Where a model is and is not used.** Only extraction and confidence notes can use a model. By default no model runs: a hand-written pattern-matching routine (regex) stands in, and the 22 Sep demo ran this way. A local-model path exists but has not been tested end to end, and its prompt asks for fewer fields than the default path returns, so it would not simply work. The 22 Sep review discussion stated that an LLM is used; the code does not by default. Retrieval is keyword matching only.

**Designed routes out of Layer 0 (not connected).** Route A: standard items go to the commercial CPQ as a starting point; Layer 0 "seeds the configurator; it does not configure". Route B: guided items go to design engineering with the basis of design. Route C: exception items go to a specialist queue. Every payload requires human completion.

**Status summary.**
- Built and connected: ingestion, extraction, scope, tier, validation, solver, coverage map, provenance, approval-gated pipeline, front end.
- Built, not connected: routing adapters, proposal checker, requirement registry.
- Stubs: connectors.
- Not built: scanned-page reading (OCR), live connectors, handling of addenda and customer questions, human edit, split and merge of requirements, side-by-side review, estimation sheets, an immutable audit log (approvals sit in editable state), commercial, legal and staffing requirements, any go/no-go output.

**Limits.** No front-end login; the grid-interface layer has one brand (EPC Power, acquisition pending) so a supply warning always appears; solving is low-voltage only; extraction misreads propagate downstream. Built with AI coding tools under one version-control commit; whether this folder is the newest 17-module version is unconfirmed.

### 22 Sep fresh codebase and v1.0 release

**What it is.** A restart on 22 Sep with a different framing: "the intake layer in front of your CPQ" that extracts specifications with exact source anchors and checks them against the customer's past bid. v1.0 (23 Sep) is its release. The release's own `ARCHITECTURE.md` differs from the same-named file in the fresh codebase folder.

**Intended design (22 Sep).** Six stages: ingestion, model extraction with source anchors, scope detection, tiering and routing, rules check, coverage and deviation detection. Only extraction existed when the design was written. A five-module MVP (minimum viable product: the smallest version worth piloting) adds governance, specification editing, deviation detection against a past bid, and a three-panel review screen (customer RFP, previous bid, extracted specifications). These are completion claims, not verified status.

**Flow as wired in v1.0.**

```text
RFP text
  -> Extraction (model finds regions; exact-span match) -> Specification records
       (tier and rules slots exist but are empty)
  -> Backtest: compare with the past bid's actual content
  -> Result: would the change order have been caught?

Every change to a record goes through governance:
  event log (immutable, case-scoped)
  -> override tracking
  -> correction ledger (same correction by 5+ engineers)
  -> pattern detector (repeats become rule candidates)
  -> rule versioning (versions move forward, never overwritten)
```

**Components and verified status.** "Built" means code exists; "verified" means actually run in quality-assurance (QA) testing.

| Component | Responsibility | Built | Verified |
|---|---|---|---|
| Specification data model | Shape of a specification, anchor and provenance | Yes | Yes |
| Model extraction | Region finding then exact text match; never invents a location | Yes | Yes (2 of 2 specifications from one test RFP) |
| Scope detection, tiering, rules engine | Empty slots only | No / partial | Phase 2 |
| Governance chain (event log, override tracking, correction ledger, pattern detector, rule versioning) | Immutable audit trail and learning from human corrections | Yes | No |
| Requirement lifecycle (edit, split, merge) | Each change logged; concurrent-edit conflicts not handled | Yes | No |
| Backtest framework | Replay a historical case | Yes | Yes (two real bugs fixed 23 Sep) |
| Metrics calculator | Catch rate, return on investment (ROI), margin | Yes | Runs, but valid only on real data (one case so far) |
| Three-panel front end | Review screen | Source only | No (never compiled or run) |
| Production PDF ingestion | Phase 2 | No | - |
| Live connectors | Need SpinCo/Flex IT credentials | No | - |

Only five of these were run in QA. "Unverified is not broken". Value figures claimed by these documents (catch rate, return on investment, money protected, hours saved) were later retracted and are superseded; they are not used here as results. The Syracuse past bid and change-order example is constructed for illustration.

**Model use.** The design says "LLM for reading, not regex" because pattern matching cannot tell "arc-resistant" from "arc resistance NOT SPECIFIED". v1.0 does not bundle a model, yet extraction ran in QA; how it did so is not explained (Needs confirmation).

**Technology shape.** Python, a local event store, a React review screen; a backend API is proposed only. Explicit non-choices: no cloud model, no vector database, no scanned-page reading.

**Limits.** Input starts at plain RFP text. Tiering and rules checks are empty. Two people editing one case at once is not handled.

### v1.1 three-stage decision demo (`CPQ/`)

**What it is.** "Layer 0 v1.1 - Portfolio-Risk-Intake System": a rebuild that evaluates switchgear opportunities across three procurement decision stages.

1. **Bid stage.** Compares an incoming specification with the standard portfolio, detects deviations, estimates margin impact, and returns bid, hold or no-bid.
2. **Execution stage.** Compares a committed order's specification across contract phases, rates technical, supply-chain and field risk, and decides whether an engineering change notice (ECN: a formal approval of a design change) is required and whether the next phase is locked.
3. **Portfolio stage.** Checks simultaneous customer opportunities for specification, capacity and timeline conflicts and recommends the safest combination.

**Flow.**

```text
synthetic scenario data files
  -> loader ("extraction"): scenario data -> shared specification model
  -> bid recommendation | lifecycle tracking | portfolio risk check
  -> metrics calculator
  -> orchestrator: one aggregate result with isolated case identifiers
  -> backend (a single call) -> React interface with one tab per scenario
```

**Status.** All listed components are complete as demo code: shared specification model, loader, three decision engines, metrics, orchestrator, backend, interface. Six QA tests and a pre-demo package check pass; two runs give identical results. The browser click-through was not done. Known defect: the metrics' "highest risk factor" picks alphabetically rather than by severity.

**What v1.1 does not do.** No RFP document is read; "extraction" only converts pre-structured scenario data. No PDF ingestion, no connection to ERP, no alerting, no external integration. Several constants (standard lead time, plant capacity, material risk ratings, deadlines, margins) were invented so the synthetic data would produce the expected outputs, and customer-and-product pairings are not confirmed as realistic. Its margin estimates relate to the open question of whether prices or margins belong in Layer 0.

**Code observation (context only, not a requirement).** The backend runs fixed Python rules (bid recommendation, lifecycle tracking, portfolio risk check) over the scenario files in one web call and returns the result. No language model is called. This clarifies the 5 Oct review description of the backend as just reading JSON (a structured text data format) from the data folder: the code shows rules computing recommendations, not only displaying stored results. Whether the "logic engine" described in the review meetings (rules plus retrieval-augmented generation, RAG: supplying a model with retrieved reference text) exists anywhere is Needs confirmation.

**Gap against the intended workflow.** The review meetings identified the central missing piece as a three-view traceability screen (original RFP, breakdown and assignment, team responses). v1.1 does not provide it, nor does any other line. Whether it was lost or never built is unresolved.

### Comparison of the code lines

| Aspect | v0.3.0 | 22 Sep / v1.0 | v1.1 |
|---|---|---|---|
| Framing | Triage and routing in front of CPQ | Specification extraction and deviation check in front of CPQ | Bid, execution and portfolio decision support |
| Input | Real RFP (PDF or text) | RFP text | Synthetic scenario data; no RFP |
| Model use | Optional, untested; pattern matching by default | Designed, no model bundled | None |
| Human gate | Approve or reject between stages | Review and override, logged | None in the demo |
| Audit | Editable state | Immutable event log (unverified) | None |
| Tiers | Built and wired | Empty slots | Not used |
| Integrations | Stubs | None | None |
| Workflow steps touched | 1; partial 2, 5, 7 | 1; input to 3; cross-cutting audit | Partial 3 only |

## External Systems and Integrations

No system below is integrated with any code line. Connectors exist as stubs in v0.3.0 only. The integration boundaries are open: what is handed off, what is read back, whether opportunities are created in a CRM.

| System | What it does | Relationship to Layer 0 | Status |
|---|---|---|---|
| Logik.io (with Salesforce CRM) | Configuration engine and CPQ | Downstream; Layer 0 might seed it (Route A). Early documents stated that Flex had no CPQ; later market data found Logik.io in its stack. Which brands it covers, and whether SpinCo keeps it, is Needs confirmation. Whether opportunities are created in Salesforce is open | Not integrated; boundary open |
| QuoteWin | Quoting tool (handles requests for quotation) | Downstream system of record | Stub only (v0.3.0) |
| aPriori | Should-cost (estimating what a part should cost to make) and design-for-manufacture | Costing; first connector named for real integration | Stub only |
| SAP and Infor LN | Two ERP systems run in parallel | Systems of record | Stub only |
| Product life-cycle management (PLM) tools: Oracle PLM, Autodesk Vault, Solidpdm | Store product data and CAD drawings | Systems of record; pointer-link targets (Proposed) | None |
| Design automation (for example DriveWorks, Tacton, Autodesk) | Parametric design | Routed to, not integrated | None |
| Design engineers and specialist teams (Critical Power, Embedded Power, Thermal, Cloud) | Perform bespoke work and answer requirements | Receive assigned work | Manual |
| Model runtime (local) | Runs the language model | Called from one place only | Local path untested; v1.0 bundles none; cloud versus local Needs confirmation |

**Pointer links to artefacts in other systems (Proposed (inferred design)).** Today Layer 0 reads nothing but the RFP; CAD drawings, vendor specifications, test reports and email are not linked. The proposal is not to build parsers for them but to add a lightweight list of pointers to each requirement record (a citation, never a copy), read-only lookups through the connector stubs, and, where no integration exists (email is likely), an engineer-attached reference recorded in the audit history. This serves steps 5 to 7. The scaffolding it cites (requirement registry, connector stubs) belongs to v0.3.0, while the event log and correction ledger belong to v1.0; no source shows both in one codebase.

This list comes from a market-data study of Flex's systems and from the project's architecture documents. Real API contracts and credentials must come from SpinCo IT. Where SpinCo keeps CAD files, vendor specifications and test reports is unknown.

## History

### Earlier framings of Layer 0

Layer 0 was framed differently in each iteration. The framings are earlier, written descriptions; the workflow in this document is the current working baseline, replacing them as the main definition while keeping what they built.

1. **Agentic CPQ (superseded).** A system that reads an RFP, drafts a six-layer design, routes it to teams and assembles a proposal, with a human approval at each of five stages. An expert review of an earlier browser demo led to a local model, rules separated from the model, an enforced approval gate and connector stubs. A second version proposed classifying a tier before designing, using a per-company default with a per-component override and letting repeated designs "graduate" from bespoke to standard; its estimated automation mix was expert judgment, not measured. Real public RFPs exposed four extraction and routing defects that were then fixed. This framing was replaced by "the layer in front of your CPQ". The v0.3.0 package marks it superseded, and the proposal-assembly stage survives only as unused code. Autonomous proposal assembly is not part of the current direction.
2. **Bid intake, triage and routing in front of CPQ** (v0.3.0).
3. **Specification intake and deviation check in front of CPQ** (22 Sep restart, v1.0).
4. **Portfolio-risk intake and decision support** (v1.1).
5. **Opportunity management from RFP to final bid response** (review meetings of 22 Sep, 5 Oct and 8 Oct 2026): the working baseline described in this document. The 8 Oct review added the three screens, roles, offering types, the agentic process and RAG, and adopted Layer0-Flex as the single code base.

### Chronology

1. **Earliest framing: agentic CPQ.** History only (see above).
2. **v0.3.0 (21 Sep, v0.3.1 on 22 Sep).** Bid intake, triage and routing in front of CPQ.
3. **22 Sep fresh restart, then v1.0 (23 Sep).** An extraction-and-governance framing, started as a restart.
4. **v1.1 (planned 23 Sep; release folder dated 24 Sep; parent folder 28 Sep).** A pivot to bid, execution and portfolio decision support, "a rebuild" with "no prior v1.0 codebase".
5. **22 Sep, 5 Oct and 8 Oct review meetings.** Layer 0 restated as the opportunity-management workflow for a bid that may span several business units. On 8 Oct the project team adopted the Layer0-Flex repository as the single code base (skeleton only), and the first screen walkthrough was planned for 9 Oct with a functioning version targeted for 12 Oct 2026.

### Relationships

- The lines are separate code lines, not increments. v1.1 reused nothing from v1.0; v1.0 was a restart from v0.3.0. Module IDs, status vocabulary and even file names collide (two different `ARCHITECTURE.md` and two `MODULE_STATUS.md` documents).
- Each line implements different shared principles. Approval gating, tiers, the solver, coverage map and provenance with source anchors are strongest in v0.3.0. The immutable log, correction learning, requirement editing and backtesting exist only in the 22 Sep and v1.0 line. Portfolio and execution-stage reasoning exist only in v1.1.
- The first two review meetings covered the 22 Sep demo and the v1.1 demo; the third (8 Oct) set the new baseline. Neither delivered the three-view traceability or the logic engine described.
- A reading of the review meetings in terms of three offerings: CPQ fits only the configurable offering; Layer 0 targets multi-company custom and semi-custom data-centre bids where products from several companies are sold together. Documents describing Layer 0 purely as a CPQ front end should be read against this.
- Which line is the baseline for further work was resolved on 8 Oct 2026: Layer0-Flex. The documents were consolidated before more coding, as agreed. Confirmed in the meetings: call it a PoC or pilot, not a product; consolidate the documents before more coding.

### Earlier proposed layered target (CPQ comparison study)

A study of the components of a full CPQ concluded that Layer 0 should be built and everything else integrated. It is an earlier proposal, not confirmed.

```text
LAYER 0 - RFP intake and triage (build)
  unstructured RFP -> structured requirements -> scope detection
  -> automation-tier classification -> bid/no-bid signal
  (local model, evidence-traced, human-gated)
      |-- CTO_AUTOMATE  -> commercial CPQ (Logik.io or similar)
      |-- ETO_GUIDED    -> CPQ for standard sub-assemblies + design automation
      |-- ETO_EXCEPTION -> specialist engineers, margin-protected placeholder
      v
"LAYER 2" - Costing and pricing (integrate): aPriori should-cost; CPQ pricing
      v
"LAYER 3" - Systems of record (integrate): QuoteWin, SAP, Infor LN, design-data vault
            through an abstracted connector interface
```

The study found that a traditional CPQ works at quote-to-cash steps 3 to 8 and Layer 0 at the earlier steps, so overlap is small. It judged that unstructured RFP intake, automation-tier triage and an evidence trace are missing from CPQ, and recommended buying or integrating the rest and obtaining a cycle-time breakdown before building further. Rationale for a thin front layer: SpinCo has two ERP systems, brand-level IT autonomy from earlier acquisitions, and no single configuration model across its brands. Separation is targeted for the first quarter of calendar 2027, so back-end unification will not land first, but a front layer with abstracted connectors can.

## Constraints and Limits

- No code line reads scanned pages; ZIP files are listed, not opened.
- **Regex is rejected (8 Oct 2026).** Earlier lines extract by pattern matching by default; the model path is incomplete and untested. The review discussions expressed distrust of both (the LLM is very hard to trust, and pattern matching picked up table-of-contents entries such as "Introduction, page 5" as requirements, using about 100,000 model tokens). Requirement identification must be model-based on top of deterministic layout reading, with anchors verified against the page text.
- The new baseline: stage 0 is built: a running skeleton with a demonstration seeded from the Syracuse RFP; the reader and matcher agents have not yet been run on the full RFP (8 Oct 2026).
- Clause segmentation is unreliable on full documents, so coverage counts there are not trustworthy.
- Commercial, legal and staffing requirements are not modelled or routed in v0.3.0.
- No immutable audit log in the v0.3.0 line; the audit trail in the v1.0 line is unverified. Human edit, split and merge is built only in the v1.0 line and untested.
- Solving covers low-voltage arithmetic only, with generic standards values rather than SpinCo's.
- The grid-interface layer has a single brand, so a supply-risk warning appears on every run.
- Demo data in v1.1 is synthetic with invented constants; metrics from the v1.0 line rest on one case. The demo cases are illustrative and do not match SpinCo's customer types.
- Maturity: the PoC sits between "blueprint" and "pilot" on the maturity ladder (Blueprint, PoC, Pilot, MVP, Product). Risks not retired: volume (hundreds of concurrent bids), real connectors, whether the tier split is economically correct against real quote history, whether physical checks catch what an engineer would, and local model inference end to end.
- Concurrent-bid support is a gap: a portfolio or workload view of in-flight cases and handling of two people editing one requirement are Phase 2 or not scheduled.
- Everything built so far was written with AI coding tools, without version control across folders. Documents and code were fragmented and contradictory; since 8 Oct 2026 Layer0-Flex is the single code base under Git (partly resolves the version-control gap).
- Remaining ambiguities from the review meetings: the exact list of the six business units (EP² is confirmed as one) and its mapping to brands, pillars and teams; the exact BOM source system; "$7 billion" against $6.6B FY26 revenue in written sources; a "January 4" start with no year; the phrase "pre-RFI bid response system" against the RFPs actually processed; whether bid/no-bid output is a deliverable or only decision support (the working baseline is support).
