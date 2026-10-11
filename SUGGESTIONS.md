# Layer 0: Suggestions for the Next Steps

Status: written against the Layer0-Flex code base on 11 Oct 2026. Everything below is a proposal for discussion, not a commitment. Each suggestion names the files it starts from, so it can be checked against the code. Figures quoted as "measured" come from `scripts/score_reader.py`, `scripts/model_guard.py` and the token counts in `Documents/technical-architecture.md` section 6.2c; everything else is an estimate.

## What the PoC already does (the baseline)

1. **Reads a PDF into a deterministic page layout model** (`app/modules/ingestion/service.py`): native text with line numbers and boxes, whole-page OCR for pages without a text layer, ruled tables (pdfplumber), header/footer and contents-page detection. Two runs give byte-identical layouts; the Syracuse parse is frozen in `data/layout_cache/`.
2. **A reader agent proposes requirement line items** one page per call (`app/modules/requirements/agent.py`), and every quote is anchored on its page or stored as `UNANCHORED` (`anchoring.py`). Measured on the Syracuse RFP: recall 91.9% of the 283 certain golden items; 54% of the 840 proposals overlap a golden item (`data/golden/`, `scripts/score_reader.py`).
3. **Duplicates and groups**: near-verbatim repeats are marked by text comparison, and a grouping agent turns related line items on a page into one requirement with sub-requirements (`grouping.py`). On Syracuse, 814 line items become 348 requirements (162 groups, 21 duplicates).
4. **Human review and a frozen baseline**: approve, reject, edit, split, merge, ungroup, add a missed requirement by pasting a quote or selecting lines on the page; a per-item history rebuilt from the append-only audit log; freeze as baseline 1 (`requirements/service.py`, `web/app/opportunities/[id]/requirements/`).
5. **Matching to business units and products** with one matcher call per page and the whole catalog as a cached prompt prefix; rules route non-product categories to the bid desk without a call; retrieval-only fallback is labelled as such; a person accepts, rejects or sets the match (`matching/`). One first read of a new 101-page RFP costs 208 model calls, about 251k input and 81k output tokens, roughly $1.40 to $1.44 at GPT-4o list price.
6. **Decision support**: an evidence pack (category counts, suggested units, offering mix, unanchored and unmatched items, ported scope and engineering checks, data-sheet deviations, workload across opportunities) and a go/no-go summary with criteria and advice; a named person records participation and go/no-go with the evidence as shown (`decisions/`).
7. **One-step dispatch, inbox, checklist responses and validation** per unit, with withdrawal and reopening when matches or participation change, and a per-unit hand-off payload grouped by route (`workpackages/`).
8. **Consolidation**: coverage check, compliance matrix as CSV and a formatted Excel workbook written by code, and a response-outline agent that drafts chapters only from validated answers with citation guards (`consolidation/`).
9. **Change handling as a delta**: an addendum is read and classified against the frozen baseline (five TF-IDF-ranked candidates per statement), a person confirms each item, the bid manager applies it to create baseline 2, affected answers return to the units and only changed requirements are re-matched (`changes/`).
10. **Every model answer is frozen** in `data/llm_cache/` keyed by task, model, prompts and schema (`app/core/llm.py`); embeddings are frozen in `data/vector_cache/` with a keyword fallback (`app/core/vectors.py`); a model-change guard replays the demo and compares a candidate model before any switch (`scripts/model_guard.py`); a knowledge-base queue lets people send validated material to a curator, and approved items join the long-term retrieval index (`knowledge/`, `catalog/`).

The design rules that every suggestion below must keep: agents propose and named people decide (R4); the first pass is frozen and later runs process only the delta (R2); every source is exact or marked unanchored (R1); unknown never passes (R5); the audit log is append-only (R8); requirement identification never uses pattern matching (R5).

## 1. AI & Machine Learning Opportunities

### 1.1 Requirement extraction quality: learn from the golden list and the review log

- **Where:** `app/modules/requirements/agent.py` (SYSTEM prompt, one page per call), `scripts/score_reader.py`, `data/golden/RFP-2023-20-Switchgear-Procurement-Final.json` (361 items, 78 uncertain), the `edit`, `reject`, `split`, `merged`, `proposed` (by a person) events in `audit_event`.
- **What:** Turn the review actions into a labelled set and use it to tune the reader, without fine-tuning. Rejected items are false positives; items added by `add_missed` / `add_from_lines` are false negatives; `split` and `merge` events show the wrong granularity; `edit` events with a category change show category confusion. Add a `scripts/review_signals.py` that exports these from the audit log per opportunity, and extend `score_reader.py` to report precision per category and the "extra" items grouped by page type (forms, drawing sheets, standards lists).
- **Why:** Recall is good (91.9%) but only 54% of proposals overlap a golden item. Most "extra" items are finer-grained lists or come from pages the golden list excludes, so the review burden, not recall, is the cost. The golden list is still a draft until a person reviews it; the review log is the cheapest source of real labels.
- **How:** (1) Few-shot examples in the system prompt per page type (a form page, a standards list, a specification page) chosen from reviewed items; (2) an explicit "do not list" rule set derived from the most common rejects (blank-form fields, "by others" work, Authority rights); (3) a second reader pass only for pages where the first answer returned zero items but the page has more than N body lines (a recall check, cheap). Every prompt change changes the cache key, so answers are regenerated and gated by `model_guard compare` (reader recall threshold 0.90) before the switch.
- **Technology:** Existing gateway (Azure OpenAI GPT-4o, JSON schema, temperature 0). Fine-tuning is excluded by the review direction (`Documents/project-overview.md` 13.3) and would only make sense after dozens of reviewed real RFPs on an enterprise-hosted model; it is listed in section 5.
- **Data:** The golden list, the audit log of real reviews (none yet from the business), and future RFPs read with the live model.
- **Complexity:** Low to medium (scripts and prompt work; the regeneration run costs one read per sample RFP).
- **PoC value:** High: fewer items to reject in review is the first thing a bid manager will notice.

### 1.2 Matcher learning from accept, reject and manual decisions

- **Where:** `app/modules/matching/service.py` (`decide`, `set_manual`, `Match.status`, `Match.method`), `matching/agent.py` (fixed prompt prefix: rules plus catalog plus past responses), `catalog/service.py` (`learn`, `_index`).
- **What:** Use people's decisions on matches as the matcher's memory, without touching its frozen prompt. Before the model is asked, look for an accepted or manual match on a near-identical requirement (same unit catalog, cosine similarity of the quote above a threshold) in earlier opportunities, and propose it with `method="learned"` and a rationale that names the source opportunity and the person who decided. The model is only asked for what nothing was learned for.
- **Why:** The matcher's prompt holds the illustrative catalog and eight past responses; the real signal will be the hundreds of accept / reject / change actions on real bids. Adding them to the prompt would invalidate every frozen matcher answer (the prompt is part of the key), so the learning layer must sit beside the prompt, as `catalog.learn` already does for the retrieval index.
- **How:** Add `matching.learned_matches(db)` that reads accepted and manual `Match` rows across opportunities, embeds their requirement quotes (frozen vectors), and in `match()` checks each new requirement against them before batching; keep the model's proposal for the rest. Rejections lower the rank of that (unit, product) pair in the retrieval evidence for similar quotes. Show "learned from OPP-0001" on screen 3 so the person sees why.
- **Technology:** `app/core/vectors.Index` over learned matches; no new library. A re-ranker over retrieval hits (acceptance counts per product) is plain arithmetic.
- **Data:** `match` and `audit_event` tables; there are no real decisions yet, so the first value comes from the demo re-run and the pilot.
- **Complexity:** Medium. The threshold for "near-identical" must be measured on real RFPs (start high, e.g. 0.9 cosine, and show the similarity).
- **PoC value:** Medium now, high in a pilot: the second RFP of the same kind matches itself from the first one's decisions, with no call.

### 1.3 Answer drafting per unit from the knowledge base

- **Where:** `web/app/inbox/[bu]/page.tsx` (free-text response form), `workpackages/service.py` (`respond`), `catalog/service.py` (`search`, `past_responses`, `learned`), `consolidation/agent.py` (the citation guard pattern).
- **What:** A "Suggest an answer" button on each assignment: retrieve the unit's closest past responses and approved knowledge items, ask the model for a checklist answer (compliance, product, two or three sentences) that cites the knowledge items it used, and put it in the form as a draft. The design engineer edits and submits; nothing is submitted by the agent.
- **Why:** The response step is where the units spend their time, and the knowledge base exists so that earlier answers are reused (plan section 8, items 3 and 4). Today the retrieval index is used for matching evidence and outline references only.
- **How:** New task `draft_answer` through the gateway, prompt built like the outline agent's: the requirement quote, the matched product's catalog entry, the top k past responses of that unit (numbered), a schema with `compliance`, `response`, `cites`. Drop a draft whose citations are invalid. Candidates must be chosen deterministically (TF-IDF or frozen vectors, as the changes module does) so the frozen answer does not depend on the search mode. Mark the assignment "drafted by agent" in the audit event when the person submits an unedited draft.
- **Technology:** Existing gateway and index; one short call per assignment, only on demand.
- **Data:** Real past responses per unit (`past_responses.json` is illustrative, 8 entries); the knowledge queue will grow it.
- **Complexity:** Low to medium.
- **PoC value:** High for the demo story (a unit answers from its own history) and for the pilot.

### 1.4 Duplicates and grouping with embeddings

- **Where:** `requirements/grouping.py` (`duplicates`: difflib ratio 0.92 on normalised quotes, exact-match shortcut; `group`: one model call per page with at least three items), `app/core/vectors.py`.
- **What:** Keep text comparison for near-verbatim duplicates (plain logic is right there) and add an embedding pass for what it cannot see: a cover-page restatement that paraphrases the specification, and related items on different pages (a drawing listed in the submission section and again in the specification). Propose "related to" links and cross-page group candidates for a person to confirm; never merge automatically.
- **Why:** The grouping agent works page by page, so cross-page relations are invisible, and difflib only catches almost identical strings.
- **How:** Embed the requirement texts (frozen vectors, as the RFP passages are), take pairs above a similarity threshold, and show them as a "possible duplicate / related" filter on the Requirements page with the two quotes side by side. The reviewer's choice (merge, keep both, link) is an audit event. Cross-page merging needs multi-page anchors, which `merge()` refuses today by design; a "related" link that does not merge avoids that.
- **Technology:** `Index.search_many` over the requirements themselves; cosine over a few hundred vectors is instant.
- **Data:** None beyond the RFP.
- **Complexity:** Low for the detection, medium for the review UI.
- **PoC value:** Medium: fewer repeated answers from the units on the 348-requirement demo.

### 1.5 Change impact prediction

- **Where:** `changes/service.py` (`rank`: five TF-IDF candidates per statement; `apply`: affected requirements = the changed ones and their groups), `requirements/service.apply_change`, `workpackages.return_for_change`.
- **What:** After classification, predict which other requirements and answers a change probably touches even though they are not its target: a change of breaker positions touches the drawing list, the data sheet and the bus rating; a due-date change touches every schedule requirement. Show them as "review suggested" on the Changes page; the person decides whether to return those answers too.
- **Why:** Today only the targeted requirement's answers are returned. Real addenda change one number that several requirements depend on.
- **How:** Deterministic first: same group, same page, same data-sheet table (`line.cell`), same section. Then embedding similarity between the new wording and every approved requirement. Optionally one model call per modified statement: "which of these ten candidates does this change affect, and why", with the candidates ranked by TF-IDF so the prompt is stable offline. Every suggestion carries its basis (group, table, similarity, model) so the person can judge it.
- **Technology:** Existing index and gateway.
- **Data:** The frozen baseline and the change set.
- **Complexity:** Medium.
- **PoC value:** Medium; it strengthens the "changes touch only what changed" story without weakening it (nothing is applied without a person).

### 1.6 Bid/no-bid risk scoring from history

- **Where:** `decisions/service.py` (`summary`: criteria met / not met / unknown, advice "n of m criteria met"), `decisions/models.py` (`Decision.evidence`, `criteria`), `data/knowledge_base/go_no_go.json` (coverage threshold 0.8, three criteria "data not available").
- **What:** Not a model yet. The honest first step is to record outcomes: add `outcome_recorded` (won, lost, withdrawn, no bid) and the final figures to the opportunity when they are known, so that the evidence packs stored with each decision become a history. After a few dozen real decisions, a transparent score (criteria weights fitted by logistic regression, or simply the win rate per criterion pattern) can be shown beside the advice, with the number of cases it rests on.
- **Why:** The thresholds are placeholders and the only supported statement is which criteria are met. A learned score shown without a history would be theatre.
- **How:** Capture first (two fields and one audit event), then analysis in a script over `decision.evidence`, then a weighted score in `summary()` labelled with its sample size. A language model has no role here: the inputs are structured, and a liability-bearing judgement must stay explainable (project-overview section 5, "the model reads; it does not decide").
- **Technology:** scikit-learn (already installed) for the fit; the score itself is arithmetic in `summary()`.
- **Data:** Real decisions and outcomes; none exist. SpinCo's past bids would let the score be back-tested before it is shown.
- **Complexity:** Low to capture, medium to calibrate.
- **PoC value:** Low for the demo, high for the business case (it is the measurement the project still lacks).

### 1.7 OCR and layout models for drawings and tables

- **Where:** `ingestion/service.py` (`_read_page`: whole-page Tesseract when there is no text layer, 38 of 106 OCR lines on page 83 are low confidence; `_add_tables`: ruled tables only, pages with more than 3,000 drawn edges are skipped; figure text inside a native page is not read), `requirements/agent.py` (tables are read as lines, not as rows).
- **What:** (1) Give the reader the row structure of data-sheet tables ("Description | Requirement | Units") instead of the raw lines; (2) region OCR for images inside native pages (title blocks, notes on drawings); (3) a table-structure model for tables without ruling lines; (4) on the parsing machine only, a vision-capable model call for drawing sheets that returns text with boxes, verified against OCR words before anything is anchored.
- **Why:** The known limits in `Documents/technical-architecture.md` section 14 are all here. Drawings and unruled tables carry requirements (ratings, quantities) that the current reader sees as loose lines or not at all.
- **How:** Keep the layout model as the only input to the reader (determinism and freezing depend on it). Add `tables_as_text` to the page prompt for pages with tables; this changes those pages' prompts, so their answers are regenerated and compared with the guard. For region OCR, reuse `_ocr_lines` on a cropped pixmap and mark lines `figure_text`. A vision call must go through the gateway with the page image hash in the key, and its output is only accepted where the words also appear in the OCR layer (rule R5: an unverified reading is flagged, never trusted).
- **Technology:** Tesseract (present), pdfplumber text-strategy tables, an open-source table-structure model if unruled tables prove common; a vision deployment on the same Azure tenant for drawings. All optional and parsing-machine only, as today.
- **Data:** More real RFPs with scanned pages and drawings; Syracuse has one scanned page.
- **Complexity:** Medium for tables-as-rows, high for drawings.
- **PoC value:** Medium: visible on page 83 and the data sheet (pages 72 to 74) of the demo RFP.

### 1.8 Agentic Q&A over the RFP with citations

- **Where:** `ingestion/service.py` (`search_rfp`: short-term index of about 600 passages with page and lines), `web/app/opportunities/[id]/page.tsx` ("Search this RFP" shows passages only), `consolidation/agent.py` (citation guard).
- **What:** "Ask the RFP": a question in natural language gets a short answer that cites passages by page and lines, and clicking a citation opens the page in pane 1 with the lines highlighted. Questions the RFP does not answer get "not found in the RFP", never a guess.
- **Why:** Bid managers and engineers ask "what is the short-circuit rating" and "when is the pre-bid meeting" dozens of times per bid; the index exists, only the last step is missing.
- **How:** One gateway task `answer_rfp`: numbered passages (top k from the index) plus the question; the schema returns `answer`, `cites` (passage numbers), `found` (boolean). Apply the outline agent's guard: drop any sentence whose citations are not among the shown passages. Note the trade-off: the frozen answer depends on which passages were retrieved, and retrieval differs between embedding and keyword mode, so the page must say which mode produced the answer, and the demo should use frozen embeddings (already committed for the sample RFP). Every answer is an audit event so later disputes can see what the tool said.
- **Technology:** Existing index and gateway; no agent framework is needed for a single retrieve-then-answer step.
- **Data:** The RFP only.
- **Complexity:** Low.
- **PoC value:** High for a demo moment, medium for the workflow.

### 1.9 Where plain logic is better than a model

- Bid-desk routing by category (`matching/service.py`), furniture and contents detection, data-sheet value parsing (`decisions/portfolio.py`), coverage and compliance matrix, ID allocation, the drastic-change share, exact duplicates: all deterministic today and should stay so. They are explainable, free and repeatable.
- The keyword scope detection and the regular-expression facts in `matching/checks.py` are evidence, not identification, and may stay rule-based; the keyword lists are the part to calibrate (section 4.3).
- Validation of a unit's answer (is the compliance consistent with the text? does "met" come with a product?) is a rule first; a model check (section 3) is an optional second opinion.
- Go/no-go scoring (1.6) must not be a language-model judgement.

## 2. Technology & Library Recommendations

Each item says when it fits and when it is not needed. The web application stays on plain CSS with no new npm dependencies; back-end additions are listed only where they remove real work.

- **pgvector or Chroma (vector store).** Not needed now: `app/core/vectors.py` holds a few thousand vectors in numpy and searches them in microseconds; frozen `.npy` files make offline demos free. Fit: when the long-term index holds hundreds of thousands of passages (every past response of every unit, full past RFPs) or must be shared by several API processes. pgvector fits best because it rides on the PostgreSQL move below and keeps one database; Chroma if a file-based store is preferred for a single machine. The `Index` class keeps its contract either way.
- **PostgreSQL before a pilot.** SQLite allows one writer and the audit-log triggers in `db.py` are SQLite-only. Several bid managers and units writing at once need PostgreSQL; the same SQLAlchemy code runs on it (`DATABASE_URL`). The append-only guarantee must then be re-created as PostgreSQL triggers or a restricted role (`REVOKE UPDATE, DELETE ON audit_event`), with a test like `test_demo_flow_and_api`'s audit check running on both.
- **Alembic migrations before a pilot.** `init_db()` is `create_all` plus a column check that stops start-up with a reset instruction; fine for a demo, unacceptable once real data exists. Add Alembic with an initial autogenerated revision and run `alembic upgrade head` from `setup.cmd`. Not needed for tomorrow's demo.
- **Background jobs with progress for long agent runs.** The reader on a new 100-page RFP takes about a minute live and the Changes upload blocks the request while the document is read and classified. Fit: a `job` table (id, kind, opportunity, total, done, status, error) written by the existing `ThreadPoolExecutor` loops, a FastAPI `BackgroundTasks` start as the document upload already does, and a `GET /api/jobs/{id}` the page polls every two seconds. No Celery, Redis or queue is needed for one process; add a queue only when several API processes run.
- **A proposal document generator (docx).** The outline downloads as Markdown; bid teams work in Word. `python-docx` (one back-end dependency, no model) can render the same outline into the proposal template with headings, the cited requirement IDs as footnotes and the compliance matrix as an appendix. pptx is not needed: nothing in the workflow is a presentation.
- **PDF.js for in-browser text selection.** Not needed for anchoring: pane 1 renders a PNG with highlight boxes from the layout model, and `LinePicker` selects lines by number, which is exactly what the anchors need. Fit only for zoom and find-on-page in pane 1; both can be done on the PNG (CSS zoom, search through the layout lines) without a PDF viewer. Recommendation: do not add it.
- **Charting for the portfolio.** The portfolio page uses CSS bars for unit progress, and the evidence pack is tables. Inline SVG (no library) is enough for a workload-versus-capacity bar per unit and a category breakdown; a charting library would be the first UI dependency and adds nothing the demo needs. Not recommended.
- **Authentication for a pilot.** The acting user is a cookie and an `X-Actor` header (`app/core/web.py`). A pilot needs sign-in through the enterprise identity provider (OpenID Connect), a `user` table with roles (bid manager, curator, unit product manager, unit design engineer) replacing the name checks in `workpackages`, `knowledge` and `changes` (`BID_MANAGER` constants), and the audit `actor` set from the token. Keep the header picker behind a flag for demos.
- **An enterprise-hosted model for non-public bids.** Rule R9 and the roadmap in `team/PLAN.md` section 8 (item 7). The gateway is the only place to change: a second provider in `llm.py` (same JSON-schema contract), with `model_guard compare` as the acceptance test. Not needed for the public sample RFP.
- **Not recommended:** an agent framework or orchestration library (every agent is one call with a schema and a guard; a framework would hide the frozen-answer mechanism), a message bus, microservices, a front-end component library.

## 3. Feature Enhancement Ideas

1. **Answer-to-requirement consistency check** before validation: rule-based (a "met" answer with no product on a product item; a "partial" with empty text) and, on demand, one model call that says whether the response addresses the quoted requirement, shown as a note to the validator. Where: `workpackages.validate`, inbox page.
2. **Customer clarification list**: unanchored items, rule warnings ("not stated: clarify before quoting" in `checks.py`), and low-confidence change items collected into a numbered list of questions to send to the customer, exported with the compliance matrix. Where: `decisions.evidence`, consolidation page.
3. **Version diff on the Requirements and Changes pages**: the history view lists versions; a word-level diff of old and new wording (difflib, no model) makes an addendum's effect visible in one glance.
4. **Addenda before the freeze**: today a document uploaded with role `addendum` is stored but only the main RFP is read, and change handling needs a baseline. Allow reading an addendum into draft line items before the freeze, anchored in the addendum (the trace page already supports several documents).
5. **Due dates and reminders on assignments**: a due date set at dispatch (from the RFP's schedule requirements), shown in the inbox and on the portfolio; an "overdue" filter. A daily e-mail digest is a pilot item.
6. **Audit log page per opportunity**: the data exists (`audit.history`); a filterable table (who, when, what) answers "who changed this and why" without opening each item.
7. **Bulk review tools**: approve by page range or category, keyboard shortcuts (approve, reject, next) on the Requirements page; the 348-requirement review is the longest manual step of the demo.
8. **Catalog maintenance**: products and past responses are JSON files (rule R7). A read-only catalog page exists; add import from a spreadsheet per unit with validation (unique IDs, active unit, offering type) and a file version stamp shown on screen 3, so each unit can replace the illustrative entries without editing JSON.
9. **Comparison with a past bid of the same customer**: the v1.0 idea (deviation detection against a past bid, PM-003) applied with real data: match the new RFP's requirements to the past RFP's approved requirements by embedding, list what is new. Needs one real past bid.
10. **Hand-off payload download** on the inbox page (the API `GET /api/opportunities/{id}/handoff/{bu}` exists; the page has no button).
11. **Opportunity closing**: a `submitted` status with the final matrix and outline stored as files under the opportunity, and the won/lost outcome (section 1.6).
12. **Reader quality card** on the RFP page after extraction: items proposed, anchored, unanchored, duplicates, groups, pages with problems, and the share answered by the agent versus retrieval-only in matching, so the bid manager knows how much to trust the first pass.
13. **Zoom and find-on-page in pane 1**: CSS zoom of the page image with the highlight boxes scaling with it, and a find box over the layout lines of the shown page that scrolls to and outlines the hit; both work on the PNG and the layout model, so no PDF viewer is needed.
14. **Workload on the portfolio page**: the per-unit open work and capacity already computed for the evidence pack (`decisions/portfolio.workload`) shown once across all opportunities, as an inline SVG bar per unit, so the question "who is overloaded this month" has one place.
15. **Unit-level product manager view**: today the product manager and the design engineer share the inbox. A per-unit summary (requirements by offering type, products named, open deviations) gives the product manager the "what are we being asked to offer" view without reading every answer.

## 4. Existing Logic That Could Be Improved Further

### 4.1 TF-IDF fallback (`app/core/vectors.py`)

- **Current:** Without frozen vectors or an embedding provider, `Index` fits a TF-IDF (1-2 grams, English stop words) per index and ranks by cosine; the mode is reported as "keywords".
- **Limitation:** No stemming, so "breakers" and "breaker" differ; ranking differs from the embedding mode, so an offline laptop can show different search results and outline references than the online demo; the fit is repeated for every new `Index` instance.
- **Proposed:** Commit frozen vectors for every text the demo can produce (already done for the sample RFPs and catalog; add the learned knowledge items and the requirement texts used by 1.2 and 1.4), so the fallback is only reached for a new RFP offline. For the fallback itself, BM25 with a simple stemmer is a small, dependency-free improvement; and show the mode on every page that uses search (the RFP page already does).

### 4.2 Duplicate detection (`requirements/grouping.py`)

- **Current:** difflib `SequenceMatcher` ratio over normalised quotes with three cheap upper bounds, threshold 0.92, only for quotes longer than 40 characters; exact matches via a dictionary.
- **Limitation:** Quadratic in the number of items (about 350,000 pairs for 840 items, kept fast only by the bounds); misses paraphrased restatements; the threshold is a guess.
- **Proposed:** Keep the exact and near-exact path; add the embedding pass of 1.4 for paraphrases; measure the threshold against the 21 duplicates on Syracuse plus the reviewer's restore actions (`approve` of a duplicate), and store it in a data file with the other thresholds (4.4).

### 4.3 Keyword scope detection and facts ported from v0.3.0 (`matching/checks.py`, `data/knowledge_base/spinco_layers.json`)

- **Current:** A layer is in scope on keyword counts (min hits 3, two distinct terms, or a decisive term); facts such as rack density and UPS kVA come from regular expressions over the quotes; "no layer met the threshold" assumes full scope.
- **Limitation:** Keyword lists were written for the data-centre samples; on a real RFP a stray word ("interconnect" in a cable spec) puts a layer in scope, and the full-scope default makes every unit look suggested when nothing matches. The regular expressions are brittle on units and spelling ("13.2kV" versus "13.2 kV" is handled, "13,2 kV" is not).
- **Proposed:** Derive scope from the matches instead of keywords once matching has run (a layer is in scope when an accepted match points to a unit of that layer; keywords only before matching), keep keyword evidence as a secondary view, and read facts from the data-sheet tables first (`portfolio.data_sheet`) and from quotes second. Replace the "full scope assumed" default with "scope unknown" (rule R5: unknown never passes).

### 4.4 Placeholder thresholds scattered in code

- **Current:** `MIN_SCORE = 0.08` (matching), `DUPLICATE_RATIO = 0.92`, `DRASTIC_SHARE = 0.25` (changes), `coverage_threshold 0.8` (go_no_go.json), `LOW_CONFIDENCE = 60`, `UNMAPPED_SHARE = 0.05`, `BAND = 0.08`, table limits (ingestion), `READER_RECALL = 0.90` and the other guard thresholds (model_guard), capacities and standard ratings (portfolio.json, one product).
- **Limitation:** They are starting guesses (each one says so), live in five places, and the pages label only some of them as placeholders.
- **Proposed:** One `data/knowledge_base/thresholds.json` read through `catalog`, a `source` field per value ("placeholder" or "calibrated on N RFPs, date"), and the label shown wherever the value drives a message. Calibration is a script over real RFPs, not a code change.

### 4.5 Synchronous long requests

- **Current:** `POST /opportunities/{id}/requirements/extract` and `POST /opportunities/{id}/changes` run the agents inside the request; the document upload starts ingestion as a background task but offers no progress, so the page says "use Refresh status".
- **Limitation:** A live read of a long RFP holds the connection for a minute or more (proxy time-outs, a second click re-uploads), and the user sees no progress; a failure half-way leaves no record.
- **Proposed:** The job table and polling endpoint of section 2; the reader and change agents report `done / total` chunks from their executor loops; the page shows "page 37 of 101" and the problems list grows as they happen.

### 4.6 ID allocation by max + 1

- **Current:** `opportunities.create` reads every ID and retries on the unique-constraint error; `_next_req_id` scans every requirement ID and every requirement audit event of the opportunity on each `add()` (814 times during an extraction); `_next_kb_id` takes the last row plus one with no retry; baseline numbers are not protected against two simultaneous applies (noted in the architecture).
- **Limitation:** Correct but quadratic for extraction, and `_next_kb_id` can fail with an unhandled integrity error when two people send items at once.
- **Proposed:** A `sequence` table (name, last) incremented in the same transaction (one `UPDATE ... RETURNING` on PostgreSQL, a row-level update on SQLite), used by all four allocators; the "never reuse an ID" rule is then guaranteed by the sequence rather than by scanning the audit log. The audit-based rule stays as a test.

### 4.7 SQLite and the single process

- **Current:** SQLite with `check_same_thread=False`; JSON columns for units, evidence and bboxes; `lru_cache` on the catalog index and the RFP index inside the process; the learned knowledge in a JSON file next to the database.
- **Limitation:** One writer at a time; caches are per process, so a second API process would not see a newly learned item; the learned file is outside the database and outside the audit triggers.
- **Proposed:** PostgreSQL for a pilot (section 2); move learned knowledge into a table (it already has `KnowledgeItem` rows, so `catalog.learn` can read approved items from there and drop the file); invalidate the in-process indexes by a version row rather than `cache_clear()`.

### 4.8 Layout cache keyed by file hash only (`ingestion/service.py`)

- **Current:** `ingest()` uses `data/layout_cache/<sha256>.json` whenever it exists, regardless of `pipeline_version`.
- **Limitation:** A parser change on the parsing machine without a re-freeze leaves other machines on an older layout silently; the version is stored but not compared.
- **Proposed:** Compare the stored `pipeline_version` with the current one and report "frozen layout from an older parser" in the ingest result and on the RFP page; still use it (deterministic demos), but say so.

### 4.9 Matcher page header heuristic (`matching/agent.py: page_header`)

- **Current:** The header block is every line above the bottom of the last furniture line in the top half of the page.
- **Limitation:** Two-column data sheets and pages without detected furniture give an empty or over-long header; the header changes the prompt, so a layout change moves frozen answers.
- **Proposed:** Use the section path once headings are in the layout model (stage 1 item, not yet built), falling back to the current rule; both are deterministic.

### 4.10 Reading all versions to find the current ones (`requirements.current`)

- **Current:** A subquery for the max version per `req_id`, then Python filtering and sorting; called many times per request (trace, coverage, evidence, dispatch each call it, and `children()` calls it per group).
- **Limitation:** On 348 requirements it is fine; a trace page already triggers it several times, and `children()` makes it O(groups × requirements).
- **Proposed:** A `current` flag maintained on write (set false on the old version in `_version`), an index on (opportunity_id, current), and `children_by_parent()` returning a dict in one pass.

### 4.11 Grouping only within a page (`grouping.py`)

- **Current:** One call per page with three or more items; groups cannot span pages.
- **Limitation:** A drawing list or standards list that continues on the next page becomes two requirements; tables that continue are already linked in the layout (`continues_from`) but the grouper does not use that.
- **Proposed:** Treat a page and its continuation table as one grouping unit; otherwise propose cross-page links through 1.4.

## 5. Experimental Ideas

Clearly separate from the roadmap: each needs data, a decision or a proof before it belongs in a plan.

- **Fine-tuning a small reader model** on reviewed RFPs, hosted inside the enterprise. Excluded by the current direction; worth revisiting only when hundreds of reviewed real RFPs exist and the hosted-model decision (section 14 of the architecture) is taken. The frozen-answer mechanism and `model_guard` would stay as they are.
- **Two independent reads of each page** (a second prompt wording or a second model) with the union offered for review: raises recall at twice the reading cost; the difference set is itself a useful review filter. Measure on the golden list first.
- **Vision reading of drawing sheets** (1.7, item 4): promising for title blocks and notes, but every reading must be verified against OCR words before it can be anchored, and drawings may carry the most sensitive customer data.
- **Automatic catalog drafting from unit datasheets**: feed a unit's product datasheets through the reader pipeline to draft `products.json` entries (name, description, keywords, standard ratings for the deviation check). A product manager approves each entry; it would also fill `portfolio.json` with real standard ratings.
- **Similar-RFP detection across opportunities**: embed whole RFPs (mean of passage vectors) to flag "this looks like OPP-0003 from last year" at upload, and reuse its decisions and answers through 1.2 and 1.3.
- **A requirement dependency graph** built from change-impact predictions (1.5) and confirmed by people, visualised as a small inline SVG on the Changes page: which requirements move together when one changes.
- **Self-check of the outline against the RFP's submission requirements**: a model pass that reads the drafted outline and the submission-category requirements and lists what the proposal format still lacks (page limits, forms, signatures). Useful, but it is a judgement about the proposal, so it stays advice.
- **Bid outcome prediction** (1.6) as a learned model: only after outcomes are recorded and back-tested on SpinCo history; otherwise it stays a criteria count.

## 6. Prioritized Recommendations

Priority: P0 = before or right after the pilot decision (small, high value, or a precondition); P1 = first pilot increment; P2 = pilot with real data; P3 = later or experimental.

| Feature / Area | Current Limitation | Suggested Improvement | Technology | PoC Value | Complexity | Priority (P0-P3) |
|---|---|---|---|---|---|---|
| Reader precision (1.1) | 54% of proposals overlap a golden item; review burden | Export review signals from the audit log; per-category precision; few-shot and "do not list" rules; regenerate under `model_guard` | Existing gateway, scripts | High | Low-Med | P0 |
| Ask the RFP with citations (1.8) | Search returns passages only | Retrieve-then-answer task with citation guard, mode shown, audited | Existing index and gateway | High | Low | P0 |
| Progress for long runs (2, 4.5) | Extract and change upload block the request without progress | Job table, background start, polling endpoint, "page n of N" | FastAPI BackgroundTasks, one table | Medium | Low-Med | P0 |
| Thresholds as data (4.4) | Guesses in five places, partly unlabelled | One thresholds file with a source field; label on every page that uses one | JSON through `catalog` | Medium | Low | P0 |
| Outcome capture (1.6, 3.11) | No won/lost record; no history for any score | Outcome fields and audit event on the opportunity | SQLAlchemy | Medium | Low | P0 |
| Answer drafting per unit (1.3) | Units type every answer from scratch | "Suggest an answer" from the unit's past responses and approved knowledge, cited, person submits | Gateway, index | High | Low-Med | P1 |
| Matcher memory (1.2) | Decisions on matches are not reused; prompt cannot change without regeneration | Learned-match lookup before the model call; rejections re-rank evidence; "learned from" shown | `vectors.Index` | Medium-High | Medium | P1 |
| Alembic and PostgreSQL (2, 4.7) | create_all, SQLite single writer, SQLite-only audit triggers | Migrations; PostgreSQL with append-only trigger or role; same tests on both | Alembic, PostgreSQL | Medium (pilot precondition) | Medium | P1 |
| Sign-in and roles (2) | Actor from a cookie; role checks by name constants | OpenID Connect, user and role table, audit actor from the token | OIDC | Medium (pilot precondition) | Medium | P1 |
| Consistency check on answers (3.1) | Validator reads every answer unaided | Rule checks at submit; optional model note for the validator | Rules, one call on demand | Medium | Low | P1 |
| Version diff and audit page (3.3, 3.6) | History is a list; audit data has no page | Word-level diff; filterable audit table per opportunity | difflib, one page | Medium | Low | P1 |
| ID allocation (4.6) | Scans per add; KB IDs can collide | Sequence table in the same transaction | SQLAlchemy | Low | Low | P1 |
| Tables as rows for the reader (1.7) | Data sheets read as loose lines | `tables_as_text` in the page prompt; regenerate and compare | Layout model, gateway | Medium | Medium | P1 |
| Embedding duplicates and relations (1.4, 4.2, 4.11) | difflib near-verbatim only; grouping per page | Similarity pass with "related" links for review; continuation tables grouped together | `vectors.Index` | Medium | Low-Med | P2 |
| Change impact suggestions (1.5) | Only targeted requirements' answers return | Group, table, section and similarity based suggestions, optional model pass, person decides | Index, gateway | Medium | Medium | P2 |
| Scope from matches (4.3) | Keyword scope; full scope assumed when nothing matches | Scope from accepted matches; facts from data-sheet tables; "unknown" instead of full scope | Rules | Medium | Low-Med | P2 |
| Catalog import per unit (3.8) | Illustrative JSON edited by hand | Spreadsheet import with validation and a version stamp | openpyxl | Medium | Low-Med | P2 |
| Proposal document (2) | Outline as Markdown | docx rendering of outline plus matrix appendix, no model | python-docx | Medium | Low-Med | P2 |
| Region OCR and unruled tables (1.7) | Figure text and unruled tables not read | Region OCR marked `figure_text`; text-strategy tables; parsing machine only | Tesseract, pdfplumber | Medium | Medium | P2 |
| Clarification list for the customer (3.2) | Warnings and unanchored items scattered | Numbered question list exported with the matrix | Rules | Medium | Low | P2 |
| Vector store (2) | Numpy index in one process | pgvector when the index reaches hundreds of thousands of passages or several processes | pgvector | Low now | Medium | P3 |
| Enterprise-hosted model (2) | Hosted model only; real bids cannot be sent | Second provider in the gateway, accepted through `model_guard compare` | Local or private deployment | High for real bids | Medium-High | P3 (decision first) |
| Bid risk score from history (1.6) | Criteria count only | Transparent weighted score with sample size, after back-testing | scikit-learn | Low now | Medium | P3 |
| Vision reading of drawings (1.7, 5) | Drawing sheets skipped; page 83 low confidence | Vision call verified against OCR words, anchored only when verified | Vision deployment | Medium | High | P3 |
| Fine-tuned reader (5) | Excluded by direction; no data | Revisit with hundreds of reviewed RFPs and an enterprise model | Fine-tuning | Unknown | High | P3 |
