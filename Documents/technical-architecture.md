# Layer 0: Technical Architecture

## 1. Purpose, Who This Is For, and Status

**Purpose.** This document describes how Layer 0 is built: the modules, the data they hold, how an RFP is read into traceable requirement line items, how those line items are matched to business-unit products, and how they move through the opportunity workflow to the final response. It is the build reference for the PoC in the **Layer0-Flex** repository.

**Who this is for.** Developers building Layer 0, and the Zensar point of contact who reviews the design. Business background is in [business-and-domain-background.md](business-and-domain-background.md); the problems are in [problem-mapping.md](problem-mapping.md); the earlier code lines and how their modules are ported are in [architecture-overview.md](architecture-overview.md).

**Status (8 Oct 2026).**
- The **workflow** is the one described in the review meetings of 22 Sep, 5 Oct and 8 Oct 2026 ([project-overview.md](project-overview.md) section 7). It has not been formally signed off.
- The **architecture is not being redesigned.** The 8 Oct review asked that the existing modules be wired in, tested and used, and that the three screens be delivered. This document maps those modules onto one code base.
- **Stage 0 is built** in Layer0-Flex: a running skeleton with every module in place, a demonstration seeded from the real Syracuse RFP, and a smoke test. Stage 0 reads native PDF text only, and matching runs in retrieval-only mode until model answers are generated (section 13).
- The document-reading tools (PyMuPDF, pdfplumber, Tesseract OCR) were decided by the project team on 7 Oct 2026. Everything else is **Proposed (inferred design)** unless it is marked built.
- Open points are in section 14 and are marked **Needs confirmation** where they appear.

## 2. What the System Must Do

Layer 0 follows one opportunity from the arrival of the RFP to the final response. The roles are the **bid manager**, who owns the opportunity and knows all the business units, and, in each business unit, a **product manager** and a **design engineer** (Expected, review meetings).

1. **Read the RFP** and break it into requirement **line items**. Each has a unique requirement ID and traces back to its exact source: document, page, lines (for example "page 55, lines 46 to 49") and quoted text.
2. **Match each requirement to the product offerings of the business units.** The result is the unit, the product or configuration, and the offering type: configure-to-order (CTO), semi-custom, or engineered-to-order (ETO). One RFP may involve one or several units.
3. **Support the human decisions**: which units take part, and go or no-go. A named person decides.
4. **Dispatch in one step.** Each participating unit receives the main RFP and its own line items.
5. **Collect checklist responses.** For each assigned line item, the unit states whether it is met and with what. The response is then validated.
6. **Consolidate.** Responses flow back to the bid manager, who checks that every requirement is answered and assembles the final response.

These six build steps cover the seven workflow steps in [project-overview.md](project-overview.md) section 7: workflow step 2 (participation) is suggested by matching here and decided in step 3; workflow steps 4 and 5 (set up the workflow, assign work packages) are the one-step dispatch.

Across every step: an append-only audit history, data retained for the life of the project (warranty included), and change requests handled as a delta against the frozen baseline.

**The three screens** are the centre of the demonstration: (1) the original RFP, (2) the requirement breakdown, and (3) the requirement-to-product mapping with each unit's response. The three are linked (section 9).

## 3. Design Rules

| # | Rule | What it means in the build |
|---|---|---|
| R1 | **Everything traces to the source** | Every requirement carries document hash, page, line range, highlight boxes and the verbatim quote. A location is never invented: a quote that cannot be found on the page is stored as `UNANCHORED` and shown with a warning |
| R2 | **Agentic first pass, then frozen** | Agents propose; a person reviews; the approved set is frozen as a baseline. Every model answer is cached, so a re-run returns the same answer. Later runs process only the delta (change requests) |
| R3 | **Changes touch only what changed** | A change creates new versions of the affected requirements only, and returns their unit responses for review. A change that alters the whole RFP starts a new opportunity, decided by a person |
| R4 | **Agents propose; people decide** | The model is called through one gateway only. It proposes line items, matches and drafts. Participation, go/no-go, freezing, and accepting a response are named-person decisions |
| R5 | **Unknown never passes** | Unreadable pages, missing model answers and unanchored quotes are reported, never defaulted or skipped. Requirement identification never falls back to pattern matching (regex) |
| R6 | **Every engagement is separate** | The opportunity ID is on every record. Requirement IDs embed it, so they are unique across all opportunities |
| R7 | **Rules and knowledge as data** | Business units, products, past responses and thresholds live in versioned data files, not in code |
| R8 | **Append-only audit** | Every decision and change is an audit event. The database rejects updates and deletes on the audit table |
| R9 | **Keep data local unless decided** | RFP files stay on the machine running Layer 0. The PoC sends text to the hosted Azure OpenAI model only for the public sample RFP; using a hosted model on real customer RFPs needs a decision (section 14) |

## 4. System Overview

One Python API service, one database, one file store, and a Next.js web application. The back end is a **modular monolith** built as **modular MVC**: each module is a package with its own model (database tables), service (business logic and the public contract) and controller (JSON routes under `/api`); its views are the module's pages in the Next.js application. All back-end modules run in one process. A PoC built by a small team does not need message queues or microservices.

```text
                      +---------------------------------------------------------------+
  Next.js  <--JSON--> |  FastAPI app  (app/main.py mounts each controller at /api)     |
                      |                                                               |
                      |  opportunities   engagement workspace, documents              |
                      |  ingestion       PDF -> page layout model (lines, boxes)      |
                      |  requirements    reader agent -> line items, review, freeze   |
                      |  catalog         business units, products, past responses,   |
                      |                  retrieval index (RAG), BOM source            |
                      |  matching        matcher agent -> unit, product, offer type   |
                      |  decisions       participation, go/no-go records              |
                      |  workpackages    one-step dispatch, inbox, checklist          |
                      |                  responses, validation                        |
                      |  consolidation   coverage check, compliance matrix            |
                      |  changes         delta against the baseline (stage 5)         |
                      |  trace           three linked screens, portfolio (read-only)  |
                      |                                                               |
                      |  core: config, db, audit (append-only), model gateway, web    |
                      +-------------+---------------------+---------------------------+
                                    |                     |
                     SQLite (PoC; PostgreSQL later)   File store: originals by SHA-256,
                                                      layout JSON, page images
                                    |
                     Model gateway -> Azure OpenAI GPT-4o (cached in data/llm_cache/)
                     Tesseract (local executable, OCR regions)
```

### 4.1 Technology

| Concern | Choice | Notes |
|---|---|---|
| Language | Python 3.12 | Used by every earlier code line |
| API | FastAPI + Pydantic | JSON routes under `/api`; interactive docs at `/docs` |
| Web | Next.js (App Router, TypeScript, React), plain CSS | One route folder per module's pages; `/api/*` is proxied to the FastAPI service |
| Database | SQLAlchemy 2 over SQLite for the PoC | Same code runs on PostgreSQL for several concurrent writers. Tables are created at start-up; migrations are added before a pilot |
| Native PDF text | **PyMuPDF** | Lines with positions, page sizes, page rendering for screen 1 |
| Ruled tables | **pdfplumber** | Table and cell boundaries (stage 1 work) |
| OCR | **Tesseract 5.5**, called as a local program with TSV output | For pages with no text layer (stage 1 work). Page 83 of the Syracuse RFP is such a page |
| Language model | Azure OpenAI, GPT-4o deployment, through the model gateway | Structured JSON output (JSON schema, strict), temperature 0. Every answer is cached by task, model, prompt and schema |
| Retrieval (RAG) | TF-IDF over products and past responses (ported from v0.3.0) | Explainable keyword scores; can be swapped for embeddings without changing callers |
| Change detection | Python `difflib` | Section 8 |

**Licence check (Needs confirmation before any client use).** PyMuPDF is dual-licensed: AGPL-3.0 or a commercial licence from Artifex. AGPL is acceptable for an internal PoC; a pilot or product needs a commercial licence or a replacement. pdfplumber (MIT) and Tesseract (Apache 2.0) have no such obligation.

### 4.2 Code layout and module rules

```text
app/
  main.py                  mounts every module's controller; creates tables
  core/                    config, db, audit, llm (model gateway), web (templates, acting user)
  modules/<name>/
    models.py              tables owned by this module
    service.py             public contract: the ONLY file other modules may import
    controller.py          JSON routes under /api
    agent.py               (where needed) prompts and schemas sent through the gateway
web/                       Next.js application (the views)
  app/<route>/page.tsx     one route folder per screen, owned by the module owner
  components/              shared and per-module components
  lib/api.ts, lib/types.ts API client and response shapes
data/
  RFP/                     sample RFPs (Syracuse PDF; synthetic text samples)
  knowledge_base/          business_units.json, products.json, past_responses.json
  seed/                    demo opportunity
  llm_cache/               frozen model answers (committed)
  store/                   local uploads, layouts, page images, database (not committed)
reference/                 earlier code lines, read-only, for porting
scripts/seed_demo.py       loads the demo through the real services
tests/test_smoke.py        end-to-end smoke test and module-boundary check
```

Rules:
- A module imports another module's `service.py` only, never its models, agent or controller. A test enforces this.
- Tables do not reference another module's tables through the ORM. They hold the other record's ID (for example `req_id`).
- Every write records an audit event in the same transaction.
- The web application calls only `/api` routes; it holds no business logic.
- **Any stage can run.** Each module ships a working implementation from stage 0, a simple one where needed. A module improves behind its unchanged contract, so the application always runs end to end.

## 5. Step 1 in Detail: Reading the RFP

This turns a PDF into a **page layout model**: a structured record of every page with exact positions. Requirement extraction (section 6) reads this model, not the raw PDF.

```text
 PDF file
   |
 (5.1) intake: hash, store, register                                   [built]
   |
 (5.2) page reading (PyMuPDF): lines in reading order, boxes, size      [built]
   |
 (5.3) routing: native text, or whole-page OCR    [built]; tables       [stage 1]
   +--> tables (pdfplumber)   +--> OCR (Tesseract)
   |
 (5.4) clean-up: headers/footers, contents pages [built]; headings     [stage 1]
   |
 page layout model (JSON per document and pipeline version, never edited)
```

### 5.1 Intake

- The file is stored under its SHA-256 hash and never modified. Each opportunity gets its own document record (`<opportunity>-<first 12 hash characters>`), so the same file sent for two opportunities stays two separate documents (rule R6); the hash is kept on the record, and every anchor points to the record.
- A document record links the file to its opportunity, with its role (main RFP, addendum, Q&A, change, other).
- Files other than PDF are stored and reported as **unsupported**. Coverage is never claimed for a file that was not read (rule R5).
- Damaged or encrypted PDFs are reported as failed, not skipped.

### 5.2 Page reading (built)

- PyMuPDF reads each page's text as lines in reading order. Each line gets a **line number within its page** (1-based), its text and its bounding box.
- Coordinates are PDF points (1/72 inch), origin at the top-left of the page, rounded to 0.01 so that two runs give identical output.
- A page with no text layer is marked **unreviewed** and shown with a warning on screen 1 (rule R5). On the Syracuse RFP this is page 83.

### 5.3 Region routing (whole-page OCR built 8 Oct 2026, ruled tables 9 Oct 2026; region-level OCR later)

| Situation | Method | Reason |
|---|---|---|
| A ruled table is found by pdfplumber | **Table**, kept beside the lines | Cell boundaries are kept; each line inside a cell points to its table, row and column |
| Native text is present and readable | **Native** (PyMuPDF) | Exact text and positions |
| Page has no text layer | **OCR**, whole page | A scanned page |
| Native text is unusable (unmapped characters above a threshold, starting value 5%) | **OCR** for that region | A font without a character map |
| An image inside a text page, above a minimum size (starting value 2% of the page), with no text over it | **OCR**, marked `figure_text` | Drawings can contain requirements |

Thresholds are starting guesses, stored as data and calibrated on real SpinCo RFPs. Each routing decision is stored with its reason.

**Built so far.** A page with no text layer, or whose text layer has more than 5% unmapped characters, is read by whole-page OCR. Without Tesseract (machines other than the parsing machine) such a page is flagged with the reason and never causes a failure. On the Syracuse RFP this reads page 83, a scanned drawing, into 106 lines (38 marked low-confidence), so every one of the 101 pages has a stated method. Two runs give byte-identical layouts.

**Tables (built 9 Oct 2026).** pdfplumber finds ruled tables (the "lines" strategy) and the layout keeps each one as rows of cells, with text and boxes in the same page points as the lines. The lines themselves are not changed: a line inside a cell only gains a reference to its table, row and column. Line numbers, highlights and every frozen model answer therefore stay valid when tables are added.

A grid is kept as a table when it has at most 20 columns and at least 30% of its cells filled; blank forms and drawing grids fall below that. Pages with more than 3,000 drawn lines and boxes are drawing sheets and are not searched. A table whose column edges line up with the last table on the previous page is linked as its continuation.

On the Syracuse RFP, 34 tables are kept, including the three-page technical data sheet (pages 72 to 74, linked as one table, rows such as "Drawing Size | 24 X 36 | Inch"). 1,475 lines are tagged with their cell. Two runs give byte-identical layouts.

**OCR details.** The region is rendered at 300 dpi and passed to Tesseract with fixed settings; the TSV output gives each word's box and a confidence from 0 to 100. Pixel positions are converted to page points (page x = region x + pixel x × 72 / 300). Words below a confidence threshold (starting value 60) mark the line low-confidence, and a requirement drawn from it always goes to a person. The Tesseract path is configuration (`TESSERACT_CMD`). Each call uses one thread so results do not vary between runs.

**Tables.** pdfplumber's "lines" strategy finds ruled tables. Each table records its box, rows, columns and cells; a table that continues on the next page is linked when the columns line up. Compliance-matrix rows are common requirement sources. Known limit: tables without ruling lines lose their cell structure (the text is kept).

### 5.4 Clean-up (headers, footers and contents pages built 8 Oct 2026; headings stage 1)

- **Headers and footers.** Lines repeated in the top or bottom band of most pages are marked as page furniture. They are kept but are never offered as requirements.
- **Table of contents.** A page is a contents page when it has a "Contents" heading near the top and mostly short entries, or when many lines end in dot leaders and page numbers. It is excluded from extraction. On the Syracuse RFP this marks page 54 only, and 346 header, footer and drawing title-block lines are marked as furniture; none of the known requirements is hidden. In the earlier regex-based line, contents headings became requirements; this rule, together with model-based reading, prevents that.
- **Headings and sections** from numbering patterns and font size, so each requirement can carry a section path.

### 5.5 The page layout model

```text
document: sha256, pipeline_version, page_count
  page: page, width, height, method (native | ocr | none), unreviewed
    line: n (line number within the page), text, bbox
    (stage 1: tables -> cells; furniture flags; toc flag; section tree)
```

The pipeline version names the tool versions and settings. The same file and pipeline version give a byte-identical layout model.

## 6. Requirement Extraction: the Reader Agent

### 6.1 From layout to line items

1. The reader agent sends one page per call to the model (several calls in parallel), each line prefixed with its line number. Measured on the Syracuse RFP, six pages per call missed whole specification pages because the model returns only a limited number of items per answer: recall against the golden list was 26% with six pages per call and 92% with one.
2. The model returns, per requirement: page, **verbatim quote**, a short restatement, a category (technical, compliance, commercial, schedule, submission, legal, staffing) and a section. It is told to skip contents pages, headers, footers, blank forms and signature blocks.
3. **Anchoring.** Each quote is searched for on its page, ignoring differences in spacing, quote marks and hyphen forms. If found, the requirement gets its page, line range and highlight boxes and is `EXTRACTED`. If not found, it is `UNANCHORED`, flagged, and never accepted without a person. The model's own page and line claims are never trusted on their own.
4. Line items are stored as drafts. A re-run before the freeze replaces the drafts. After the freeze, extraction is closed and changes go through section 8.

No regular-expression or keyword fallback exists for identifying requirements (rule R5). If the model is unavailable and no cached answer exists, the gap is reported page by page.

### 6.2 Model gateway and freezing

- One module (`app/core/llm.py`) calls the model. It asks for JSON that matches a schema.
- Every answer is stored in `data/llm_cache/<task>/<hash>.json`, keyed by task, model, system prompt, prompt and schema. The cache is committed to the repository. This gives:
  - **repeatability**: a re-run returns the first answer instead of a new one;
  - **a frozen first pass** that can be reviewed and versioned like code;
  - **offline demonstrations**: with `LLM_PROVIDER=mock`, only cached answers are used and no key is needed.
- Changing a prompt or schema changes the key, so a stale answer is never reused by mistake.
- Retrieved reference material (section 7.1) is supplied in prompts. Fine-tuning is not used.

### 6.2a Grouping into requirements and sub-requirements (built 9 Oct 2026)

The reader lists every obligation separately, so a list such as "submit these twelve drawings" arrives as twelve line items. On the Syracuse RFP that gave about 810 line items, many of them closely related. Two steps follow the reader:

1. **Duplicates** are found by text comparison, not by the model. A quote that repeats an earlier one almost word for word (often a cover-page restatement of the specification) is marked as a duplicate of the first occurrence. A reviewer can restore it.
2. **Grouping agent.** For each page, the model receives the numbered line items and proposes groups that form one obligation: a drawing list, a list of standards, the features of one piece of equipment, the parts of one insurance requirement. It returns only item numbers and a short title. It never changes or drops an item: anything it does not place stays a requirement on its own, and invalid answers are discarded. The answers are cached and frozen like the reader's.

A group is one **requirement** made of **sub-requirements**. It keeps every sub-requirement's highlight and quote. Matching, dispatch, Traceability and the final response work on requirements, that is groups and stand-alone items. Approving or rejecting a group applies to its undecided sub-requirements. **Ungroup** releases the sub-requirements as requirements again.

On the Syracuse RFP: 814 line items become 348 requirements (162 groups and the stand-alone items), and 21 duplicates are marked.

### 6.2b Retrieval indexes: long-term knowledge and the per-RFP index (built 10 Oct 2026)

Retrieval-augmented generation (RAG) uses two kinds of vector index, built on one shared helper (`app/core/vectors.py`):

| Index | Holds | Lifetime | Used for |
|---|---|---|---|
| **Long-term** | Business-unit products and past responses; later, approved answers from finished bids (knowledge-base queue) | Grows as the business learns | Product search, matching evidence, response drafting |
| **Short-term** (one per RFP) | The RFP split into passages (about one paragraph each), with page and line numbers; headers and footers left out | Rebuilt every time the RFP is loaded; belongs to its opportunity only (rule R6) | "Search this RFP", drafting answers from the RFP's own wording, matching addenda to the baseline |

Embeddings come from the Azure embedding deployment (`text-embedding-3-small`, shortened to 256 dimensions) through the model gateway. Like model answers, they are frozen: the vectors of a set of texts are stored under a hash of the texts and committed for the sample RFP and the knowledge base. Re-indexing unchanged text therefore costs nothing, and the Syracuse index (about 600 passages) takes about 8 seconds the first time. Without the embedding service, for example on the offline laptop package, an index falls back to keyword (TF-IDF) search and says so.

The short-term index does not reduce the reader's input: every page still has to be read once to find its requirements. Its value is retrieval across the whole RFP. Whatever feeds a frozen prompt must give the same result online and offline, so prompts never depend on which search mode is available.

### 6.2c Keeping model calls and tokens down (built 10 Oct 2026)

Measured on the Syracuse RFP (101 pages), one first read of a new RFP:

| | Before | After |
|---|---|---|
| Model calls | 518 | 208 |
| Input tokens | about 464k | about 251k |
| Output tokens | about 98k | about 81k |
| Cost at GPT-4o list price | about $2.10 | about $1.40, less with the cached catalog prefix |

Three changes:
1. **Rules first.** Only technical and compliance requirements go to the matcher. Submission, schedule, commercial, legal and staffing requirements go to the bid manager by rule, with no model call (136 of 348 on Syracuse; the model had sent almost all of them there anyway).
2. **One matcher call per page.** The rules and the whole catalog (products and past responses, about 1,450 tokens) form the fixed opening of every call, which the model service caches and bills at a discount; then come all the product requirements of that page. Each answer is still checked against the catalog. 353 calls become 62.
3. **Short pages share a reader call** while their lines total 60 or fewer (at most 4 pages); longer pages stay alone. A page that stays alone keeps its exact earlier prompt and frozen answer. Reader accuracy is unchanged: recall 91.9% against the golden list.

Answers are frozen as before, so a re-read of the same RFP makes no call at all. A cheaper model for grouping and matching (a `gpt-4o-mini` deployment) would cut the cost about tenfold again; it needs a new Azure deployment.

### 6.3 Human review and freezing

The bid manager reviews each line item against its highlighted source (built 8 Oct 2026). The actions are:
- **approve** or **reject**, one at a time or for a selection;
- **edit** the short text or the category;
- **split** one line item that holds several obligations into parts. Each part is a piece of the original quote and is anchored again;
- **merge** several line items that are one obligation. The merged item keeps every source box and the joined quote;
- **add** a requirement the agent missed, by pasting its quote, which is anchored like any other.

Every line item has a history view (built 9 Oct 2026), rebuilt from the append-only audit log: its original wording, each later version with who changed it, when and why, and a timeline of every action on it. Split and merged originals are kept, marked as replaced, and drop out of matching, dispatch and the final response. The new items record which ones they came from. Each action is an audit event.

Freezing needs every active line item to be approved or rejected. A named person then **freezes** the approved set as **baseline 1**. From then on, requirements change only through new versions created by change handling. Adding a requirement by drawing a box on the page is a later addition.

### 6.4 The requirement record

```text
requirement
  req_id        REQ-<opportunity number>-<sequence>, e.g. REQ-0001-0042; unique across opportunities
  version       1, 2, ... (only the latest is current; all are kept)
  text          short restatement shown on the line item
  quote         verbatim source text
  document_id   the document record (opportunity + file hash); the hash itself is on the document
  page, line_start, line_end, bboxes   the exact source
  category, section
  provenance    EXTRACTED | UNANCHORED
  status        proposed | approved | rejected | split | merged | duplicate
  kind          item | group;  parent_id: the group a sub-requirement belongs to
  derived_from  the line items it was split from or merged from
  baseline      frozen baseline number, empty while draft
```

The provenance classes reuse the v0.3.0 `provenance/anchors.py` design; the record is the v0.3.0 requirement registry (M17) made the unit of work.

## 7. Matching, Decisions, Dispatch, Responses, Consolidation

### 7.1 Catalog and knowledge base (RAG)

- `business_units.json`: the working list of business units, with pillar, status, product manager and design engineer. EP² is part of SpinCo per written direction from the Zensar point of contact. EPC Power is listed as pending and is not offered.
- `products.json`: each unit's product families, offering type, description, retrieval keywords and BOM lines. The seed content is **illustrative** and must be replaced with each unit's real catalog (Needs confirmation).
- `past_responses.json`: past RFP answers per unit. Validated responses from finished opportunities are added here, which is the database-to-knowledge-base connector (stage 4).
- Retrieval ranks products and past responses for a requirement's text. Scores are kept as evidence.
- **BOM.** Layer 0 does not construct a bill of materials. Screen 3 shows the BOM lines of the matched product, read from the BOM source system. In the PoC the source is the catalog file; the real source system is Needs confirmation.

### 7.2 Matching (step 2)

For each approved requirement, the top retrieval hits go to the **matcher agent** with the requirement quote. It returns the unit, the product (chosen only from the candidates), the offering type and a short rationale citing the candidate. Commercial, submission and legal items are marked as not product items and go to the bid manager.

If no model answer exists, matching runs **retrieval-only**: the top product hit above a minimum score, marked as such. This is a fallback for routing, not for identifying requirements, and every match is shown for a person to accept, reject or change.

Offering types and the earlier automation tiers:

| Offering type | Meaning | Earlier tier |
|---|---|---|
| CTO | Catalog product with options, quoted through CPQ | `CTO_AUTOMATE` |
| SEMI_CUSTOM | Configured product plus workshop work for this customer | `ETO_GUIDED` (standard base, custom remainder) |
| ETO | Designed for the requirement; no existing product | `ETO_GUIDED` (basis of design, engineer approves) or `ETO_EXCEPTION` (engineer designs) |

### 7.3 Participation and go/no-go (step 3)

The **evidence pack** shows requirement counts by category, the units suggested by matching, the offering-type mix, unanchored items and unmatched items. The bid manager records which units take part, then go or no-go, each with a rationale. The decision record stores the evidence as it was shown. The v1.1 bid and portfolio checks are part of the evidence pack (built 10 Oct 2026), run on the real RFP rather than on hand-made records:

- **Deviations from the standard product.** The ratings in the RFP's own data sheet (its ruled tables, section 5.3) are compared with the standard ratings of the products the requirements are matched to. As in v1.1, a rating above the standard for voltage, current or frequency is high severity; for impulse level or momentary rating, medium. Each deviation cites its page and data-sheet row.
- **Capacity and portfolio conflicts.** For each unit taking part, its open work across every opportunity in Layer 0, plus what this opportunity adds, is compared with the unit's capacity. The other opportunities competing for the unit are named.

Both fill a go/no-go criterion. The standard ratings and capacities (`portfolio.json`) are invented placeholders until the units confirm them, and the page and the criterion text say so. Reading a value from a data-sheet cell is value parsing, not requirement identification.

### 7.4 Dispatch (step 4: one step)

On a go decision, one action creates an **assignment** for each requirement and its matched participating unit, owned by that unit's design engineer. Items that are not product items are assigned to the **bid desk** (the bid manager). A requirement may have assignments for several units. A unit's **work package** is its set of assignments, shown in its inbox with the main RFP and each line item's source. Dispatch can be repeated safely; it does not duplicate assignments.

Workflow templates per customer type (mandatory and optional steps) are not built. The review of 8 Oct asked to keep the workflow to one step.

### 7.5 Checklist responses and validation (step 5)

For each assignment, the unit records **compliance** (met, partial, not met, exception), the product or configuration that meets it, and a short response. The bid manager then **validates** it (validated) or **returns** it (returned, with a note). Every action is audited. Unit progress (validated out of total) is shown on the portfolio and on the three screens.

### 7.6 Consolidation (step 6)

- **Coverage check.** A requirement is *answered* when every assignment for it is validated. Anything else blocks completion and is listed.
- **Compliance matrix** export. An Excel workbook with a customer sheet (validated answers only, in customer words, in RFP order, sub-requirements with their references) and an internal tracking sheet. Every cell is written as text, never as a formula. Also a CSV: requirement ID, source (page and lines), category, requirement, quote, unit, product, offering type, compliance, response, validator, state, assignment status and responded by. The CSV starts with a UTF-8 byte order mark so that Excel reads non-ASCII text.
- **Response outline** (built 10 Oct 2026). Writing the final response remains a human task. A drafting agent gives the bid manager a first draft to edit:
  - **Chapters.** The outline follows a proposal, not the RFP's own headings: an executive summary, then one chapter per group of requirement categories (technical; compliance and legal; commercial and schedule; staffing; submission).
  - **Drafting.** The agent drafts each chapter only from the validated answers, with the RFP's wording for each one. It makes one call per chapter that has answers, plus one for the summary. It may not add products, ratings, dates, promises or qualities that the answers do not state, and it lists what the bid manager still has to add or confirm.
  - **Citations.** Every paragraph cites the answers it rests on. A paragraph without a valid citation is removed.
  - **Open requirements.** These are listed, never drafted. Answers that are not full compliance are shown separately.
  - **Related passages.** Passages from both retrieval indexes (this RFP and past responses) are shown beside the draft. They are kept out of the prompt, so a frozen draft does not depend on whether search runs on embeddings or keywords.
  - **Without a model answer.** When no model answer is available, the chapter shows the validated answers as they are, marked as not drafted.
  - **Download.** The outline downloads as Markdown.
  - **Known limit.** The drafts can still lean promotional in tone. The page labels them as drafts to edit.

## 8. Change Handling (stage 5)

Addenda, Q&A answers, change requests and execution-stage changes all use one path.

1. The change document is ingested like the RFP and linked to the same opportunity with the role "change".
2. Its candidate requirements are compared with the frozen baseline: section first, then text similarity (`difflib`). Each item is **added, modified, removed or unchanged**.
3. A person confirms the classification.
4. Only affected requirements get a **new version**. Added requirements get new IDs and are matched and dispatched.
5. Assignments of changed requirements are **returned** for review, and the owning units see them in their inbox.
6. **A drastic change.** If the share of modified or removed requirements passes a threshold (to be set), the system suggests a new opportunity linked to the old one. A person decides.

**Needs confirmation:** the threshold for a drastic change, and SpinCo's engineering change process.

## 9. Views

| View | Level | Shows |
|---|---|---|
| **Portfolio** | All opportunities | Every opportunity, its status, requirement count and each unit's validated/total responses |
| **Traceability** (the three screens) | One opportunity | (1) the RFP page with every requirement's source lines highlighted; (2) the requirement line items with ID, source and quote; (3) unit, product, offering type, rationale, BOM lines and unit responses. Selecting a requirement in any pane selects it in all three and opens its page |
| **Requirement review** | One opportunity | Line items with quote and source; approve, edit, reject; freeze |
| **Decisions** | One opportunity | Evidence pack, participation, go/no-go, dispatch |
| **Unit inbox** | One business unit | Its assignments across all opportunities, with the checklist response form and validation |
| **Final response** | One opportunity | Coverage, blocking items, compliance matrix download: an Excel workbook (a customer sheet with validated answers in customer words, in RFP order with sub-requirements and their references; an internal tracking sheet) and a CSV |
| **Response outline** | One opportunity (under Final response) | The drafting agent's first draft per chapter with cited requirements, what to add or confirm, the validated answers, what is still open, related passages; Markdown download |

Navigation: the top bar has three destinations (Opportunities, My work, Product catalog) and a New opportunity button. Inside an opportunity, a stepper follows the workflow order: RFP, Requirements, Traceability, Bid decision, Final response; a step is ticked once the opportunity has moved past it. Change handling is shown as a separate, planned link.

The acting user is chosen from a list in the header (bid manager, or a unit's product manager or design engineer). Real sign-in is added before a pilot.

## 10. Data Model

```text
opportunity ----< document                          (opportunities)
     |
     +----< requirement (req_id, version)           (requirements)
     +----< baseline
     +----< match (req_id -> bu, product, offering) (matching)
     +----< decision (participation | go_no_go)     (decisions)
     +----< assignment (req_id, bu: response,       (workpackages)
                        compliance, validation)
audit_event (append-only; every module writes to it)      (core)
business units, products, past responses: data files      (catalog)
```

- Every table except the catalog data has an `opportunity_id`, and every page is scoped by opportunity (rule R6).
- Requirements are versions: (req_id, version) is unique, and frozen versions are never edited.
- The audit table records who, when, which entity, before and after values and the reason. SQLite triggers reject updates and deletes on it.

## 11. Interfaces (API routes, all under `/api`)

| Purpose | Route |
|---|---|
| Opportunity and documents | `GET /opportunities/new`, `POST /opportunities`, `GET /opportunities/{id}`, `POST /opportunities/{id}/documents` |
| Layout and page images | `POST /documents/{doc}/ingest`, `GET /documents/{doc}/pages/{n}` (JSON), `GET /documents/{doc}/pages/{n}.png` |
| Requirements | `GET /opportunities/{id}/requirements`, `POST /opportunities/{id}/requirements/extract`, `POST /requirements/{req_id}/review`, `POST /opportunities/{id}/baselines` |
| Catalog | `GET /catalog`, `GET /catalog/search?q=` |
| Matching | `POST /opportunities/{id}/match`, `POST /matches/{match_id}/decide` |
| Decisions | `GET /opportunities/{id}/decisions`, `POST /opportunities/{id}/participation`, `POST /opportunities/{id}/go-no-go` |
| Work packages | `POST /opportunities/{id}/dispatch`, `GET /inbox`, `GET /inbox/{bu}`, `POST /assignments/{id}/respond`, `POST /assignments/{id}/validate` |
| Consolidation | `GET /opportunities/{id}/consolidation`, `GET /opportunities/{id}/compliance-matrix.csv`, `GET /opportunities/{id}/compliance-matrix.xlsx`, `GET /opportunities/{id}/response-outline`, `GET /opportunities/{id}/response-outline.md` |
| Views | `GET /portfolio`, `GET /opportunities/{id}/trace` |
| Changes (stage 5) | `GET /opportunities/{id}/changes` |

Every write uses the acting user's name.

## 12. Testing

- **Smoke test** (`tests/test_smoke.py`, built): seeds the Syracuse demo through the real services, opens every screen, downloads the compliance matrix, and checks that the audit table rejects updates. A second test fails if any module imports another module's internals.
- **Self-checks** next to non-trivial logic (built for anchoring and retrieval): `python -m app.modules.<module>.<file>`.
- **Golden requirement list** for the Syracuse RFP (`data/golden/`, built 8 Oct 2026): 361 requirements drafted from the frozen layout independently of the reader agent, 78 marked uncertain. It is a draft until a person reviews it. `scripts/score_reader.py` measures the reader against it. First result: recall 92% of the certain items, and 54% of the reader's 840 proposals overlap a golden item. Most of the rest are finer-grained items (each listed drawing or standard as its own line item) or come from pages the golden list leaves out (blank forms, drawing sheets, the standards list). Contents pages produce no requirements.
- **Repeatability:** ingest the same PDF twice and compare the layout model byte for byte; re-run extraction and matching and compare (cached answers make this exact).
- **Change test** (stage 5): apply a sample addendum and check that only the affected requirements changed version.

## 13. Build Stages

Each stage leaves the application running end to end. The demonstration RFP is the Syracuse switchgear PDF in `data/RFP/` (single business area, likely Crown and EP²); the synthetic data-centre campus text in `data/RFP/samples/` is the multi-unit case.

| Stage | Builds | Done when | Target |
|---|---|---|---|
| 0 | Skeleton: all modules, seeded demonstration, three screens on seed data, smoke test | Built | 8 Oct 2026 |
| 1 | Reading: OCR, tables, contents and furniture detection; reader agent run on the full RFP, answers cached; golden list | Every page has a stated method; contents pages give no requirements; highlights land on the right lines | 9 Oct 2026 (walkthrough of the screens) |
| 2 | Review actions (edit, split, merge, add missed); matching agent answers cached; EP² and unit catalogs refined | The bid manager can review, freeze and see a sensible unit and product for every line item | 10 to 11 Oct 2026 |
| 3 | Decisions, dispatch, inbox, checklist responses, validation polished on the real extraction | Two units respond to their own line items; progress shows on the screens | 12 Oct 2026 (functioning version) |
| 4 | Consolidation: coverage, compliance matrix, response-outline agent, validated responses into the knowledge base; v1.1 evidence checks | Unanswered requirements block completion; a finished opportunity enriches retrieval | after 12 Oct 2026 |
| 5 | Change handling (delta against baseline) | A sample addendum changes only the affected requirements and returns their responses | after 12 Oct 2026 |

## 14. Open Decisions and Known Limits

**Decisions needed (Needs confirmation):**
1. Model hosting for real customer RFPs: the Azure OpenAI deployment (as used for the public sample) or a local model, and whether RFP text may leave the machine.
2. The exact business-unit list and each unit's real product catalog and past responses.
3. The BOM source system that screen 3 should read from.
4. Whether responses include estimation sheets, prices or margins.
5. PyMuPDF licence for anything beyond an internal PoC.
6. The threshold for a drastic change, and SpinCo's engineering change process.
7. Whether customer-type workflow templates are needed beyond the one-step dispatch.

**Known limits of stage 0:**
- Scanned pages are read by whole-page OCR on the parsing machine only (others use the committed layout); OCR inside an otherwise native page (figure text) is not yet built.
- Tables are in the layout, but the reader agent still reads their lines as text. Showing it the row structure ("Description | Requirement | Units") would help data sheets, but it changes the reader's input on those pages, so their answers would be regenerated. Tables without ruling lines are not detected.
- Matching runs retrieval-only until matcher answers are generated and cached; retrieval is keyword-based.
- The catalog, BOM lines and seeded unit responses are illustrative.
- One acting user is picked from a list; no sign-in.
- SQLite allows one writer at a time; enough for a PoC.

## 15. Reuse from Existing Code Lines

The earlier code is copied, read-only, into `reference/` in the repository and ported module by module. The full M1-to-M17 port table is in [architecture-overview.md](architecture-overview.md).

| Existing piece | Code line | New module |
|---|---|---|
| Ingestion and boundary classifier (M1) | v0.3.0 | ingestion |
| Provenance anchors (M11) and requirement registry (M17) | v0.3.0 | requirements |
| Knowledge base and TF-IDF retrieval; connector stubs (M9) | v0.3.0 | catalog |
| Scope detection (M3), tiers (M4), validation rules (M5), solver (M13) | v0.3.0 | matching (evidence) |
| Routing payloads (M8), approval gates (M7) | v0.3.0 | workpackages |
| Coverage map (M14), proposal checker (M15) | v0.3.0 | consolidation |
| Model runtime seam (M10), model-change guard (M16) | v0.3.0 | core (model gateway, golden tests) |
| Bid, execution and portfolio rules | v1.1 | decisions (evidence), changes |
| Event log, edit, split and merge ideas | v1.0 | core audit, requirements review |

Each piece is ported only when its stage needs it, with its known defects fixed or recorded.
