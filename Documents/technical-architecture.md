# Layer 0: Technical Architecture

## 1. Purpose, Who This Is For, and Status

**Purpose.** This document describes how Layer 0 should be built: the components, the data they hold, how an RFP is read into traceable requirements, and how those requirements move through the opportunity workflow. It is the build reference for the next version of the PoC.

**Who this is for.** Developers who will build Layer 0, and the client point of contact who reviews the design before code is written. Business background is in [business-and-domain-background.md](business-and-domain-background.md); the problems are in [problem-mapping.md](problem-mapping.md); the existing code lines are described in [architecture-overview.md](architecture-overview.md).

**Status.**
- The **workflow** it implements is the working baseline in [project-overview.md](project-overview.md) section 7. It has not been formally signed off.
- The **document-reading tools** are decided by the project team (7 Oct 2026): PyMuPDF, pdfplumber and Tesseract OCR (section 5).
- Everything else is **Proposed (inferred design)**. Nothing in this document is built yet.
- Open points are listed in section 14 and are marked **Needs confirmation** where they appear.

## 2. What the System Must Do

Layer 0 follows one opportunity from the arrival of the RFP to the final bid response:

1. **Read the RFP** and turn it into distinct requirements. Each one keeps its exact source: document, page, position on the page and quoted text.
2. **Determine participation**: whether one, several or all business units need to take part. This is an opportunity-level decision, made before go/no-go.
3. **Support a human go/no-go decision** with assembled evidence. A named person decides.
4. **If go, set up the opportunity's workflow** from a template. Some steps are mandatory, some configurable by customer type and product mix.
5. **Break the RFP into requirements and work packages** and assign each requirement to its owning team or teams. One requirement may go to more than one team.
6. **Track each team's response** against its assigned requirements.
7. **Consolidate** into the final bid response, checking that every requirement is answered or explicitly excluded.

Across every step: human approval, an audit history, and change handling (clarifications, addenda, change requests and execution-stage changes) applied only to the requirements affected.

## 3. Design Rules

These rules come from the review meetings and from the lessons of the earlier code lines. Each component below is checked against them.

| # | Rule | What it means in the build |
|---|---|---|
| R1 | **Everything traces to the source** | Every requirement carries anchors: document hash, page, bounding box and quoted text. A location is never invented; an item without one is `UNANCHORED` and shown with a warning |
| R2 | **Repeatable first pass, then frozen** | Reading is deterministic (fixed tool versions, fixed settings). After human review the requirement set is frozen as the baseline. Re-running never silently changes it. Reason: re-generating an RFP gives different results, which would move requirements between teams and break the workflow |
| R3 | **Changes touch only what changed** | A change creates new versions of the affected requirements only, and flags their assignments and responses for review. A change large enough to alter the whole RFP starts a new opportunity, decided by a person |
| R4 | **The model reads; rules and people decide** | A language model is optional and is called only through one gateway, only to propose readings. Classification, participation, go/no-go, assignment and "answered" are rules plus named people |
| R5 | **Unknown never passes** | Unreadable regions, low-confidence OCR and missing values are reported, never defaulted or skipped |
| R6 | **Every case is separate** | The opportunity ID is part of every record; nothing crosses opportunities except the portfolio view, which only reads |
| R7 | **Rules as data** | The capability map, workflow templates, requirement patterns and thresholds live in versioned data files, not in code |
| R8 | **Append-only audit** | Every decision and change is an audit event that cannot be edited |
| R9 | **Local first** | RFP files and text stay on the machine running Layer 0. Any cloud model use needs an explicit decision (section 14) |

## 4. System Overview

One Python service, one database, one file store and one web interface. This is a modular monolith: modules are separate packages with clear interfaces, deployed as one process. A PoC built by one team does not need message queues, microservices or a workflow engine.

```text
                        +-------------------------------------------+
  Browser (React) <---> |  API (FastAPI)                            |
                        |                                           |
                        |  ingestion      PDF -> page layout model  |
                        |  requirements   layout -> requirements    |
                        |  capability     rules: units, teams       |
                        |  decisions      participation, go/no-go   |
                        |  workflow       templates, step states    |
                        |  work           assignments, responses    |
                        |  consolidation  coverage, final response  |
                        |  changes        diff against baseline     |
                        |  views          3-way, opportunity,       |
                        |                 portfolio (read-only)     |
                        |  audit          append-only events        |
                        |  model_gateway  optional, off by default  |
                        +------------+----------------+-------------+
                                     |                |
                         Database (SQLite for PoC;    File store: original files
                         PostgreSQL later)            by SHA-256, page renders,
                                                      layout JSON (immutable)
                                     |
                         Tesseract (local executable, called per OCR region)
```

### 4.1 Technology

| Concern | Choice | Notes |
|---|---|---|
| Language | Python 3.12 | Already used by every code line |
| API | FastAPI + Pydantic | Already in v0.3.0 `requirements.txt` |
| Database | SQLAlchemy 2 over SQLite for the PoC | Same code runs on PostgreSQL when more than one user writes at once |
| Native PDF text | **PyMuPDF** | Text with coordinates, fonts and sizes; page sizes and rotation; image regions; page rendering for OCR and the viewer |
| Ruled tables | **pdfplumber** | Table and cell boundaries from ruling lines; already used by v0.3.0 |
| OCR | **Tesseract 5.5** (installed locally) | Called as a command-line program with TSV output: word boxes plus confidence, no extra Python package |
| Text comparison | Python `difflib` | Change detection (section 8) |
| Interface | React | Both existing code lines use React |
| Background work | A process pool inside the service | Ingestion of a 100-page RFP with OCR runs in the background; the interface polls its status. No separate job queue |

**Licence check (Needs confirmation before any client use).** PyMuPDF is dual-licensed: AGPL-3.0 or a commercial licence from Artifex. AGPL obliges anyone who offers the software over a network to publish its source. This is acceptable for an internal PoC, but a pilot or product needs a commercial licence or a replacement. pdfplumber (MIT) and Tesseract (Apache 2.0) have no such obligation.

## 5. Step 1 in Detail: Reading the RFP

This is the first part to build. It turns a PDF into a **page layout model**, a structured record of everything on every page with exact positions, and then into candidate requirements.

```text
 PDF file
   |
 (5.1) intake: hash, store, register
   |
 (5.2) page profiling (PyMuPDF): size, rotation, text layer, images, fonts
   |
 (5.3) region routing: for each region, choose table / native text / OCR
   |
   +--> (5.4) tables (pdfplumber): cells with boundaries
   +--> (5.5) native text (PyMuPDF): spans with font, size, position
   +--> (5.6) OCR (Tesseract): words with position and confidence
   |
 (5.7) merge into one coordinate system; cross-check
   |
 (5.8) layout clean-up: reading order, headers and footers, headings,
       table of contents, hyphenation
   |
 page layout model (immutable JSON per document and pipeline version)
   |
 (6) requirement extraction -> human review -> frozen baseline
```

### 5.1 Intake

- The file is stored under its SHA-256 hash and never modified. The hash is the document ID used in every anchor.
- A `document` record links the file to its opportunity, with its role (main RFP, addendum, Q&A, drawing, change request) and the date received.
- **Files other than PDF are named, stored and reported as unprocessed.** This includes Word, Excel, CAD and email files. Coverage is never claimed for a file that was not read (rule R5). Word and Excel readers can be added later as separate readers that produce the same layout model.
- Encrypted or damaged PDFs are reported, not skipped.

### 5.2 Page profiling (PyMuPDF)

For each page, record:
- page number and printed page label (if the PDF defines labels);
- size, rotation, and crop box;
- the native text layer: character count, fonts and sizes used, the share of characters that could not be mapped to real letters (shown as the replacement character U+FFFD);
- invisible text (text render mode 3, usually an earlier OCR layer added by a scanner), detected through the text trace;
- image regions with their bounding boxes and the share of the page they cover;
- the body font: the most common font size on the page, used later to detect headings.

### 5.3 Region routing

Each page is split into regions, and each region is read by exactly one method. Routing is rule-based, and the thresholds are values in a data file (rule R7).

| Situation | Method | Reason |
|---|---|---|
| A ruled table is found by pdfplumber | **Table** | Cell boundaries are kept; table text is removed from the paragraph stream so it is not read twice |
| Native text is present and readable | **Native** (PyMuPDF) | Exact text and exact positions; no recognition errors |
| Page has no text layer | **OCR**, whole page | A scanned page |
| Native text is unusable: unmapped characters above a threshold (starting value 5%) | **OCR** for that region | The text layer exists but the letters are wrong (a font without a character map) |
| An image covers most of the page and native text is sparse | **OCR**, whole page | A scan with only a partial text layer |
| An image inside a text page, above a minimum size (starting value 2% of the page), with no native text over it | **OCR** for that region, marked `figure_text` | Drawings and embedded screenshots can contain requirements; logos and decorations should not create noise |
| Invisible text from an earlier OCR layer | **Native**, marked `prior_ocr` with lower confidence | Earlier OCR is used, but its quality is unknown |

Starting thresholds are guesses and must be calibrated on real SpinCo RFPs. Each routing decision is stored with the reason, so a reviewer can see why a page was OCR'd.

PyMuPDF also has a table finder. pdfplumber is used for tables as decided; if both give the same results on real RFPs, one of them can be dropped later.

### 5.4 Tables (pdfplumber)

- Uses the "lines" strategy, which finds ruled tables (tables drawn with lines between cells).
- For each table, records: bounding box, rows, columns, each cell's boundary and text, and the header row when one is detected.
- Merged cells are kept as one cell spanning several rows or columns.
- **A table that continues on the next page** is linked as one logical table when the columns line up and the header repeats.
- Each table row becomes a candidate requirement source. Compliance matrices, where each row is a requirement and there is a "comply: yes/no" column, are common in RFPs.
- **Known limit:** tables without ruling lines are not detected as tables in the first version. Their text is read as normal text, so the content is not lost, but the cell structure is.

### 5.5 Native text (PyMuPDF)

- Records text as blocks, lines and spans. Each span keeps its bounding box, font, size, bold and italic flags, and colour.
- Character-level positions are kept when a requirement starts or ends in the middle of a line, so the highlight in the viewer is exact.

### 5.6 OCR (Tesseract)

- The region is rendered to an image at 300 dpi by PyMuPDF and passed to Tesseract through standard input.
- Tesseract is called with fixed settings (language, page segmentation mode) and returns TSV: each word with its pixel box and a confidence from 0 to 100.
- Pixel positions are converted back into page coordinates: page x = region x + pixel x × 72 / 300 (and the same for y).
- **Confidence.** Words below a threshold (starting value 60) are marked low-confidence. A requirement drawn from low-confidence words is always sent to a person to check (rule R5).
- The path to the Tesseract executable and its language data is configuration. On the development machine it is installed under `%LOCALAPPDATA%\Tesseract-OCR`; it is not on the system path.
- OCR regions run in parallel in the process pool. Each Tesseract call is limited to one thread so that results do not vary between runs.

### 5.7 One coordinate system, and a cross-check

All positions are stored in one system: **PDF points (1/72 inch), origin at the top-left of the unrotated page, relative to the crop box.** PyMuPDF already uses this. pdfplumber and OCR positions are converted into it. Page rotation is stored once per page and applied only by the viewer.

**Cross-check.** On every page with native text, the same words are located by both PyMuPDF and pdfplumber, and their positions are compared. If they disagree by more than 1 point, the page is marked and its tables are not trusted until someone reviews them. This catches crop-box offsets and rotation mistakes, which would otherwise put highlights in the wrong place.

### 5.8 Layout clean-up

- **Reading order.** Blocks are sorted top to bottom and left to right. Pages with two or more text columns are detected by gaps in the x-positions, and the columns are read in order. Pages where the order is uncertain are marked.
- **Headers and footers.** Lines that repeat in the top or bottom band of most pages (ignoring page numbers) are marked as page furniture. They are kept, not deleted, but they do not become requirements.
- **Headings and sections.** Detected from numbering patterns (for example `3.2.1`, `Section 4`, `Article IV`, `Appendix C`) and from font size or bold relative to the body font. This gives a section tree, so every requirement has a section path such as "4 Technical > 4.2 Switchgear > 4.2.3 Arc resistance".
- **Table of contents.** Pages with many lines that end in dot leaders and page numbers are marked as contents pages. They are excluded from requirement extraction and used only to check section titles. (The v0.3.0 line turned contents headings into requirements; this rule prevents that.)
- **Hyphenation** across line ends is joined. Positions are kept for both halves.

### 5.9 The page layout model

The output is one JSON file per document per pipeline version, stored in the file store and never edited. In outline:

```text
document: sha256, filename, page_count, pipeline_version
  page: number, label, width, height, rotation, routing decisions
    region: id, kind (text | table | ocr | figure_text), bbox, method, confidence
      line: id, bbox, text, char_start, char_end
        span: bbox, text, font, size, bold, italic
    table: id, bbox, continues_from, rows -> cells (bbox, row, col, rowspan, colspan, text)
  page_text: the page's canonical text; every line knows its character range in it
  furniture: headers, footers; toc: true | false
  sections: tree of headings with their positions
```

- Element IDs are stable and readable, for example `9f3a1c2b7e44:p12:t2:r5:c3` (document, page, table 2, row 5, column 3).
- Every element has both a **bounding box** (for highlighting) and a **character range** in the page text (compatible with the v0.3.0 page-local anchors).
- **Repeatability.** The pipeline version combines the PyMuPDF, pdfplumber and Tesseract versions, the Tesseract settings and the rules-file version. Coordinates are rounded to 0.01 point and keys are written in a fixed order. The same file and the same pipeline version give a byte-identical layout model. A test checks this (section 12).

## 6. Requirement Extraction (still Step 1)

### 6.1 From layout to candidate requirements

1. **Segment** the text into candidate clauses: numbered clauses, list items, table rows and sentences, never crossing a section boundary.
2. **Detect requirements** with rules from a data file:
   - obligation phrases: "shall", "must", "is required to", "will provide", "shall not";
   - compliance-table rows;
   - references to standards (IEEE, ANSI, UL, NFPA, IEC);
   - delivery dates, warranty, penalties and submission instructions.
3. **Tag each requirement** with a category (technical, commercial, legal, schedule, staffing, compliance, submission) and with capability tags used later for participation and assignment (for example `mv_switchgear`, `liquid_cooling`, `rack_power`).
4. **Attach anchors.** A requirement can span several lines or pages, so it holds a list of anchors.

### 6.2 Optional model gateway

The first version works without a language model. If a model is enabled later, it may only **propose** splits, categories or tags, and it must return the exact quoted text it relied on.

- Every returned quote is searched for in the canonical page text (ignoring differences in whitespace). If found, it gets an anchor. If not found, the item is `UNANCHORED`, flagged, and never accepted automatically.
- The model runs at temperature 0. Each call records the model name and version, the prompt version and a hash of the input.
- Results are cached by that combination, so a re-run reads the stored result instead of asking the model again (rule R2).
- Rules and reference material retrieved from past RFPs (retrieval-augmented generation, RAG) can be supplied to the model. Fine-tuning a model is not used.

### 6.3 Human review and freezing

The review screen shows the rendered source page on the left with the requirement highlighted from its bounding boxes, and the extracted requirement list on the right. The reviewer can approve, edit, split, merge, reject or add a missed requirement (drawing a box on the page creates the anchor). Each action is an audit event.

When review is complete, a named person **freezes** the set as **baseline 1**. From then on, requirements change only by new versions created through change handling (section 8).

### 6.4 The requirement record

```text
requirement
  id                 REQ-<opportunity>-<sequence>, stable across versions
  version            1, 2, ... (only the latest is current; all are kept)
  text               cleaned text
  quote              verbatim source text
  anchors[]          document sha256, page, bbox list, char range, method
                     (native | table | ocr | prior_ocr), confidence
  section_path       e.g. "4 > 4.2 > 4.2.3"
  category, tags     from rules (and reviewer edits)
  provenance         EXTRACTED | DERIVED | UNANCHORED
  status             extracted > reviewed > assigned > responded
                     > consolidated > answered | excluded
  baseline           which frozen baseline it belongs to
```

The provenance classes and the page-local anchor reuse the v0.3.0 `provenance/anchors.py` design, extended with bounding boxes, method and confidence.

## 7. Steps 2 to 7

### 7.1 Capability map (rules as data)

A versioned data file maps capability tags to business units and to teams. One tag may map to several units or teams. It can be seeded from the v0.3.0 `knowledge_base/spinco_layers.json` (product layers to brands to teams).

**Needs confirmation:** which business units exist (the review meetings spoke of "six companies") and which teams sit under them. The map is data, so it can change without code changes.

### 7.2 Participation (step 2)

- Rules read the tags of the reviewed requirements and suggest which units should take part, each with the requirements that triggered it as evidence.
- A named person confirms, adds or removes units. The result is a **participation decision record**: who, when, the units, the evidence, and a reason for any change from the suggestion.

### 7.3 Go/no-go (step 3)

The system assembles an **evidence pack**:
- requirement counts by category and tier, and the participating units;
- deviations from the standard portfolio (the v1.1 bid-stage rules can be reused here, with their invented constants replaced or labelled as placeholders);
- conflicts with other opportunities on capacity, specification and timeline (the v1.1 portfolio check, same caveat);
- unanchored, low-confidence and unreadable items;
- open questions for the customer.

A named person decides go or no-go. The **decision record** stores the outcome, the evidence shown and the rationale. The system never decides.

### 7.4 Workflow (step 4)

- Workflow templates are data files, selected by customer type and participating units. Each template is an ordered list of steps; each step is marked mandatory or optional and has a role responsible.
- On a go decision, a template is copied into the opportunity as its workflow. Optional steps can be switched off by a named person, with a reason.
- Step states: not started, in progress, done, skipped (with reason). This is a simple state field, not a workflow engine.

**Needs confirmation:** the real templates and mandatory steps.

### 7.5 Assignment and work packages (step 5)

- Rules suggest the owning team or teams for each requirement from its tags and the capability map.
- A person confirms. One requirement can have several assignments, one per team, each with an owner and a due date.
- A work package is the set of a team's assignments within one opportunity. It is a view, not a separate copy of the data.

### 7.6 Team responses (step 6)

- One response record per assignment: the response text or a link to the team's document, its status (not started, in progress, submitted, accepted, rejected), the author and the date.
- Each team sees its outstanding assignments. People write the responses; Layer 0 tracks and links them.
- **Needs confirmation:** whether responses include estimation sheets or prices.

### 7.7 Consolidation (step 7)

- The final response has an outline of sections. Each requirement is linked to the section or sections that answer it.
- **Coverage check:** every requirement in the current baseline must be *answered* (linked to an accepted response and a final-response section) or *excluded* (with a reason and an approver). Anything else blocks completion and is listed.
- **Export:** a compliance matrix (spreadsheet) with requirement, source page and quote, team, response and final-response section. Writing the final document itself remains a human task.

## 8. Change Handling

Changes arrive as addenda, Q&A answers, change requests, or (after award) execution-stage specification changes between contract phases. All use one path.

1. The change document is ingested through the same pipeline (section 5), linked to the same opportunity with the role "change".
2. Its candidate requirements are compared with the current baseline. Matching uses the section number first, then text similarity (`difflib`). Each item is classified as **added, modified, removed or unchanged**.
3. A person reviews and confirms the classification.
4. Only affected requirements get a **new version**. The previous version stays visible. Added requirements get new IDs and enter assignment.
5. The assignments, responses and final-response links of every changed requirement are marked **needs review**, and their teams are notified in the interface.
6. **A drastic change.** If the share of modified or removed requirements passes a threshold (to be set), the system suggests starting a new opportunity. A person decides, and the new opportunity links to the old one.
7. **Execution-stage changes** (for example a material change between Phase 1 and Phase 2) follow the same path. The v1.1 execution-stage rules (engineering change notice needed, next phase locked) can be reused as an evidence check on the change.

**Needs confirmation:** the threshold for a drastic change, and the real engineering change process at SpinCo.

## 9. Views

All views read the same tables; there is no separate reporting store.

| View | Level | Shows |
|---|---|---|
| **Portfolio** | All opportunities | Every opportunity across customers, its stage (bid, execution), its decision status, open items per team, and cross-opportunity conflicts. This is the top level, not a drill-down |
| **Opportunity: bid stage** | One opportunity | Requirements summary, participation, go/no-go evidence and decision, workflow progress |
| **Opportunity: execution stage** | One opportunity | Committed baseline, changes by phase, change checks, locked phases |
| **Three-way traceability** | One opportunity | Three linked panes: (1) the RFP with highlighted source passages, (2) the breakdown and assignment of each requirement, (3) the team responses and final-response sections. Selecting a requirement in any pane selects it in the other two. Every requirement and its deviations are listed |
| **Review** | One document | Source page with highlights on the left, extracted requirements on the right (section 6.3) |

The three-way view is the screen the review meetings found missing. It is part of the first demonstrable release (section 13).

## 10. Data Model

```text
opportunity ----< document ----< page_layout (file store, immutable)
     |
     +----< requirement (id, version) ----< anchor
     |          |
     |          +----< assignment >---- team >---- business_unit
     |          |          |
     |          |          +---- response
     |          |
     |          +----< final_response_link >---- final_response_section
     |          |
     |          +----< change_link >---- change (from a change document)
     |
     +---- participation_decision ----< participating_unit
     +---- go_no_go_decision
     +---- workflow ----< workflow_step
     +---- baseline (frozen sets of requirement versions)

audit_event (append-only; every table above writes to it)
```

- Every table except `business_unit`, `team` and the rules files has an `opportunity_id` column, and every API call is scoped by opportunity (rule R6).
- Requirements are stored as versions: the pair (requirement ID, version) is unique, and nothing is updated in place after a baseline is frozen.
- **Audit events** record who, when, which entity, the previous and new values, and the reason. In SQLite, triggers reject updates and deletes on this table. A hash chain to make tampering evident is not needed for the PoC and can be added if required.

## 11. Interfaces (API Outline)

| Purpose | Endpoint |
|---|---|
| Create an opportunity; upload documents | `POST /opportunities`, `POST /opportunities/{id}/documents` |
| Ingestion status and layout | `GET /documents/{doc}/status`, `GET /documents/{doc}/pages/{n}` (layout JSON), `GET /documents/{doc}/pages/{n}/image` |
| Requirements and review | `GET /opportunities/{id}/requirements`, `POST /requirements/{rid}/review` (approve, edit, split, merge, reject), `POST /opportunities/{id}/baselines` (freeze) |
| Decisions | `POST /opportunities/{id}/participation`, `POST /opportunities/{id}/go-no-go` |
| Workflow and work | `POST /opportunities/{id}/workflow`, `POST /requirements/{rid}/assignments`, `PUT /assignments/{aid}/response` |
| Consolidation | `GET /opportunities/{id}/coverage`, `GET /opportunities/{id}/compliance-matrix` |
| Changes | `POST /opportunities/{id}/changes` (upload change document), `POST /changes/{cid}/confirm` |
| Views | `GET /portfolio`, `GET /opportunities/{id}/trace` |
| Audit | `GET /opportunities/{id}/audit` |

Every write takes the acting user's name; there is no anonymous write. For the PoC, a user is picked from a list; real sign-in is added before a pilot.

## 12. Testing

- **Small generated PDFs** with known text, tables and positions, created with reportlab (already in the v0.3.0 requirements). For OCR, a test page is rendered to an image-only PDF so that the expected words and boxes are known.
- **Golden files** on the sample RFPs: the real 101-page Syracuse switchgear PDF in `layer0-delivery/code/spinco-agentic-cpq/knowledge_base/sample_rfps/real_pdfs/`, plus the text samples. The layout model and the requirement list are stored, and any change shows as a reviewed difference.
- **Repeatability test:** ingest the same PDF twice and compare the layout model byte for byte.
- **Coordinate test:** the cross-check of section 5.7 runs on every page of the golden files.
- **Traceability test:** for each requirement in a sample opportunity, follow the chain from source to final-response section and back; any break fails the test.
- **Change test:** apply a sample addendum and check that only the affected requirements changed version, and that their responses were marked for review.

## 13. Build Order

Each phase ends with a demonstration on the Syracuse PDF (single-unit) and on the synthetic data-centre campus sample (multi-unit).

| Phase | Builds | Done when |
|---|---|---|
| 1 | Intake, profiling, routing, native text, tables, OCR, layout model, review screen | Every page of the Syracuse PDF is read by a stated method; contents pages are excluded; highlights land on the right text; two runs are identical |
| 2 | Requirement rules, anchors, review actions, freezing, audit log | A reviewer can produce and freeze a baseline; every requirement opens its source passage |
| 3 | Capability map, participation, go/no-go evidence and decision records | The multi-unit sample suggests several units and the single-unit sample suggests one, each with evidence; decisions are recorded with a named person |
| 4 | Workflow templates, assignments, responses | Requirements are assigned (some to two teams) and responses are tracked per team |
| 5 | Coverage check, compliance matrix, three-way view, portfolio view | A reviewer can follow any requirement across the three panes; unanswered requirements block completion |
| 6 | Change handling | A sample addendum changes only the affected requirements and flags their responses |

Phases 1 and 2 need no business decisions. Phases 3 to 6 need the open points in section 14.

## 14. Open Decisions and Known Limits

**Decisions needed (Needs confirmation):**
1. PyMuPDF licence for anything beyond an internal PoC (section 4.1).
2. The business units and teams, and how they map to each other (section 7.1).
3. Workflow templates and mandatory steps (section 7.4).
4. Whether responses include estimation sheets, prices or margins.
5. The threshold for a drastic change, and the engineering change process (section 8).
6. Whether a language model is used, and if so whether it is local or cloud, and whether RFP text may leave the machine.
7. Order of steps 2 and 3. The review meetings gave both "participation, then go/no-go" and "can we bid, then which units". This design allows either, because both are decision records over the same evidence.

**Known limits of the first version:**
- Tables without ruling lines lose their cell structure (text is kept).
- Handwriting, stamps and very poor scans give low-confidence OCR and are sent for human checking.
- Only English OCR is configured. Other languages need their Tesseract language data.
- Word, Excel, CAD and email files are recorded but not read.
- Routing and confidence thresholds are starting guesses until calibrated on real SpinCo RFPs.
- SQLite allows one writer at a time. This is enough for a PoC; PostgreSQL is needed for several concurrent users.

## 15. Reuse from Existing Code Lines

| Existing piece | Code line | Used for |
|---|---|---|
| Provenance classes and page-local anchors (`provenance/anchors.py`) | v0.3.0 | Requirement anchors (extended with bounding box, method and confidence) |
| pdfplumber ingestion and extractor-version recording (`ingestion/ingest.py`) | v0.3.0 | Starting point for table reading and the pipeline version |
| Product layers, brands and teams (`knowledge_base/spinco_layers.json`) | v0.3.0 | Seed for the capability map |
| Sample RFPs, including the real Syracuse PDF | v0.3.0 | Golden tests |
| Bid-stage, execution-stage and portfolio rules | v1.1 | Evidence checks for go/no-go and changes, with placeholder constants labelled |
| Case-scoped event log and edit, split and merge ideas | v1.0 | Design reference for the audit log and review actions |

Nothing is merged wholesale. Each piece is copied in only when its phase needs it, with its known defects (listed in [architecture-overview.md](architecture-overview.md)) fixed or recorded.
