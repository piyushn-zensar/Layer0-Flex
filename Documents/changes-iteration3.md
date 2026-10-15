# Layer 0: Changes Requested on 15 Oct 2026 (Iteration 3)

Status: **Expected (written direction)** for what was asked; **Proposed (inferred design)** for how the build answers it. The feasibility notes are a quick project-team analysis of the code at commit 7346766 (15 Oct 2026). Nothing in this document is built yet. Written 15 Oct 2026.

## 1. Purpose, Who This Is For, and Sources

**Purpose.** This document registers the changes requested in writing on 15 Oct 2026. For each change it says what was asked, what the system does today, what must change, how well the change fits the current build (integration feasibility), how the result is checked, and what still needs confirmation. The numbering continues from [changes.md](changes.md) (C-01 to C-22), so this register starts at C-23.

**Who this is for.** The Zensar point of contact, who reviews the direction, and the developers who build it.

**Sources.**
- The written direction of 15 Oct 2026 (the change request this document registers).
- The code at commit 7346766, checked on 15 Oct 2026.
- [changes.md](changes.md) (C-01 to C-22) and [technical-architecture.md](technical-architecture.md) section 16 (the iteration-2 design).
- The public Flex product page [flex.com/products/power-and-cooling](https://flex.com/products/power-and-cooling) and [flex.com/robots.txt](https://flex.com/robots.txt), checked on 15 Oct 2026.

**How it relates to the other documents.** The iteration-2 changes (C-01 to C-22) that are still open continue. This document supersedes these parts of the iteration-2 design:

| Iteration-2 rule | Replaced by |
|---|---|
| The bid manager publishes the register before assessment (C-05; technical-architecture 16.3 "Publishing") | Automatic freeze when extraction completes (C-27) |
| The same file sent to two bids is two separate documents (technical-architecture 5.1) | A document instance already read opens its existing bid (C-27) |
| Product manager and design engineer per unit; the bid manager owns all non-product items (C-07, C-08) | Unit manager and unit designers / engineers (C-25) |
| The bid manager validates unit answers (current build) | The unit manager validates the unit's responses (C-25); the bid manager approves only the overall schedule and high-level compliance (C-24) |
| API paths stay `/api/opportunities/...` (changes.md section 8) | API paths say `/api/bids/...` (C-31) |
| A separate Requirements step and a Knowledge base page (technical-architecture 16.2) | Requirement Traceability holds the requirements (C-30); no Knowledge base page (C-33) |
| Retrieved evidence is shown to people but kept out of model prompts (design rule R2, technical-architecture section 3) | Reviewed, cited evidence is passed to the model, with every evidence version recorded (C-29) |

## 2. Summary

Five themes run through the request:

1. **Each role sees and approves only what it owns.** The bid manager reads an executive summary and approves the overall schedule and the high-level compliance position. Each unit's manager owns the unit's non-technical requirements, compliance and schedule; the unit's designers and engineers own its technical requirements (C-23, C-24, C-25).
2. **Requirements are frozen automatically per document instance.** A successful extraction is saved and frozen at once, with no approval. A document instance that was already read is never read again; the user is taken to its bid (C-27).
3. **Complete sign-in and permissions.** People can sign up; the server enforces roles on every screen and API (C-26).
4. **Knowledge from sources, with review.** The product catalog refreshes itself from the official Flex product page. A source-backed knowledge base with reviewed examples supports interpretation and assessment, and every assessment can be explained by its citations. Knowledge changes never rewrite frozen requirements (C-28, C-29).
5. **Simpler, more flexible screens.** Requirements live on one Requirement Traceability page with filters and sorting; the Knowledge base page goes; each of the three panes can be moved to its own window or monitor; the API uses the word "bids" (C-30 to C-34).

Four measures are kept apart on every summary, because they answer different questions:

| Measure | Question it answers | Computed from | It is not |
|---|---|---|---|
| **Domain alignment** | Do the bid's technical requirements fall within the domains of the units and products in the catalog? | Requirement categories and product matches, against unit domains and catalog records | A chance of winning |
| **Product-evidence coverage** | For how many technical requirements is there reviewed product evidence? | Cited catalog records, verified datasheets and approved engineering rules | A unit's compliance answer |
| **Specialist-review progress** | How far have the units assessed the work sent to them? | Validated unit responses against the items sent | A quality measure |
| **Preliminary feasibility** (the overall assessment score) | Before and during assessment, what share of the technical requirements look feasible on the evidence? | A documented formula over the three measures above and the evidence gaps (C-23) | A probability. Retrieval similarity and a model's self-reported confidence are never shown as feasibility |

## 3. Revised Target Workflow (revision 4)

Expected (written direction), 15 Oct 2026, for the owners. The detailed sequence is the **Proposed (inferred design)** default.

| # | Stage | Owner | What happens |
|---|---|---|---|
| 1 | Intake and extraction | System | Identify the document instance. If it was read before, open its bid. Otherwise read it into source-backed requirements and **freeze them automatically** (baseline 1, with the extraction snapshot E1). Text without verifiable evidence goes to the exception queue |
| 2 | Executive summary | Bid manager | Read what the customer wants, the major sections, the suggested units, the open questions and the assessment (domain alignment, product-evidence coverage, review progress, preliminary feasibility, evidence gaps). No per-requirement approval |
| 3 | Routing | Bid manager | Choose the participating units and send the work for assessment |
| 4 | Unit assessment | Unit manager; unit designers / engineers | Designers and engineers address the unit's technical requirements. The unit manager addresses the unit's non-technical requirements, validates the unit's responses (unit-level compliance) and enters the unit's estimated completion date |
| 5 | Consolidated schedule and compliance | Bid manager | Once every participating unit has given its estimated completion date, the consolidated schedule and the planned submission date can be finalised. The bid manager approves the overall schedule and the high-level compliance position |
| 6 | Go / no-go | Bid manager | The final call stays with the bid manager (project-team decision, 13 Oct 2026), unless the approvals in stage 5 replace it (open question 3) |
| — | Changes | Bid manager and specialists | Customer changes and extraction corrections are versioned on top of the frozen baseline (C-04, unchanged) |

## 4. Change Register

Feasibility: **Fits** = extends existing parts; **Fits with rework** = changes an existing contract, rule or screen; **Needs a decision** = cannot be built as asked until an open question is answered. Size (rough, for comparison only, not a schedule): **S** = hours; **M** = one to two working days; **L** = several days; **XL** = more than a week, delivered in phases.

| ID | Change | Feasibility | Size | Status |
|---|---|---|---|---|
| C-23 | Executive summary with a defined assessment score and evidence gaps | Fits with rework | L | Expected (written direction) |
| C-24 | Bid manager approves only the overall schedule and high-level compliance; consolidated schedule from the units' completion dates | Fits with rework | M–L | Expected (written direction) |
| C-25 | Unit manager (non-technical requirements, unit compliance and schedule); unit designers / engineers (technical requirements) | Fits with rework | M | Expected (written direction) |
| C-26 | Sign-up; end-to-end authentication; role-based authorization on every screen and API | Fits | M | Expected (written direction) |
| C-27 | Automatic requirement freeze per document instance; an instance already read opens its bid | Fits with rework | M | Expected (written direction) |
| C-28 | Product catalog refreshed from the official Flex product pages on start and every 24 hours, with product-name versions | Fits with rework | M–L | Expected (written direction) |
| C-29 | Source-backed knowledge base and retrieval (RAG) | Fits with rework | XL | Expected (written direction) |
| C-30 | Requirements page merged into **Requirement Traceability** | Fits with rework | M | Expected (written direction) |
| C-31 | API paths say "bids" instead of "opportunities" | Fits | S–M | Expected (written direction) |
| C-32 | Filtering and sorting on Requirement Traceability | Fits | S | Expected (written direction) |
| C-33 | Knowledge base page removed; storage, retrieval and review kept | Fits (after in-context review exists) | S | Expected (written direction) |
| C-34 | Flexible workspace: draggable, detachable panes in separate windows | Fits with rework | M | Expected (written direction) |

## 5. Changes in Detail

Each change lists what was asked, today's behaviour, the required change, its integration feasibility, how it is checked and what is open.

### C-23. Executive summary with a defined assessment score

- **Asked.** The bid manager sees only the executive summary, including a system-generated assessment score based on the knowledge base and relevant historical evidence. The assessment shows domain alignment and preliminary feasibility, and identifies evidence gaps. Domain alignment, product-evidence coverage and specialist-review progress are shown separately; any overall score is clearly defined; retrieval similarity or a model's confidence is never presented as a feasibility probability.
- **Today.** The bid summary (Bid decision page) gives counts by category and by compliance level (fully, partly, not, bid desk), requirements that need an owner, open questions, ten go/no-go criteria marked met, not met or unknown, and advice as a sentence ("N of M criteria met"). There is no numeric score and no evidence citation. The Assessment screen (built 15 Oct 2026) shows this summary with the open questions, participation, routing and Send for assessment; the Bid decision page keeps the evidence and go/no-go.
- **Change.**
  - The **executive summary** is the bid manager's entry view of a bid: what the customer wants, the major sections, counts by category and offering type, the suggested units, the open questions and the assessment panel. Details stay one click away on Requirement Traceability; they are not the bid manager's working view.
  - The **assessment panel** shows the four measures of section 2 separately, each as "x of y" with the requirements behind it.
  - **Preliminary feasibility** (proposed default, kept in the decision configuration so it can be changed): the share of technical requirements that are within the units' domains and have reviewed product evidence with no conflicting evidence. As units answer, each validated response replaces the estimate for that requirement. The label reads "Preliminary assessment, not a probability".
  - **Evidence gaps** list: technical requirements with no product evidence; evidence only from unreviewed or illustrative sources; exceptions; requirements that need an owner; conflicts between the evidence and the RFP.
  - Each summary records the evidence versions it used (C-29, point 4), so a later knowledge change does not alter it silently.
- **Integration feasibility.** Fits with rework. Counts, needs-owner, open questions and criteria exist in the decisions module; the measures and gaps are new, deterministic calculations (no model call). Product-evidence coverage depends on catalog records with provenance (C-28) and reviewed evidence with citations (C-29). A first version can use today's matches and the catalog's source links, labelled as such, and switch to reviewed evidence when C-29 lands. The assessment panel is added to the existing Assessment step.
- **Checked by.** Every number on the summary opens the requirements it counts; no similarity score or model confidence appears as a probability; a bid's summary does not change after a knowledge-base change until a reassessment is requested.
- **Open.** The formula and its weights (open question 10). "Relevant historical evidence" needs real past Flex bids and responses (C-19).

### C-24. Bid manager approves the overall schedule and high-level compliance

- **Asked.** Limit the bid manager's approvals to the overall schedule and high-level compliance. The consolidated schedule and the planned submission date can be finalised for approval only after all units provide their estimated completion dates.
- **Today.** No date is stored anywhere: not on the bid, the unit's work or the decision. The "Schedule" go/no-go criterion only reads the validated answers to requirements of the category "schedule". The bid manager validates every unit answer (validation inside the unit, C-07, is not built yet), answers the bid desk items, records participation and dispatch, and records go/no-go.
- **Change.**
  - Each participating unit's manager enters the unit's **estimated completion date** for its part of the response, with an optional note.
  - The bid holds the **RFP submission due date** (from the RFP's submission requirements, confirmed by the bid manager) and a **consolidated schedule**: each unit's date, the latest unit date, the consolidation time and the **planned submission date**. A warning shows when the planned date falls after the due date.
  - **Schedule approval**: the bid manager can finalise and approve the consolidated schedule only when every participating unit has a date. The server refuses it otherwise.
  - **High-level compliance approval**: the bid manager approves the consolidated compliance position (fully, partially and non-compliant counts per unit, open gaps) from the compliance matrix, not individual technical answers.
  - Both approvals are audited. A later change to a unit date or to a unit's validated answers reopens the approval.
  - The bid manager no longer validates individual unit answers (C-25).
- **Integration feasibility.** Fits with rework. The dates and approvals go into new tables (per bid and unit; per bid approval), which avoids the database reset that new columns on existing tables force today. The validation rule in the work-package service (bid manager only) changes. The "Schedule" criterion is rewritten to use the dates. The compliance matrix and its counts already exist.
- **Checked by.** Approval is refused by the server until every participating unit has a date; changing a unit's date after approval reopens it; the bid manager cannot validate a unit's technical answer.
- **Open.** Whether go/no-go stays as a separate call (open question 3); the consolidation time and where the due date comes from (open question 4).

### C-25. Unit manager and unit designers / engineers

- **Asked.** The unit manager handles the non-technical requirements for the unit, including unit-level compliance and scheduling. The unit's designers and engineers review and address the technical requirements assigned to the unit.
- **Today.** Roles are bid manager, product manager, design engineer and administrator. Requirements have seven categories; *technical* and *compliance* are product categories that the matcher routes to units, while *commercial*, *schedule*, *submission*, *legal* and *staffing* go to the bid desk, which is the bid manager. Unit work is assigned to the unit's design engineer. Who may answer is checked by comparing display names from the business-unit file. The workflow configuration planned in iteration 2 (C-07) is not built.
- **Change.**
  - Unit roles become **Unit manager** and **Unit designer / engineer**. Decided 15 Oct 2026: the unit manager is the unit's product manager (same accounts and stored names); the design engineer becomes unit designer / engineer.
  - **Routing by category.** A unit's technical requirements (categories technical and compliance) go to its designers and engineers. Non-technical requirements that concern a participating unit (for example delivery, warranty, unit commercial terms) go to that unit's manager. Bid-level administrative items that belong to no unit (for example submission format or a bid bond) stay on the bid desk (open question 2).
  - The unit manager **validates** the unit's responses (unit-level compliance) and enters the unit's completion date (C-24).
  - The rights are read from the workflow configuration, so another sequence is a configuration change, not a code change.
- **Integration feasibility.** Fits with rework. The technical / non-technical split already exists in the category list. New: the role label and value, routing of non-technical items to units (the matcher assigns only product categories to units today, so a non-technical item needs a rule: every participating unit, or a unit chosen by the bid manager), and permission checks moved from display names to role and unit. The seeded demonstration and the walkthrough assume the bid desk owns all non-technical items, so both are refreshed.
- **Checked by.** A unit designer / engineer cannot validate; a unit manager cannot answer another unit's items; a non-technical item for a unit reaches that unit's manager, not the bid desk.
- **Open.** Open question 2.

### C-26. Sign-up and complete authentication and authorization

- **Asked.** Add a sign-up option. Complete the end-to-end authentication flow and enforce role-based authorization across the application and the APIs. Email verification is out of scope.
- **Today.** Sign-in with a signed token is built (C-09): sign-in, sign-out and "who am I"; every module API refuses requests without a session; the token is kept in an HttpOnly cookie. Accounts come from a roster file; there is no sign-up. Writes are checked by role in every module except the knowledge items (send and review), which any signed-in person can call. Some checks still compare display names (who may answer a unit's item, the knowledge curator), and the bid manager still validates unit answers until validation inside the unit (C-07) is built. The web application has no page-level guard; some buttons are greyed by role.
- **Change.**
  - A **Sign up** page and API: username, display name, password, and the person's **role** (bid manager, unit manager, unit designer / engineer) and unit, chosen by the person (decided 15 Oct 2026: kept simple for the proof of concept). The administrator role cannot be chosen; the administrator account is seeded by the server. Choosing one's own role is a known proof-of-concept limit: a pilot assigns roles centrally (C-09 open point).
  - Accounts created by sign-up are not overwritten by the roster file; only roster accounts follow it.
  - Minimum password length, unique usernames and a limit on repeated failed sign-in and sign-up attempts.
  - **Server-side authorization on every write**, per the permission matrix (technical-architecture 16.6, updated for C-24 and C-25), using the role and unit in the token instead of display names.
  - **Web**: a guard sends signed-out visitors to sign-in and returns them to the page they asked for; screens show only the actions the role may take. The server stays the control.
  - Excluded: email verification and password reset by email. An administrator resets a password.
- **Integration feasibility.** Fits. Password hashing, the account table, the token, the sign-in page and the 401 handling exist. New: one sign-up route and page, role checks on the knowledge routes, and the switch from name to role and unit checks. Accounts are stored apart from the demonstration data, so a demonstration reset keeps signed-up accounts.
- **Checked by.** A request without a session gets 401 on every API; for each role, every forbidden write gets 403 (one test per role over all write routes); a signed-up account has exactly the rights of the role it chose; sign-up cannot choose administrator.
- **Open.** None.

### C-27. Automatic requirement freeze per document instance

- **Asked.** Freezing requirements means preserving a consistent extraction for a particular document instance. It is an automatic system action and needs no bid-manager approval. Once extraction completes successfully, the extracted requirements are saved and frozen in the database at once. The **Document ID** and **Document Instance ID** identify the instance. If the instance was already processed, the user is taken to its existing bid and stored requirements instead of extracting again. Knowledge-base updates or reassessments must not silently modify the frozen baseline.
- **Today.** Each uploaded file is fingerprinted (SHA-256) and stored once; the document's ID is the bid ID plus the start of the fingerprint. The same file uploaded twice to one bid is recognised; the same file sent to another bid is a separate document by design (technical-architecture 5.1). The bid manager starts the extraction, which writes the extraction snapshot E1 (never modified), admits verified requirements to the register and puts unverified text in the exception queue. Until the bid manager publishes, corrections change the working rows (E1 keeps the original) and a re-read with a reason (E2) is possible. Publishing creates baseline 1; go/no-go, dispatch and change documents need it. After publishing, only versioned corrections and customer changes write requirement rows; matching and the knowledge base never do.
- **Change.**
  - **Document identity** (decided 15 Oct 2026): the **Document ID** and **Document Instance ID** are the identifiers embedded in the file by the tool that wrote it. The Document ID stays the same for the whole life of the document; the Instance ID changes with each save or edit. In a PDF they are the two entries of the trailer `/ID` (or `xmpMM:DocumentID` and `xmpMM:InstanceID` in its XMP metadata); in a Word document, the document ID in its settings. When a file carries no embedded ID (some PDFs and all spreadsheets), the SHA-256 fingerprint of the file is used for both. Both are stored with the document.
  - **Known instance.** On upload the system reads both IDs. If that Document ID and Instance ID were already read, in any bid, nothing is read again: the user is taken to the existing bid and its stored requirements, with a message saying so (decided 15 Oct 2026, also when the upload was meant for a different bid). If the Document ID is known but the Instance ID is new (the document was edited and saved again), the user is told which bid holds the earlier instance and can add the new one there as a change document.
  - **Automatic freeze.** When extraction completes successfully (every page read or deliberately skipped), the register is saved and frozen at once as baseline 1, together with the extraction snapshot E1. No one approves it. If extraction does not complete, nothing is frozen and the read can be retried.
  - **After the freeze** every difference is a versioned extraction correction or customer change on top of the baseline (C-04, unchanged). Exceptions stay in the queue; resolving one is a correction.
  - **Knowledge and reassessment** write assessment records (C-29), never requirement rows. A reassessment is an explicit, versioned action.
  - "Send for assessment" no longer publishes; it only routes and dispatches. The bid manager's Publish button is removed.
- **Integration feasibility.** Fits with rework. The file fingerprint is already computed and indexed; the PDF library in use reads the trailer `/ID` and the XMP metadata, and Word settings are read from the file directly, so no new library is needed. The two IDs go into a new table beside the document, so finding a known instance across bids is one lookup. Embedded IDs are written by the authoring tool: some tools omit or reuse them, hence the fingerprint fallback. The freeze is today's publish, called at the end of a successful extraction instead of by a person; its checks (a read main RFP, at least one verified requirement) define "successful". What changes: the rule that the same file in two bids is two documents is reversed; the review window between E1 and publishing disappears, so every fix becomes a versioned correction (before routing a correction returns no answers, but it does create the next baseline); a re-read is no longer possible after the freeze (open question 7); the Publish button, its walkthrough step and the tests that publish by hand change. The one-click samples upload the same files as the seeded bids, so they would open the seeded bids instead of creating new ones, which changes the intake part of the walkthrough.
- **Checked by.** Uploading the same file twice opens the first bid; requirements are frozen right after extraction with no person acting; a knowledge-base change, a catalog refresh or a re-match leaves every requirement row and baseline unchanged (a test compares them before and after).
- **Open.** Open question 7.

### C-28. Product catalog refreshed from the official Flex product page

- **Asked.** Scrape the official Flextronics product catalog page ([flex.com/products](https://flex.com/products), decided 15 Oct 2026, with other official pages); keep each version of a product's name so name changes can be traced; refresh on server start or restart and every 24 hours through a scheduled job; store the catalog in the database with source references and refresh timestamps.
- **Today.** The catalog is three files (products, catalog items, business units), compiled by hand from public Flex pages retrieved on 12 Oct 2026, each item with its source link but no retrieval time. It is read once per server process. There is no start-up hook, scheduler, outbound web request or HTML-parsing library in the application. The matcher's instructions include the product list, so any change to a product name, description or the list itself changes every frozen matcher answer.
- **Public page check (15 Oct 2026).** [flex.com/products/power-and-cooling](https://flex.com/products/power-and-cooling) is plain HTML (no script rendering, forms or pagination). It groups products under Critical Power, Embedded Power and Liquid Cooling, each with a name, key features and a link. Most product detail pages are on the unit sites (Anord Mardix, Crown Technical Systems, EP², JetCool). The page has no datasheets. The site's robots.txt allows crawling except its administration area. The page shows a copyright notice; no terms of use were seen on it.
- **Change.**
  - **Sources** (decided 15 Oct 2026): [flex.com/products](https://flex.com/products) and the official pages it links to for the units in scope: [power and cooling](https://flex.com/products/power-and-cooling), [power modules](https://flex.com/products/power-modules), and the product pages of Anord Mardix, Crown Technical Systems, EP² and JetCool. Automotive and components (Coreworks and the other component makers listed there) are outside the domain and are left out. Each site's robots.txt is checked on every refresh.
  - **Tables**: catalog sources (URL, publisher, retrieval time, response status, content fingerprint), catalog products (a stable key from the product's link, unit, category, active) with **product versions** (name, key features, link, source, valid from, valid to), and a refresh log. A changed name or description closes the old version and opens a new one, so every earlier name stays traceable and a bid can show the name it was assessed with.
  - **Refresh** on server start and every 24 hours, inside the API process, one refresh at a time. A failed refresh keeps the last good catalog and logs the failure. Without network (the laptop demonstration) the stored catalog is used.
  - **Provenance.** Scraped records keep their source and time. They show that a product exists and what is published about it; they are not proof of compliance. A product-compliance claim needs product evidence (a verified datasheet or an approved engineering rule) and review (C-29, point 3).
  - **Catalog versions.** A refresh that changes content creates a new catalog version. Matching and assessments record the version they used, and an existing bid keeps its version until a reassessment is requested. A refresh therefore never changes a bid's matches silently, and the frozen answers stay valid.
  - Curated unit data and engineering rules stay as they are.
- **Integration feasibility.** Fits with rework. Reading the page needs only the HTTP client already installed and the standard-library HTML parser; no new library. The work is in the integration: about ten parts of the system read the catalog files and move to database reads, and the matcher must read a pinned catalog version so frozen answers keep working. Reading four unit sites, each with its own page layout, is most of the effort; each gets a small parser and a check that fails loudly when its layout changes.
- **Checked by.** Starting without network uses the stored catalog without error; with network the records carry source and time; a refresh that changes a product leaves existing bids' matches unchanged; each refresh appears in the log.
- **Open.** None.

### C-29. Source-backed knowledge base and retrieval (RAG)

- **Asked.** A source-backed knowledge base built from engineering references, documented product capabilities and reviewed historical examples, supporting requirement interpretation and bid assessment, in eight points: separate collections; source context kept during ingestion; review controls; versioned database records as the authority; task-specific retrieval; a controlled feedback loop; explainable assessments; validation of the first implementation. Classifier training and clustering are out of scope.
- **Today.** Two retrieval indexes exist: a long-term index (products, catalog items, past responses, approved knowledge items) and a per-bid index of RFP passages with page and line. Embeddings are frozen per whole index; a keyword (TF-IDF) search is the fallback; the two are never combined; the only filter is the unit. The knowledge queue is item-level (requirement, response or decision; queued, approved, rejected), curated by the bid manager; approved items are kept in a local file, not the database. Retrieved evidence is shown to people but kept out of model prompts on purpose (design rule R2). No record says which evidence an assessment used; frozen model answers record only the task and model. Evaluation tools exist for the reader (golden list) and for model changes (model-change guard); there is no retrieval measure.
- **Change** (by point of the request):
  1. **Collections**: engineering references (specifications, technical guides, publications); product capability evidence (catalog records, verified datasheets, approved engineering rules); reviewed examples and experience (validated classifications, corrected mappings, approved responses, lessons learned); current bid evidence (the bid's RFP, addenda, extracted requirements and specialist assessments). Bid evidence is filtered to its bid inside the retrieval service, never left to the caller. Material becomes reusable only after review.
  2. **Ingestion with source context**: each source is registered with publisher, revision, scope, permissions and file fingerprint. It is parsed with the existing page and line model (PDF, Word, Excel), keeping headings, tables, footnotes and operating conditions; every passage keeps its exact location. The model proposes topics, content types, technical attributes, applicability and ambiguities; these annotations are stored beside the original passage and never replace it.
  3. **Review controls**: document-level review admits a reference document; item-level review covers derived facts, engineering rules and reusable examples; review rights go to qualified specialists by role and unit. Scraped catalog content keeps its provenance; product-compliance claims need product evidence and review.
  4. **Versioned records as the authority**: source documents, passages, knowledge items, review states, applicability and lifecycle (draft, in review, published, retired) are database records; every change is a new version. Retrieval indexes are built from published records and can always be rebuilt. An **assessment record** keeps the evidence versions, citations, model and prompt version, conclusions and unresolved questions of each assessment.
  5. **Task-specific retrieval**: one retrieval profile per task (requirement interpretation, technical explanation, product matching, numerical assessment, response drafting, executive summary) sets the collections, filters (access, applicability, bid, review state) and number of passages. Semantic and keyword results are combined. The selected evidence goes into the prompt with citation identifiers; claims without a citation are dropped. Retrieval supports extraction but never creates requirements: obligations come only from the bid's own documents.
  6. **Feedback loop**: specialist corrections stay in the bid's history (as today). A useful correction can be nominated, reviewed and published as a reviewed example with its conditions and limits. Examples cover requirements, preferences, background information, partial compliance and insufficient evidence. Illustrative answers (such as today's sample past responses) are excluded from verified evidence.
  7. **Explainable assessments**: each returns the conclusion, the supporting RFP passages, the reference or product evidence, the review status and any missing information, conflicts or assumptions. The measures of section 2 are shown separately (C-23). A knowledge change triggers nothing by itself; an explicit, versioned reassessment keeps the earlier results and the frozen requirements.
  8. **Validation**: an independently reviewed evaluation set measures extraction coverage, interpretation accuracy, retrieval relevance, citation support, numerical comparisons, handling of unknowns and isolation between bids. The reader's golden list and the model-change guard are reused.
- **Delivery in phases** (the request's priority order): R1 source registration, reference ingestion and document review; R2 reviewed-example memory and the feedback loop; R3 retrieval in the model calls with assessment records and citations; R4 explainable assessments and versioned reassessment; R5 the evaluation set and its report.
- **Integration feasibility.** Fits with rework; the largest change. Reusable: the page and line model for parsing, the embedding gateway and frozen vectors, the keyword search, the knowledge queue and audit log, the append-only snapshot pattern, the response outline's citation guard and the model-change guard. New: about six tables, an in-context review list (see C-33), retrieval profiles, combined ranking and per-document vector storage (today a change to one document re-embeds its whole index). Rework: design rule R2 changes. Once evidence enters prompts, the frozen matcher and outline answers are generated again with the live model, and prompts change whenever reviewed evidence changes; this is why evidence versions are pinned per assessment. Content: engineering references and verified datasheets must come from the business. Published standards (IEEE, IEC, UL) are licensed documents and cannot be collected or shared freely. The open decision on an enterprise-hosted model for non-public bids remains.
- **Checked by.** Every cited passage opens at its exact location; no evidence from another bid ever appears; the number of requirements of a bid is unchanged by retrieval; the evaluation report covers all seven measures of point 8.
- **Open.** Open questions 9 and 10.

### C-30. Requirements page merged into Requirement Traceability

- **Asked.** Remove the separate Requirements page, since requirements are already shown on the Traceability page. Rename Traceability to **Requirement Traceability**.
- **Today.** The Requirements page holds the Register and Exceptions tabs, filter chips and search, edit, split, merge, ungroup, exclude with a reason, restore, the history of each requirement, adding a missed requirement by selecting lines, linking or dismissing exceptions, corrections with a reason after publishing, Publish, and the extraction snapshots. Traceability shows each requirement with its source and match in the second pane, but has none of these actions. The Requirements page is linked from the step bar, the top bar, the Changes, Bid decision and Compliance matrix pages, and has its own walkthrough chapter.
- **Change.**
  - The Requirements step is removed. The actions it holds that are still needed move to Requirement Traceability: the exception queue (link to lines, dismiss), corrections with a reason (add, edit, split, merge, exclude), adding a requirement by selecting lines, and the history of each requirement. The Publish button goes (C-27).
  - Steps inside a bid: **RFP · Requirement Traceability · Assessment · Compliance matrix · Bid decision**, with Changes as a separate link. The old address redirects to the new page.
- **Integration feasibility.** Fits with rework. The actions call existing API routes, so the backend does not change. The work is moving the page's controls into the second pane of Requirement Traceability, which today shows the register from one data load and gains an Exceptions view; the line picker moves with them. Links from five pages and three walkthrough chapters are updated. Done after C-27, so Publish does not need to move.
- **Checked by.** Every action of the old page is reachable on Requirement Traceability; old links redirect; the walkthrough shows the new step.

### C-31. API paths say "bids"

- **Asked.** Replace the remaining `opportunities` wording in API paths with `bids` and update the matching calls in the web application.
- **Today.** 38 API routes in ten modules start with `/api/opportunities`; 20 web files call them; the tests use them about 318 times in 19 files; five walkthrough chapters call them. The browser page addresses use the same word (`/opportunities/...`, in 13 more web files), so a blind text replacement would change them too. Visible text already says "Bid".
- **Change.** `/api/opportunities/...` becomes `/api/bids/...` in every module, the web application's API client, the tests and the walkthrough. Internal module names, table names and stored identifiers (`OPP-0001`) stay; whether the visible bid ID changes remains open (changes.md open question 2).
- **Integration feasibility.** Fits. The change is mechanical but wide: route definitions, web calls, tests and walkthrough change together in one coordinated change that replaces API paths only, not page addresses; the full test suite and the walkthrough run before it is shared. Frozen model answers contain no API paths and are unaffected. No old paths are kept alongside: the web application is the only client.
- **Checked by.** No `/api/opportunities` path is left in the API, the web application, the tests or the walkthrough; the full test suite and the walkthrough pass.
- **Open.** Open question 11.

### C-32. Filtering and sorting on Requirement Traceability

- **Asked.** Add filtering and sorting to the Requirement Traceability page.
- **Today.** Traceability has no search, filter or sort; the only state in the page address is the selected requirement (`#REQ-...`). The summary counts on the Assessment and Bid decision pages already link to Traceability with `?category=` or `?offering=` (built 15 Oct 2026), but the page does not apply them yet. The Requirements page already has filter chips and a text search that can be reused.
- **Change.** Filters: category, offering type, unit, response state and compliance, source verified or exception, origin (extraction, correction, customer change), page range and text search. Sorting: RFP order (the default), requirement ID, category, unit, compliance and last change. Filters are kept in the page address, so summary counts can open a filtered view (this delivers the optional drill-down C-20).
- **Integration feasibility.** Fits. All rows are already loaded in one call, so filtering and sorting run in the browser with no API change.
- **Checked by.** Each filter and sort gives the expected rows on the Syracuse bid; a filtered address opened in a new tab shows the same rows.

### C-33. Knowledge base page removed

- **Asked.** Remove the dedicated Knowledge base page from the screens. Keep the knowledge storage, retrieval and review that RAG needs.
- **Today.** The top bar links to a Knowledge base page where the curator (the bid manager) approves or rejects queued items. "Send to knowledge base" buttons sit on Traceability, the response outline and the Bid decision page. A walkthrough chapter covers the page.
- **Change.** The page, its top-bar link and its walkthrough chapter go. Storage, retrieval and review stay. Review moves into context: each reviewer sees the items waiting for their review in My work and decides there (C-29, point 3). The "Send to knowledge base" buttons become "Nominate as a reviewed example" (C-29, point 6).
- **Integration feasibility.** Fits, but the order matters. The page is the only review screen today, so it is removed once the in-context review list exists; otherwise review would be possible only through the API. Several walkthrough chapters refer to it and are updated.
- **Checked by.** No link to the page remains; a nominated item can be reviewed from My work; approved items are still found by retrieval.

### C-34. Flexible workspace: draggable, detachable panes

- **Asked.** Make all three workspace panes draggable and detachable. Each pane can open in a separate browser tab or window, so people can arrange the workspace across three monitors.
- **Today.** The three panes live in one page and share its state; selecting a requirement scrolls the linked panes inside that page. Each pane has Linked / Unlinked and Enlarge / Restore (C-15, built). Nothing in the web application drags, resizes, opens windows or sends messages between windows today.
- **Change.** Each pane can be dragged to reorder and resized in the main window, and detached with "Open in new window". Detached panes follow the selection through the browser's same-origin messaging, respecting each pane's Linked or Unlinked setting. Closing a detached window returns its pane to the main window. The layout is remembered per browser.
- **Integration feasibility.** Fits with rework. No new library is needed: the browser's own drag and drop, resizable areas and same-origin messaging (BroadcastChannel) cover it. The panes are split out of the page into parts that can also show alone at their own address, each loading its own data; the sign-in cookie is shared by all windows of one browser, so there is no second sign-in. Limits: the walkthrough runs in the main window only; browsers open a new window only from a click; the walkthrough's pane targets change.
- **Checked by.** With three windows on three monitors, selecting a requirement in one moves the linked panes in the others; an unlinked pane stays put; closing a window restores its pane.

## 6. Integration Feasibility (quick analysis)

### 6.1 Verdict

No change is blocked technically. The unit manager (C-25), the sign-up role policy (C-26), the meaning of the Document ID (C-27) and the catalog sources (C-28) were decided on 15 Oct 2026. The table summarises where each change lands.

| ID | Builds on | Main integration point | Feasibility | Size |
|---|---|---|---|---|
| C-23 | Bid summary, criteria, matches | New measures need catalog provenance (C-28) and reviewed evidence (C-29); first version from today's matches | Fits with rework | L |
| C-24 | Compliance matrix, decisions | New dates and approvals; validation moves from the bid manager to the unit | Fits with rework | M–L |
| C-25 | Category list, dispatch | Non-technical items routed to units; name-based checks become role checks | Fits with rework | M |
| C-26 | Sign-in, token, account table, role checks | Sign-up with a chosen role; knowledge routes; name checks become role and unit checks | Fits | M |
| C-27 | Extraction snapshot, versions | Publish step removed; embedded Document and Instance IDs with fingerprint fallback; sample uploads would open the seeded bid | Fits with rework | M |
| C-28 | Catalog files with source links | Catalog files become versioned database records; several sites; matcher pinned to a catalog version | Fits with rework | M–L |
| C-29 | Indexes, knowledge queue, citation guard | Design rule R2 reversed; frozen answers regenerated once; new tables | Fits with rework | XL |
| C-30 | Traceability page | Requirements actions moved into pane 2 | Fits with rework | M |
| C-31 | All module routers | One coordinated rename across API, web, tests and walkthrough | Fits | S–M |
| C-32 | Traceability data | Client-side filters kept in the address | Fits | S |
| C-33 | Knowledge module | Review list in My work before the page goes | Fits | S |
| C-34 | Linked / Unlinked and Enlarge panes | Panes split out of one page; same-origin messaging between windows | Fits with rework | M |

### 6.2 Cross-cutting points

1. **Frozen model answers.** The matcher's instructions contain the catalog, so a catalog refresh (C-28) or evidence in prompts (C-29) changes them and the frozen answers no longer apply. Each bid therefore pins the catalog and evidence versions it was assessed with; frozen answers are generated again once with the live model; the offline demonstration keeps working from the pinned versions. A new bid on a laptop without a model key still falls back to retrieval-only matches.
2. **Database changes.** There are no migrations: a new column on an existing table stops the server until the demonstration database is reset. New data goes into new tables where possible, and a reset follows each schema change. Accounts are kept apart and survive a reset.
3. **Rules that are reversed** (section 1 table): publish by the bid manager, validation by the bid manager, API paths unchanged, and evidence kept out of prompts.
4. **One permission model.** Authorization is split today between role checks and display-name checks; C-25 and C-26 move both to the role and unit in the token, together.
5. **Walkthrough, tests and documents.** Removing the Requirements and Knowledge base pages, renaming the API paths and roles, and the automatic freeze break walkthrough chapters and tests. The walkthrough and the current-system documents are refreshed once the screens settle.
6. **Iteration-2 work still open folds in.** The Assessment screen gains the assessment panel and the schedule (C-23, C-24), and its Send for assessment stops publishing (C-27); the workflow configuration uses unit managers and designers / engineers (C-25); the Traceability side of the drill-down (C-20) is delivered by C-32.

### 6.3 Recommended order

1. **C-31** API rename, as one coordinated change while little else is in progress.
2. **C-25** and **C-26** together: one role and permission model.
3. **C-27** automatic freeze (removes Publish; needed by C-30 and by routing).
4. **C-30** and **C-32** Requirement Traceability, then **C-34** detachable panes.
5. **C-24** schedule and compliance approvals (needs the unit manager of C-25).
6. **C-28** catalog refresh with pinned catalog versions.
7. **C-29** in phases R1 to R5; **C-33** once the in-context review list exists (R2); **C-23** first from today's matches, then on reviewed evidence after R3.

## 7. Open Questions (Needs confirmation)

| # | Question | For |
|---|---|---|
| 1 | Settled (15 Oct 2026): the unit manager is the unit's product manager | — |
| 2 | Which non-technical requirements go to every participating unit's manager, and which stay with the bid desk (bid-level administrative items)? | Zensar point of contact |
| 3 | Does the bid manager still record a separate go/no-go call (13 Oct 2026 decision), or do the schedule and compliance approvals replace it? | Zensar point of contact |
| 4 | How much consolidation time is allowed between the latest unit date and submission, and is the RFP due date read from the RFP or entered? | Zensar point of contact |
| 5 | Settled (15 Oct 2026): the person chooses a role at sign-up, except administrator, which is seeded by the server | — |
| 6 | Settled (15 Oct 2026): the Document ID and Instance ID are the IDs embedded in the file; the same instance arriving for a different bid opens the existing bid | — |
| 7 | After the automatic freeze, is a reasoned re-read of the same instance (snapshot E2) still allowed? | Zensar point of contact |
| 8 | Settled (15 Oct 2026): flex.com/products and the official pages it links to for the units in scope. Still open: the site owner's permission for automated retrieval before a pilot | Zensar point of contact |
| 9 | Which engineering references and verified datasheets can be used (and are licensed), who reviews each collection, and who reviews the evaluation set? | Zensar point of contact |
| 10 | The preliminary-feasibility formula and its weights | Zensar point of contact |
| 11 | Should the browser page addresses also change from `/opportunities/...` to `/bids/...`? | Zensar point of contact |

## 8. What Does Not Change

- The modular architecture and module boundaries; the model gateway with frozen answers; the append-only audit log.
- Traceability to page and lines as the centre of the product; the three panes (now movable).
- Agents propose and named people decide; requirement identification never falls back to pattern matching; retrieval never creates requirements.
- The extraction snapshot E1 and versioned corrections and customer changes (C-04).
- Simple signed-token sign-in (C-09), extended rather than replaced.
- Table names and stored identifiers.
