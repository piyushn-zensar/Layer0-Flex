# Layer 0: API, End to End (Current System)

Status: Implemented (as built). Describes the code at commit 4c6d866 of the Layer0-Flex repository as of 13 Oct 2026.

Audience: developers, integrators and testers who call, test or extend the API.

Companion documents: [01-system-architecture.md](01-system-architecture.md), [02-technical-architecture.md](02-technical-architecture.md), [03-ui-view.md](03-ui-view.md). Earlier design documents: [../technical-architecture.md](../technical-architecture.md), [../architecture-overview.md](../architecture-overview.md).

Screenshots were taken from an isolated copy of the application running the bundled demo data in offline mode; they are in [images/](images/).

## Changes Decided After This Baseline

This document describes the system as built at commit 4c6d866. The review of 12 Oct 2026 decided changes that are not built yet; they are listed in [../changes.md](../changes.md) (C-01 to C-22) with their target design in [../technical-architecture.md](../technical-architecture.md) section 16. Until each change is built, the description below stays accurate. Sections affected:

| Section | Changes | What will differ |
|---|---|---|
| [3. Conventions](#3-conventions) | C-09 | Session cookie and 401 instead of the X-Actor header |
| [7. Requirements Endpoints](#7-requirements-endpoints) | C-02, C-03, C-04 | New: extraction snapshots, resolve, dismiss, corrections; publish semantics for baselines |
| [8. Changes Endpoints](#8-changes-endpoints) | C-04 | Customer-change origin |
| [11. Decisions Endpoints](#11-decisions-endpoints) | C-06, C-10 | Go/no-go after assessment; revised criteria |
| [12. Work Package Endpoints](#12-work-package-endpoints) | C-06, C-07, C-12, C-16, C-17 | Dispatch without go; configurable validation; new response fields; history; comments |
| [14. Consolidation Endpoints](#14-consolidation-endpoints) | C-13 | New JSON compliance-matrix endpoint; new export columns |
| [16. Front-End Route Handler and Built-In Endpoints](#16-front-end-route-handler-and-built-in-endpoints) | C-09 | New auth endpoints: login, logout, me |
| [19. Dependencies Between Endpoints](#19-dependencies-between-endpoints) | C-06 | Dispatch no longer depends on go/no-go |

## Contents

- [Changes Decided After This Baseline](#changes-decided-after-this-baseline)
- [1. About This Document](#1-about-this-document)
- [2. The API at a Glance](#2-the-api-at-a-glance)
- [3. Conventions](#3-conventions)
- [4. Endpoint Index](#4-endpoint-index)
- [5. Opportunities and Documents Endpoints](#5-opportunities-and-documents-endpoints)
- [6. Ingestion Endpoints](#6-ingestion-endpoints)
- [7. Requirements Endpoints](#7-requirements-endpoints)
- [8. Changes Endpoints](#8-changes-endpoints)
- [9. Catalog Endpoints](#9-catalog-endpoints)
- [10. Matching Endpoints](#10-matching-endpoints)
- [11. Decisions Endpoints](#11-decisions-endpoints)
- [12. Work Package Endpoints](#12-work-package-endpoints)
- [13. Knowledge Endpoints](#13-knowledge-endpoints)
- [14. Consolidation Endpoints](#14-consolidation-endpoints)
- [15. Trace Endpoints](#15-trace-endpoints)
- [16. Front-End Route Handler and Built-In Endpoints](#16-front-end-route-handler-and-built-in-endpoints)
- [17. Shared Data Shapes](#17-shared-data-shapes)
- [18. Error Catalogue](#18-error-catalogue)
- [19. Dependencies Between Endpoints](#19-dependencies-between-endpoints)
- [20. Calling Sequences](#20-calling-sequences)
- [21. Screen Load Sequences](#21-screen-load-sequences)
- [22. State Machines Driven by the API](#22-state-machines-driven-by-the-api)

## 1. About This Document

### 1.1 Purpose

This document describes the Layer 0 application programming interface (API) as it is built today. An API is the set of web addresses (endpoints) that the screens, scripts and other systems call to read and change Layer 0 data. For every endpoint it gives the method, the path, what the endpoint is for, its parameters, its request body, its response, its status codes and exact error messages, what it writes, which agent (model task) it calls, what must be true before it can be called, which screen calls it, and a ready-to-run `curl` example. It then explains how the endpoints depend on each other: the exact calling sequences, the sequence of calls each screen makes when it loads, and the state machines that the API drives.

The document is an as-built description. It says what the code does, not what an earlier design intended. Where an idea exists only as a proposal, it is labelled as such (see section 1.6).

### 1.2 Audience

- Client architects and reviewers who need to know what the API offers and how it behaves.
- Integration engineers who will connect another system (for example a CPQ tool, a design-engineering queue or a reporting tool) to Layer 0.
- Developers and testers who extend, test or operate the proof of concept (PoC).
- Bid teams who want to understand what happens behind each button.

No knowledge of the code is needed to read sections 1 to 4. Sections 5 to 18 are a reference. Sections 19 to 22 explain the flows end to end.

### 1.3 Scope

| In scope | Out of scope (where to find it) |
|---|---|
| All 51 operations of the FastAPI application under `/api` (11 modules) | The screens, their layout and their components (03-ui-view.md) |
| The Next.js route handler `GET /tour-session` | The Next.js page routes such as `/portfolio` or `/opportunities/{id}/trace`: they return web pages, not data (03-ui-view.md) |
| The FastAPI built-in endpoints `GET /docs`, `GET /redoc`, `GET /openapi.json` | The system context, the module structure and the data flow (01-system-architecture.md) |
| Request and response shapes, error messages, side effects, model calls | The code structure, the data model, configuration, installation and deployment (02-technical-architecture.md) |
| Dependencies between endpoints, calling sequences, screen load sequences, state machines | The internal design of each agent's prompt (02-technical-architecture.md) |

Nothing is left out on purpose: every endpoint the running application exposes is listed in section 4 and described in sections 5 to 16.

### 1.4 Code Baseline

| Item | Value |
|---|---|
| Repository | Layer0-Flex |
| Code version | commit `4c6d866` |
| Described as of | 13 Oct 2026 |
| API title (OpenAPI) | "Layer 0 API - opportunity workflow PoC", version `0.1.0`, OpenAPI `3.1.0` |
| API entry point | `app/main.py` |
| Web proxy and route handler | `web/next.config.ts`, `web/app/tour-session/route.ts` |
| Browser API client | `web/lib/api.ts` |

The single source of truth is the code. Every statement in this document was checked against the files named in it. File paths are given relative to the repository root.

### 1.5 How the Examples Were Produced

- All example responses were captured on 13 Oct 2026 from an isolated running copy of the application. The copy had its own database and file store, so the examples did not touch any other installation.
- The copy ran the bundled demo data in offline (mock) mode (`LLM_PROVIDER=mock`). In this mode no language model is contacted. Every agent answer comes from the committed frozen answers in `data/llm_cache/`. Section 3.10 explains what happens when no frozen answer exists.
- The demo data in that copy:
  - `OPP-0001`: Syracuse Regional Airport Authority, RFP 2023-20 switchgear procurement (101 pages). 348 requirements were frozen as baseline 1, matched, participation and a "go" were recorded, and work was dispatched. Then the illustrative Addendum No. 1 was read and applied, which created baseline 2: `REQ-0001-0977` and `REQ-0001-0978` added, `REQ-0001-0039` and `REQ-0001-0332` modified, `REQ-0001-0130` removed.
  - `OPP-0002`: a fictional one-page hyperscale AI campus RFP with 10 requirements, dispatched to several units.
  - `OPP-0003`: a blank opportunity with no documents (empty states).
  - `OPP-0004`: the hyperscale sample attached, 4 requirements added by hand, review in progress, not frozen.
  - One knowledge item (`KB-0001`) queued for the curator.
- Calls that change data were made only on opportunities created for the examples (for example `OPP-0005`, "API conventions example"), never on the four demo opportunities. Several error examples come from refused calls: a refused call changes nothing.
- Long responses are trimmed. A trimmed part is shown as `…`. Field names, values, identifiers and messages are copied exactly.
- Identifiers, counts and timestamps come from that copy. Another installation will show other values.
- The `curl` examples use the standard address of the API, `http://127.0.0.1:8000` (the isolated copy listened on another port; the answers are the same).

### 1.6 Status Labels

| Label | Meaning |
|---|---|
| Implemented | The code does this today. Because almost everything in this document is implemented, the label is given once per section or in a table column, not on every sentence. |
| Proposed (not built) | An idea from `SUGGESTIONS.md` or from a code comment that marks later work. The running system does not do it. |
| Needs confirmation | Something that cannot be verified from the code (for example a business threshold that the code marks as a placeholder). |

### 1.7 How to Read an Endpoint Entry

Sections 5 to 16 describe the endpoints one by one. Each entry uses the same structure:

| Part | What it gives |
|---|---|
| Method and path | The HTTP method and the path, with path parameters in braces, for example `POST /api/requirements/{req_id}/review` |
| Purpose | One or two sentences in plain English |
| Parameters | Path and query parameters, with type, constraint and default |
| Request body | Every field, type, constraint and default (JSON or multipart) |
| Response | Every field, with a real trimmed example |
| Status codes and errors | Each status code with the exact error message text |
| Side effects | Tables and files written, and the audit action recorded |
| Model calls | The agent task name sent to the model gateway, or "none" |
| Preconditions | What must be true first (for example "the baseline is frozen") |
| Called by | The screen and control that call it, or "not called by the UI" |
| Example | A `curl` command |

### 1.8 Terms Used in This Document

| Term | Meaning |
|---|---|
| Opportunity | One bid that Layer 0 works on, identified as `OPP-0001` and so on. It holds documents, requirements, decisions and work. |
| RFP | Request for proposal: the customer's tender document. The opportunity's first RFP is its main document (role `main`). |
| Change document | A later document from the customer (addendum, answers to questions, change request) that changes the requirements after they were frozen. |
| Layout model | The machine-readable form of a PDF: per page, its lines with numbers and position boxes, its tables, and which lines are headers or footers. Every source reference in Layer 0 points into it. |
| Line item / requirement | One obligation taken from the RFP, with a verbatim quote and its exact source (page and lines). Identified as `REQ-0001-0001` and so on. |
| Group and sub-requirement | A requirement made of several related line items on the same page. The line items become its sub-requirements. |
| Anchored / unanchored | A requirement whose quote was found on its page and lines is `EXTRACTED` (anchored). One whose quote could not be found is kept as `UNANCHORED` for a person to check. |
| Baseline | The frozen set of approved requirements. Baseline 1 is made by the freeze; each applied change document makes the next baseline. |
| Agent | A step in which the language model proposes something (requirements, groups, matches, change classifications, a response draft). A person always confirms or decides. |
| Frozen answer | A model answer stored in `data/llm_cache/` and committed with the code. The same question gets the same answer again, without calling the model. |
| Offline (mock) mode | Running without a model connection (`LLM_PROVIDER=mock`, the default). Only questions with a frozen answer can be answered. |
| Business unit | A Flex business unit that offers products, identified by a code such as `CROWN` or `EP2`. `BID` is the bid desk, a pseudo-unit for requirements the bid manager answers. |
| Match | The proposed business unit or units, product and offering type for one requirement. |
| Offering type | How a product is offered: `CTO` (configure to order), `SEMI_CUSTOM`, `ETO` (engineer to order), or `NONE` (not a product item). |
| Participation | The decision about which business units take part in the bid. |
| Go / no-go | The decision whether to bid. |
| Assignment / work package | One requirement assigned to one business unit. A unit's assignments form its work package. |
| Compliance | A unit's answer level: `met`, `partial`, `not_met` or `exception`. |
| Validation | The bid manager's check of a unit's answer: validated, or returned with a note. |
| Change set / change item | One change document read against the baseline, and each statement in it with its proposed and confirmed classification. |
| Knowledge item | A requirement, validated answer or decision rationale sent to the knowledge base, waiting for the curator. Identified as `KB-0001` and so on. |
| Actor | The person on whose behalf a call is made. It is recorded on every change (section 3.1). |
| Audit event | One row of the append-only audit log: who did what, when, to which item. |
| Hand-off payload | A JSON file per business unit and opportunity for the unit's own downstream systems. |
| Compliance matrix | The export of every requirement with its unit, product, compliance and answer (CSV and Excel). |
| Response outline | A first draft of the proposal chapters, written only from validated answers. |

### 1.9 Companion Documents

| Document | What it covers |
|---|---|
| 01-system-architecture.md | System context, modules and how data flows between them |
| 02-technical-architecture.md | Code structure, data model, configuration, model gateway, installation and operation |
| 03-ui-view.md | Every screen and every component, end to end, with screenshots |
| 04-api-view.md (this document) | Every API endpoint and how the endpoints work together |
| `Documents/technical-architecture.md`, `Documents/architecture-overview.md` | The earlier design documents. Their terms are used here. Where they differ from the code, this document follows the code. |

## 2. The API at a Glance

### 2.1 Base Address and the Web Proxy

Layer 0 runs as two processes on one machine:

| Process | Address | What it serves |
|---|---|---|
| FastAPI back end (`app/main.py`, started by `start.cmd` with `.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 75`) | `http://127.0.0.1:8000` | Every data endpoint, all under the prefix `/api`; the interactive documentation `/docs`, `/redoc`, `/openapi.json` |
| Next.js web app (`web/`, started by `start.cmd` with `npm start -- -p 3000`) | `http://localhost:3000` | The screens; the route handler `/tour-session`; a proxy for `/api/*` |

The browser talks only to the web app. The web app forwards every request whose path starts with `/api/` to the back end. The rule is in `web/next.config.ts`:

- source `/api/:path*`, destination `${API_URL}/api/:path*`;
- `API_URL` is an environment variable of the web app; its default is `http://127.0.0.1:8000`;
- `experimental.proxyTimeout` is 30 minutes (`30 * 60 * 1000` ms). The code comment explains why: agent runs on a new RFP make hundreds of model calls and can take many minutes, and the default proxy wait of about 30 seconds cut them off with "socket hang up" while the API kept working.

So the same endpoint can be reached in two ways, with the same result:

| From | Address of `GET /api/people` |
|---|---|
| A browser or script, through the web app | `http://localhost:3000/api/people` |
| A script on the same machine, directly | `http://127.0.0.1:8000/api/people` |

The back end listens on `127.0.0.1` only, so it cannot be reached from another machine. Only `/api/*` is forwarded: `/docs`, `/redoc` and `/openapi.json` answer only on the back-end address (through the web app they return "404 Not Found").

`start.cmd` sets `--timeout-keep-alive 75` because the web app's proxy reuses idle connections. With uvicorn's default of 5 seconds, a page load now and then failed with "socket hang up".

### 2.2 Interactive Documentation

FastAPI generates three built-in endpoints from the code (Implemented; detailed in section 16):

| Endpoint | What it is |
|---|---|
| `GET /docs` | Swagger UI: a web page that lists every operation, shows its request and response schema, and lets a person try it |
| `GET /redoc` | The same specification shown with ReDoc, as a readable reference |
| `GET /openapi.json` | The machine-readable OpenAPI 3.1.0 specification (title "Layer 0 API - opportunity workflow PoC", version `0.1.0`) |

The specification groups the operations by tag. Each tag is the name of the module that owns the operation. The specification lists the request models (for example `OpportunityIn`, `ReviewIn`, `RespondIn`) and the validation error shape. It does not describe the response bodies: the controllers return plain dictionaries, so all 51 operations show the status 200 "Successful Response" with an empty `application/json` schema. The specification even lists the CSV, Excel, Markdown and PNG downloads as `application/json`; their real content types are in section 3.4. It lists no error statuses other than 422. Sections 5 to 15 and section 17 of this document fill these gaps.

### 2.3 Architecture Diagram

```text
  Person in a browser  ("Acting as" picker sets who acts)
        |
        |  same-origin HTTP: pages, /api/*, /tour-session
        v
  +---------------------------------------------------------------+
  | Next.js web app   (web/, port 3000)                           |
  |   pages and components (client-side fetch, web/lib/api.ts)   |
  |   GET /tour-session  (route handler, walkthrough session id)  |
  |   rewrite /api/:path*  ->  ${API_URL}/api/:path*              |
  |   (API_URL default http://127.0.0.1:8000; proxy time-out 30m) |
  +---------------------------------------------------------------+
        |
        |  HTTP, request forwarded with its headers (X-Actor) and cookies
        v
  +---------------------------------------------------------------+
  | FastAPI app "Layer 0 API - opportunity workflow PoC"          |
  | (app/main.py, port 8000; /docs  /redoc  /openapi.json)        |
  |                                                               |
  |  /api routers, registered in workflow order:                  |
  |   opportunities (5)  ingestion (4)     requirements (10)      |
  |   catalog (3)        matching (3)      decisions (3)          |
  |   workpackages (5)   consolidation (5) knowledge (4)          |
  |   changes (7)        trace (2)                                |
  |        |                                                      |
  |        |  controller.py  ->  service.py (public functions)    |
  |        v                                                      |
  |  app/core:  db.py (one session per request)                   |
  |             audit.py (append-only audit log)                  |
  |             web.py (acting person, row serialisation)         |
  |             llm.py (model gateway, frozen answers)            |
  |             vectors.py (retrieval indexes)   config.py        |
  +---------------------------------------------------------------+
      |                 |                     |                  |
      v                 v                     v                  v
  SQLite database    Store files           Committed data      Azure OpenAI
  STORE/layer0.db    STORE/files/          data/knowledge_base (only when
  (11 tables,        STORE/layouts/        data/llm_cache      LLM_PROVIDER=azure;
   WAL mode)         STORE/pages/          data/vector_cache   never contacted in
                     STORE/knowledge_      data/layout_cache   offline mode)
                       learned.json        data/RFP
```

`STORE` is the directory named by the environment variable `STORE_DIR` (default `data/store`, not committed). The data directories under `data/` are committed with the code.

### 2.4 Operations per Module

The application registers one router per module, all under the prefix `/api`, in this order (`MODULES` in `app/main.py`): opportunities, ingestion, requirements, catalog, matching, decisions, workpackages, consolidation, knowledge, changes, trace.

| Module (OpenAPI tag) | GET | POST | Total | What it owns | Detailed in |
|---|---|---|---|---|---|
| opportunities | 2 | 3 | 5 | Opportunities, documents, bundled samples (`opportunity`, `document`; `STORE/files/`) | Section 5 |
| ingestion | 3 | 1 | 4 | Reading PDFs into the layout model, page images, RFP search (`STORE/layouts/`, `STORE/pages/`) | Section 6 |
| requirements | 2 | 8 | 10 | Line items, groups, review, freeze, history (`requirement`, `baseline`) | Section 7 |
| catalog | 3 | 0 | 3 | Business units, products, catalog items, past responses, people (read-only, from `data/knowledge_base/`) | Section 9 |
| matching | 0 | 3 | 3 | Requirement-to-unit matches (`match`) | Section 10 |
| decisions | 1 | 2 | 3 | Participation and go/no-go with their evidence (`decision`) | Section 11 |
| workpackages | 2 | 3 | 5 | Dispatch, unit answers, validation, hand-off (`assignment`) | Section 12 |
| consolidation | 5 | 0 | 5 | Coverage, compliance matrix, response outline (read-only) | Section 14 |
| knowledge | 2 | 2 | 4 | Knowledge-base queue and curation (`knowledge_item`; `STORE/knowledge_learned.json`) | Section 13 |
| changes | 1 | 6 | 7 | Change documents against the baseline (`change_set`, `change_item`) | Section 8 |
| trace | 2 | 0 | 2 | Portfolio and the three linked traceability screens (read-only) | Section 15 |
| **Total** | **23** | **28** | **51** | Every module that changes data also writes `audit_event` | |

Four further endpoints are not part of the `/api` set: the Next.js route handler `GET /tour-session` and the three FastAPI built-ins (section 16). With them the system exposes 55 endpoints.

### 2.5 Operations per Method

| Method | Count | Use |
|---|---|---|
| GET | 23 | Reads, exports and downloads. None changes database rows. A few write cache files (section 3.16). |
| POST | 28 | Every change: creating, uploading, reading, reviewing, deciding, dispatching, answering, applying |
| PUT, PATCH, DELETE | 0 | Not used. Nothing is edited in place or deleted through the API: a change is a new row, a new version or a new status, and every change is an audit event. |

### 2.6 Path Families

| Path prefix | Operations | Examples |
|---|---|---|
| `/api/opportunities` and `/api/opportunities/{opp_id}/...` | 28 | create, detail, documents, requirements, baselines, match, decisions, dispatch, hand-off, changes, consolidation, trace, knowledge |
| `/api/documents/{doc_id}/...` | 3 | ingest, page layout, page image |
| `/api/requirements/{req_id}/...` | 4 | review, split, ungroup, history |
| `/api/changes/{set_id}/...` | 4 | decide an item, confirm all, apply, discard |
| `/api/matches/{match_id}/decide` | 1 | accept or reject a match |
| `/api/assignments/{assignment_id}/...` | 2 | respond, validate |
| `/api/inbox/{bu}` | 1 | a unit's work |
| `/api/knowledge` and `/api/knowledge/{kb_id}/review` | 3 | send, list, review |
| `/api/catalog`, `/api/catalog/search`, `/api/people`, `/api/samples`, `/api/portfolio` | 5 | reference data and the opportunity list |
| **Total** | **51** | |

There is no `GET /api/opportunities` list endpoint. The list of opportunities comes from `GET /api/portfolio` (section 15), newest first, with each one's requirement count and per-unit progress.

### 2.7 Interaction Style

| Aspect | How the API behaves (Implemented) |
|---|---|
| Style | Plain request and response over HTTP. Each call does its work and answers when it is done. |
| Long calls | Agent runs happen inside the request: `POST .../requirements/extract`, `POST .../match`, `POST .../changes`, `POST .../changes/from-sample`, `POST /api/changes/{set_id}/apply`, and `GET .../response-outline` (section 3.12). |
| Background work | One case only: after `POST .../documents` and `POST .../documents/from-sample` answer, the PDF is read into the layout model in a background task. Nothing reports progress; the client reads the document's `status` again (`GET /api/opportunities/{opp_id}`). |
| Data format | JSON in and out, UTF-8. Exceptions: file uploads are `multipart/form-data`; downloads are CSV, Excel, Markdown, PNG and a JSON file served as an attachment (section 3.4). |
| Paging | None. Every list is returned in full (for example, in the demo copy, 349 rows for the `OPP-0001` traceability view and 978 rows, including inactive line items and sub-requirements, for its requirements list). |
| Sorting and filtering | Fixed per endpoint (section 3.14). The only filter parameter is `status` on `GET /api/knowledge`; the only search parameters are `q` and `k`. |
| Versioning | None. The paths carry no version number. |
| Authentication | None. The acting person is a name sent in the `X-Actor` header (section 3.1). |
| Cross-origin calls | No CORS middleware is configured. A browser page from another origin cannot call the API; the Layer 0 screens call it through the same-origin proxy. |
| Rate limits, request size limits | None set in the code. Uploaded files are read whole into memory. |
| Streaming, server push, webhooks | None. |

### 2.8 The Workflow the Endpoints Follow

The modules are registered in workflow order, and the main path through the API follows the life of a bid. The arrows show the usual order; sections 19 to 22 give the exact preconditions, sequences and state machines.

```text
 1. POST /api/opportunities                         create the opportunity           status: new
 2. POST /api/opportunities/{opp}/documents         attach the main RFP (PDF)
       (background) read into the layout model      document: uploaded -> ingesting -> ingested
 3. POST /api/opportunities/{opp}/requirements/extract
                                                    reader + grouping agents         status: review
 4. POST /api/requirements/{req}/review  (many)     approve / reject / edit; split, merge, ungroup, add missed
 5. POST /api/opportunities/{opp}/baselines         freeze baseline 1                status: frozen
 6. POST /api/opportunities/{opp}/match             matching agent proposes units
    POST /api/matches/{id}/decide, POST .../requirements/{req}/match   people accept, reject, change
 7. POST /api/opportunities/{opp}/participation     which units take part
 8. POST /api/opportunities/{opp}/go-no-go          go or no-go                      status: go | no_go
 9. POST /api/opportunities/{opp}/dispatch          one assignment per unit          status: dispatched
10. POST /api/assignments/{id}/respond  (units)     answer each requirement
11. POST /api/assignments/{id}/validate (bid mgr)   validate or return with a note
12. GET  .../consolidation, .../compliance-matrix.xlsx, .../response-outline    final response material
    GET  /api/opportunities/{opp}/handoff/{bu}      hand-off file for a unit's systems
 *  POST /api/knowledge, POST /api/knowledge/{kb}/review   at any time once the source exists
 *  POST /api/opportunities/{opp}/changes           a change document after the freeze
    POST /api/changes/{set}/items/{item} | confirm-all, then POST /api/changes/{set}/apply
                                                    next baseline; answers returned; re-match; re-dispatch
```

## 3. Conventions

The rules in this section apply to every endpoint (Implemented). Sections 5 to 16 only mention where an endpoint differs.

### 3.1 Who Is Acting: the X-Actor Header

Layer 0 records a named person on every change (rule: agents propose, people decide). The person is sent with each request:

| Item | Rule (`app/core/web.py`, `web/lib/api.ts`) |
|---|---|
| Header | `X-Actor` (header names are not case-sensitive) |
| Value | The person's name, URL-encoded as UTF-8 (JavaScript `encodeURIComponent`). Example: `EP%C2%B2%20Design%20Engineer` for "EP² Design Engineer". |
| Fallback | If the header is missing or empty, the server reads the cookie `actor`. The web app writes this cookie when a person chooses a name in the "Acting as" picker (`actor=<URL-encoded name>; path=/; max-age=31536000`, one year). |
| Default | If neither gives a name, the actor is `Bid Manager`. A script that sends no header therefore acts as the Bid Manager. |
| Cleaning | The value is URL-decoded, every non-printable character (for example a line break or a tab) is removed, leading and trailing spaces are removed, and the result is cut to 80 characters, the size of every actor column. |
| Check against a list | None. Any name is accepted and recorded. `GET /api/people` lists the names the picker offers (section 9). |
| Who sends it | The browser client `api()` in `web/lib/api.ts` sets `X-Actor` on every call from the current cookie. Plain links and images (downloads, page images) send no `X-Actor`, but the browser sends the cookie; these are reads that record nothing. |

Real example. The header below has two leading spaces and a trailing line break; the stored name is clean:

```text
POST /api/opportunities
X-Actor: %20%20EP%C2%B2%20Design%20Engineer%0A
{"title": "API conventions example", "customer": "Example customer", "customer_type": "Utility"}

200 OK
{"id":"OPP-0005","title":"API conventions example","customer":"Example customer",
 "customer_type":"Utility","status":"new","created_by":"EP² Design Engineer",
 "created_at":"2026-10-13T07:56:04.433748+00:00"}
```

When an agent acts, the recorded actor names the agent and, in brackets, the person who started it:

| Agent | Recorded actor | Where it appears |
|---|---|---|
| Reader agent | `reader agent (<person>)` | `requirement.created_by` and the `proposed` audit events of extracted line items |
| Grouping agent | `grouping agent (<person>)` | `requirement.created_by` and the `grouped` audit events of groups |
| Matching agent | `matching agent (<person>)` | the `proposed` audit events of matches (from `POST .../match` and from the re-match inside `POST /api/changes/{set_id}/apply`) |

Most endpoints accept any actor and only record it. Five operations check the name and refuse a wrong person with status 403:

| Operation | Who may call it | Message for anyone else |
|---|---|---|
| `POST /api/changes/{set_id}/apply` | `Bid Manager` | "Only the Bid Manager applies a change set." |
| `POST /api/changes/{set_id}/discard` | `Bid Manager` | "Only the Bid Manager discards a change set." |
| `POST /api/assignments/{assignment_id}/validate` | `Bid Manager` | "Only the Bid Manager validates or returns answers." |
| `POST /api/knowledge/{kb_id}/review` | the curator, `Bid Manager` in the PoC | "Only the knowledge curator (in the PoC, the Bid Manager) approves knowledge." |
| `POST /api/assignments/{assignment_id}/respond` | the unit's product manager or design engineer, as named in `data/knowledge_base/business_units.json`; for the bid desk (`BID`), `Bid Manager` | "Only {bu}'s product manager or design engineer can answer this item." |

The names are compared exactly (case and spelling). The constants are `BID_MANAGER` in `app/modules/changes/service.py` and `app/modules/workpackages/service.py`, and `CURATOR` in `app/modules/knowledge/service.py`; code comments mark them as PoC simplifications until real roles come with sign-in.

Security note. There is no authentication. Anyone who can reach the API can act under any name. In the standard set-up the API listens only on `127.0.0.1`, so only programs on the same machine reach it directly. Proposed (not built): sign-in through the enterprise identity provider (OpenID Connect), a user table with roles (bid manager, curator, unit product manager, unit design engineer) replacing the name checks, and the audit actor taken from the sign-in token, with the header picker kept behind a flag for demos (`SUGGESTIONS.md`, section 2).

### 3.2 Request Bodies and Content-Type

- Every body that is not a file upload is a JSON object. The request must carry `Content-Type: application/json`.
  - Without it (for example `curl -d` with its default form type), FastAPI does not parse the body and answers 422: `{"detail":[{"type":"model_attributes_type","loc":["body"],"msg":"Input should be a valid dictionary or object to extract fields from","input":"{\"units\":[\"CROWN\"]}"}]}`.
  - Malformed JSON gives 422 with `"type":"json_invalid"` and `"msg":"JSON decode error"`.
- Fields that a model does not define are ignored.
- Fields with a default may be left out (each section gives the defaults).
- A POST that takes no body (for example `POST .../baselines`, `POST .../match`, `POST .../dispatch`, `POST /api/changes/{set_id}/apply`) ignores any body sent. The web client `post()` always sends `{}` when it has nothing to send.
- Query parameters are used only for search and filter: `q` and `k` (`GET /api/catalog`, `GET /api/catalog/search`, `GET .../rfp-search`) and `status` (`GET /api/knowledge`).
- Path parameters are text, except `set_id`, `item_id`, `match_id`, `assignment_id` and `page_no`, which are integers (section 3.7).

### 3.3 File Uploads (multipart/form-data)

Two operations take a file:

| Operation | Form fields | Rules |
|---|---|---|
| `POST /api/opportunities/{opp_id}/documents` | `file` (required), `role` (text, default `main`) | The screen offers the roles `main`, `addendum`, `qa`, `change`, `other`. The server accepts any text and treats only `main` specially: an opportunity has at most one main RFP. A file whose name does not end in `.pdf` (any case) is stored with status `unsupported` and never read. |
| `POST /api/opportunities/{opp_id}/changes` | `file` (required) | The role is always `change`. The file name must end in `.pdf` (any case), else 409 "Upload the change document as a PDF.". If the upload carries no file name, `change.pdf` is used. |

- The PDF test is the file name's extension, not the file content.
- The file is read whole into memory and stored as `STORE/files/<sha256>.pdf` (or `STORE/files/<sha256>` for other files). No size limit is set in the code (Needs confirmation for production use).
- The server's file path is never returned: the `path` column is removed from every document in a response.
- The bundled sample documents can be attached without a file through the `.../from-sample` operations, with a JSON body `{"name": "<sample name>"}` (sections 5 and 8).

Example of an upload, and a real answer for a non-PDF file uploaded twice to `OPP-0005` (the second answer is the same document, marked `existing`):

```text
curl -X POST -H "X-Actor: Bid%20Manager" \
     -F "file=@RFP-2023-20-Switchgear-Procurement-Final.pdf" -F "role=main" \
     http://127.0.0.1:8000/api/opportunities/OPP-0005/documents

POST /api/opportunities/OPP-0005/documents   file=note.txt role=other   (first time)
{"id":"OPP-0005-78be2cb12be2","sha256":"78be2cb12be273c25bc582192130f66582b9b539c8a16f012ac8b80b14bd03d6",
 "opportunity_id":"OPP-0005","filename":"note.txt","role":"other","status":"unsupported","page_count":0,
 "received_at":"2026-10-13T07:57:37.206530+00:00","existing":false}

POST /api/opportunities/OPP-0005/documents   file=note.txt role=other   (second time)
{"id":"OPP-0005-78be2cb12be2", … ,"received_at":"2026-10-13T07:57:37.206530","existing":true}
```

### 3.4 Downloads and Binary Responses

Five GET operations return something other than a JSON body for a screen:

| Operation | Content-Type | File name (Content-Disposition) | Content |
|---|---|---|---|
| `GET /api/opportunities/{opp_id}/compliance-matrix.csv` | `text/csv; charset=utf-8` | `attachment; filename="<opp>-compliance-matrix.csv"` | One row per assignment (one row for a requirement with none), 14 columns. Starts with a UTF-8 byte order mark so that Excel opens it as UTF-8. A cell that starts with `=`, `+`, `-`, `@`, a tab or a carriage return gets a leading `'` so that it cannot run as a formula. |
| `GET /api/opportunities/{opp_id}/compliance-matrix.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | `attachment; filename="<opp>-compliance-matrix.xlsx"` | Excel workbook with the sheets "Compliance matrix" and "Tracking" |
| `GET /api/opportunities/{opp_id}/response-outline.md` | `text/markdown; charset=utf-8` | `attachment; filename="<opp>-response-outline.md"` | The response outline as Markdown |
| `GET /api/opportunities/{opp_id}/handoff/{bu}` | `application/json` | `attachment; filename="<opp>-<bu>-handoff.json"` | The unit's hand-off payload (a JSON object, downloaded as a file) |
| `GET /api/documents/{doc_id}/pages/{page_no}.png` | `image/png` | none (shown inline) | One page of a stored PDF, rendered at 110 dpi |

In the three file names built by the consolidation module, every character of the opportunity ID other than a letter, digit or hyphen is replaced by `_`, and the ID is cut to 40 characters. The hand-off file name uses the path values as given; an unknown opportunity fails with 404 before the name is built.

Real headers from the demo copy:

```text
GET /api/opportunities/OPP-0001/compliance-matrix.csv
200 OK
content-type: text/csv; charset=utf-8
content-disposition: attachment; filename="OPP-0001-compliance-matrix.csv"
content-length: 160157

GET /api/opportunities/OPP-0001/handoff/CROWN
200 OK
content-type: application/json
content-disposition: attachment; filename="OPP-0001-CROWN-handoff.json"

GET /api/documents/OPP-0001-893403680eda/pages/1.png
200 OK
content-type: image/png
content-length: 160647
```

### 3.5 Identifier Formats

| Identifier | Format | Example | How it is made |
|---|---|---|---|
| Opportunity | `OPP-` + 4 digits | `OPP-0001` | Highest existing number + 1. If two people create one at the same moment, the loser retries with the next number (up to 20 tries, then 422 "Could not allocate an opportunity ID; try again."). |
| Document | `<opportunity ID>-` + the first 12 hexadecimal characters of the file's SHA-256 hash | `OPP-0001-893403680eda` | From the file content, so the same file in the same opportunity always has the same ID. The layout and page endpoints accept only IDs made of letters, digits and hyphens, at most 40 characters; anything else is "not found". |
| Requirement | `REQ-` + the opportunity's 4 digits + `-` + 4 digits | `REQ-0001-0977` | Highest number ever issued for the opportunity + 1, counting every ID in the audit log too, so a discarded draft's ID is never reused. A requirement keeps its ID across versions; each version has a `version` number. |
| Baseline | Integer per opportunity | `1`, `2` | 1 at the freeze; + 1 for each applied change set that changes something |
| Knowledge item | `KB-` + 4 digits, one sequence for the whole installation | `KB-0001` | Last number + 1; never reused |
| Match, assignment, decision, change set, change item | Integer, from the database | `1`, `358` | Auto-increment. `match_id` and `assignment_id` in a path must be between 1 and 2147483647, else 422. |
| Business unit | Code from `data/knowledge_base/business_units.json` | `CROWN`, `EP2`, `ANORD`, `FPM`, `JETCOOL`, `CLOUD`, `EMS`, `AFS` (active), `EPC` (pending) | Data, not code. `BID` is the bid desk pseudo-unit. |
| Product | Code from `data/knowledge_base/products.json` | `CROWN-ARMV`, `EP2-RPP` | Data |
| Sample document | Name from a fixed list in `app/modules/opportunities/service.py` | `syracuse_rfp`, `hyperscale_rfp`, `syracuse_addendum_1` | Code. The API serves these names only, never a path. |

Opportunity and requirement IDs are text. Their numbers are zero-padded, so text order equals number order up to 9999.

### 3.6 Timestamps

- All timestamps are UTC, written by `utcnow()` (`app/core/db.py`) and returned in ISO 8601 form.
- Two forms appear:
  - a value just written and returned in the same response carries the offset `+00:00`, for example `"created_at":"2026-10-13T07:56:04.433748+00:00"` from `POST /api/opportunities`;
  - a value read back from the database carries no offset, because SQLite stores date-times as text without a zone, for example `"created_at":"2026-10-13T05:50:59.097134"` from `GET /api/opportunities/OPP-0001`.
- Both are UTC. A client must treat a value without an offset as UTC. (JavaScript's `Date` reads such a string as local time.)
- `generated_at` in the hand-off payload is made at request time and always carries `+00:00`.

### 3.7 Validation Errors (422)

FastAPI checks every request against its declared parameters and body model before the endpoint runs. A failure gives status 422 with a list of problems. Real examples:

```text
POST /api/opportunities   {}
422 {"detail":[{"type":"missing","loc":["body","title"],"msg":"Field required","input":{}}]}

POST /api/matches/0/decide   {"action":"accept"}
422 {"detail":[{"type":"greater_than_equal","loc":["path","match_id"],
     "msg":"Input should be greater than or equal to 1","input":"0","ctx":{"ge":1}}]}

POST /api/assignments/1/validate   {"ok":false}
422 {"detail":[{"type":"value_error","loc":["body"],
     "msg":"Value error, Say why the answer is returned (note).","input":{"ok":false},"ctx":{"error":{}}}]}

GET /api/knowledge?status=bogus
422 {"detail":[{"type":"literal_error","loc":["query","status"],
     "msg":"Input should be 'queued', 'approved' or 'rejected'","input":"bogus",
     "ctx":{"expected":"'queued', 'approved' or 'rejected'"}}]}

GET /api/opportunities/OPP-0001/rfp-search          (no q)
422 {"detail":[{"type":"missing","loc":["query","q"],"msg":"Field required","input":null}]}
```

Each problem has `type`, `loc` (where: `body`, `query` or `path`, then the field), `msg` (the human text) and `input`; some have `ctx`.

Every constraint declared at the API boundary:

| Request model or parameter | Field | Constraint |
|---|---|---|
| `OpportunityIn` (`POST /api/opportunities`) | `title` | required text |
| `OpportunityIn` | `customer`, `customer_type` | text, default `""` |
| `ReviewIn` (requirements) | `action` | one of `approve`, `reject`, `edit`; `text`, `category` text or null; `reason` default `""` |
| `SplitIn` | `parts` | list of at least 2 `Part` (`quote` required, `text` default `""`); `reason` default `""` |
| `MergeIn` | `req_ids` | list of at least 2; `text` required; `reason` default `""` |
| `AddIn` | `quote` | required; `text` default `""`; `category` default `technical`; `page` integer or null |
| `LinesIn` | `page`, `line_start`, `line_end` | required integers; `text` default `""`; `category` default `technical` |
| `DecideIn` (matching) | `action` | one of `accept`, `reject` |
| `ChangeIn` / `UnitIn` (matching) | `units`; `offering_type` | `units` required list (may be empty); each `product_id` required text, `offering_type` one of `CTO`, `SEMI_CUSTOM`, `ETO` |
| `ParticipationIn` | `units` | required list of text; `rationale` default `""` |
| `GoNoGoIn` | `outcome` | one of `go`, `no_go`; `rationale` default `""`; `criteria` default `[]` |
| `CriterionIn` | `id`; `status` | `id` required; `status` one of `met`, `not_met`, `unknown`; `note` default `""` |
| `RespondIn` | `compliance` | one of `met`, `partial`, `not_met`, `exception`; `product_ref`, `response` default `""` |
| `ValidateIn` | `ok`, `note` | `ok` required boolean; `note` default `""` and must not be blank when `ok` is false |
| `SendIn` (knowledge) | `kind`; `ref`; `note` | `kind` one of `requirement`, `response`, `decision`; `ref` 1 to 40 characters; `note` at most 2000 characters, default `""` |
| `ReviewIn` (knowledge) | `approve`; `note`; `response` | `approve` required boolean; `note` at most 2000, default `""`; `response` at most 8000 or null |
| `DecideIn` (changes) | `kind`; `target`; `text` | `kind` one of `added`, `modified`, `removed`, `unchanged`, `not_a_requirement`; `target` at most 20 characters or null; `text` at most 2000 or null |
| `SampleIn` | `name` | required text |
| Query on `GET /api/catalog` | `q` | text, default `""` |
| Query on `GET /api/catalog/search` | `q`; `k` | `q` required; `k` integer 1 to 50, default 5 |
| Query on `GET .../rfp-search` | `q`; `k` | `q` required; `k` integer, default 8, silently limited to 1..25 |
| Query on `GET /api/knowledge` | `status` | one of `queued`, `approved`, `rejected`, or absent |
| Path `match_id`, `assignment_id` | | integer 1 to 2147483647 |
| Path `set_id`, `item_id` | | integer |
| Path `page_no` | | integer by route pattern: a non-integer such as `pages/abc` matches no route and gives the plain 404 `{"detail":"Not Found"}` |

Other checks are made by the services and give a text `detail` (section 3.8). Column sizes in the database (for example 200 characters for a title) are not enforced by SQLite and are not checked by the API.

### 3.8 Error Mapping

Services raise three kinds of error: "not found" (`LookupError`), "wrong person" (`PermissionError`) and "not allowed now, or bad value" (`ValueError`). Each controller turns them into HTTP status codes. The mapping is not the same in every module:

| Module (controller) | Not found | Wrong person | Not allowed now or bad value | Particular rules |
|---|---|---|---|---|
| opportunities | 404 | not used | 422 on create; 409 on uploads and samples | `GET /api/opportunities/{opp_id}` gives 404 "<opp> not found" (no full stop); `POST .../documents/from-sample` gives 404 "Opportunity <opp> not found." |
| ingestion | 404 | not used | not used | `POST /api/documents/{doc_id}/ingest` reports an unreadable or unsupported file as 200 with an `error` field |
| requirements | 404 | not used | 409 | |
| catalog | none | none | none | only FastAPI's 422 for `q` and `k` |
| matching | 404 (`decide`, manual change) | not used | 422 (manual change) | `POST .../match` has no error mapping: an unknown opportunity gives 200 with zero counts |
| decisions | 404 | not used | 422 for participation; 409 for go/no-go | unknown criteria give 422 "Unknown criteria: [...]." before the opportunity is checked |
| workpackages | 404 | 403 | 409 | an unknown unit on `GET /api/inbox/{bu}` gives 404 "Unit <bu> not found." |
| consolidation | 404 | not used | not used | |
| knowledge | 404 | 403 | 409 | `GET /api/opportunities/{opp_id}/knowledge` does not check the opportunity: an unknown one gives 200 `{}` |
| changes | 404 | 403 | 409 | |
| trace | 404 | not used | not used | |

Real examples:

```text
GET  /api/opportunities/OPP-9999                  404 {"detail":"OPP-9999 not found"}
GET  /api/opportunities/OPP-9999/requirements     404 {"detail":"Opportunity OPP-9999 not found."}
GET  /api/documents/OPP-0001-893403680eda/pages/500
                                                  404 {"detail":"Page 500 not found; the document has 101 pages."}
POST /api/changes/999/apply                       404 {"detail":"Change set 999 not found."}
POST /api/knowledge/KB-0001/review   (X-Actor: Crown Product Manager)
                                                  403 {"detail":"Only the knowledge curator (in the PoC, the Bid Manager) approves knowledge."}
POST /api/changes/1/apply            (X-Actor: Crown Product Manager)
                                                  403 {"detail":"Only the Bid Manager applies a change set."}
POST /api/changes/1/apply            (Bid Manager; the set is already applied)
                                                  409 {"detail":"Change set 1 is applied; only a set in review can be changed."}
POST /api/opportunities/OPP-0005/baselines        409 {"detail":"Upload the main RFP and wait until it has been read."}
POST /api/opportunities/OPP-0005/dispatch         409 {"detail":"Freeze the requirements before dispatch (review page)."}
GET  /api/opportunities/OPP-0001/handoff/BID      409 {"detail":"The bid desk answers its items itself; it has no downstream system to hand off to."}
POST /api/opportunities/OPP-0005/documents/from-sample  {"name":"syracuse_addendum_1"}
                                                  409 {"detail":"Sample 'syracuse_addendum_1' is a change document, not an RFP."}
POST /api/opportunities/OPP-9999/go-no-go  {"outcome":"go","criteria":[{"id":"nope","status":"met"}]}
                                                  422 {"detail":"Unknown criteria: ['nope']."}
```

The order of checks matters when a call breaks two rules. For example, `POST /api/changes/{set_id}/apply` checks that the set exists (404), then the person (403), then the state (409). Section 18 lists every message.

An error the code does not expect (for example a failed network call to the model service when `LLM_PROVIDER=azure`, or a database constraint that is not caught) gives status 500 with the plain-text body `Internal Server Error`.

### 3.9 Error Body Shape and How the Web App Shows It

- Every handled error has the JSON body `{"detail": <value>}`. The value is a text message for errors raised by the services and controllers, and a list of problems for request validation (section 3.7).
- The web client (`web/lib/api.ts`) turns a failed response into one line of text:
  - a text `detail` is shown as it is;
  - a list `detail` is shown as its `msg` values joined by `"; "`;
  - a body that is not JSON is shown as `Request failed (<status>): <first 200 characters of the body>`.
- The screens show that line in a toast or an inline alert. A leading `Error:` or status code is removed, and an empty message falls back to "Something went wrong. Please try again.".

### 3.10 When a Frozen Model Answer Is Missing

The model gateway (`app/core/llm.py`) is the only place where a language model is called. It first looks for a frozen answer, keyed by the task name, the model name, the system prompt, the prompt and the schema. If none exists and the provider is not `azure`, it raises an error with the text "No cached answer for <task>/<key>; set LLM_PROVIDER=azure to generate it.". With `LLM_PROVIDER=azure`, a refusal raises "Model refused: <reason>" and a cut-off answer raises "Answer truncated at max_tokens; send a smaller chunk.". Each module handles this error in its own way, and none of them guesses an answer:

| Endpoint | Model task | What the caller sees when no answer is available |
|---|---|---|
| `POST /api/opportunities/{opp_id}/requirements/extract` | `read_requirements`, `group_requirements` | 200. The pages that could not be read are listed in `problems`, in the form `"pages 12-15: No cached answer for read_requirements/<key>; set LLM_PROVIDER=azure to generate it."`; a page that could not be grouped gives `"page 7: not grouped (<message>)"`. The other pages are proposed as usual. The RFP step shows "<n> line items proposed, but some pages were not read:" with the list. |
| `POST /api/opportunities/{opp_id}/match` | `match_requirement` | 200. Each requirement of an unanswered page batch falls back to the best catalog search hit (method `retrieval_only`) or to the bid manager. The response counts them under `retrieval_only`. |
| `POST /api/changes/{set_id}/apply` (follow-up re-match) | `match_requirement` | As for `POST .../match`: the fallback applies and the apply succeeds. |
| `POST /api/opportunities/{opp_id}/changes` and `.../changes/from-sample` | `read_changes`, `classify_change` | 409 "No frozen answers exist for <file name> in this offline demo; connect the model service to read new documents.". No change set is created. The uploaded document stays stored (role `change`) and read. |
| `GET /api/opportunities/{opp_id}/response-outline` and `.../response-outline.md` | `draft_outline` | 200. The chapter or summary shows the validated answers without a draft: `"drafted": false` and the note "Draft not refreshed: the model service is not connected in this demo, so the validated answers are shown as they are.". The Markdown file shows "_Not drafted: <note>_". |

Search does not need the model in offline mode. Without embeddings, the search indexes fall back to keyword (TF-IDF) search and report the mode `keywords` (sections 6 and 9).

### 3.11 Idempotency and Repeated Calls

An operation is idempotent when calling it twice has the same effect as calling it once.

| Operation | What a repeated call does |
|---|---|
| `POST .../documents` (the same file again) | The file is recognised by its SHA-256 hash within the opportunity. Nothing new is stored and no audit event is written. The response is the existing document with `"existing": true` (the role sent the second time is ignored). If that document's reading never finished (status `uploaded`), reading starts again. |
| `POST .../documents/from-sample` (the same sample again) | Same as above: `"existing": true`. |
| `POST /api/documents/{doc_id}/ingest` | Reads the file again and rewrites its layout; the result is the same for the same file and pipeline version. |
| `POST .../requirements/extract` | Allowed again only until review has started. A re-run deletes the agents' unreviewed drafts (audit `discarded`) and proposes new line items with new IDs; IDs are never reused. People's own additions stay. After the first review action: 409 "Review has started (<n> review actions); re-reading would lose that work. Add what is missing with 'Add a requirement' instead." |
| `POST /api/requirements/{req_id}/review` | The same action twice changes nothing the second time and records no second audit event. The response is the current row. |
| `POST .../baselines` | Once only. Again: 409 "Requirements are frozen in baseline <n>; later changes go through the changes module." |
| `POST .../match` | Repeatable. Proposals are refreshed; accepted, manual and rejected matches are kept and counted as `kept`. |
| `POST /api/matches/{match_id}/decide` | Repeatable; each call sets the status and records an audit event. |
| `POST .../requirements/{req_id}/match` | Each call adds a new manual match; the latest one counts. |
| `POST .../participation`, `POST .../go-no-go` | Not idempotent: each call adds a decision record with its evidence. The latest one counts. |
| `POST .../dispatch` | Repeatable. It creates only missing assignments (`{"created": 0}` when nothing is missing), withdraws work that no longer fits and reopens withdrawn work that fits again. |
| `POST /api/assignments/{id}/respond` | Only from `assigned` or `returned`; a second submit gives 409 "This item is submitted; only assigned or returned items can be answered." |
| `POST /api/assignments/{id}/validate` | Only from `submitted`; a second call gives 409 "This item is validated; only submitted answers can be validated or returned." (or "is returned"). |
| `POST /api/knowledge` | The same source cannot be queued twice: 409 "Already queued as KB-0001." (or "Already approved as …"). After a rejection it may be sent again. |
| `POST /api/knowledge/{kb_id}/review` | Once: 409 "<kb_id> is already <status>." |
| `POST .../changes` | One change set in review per opportunity. The same file again after it was applied: 409 "<file> was already applied (change set <n>, baseline <m>)." |
| `POST /api/changes/{set_id}/apply`, `/discard` | Protected against double clicks and two tabs: only the first call changes the set. A second gets 409 "Change set <n> was applied or discarded meanwhile; refresh the page." (if both ran at once) or "Change set <n> is applied; only a set in review can be changed." |
| `POST /api/opportunities` | Not idempotent: each call creates a new opportunity. |

### 3.12 Long-Running Synchronous Calls and Time-Outs

These calls do their whole work before they answer:

| Operation | Work inside the request | Model calls | Parallel model calls |
|---|---|---|---|
| `POST .../requirements/extract` | Reader agent over every body page of the main RFP (contents pages and headers and footers left out), duplicate marking, grouping agent per page | `read_requirements`: one call per chunk of consecutive pages (up to 4 pages while their body lines total at most 60; a longer page goes alone); `group_requirements`: one call per page with at least 3 line items | 4 |
| `POST .../match` | Catalog search for every approved requirement not yet decided, then the matching agent | `match_requirement`: one call per batch of up to 15 product requirements from the same page; requirements of other categories go to the bid manager by rule, without a call | 4 |
| `POST .../changes`, `.../changes/from-sample` | Store; read the PDF into a layout if not read yet; change agent lists the statements; candidates ranked; change agent classifies them | `read_changes` per chunk of pages (same packing as the reader); `classify_change` per batch of up to 12 statements | 4 |
| `POST /api/changes/{set_id}/apply` | New baseline, answers returned, re-match of added and modified requirements, dispatch | `match_requirement` for the re-match | 4 |
| `GET .../response-outline`, `.../response-outline.md` | Coverage, then one draft per chapter that has validated answers, one executive summary, and search references | `draft_outline` per chapter and once for the summary, on every request | 1 (one after another) |
| `POST /api/documents/{doc_id}/ingest` | Parse the PDF (text layer, OCR when Tesseract is installed, ruled tables, headers and footers, contents pages) and rebuild the RFP search index | none | none |

Offline, with frozen answers, these calls take seconds. With a live model, the screens warn "Reader agent running… (about a minute for a 100-page RFP)". The time limits on the way are:

| Limit | Value | Where |
|---|---|---|
| Web proxy wait | 30 minutes | `web/next.config.ts`, `experimental.proxyTimeout` |
| Idle keep-alive of the API | 75 seconds | `start.cmd`, `--timeout-keep-alive 75` |
| Model answer size | `max_tokens` 16000, temperature 0 | `app/core/llm.py` |
| Database lock wait | 30 seconds | `app/core/db.py`, connection `timeout` 30 and `PRAGMA busy_timeout=30000` |
| Request time-out in the API | none | |
| Browser `fetch` time-out | none | `web/lib/api.ts` |

Closing the browser page does not stop the work on the server. Proposed (not built): a job table with progress polling (`GET /api/jobs/{id}`) for the long agent runs (`SUGGESTIONS.md`, sections 2 and 4.5).

### 3.13 Concurrency

- One database session per request (`get_db` in `app/core/db.py`). Each service commits its own work.
- SQLite runs in WAL mode: readers never block a writer and a writer never blocks readers. A writer waits up to 30 seconds for the lock instead of failing with "database is locked" (for example during a bulk approve, which the Requirements screen sends as many parallel calls).
- Races the code handles:
  - two new opportunities at once: the second takes the next number (up to 20 tries);
  - two dispatches of one opportunity: a unique rule on (`req_id`, `bu`) stops the second with 409 "Dispatch is already running for this opportunity; refresh and try again.";
  - two change documents uploaded at once: the second gets 409 "<file> (change set <n>) is still in review: apply or discard it first.";
  - two applies or discards of one change set: only the first goes through (section 3.11).
- Not protected: two knowledge items sent at the very same moment can collide on the next `KB-` number and fail with a 500 (`SUGGESTIONS.md`, section 4.6). Proposed (not built): a sequence table for all identifiers.
- The search indexes and the catalog data live in the API process memory. Running several API processes is not supported (`SUGGESTIONS.md`, section 4.7).

### 3.14 Ordering of Results

| Response | Order |
|---|---|
| Requirements (`GET .../requirements`), traceability rows, coverage rows, compliance matrix, response outline | Document order: the main RFP first, then change documents in the order they were received; within a document by page, then first line; a group before its own sub-requirements; requirements not found in the source last; ties by requirement ID |
| Documents of an opportunity | Order received |
| Opportunities (`GET /api/portfolio`) | Newest first (by ID, descending) |
| A unit's inbox (`GET /api/inbox/{bu}`) | By opportunity ID, then requirement ID |
| Knowledge items (`GET /api/knowledge`) | Newest first |
| Change sets (`GET .../changes`) | Newest first; the items of each set in document order (`n` from 1) |
| Requirement history | Events in the order they happened; versions numbered from 1 (the original wording) |
| Search results (`rfp-search`, `catalog?q=`, `catalog/search`) | Best score first; equal scores in index order; results with a score of 0 are left out |
| People (`GET /api/people`) | `Bid Manager` first, then for each active unit, in data-file order, its product manager and its design engineer |
| Catalog units, products, items | Data-file order |

### 3.15 Status Codes Used

| Code | Meaning in Layer 0 |
|---|---|
| 200 | Success. Every operation answers 200 on success, including creations (no 201) and the agent runs. |
| 403 | The acting person may not do this (section 3.1). |
| 404 | The opportunity, document, page, requirement, match, assignment, change set, item, unit or knowledge item does not exist. Also "The main RFP has not been read yet." for RFP search, and "No work for <unit> in <opp>." for a hand-off. |
| 409 | The call is not allowed in the current state (for example before a freeze, after a freeze, a set not in review), or a value is not acceptable (requirements, work packages, knowledge, changes, uploads). |
| 422 | The request does not match the declared shape (section 3.7), or a value is rejected on create opportunity, participation, go/no-go criteria or a manual match. |
| 500 | An unexpected error (section 3.8). |

### 3.16 Caching and Freshness

- The web client asks with `cache: "no-store"`, so the browser never reuses an old answer. A screen fetches its data when it opens, and again whenever its browser tab comes back into view.
- The API sends no caching headers. `GET /tour-session` sends `Cache-Control: no-store`.
- Inside the API process:
  - the business-unit, product, catalog-item and rule files in `data/knowledge_base/` are read once and kept until the API restarts;
  - the long-term search index is rebuilt on its next use after the curator approves a knowledge item;
  - the RFP search indexes are kept for up to 8 documents; they are rebuilt whenever a document is read.
- Files written by reads:
  - `GET /api/documents/{doc_id}/pages/{page_no}.png` renders a page the first time and keeps it as `STORE/pages/<sha256>/<page>.png`;
  - with `LLM_PROVIDER=azure`, a model call without a frozen answer stores the new answer in `data/llm_cache/<task>/`, and new embeddings are stored in `data/vector_cache/`. This also happens on `GET .../response-outline` and on searches. In offline mode nothing is written.

## 4. Endpoint Index

### 4.1 How to Read the Index

The index in section 4.2 lists every endpoint the system exposes: the 51 operations under `/api` (all Implemented), the Next.js route handler `GET /tour-session`, and the three FastAPI built-ins. Rows follow the order of sections 5 to 16. Within a section they follow the order of the routes in the controller.

| Column | Meaning |
|---|---|
| # | Running number, 1 to 55 |
| Method, Path | The HTTP method and the path; `{...}` marks a path parameter. `{opp}` stands for `{opp_id}` where the row would otherwise be too long. |
| Module | The module (OpenAPI tag) that owns the endpoint |
| Purpose | What the endpoint does, in one line |
| Mutates | "yes" when the call writes database rows or stored files (cache files do not count; see section 3.16) |
| Model task | The agent task the call sends to the model gateway (`complete_json` in `app/core/llm.py`), or "no". Embedding calls are listed in section 4.3. |
| Audit actions | The `action` values written to the append-only audit log, with the `entity` in brackets. "none" means the call writes no audit event. |
| Called by | The screen and the control that make the call. Screen names are those of the top bar and the opportunity step bar: Opportunities, New opportunity, RFP, Requirements, Traceability, Bid decision, Final response, Response outline, Changes, My work, Product catalog, Knowledge base. "Walkthrough" is the guided tour. |
| Section | Where the endpoint is described in full |

### 4.2 The Index

| # | Method | Path | Module | Purpose | Mutates | Model task | Audit actions | Called by | Section |
|---|---|---|---|---|---|---|---|---|---|
| 1 | POST | `/api/opportunities` | opportunities | Create an opportunity with the next free `OPP-` number, status `new` | yes | no | `created` (opportunity) | New opportunity: "Create" | 5 |
| 2 | GET | `/api/opportunities/{opp_id}` | opportunities | One opportunity and its documents (file path removed) | no | no | none | RFP: page load and "Refresh status"; opportunity header and step bar on every opportunity screen (`OppSteps`); Requirements: line picker (`LinePicker`); Walkthrough | 5 |
| 3 | POST | `/api/opportunities/{opp_id}/documents` | opportunities | Upload a document (multipart `file`, `role`); answers at once and reads a PDF in the background; flags a re-upload as `existing` | yes | no | `uploaded` (document), for a new file only | RFP: "Upload and read" | 5 |
| 4 | GET | `/api/samples` | opportunities | List the bundled sample documents: name, file name, kind (`rfp` or `change`), pages, description | no | no | none | not called by the UI (named in the walkthrough text) | 5 |
| 5 | POST | `/api/opportunities/{opp_id}/documents/from-sample` | opportunities | Attach a bundled sample RFP as the main document, exactly like an upload | yes | no | `uploaded` (document), for a new file only | Walkthrough, intake chapter: "Use example: syracuse_rfp" | 5 |
| 6 | POST | `/api/documents/{doc_id}/ingest` | ingestion | Read a stored document into the layout model now (synchronous) and rebuild its RFP search index | yes (document status and page count; layout file) | no | none | not called by the UI | 6 |
| 7 | GET | `/api/documents/{doc_id}/pages/{page_no}` | ingestion | One page of the layout model: size, reading method, lines with numbers and boxes, tables, header and footer marks | no | no | none | Requirements: line picker (`LinePicker`), when a page is shown | 6 |
| 8 | GET | `/api/documents/{doc_id}/pages/{page_no}.png` | ingestion | One page as a PNG image (110 dpi) | no (keeps a cached image file) | no | none | Traceability: pane 1 page image; Changes: change document viewer (`ChangeDocument`); Requirements: line picker | 6 |
| 9 | GET | `/api/opportunities/{opp_id}/rfp-search` | ingestion | Search the opportunity's main RFP (`q`, `k`): best passages with page and line range, and the search mode | no | no | none | RFP: "Search this RFP", "Search" | 6 |
| 10 | GET | `/api/opportunities/{opp_id}/requirements` | requirements | Every requirement in its latest version (inactive items and sub-requirements included) and the latest baseline | no | no | none | Requirements: page load and after every action; Walkthrough, knowledge chapter | 7 |
| 11 | POST | `/api/opportunities/{opp_id}/requirements/extract` | requirements | Run the reader agent and the grouping agent on the main RFP; marks duplicates; drafts only | yes | `read_requirements`, `group_requirements` | `discarded`, `proposed`, `duplicate_of`, `grouped` (requirement); `status` (opportunity, to `review`) | RFP: "Run the reader agent → requirements" | 7 |
| 12 | POST | `/api/opportunities/{opp_id}/requirements` | requirements | Add a requirement the agent missed, from a pasted quote (located on the RFP) | yes | no | `proposed` (requirement) | Requirements: "Add a requirement the agent missed", "Or paste the quote", "Add" | 7 |
| 13 | POST | `/api/opportunities/{opp_id}/requirements/from-lines` | requirements | Add a requirement from lines selected on an RFP page (quote = those lines, headers and footers left out) | yes | no | `proposed` (requirement) | Requirements: line picker, "Add requirement" | 7 |
| 14 | POST | `/api/opportunities/{opp_id}/requirements/merge` | requirements | Merge two or more line items of the same page into one new line item | yes | no | `merged` (new requirement), `merged_into` (each original) | Requirements: selection bar, "Merge into one" | 7 |
| 15 | POST | `/api/requirements/{req_id}/review` | requirements | Approve, reject or edit one line item or group (a group's decision covers its sub-requirements) | yes | no | `approve`, `reject` or `edit` (requirement); none when nothing changed | Requirements: row "Approve", "Reject", "Edit"; selection bar "Approve", "Reject" (one call per selected item, in parallel) | 7 |
| 16 | POST | `/api/requirements/{req_id}/ungroup` | requirements | Release a group's sub-requirements as stand-alone requirements | yes | no | `ungrouped` (requirement) | Requirements: "Ungroup" | 7 |
| 17 | GET | `/api/requirements/{req_id}/history` | requirements | Every version and every event of one requirement, rebuilt from the audit log | no | no | none | Requirements: "History"; Walkthrough, requirements chapter | 7 |
| 18 | POST | `/api/requirements/{req_id}/split` | requirements | Split one line item into two or more, each anchored again | yes | no | `proposed` (each part), `split` (original) | Requirements: "Split" | 7 |
| 19 | POST | `/api/opportunities/{opp_id}/baselines` | requirements | Freeze the approved requirements as baseline 1 | yes | no | `frozen` (baseline); `status` (opportunity, to `frozen`) | Requirements: "Freeze baseline" | 7 |
| 20 | GET | `/api/opportunities/{opp_id}/changes` | changes | The current baseline, the drastic-change threshold and every change set with its items, newest first | no | no | none | Changes: page load and after every action; Walkthrough, changes chapter | 8 |
| 21 | POST | `/api/opportunities/{opp_id}/changes` | changes | Upload a change PDF; read it and classify each statement against the baseline; creates a change set in review | yes | `read_changes`, `classify_change` | `uploaded` (document, new file only); `read` (change) | Changes: "Read the change document" | 8 |
| 22 | POST | `/api/opportunities/{opp_id}/changes/from-sample` | changes | The same with a bundled sample change document | yes | `read_changes`, `classify_change` | `uploaded` (document, new file only); `read` (change) | Walkthrough, changes chapter: "Use example: Addendum No. 1 (Syracuse)" | 8 |
| 23 | POST | `/api/changes/{set_id}/items/{item_id}` | changes | Confirm or override one statement's classification (kind, target, new wording) | yes | no | `confirmed` or `overridden` (change) | Changes: item decision form, "Confirm" (`ChangeDecision`) | 8 |
| 24 | POST | `/api/changes/{set_id}/confirm-all` | changes | Confirm every still-proposed item as proposed | yes | no | `confirmed_all` (change) | Changes: "Confirm all proposals" (`ChangeSetCard`) | 8 |
| 25 | POST | `/api/changes/{set_id}/apply` | changes | Apply a fully confirmed set (Bid Manager only): next baseline, changed answers returned to units, re-match, re-dispatch | yes | `match_requirement` (re-match of added and modified requirements) | `proposed`, `approve`, `revised`, `removed` (requirement); `frozen` (baseline); `applied` (change); then `returned`, `assigned`, `reopened`, `withdrawn` (assignment), `proposed` (match), `status` (opportunity); `follow_up_failed` (change) if a follow-up step fails | Changes: "Apply to requirements" (`ChangeSetCard`) | 8 |
| 26 | POST | `/api/changes/{set_id}/discard` | changes | Drop a change set in review (Bid Manager only); the baseline stays | yes | no | `discarded` (change) | Changes: "Discard", after the confirmation dialog "Discard this change set?" | 8 |
| 27 | GET | `/api/catalog` | catalog | Business units (pending ones included), products, catalog items; with `q`, the 10 best search results | no | no | none | Product catalog: page load and search; Traceability: match "Change" editor (`MatchActions`), loaded once | 9 |
| 28 | GET | `/api/catalog/search` | catalog | Search the long-term index (products, past responses, catalog items, approved knowledge) with `q` and `k` | no | no | none | not called by the UI | 9 |
| 29 | GET | `/api/people` | catalog | The names offered in "Acting as", each with its unit (`null` for the Bid Manager) | no | no | none | Top bar: "Acting as" picker (`ActorPicker`); My work: redirect from `/inbox` to the person's unit | 9 |
| 30 | POST | `/api/opportunities/{opp_id}/match` | matching | Propose units, products and offering types for every approved requirement not yet decided by a person | yes | `match_requirement` | `proposed` (match) | Traceability: "Match products" | 10 |
| 31 | POST | `/api/matches/{match_id}/decide` | matching | Accept or reject a proposed match | yes | no | `accept` or `reject` (match) | Traceability pane 3: "Accept", "Reject" (`MatchActions`) | 10 |
| 32 | POST | `/api/opportunities/{opp_id}/requirements/{req_id}/match` | matching | Set a person's own match: units with offering types; an empty list sends the requirement to the bid manager | yes | no | `manual` (match) | Traceability pane 3: "Change" editor, "Save" (`MatchActions`) | 10 |
| 33 | GET | `/api/opportunities/{opp_id}/decisions` | decisions | Evidence pack, go/no-go summary (after the freeze), active units, latest participation and go/no-go | no | no | none | Bid decision: page load and after every action | 11 |
| 34 | POST | `/api/opportunities/{opp_id}/participation` | decisions | Record which active units take part, with a rationale | yes | no | `decided` (participation) | Bid decision: "Record participation" | 11 |
| 35 | POST | `/api/opportunities/{opp_id}/go-no-go` | decisions | Record go or no-go, with the person's judgement per criterion and a rationale | yes | no | `decided` (go_no_go); `status` (opportunity, to `go` or `no_go`, or back to where a stopped bid was) | Bid decision: "Go", "No-go" | 11 |
| 36 | POST | `/api/opportunities/{opp_id}/dispatch` | workpackages | Create one assignment per matched participating unit (else the bid desk) for every frozen requirement; withdraw and reopen as needed | yes | no | `assigned`, `reopened`, `withdrawn` (assignment); `status` (opportunity, to `dispatched`) | Bid decision: "Dispatch work packages to units" | 12 |
| 37 | GET | `/api/opportunities/{opp_id}/handoff/{bu}` | workpackages | Download a unit's hand-off payload as `<opp>-<bu>-handoff.json` (CPQ seed, basis of design, specialist queue) | no | no | none | My work: "Hand-off for this unit's systems", one link per opportunity | 12 |
| 38 | GET | `/api/inbox/{bu}` | workpackages | A unit's active work across all opportunities, each item with its requirement, plus the unit and the compliance values | no | no | none | My work (`/inbox/{bu}`): page load and after every action; Walkthrough, inbox and knowledge chapters | 12 |
| 39 | POST | `/api/assignments/{assignment_id}/respond` | workpackages | A unit's product manager or design engineer submits the answer (compliance, product, response) | yes | no | `responded` (assignment) | My work: "Submit"; "Submit all answered rows" (one call per row, one after another) | 12 |
| 40 | POST | `/api/assignments/{assignment_id}/validate` | workpackages | The Bid Manager validates a submitted answer or returns it with a note | yes | no | `validated` or `returned` (assignment) | My work: "Validate"; "Return", then "Return with note" | 12 |
| 41 | POST | `/api/knowledge` | knowledge | Send a requirement, a validated answer or a decision rationale to the curator's queue | yes | no | `sent` (knowledge) | "Send to knowledge base", "Send" (`SendToKnowledge`) on Traceability, Bid decision and Response outline; Walkthrough, knowledge chapter | 13 |
| 42 | GET | `/api/knowledge` | knowledge | All knowledge items (optional `status` filter), the curator's name, the learned count and the index mode | no | no | none | Knowledge base: page load and after every action (tabs filter in the browser); Walkthrough | 13 |
| 43 | GET | `/api/opportunities/{opp_id}/knowledge` | knowledge | What was already sent from this opportunity: `"<kind>:<ref>"` mapped to its status | no | no | none | Traceability, Bid decision, Response outline (state of the "Send to knowledge base" buttons) | 13 |
| 44 | POST | `/api/knowledge/{kb_id}/review` | knowledge | The curator approves an item (optionally tidying its answer) or rejects it with a note; approved items join the long-term index | yes (approval also writes `STORE/knowledge_learned.json`) | no | `approved` or `rejected` (knowledge) | Knowledge base: "Approve into the knowledge base", "Reject" | 13 |
| 45 | GET | `/api/opportunities/{opp_id}/consolidation` | consolidation | Coverage: every requirement with its match, assignments and state (`answered`, `pending`, `not_assigned`); totals and the blocking list | no | no | none | Final response: page load | 14 |
| 46 | GET | `/api/opportunities/{opp_id}/compliance-matrix.csv` | consolidation | Download the compliance matrix as CSV | no | no | none | Final response: "CSV" | 14 |
| 47 | GET | `/api/opportunities/{opp_id}/compliance-matrix.xlsx` | consolidation | Download the compliance matrix as an Excel workbook | no | no | none | Final response: "Download compliance matrix (Excel)" | 14 |
| 48 | GET | `/api/opportunities/{opp_id}/response-outline` | consolidation | Draft response chapters and executive summary from validated answers, with sources, exceptions, open items and search references | no | `draft_outline` | none | Response outline: page load ("Drafting the outline…") | 14 |
| 49 | GET | `/api/opportunities/{opp_id}/response-outline.md` | consolidation | Download the same outline as Markdown | no | `draft_outline` | none | Response outline: "Download outline (Markdown)" | 14 |
| 50 | GET | `/api/portfolio` | trace | Every opportunity, newest first, with its current requirement count and per-unit progress | no | no | none | Opportunities (`/portfolio`): page load; My work: unit switcher and waiting counts | 15 |
| 51 | GET | `/api/opportunities/{opp_id}/trace` | trace | Data of the three linked panes: per requirement its match, product, unit, BOM, assignments, sub-requirements and highlight boxes; documents, pages, progress | no | no | none | Traceability: page load and after every action | 15 |
| 52 | GET | `/tour-session` | Next.js route handler (`web/app/tour-session/route.ts`) | Walkthrough session identity: `{"id": "<random UUID>"}`, one per web-server run, `Cache-Control: no-store` | no | no | none | Walkthrough engine (`TourProvider`), once per page load | 16 |
| 53 | GET | `/docs` | FastAPI built-in | Swagger UI: interactive list of all operations (back-end address only) | no | no | none | not called by the UI | 16 |
| 54 | GET | `/redoc` | FastAPI built-in | ReDoc reference page of the same specification (back-end address only) | no | no | none | not called by the UI | 16 |
| 55 | GET | `/openapi.json` | FastAPI built-in | Machine-readable OpenAPI 3.1.0 specification (back-end address only) | no | no | none | not called by the UI (used by `/docs` and `/redoc`) | 16 |

### 4.3 Notes to the Index

Embedding calls. With `LLM_PROVIDER=azure`, the search indexes ask the embedding model (`embed()` in `app/core/llm.py`) for vectors that are not frozen in `data/vector_cache/`, and for each search query. This concerns:

| Endpoint | What is embedded |
|---|---|
| `GET .../rfp-search` (9) | the question |
| `GET /api/catalog?q=` (27), `GET /api/catalog/search` (28) | the question; the long-term index on its first use after a start or after a knowledge approval |
| `POST .../match` (30) and `POST /api/changes/{set_id}/apply` (25) | the quote of every requirement being matched (sent together, in requests of up to 256 texts) |
| `GET .../response-outline` (48) and `.md` (49) | one query per chapter, against the RFP index and the long-term index |
| `POST .../documents` (3, background), `.../documents/from-sample` (5, background), `POST /api/documents/{doc_id}/ingest` (6), `POST .../changes` (21, 22) | the RFP passages when the RFP index is rebuilt, unless frozen vectors exist |

In offline mode no embedding call is made: the indexes use keyword (TF-IDF) search and report the mode `keywords`.

Background work. Rows 3 and 5 answer before the PDF is read. The background task then sets the document status to `ingesting`, writes `STORE/layouts/<doc_id>.json`, sets `ingested` (with the page count) or `failed`, and rebuilds the RFP search index. It writes no audit event.

Which calls write which audit actions. Every audit event holds the time, the opportunity, the actor, the action, the entity, the entity ID and a data object (for example before and after, a reason, a note). The table groups the actions that the endpoints write by entity:

| Entity | Actions | Written by (index rows) |
|---|---|---|
| opportunity | `created`, `status` | 1; `status` by 11, 19, 25, 35, 36 |
| document | `uploaded` | 3, 5, 21, 22 |
| requirement | `proposed`, `discarded`, `duplicate_of`, `grouped`, `ungrouped`, `split`, `merged`, `merged_into`, `approve`, `reject`, `edit`, `revised`, `removed` | 11, 12, 13, 14, 15, 16, 18, 25 |
| baseline | `frozen` | 19, 25 |
| match | `proposed`, `accept`, `reject`, `manual` | 30, 31, 32, 25 |
| participation, go_no_go | `decided` | 34, 35 |
| assignment | `assigned`, `reopened`, `withdrawn`, `responded`, `validated`, `returned` | 36, 39, 40, 25 |
| knowledge | `sent`, `approved`, `rejected` | 41, 44 |
| change | `read`, `confirmed`, `overridden`, `confirmed_all`, `applied`, `discarded`, `follow_up_failed` | 21, 22, 23, 24, 25, 26 |

The audit log is append-only: database triggers reject any update or delete of `audit_event` ("audit_event is append-only"). No endpoint reads the log directly except `GET /api/requirements/{req_id}/history` (17), which rebuilds one requirement's history from it.

Endpoints the screens do not call. `POST /api/documents/{doc_id}/ingest`, `GET /api/samples`, `GET /api/catalog/search`, `GET /docs`, `GET /redoc` and `GET /openapi.json` are for scripts, integrations and developers. The `status` filter of `GET /api/knowledge` is not used by the screen, which loads every item and filters by tab in the browser. Two operations are called only by the walkthrough: `POST .../documents/from-sample` and `POST .../changes/from-sample`.

### 4.4 Cross-Checks

| Check | Result |
|---|---|
| Operations under `/api` in the live OpenAPI specification | 51 (23 GET, 28 POST), all in the index (rows 1 to 51) |
| Route decorators in the 11 controller files | 51, the same set |
| Further endpoints | 4 (rows 52 to 55) |
| Operations that change stored data | 28 (every POST) |
| Operations that call the model gateway for a model answer | 7: rows 11, 21, 22, 25, 30, 48, 49 |
| Operations that check the acting person's name | 5: rows 25, 26, 39, 40, 44 |
| Operations that return a file download | 4 (rows 37, 46, 47, 49), plus the page image (row 8) |
| Operations not called by any screen | 6 (rows 4, 6, 28, 53, 54, 55) |

## 5. Opportunities and Documents Endpoints

This section and sections 6 to 8 describe the intake half of the API: creating an opportunity, attaching and reading its documents, building the requirement list and freezing it, and processing change documents against the frozen list. Every operation described here is Implemented; the few points that could not be verified are marked "Needs confirmation" where they occur.

**How the examples were produced.** GET examples come from the isolated demo copy of the API on 13 Oct 2026 (OPP-0001 to OPP-0004, see section 1). POST examples were produced on the same copy by acting only on two opportunities created for this document:

- **Example run A** (it received the ID `OPP-0007`): the Syracuse sample RFP attached, the reader agent run, every requirement approved, baseline 1 frozen, then the illustrative Addendum No. 1 read three times (change set 2 discarded, change set 3 applied as baseline 2).
- **Example run B** (ID `OPP-0010`): the one-page hyperscale sample uploaded as a file, requirements added by hand, reviewed, split, merged and frozen, then the offline refusals.

Timestamps in responses are UTC. A row returned straight after it is created carries a `+00:00` offset (the value still in memory); the same value read back later from the database has no offset (for example `2026-10-13T08:04:44.385826+00:00` on create, `2026-10-13T08:04:44.385826` on the next GET). Example curl commands target the normal API port (`http://127.0.0.1:8000`) and send the acting person in the `X-Actor` header, URL-encoded (section 3 explains the header and its default).

The module behind this section is `opportunities` (`app/modules/opportunities/controller.py`, `service.py`, `models.py`; OpenAPI tag `opportunities`). Its controller maps service errors as follows: on create, a `ValueError` becomes **422**; on document attach, `LookupError` becomes **404** and `ValueError` becomes **409**. Request-validation failures (a missing or wrongly typed field) are FastAPI's standard **422** with a `detail` list (section 18).

| # | Method and path | Purpose | Writes |
|---|---|---|---|
| 5.1 | POST `/api/opportunities` | Create an opportunity | `opportunity`, `audit_event` |
| 5.2 | GET `/api/opportunities/{opp_id}` | Read an opportunity and its documents | nothing |
| 5.3 | POST `/api/opportunities/{opp_id}/documents` | Attach a file (multipart); reading starts in the background | file store, `document`, `audit_event`; then layout file and index |
| 5.4 | GET `/api/samples` | List the bundled sample documents | nothing |
| 5.5 | POST `/api/opportunities/{opp_id}/documents/from-sample` | Attach a bundled sample RFP as the main RFP | same as 5.3 |

There is no "list opportunities" endpoint: the opportunity list on the portfolio page comes from `GET /api/portfolio` (see 04-api-view.md, section 15).

### 5.1 POST /api/opportunities

**Purpose.** Creates one opportunity: the workspace for one RFP (request for proposal) and everything that follows from it. The server allocates the next free ID (`OPP-0001`, `OPP-0002`, ...), records who created it and starts it in status `new`.

**Path parameters.** None.

**Query parameters.** None.

**Request body** (`application/json`, schema `OpportunityIn`):

| Field | Type | Required | Constraints | Default | Meaning |
|---|---|---|---|---|---|
| `title` | string | yes | Must contain at least one non-blank character. Stored trimmed. Column `VARCHAR(200)` (SQLite does not enforce the length). | none | Name of the opportunity, shown everywhere in the web app. |
| `customer` | string | no | Free text, stored as sent. Column `VARCHAR(120)`. | `""` | Customer name. |
| `customer_type` | string | no | Free text, not validated by the API. The web form offers `utility`, `hyperscaler`, `neocloud`, `colocation`, `silicon provider`, `public sector` or empty. Column `VARCHAR(40)`. | `""` | Customer segment. |

**Response** (200): the new `opportunity` row.

| Field | Type | Meaning |
|---|---|---|
| `id` | string | `OPP-` plus a four-digit number: the highest number in use plus one. |
| `title` | string | The trimmed title. |
| `customer` | string | As sent. |
| `customer_type` | string | As sent. |
| `status` | string | Always `new` (lifecycle in section 22). |
| `created_by` | string | The acting person (`X-Actor` header, default `Bid Manager`). |
| `created_at` | string (date-time, UTC) | Creation time. |

Real example (example run A):

```json
{"id": "OPP-0007",
 "title": "API example A: Syracuse switchgear (documentation run)",
 "customer": "Syracuse Regional Airport Authority",
 "customer_type": "public sector",
 "status": "new",
 "created_by": "Bid Manager",
 "created_at": "2026-10-13T08:04:44.385826+00:00"}
```

**Status codes and exact error messages.**

| Code | When | Body |
|---|---|---|
| 200 | Created. | The row above. |
| 422 | The title is empty or only spaces (for example `{"title": "   "}`). | `{"detail": "A title is required."}` |
| 422 | The `title` field is missing. | `{"detail": [{"type": "missing", "loc": ["body", "title"], "msg": "Field required", "input": {"customer": "x"}}]}` |
| 422 | Twenty attempts in a row collided with IDs taken at the same moment by other requests. | `{"detail": "Could not allocate an opportunity ID; try again."}` |

**Side effects.** Inserts one `opportunity` row. Writes one audit event: action `created`, entity `opportunity`, entity ID and opportunity ID = the new ID, data `{"title": <title as sent, untrimmed>}`. ID allocation reads every existing ID, takes the maximum number plus one and commits; if two requests take the same number at once, the database's primary-key check rejects the second, which rolls back and tries the next number (up to 20 attempts).

**Model calls.** None.

**Preconditions.** None. **Postconditions.** The opportunity exists in status `new` with no documents. Its status only moves forward through the workflow from here (section 22).

**Called by.** New opportunity page (`/opportunities/new`, see 03-ui-view.md): the **Create** button. The page trims the title itself and shows "A title is required." without calling the API when it is blank; after a successful call it opens `/opportunities/{id}` (the RFP step). See `images/02-new-opportunity.png`.

**Example curl.**

```bash
curl -s -X POST http://127.0.0.1:8000/api/opportunities \
  -H 'Content-Type: application/json' -H 'X-Actor: Bid%20Manager' \
  -d '{"title": "Switchgear procurement (RFP 2023-20)", "customer": "Syracuse Regional Airport Authority", "customer_type": "public sector"}'
```

### 5.2 GET /api/opportunities/{opp_id}

**Purpose.** Returns one opportunity and the documents attached to it, in the order they were received. The web app polls it to follow a document while it is being read.

**Path parameters.**

| Name | Type | Meaning |
|---|---|---|
| `opp_id` | string | Opportunity ID, for example `OPP-0001`. |

**Query parameters.** None. **Request body.** None.

**Response** (200):

| Field | Type | Meaning |
|---|---|---|
| `opportunity` | object | The `opportunity` row: `id`, `title`, `customer`, `customer_type`, `status`, `created_by`, `created_at` (as in 5.1). |
| `documents` | array of objects | Every document of the opportunity, oldest first (by `received_at`). Each is a `document` row without its server file path (see the table below). |

Document object (also returned by 5.3 and 5.5):

| Field | Type | Meaning |
|---|---|---|
| `id` | string | `<opportunity ID>-<first 12 hex characters of the file's SHA-256>`, for example `OPP-0001-893403680eda`. The same file attached to two opportunities is two documents. |
| `sha256` | string | SHA-256 of the file's bytes (64 hex characters). The bytes are stored once under this hash and never modified. |
| `opportunity_id` | string | Owning opportunity. |
| `filename` | string | Name of the file as uploaded. |
| `role` | string | `main` (the RFP; at most one per opportunity), or `addendum`, `qa`, `change`, `other` (free text; the API does not check the value). The changes flow always stores `change`. |
| `status` | string | `uploaded`, `ingesting`, `ingested`, `failed` or `unsupported` (section 22). |
| `page_count` | integer | Number of pages; `0` until the document has been read. |
| `received_at` | string (date-time, UTC) | When it was attached. |

The server's file path (column `path`) is deliberately left out of every API response.

Real example (OPP-0001 after the addendum was applied; 2 documents, complete):

```json
{"opportunity": {"id": "OPP-0001", "title": "Switchgear procurement (RFP 2023-20)",
  "customer": "Syracuse Regional Airport Authority", "customer_type": "public sector",
  "status": "dispatched", "created_by": "Bid Manager", "created_at": "2026-10-13T05:50:59.097134"},
 "documents": [
  {"id": "OPP-0001-893403680eda",
   "sha256": "893403680eda487a7fcf4968231102e10345324aefd0503d2b28b97d3347a76e",
   "opportunity_id": "OPP-0001", "filename": "RFP-2023-20-Switchgear-Procurement-Final.pdf",
   "role": "main", "status": "ingested", "page_count": 101, "received_at": "2026-10-13T05:50:59.127038"},
  {"id": "OPP-0001-180eb141aec2",
   "sha256": "180eb141aec27c6c16fe8cef672366dea3db26b86c0837ea6265caaf9a9f4801",
   "opportunity_id": "OPP-0001", "filename": "rfp_syracuse_addendum_1.pdf",
   "role": "change", "status": "ingested", "page_count": 1, "received_at": "2026-10-13T06:40:09.579061"}]}
```

The blank demo opportunity returns `{"opportunity": {"id": "OPP-0003", "title": "Blank opportunity (empty states)", ..., "status": "new", ...}, "documents": []}`.

**Status codes and exact error messages.**

| Code | When | Body |
|---|---|---|
| 200 | Found. | As above. |
| 404 | No such opportunity. | `{"detail": "OPP-9999 not found"}`. This is the only unknown-opportunity message without the word "Opportunity" and without a full stop; every other endpoint says `"Opportunity OPP-9999 not found."` (section 18). |

**Side effects.** None. **Model calls.** None.

**Called by.**
- RFP documents page (`/opportunities/{id}`): on load, on the **Refresh status** button, after an upload, and whenever the browser tab regains focus. See `images/03-rfp-step-OPP-0001.png`.
- Opportunity header and step bar (on every opportunity page): on every route change, every 5 seconds, and on the browser event `opp-status-changed` (fired after a freeze, an apply or a discard), to keep the status badge and the steps current.
- "Add a requirement the agent missed" line picker on the Requirements page: to find the main RFP's document ID and page count.
- The walkthrough's checks (intake chapter).

**Example curl.**

```bash
curl -s http://127.0.0.1:8000/api/opportunities/OPP-0001 -H 'X-Actor: Bid%20Manager'
```

### 5.3 POST /api/opportunities/{opp_id}/documents

**Purpose.** Attaches one received file to an opportunity. The server stores the bytes, records the document and answers at once; reading the PDF into the page layout model (section 6.1) then runs in the background, and the web page follows its progress by polling 5.2.

**Path parameters.**

| Name | Type | Meaning |
|---|---|---|
| `opp_id` | string | Opportunity ID. |

**Query parameters.** None.

**Request body** (`multipart/form-data`, schema `Body_upload_api_opportunities__opp_id__documents_post`):

| Field | Type | Required | Constraints | Default | Meaning |
|---|---|---|---|---|---|
| `file` | file (binary) | yes | Any file type. No size limit is enforced: the whole file is read into memory. Only a name ending in `.pdf` (any case) is read; any other file is recorded with status `unsupported`. | none | The received document. |
| `role` | string (form field) | no | Free text, not validated. Only one document per opportunity may have the role `main`. | `main` | `main` for the RFP; `addendum`, `qa`, `change` or `other` for later documents. |

**Behaviour, step by step** (`opportunities.service.add_document` and `controller._attach`):

1. The opportunity must exist.
2. The SHA-256 of the bytes is computed. If this opportunity already has a document with the same hash, that existing document is returned unchanged (its earlier role and status are kept; the `role` sent now is ignored) and nothing is stored or recorded.
3. Otherwise, if `role` is `main` and the opportunity already has a main document, the request is refused (409).
4. The bytes are written to `<store>/files/<sha256>.pdf` (or `<store>/files/<sha256>` without extension for a non-PDF name). `<store>` is `data/store` unless the `STORE_DIR` environment variable says otherwise.
5. A `document` row is created: ID `<opp>-<sha256[:12]>`, status `uploaded` for a `.pdf` name, `unsupported` otherwise. Audit event `uploaded` is written and committed.
6. If the returned document's status is `uploaded` (a new PDF, or the same PDF whose reading never started), the read is scheduled as a background task that runs after the response: `ingestion.ingest` in its own database session (section 6.1).
7. The response is the document plus `existing`: `true` when the document already existed before this call.

**Response** (200): the document object of 5.2 plus one field.

| Field | Type | Meaning |
|---|---|---|
| (document fields) | | As in 5.2; at this moment `status` is usually `uploaded` and `page_count` `0`. |
| `existing` | boolean | `true` when the same bytes were already attached to this opportunity, so nothing new was added. |

Real example (example run B, the hyperscale PDF uploaded as a file with role `main`):

```json
{"id": "OPP-0010-c7749ef1bfc9",
 "sha256": "c7749ef1bfc98fabdd250e4f70de53841327a00646d8525352dfaccaa70702ae",
 "opportunity_id": "OPP-0010", "filename": "rfp_hyperscale_campus.pdf", "role": "main",
 "status": "uploaded", "page_count": 0, "received_at": "2026-10-13T08:26:13.924268+00:00",
 "existing": false}
```

Three seconds later, GET 5.2 showed the same document with `"status": "ingested", "page_count": 1`.

A non-PDF file is recorded but never read (example run B, `note.txt` with role `other`):

```json
{"id": "OPP-0010-5891b5b522d5", "sha256": "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03",
 "opportunity_id": "OPP-0010", "filename": "note.txt", "role": "other", "status": "unsupported",
 "page_count": 0, "received_at": "2026-10-13T08:26:16.937048+00:00", "existing": false}
```

**Status codes and exact error messages.**

| Code | When | Body |
|---|---|---|
| 200 | Stored (or already present). | As above. |
| 404 | No such opportunity. | `{"detail": "Opportunity OPP-9999 not found."}` |
| 409 | `role` is `main` and the opportunity already has a main RFP (a different file). | `{"detail": "This opportunity already has a main RFP; upload this file as an addendum, Q&A or other."}` |
| 422 | No `file` part in the form. | `{"detail": [{"type": "missing", "loc": ["body", "file"], "msg": "Field required", "input": null}]}` |

**Side effects.**
- File written: `<store>/files/<sha256>[.pdf]` (shared by every opportunity that receives the same bytes).
- Table `document`: one row inserted.
- Audit: action `uploaded`, entity `document`, entity ID = document ID, data `{"sha256", "filename", "role"}`.
- Background (PDF only): the read of section 6.1, which moves the document to `ingesting`, then `ingested` (with `page_count`) or `failed`, writes `<store>/layouts/<document ID>.json` and rebuilds the RFP search index. The background read writes no audit event.
- The opportunity's status does not change (the lifecycle value `reading` exists but no code sets it; section 22).

**Model calls.** None. Reading a PDF is deterministic (PyMuPDF text, Tesseract OCR when installed, pdfplumber tables). Building the search index requests embeddings only when the Azure provider is configured and no frozen vectors exist for the text; offline it never calls a model.

**Preconditions.** The opportunity exists; at most one main RFP. **Postconditions.** The document exists; for a PDF, it reaches `ingested` (or `failed`) shortly after the response. For a 101-page RFP with a frozen layout (the Syracuse sample) this takes a few seconds; a new PDF is parsed live.

**Called by.** RFP documents page (`/opportunities/{id}`): the form with **RFP file (PDF)**, **Role** (select `main`, `addendum`, `qa`, `change`, `other`; default `main`, or `addendum` once requirement review has started, when the form moves into the collapsed **Add another document** panel) and the **Upload and read** button. While the request runs the page shows "Uploading and reading the RFP… (about a minute for a 100-page RFP)"; on return it reloads the list and shows the toast "Document received and read.", although the reading itself may still be running in the background (use **Refresh status**). See `images/19-rfp-step-OPP-0003-empty.png` and `images/03-rfp-step-OPP-0001.png`.

**Example curl.**

```bash
curl -s -X POST http://127.0.0.1:8000/api/opportunities/OPP-0003/documents \
  -H 'X-Actor: Bid%20Manager' \
  -F 'file=@RFP-2023-20-Switchgear-Procurement-Final.pdf' -F 'role=main'
```

### 5.4 GET /api/samples

**Purpose.** Lists the sample documents bundled with the application, which the walkthrough (and anyone without a file at hand) can attach by name instead of uploading a file. The list is a fixed whitelist in `app/modules/opportunities/service.py` (`SAMPLES`); the API exposes names only, never file paths.

**Path parameters.** None. **Query parameters.** None. **Request body.** None.

**Response** (200):

| Field | Type | Meaning |
|---|---|---|
| `samples` | array | One object per sample. |
| `samples[].name` | string | The name to send to 5.5 or 8.3. |
| `samples[].filename` | string | The file name the document gets. |
| `samples[].kind` | string | `rfp` (attachable as the main RFP, 5.5) or `change` (readable as a change document, 8.3). |
| `samples[].pages` | integer | Page count. |
| `samples[].description` | string | What the sample is and how it behaves offline. |

Real example (complete):

```json
{"samples": [
  {"name": "syracuse_rfp", "filename": "RFP-2023-20-Switchgear-Procurement-Final.pdf", "kind": "rfp", "pages": 101,
   "description": "Syracuse Regional Airport Authority, RFP 2023-20 Switchgear Procurement: the public RFP behind the demo opportunity. Read offline from frozen answers: about 810 line items grouped into about 350 requirements, each anchored to its page and lines."},
  {"name": "hyperscale_rfp", "filename": "rfp_hyperscale_campus.pdf", "kind": "rfp", "pages": 1,
   "description": "Fictional one-page RFP for a 48 MW hyperscale AI training campus (800 VDC distribution, liquid cooling): the multi-unit case. It has no frozen reader answers, so reading it needs the model connection."},
  {"name": "syracuse_addendum_1", "filename": "rfp_syracuse_addendum_1.pdf", "kind": "change", "pages": 1,
   "description": "Illustrative Addendum No. 1 to the Syracuse RFP, written for the PoC: it revises, removes and adds requirements against the frozen baseline. Its frozen change-agent answers match the demo opportunity's requirement set only."}]}
```

The files live under `data/RFP/` (`RFP-2023-20-Switchgear-Procurement-Final.pdf`, `samples/rfp_hyperscale_campus.pdf`, `samples/rfp_syracuse_addendum_1.pdf`). Only the Syracuse RFP has a frozen layout in `data/layout_cache/`; the other two are parsed live when attached (fast: one page each).

**Status codes.** 200 only. **Side effects.** None. **Model calls.** None.

**Called by.** No screen calls this endpoint. The walkthrough attaches samples by their fixed names (`syracuse_rfp`, `syracuse_addendum_1`) and only mentions this endpoint in its explanatory text.

**Example curl.**

```bash
curl -s http://127.0.0.1:8000/api/samples
```

### 5.5 POST /api/opportunities/{opp_id}/documents/from-sample

**Purpose.** Attaches a bundled sample RFP (5.4, kind `rfp`) as the opportunity's main RFP. It goes through exactly the same storing, background reading, response shape and status transitions as a file upload (5.3) with role `main`.

**Path parameters.**

| Name | Type | Meaning |
|---|---|---|
| `opp_id` | string | Opportunity ID. |

**Query parameters.** None.

**Request body** (`application/json`, schema `SampleIn`):

| Field | Type | Required | Constraints | Default | Meaning |
|---|---|---|---|---|---|
| `name` | string | yes | A sample name from 5.4 whose kind is `rfp`: `syracuse_rfp` or `hyperscale_rfp`. | none | Which sample to attach. |

**Response** (200): as 5.3 (document object plus `existing`). The role is always `main`.

Real example (example run A):

```json
{"id": "OPP-0007-893403680eda",
 "sha256": "893403680eda487a7fcf4968231102e10345324aefd0503d2b28b97d3347a76e",
 "opportunity_id": "OPP-0007", "filename": "RFP-2023-20-Switchgear-Procurement-Final.pdf", "role": "main",
 "status": "uploaded", "page_count": 0, "received_at": "2026-10-13T08:05:38.674389+00:00", "existing": false}
```

The background read had finished before the next GET (frozen layout): `"status": "ingested", "page_count": 101`. Sending the same name again returns the same document with `"existing": true` and its current status (`ingested`, 101 pages).

**Status codes and exact error messages** (checked in this order).

| Code | When | Body |
|---|---|---|
| 200 | Attached (or already attached). | As above. |
| 404 | No such opportunity. | `{"detail": "Opportunity OPP-9999 not found."}` |
| 409 | Unknown sample name. | `{"detail": "Unknown sample 'nope'; see /api/samples."}` |
| 409 | The sample is a change document. | `{"detail": "Sample 'syracuse_addendum_1' is a change document, not an RFP."}` |
| 409 | The opportunity already has a different main RFP (for example `hyperscale_rfp` after `syracuse_rfp`). | `{"detail": "This opportunity already has a main RFP; upload this file as an addendum, Q&A or other."}` |
| 422 | `name` missing. | FastAPI validation list (`"loc": ["body", "name"]`). |

**Side effects.** As 5.3: file under `<store>/files/`, `document` row, audit `uploaded` (role `main`), background read.

**Model calls.** None. Note for offline use: the Syracuse RFP can be taken all the way through the reader agent offline (frozen layout and frozen reader answers); the hyperscale sample is read into a layout offline, but the reader agent finds no frozen answers for it (see 7.2).

**Preconditions.** The opportunity exists and has no other main RFP. **Postconditions.** As 5.3.

**Called by.** Only the walkthrough: in the intake chapter, the step that attaches the Syracuse RFP has a **Use example** button that sends `{"name": "syracuse_rfp"}` for the walkthrough's opportunity and then presses **Refresh status**. The RFP page itself only offers the file input (5.3).

**Example curl.**

```bash
curl -s -X POST http://127.0.0.1:8000/api/opportunities/OPP-0003/documents/from-sample \
  -H 'Content-Type: application/json' -H 'X-Actor: Bid%20Manager' -d '{"name": "syracuse_rfp"}'
```

## 6. Ingestion Endpoints

Module `ingestion` (`app/modules/ingestion/controller.py`, `service.py`). Status: Implemented. This module has no table; it writes the layout file and page images to the store. Error mapping: `LookupError` → 404 only.

The page layout model (returned by 6.2) is described in 02-technical-architecture.md, section 8, and its fields in section 17 of this document.

### 6.1 POST /api/documents/{doc_id}/ingest

Reads (or re-reads) a stored PDF into the page layout model and rebuilds the opportunity's RFP search index. No model call (deterministic). Synchronous; can take minutes for a large scanned PDF.

Path parameter: `doc_id` (for example `OPP-0001-893403680eda`). No body.

Response 200 on success:

```json
{"document":"OPP-0001-893403680eda","page_count":101,"index":"embeddings","passages":566,"unreviewed_pages":[]}
```

Response 200 with an error object when the file cannot be read (the document becomes `failed`), or for a non-PDF (status stays `unsupported`):

```json
{"document":"OPP-0005-0a1b2c3d4e5f","error":"unsupported file type; recorded but not read"}
```

Errors: 404 `Document 'X' not found.`

Behaviour: status `ingesting`; uses the frozen layout `data/layout_cache/<sha256>.json` when one exists (identical line numbers on every machine), else parses the PDF (native text with PyMuPDF; whole-page OCR with Tesseract when a page has no usable text layer and Tesseract is installed; ruled tables with pdfplumber; header/footer and contents-page marking); writes `<STORE_DIR>/layouts/<doc_id>.json`; status `ingested` with `page_count`; rebuilds the passage index. Pages with no readable text are listed in `unreviewed_pages`, never skipped silently. No audit event.

Called by: no screen (upload runs the same function in the background). Useful for operators and tests.

```bash
curl -s -X POST http://127.0.0.1:8000/api/documents/OPP-0001-893403680eda/ingest -H 'X-Actor: Bid%20Manager'
```

### 6.2 GET /api/documents/{doc_id}/pages/{page_no}

Returns one page of the layout model: its lines with numbers and boxes, its tables and its review flags.

Path parameters: `doc_id`; `page_no` (integer, 1-based).

Response 200 (trimmed; page 1 of the Syracuse RFP has 23 lines):

```json
{"page":1,"width":612.0,"height":792.0,"method":"native","unreviewed":false,"toc":false,
 "lines":[{"n":1,"text":"REQUEST FOR PROPOSALS","bbox":[205.44,237.52,413.78,265.12],"furniture":false},
          "... 21 more ...",
          {"n":23,"text":"All Rights Reserved","bbox":[...],"furniture":true}],
 "tables":[]}
```

Other observed pages: page 54 has `"toc": true` (contents page); page 83 has `"method": "ocr"`, `"reason": "no text layer"` and OCR lines carrying `conf` and `low_confidence`; page 72 has one table `p72-t1` (3 columns, 33 rows) and its lines carry `"cell": ["p72-t1", row, column]`.

Errors: 404 `Document 'NOPE-123' not found.`; 404 `Document X has not been read yet.`; 404 `Page 0 not found; the document has 101 pages.` (also for a page above the count); 404 `{"detail":"Not Found"}` when `page_no` is not an integer (the route does not match).

Called by: the line picker on the Requirements screen ("Add a requirement the agent missed"), on open and on every page change.

### 6.3 GET /api/documents/{doc_id}/pages/{page_no}.png

Returns the page as a PNG image, rendered at 110 dpi (a 612 × 792 pt page is 935 × 1210 px). The first request renders and caches it in `<STORE_DIR>/pages/<sha256>/<n>.png`; later requests read the file.

Response 200: `image/png` bytes. Errors: as 6.2.

Called by: Traceability pane 1 (the RFP page with highlights), the line picker, and the "Change document" panel of a change set on the Changes screen.

### 6.4 GET /api/opportunities/{opp_id}/rfp-search

Searches the opportunity's main RFP (its short-term retrieval index: passages of up to 500 characters, headers and footers left out) and returns the best passages with page and line numbers.

Query parameters:

| Name | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `q` | string | yes | - | The question in plain words; an empty string returns no passages |
| `k` | integer | no | 8 | Number of passages; clamped to 1..25 |

Response 200:

```json
{"mode":"embeddings","passages":[
 {"page":55,"line_start":47,"line_end":57,"text":"positions with protective relay and controls, ... 2. Switchgear shall be Arc-resistant Type 2B. The switchgear shall meet or exceed the most conservative interpretation of standard IEEE C37.20.7. ...","score":0.202},
 {"page":53,"line_start":1,"line_end":29,"text":"Syracuse Hancock International Airport Landside Switchgear Relocation SPECIFICATION FOR METAL CLAD SWITCHGEAR ...","score":0.158}]}
```

`mode` is `embeddings` when the passages have vectors (frozen or computed), else `keywords`. In offline mode with frozen passage vectors the query itself cannot be embedded, so scoring falls back to keyword (TF-IDF) similarity while `mode` still says `embeddings` (Known limit). Only passages with a score above 0 are returned.

Errors: 404 `Opportunity OPP-9999 not found.`; 404 `The main RFP has not been read yet.`; 422 when `q` is missing.

Called by: RFP step, card **Search this RFP** (button **Search**); the walkthrough example "what short-circuit rating is required?".

## 7. Requirements Endpoints

Module `requirements` (`app/modules/requirements/controller.py`, `service.py`, `agent.py`, `grouping.py`, `anchoring.py`). Status: Implemented. Error mapping: `LookupError` → 404, `ValueError` → 409; Pydantic violations → 422.

**Freeze rule.** Once the opportunity has a frozen baseline, every write in this section returns 409 `Requirements are frozen in baseline N; later changes go through the changes module.` The only write after a freeze is applying a change set (section 8.6).

Every requirement endpoint returns requirement rows: `id`, `req_id`, `version`, `opportunity_id`, `document_id`, `text`, `quote`, `category`, `section`, `page`, `line_start`, `line_end`, `bboxes`, `provenance`, `status`, `derived_from`, `kind`, `parent_id`, `baseline`, `created_by`, `created_at`, plus the computed `source` (see section 17).

### 7.1 GET /api/opportunities/{opp_id}/requirements

Every requirement of the opportunity (the latest version of each), including inactive ones (rejected, duplicate, split, merged, removed) and sub-requirements, in document order, plus the latest baseline.

Response 200: `{"requirements": [<requirement>...], "baseline": <baseline row> | null}`.

Order: anchored items before unanchored ones, the main RFP before change documents (in upload order), then page, first line, a group before its own sub-requirements, then ID.

```json
{"requirements":[
  {"id":1,"req_id":"REQ-0001-0001","version":1,"opportunity_id":"OPP-0001","document_id":"OPP-0001-893403680eda","text":"Proposals must be submitted by September 15, 2023, 4pm.","quote":"Submission Deadline: September 15, 2023 by 4pm","category":"schedule","section":"Submission Deadline","page":1,"line_start":5,"line_end":5,"bboxes":[[72.0,343.34,361.25,364.09]],"provenance":"EXTRACTED","status":"approved","derived_from":[],"kind":"item","parent_id":null,"baseline":1,"created_by":"reader agent (Bid Manager)","created_at":"2026-10-13T05:50:59.462539","source":"p. 1, line 5"},
  "... 975 more rows before the addendum (814 line items, 162 groups) ..."],
 "baseline":{"id":3,"opportunity_id":"OPP-0001","number":2,"count":349,"frozen_by":"Bid Manager","frozen_at":"2026-10-13T06:56:17.297436"}}
```

Row variants in the demo: a group `REQ-0001-0815` (`kind` `group`, `text` "Submission requirements for proposals", `quote` = member quotes joined by " … ", `source` "p. 1, lines 14-20"); its sub-requirements `REQ-0001-0004` to `0006` with `parent_id` `REQ-0001-0815`; a duplicate `REQ-0001-0072` (`status` `duplicate`, `derived_from` `["REQ-0001-0043"]`, `baseline` null); an unanchored item `REQ-0001-0141` (`page` null, `bboxes` [], `source` "not found in source").

Errors: 404 `Opportunity OPP-9999 not found.`

Called by: Requirements screen on load and after every action; walkthrough checks.

### 7.2 POST /api/opportunities/{opp_id}/requirements/extract

Runs the reader agent on the main RFP, marks duplicates and runs the grouping agent: the first proposal of requirement line items, groups and sub-requirements (all `proposed`). Synchronous and long-running when the answers are not frozen (hundreds of model calls on a 100-page RFP); the web proxy allows 30 minutes.

No body. Response 200:

```json
{"proposed":814,"duplicates":21,"groups":162,"requirements":348,"problems":[]}
```

`problems` lists pages the agents could not read (for example `pages 1-1: No cached answer for read_requirements/<key>; set LLM_PROVIDER=azure to generate it.` in offline mode on an RFP with no frozen answers) and pages not grouped. They are reported, never guessed.

Errors: 404 opportunity; 409 frozen; 409 `Upload the main RFP and wait until it has been read.`; 409 `Review has started (N review actions); re-reading would lose that work. Add what is missing with 'Add a requirement' instead.`

Side effects: earlier agent drafts (`proposed` or `duplicate` rows created by an agent) are discarded (audit `discarded`); people's own additions stay; new rows with `created_by` `reader agent (<actor>)` or `grouping agent (<actor>)`; audit `proposed`, `duplicate_of`, `grouped`; opportunity status → `review`.

Model calls: `read_requirements` (pages packed up to 4 pages / 60 lines per call, 4 calls in parallel; 83 calls for the Syracuse RFP) and `group_requirements` (one call per page with 3 or more items).

Called by: RFP step, button **Run the reader agent → requirements** (shown when the main RFP is read and the status is `new` or `review`). On success without problems the screen opens Requirements.

### 7.3 POST /api/opportunities/{opp_id}/requirements

Adds a requirement the agent missed, from a quote pasted from the RFP. The quote is searched in the main RFP to anchor it.

Request body (`AddIn`):

| Field | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `quote` | string | yes | - | Text copied from the RFP |
| `text` | string | no | `""` | Short restatement; default is the quote (first 200 characters) |
| `category` | string | no | `technical` | One of `technical`, `compliance`, `commercial`, `schedule`, `submission`, `legal`, `staffing` |
| `page` | integer or null | no | null | Hint: the page searched first (any page may match) |

Response 200: the new requirement (`status` `proposed`; `provenance` `EXTRACTED` when the quote was found, else `UNANCHORED` with `source` "not found in source").

```json
{"id":987,"req_id":"REQ-0004-0001","version":1,"opportunity_id":"OPP-0004","document_id":"OPP-0004-c7749ef1bfc9","text":"IT capacity: approximately 48 MW critical load, Phase 1","quote":"IT capacity: approximately 48 MW critical load, Phase 1","category":"technical","section":"","page":1,"line_start":5,"line_end":5,"bboxes":[["..."]],"provenance":"EXTRACTED","status":"proposed","derived_from":[],"kind":"item","parent_id":null,"baseline":null,"created_by":"Bid Manager","created_at":"...","source":"p. 1, line 5"}
```

Errors: 404 opportunity; 409 frozen; 409 `Unknown category 'x'.`; 409 `Upload the main RFP and wait until it has been read.`; 409 `A requirement needs a quote copied from the RFP.`

Side effects: audit `proposed`. The opportunity status does not change.

Called by: Requirements screen, "Or paste the quote" form, button **Add**.

### 7.4 POST /api/opportunities/{opp_id}/requirements/from-lines

Adds a missed requirement by selecting lines on a page of the main RFP. The quote is exactly those lines (header and footer lines left out), so the source is exact.

Request body (`LinesIn`):

| Field | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `page` | integer | yes | - | Page of the main RFP |
| `line_start` | integer | yes | - | First line (1-based) |
| `line_end` | integer | yes | - | Last line; at most 40 lines in total |
| `text` | string | no | `""` | Short text; default the quote |
| `category` | string | no | `technical` | Requirement category |

Example: request `{"page":1,"line_start":11,"line_end":11,"text":"Energization within 9 months of award","category":"schedule"}` → `REQ-0004-0004`, `proposed`, `EXTRACTED`, `source` "p. 1, line 11", `quote` "- Timeline: energization required within 9 months of award".

Errors (409 unless stated): 404 opportunity; frozen (with the added sentence "A requirement missed before the freeze now comes in through the Changes page."); `Unknown category 'x'.`; `Upload the main RFP and wait until it has been read.`; `Page N not found; the RFP has M pages.`; `Page N has no readable lines (not read; it needs OCR).`; `Choose lines between 1 and N on page P, the first line before the last.`; `Select at most 40 lines; split a longer passage into several requirements.`; `Only header or footer lines are selected; select the requirement's own lines.`

Called by: the line picker, button **Add requirement**.

### 7.5 POST /api/opportunities/{opp_id}/requirements/merge

Merges two or more line items of the same page into one new requirement.

Request body (`MergeIn`): `req_ids` (array of strings, at least 2), `text` (string, required: the merged requirement's short text), `reason` (string, default `""`).

Response 200: the new merged requirement (`status` `proposed`, `derived_from` = the originals, `quote` = the original quotes joined by " … ", lines from the first to the last). The originals become `merged`.

Errors, checked in this order: 409 `Give the merged requirement a short text.`; 404 `REQ-… not found.`; 409 frozen or `REQ-… is <status>; it can no longer be changed.`; 409 `A merge needs at least two line items.`; 409 `Line items from another opportunity cannot be merged.`; 409 `Groups and sub-requirements cannot be merged; ungroup first.`; 409 `Only line items on the same page can be merged; keep cross-page items separate.`; 422 fewer than two IDs in the body.

Side effects: audit `merged` on the new ID (`merged_from`, `reason`) and `merged_into` on each original.

Called by: Requirements screen, bulk bar **Merge into one** → text → **Merge**.

### 7.6 POST /api/requirements/{req_id}/review

A person's decision on one requirement: approve, reject or edit.

Request body (`ReviewIn`):

| Field | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `action` | `approve` \| `reject` \| `edit` | yes | - | The decision |
| `text` | string or null | no | null | New short text (edit) |
| `category` | string or null | no | null | New category (edit) |
| `reason` | string | no | `""` | Recorded in the audit event |

Effects:
- `approve` / `reject` set the status. On a group, approve also approves its `proposed` sub-requirements (and its rejected ones when the group itself was rejected); reject rejects every active sub-requirement.
- Approving a `duplicate` or `rejected` item restores it as `approved`.
- `edit` changes text and/or category in place (the earlier wording stays in the audit log and in the history, 7.8).
- A review that changes nothing (the same click twice) writes no event.

Response 200: the requirement after the review.

Errors: 404 `REQ-… not found.`; 409 frozen; 409 `REQ-… is split; review its replacement instead.` (also for `merged`); 409 `Unknown category 'x'.`; 422 for an action outside the three values.

Side effects: audit `approve`, `reject` or `edit` with `before` and `after` (`status`, `text`, `category`) and `reason`.

Called by: Requirements screen, row buttons **Approve**, **Reject**, the **Edit** form (**Save**), bulk **Approve** / **Reject** (one request per selected item, sent in parallel).

### 7.7 POST /api/requirements/{req_id}/ungroup

Releases a group's sub-requirements as stand-alone requirements; the group becomes `split`. No body.

Response 200: array of the released sub-requirements (statuses unchanged, `parent_id` now null).

Errors: 404; 409 `REQ-… is not a group.`; 409 frozen or inactive.

Side effects: audit `ungrouped` (`into`). Called by: Requirements screen, row button **Ungroup** on an active group.

### 7.8 GET /api/requirements/{req_id}/history

The requirement's versions and events, rebuilt from the audit log.

Response 200:

```json
{"req_id":"REQ-0001-0001","quote":"Submission Deadline: September 15, 2023 by 4pm","source":"p. 1, line 5","derived_from":[],
 "versions":[{"n":1,"at":"2026-10-13T05:50:59.465553","by":"reader agent (Bid Manager)","label":"original","text":"Proposals must be submitted by September 15, 2023, 4pm.","category":"schedule"}],
 "events":[{"at":"...","by":"reader agent (Bid Manager)","action":"proposed","details":{"provenance":"EXTRACTED","derived_from":[],"category":"schedule"}},
           {"at":"...","by":"Bid Manager","action":"approve","details":{"reason":""}},
           {"at":"...","by":"Bid Manager","action":"frozen","details":{"count":348}}]}
```

`versions[].label` is `original`, `edited` (an edit that changed text or category) or `revised` (a change document; `reason` names it). `events[].details` leaves out the long fields (`text`, `quote`, `before`, `after`). The `frozen` events of every baseline the requirement belongs to are included.

Errors: 404 `REQ-9999-0001 not found.` Called by: Requirements screen, row toggle **History**; walkthrough.

### 7.9 POST /api/requirements/{req_id}/split

Splits one stand-alone line item into two or more parts, each anchored again in the RFP.

Request body (`SplitIn`): `parts` (array of at least 2 objects `{"quote": string (required), "text": string (default "")}`), `reason` (string, default `""`).

Response 200: array of the new parts (`status` `proposed`, `derived_from` = the original). The original becomes `split`.

Errors: 404; 409 `REQ-… is a group; use Ungroup to release its sub-requirements.`; 409 `A split needs at least two parts.` (after blank quotes are dropped); 409 frozen or inactive; 422 fewer than two parts in the body.

Side effects: audit `proposed` per part, `split` on the original (`into`, `reason`). Called by: Requirements screen, row **Split** form (one quote per line).

### 7.10 POST /api/opportunities/{opp_id}/baselines

Freezes the reviewed requirements as baseline 1. No body.

Response 200: the baseline row:

```json
{"id":1,"opportunity_id":"OPP-0001","number":1,"count":348,"frozen_by":"Bid Manager","frozen_at":"2026-10-13T05:51:48.486713"}
```

`count` is the number of top-level approved requirements (groups and stand-alone items, not sub-requirements).

Errors: 404 opportunity; 409 already frozen (`Requirements are frozen in baseline 1; ...`); 409 `Upload the main RFP and wait until it has been read.`; 409 `N line items still need approve or reject before freezing.`; 409 `Nothing is approved; a baseline needs at least one requirement.`

Side effects: `baseline = 1` on every approved top-level requirement and every approved sub-requirement of an approved group; a `baseline` row; audit `frozen` (entity `baseline`, ID `1`, `count`); opportunity status → `frozen`. From then on every write in this section returns 409.

Called by: Requirements screen, **Freeze baseline** → confirm dialog "Freeze the baseline?".

## 8. Changes Endpoints

Module `changes` (`app/modules/changes/controller.py`, `service.py`, `agent.py`). Status: Implemented. Error mapping: `LookupError` → 404, `PermissionError` → 403, `ValueError` → 409.

A change document (addendum, Q&A answers, change request) is stored with role `change`, read like the RFP and compared with the frozen baseline. The change agent proposes a classification for every statement; a person confirms each one; only the Bid Manager applies or discards the set. One set per opportunity can be in review at a time.

The change set object (`view`) and the change item object (`item_view`) are described in section 17.

### 8.1 GET /api/opportunities/{opp_id}/changes

Overview of an opportunity's change handling: the current baseline, the drastic threshold and every change set, newest first.

Response 200 (OPP-0001 after Addendum No. 1 was applied; items trimmed):

```json
{"baseline":{"number":2,"count":349},"drastic_threshold":0.25,
 "sets":[{"id":1,"opportunity_id":"OPP-0001","document_id":"OPP-0001-180eb141aec2","filename":"rfp_syracuse_addendum_1.pdf","status":"applied","created_by":"Bid Manager","created_at":"2026-10-13T06:40:10.045123","applied_by":"Bid Manager","applied_at":"...","baseline_from":1,"baseline_to":2,
   "counts":{"added":2,"modified":2,"removed":1,"unchanged":1,"not_a_requirement":2},"confirmed":8,"total":8,"share":0.009,"drastic":false,
   "pages":[{"page":1,"width":612.0,"height":792.0}],
   "result":{"baseline":2,"added":["REQ-0001-0977","REQ-0001-0978"],"modified":["REQ-0001-0039","REQ-0001-0332"],"removed":["REQ-0001-0130"],"returned":2,"dispatched":2,"note":""},
   "items":[{"id":1,"n":1,"page":1,"line_start":12,"line_end":13,"bboxes":[[72.0,270.71,459.41,285.14],[72.0,285.71,188.02,300.14]],"source":"p. 1, lines 12-13","quote":"Section 1.9, Submission Due Date, page 5: replace \"09/15/2023 by 4:00PM\" with \"09/29/2023 by 4:00PM\".","text":"Submit proposals by 09/29/2023 at 4:00 PM via email.","category":"schedule","action":"modify","proposed_kind":"modified","proposed_target":"REQ-0001-0039","rationale":"The change document specifies a new submission due date, which modifies the existing requirement in candidate A.","confidence":0.95,"kind":"modified","target":"REQ-0001-0039","status":"confirmed","decided_by":"Bid Manager","target_text":"Submit proposals by 09/15/2023 at 4:00 PM via email.","target_source":"p. 5, lines 23-24","candidates":[{"req_id":"REQ-0001-0039","text":"Submit proposals by 09/15/2023 at 4:00 PM via email.","source":"p. 5, lines 23-24"},"... 5 candidates"]},
             "... 8 items in total"]}]}
```

Before any freeze: `{"baseline":null,"drastic_threshold":0.25,"sets":[]}`.

Errors: 404 `Opportunity OPP-9999 not found.` Called by: Changes screen on load and after every action.

### 8.2 POST /api/opportunities/{opp_id}/changes

Uploads a change document; it is stored, read and classified before the response (synchronous).

Request: `multipart/form-data` with `file` (required; the file name must end in `.pdf`; a missing name becomes `change.pdf`).

Response 200: the new change set (`status` `review`, every item `proposed`).

Errors (409 unless stated): 404 opportunity; 422 no file; `Freeze the requirements first: a change document is compared with the frozen baseline.`; `<filename> (change set N) is still in review: apply or discard it first.`; `Upload the change document as a PDF.`; `This file is the main RFP of OPP-…, not a change document.`; `<filename> was already applied (change set N, baseline M).`; `<filename> could not be read: <error>`; `No frozen answers exist for <filename> in this offline demo; connect the model service to read new documents.`; `The change agent found no statements in <filename>.`

Processing order: store the file as a `change` document (storage rules of 5.3) → ingest it if needed → `read_changes` (statements: quote, text after the change, category, action add / modify / delete / clarify / info) → rank up to five candidate baseline requirements per statement by keyword similarity → `classify_change` (one call per page, up to 12 statements; `info` statements are classified `not_a_requirement` by rule without a call) → anchor every quote in the change document → create the set and its items → audit `read` (`statements`, `proposed` counts per kind).

Known limit: when reading fails after the file was stored, the document row and file remain although no change set is created.

Called by: Changes screen, **Read the change document** (the file input is disabled while a set is in review).

### 8.3 POST /api/opportunities/{opp_id}/changes/from-sample

Same as 8.2 with a bundled sample change document. Request body: `{"name":"syracuse_addendum_1"}`.

Errors: as 8.2, plus 409 `Unknown sample 'x'; see /api/samples.` and 409 `Sample 'syracuse_rfp' is an RFP, not a change document.` In offline mode the frozen answers of the sample addendum match the demo opportunity's requirement set only; on another opportunity the call returns the 409 "No frozen answers exist ..." message.

Called by: the walkthrough's one-click example "Addendum No. 1 (Syracuse)" on OPP-0001.

### 8.4 POST /api/changes/{set_id}/items/{item_id}

A person confirms or overrides one classification.

Request body (`DecideIn`):

| Field | Type | Required | Constraints | Meaning |
|---|---|---|---|---|
| `kind` | string | yes | `added`, `modified`, `removed`, `unchanged`, `not_a_requirement` | The decision |
| `target` | string or null | for modified / removed / unchanged | max 20 | The baseline requirement the statement is about; any approved baseline requirement, not only the five candidates |
| `text` | string or null | no | max 2000 | Replaces the new wording when not blank |

Response 200: the item (`status` `confirmed`, `kind`, `target`, `decided_by`).

Errors: 404 `Change set N not found.`; 404 `Item N is not in change set M.`; 409 `Change set N is applied; only a set in review can be changed.`; 409 `Name the baseline requirement this statement changes.` (or "removes" / "leaves unchanged"); 409 `REQ-… is not an approved requirement of baseline N.`; 409 `Change set N was applied or discarded meanwhile; refresh the page.`; 422 unknown kind.

Side effects: audit `confirmed` (the decision equals the agent's proposal) or `overridden` (`item`, `kind`, `target`, `before`, `after_text`). Anyone may decide; an item can be decided again while the set is in review.

Called by: Changes screen, per-row decision editor, button **Confirm**.

### 8.5 POST /api/changes/{set_id}/confirm-all

Confirms every still-proposed item as the agent proposed it. No body. Response 200: the change set. Errors: 404; 409 not in review or changed meanwhile. Audit `confirmed_all` (`items`). Called by: **Confirm all proposals**.

### 8.6 POST /api/changes/{set_id}/apply

Applies a fully confirmed change set, creating the next baseline. Bid Manager only. No body. Long-running when new or changed requirements must be matched.

Response 200: the change set with `status` `applied`, `baseline_to` and `result`:

```json
{"baseline":2,"added":["REQ-0001-0977","REQ-0001-0978"],"modified":["REQ-0001-0039","REQ-0001-0332"],"removed":["REQ-0001-0130"],"returned":2,"dispatched":2,"note":""}
```

Errors: 404; 403 `Only the Bid Manager applies a change set.`; 409 not in review; 409 `N classification(s) still need a person's confirmation (items [..]).`; 409 `Items [..] all change REQ-…: put the combined new wording in one of them and mark the others unchanged.`; 409 `This set was read against baseline N, which is no longer the latest; discard it and upload the document again.`; 409 changed meanwhile.

Effects, in one transaction: `modified` → a new version of the target anchored in the change document; `removed` → a new version with status `removed` (for a group, its sub-requirements too); `added` → a new requirement ID, approved, in the new baseline; a new `baseline` row (number + 1); audit `revised`, `removed`, `proposed` / `approve`, `frozen`, `applied`. Then follow-ups (failures are written to `result.note`, not raised): the answers of affected requirements are returned to their units with a note "Changed by <file>: …"; only added and modified requirements are matched again; work is dispatched again when work had been dispatched before and the latest go/no-go is `go`. Possible notes: `Nothing changed: the baseline stays N.`; `Not dispatched: no work was dispatched before this change; dispatch from the decisions page.`; `Not dispatched: the latest go/no-go is not 'go'. ...`; `Baseline N is applied, but the follow-up stopped (...)` (audit `follow_up_failed`).

Called by: Changes screen, **Apply to requirements** (enabled for the Bid Manager when all items are confirmed) → confirm dialog.

### 8.7 POST /api/changes/{set_id}/discard

Discards a change set in review; the baseline is unchanged and the document may be read again later. Bid Manager only. No body.

Response 200: the change set with `status` `discarded`. Errors: 404; 403 `Only the Bid Manager discards a change set.`; 409 not in review or changed meanwhile. Audit `discarded`.

Called by: Changes screen, **Discard** → confirm dialog "Discard this change set?".

## 9. Catalog Endpoints

The catalog module (`app/modules/catalog/`) serves the business units, the product families, their published models and the long-term retrieval index. It has no database table. Everything it returns is read from JSON files in `data/knowledge_base/` ("rules as data"):

| File | What the catalog endpoints take from it |
|---|---|
| `business_units.json` | 9 units: code, name, pillar, status (`active` or `pending`), focus, product manager, design engineer, source URL |
| `products.json` | 61 product families (60 belong to active units; `EPC-800V` belongs to the pending unit EPC) |
| `catalog_items.json` | 76 models or series (73 belong to active units) |
| `past_responses.json` | 8 illustrative past answers (indexed for search) |
| `<STORE_DIR>/knowledge_learned.json` | knowledge approved by the curator in this installation (indexed for search; the file exists only after the first approval) |

Each JSON file is read once per API process (`functools.lru_cache` in `app/modules/catalog/service.py`). An edit to a knowledge-base file therefore takes effect only after the API is restarted. The search index is rebuilt automatically when the curator approves a knowledge item (see 04-api-view.md, section 13).

All three endpoints are Implemented. They are read-only, write nothing, record no audit event and make no language-model call. They are tagged `catalog` in the OpenAPI document.

**How search scores hits.** The long-term index (`app/core/vectors.py`, class `Index`) holds, in this order: every product of an active unit (text = name, description and keywords), every seeded past response, every curator-approved item (marked `"learned": true`), and every catalog item of an active unit (text = name, model and specs). Scoring has two modes:

- With an embedding provider (`LLM_PROVIDER=azure`), the query is embedded and compared by cosine similarity with the document vectors (frozen in `data/vector_cache/` when the indexed text is unchanged).
- Without a provider (offline mode, as in the isolated copy), the query cannot be embedded, so scores come from a keyword (TF-IDF, unigrams and bigrams, English stop words removed) cosine similarity. The index may still report its mode as `embeddings` when frozen document vectors exist; the query scoring is keyword-based all the same.

A hit with a score of 0 or less is never returned. Scores are rounded to 3 decimals.

### 9.1 GET /api/catalog

**Purpose.** One call that returns the whole catalog: every business unit (including the pending one), every product family and every model of the active units, plus, when a query is given, the ten best hits of the long-term index.

**Path parameters.** None.

**Query parameters.**

| Name | Type | Required | Default | Constraints | Meaning |
|---|---|---|---|---|---|
| `q` | string | no | `""` | none | Search text. Empty: no search is run and `results` is `[]`. Not empty: `results` holds at most 10 hits of the long-term index. |

**Request body.** None.

**Response (200).** A JSON object:

| Field | Type | Meaning |
|---|---|---|
| `units` | array of unit objects | All 9 business units, active and pending (`units(include_pending=True)`), in file order: EP2, CROWN, ANORD, FPM, JETCOOL, CLOUD, EPC (pending), EMS, AFS. |
| `units[].code` | string | Unit code, for example `CROWN`. |
| `units[].name` | string | Display name, for example `Crown Technical Systems`. |
| `units[].pillar` | string | Group the unit belongs to, for example `Critical Power`. |
| `units[].status` | string | `active` or `pending`. Only EPC is `pending` ("not offered until closed"). |
| `units[].focus` | string | One-paragraph description of what the unit makes. |
| `units[].product_manager` | string | Role placeholder used as an actor name, for example `Crown Product Manager`. |
| `units[].design_engineer` | string | Role placeholder used as an actor name and as the owner of dispatched work, for example `Crown Design Engineer`. |
| `units[].source_url` | string | Public page the unit data was taken from. |
| `products` | array of product objects | The 60 product families of active units (`EPC-800V` is left out). |
| `products[].id` | string | Product family id, for example `CROWN-ARMV`. |
| `products[].bu` | string | Code of the unit that makes it. |
| `products[].name` | string | Display name. |
| `products[].offering_type` | string | Usual offering type: `CTO` (configure-to-order), `SEMI_CUSTOM` (configured product plus extra workshop work) or `ETO` (engineered-to-order). |
| `products[].description` | string | Description; also part of the matcher's fixed prompt. |
| `products[].keywords` | string | Retrieval keywords. |
| `products[].source_url` | string | Public page. |
| `products[].bom` | array of `{item, qty}` | Bill-of-materials lines. Illustrative placeholders for the original families; empty for newer families. |
| `items` | array of catalog-item objects | The 73 models or series of active units. |
| `items[].id` | string | `<family>/<model>`, for example `ANORD-LVSB/MDX`. |
| `items[].family` | string | The product family id it belongs to. |
| `items[].bu` | string | Unit code. |
| `items[].model` | string | Model or series name. |
| `items[].name` | string | Full name. |
| `items[].specs` | string | Specifications copied from the public page (not confirmed by the units). |
| `items[].source_url` | string | Public page. |
| `results` | array of hits | `[]` when `q` is empty; otherwise at most 10 hits, best first. Hit shapes are listed below. |

Hit shapes in `results` (and in `GET /api/catalog/search`):

| `kind` | Fields |
|---|---|
| `product` | `kind`, `id`, `bu`, `offering_type`, `text`, `score` |
| `catalog_item` | `kind`, `id`, `bu`, `family`, `offering_type` (the family's), `text`, `score` |
| `past_response` | `kind`, `id`, `bu`, `text`, `score`; a curator-approved item also has `"learned": true` |

Real example from the isolated API (`GET /api/catalog?q=switchgear`, 70,899 bytes, trimmed):

```json
{
  "units": [
    {"code": "EP2", "name": "Electrical Power Products (EP²)", "pillar": "Critical Power", "status": "active",
     "focus": "Engineered-to-order protective relay and control panels, drop-in-place integrated control enclosures ...",
     "product_manager": "EP² Product Manager", "design_engineer": "EP² Design Engineer", "source_url": "https://ep2.com/"},
    "... 9 units in total; EPC has \"status\": \"pending\""
  ],
  "products": [
    {"id": "EP2-RPP", "bu": "EP2", "name": "Relay and protection panel", "offering_type": "ETO",
     "description": "Protective relays and substation relay and protection panels to the one-line diagram: ...",
     "keywords": "protective relays controls protection and control panel relay panel ...",
     "source_url": "https://ep2.com/quality-products/relay-panels/",
     "bom": [{"item": "Protective relay, feeder (illustrative)", "qty": "per feeder"},
             {"item": "Panel enclosure and swing rack (illustrative)", "qty": "1 per panel"},
             {"item": "Test switches and terminal blocks (illustrative)", "qty": "per relay"}]},
    "... 60 products in total"
  ],
  "items": [
    {"id": "ANORD-LVSB/MDX", "family": "ANORD-LVSB", "bu": "ANORD", "model": "MDX", "name": "MDX Switchgear (IEC 61439-2)",
     "specs": "Main busbar up to 8000 A; ACB incomers 800-6300 A drawout/fixed; ...",
     "source_url": "https://anordmardix.com/mdx-switchgear/"},
    "... 73 items in total"
  ],
  "results": [
    {"kind": "product", "id": "CROWN-MCSG", "bu": "CROWN", "offering_type": "ETO",
     "text": "Non-arc metal-clad and MV enclosed switchgear. Standard MV metal-clad switchgear 4.16-38 kV ...", "score": 0.295},
    {"kind": "product", "id": "ANORD-MVSG", "bu": "ANORD", "offering_type": "SEMI_CUSTOM", "text": "...", "score": 0.2},
    {"kind": "product", "id": "CROWN-ARMV", "bu": "CROWN", "offering_type": "ETO", "text": "...", "score": 0.186},
    {"kind": "catalog_item", "id": "CROWN-ARMV/Arc-Resistant Switchgear", "bu": "CROWN", "family": "CROWN-ARMV",
     "offering_type": "ETO", "text": "Crown arc-resistant metal-clad switchgear ...", "score": 0.147},
    "... 10 hits in total (then CROWN-EHOUSE/TPSS 0.121, ANORD-POD/Power SKID 0.096, CROWN-ACC 0.094, ANORD-POD 0.093, CROWN-EHOUSE 0.09, ANORD-POD/Power Pod 0.09)"
  ]
}
```

Without `q` the same call returns 66,108 bytes with `"results": []`.

**Status codes.**

| Code | When | Body |
|---|---|---|
| 200 | Always, for any value of `q` | The object above |

There is no endpoint-specific error. A query that matches nothing returns `"results": []`.

**Side effects.** None. No table or file is written, no audit event is recorded.

**Model calls.** None. With `LLM_PROVIDER=azure` a non-empty `q` is embedded through the model gateway (`app/core/llm.embed`); offline, keyword scoring is used and nothing is called.

**Preconditions.** None. **Postconditions.** None (read-only).

**Called by.**

- Product catalog screen (`web/app/catalog/page.tsx`, route `/catalog`, see 03-ui-view.md): on page load with `q=` (empty) and again after **Search** (the search box sets `q`) or **Clear** (resets `q` to empty). The screen groups `products` under each unit and `items` under each product as "<n> model(s) / series"; the results table shows Score, Kind ("model of <family>" for a catalog item), Unit, ID and the first 160 characters of the text. See `images/14-catalog.png` and `images/36-catalog-search.png`.
- Traceability screen, pane 3, match **Change** editor (`web/components/matching/MatchActions.tsx`): the first time a person clicks **Change**, the editor calls `GET /api/catalog` (no `q`) to fill the product drop-down, and drops units whose `status` is not `active` on the client side, so the pending unit is never offered. See `images/37-trace-match-change-editor-OPP-0001.png`.

**Example.**

```bash
curl -s "http://127.0.0.1:8000/api/catalog?q=switchgear" -H 'X-Actor: Bid%20Manager'
```

### 9.2 GET /api/catalog/search

**Purpose.** Ranked search of the long-term index only, with a caller-chosen number of hits. It returns the same hits as `results` of `GET /api/catalog`, without the catalog lists. No screen calls it; it is for integrations and for trying the index in the interactive API documentation (`/docs`).

**Path parameters.** None.

**Query parameters.**

| Name | Type | Required | Default | Constraints | Meaning |
|---|---|---|---|---|---|
| `q` | string | yes | none | none | Search text. An empty or blank value returns `[]`. |
| `k` | integer | no | `5` | `1 <= k <= 50` | Maximum number of hits. |

**Request body.** None.

**Response (200).** A JSON array of hits, best first, at most `k` long. Hit shapes are those of section 9.1 (`product`, `catalog_item`, `past_response`).

Real example (`GET /api/catalog/search?q=liquid%20cooling%20120%20kW&k=3`, texts trimmed):

```json
[
  {"kind": "past_response", "id": "PAST-JETCOOL-001", "bu": "JETCOOL",
   "text": "Liquid cooling for 120 kW racks. Met. Direct-to-chip cold plates with row-level CDUs sized for 120 kW per rack.",
   "score": 0.587},
  {"kind": "product", "id": "JETCOOL-HYBRID", "bu": "JETCOOL", "offering_type": "CTO",
   "text": "Liquid-assisted air cooling (SmartPlate System). ...", "score": 0.223},
  {"kind": "product", "id": "JETCOOL-CDU", "bu": "JETCOOL", "offering_type": "SEMI_CUSTOM",
   "text": "Coolant distribution unit. ...", "score": 0.22}
]
```

`GET /api/catalog/search?q=switchgear` (default `k=5`) returns CROWN-MCSG 0.295, ANORD-MVSG 0.2, CROWN-ARMV 0.186, CROWN-ARMV/Arc-Resistant Switchgear 0.147 and CROWN-EHOUSE/TPSS 0.121.

**Status codes and exact error bodies** (all from request validation, observed live):

| Code | When | Body |
|---|---|---|
| 200 | Valid request | Array of hits (possibly `[]`) |
| 422 | `q` missing | `{"detail":[{"type":"missing","loc":["query","q"],"msg":"Field required","input":null}]}` |
| 422 | `k` below 1 (for example `k=0`, `k=-1`) | `{"detail":[{"type":"greater_than_equal","loc":["query","k"],"msg":"Input should be greater than or equal to 1","input":"0","ctx":{"ge":1}}]}` |
| 422 | `k` above 50 | `{"detail":[{"type":"less_than_equal","loc":["query","k"],"msg":"Input should be less than or equal to 50","input":"51","ctx":{"le":50}}]}` |
| 422 | `k` not an integer | Standard validation body with `type` `int_parsing` |

**Side effects.** None. **Model calls.** As in section 9.1 (embedding of `q` only with a provider). **Preconditions / postconditions.** None.

**Called by.** No screen. The test suite checks that `k=-1` is refused with 422 (`tests/test_smoke.py`, `test_workflow_order_and_roles`).

**Example.**

```bash
curl -s "http://127.0.0.1:8000/api/catalog/search?q=liquid%20cooling%20120%20kW&k=3" -H 'X-Actor: Bid%20Manager'
```

### 9.3 GET /api/people

**Purpose.** The list of people a user can act as in this proof of concept, each with the business unit they belong to. The OpenAPI description reads: "Actors for the PoC user picker, with their business unit (None = bid manager)." There is no sign-in: the chosen name is sent on every request in the `X-Actor` header (see 04-api-view.md, section 3).

**Parameters and body.** None.

**Response (200).** A JSON array of `{name, bu}` objects:

| Field | Type | Meaning |
|---|---|---|
| `name` | string | Actor name: `Bid Manager`, then the product manager and the design engineer of every **active** unit, in unit order. |
| `bu` | string or null | Code of the unit whose product manager or design engineer this is; `null` for the Bid Manager. |

The list has 17 entries: the Bid Manager plus 2 people for each of the 8 active units. The two EPC people are not listed, because EPC is pending.

Real response from the isolated API (complete, 884 bytes):

```json
[{"name":"Bid Manager","bu":null},
 {"name":"EP² Product Manager","bu":"EP2"},{"name":"EP² Design Engineer","bu":"EP2"},
 {"name":"Crown Product Manager","bu":"CROWN"},{"name":"Crown Design Engineer","bu":"CROWN"},
 {"name":"Anord Mardix Product Manager","bu":"ANORD"},{"name":"Anord Mardix Design Engineer","bu":"ANORD"},
 {"name":"Flex Power Modules Product Manager","bu":"FPM"},{"name":"Flex Power Modules Design Engineer","bu":"FPM"},
 {"name":"JetCool Product Manager","bu":"JETCOOL"},{"name":"JetCool Design Engineer","bu":"JETCOOL"},
 {"name":"Cloud Product Manager","bu":"CLOUD"},{"name":"Cloud Design Engineer","bu":"CLOUD"},
 {"name":"Flex Manufacturing Services Product Manager","bu":"EMS"},{"name":"Flex Manufacturing Services Design Engineer","bu":"EMS"},
 {"name":"Flex Aftermarket Services Product Manager","bu":"AFS"},{"name":"Flex Aftermarket Services Design Engineer","bu":"AFS"}]
```

**Status codes.** 200 only.

**Side effects.** None. **Model calls.** None. **Preconditions / postconditions.** None.

**Called by.**

- Top bar, **Acting as** picker (`web/components/shell/ActorPicker.tsx`), on every page load: fills the drop-down. Choosing a name stores it in the `actor` cookie (one year) and reloads the page, so every later request carries the new `X-Actor` header.
- **My work** (`web/app/inbox/page.tsx`, route `/inbox`): finds the acting person in the list and redirects to `/inbox/<bu>`, or to `/inbox/BID` (the bid desk) when the person has no unit or is not in the list. On failure the screen shows "Could not find your work package: <error>. Refresh to try again." See `images/25-inbox-redirect.png`.

The names in this list are the only names the work-package endpoints accept as a unit's answerer (section 12.4); the name `Bid Manager` is the only one accepted for validation (section 12.5).

**Example.**

```bash
curl -s http://127.0.0.1:8000/api/people -H 'X-Actor: Bid%20Manager'
```

## 10. Matching Endpoints

The matching module (`app/modules/matching/`) proposes, for every approved requirement, which business unit or units and which product family would meet it, and with which offering type. A person then accepts, rejects or changes each proposal. The three endpoints below are Implemented and tagged `matching` in the OpenAPI document.

**The `match` table.** Every proposal and every manual choice is a row in table `match` (`app/modules/matching/models.py`). The change endpoint returns the full row (section 10.3). The Traceability endpoint returns the row without `evidence` (see 04-api-view.md, section 15). The fields are:

| Field | Type | Meaning |
|---|---|---|
| `id` | integer | Match id; the `{match_id}` of section 10.2. |
| `opportunity_id` | string | For example `OPP-0001`. |
| `req_id` | string | Requirement id, for example `REQ-0001-0887`. |
| `bu` | string or null | Main (first) unit; `null` when the bid manager answers it (the "bid desk"). |
| `product_id` | string or null | Main product family; `null` for the bid desk. |
| `offering_type` | string | Main offering type: `CTO`, `SEMI_CUSTOM`, `ETO`, or `NONE` (not a product item). |
| `units` | array of `{bu, product_id, offering_type}` | Every unit and product, main one first; `[]` = bid desk. |
| `confidence` | number | The agent's confidence; the retrieval score for a retrieval-only proposal; `1.0` for rule and manual rows. |
| `rationale` | string | Why. For a manual row: `Set by <actor>.` |
| `evidence` | array of hits | The 5 best long-term-index hits for the requirement's quote (hit shapes as in section 9.1); `[]` for a manual row. |
| `method` | string | `agent` (model answer), `retrieval_only` (fallback: closest catalog entry), `rule` (not a product category, no model call), `manual` (set by a person). |
| `status` | string | `proposed`, `accepted` or `rejected`. |
| `decided_by` | string or null | Who accepted, rejected or set it. |
| `created_at` | datetime | When the row was written. |

**Which row counts.** Rows are never deleted. A re-run of matching and every manual change insert a new row; for each requirement the latest row wins. A requirement whose latest row is `rejected` counts as having **no match** everywhere: Traceability shows it as not matched, the bid decision lists it under `unmatched`, and dispatch sends it to the bid desk. No older proposal comes back. Accepting or rejecting updates the `status` of an existing row.

**How the front end labels `method`** (`web/components/matching/MatchActions.tsx`): `manual` "set by a person"; `agent` "proposed by the matching agent"; `rule` "routed to the bid desk by rule (not a product category)"; `retrieval_only` "closest catalog entry (no agent answer)".

### 10.1 POST /api/opportunities/{opp_id}/match

**Purpose.** Run the matching agent over the opportunity: propose a unit, product and offering type for every approved requirement that no person has decided yet. A re-run refreshes only proposals; accepted, rejected and manual matches are a person's decision and are kept.

**Path parameters.**

| Name | Type | Meaning |
|---|---|---|
| `opp_id` | string | Opportunity id, for example `OPP-0001`. Not checked for existence (see status codes). |

**Query parameters.** None. **Request body.** None (an empty body or `{}` is accepted).

**What the call does, step by step** (`app/modules/matching/service.py`, function `match`):

1. Finds the requirements already decided: those whose latest match row has a status other than `proposed`. They are counted as `kept` and not touched.
2. Selects the current requirements with status `approved` that are not decided. A frozen baseline is **not** required: matching works before freezing. Requirements still `proposed` or `rejected` in the review are skipped.
3. Retrieves evidence: the 5 best long-term-index hits for each requirement's quote, in one batched search.
4. Routes by category. A requirement whose category is not `technical` or `compliance` (for example `schedule`, `commercial`, `submission`, `legal`, `staffing`) goes to the bid desk by rule, with no model call: `units` `[]`, `confidence` 1.0, rationale `A <category> requirement, not a product item: the bid manager answers it.`, method `rule`.
5. Groups the `technical` and `compliance` requirements into page batches: same document and page, at most 15 per batch, in document order.
6. Sends each batch to the model gateway, four batches in parallel (task `match_requirement`). The prompt carries the page header (the header lines of the source page, read from the frozen page layout) and the numbered requirements as `<n>. (<category>) <quote>`. The fixed system part holds the matching rules, the 60 active product families and the past responses of the active units. No requirement id is in the prompt.
7. Checks each answer: only units whose `product_id` is a catalog product family are kept; the unit is taken from the product, so unit and product never disagree; duplicates are dropped; at most 3 units are kept. An empty `units` list in the answer means "not a product item" (bid desk), method `agent`.
8. Falls back where there is no usable answer (no answer for that number, the model gateway is unavailable, or the model named only things that are not catalog products). The retrieval-only rule takes the best `product` hit, else the best `catalog_item` hit (standing for its family). If the requirement is not a product category, there is no hit, or the hit's score is below 0.08, the result is the bid desk with rationale `Not matched to a product; the bid manager answers it.` and confidence 0.0. Otherwise one unit, with rationale `Closest catalog entry <id> (retrieval score <score>).` and the score as confidence. When the model did answer but named no catalog product, the rationale starts with `Model answer [<ids>] has no catalog product. `. Method `retrieval_only`.
9. Inserts one new `match` row per selected requirement (status `proposed`), records one audit event per row, and commits once.

**Response (200).**

| Field | Type | Meaning |
|---|---|---|
| `matched` | integer | Requirements that received a new proposal. |
| `kept` | integer | Requirements kept because a person decided them (accepted, rejected or manual). |
| `calls` | integer | Page batches sent to the model gateway (including those answered from frozen answers). |
| `agent` | integer, optional | Proposals from a model answer. Present only when greater than 0. |
| `rule` | integer, optional | Proposals routed to the bid desk by category. Present only when greater than 0. |
| `retrieval_only` | integer, optional | Proposals from the retrieval fallback. Present only when greater than 0. |

Real examples. These requests were made on a private copy of the isolated API's data, on a new opportunity (`OPP-0005`) created for this document. It holds the 10 requirements of the one-page hyperscale sample, added by hand and approved. First run:

```json
{"matched": 10, "kept": 0, "calls": 1, "agent": 9, "rule": 1}
```

The same call after one match was accepted, one rejected and two were set by hand:

```json
{"matched": 7, "kept": 3, "calls": 1, "retrieval_only": 6, "rule": 1}
```

The second run shows an offline-mode effect. The page batch now held 7 requirements instead of 10, so the prompt differed from the one whose answer is frozen; the gateway had no answer, and all six product-category requirements fell back to retrieval-only. In offline mode, a re-run after some matches were decided can therefore replace agent proposals with retrieval-only ones. For example "About 48 MW critical IT load in phase 1.", which the agent had routed to the bid desk, became `ANORD-STS` with score 0.135. With a live model, the new batch is answered by the model instead.

On an opportunity with no approved requirement, or with an unknown `opp_id`, the response is `{"matched": 0, "kept": 0, "calls": 0}`.

**Status codes.**

| Code | When | Body |
|---|---|---|
| 200 | For a known or an unknown `opp_id` | The counts above |
| 500 | Unexpected failure, for example a page-anchored requirement whose document layout is missing from the store | `Internal Server Error` (no mapped message) |

There is no 404: an unknown opportunity simply has nothing to match. A missing frozen answer is never an error, because the service falls back to retrieval.

**Side effects.**

- Table `match`: one inserted row per requirement counted in `matched`.
- Table `audit_event`: one event per inserted row; action `proposed`, entity `match`, entity id = the requirement id, data `{"units": [...], "method": "agent" | "rule" | "retrieval_only"}`. The actor is recorded as `matching agent (<X-Actor>)`, for example `matching agent (Bid Manager)`: the agent proposes, the person asked.
- Files: none written. Page layouts are only read.
- Other modules called: requirements (current requirements), catalog (products, past responses, search), ingestion (page layout for the page header).

**Model calls.** Task `match_requirement`, one call per page batch, through `app/core/llm.complete_json` (structured JSON output, temperature 0). Answer schema: `{"answers": [{"n", "units": [{"bu", "product_id", "offering_type": "CTO" | "SEMI_CUSTOM" | "ETO"}], "confidence", "rationale"}]}`. Every answer is cached in `data/llm_cache/match_requirement/<key>.json`, keyed by task, model, system prompt, prompt and schema; the repository holds 67 frozen answers. Offline (`LLM_PROVIDER` other than `azure`), a batch whose exact prompt has a frozen answer gets it; any other batch gets the retrieval-only fallback. Because no requirement id is in the prompt, the same RFP text gets the same frozen answer in any opportunity.

**Preconditions.** None enforced. In practice the requirements must first be approved on the Requirements screen, otherwise `matched` is 0.

**Postconditions.** Every approved, undecided requirement has a new latest row with status `proposed`. Decided requirements are unchanged.

**Duration.** Synchronous. On a new RFP with a live model it can take minutes; the web proxy waits up to 30 minutes (`experimental.proxyTimeout` in `web/next.config.ts`).

**Called by.**

- Traceability screen, button **Match products** (`web/app/opportunities/[id]/trace/page.tsx`). While it runs the button shows a busy state. On success the toast reads `Matching done: <matched> requirement(s) matched, <kept> kept as decided.` and the screen reloads its data; on failure the toast shows the error text.
- Changes module, after a change set is applied (see 04-api-view.md, section 8). It calls the same service function with the added and modified requirements only, so that the page batches of untouched requirements, and their frozen answers, stay as they were. This "only these requirements" option is not available through the endpoint.
- The demo seed script (`scripts/seed_demo.py`), with the actor `matching agent (seed)`.

**Example.**

```bash
curl -s -X POST http://127.0.0.1:8000/api/opportunities/OPP-0001/match -H 'X-Actor: Bid%20Manager'
```

### 10.2 POST /api/matches/{match_id}/decide

**Purpose.** A person accepts or rejects one proposed match.

**Path parameters.**

| Name | Type | Constraints | Meaning |
|---|---|---|---|
| `match_id` | integer | `1 <= match_id <= 2147483647` | The `id` of a `match` row (from the Traceability payload, `rows[].match.id`). |

**Request body** (`DecideIn`; OpenAPI schema name `app__modules__matching__controller__DecideIn`, because the changes module has its own `DecideIn`):

| Field | Type | Required | Constraints | Default | Meaning |
|---|---|---|---|---|---|
| `action` | string | yes | `accept` or `reject` | none | `accept` sets status `accepted`; `reject` sets status `rejected`. |

This endpoint never changes units or products. Changing them is done with section 10.3, whose body is `ChangeIn` (a list of `UnitIn`).

**Response (200).** `{"ok": true}`.

**Status codes and exact messages** (observed):

| Code | When | Body |
|---|---|---|
| 200 | Row found and updated | `{"ok": true}` |
| 404 | No row with that id | `{"detail": "Match 999999 not found."}` (pattern `Match <id> not found.`) |
| 422 | `action` not `accept` or `reject` | `{"detail":[{"type":"literal_error","loc":["body","action"],"msg":"Input should be 'accept' or 'reject'","input":"approve","ctx":{"expected":"'accept' or 'reject'"}}]}` |
| 422 | `match_id` below 1 | `msg` `Input should be greater than or equal to 1`, `loc` `["path","match_id"]` |
| 422 | `match_id` above 2147483647 | `msg` `Input should be less than or equal to 2147483647` |
| 422 | Body or `action` missing | `type` `missing`, `msg` `Field required` |

**Side effects.**

- Table `match`: `status` set to `accepted` or `rejected` and `decided_by` set to the actor, on that row.
- Table `audit_event`: action `accept` or `reject` (the verb, not the status), entity `match`, entity id = the requirement id, data `{"bu": <main unit>, "product": <main product>}`.
- Nothing is re-dispatched. If work was already dispatched, a rejection reaches the units only at the next dispatch (section 12.1), when the requirement counts as unmatched and goes to the bid desk.

**Model calls.** None.

**Preconditions.** The row exists. There is no state guard: any row can be decided, including one already decided, a rule row with no units, or an older row that is no longer the latest (deciding an older row has no visible effect, because only the latest row counts). Accepting a rejected row restores it.

**Postconditions.** For the latest row, `accepted` makes the requirement "decided" (a re-run of matching keeps it) and removes it from the `not_reviewed` count of the bid decision (section 11.1). `rejected` makes the requirement unmatched and also keeps it out of re-runs.

**Called by.** Traceability screen, pane 3, buttons **Accept** and **Reject** (`web/components/matching/MatchActions.tsx`), shown only while the match status is `proposed`. Toasts: `<REQ>: match accepted.` and `<REQ>: match rejected. Use Change to pick a unit.` The screen then reloads its data. See `images/37-trace-match-change-editor-OPP-0001.png` (row REQ-0001-0002 shows **Accept**, **Reject** and **Change**).

**Example.**

```bash
curl -s -X POST http://127.0.0.1:8000/api/matches/134/decide -H 'X-Actor: Bid%20Manager' \
  -H 'Content-Type: application/json' -d '{"action": "accept"}'
```

### 10.3 POST /api/opportunities/{opp_id}/requirements/{req_id}/match

**Purpose.** A person sets the match of one requirement directly: one or more product families, each with an offering type, or none (the bid manager answers it). This is the endpoint that takes `ChangeIn`.

**Path parameters.**

| Name | Type | Meaning |
|---|---|---|
| `opp_id` | string | Opportunity id. |
| `req_id` | string | Requirement id; it must belong to `opp_id`. |

**Request body** (`ChangeIn`, containing `UnitIn` objects):

| Field | Type | Required | Constraints | Default | Meaning |
|---|---|---|---|---|---|
| `units` | array of `UnitIn` | yes | may be empty | none | The person's choice, main one first. `[]` = not a product item: the bid desk answers it. |
| `units[].product_id` | string | yes | a product family of an **active** unit | none | Product family id, for example `FPM-800V`. The unit is taken from the product; the body has no unit field. |
| `units[].offering_type` | string | yes | `CTO`, `SEMI_CUSTOM` or `ETO` (`NONE` is refused) | none | Offering type for this product on this requirement. |

The service drops a repeated product (the first occurrence wins). A manual choice has no limit on the number of units; the limit of 3 applies only to agent answers.

**Response (200).** The new `match` row with every field of the table at the top of this section, including `evidence` (always `[]`): `method` `manual`, `status` `accepted`, `confidence` 1.0, `rationale` `Set by <actor>.`, `decided_by` = the actor. In this response `created_at` carries a `+00:00` offset; the same row read back later has none.

Real example (private copy, own opportunity; the repeated `FPM-800V` was dropped). Request body:

```json
{"units": [{"product_id": "FPM-800V", "offering_type": "CTO"},
           {"product_id": "FPM-DCPDU", "offering_type": "SEMI_CUSTOM"},
           {"product_id": "FPM-800V", "offering_type": "ETO"}]}
```

Response:

```json
{"id": 371, "opportunity_id": "OPP-0005", "req_id": "REQ-0005-0004", "bu": "FPM", "product_id": "FPM-800V",
 "offering_type": "CTO",
 "units": [{"bu": "FPM", "product_id": "FPM-800V", "offering_type": "CTO"},
           {"bu": "FPM", "product_id": "FPM-DCPDU", "offering_type": "SEMI_CUSTOM"}],
 "confidence": 1.0, "rationale": "Set by Bid Manager.", "evidence": [], "method": "manual",
 "status": "accepted", "decided_by": "Bid Manager", "created_at": "2026-10-13T08:06:55.264898+00:00"}
```

With `{"units": []}` the new row has `"bu": null`, `"product_id": null`, `"offering_type": "NONE"` and `"units": []`.

**Status codes and exact messages** (observed):

| Code | When | Body |
|---|---|---|
| 200 | Saved | The new row |
| 404 | Requirement unknown, or it belongs to another opportunity | `{"detail": "REQ-0005-0999 is not a requirement of OPP-0005."}` (pattern `<req_id> is not a requirement of <opp_id>.`) |
| 422 | Product unknown, or it belongs to the pending unit | `{"detail": "EPC-800V is not a product of an active business unit."}` (pattern `<product_id> is not a product of an active business unit.`) |
| 422 | `offering_type` not `CTO`, `SEMI_CUSTOM` or `ETO` | `{"detail":[{"type":"literal_error","loc":["body","units",0,"offering_type"],"msg":"Input should be 'CTO', 'SEMI_CUSTOM' or 'ETO'","input":"NONE",...}]}` |
| 422 | `units` missing | `{"detail":[{"type":"missing","loc":["body","units"],"msg":"Field required","input":{}}]}` |

The service also holds the message `<offering_type> is not an offering type.` (422), but request validation refuses a bad offering type first, so it cannot be reached through the API.

**Side effects.**

- Table `match`: one inserted row, which becomes the latest for the requirement.
- Table `audit_event`: action `manual`, entity `match`, entity id = the requirement id, data `{"units": [<chosen units>]}`.
- Nothing is re-dispatched. Already dispatched work changes only at the next dispatch (section 12.1): added units that take part get work, removed units have theirs withdrawn.

**Model calls.** None.

**Preconditions.** The requirement exists in the opportunity. There is no check of its review status, of freezing or of dispatch.

**Postconditions.** The requirement is "decided": re-runs of matching keep this row. The bid decision's `suggested_units`, `offering_mix`, engineering checks and summary reflect it at once.

**Called by.** Traceability screen, pane 3, **Change** editor (`web/components/matching/MatchActions.tsx`). It shows one row per unit with a product drop-down (grouped by active unit; choosing a product also resets the offering type to the product's usual one), an offering-type drop-down and **Remove**, plus the buttons **Add unit**, **Save** and **Cancel**. With no rows it says "No unit: the bid manager answers it (not a product item)." When the opportunity was already dispatched it warns: "Already sent to units: dispatch again on the Decisions page to apply this change. Added units get the work (if they take part); removed units have theirs withdrawn." **Save** sends only `product_id` and `offering_type` of each row; the toast reads `<REQ>: match saved.` See `images/37-trace-match-change-editor-OPP-0001.png`.

**Example.**

```bash
curl -s -X POST http://127.0.0.1:8000/api/opportunities/OPP-0001/requirements/REQ-0001-0887/match \
  -H 'X-Actor: Bid%20Manager' -H 'Content-Type: application/json' \
  -d '{"units": [{"product_id": "CROWN-ARMV", "offering_type": "ETO"}, {"product_id": "EP2-RPP", "offering_type": "ETO"}]}'
```

## 11. Decisions Endpoints

The decisions module (`app/modules/decisions/`) assembles the evidence a bid manager reads before deciding, and records two kinds of decision made by a named person: **participation** (which business units take part) and **go / no-go**. Layer 0 gives advice; it never decides. The three endpoints are Implemented and tagged `decisions` in the OpenAPI document.

**The `decision` table.** Each recorded decision is a new row in table `decision` (`app/modules/decisions/models.py`). Rows are never updated or deleted; the latest row of each kind (highest id) is the one in force.

| Field | Type | Meaning |
|---|---|---|
| `id` | integer | Decision id (also used by the knowledge module to send a rationale to the knowledge base; see 04-api-view.md, section 13). |
| `opportunity_id` | string | Opportunity id. |
| `kind` | string | `participation` or `go_no_go`. |
| `outcome` | string | Participation: always `units`. Go / no-go: `go` or `no_go`. |
| `units` | array of strings | Participation: the chosen unit codes. Go / no-go: a copy of the latest participation's units at the moment of deciding (`[]` when none was recorded); it is not updated by later participation changes. |
| `evidence` | object | The full evidence pack exactly as computed at the moment of deciding (the 11 keys of section 11.1). For go / no-go it also holds `summary` (12 keys): "stored as shown". |
| `rationale` | string | Free text from the person. |
| `criteria` | array of `{id, status, note}` | Go / no-go only: the person's own judgement per criterion. `[]` for participation. |
| `decided_by` | string | The actor. |
| `decided_at` | datetime | When. |

### 11.1 GET /api/opportunities/{opp_id}/decisions

**Purpose.** Everything the Bid decision screen shows: the evidence pack, the go / no-go summary with Layer 0's assessment of each criterion, the active business units to choose from, and the latest participation and go / no-go decisions.

**Path parameters.**

| Name | Type | Meaning |
|---|---|---|
| `opp_id` | string | Opportunity id. |

**Query parameters.** None. **Request body.** None.

**Response (200), top level.**

| Field | Type | Meaning |
|---|---|---|
| `evidence` | object | The evidence pack (table below). Always present, also before freezing. |
| `summary` | object or null | The go / no-go summary (table further below); `null` until the requirements are frozen (`evidence.frozen` false). |
| `units` | array of unit objects | The **active** business units only (8: EP2, CROWN, ANORD, FPM, JETCOOL, CLOUD, EMS, AFS), with the unit fields of section 9.1. These are the participation choices; the pending unit EPC is not offered. |
| `participation` | decision row or null | The latest participation decision (all fields of the `decision` table, with its stored evidence), or `null`. |
| `go_no_go` | decision row or null | The latest go / no-go decision, or `null`. |

**Decision history.** Only the latest decision of each kind is returned. Earlier decisions stay in table `decision` and in the audit log (`audit_event`, action `decided`), but no endpoint lists them.

**`evidence` fields** (`decisions.service.evidence`):

| Field | Type | Meaning and source |
|---|---|---|
| `requirements` | integer | Number of current requirements (every status that is still active, including `proposed` ones still under review; replaced, rejected and duplicate items and sub-requirements are not counted). |
| `frozen` | boolean | `true` when the opportunity has at least one frozen baseline. |
| `by_category` | object | Count of current requirements per category, for example `{"technical": 147, "submission": 86, ...}`. |
| `unanchored` | array of strings | Ids of current requirements whose quote was not found in the source (`provenance` `UNANCHORED`). |
| `suggested_units` | object | Unit code -> number of requirements whose current (non-rejected) match lists that unit. Every listed unit counts, not only the main one; each unit once per requirement. |
| `offering_mix` | object | Count of the main offering type over the current matches: `CTO`, `SEMI_CUSTOM`, `ETO`, `NONE` (bid desk). |
| `unmatched` | array of strings | Ids of current requirements with no match, or whose latest match is rejected. |
| `not_reviewed` | integer | Matches still `proposed` that name at least one unit: "product matches nobody accepted". |
| `checks` | object | Engineering checks over the frozen, approved requirements (table below). |
| `deviations` | object | RFP data sheet against the standard ratings of the products in play (table below). |
| `workload` | object | Each unit's open work across all opportunities against its capacity (table below). |

Matches of requirements that are no longer current (split, merged, rejected, replaced) are ignored in `offering_mix`, `unmatched` and `not_reviewed`.

**`evidence.checks` fields** (`matching.service.evidence_checks` and `app/modules/matching/checks.py`; no model call). Only requirements with status `approved` and a baseline number are checked.

| Field | Type | Meaning |
|---|---|---|
| `requirements_checked` | integer | Number of frozen, approved requirements checked. |
| `scope.in_scope` | array of integers | Layer numbers judged in scope. When no layer meets the threshold, all six are in scope ("full scope assumed"). |
| `scope.layers[]` | array | One entry per layer of `data/knowledge_base/spinco_layers.json`: `n`, `name`, `units`, `in_scope`, `basis` (`decisive term`, `<n> distinct terms`, `<hits> hits (threshold 3)`, or `no layer met the threshold; full scope assumed`), `terms` (up to 5 `{term, count, req_ids}` with at most 3 requirement ids each). A layer is in scope with 3 or more keyword hits, 2 or more distinct keywords, or one decisive term. |
| `facts` | object | Facts the rules need, each `{"value", "req_id"}` or `null` when the requirements do not state them: `vdc_800`, `voltage_stated`, `rack_density_kw`, `redundancy_2n_utility`, `ups_kva`, `rack_count`, `branch_circuits` (also `volts`), `medium_voltage`. |
| `units_outside_scope` | object | Unit code -> requirement ids, for a matched unit none of whose layers is in scope. Units with no layer (EMS, AFS) are always outside scope when matched. |
| `tier_flags` | array | `{req_id, bu, product_id, kind, note}`; `kind` is `below_default` (offering type below the unit's default automation tier: "an engineer must confirm this part is genuinely standard"), `raise` or `suggest_lower` (a component keyword such as "standard enclosure" or "first-of-kind"). |
| `rules` | array | Rules R-001 to R-004 of `engineering_rules.json`: `{id, rule, status, note}`, status `pass`, `warn`, `fail` or `n/a`. A fact the RFP does not state gives `warn`, never `pass`. Only R-002 (rack density of 100 kW or more without direct-to-chip cooling) can fail. |
| `solver` | object | Low-voltage arithmetic: `status` `SOLVED`, `SOLVED_WITH_WARNINGS` or `NOT_SOLVABLE`; `reasons`; `working` (steps `{step, expression, result, unit, reference}`); `warnings`; when solved also `inputs` and `standards_note`. |

**`evidence.deviations` fields** (`app/modules/decisions/portfolio.py`):

| Field | Type | Meaning |
|---|---|---|
| `rows` | array | `{product_id, field, rfp, standard, severity, source}`: a data-sheet value of the main RFP above the standard rating (or different from it, for frequency). Severity `high` for voltage, current and frequency; `medium` for impulse level and momentary rating. `source` is `p. <page>, data sheet row <row>`. |
| `checked` | integer | Number of data-sheet values compared. |
| `products` | array of strings | Product families in play (every unit of every current match). |
| `placeholder` | boolean | Always `true`. |
| `note` | string | `Standard ratings are PLACEHOLDERS ported from the v1.1 demo; to be confirmed.` |

Data-sheet values are read from the ruled tables of the main RFP's page layout, and only when the main document is `ingested`. Only `CROWN-ARMV` has standard ratings in `data/knowledge_base/portfolio.json` (placeholders).

**`evidence.workload` fields:**

| Field | Type | Meaning |
|---|---|---|
| `rows[].bu` | string | Unit code, or `BID` for the bid desk. |
| `rows[].open_here` | integer | Open work items of the unit in this opportunity, plus the work this opportunity would add (matches whose requirement has no active assignment yet; a match without units adds to `BID`). |
| `rows[].open_elsewhere` | integer | Open work of the unit in other opportunities. Open = assignment status `assigned`, `submitted` or `returned`. |
| `rows[].other_opportunities` | array of strings | The other opportunities with open work for the unit. |
| `rows[].total` | integer | All open work of the unit plus what this opportunity would add. |
| `rows[].capacity` | integer or null | Placeholder capacity from `portfolio.json` (CROWN 150, EP2 60, ANORD 100, FPM 100, JETCOOL 80, CLOUD 80, BID 400; none for EMS, AFS, EPC). |
| `rows[].over` | boolean | `true` when a capacity exists and `total` exceeds it. |
| `placeholder` | boolean | Always `true`. |
| `note` | string | `Capacity is a PLACEHOLDER count of open work items per unit; to be confirmed with each unit.` |

**`summary` fields** (`decisions.service.summary`; present only when frozen):

| Field | Type | Meaning |
|---|---|---|
| `rows` | array | One per frozen, approved requirement: `{req_id, category, text, level, basis, units}`. |
| `rows[].level` | string | `fully`, `partly`, `not` or `bid_desk`. From the units' answers when any active assignment has a compliance value (`met` -> fully, `partial` -> partly, `not_met` and `exception` -> not; with several answers the weakest wins). Otherwise estimated from the match: `CTO` -> fully, `SEMI_CUSTOM` and `ETO` -> partly (weakest unit wins). A match with no units -> `bid_desk`; no match at all -> `not`. |
| `rows[].basis` | string | `validated answer` (every answer validated), `answer, not yet validated`, `match`, or `no match`. |
| `rows[].units` | array of strings | The answering units, or the matched units. A unit appears once per matched product, so two products of one unit list it twice (observed: `["FPM", "FPM"]`). |
| `by_category` | object | Category -> `{"fully", "partly", "not", "bid_desk"}` counts. |
| `coverage` | number | Share of non-bid-desk rows that are `fully` or `partly`, rounded to 3 decimals; 0.0 when there is none. A bid-desk requirement that has an answer becomes a non-bid-desk row and counts here. |
| `criteria` | array | The 12 criteria of `data/knowledge_base/go_no_go.json`, each with `id`, `name`, `question`, `status` (`met`, `not_met` or `unknown`), `detail`, and `data` (`not_available`) where present. |
| `advice` | string | `Advice from Layer 0: <met> of <assessable> assessable criteria met; <n> cannot be assessed yet (data not available). A person decides.` |

**The 12 criteria and how Layer 0 assesses them.** Thresholds are placeholders. The question texts of `deviations` and `capacity` contain an internal work-item reference from the data file, which is shown verbatim on screen.

| `id` | `name` | Assessed as `met` when | `detail` text |
|---|---|---|---|
| `scope_fit` | Scope fit | `units_outside_scope` is empty | `Suggested units fit the layers in scope [<n>, ...].` or `Units outside the RFP's scope: <codes>` |
| `all_matched` | Every requirement routed | `unmatched` is empty | `Every requirement is routed.` or `<n> requirement(s) without a match.` |
| `coverage` | Coverage | `coverage` >= 0.8 | `<pct> of <n> product requirements fully or partly satisfied (threshold 80%, placeholder).` |
| `engineering_rules` | Engineering rules | no rule has status `fail` | `No engineering rule fails.` or `Failing: <ids>` |
| `open_questions` | Open questions | no rule is `warn` and nothing is unanchored | `Rule warnings: <ids or none>; unanchored requirements: <n>.` |
| `matches_reviewed` | Matches reviewed | `not_reviewed` is 0 | `<n> product match(es) not yet accepted or changed by a person.` |
| `pending_acquisition` | No pending-acquisition dependency | R-004 is not `warn` | The R-004 note, for example `No match depends on EPC Power.` |
| `deviations` | Deviations from the standard product | nothing compared, or no high or medium deviation | `No data-sheet rating found to compare with a standard product.`, or `<field>: RFP <value> vs standard <value> (<product>, <severity>, <source>)` joined by "; ", or `<n> data-sheet ratings within the standard products`; then `. Standards are placeholders.` |
| `capacity` | Capacity and portfolio conflicts | no workload row is over capacity | `Open work vs capacity: <bu> <total>/<capacity> (also in <opps>); ...` or `Over capacity: ...`; with no unit work `Open work vs capacity: no unit work yet. Capacity is a placeholder.` |
| `cost_budget` | Cost against budget | never assessed | `Data not yet available.` (status `unknown`) |
| `delivery` | Delivery against the RFP schedule | never assessed | `Data not yet available.` plus ` The RFP's schedule requirements: <ids>.` when there are schedule requirements (status `unknown`) |
| `competitors` | Competitor information | never assessed | `Data not yet available.` (status `unknown`) |

**Real example** (isolated API, `GET /api/opportunities/OPP-0001/decisions`, 142,058 bytes, about 0.84 s; after the addendum, baseline 2; trimmed):

```json
{
  "evidence": {
    "requirements": 349, "frozen": true,
    "by_category": {"schedule": 9, "compliance": 67, "submission": 86, "legal": 18, "commercial": 11, "staffing": 11, "technical": 147},
    "unanchored": ["REQ-0001-0141", "REQ-0001-0154", "REQ-0001-0168", "... 32 in total"],
    "suggested_units": {"CROWN": 99, "EP2": 5},
    "offering_mix": {"NONE": 245, "ETO": 98, "CTO": 5, "SEMI_CUSTOM": 1},
    "unmatched": [], "not_reviewed": 104,
    "checks": {
      "requirements_checked": 349,
      "scope": {"in_scope": [2, 3], "layers": [
        {"n": 1, "name": "Grid Interface", "units": ["EPC"], "in_scope": false, "basis": "1 hits (threshold 3)",
         "terms": [{"term": "interconnect", "count": 1, "req_ids": ["REQ-0001-0931"]}]},
        {"n": 2, "name": "Utility / Facility Electrical", "units": ["CROWN", "EP2", "ANORD"], "in_scope": true, "basis": "decisive term",
         "terms": [{"term": "switchgear", "count": 68, "req_ids": ["REQ-0001-0846", "REQ-0001-0887", "REQ-0001-0885"]}, "..."]},
        {"n": 3, "name": "Power Distribution (Room to Row to Rack)", "units": ["ANORD"], "in_scope": true, "basis": "5 hits (threshold 3)",
         "terms": [{"term": "prefabricated", "count": 5, "req_ids": ["REQ-0001-0903", "REQ-0001-0908", "REQ-0001-0935"]}]},
        "... layers 4, 5, 6 not in scope (0 hits)"]},
      "facts": {"vdc_800": null, "voltage_stated": {"value": "125 vdc", "req_id": "REQ-0001-0953"}, "rack_density_kw": null,
                "redundancy_2n_utility": null, "ups_kva": null, "rack_count": null, "branch_circuits": null,
                "medium_voltage": {"value": true, "req_id": "REQ-0001-0887"}},
      "units_outside_scope": {},
      "tier_flags": [{"req_id": "REQ-0001-0888", "bu": "CROWN", "product_id": "CROWN-ACC", "kind": "below_default",
                      "note": "CTO is below CROWN's default ETO_GUIDED: an engineer must confirm this part is genuinely standard."}, "... 5 in total"],
      "rules": [
        {"id": "R-001", "rule": "If any selected layer specifies 800VDC, ...", "status": "pass", "note": "Voltage architecture 125 vdc (REQ-0001-0953) needs no 800 V DC check."},
        {"id": "R-002", "rule": "If rack_density_kw >= 100, ...", "status": "n/a", "note": "Cooling (layer 5) is not in scope and no rack density is stated."},
        {"id": "R-003", "rule": "If redundancy specifies '2N' at the utility level, ...", "status": "warn", "note": "Redundancy class is not stated: the layer-2 selection cannot be verified. Clarify before quoting."},
        {"id": "R-004", "rule": "EPC Power is currently a pending acquisition ...", "status": "pass", "note": "No match depends on EPC Power."}],
      "solver": {"status": "NOT_SOLVABLE", "reasons": ["Medium-voltage equipment (REQ-0001-0887) needs protection coordination and an arc-flash study, not arithmetic."], "working": [], "warnings": []}},
    "deviations": {"rows": [{"product_id": "CROWN-ARMV", "field": "Rated continuous current", "rfp": "2000/1200 A, rms", "standard": "600 A",
                             "severity": "high", "source": "p. 74, data sheet row 8"}],
                   "checked": 5, "products": ["CROWN-ACC", "CROWN-ARMV", "EP2-AUX", "EP2-RPP"], "placeholder": true,
                   "note": "Standard ratings are PLACEHOLDERS ported from the v1.1 demo; to be confirmed."},
    "workload": {"rows": [{"bu": "BID", "open_here": 246, "open_elsewhere": 6, "other_opportunities": ["OPP-0002"], "total": 252, "capacity": 400, "over": false},
                          {"bu": "CROWN", "open_here": 99, "open_elsewhere": 0, "other_opportunities": [], "total": 99, "capacity": 150, "over": false},
                          {"bu": "EP2", "open_here": 5, "open_elsewhere": 0, "other_opportunities": [], "total": 5, "capacity": 60, "over": false}],
                 "placeholder": true, "note": "Capacity is a PLACEHOLDER count of open work items per unit; to be confirmed with each unit."}
  },
  "summary": {
    "rows": [{"req_id": "REQ-0001-0001", "category": "schedule", "text": "Proposals must be submitted by September 15, 2023, 4pm.",
              "level": "bid_desk", "basis": "match", "units": []}, "... 349 in total (bid_desk 245, partly 97, fully 7)"],
    "by_category": {"technical": {"fully": 7, "partly": 96, "not": 0, "bid_desk": 44},
                    "compliance": {"fully": 0, "partly": 1, "not": 0, "bid_desk": 66}, "...": "one entry per category"},
    "coverage": 1.0,
    "criteria": [
      {"id": "scope_fit", "name": "Scope fit", "question": "Do the suggested units fit the RFP's scope (no unit outside the layers the RFP covers)?",
       "status": "met", "detail": "Suggested units fit the layers in scope [2, 3]."},
      {"id": "open_questions", "...": "...", "status": "not_met", "detail": "Rule warnings: R-003; unanchored requirements: 32."},
      {"id": "matches_reviewed", "...": "...", "status": "not_met", "detail": "104 product match(es) not yet accepted or changed by a person."},
      {"id": "deviations", "...": "...", "status": "not_met",
       "detail": "Rated continuous current: RFP 2000/1200 A, rms vs standard 600 A (CROWN-ARMV, high, p. 74, data sheet row 8). Standards are placeholders."},
      {"id": "capacity", "...": "...", "status": "met",
       "detail": "Open work vs capacity: BID 252/400 (also in OPP-0002); CROWN 99/150; EP2 5/60. Capacity is a placeholder."},
      {"id": "cost_budget", "name": "Cost against budget", "...": "...", "data": "not_available", "status": "unknown", "detail": "Data not yet available."},
      "... 12 in total"],
    "advice": "Advice from Layer 0: 6 of 9 assessable criteria met; 3 cannot be assessed yet (data not available). A person decides."
  },
  "units": [{"code": "EP2", "name": "Electrical Power Products (EP²)", "...": "..."}, "... 8 active units"],
  "participation": {"id": 1, "opportunity_id": "OPP-0001", "kind": "participation", "outcome": "units", "units": ["CROWN", "EP2"],
                    "evidence": {"...": "11 keys, as at the time"}, "rationale": "Suggested by matching; confirmed.", "criteria": [],
                    "decided_by": "Bid Manager", "decided_at": "2026-10-13T05:51:50.431632"},
  "go_no_go": {"id": 2, "opportunity_id": "OPP-0001", "kind": "go_no_go", "outcome": "go", "units": ["CROWN", "EP2"],
               "evidence": {"...": "11 keys + summary, as at the time"}, "rationale": "In scope for the participating units.", "criteria": [],
               "decided_by": "Bid Manager", "decided_at": "2026-10-13T05:51:50.992007"}
}
```

Other live states: `OPP-0002` (10 requirements, frozen) has `suggested_units` `{"CLOUD": 1, "FPM": 1, "JETCOOL": 1, "ANORD": 1}`, `not_reviewed` 4 and participation `["CLOUD", "FPM", "JETCOOL", "ANORD"]` with a `go`. `OPP-0004` (4 requirements, review in progress, not frozen) has `frozen` false, `summary` null, all 4 requirements in `unmatched`, and no decisions. `OPP-0003` (blank) has `requirements` 0, `summary` null and an empty workload. Before freezing, `checks` is still computed over zero requirements: every layer is in scope ("no layer met the threshold; full scope assumed"), R-001 to R-003 are `warn`, R-004 `pass`, and the solver says `Required input(s) not stated: ups_kva, rack_count. The solver does not assume values.`

**Status codes.**

| Code | When | Body |
|---|---|---|
| 200 | Opportunity exists | The object above |
| 404 | Unknown opportunity | `{"detail": "Opportunity OPP-9999 not found."}` (pattern `Opportunity <opp_id> not found.`) |

The 404 check comes first ("an unknown opportunity is a 404, not an empty evidence pack").

**Side effects.** None (read-only). **Model calls.** None; every check is rule-based.

**Preconditions.** The opportunity exists. **Postconditions.** None.

**Performance.** The payload is large on a big RFP (about 142 KB for 349 requirements, because both stored decisions repeat their full evidence pack) and is recomputed on every call.

**Called by.** Bid decision screen (`web/app/opportunities/[id]/decisions/page.tsx`, route `/opportunities/<id>/decisions`): on page load, when the browser tab regains focus, and after each action on the screen (participation, go / no-go, dispatch). The screen shows the Evidence card, the Engineering checks and the Bid and portfolio checks (only when frozen), card "1. Which business units take part?" (one checkbox per entry of `units`, checked from the latest participation or, when none, from `suggested_units`), card "2. Go / no-go" (the summary, the criteria table with Layer 0's assessment and a "Your judgement" drop-down per criterion), and card "3. Send the work to the units" (only when the latest outcome is `go`). See `images/06-decisions-OPP-0001.png`, `images/18-decisions-OPP-0002.png`, `images/22-decisions-OPP-0003-empty.png` and `images/53-decisions-OPP-0001-after-addendum.png`.

**Example.**

```bash
curl -s http://127.0.0.1:8000/api/opportunities/OPP-0001/decisions -H 'X-Actor: Bid%20Manager'
```

### 11.2 POST /api/opportunities/{opp_id}/participation

**Purpose.** Record which business units take part in the bid. Dispatch (section 12.1) sends product work only to these units.

**Path parameters.**

| Name | Type | Meaning |
|---|---|---|
| `opp_id` | string | Opportunity id. |

**Request body** (`ParticipationIn`):

| Field | Type | Required | Constraints | Default | Meaning |
|---|---|---|---|---|---|
| `units` | array of strings | yes | at least one; every code must be an **active** unit | none | Participating unit codes, for example `["CROWN", "EP2"]`. Order is kept as sent. |
| `rationale` | string | no | none | `""` | Why. |

**Response (200).** The new `decision` row (all fields of the table at the top of this section), with `kind` `participation`, `outcome` `units`, `criteria` `[]` and the full evidence pack as at that moment (11 keys). `decided_at` carries `+00:00` in this response.

Real example (private copy, own opportunity; evidence shortened):

```json
{"id": 5, "opportunity_id": "OPP-0005", "kind": "participation", "outcome": "units", "units": ["JETCOOL", "FPM", "ANORD"],
 "evidence": {"requirements": 10, "frozen": true, "...": "11 keys: requirements, frozen, by_category, unanchored, suggested_units, offering_mix, unmatched, not_reviewed, checks, deviations, workload"},
 "rationale": "Units with matched products; Cloud integration handled separately.", "criteria": [],
 "decided_by": "Bid Manager", "decided_at": "2026-10-13T08:08:45.943399+00:00"}
```

**Status codes and exact messages** (observed):

| Code | When | Body |
|---|---|---|
| 200 | Recorded | The new decision row |
| 404 | Unknown opportunity | `{"detail": "OPP-9999 not found."}` (pattern `<opp_id> not found.`) |
| 422 | Empty list | `{"detail": "Choose at least one active business unit; not active: []."}` |
| 422 | Any code that is unknown or pending | `{"detail": "Choose at least one active business unit; not active: ['EPC', 'NOPE']."}` (the not-active codes, sorted) |
| 422 | `units` missing or not a list | Standard validation body (`type` `missing` or `list_type`) |

**Side effects.**

- Table `decision`: one inserted row (kind `participation`).
- Table `audit_event`: action `decided`, entity `participation`, entity id `units`, data `{"units": [...], "rationale": "...", "criteria": []}`.
- The opportunity status does not change. Existing work packages do not change until the next dispatch.

**Model calls.** None.

**Preconditions.** The opportunity exists. Freezing, matching and an earlier decision are **not** required.

**Postconditions.** `participating_units` = this row's `units`. The next go / no-go copies them; the next dispatch uses them.

**Called by.** Bid decision screen, card "1. Which business units take part?": checkboxes named `units` (one per active unit), the **Rationale** field and the button **Record participation** (busy text "Recording…"). Toast `Participation recorded.`; then the screen reloads `GET /api/opportunities/{opp_id}/decisions`. The recorded line reads "Recorded by <decided_by>: <units>", and a non-empty rationale offers **Send to knowledge base** (see 04-api-view.md, section 13).

**Example.**

```bash
curl -s -X POST http://127.0.0.1:8000/api/opportunities/OPP-0001/participation -H 'X-Actor: Bid%20Manager' \
  -H 'Content-Type: application/json' -d '{"units": ["CROWN", "EP2"], "rationale": "Suggested by matching; confirmed."}'
```

### 11.3 POST /api/opportunities/{opp_id}/go-no-go

**Purpose.** Record the go or no-go decision, with the person's own judgement on each criterion, and move the opportunity status to `go` or `no_go`.

**Path parameters.**

| Name | Type | Meaning |
|---|---|---|
| `opp_id` | string | Opportunity id. |

**Request body** (`GoNoGoIn` with `CriterionIn` objects):

| Field | Type | Required | Constraints | Default | Meaning |
|---|---|---|---|---|---|
| `outcome` | string | yes | `go` or `no_go` | none | The decision. |
| `rationale` | string | no | none | `""` | Why. |
| `criteria` | array of `CriterionIn` | no | each `id` must be one of the 12 criterion ids of section 11.1 | `[]` | The person's judgement per criterion. Any subset may be sent, in any order. |
| `criteria[].id` | string | yes | a known criterion id | none | For example `capacity`. |
| `criteria[].status` | string | yes | `met`, `not_met` or `unknown` | none | The person's judgement. |
| `criteria[].note` | string | no | none | `""` | Optional note. |

**Response (200).** The new `decision` row with `kind` `go_no_go`, `outcome` as sent, `units` copied from the latest participation, `criteria` as sent (with `note` filled in), and the evidence pack plus `summary` (12 keys).

Real example (private copy, own opportunity; evidence shortened):

```json
{"id": 6, "opportunity_id": "OPP-0005", "kind": "go_no_go", "outcome": "no_go", "units": ["JETCOOL", "FPM", "ANORD"],
 "evidence": {"...": "12 keys: the 11 evidence keys plus summary"},
 "rationale": "Hold until the grid interconnect is approved.",
 "criteria": [{"id": "capacity", "status": "met", "note": ""},
              {"id": "delivery", "status": "not_met", "note": "9 months is tight for liquid cooling"}],
 "decided_by": "Bid Manager", "decided_at": "2026-10-13T08:08:45.996465+00:00"}
```

**Status codes and exact messages** (observed). The controller checks the criteria first, then the opportunity, then the freeze:

| Code | When | Body |
|---|---|---|
| 200 | Recorded | The new decision row |
| 422 | A criterion id that is not in `go_no_go.json` | `{"detail": "Unknown criteria: ['price']."}` (pattern `Unknown criteria: [<ids>].`); checked even before the opportunity |
| 404 | Unknown opportunity | `{"detail": "OPP-9999 not found."}` |
| 409 | No frozen baseline yet | `{"detail": "Freeze the requirements before deciding go or no-go (review page)."}` |
| 422 | `outcome` not `go` or `no_go` | `{"detail":[{"type":"literal_error","loc":["body","outcome"],"msg":"Input should be 'go' or 'no_go'","input":"maybe","ctx":{"expected":"'go' or 'no_go'"}}]}` |
| 422 | A criterion `status` other than `met`, `not_met`, `unknown`, or a missing `id` / `status` | Standard validation body |

The service also holds the message `Unknown criterion or judgement: <id> = <status>.`; the checks above refuse such input first, so it cannot be reached through the API.

**Side effects.**

- Table `decision`: one inserted row (kind `go_no_go`), with the evidence and the summary stored as shown.
- Table `audit_event`: action `decided`, entity `go_no_go`, entity id = the outcome (`go` or `no_go`), data `{"units": [...], "rationale": "...", "criteria": [...]}`.
- Table `opportunity`: status set through the opportunities module's forward-only status rule, with a second audit event (action `status`, entity `opportunity`, data `{"before", "after"}`):
  - `no_go` stops the bid from any status before `submitted`.
  - `go` after `no_go` resumes at the status the stop replaced, read from the audit log (for example back to `dispatched`), or `go` when the stop came earlier.
  - `go` on a frozen opportunity moves it to `go`; a repeated or late `go` (for example after `dispatched`) does not move the status back.
- Observed on the private copy: `frozen` -> `no_go` -> `go`, then dispatch -> `dispatched`.
- No work package changes. A `no_go` does not withdraw dispatched work.

**Model calls.** None.

**Preconditions.** The requirements are frozen (at least one baseline). Participation is **not** required by the API; without it, `units` is `[]` and a later dispatch sends everything to the bid desk.

**Postconditions.** This row is the latest go / no-go. Dispatch (section 12.1) is allowed only while the latest outcome is `go`.

**Called by.** Bid decision screen, card "2. Go / no-go". The form sends `outcome`, `rationale` (the **Rationale** field) and one criterion per row of the criteria table, taken from the "Your judgement" drop-down (default: the stored judgement, else Layer 0's assessment) and the **Note** field. Buttons **Go** and **No-go** are disabled until `evidence.frozen` is true (hint "Freeze the requirements first."). **No-go** first asks for confirmation: title "Record no-go?", button "Record no-go", message "The opportunity is marked no-go. Nothing is sent to the units; a later go decision can still overrule it." Toasts: `Decision recorded: go.` or `Decision recorded: no-go.` The screen then reloads the decisions payload and refreshes the header stepper and status badge.

**Example.**

```bash
curl -s -X POST http://127.0.0.1:8000/api/opportunities/OPP-0001/go-no-go -H 'X-Actor: Bid%20Manager' \
  -H 'Content-Type: application/json' \
  -d '{"outcome": "go", "rationale": "In scope for the participating units.", "criteria": [{"id": "coverage", "status": "met", "note": "checked"}, {"id": "cost_budget", "status": "unknown"}]}'
```

## 12. Work Package Endpoints

The work-packages module (`app/modules/workpackages/`) sends each frozen requirement to the business units that answer it, collects each unit's checklist answer, and lets the bid manager validate or return it. A **work package** is a unit's set of assignments. The **bid desk** is a pseudo-unit with code `BID` for requirements the bid manager answers personally (commercial, submission, legal and other non-product items). The five endpoints are Implemented and tagged `workpackages` in the OpenAPI document.

**Error mapping.** Every endpoint of this module maps service errors the same way (`_call` in `app/modules/workpackages/controller.py`): unknown item -> 404, wrong person -> 403, wrong state -> 409. Request-validation errors are 422 as everywhere.

**Who may do what.** There is no sign-in; the acting person is the `X-Actor` header (URL-encoded; default `Bid Manager`). The rules compare that name exactly:

| Action | Allowed actor | Otherwise |
|---|---|---|
| Answer a unit's item (section 12.4) | That unit's product manager or design engineer, as named in `business_units.json` (for example `Crown Product Manager`, `EP² Design Engineer`) | 403 `Only <bu>'s product manager or design engineer can answer this item.` |
| Answer a bid-desk item (section 12.4) | `Bid Manager` only | 403 `Only BID's product manager or design engineer can answer this item.` (the message names "BID" although only the Bid Manager may answer) |
| Validate or return (section 12.5) | `Bid Manager` only, also for bid-desk answers the Bid Manager wrote | 403 `Only the Bid Manager validates or returns answers.` |
| Dispatch, read inboxes, download a hand-off | Anyone | (no check) |

**The `assignment` table.** One row per requirement and unit (`app/modules/workpackages/models.py`); the pair (`req_id`, `bu`) is unique, so a withdrawn row is reopened, never duplicated.

| Field | Type | Meaning |
|---|---|---|
| `id` | integer | Assignment id; the `{assignment_id}` of sections 12.4 and 12.5. |
| `opportunity_id` | string | Opportunity id. |
| `req_id` | string | Requirement id. |
| `bu` | string | Unit code, or `BID`. |
| `owner` | string | The unit's design engineer, or `Bid Manager` for `BID`. |
| `status` | string | `assigned`, `submitted`, `validated`, `returned` or `withdrawn`. |
| `compliance` | string or null | `met`, `partial`, `not_met` or `exception`; null until answered. |
| `product_ref` | string or null | What meets it; set at dispatch to the unit's first matched product, changed by an answer. |
| `response` | string | How it is met (`""` until answered). |
| `responded_by` / `responded_at` | string / datetime, or null | Who answered and when. |
| `validated_by` | string or null | Who validated or returned it (also set when a change document returns it). |
| `validation_note` | string | The return note, or the change note; cleared to `""` by a later validation. |
| `created_at` | datetime | When it was dispatched. |

### 12.1 POST /api/opportunities/{opp_id}/dispatch

**Purpose.** One-step dispatch: create one assignment per participating matched unit (or the bid desk) for every frozen, approved requirement. The call is repeatable: it adds new work, withdraws work that no longer fits the matches or the participation, and reopens withdrawn work that fits again.

**Path parameters.**

| Name | Type | Meaning |
|---|---|---|
| `opp_id` | string | Opportunity id. |

**Query parameters.** None. **Request body.** None.

**What the call does, step by step** (`workpackages.service.dispatch`):

1. Refuses when the opportunity has no frozen baseline, then when the latest go / no-go is missing or not `go`.
2. Reads the participating units (latest participation; none -> empty set), the current matches (rejected ones excluded) and every existing assignment of the opportunity, whatever its status.
3. Works out the wanted assignments. For every current requirement with status `approved` and a baseline number: for each unit in its match's `units` that participates, one assignment to that unit, with the unit's **first** product of that match as `product_ref`. If no unit qualifies (no match, a match with no units, a rejected match, or none of its units participates), one assignment to the bid desk `BID` with no `product_ref`. Proposed matches nobody reviewed are dispatched like accepted ones.
4. Creates each wanted assignment that does not exist yet (status `assigned`, owner = the unit's design engineer, or `Bid Manager` for `BID`). A wanted assignment that exists as `withdrawn` is reopened (status `assigned`; its earlier answer is kept for reference). A wanted assignment that exists in any other status is left untouched, with its answer.
5. Withdraws every existing assignment that is not wanted any more and is not already withdrawn (status `withdrawn`).
6. Commits. If another dispatch of the same opportunity got there first (the unique pair is violated), everything is rolled back and the call is refused (409).
7. Sets the opportunity status to `dispatched` (forward-only; a no-op when it already is).

Consequences: with no participation recorded, every requirement goes to the bid desk; a product requirement whose unit does not take part goes to the bid desk.

**Response (200).**

| Field | Type | Meaning |
|---|---|---|
| `created` | integer | Number of **new** assignment rows. Reopened and withdrawn rows are not counted. |

Real examples (private copy, own opportunity `OPP-0005`):

| Situation | Response |
|---|---|
| First dispatch: 10 frozen requirements, participation JETCOOL, FPM, ANORD | `{"created": 10}` (7 unit assignments, 3 bid-desk assignments; the CLOUD-matched requirement went to the bid desk) |
| Same call again, nothing changed | `{"created": 0}` |
| CLOUD added to the participation, then dispatch | `{"created": 1}`; the bid-desk assignment of that requirement was withdrawn |
| CLOUD removed again, then dispatch | `{"created": 0}`; the CLOUD assignment was withdrawn and the bid-desk one reopened |

**Status codes and exact messages** (all observed):

| Code | When | Body |
|---|---|---|
| 200 | Dispatched | `{"created": <n>}` |
| 409 | No frozen baseline (also for an unknown opportunity) | `{"detail": "Freeze the requirements before dispatch (review page)."}` |
| 409 | No go / no-go yet, or the latest is `no_go` | `{"detail": "Dispatch needs a 'go' decision first (decisions page)."}` |
| 409 | A concurrent dispatch of the same opportunity won | `{"detail": "Dispatch is already running for this opportunity; refresh and try again."}` |

**Side effects.**

- Table `assignment`: rows inserted, reopened (`assigned`) or withdrawn (`withdrawn`).
- Table `audit_event`, entity `assignment`, entity id = the requirement id:
  - `assigned`, data `{"bu", "owner"}`, per new row;
  - `reopened`, data `{"bu"}`, per reopened row;
  - `withdrawn`, data `{"bu", "was": <old status>}`, per withdrawn row.
- Table `opportunity`: status `dispatched`, with an audit event `status` (`{"before", "after"}`) when it changes.

**Model calls.** None.

**Preconditions.** Frozen baseline; latest go / no-go is `go`. In practice also a participation and reviewed matches.

**Postconditions.** Each unit's inbox (section 12.3) lists its active assignments; the Traceability pane 3 shows them per requirement; the bid decision's workload and summary count them.

**Called by.**

- Bid decision screen, card "3. Send the work to the units" (shown only when the latest go / no-go is `go`), button **Dispatch work packages to units**, busy text "Dispatching…", hint "Repeat after changing matches or participation: new work is sent, work that no longer fits is withdrawn." Toasts: `<n> new assignment(s) sent to the units.` or, when `created` is 0, `Nothing new to send: every unit already has its work.` The screen then reloads the decisions payload and refreshes the header stepper and status badge.
- Changes module, after a change set is applied, when work had been dispatched before and the latest go / no-go is `go` (see 04-api-view.md, section 8). A refusal is reported in the change set's result note as `Not dispatched: <message>` instead of failing.
- The demo seed script.

**Example.**

```bash
curl -s -X POST http://127.0.0.1:8000/api/opportunities/OPP-0001/dispatch -H 'X-Actor: Bid%20Manager'
```

### 12.2 GET /api/opportunities/{opp_id}/handoff/{bu}

**Purpose.** The hand-off document for one unit and one opportunity: every active assignment of the unit, grouped by the route it takes into the unit's own systems, as a JSON file download. Every item needs a person to complete it; nothing in it is a configuration or a design.

**Path parameters.**

| Name | Type | Meaning |
|---|---|---|
| `opp_id` | string | Opportunity id. |
| `bu` | string | Unit code (case-sensitive), for example `CROWN`. `BID` is refused. |

**Query parameters.** None. **Request body.** None.

**Response (200).** `Content-Type: application/json` and `Content-Disposition: attachment; filename="<opp_id>-<bu>-handoff.json"` (observed: `attachment; filename="OPP-0001-CROWN-handoff.json"`). The body:

| Field | Type | Meaning |
|---|---|---|
| `opportunity` | object | `{id, title, customer}`. |
| `document` | string or null | Id of the main RFP document. |
| `unit` | object | `{code, name, default_tier, owner, product_manager}`; `default_tier` from `spinco_layers.json` (`CTO_AUTOMATE`, `ETO_GUIDED` or `ETO_EXCEPTION`; null for EMS and AFS); `owner` is the design engineer. |
| `decision` | object or null | Latest go / no-go: `{outcome, decided_by, decided_at}`. |
| `generated_at` | string | UTC time of this download, ISO format with `+00:00`. |
| `requires_human_completion` | boolean | Always `true`. |
| `stated_facts` | object | The non-null facts of the engineering checks (section 11.1, `checks.facts`), each citing its requirement. |
| `routes` | object | Route key -> `{destination, items}`; routes without items are left out. |
| `note` | string | `Hand-off for the unit's own systems. Every item needs a person: CPQ seeds are starting points, basis-of-design items are captured requirements, not designs.` |

The three routes and how an item is routed:

| Route key | `destination` text | Chosen when |
|---|---|---|
| `cpq_seed` | `Route A: commercial CPQ (configuration seed only; Layer 0 seeds the configurator, it does not configure)` | offering type `CTO`, unless the unit's tier is `ETO_EXCEPTION` |
| `basis_of_design` | `Route B: design engineering (basis of design; captured requirements, not a design)` | offering type `SEMI_CUSTOM` or `ETO`, unless the unit's tier is `ETO_EXCEPTION` |
| `specialist_queue` | `Route C: specialist engineering queue (no design attempted)` | the unit's default tier is `ETO_EXCEPTION`. Only the pending unit EPC has that tier, and it cannot take part, so this route does not occur with the current data. |

One item is produced **per product of this unit** in the requirement's match (a requirement matched to a cold plate and a coolant distribution unit gives one CPQ item and one basis-of-design item). If the match names no product of this unit, one item is made from the assignment's `product_ref`, with the product's usual offering type (or `ETO` when unknown). Item fields:

| Field | Type | Meaning |
|---|---|---|
| `req_id` | string | Requirement id. |
| `source` | string or null | `p. <n>, line <a>` / `p. <n>, lines <a>-<b>`, or `not found in source`. |
| `quote` | string or null | The customer's words. |
| `document` | string or null | The document the requirement comes from: the main RFP, or a change document for requirements added or revised by an addendum. |
| `requirement` | string or null | Normalised requirement text. |
| `category` | string or null | Requirement category. |
| `product_id` | string | Product family. |
| `product` | string or null | Product family name. |
| `offering_type` | string | `CTO`, `SEMI_CUSTOM` or `ETO`. |
| `engineering_flags` | array of strings | Notes of the tier flags for this unit and requirement. |
| `unit_answer` | object | `{status, compliance, product_ref, response (null when empty), validated_by}` of the assignment. |
| `configuration_seed` | object | `cpq_seed` only: `{product_id, bom_lines}`; BOM lines from the catalog (illustrative; `[]` for families without BOM). |
| `basis_of_design` | object | `basis_of_design` only: `{captured_requirement: <quote>, spec_claimed: false, note: "Layer 0 has NOT designed this: captured requirements only."}` |
| `design_attempted` | boolean | `specialist_queue` only: `false`. |

Real example (isolated API, `GET /api/opportunities/OPP-0001/handoff/CROWN`, 107,954 bytes, 5 CPQ items and 94 basis-of-design items; trimmed):

```json
{
  "opportunity": {"id": "OPP-0001", "title": "Switchgear procurement (RFP 2023-20)", "customer": "Syracuse Regional Airport Authority"},
  "document": "OPP-0001-893403680eda",
  "unit": {"code": "CROWN", "name": "Crown Technical Systems", "default_tier": "ETO_GUIDED",
           "owner": "Crown Design Engineer", "product_manager": "Crown Product Manager"},
  "decision": {"outcome": "go", "decided_by": "Bid Manager", "decided_at": "2026-10-13T05:51:50.992007"},
  "generated_at": "2026-10-13T07:41:58.915937+00:00",
  "requires_human_completion": true,
  "stated_facts": {"voltage_stated": {"value": "125 vdc", "req_id": "REQ-0001-0953"},
                   "medium_voltage": {"value": true, "req_id": "REQ-0001-0887"}},
  "routes": {
    "cpq_seed": {"destination": "Route A: commercial CPQ (configuration seed only; Layer 0 seeds the configurator, it does not configure)",
      "items": [{"req_id": "REQ-0001-0480", "source": "p. 63, line 25",
                 "quote": "Provide four-hole NEMA pads for the high-voltage power cables.", "document": "OPP-0001-893403680eda",
                 "requirement": "Include four-hole NEMA pads for high-voltage power cables.", "category": "technical",
                 "product_id": "CROWN-ACC", "product": "MV switchgear accessories", "offering_type": "CTO",
                 "engineering_flags": ["CTO is below CROWN's default ETO_GUIDED: an engineer must confirm this part is genuinely standard."],
                 "unit_answer": {"status": "assigned", "compliance": null, "product_ref": "CROWN-ACC", "response": null, "validated_by": null},
                 "configuration_seed": {"product_id": "CROWN-ACC", "bom_lines": [
                   {"item": "NEMA four-hole terminal pad (illustrative)", "qty": "per cable"},
                   {"item": "Ground ball stud, 1 inch (illustrative)", "qty": "per phase"},
                   {"item": "Lockable utility termination compartment (illustrative)", "qty": "1"}]}},
                "... 5 items"]},
    "basis_of_design": {"destination": "Route B: design engineering (basis of design; captured requirements, not a design)",
      "items": [{"req_id": "REQ-0001-0977", "source": "p. 1, lines 17-19",
                 "quote": "Specification Section 1.1.E, page 56: add the following as item 11. \"The switchgear lineup shall be seismically qualified for the site, ...\"",
                 "document": "OPP-0001-180eb141aec2",
                 "requirement": "The switchgear lineup must be seismically qualified for the site, with the seismic qualification report provided with the submittals.",
                 "category": "technical", "product_id": "CROWN-ARMV", "product": "Arc-resistant metal-clad MV switchgear",
                 "offering_type": "ETO", "engineering_flags": [],
                 "unit_answer": {"status": "assigned", "compliance": null, "product_ref": "CROWN-ARMV", "response": null, "validated_by": null},
                 "basis_of_design": {"captured_requirement": "Specification Section 1.1.E, page 56: add the following as item 11. ...",
                                     "spec_claimed": false, "note": "Layer 0 has NOT designed this: captured requirements only."}},
                "... 94 items; REQ-0001-0887 shows \"unit_answer\": {\"status\": \"returned\", \"compliance\": \"met\", ...} after the addendum"]}
  },
  "note": "Hand-off for the unit's own systems. Every item needs a person: CPQ seeds are starting points, basis-of-design items are captured requirements, not designs."
}
```

`REQ-0001-0977` was added by the addendum, so its `document` is the addendum's id and its `source` is a line of the addendum. In `OPP-0002`, the single JETCOOL assignment (REQ-0002-0005, validated) gives two items: `JETCOOL-PLATE` (CTO) under `cpq_seed`, with BOM line "Cold plate (illustrative)", and `JETCOOL-CDU` (SEMI_CUSTOM) under `basis_of_design`, both with the same `unit_answer`.

**Status codes and exact messages** (observed on the isolated API):

| Code | When | Body |
|---|---|---|
| 200 | Unit has active work in the opportunity | The document above, as a download |
| 404 | Unknown opportunity | `{"detail": "OPP-9999 not found."}` |
| 409 | `bu` is `BID` | `{"detail": "The bid desk answers its items itself; it has no downstream system to hand off to."}` |
| 404 | Unknown unit, or a unit with no active assignment in the opportunity (also the pending unit EPC) | `{"detail": "No work for JETCOOL in OPP-0001."}` (pattern `No work for <bu> in <opp_id>.`) |

**Side effects.** None: nothing is written, no audit event, no status change. `generated_at` changes on every call.

**Model calls.** None.

**Preconditions.** The opportunity was dispatched and the unit has at least one non-withdrawn assignment in it.

**Postconditions.** None.

**Called by.** My work screen of a real unit (`web/app/inbox/[bu]/page.tsx`): the row "Hand-off for this unit's systems (JSON: CPQ seed, basis of design, specialist queue):" holds one plain link per opportunity in the work package, `href="/api/opportunities/<opp>/handoff/<bu>"`, so the browser downloads the file directly. The row ends with "Starting points for people, not a configuration or a design." It is not shown on the bid desk (`/inbox/BID`). The OpenAPI description of the operation carries an internal reference. See `images/11-inbox-CROWN-as-PM.png`.

**Example.**

```bash
curl -s -OJ http://127.0.0.1:8000/api/opportunities/OPP-0001/handoff/CROWN -H 'X-Actor: Bid%20Manager'
```

### 12.3 GET /api/inbox/{bu}

**Purpose.** A unit's work package across **all** opportunities: every non-withdrawn assignment, each with the latest version of its requirement. With `BID` it returns the bid desk's work package.

**Path parameters.**

| Name | Type | Meaning |
|---|---|---|
| `bu` | string | `BID`, or a unit code known to the catalog, case-sensitive. The pending unit EPC is accepted (it has no work). |

**Query parameters.** None. **Request body.** None.

**Response (200).**

| Field | Type | Meaning |
|---|---|---|
| `bu` | string | The code asked for. |
| `unit` | object or null | The unit's catalog record (fields of section 9.1); `null` for `BID`. |
| `compliance` | array of strings | The allowed answers, in order: `["met", "partial", "not_met", "exception"]`. |
| `items` | array | Every non-withdrawn assignment of the unit, ordered by opportunity id, then requirement id. Each item = all fields of the `assignment` table plus `requirement`. |
| `items[].requirement` | object or null | The latest version of the requirement: every requirement field (`id`, `req_id`, `version`, `opportunity_id`, `document_id`, `text`, `quote`, `category`, `section`, `page`, `line_start`, `line_end`, `bboxes`, `provenance`, `status`, `derived_from`, `kind`, `parent_id`, `baseline`, `created_by`, `created_at`) plus `source`. `null` if the requirement no longer exists. |

The two variants differ only in `unit` (`null` for `BID`) and in who may answer the items (the table at the top of this section).

Live sizes on the isolated API: `BID` 251 items (OPP-0001: 245 assigned; OPP-0002: 5 assigned, 1 submitted; 323,725 bytes); `CROWN` 99 items (97 assigned, 1 submitted, 1 returned by the addendum); `EP2` 5 assigned; `JETCOOL` 1 validated; `ANORD` 1 submitted; `FPM` 1 and `CLOUD` 1 assigned; `EPC`, `EMS`, `AFS` none.

Real example (isolated API, `GET /api/inbox/CROWN`, one item, requirement quote trimmed). This assignment was validated before Addendum No. 1 and returned by it with a change note:

```json
{
  "bu": "CROWN",
  "unit": {"code": "CROWN", "name": "Crown Technical Systems", "pillar": "Critical Power", "status": "active", "focus": "...",
           "product_manager": "Crown Product Manager", "design_engineer": "Crown Design Engineer", "source_url": "..."},
  "compliance": ["met", "partial", "not_met", "exception"],
  "items": [
    {"id": 134, "opportunity_id": "OPP-0001", "req_id": "REQ-0001-0887", "bu": "CROWN", "owner": "Crown Design Engineer",
     "status": "returned", "compliance": "met", "product_ref": "CROWN-ARMV",
     "response": "Two-section 15 kV arc-resistant metal-clad lineup offered.",
     "responded_by": "Crown Design Engineer", "responded_at": "2026-10-13T05:51:51.150031", "validated_by": "Bid Manager",
     "validation_note": "Changed by rfp_syracuse_addendum_1.pdf: sub-requirement REQ-0001-0332 now reads: Switchgear must include twenty (20) 15kV vacuum circuit breaker positions, meters, switches, VT’s, and CT’s.",
     "created_at": "2026-10-13T05:51:51.120144",
     "requirement": {"id": 887, "req_id": "REQ-0001-0887", "version": 1, "opportunity_id": "OPP-0001", "document_id": "OPP-0001-893403680eda",
                     "text": "Switchgear components and accessories",
                     "quote": "This Specification covers the manufacturer, furnishing, delivering, and testing of a Metal Clad Switchgear lineup ...",
                     "category": "technical", "...": "...", "source": "p. 55, lines 7-65"}},
    "... 99 items in total"
  ]
}
```

**Status codes and exact messages** (observed):

| Code | When | Body |
|---|---|---|
| 200 | `BID` or a known unit code | The object above |
| 404 | Unknown code, including a wrong case such as `crown` | `{"detail": "Unit NOPE not found."}` (pattern `Unit <bu> not found.`) |

**Side effects.** None. **Model calls.** None. **Preconditions / postconditions.** None.

**Called by.**

- My work screen (`web/app/inbox/[bu]/page.tsx`, route `/inbox/<bu>`): on page load, when the tab regains focus and after every answer, validation or return. The title is "My work: <unit name>" or "My work: Bid desk (bid manager)". `compliance` fills the **Compliance** drop-down of each answer form; the opportunity ids of `items` give the "Open the RFP:" links and the hand-off links; `requirement` gives the requirement text, quote and "show highlighted source" link (or an "unanchored" badge when the quote was not located on the page, and "This requirement no longer exists in the opportunity." when `requirement` is null). The same screen also reads the portfolio endpoint for the unit switcher (see 04-api-view.md, section 15). See `images/10-inbox-BID.png`, `images/11-inbox-CROWN-as-PM.png`, `images/12-inbox-EP2-as-DE.png`, `images/13-inbox-EMS-empty.png` and `images/38-inbox-CROWN-as-DE.png`.
- Walkthrough chapters "unit inboxes" and "knowledge base" read `/api/inbox/CROWN` to find rows to point at.

**Example.**

```bash
curl -s http://127.0.0.1:8000/api/inbox/CROWN -H 'X-Actor: Bid%20Manager'
curl -s http://127.0.0.1:8000/api/inbox/BID -H 'X-Actor: Bid%20Manager'
```

### 12.4 POST /api/assignments/{assignment_id}/respond

**Purpose.** A unit (or, for the bid desk, the Bid Manager) answers one assigned or returned item: compliance, what meets it and how. The item becomes `submitted` and waits for validation.

**Path parameters.**

| Name | Type | Constraints | Meaning |
|---|---|---|---|
| `assignment_id` | integer | `1 <= assignment_id <= 2147483647` | Assignment id (`items[].id` of section 12.3). |

**Request body** (`RespondIn`):

| Field | Type | Required | Constraints | Default | Meaning |
|---|---|---|---|---|---|
| `compliance` | string | yes | `met`, `partial`, `not_met` or `exception` | none | The unit's answer. |
| `product_ref` | string | no | none | `""` | Product or configuration that meets it. An empty value **keeps** the current `product_ref` (the product set at dispatch or by an earlier answer). |
| `response` | string | no | none (an empty text is accepted) | `""` | How it is met. |

**Response (200).** `{"ok": true}`.

**Status codes and exact messages** (observed on the private copy). Checked in this order: the item, the person, the state.

| Code | When | Body |
|---|---|---|
| 200 | Answer stored | `{"ok": true}` |
| 404 | No assignment with that id | `{"detail": "Assignment 999999 not found."}` |
| 403 | Unit item, actor is not that unit's product manager or design engineer (also the Bid Manager, or no `X-Actor` header) | `{"detail": "Only JETCOOL's product manager or design engineer can answer this item."}` (pattern `Only <bu>'s product manager or design engineer can answer this item.`) |
| 403 | Bid-desk item, actor is not `Bid Manager` | `{"detail": "Only BID's product manager or design engineer can answer this item."}` |
| 409 | Item is `submitted`, `validated` or `withdrawn` | `{"detail": "This item is submitted; only assigned or returned items can be answered."}` (pattern `This item is <status>; only assigned or returned items can be answered.`) |
| 422 | `compliance` missing or not one of the four values | `{"detail":[{"type":"literal_error","loc":["body","compliance"],"msg":"Input should be 'met', 'partial', 'not_met' or 'exception'","input":"yes",...}]}` or `type` `missing` |
| 422 | `assignment_id` out of range | `Input should be greater than or equal to 1` / `... less than or equal to 2147483647` |

**Side effects.**

- Table `assignment`: `compliance`, `product_ref` (unless empty), `response`; `status` `submitted`; `responded_by` = actor; `responded_at` = now (UTC).
- Table `audit_event`: action `responded`, entity `assignment`, entity id = the requirement id, data `{"bu", "compliance"}`.

**Model calls.** None.

**Preconditions.** The item is `assigned` or `returned`; the actor may answer it.

**Postconditions.** The item is `submitted`: the unit can no longer edit it, it counts as "answer, not yet validated" in the go / no-go summary, and the Bid Manager can validate or return it. The earlier `validation_note` of a returned item stays until the next validation.

Real sequence (private copy, own opportunity; assignment 365 belongs to JETCOOL):

| Request | Actor | Result |
|---|---|---|
| `{"compliance": "met", "response": "x"}` | Bid Manager | 403 `Only JETCOOL's product manager or design engineer can answer this item.` |
| `{"compliance": "met", "product_ref": "", "response": "Direct-to-chip cold plates ..."}` | JetCool Product Manager | 200; `product_ref` kept as `JETCOOL-PLATE` |
| `{"compliance": "partial"}` | JetCool Product Manager | 409 `This item is submitted; only assigned or returned items can be answered.` |
| after a return: `{"compliance": "met", "product_ref": "JETCOOL-PLATE", "response": "Cold plates plus a 300 kW in-rack CDU per rack pair."}` | JetCool Design Engineer | 200 |

**Called by.** My work screen (`web/app/inbox/[bu]/page.tsx`), only when the acting person may answer (the unit's product manager or design engineer; on the bid desk the Bid Manager) and only on `assigned` or `returned` rows:

- Row form: **Compliance** drop-down (default the stored answer, else `met`), **Product / configuration** input (default `product_ref`), **How it is met** text area, button **Submit**. The form posts its three fields as JSON. Toast `<REQ> submitted for validation.` A returned row shows an alert "Returned" with "by <validated_by>: <validation_note>" above the form.
- Header button **Submit all answered rows**: posts every open row whose "How it is met" is not empty, one after the other. Each row then shows "sent" or "not sent: <error>". Toasts: `<n> row(s) submitted for validation.`, `<sent> row(s) sent, <failed> not sent; see the rows.`, or `Nothing to send: type an answer in at least one row first.`

Other actors see the work package read-only, with the note "You are acting as <name>: you can read this work package but not answer it. Switch with “Acting as” in the top bar." See `images/38-inbox-CROWN-as-DE.png` and `images/12-inbox-EP2-as-DE.png`.

**Example.**

```bash
curl -s -X POST http://127.0.0.1:8000/api/assignments/139/respond -H 'X-Actor: Crown%20Design%20Engineer' \
  -H 'Content-Type: application/json' \
  -d '{"compliance": "met", "product_ref": "CROWN-ACC", "response": "Standard catalog termination kit."}'
```

An actor name with non-ASCII characters must be URL-encoded, for example `-H 'X-Actor: EP%C2%B2%20Design%20Engineer'`.

### 12.5 POST /api/assignments/{assignment_id}/validate

**Purpose.** The Bid Manager validates a submitted answer, or returns it to the unit with a note saying why.

**Path parameters.**

| Name | Type | Constraints | Meaning |
|---|---|---|---|
| `assignment_id` | integer | `1 <= assignment_id <= 2147483647` | Assignment id. |

**Request body** (`ValidateIn`):

| Field | Type | Required | Constraints | Default | Meaning |
|---|---|---|---|---|---|
| `ok` | boolean | yes | none | none | `true` validates; `false` returns the answer to the unit. |
| `note` | string | no | must contain non-blank text when `ok` is `false` | `""` | Why it is returned. The unit sees it. Stored also on validation (normally empty). |

**Response (200).** `{"ok": true}`.

**Status codes and exact messages** (observed on the private copy). Request validation first, then the item, the person and the state:

| Code | When | Body |
|---|---|---|
| 200 | Validated or returned | `{"ok": true}` |
| 422 | `ok` is `false` and `note` is empty or blank | `{"detail":[{"type":"value_error","loc":["body"],"msg":"Value error, Say why the answer is returned (note).","input":{"ok":false,"note":"  "},"ctx":{"error":{}}}]}`; the screen shows `Value error, Say why the answer is returned (note).` |
| 422 | `ok` missing | `type` `missing`, `loc` `["body","ok"]`, `msg` `Field required` |
| 404 | No assignment with that id | `{"detail": "Assignment 999999 not found."}` |
| 403 | Actor is not `Bid Manager` (also the unit's own people: no self-validation) | `{"detail": "Only the Bid Manager validates or returns answers."}` |
| 409 | Item is not `submitted` | `{"detail": "This item is assigned; only submitted answers can be validated or returned."}` (pattern `This item is <status>; only submitted answers can be validated or returned.`) |

The service also holds the message `A returned answer needs a note saying why (design 7.5).` (409); the request validation above refuses a blank return note first, so it cannot be reached through the API.

**Side effects.**

- Table `assignment`: `status` `validated` (ok) or `returned` (not ok); `validated_by` = actor; `validation_note` = the note (a validation with an empty note clears an earlier return note).
- Table `audit_event`: action `validated` or `returned` (the new status), entity `assignment`, entity id = the requirement id, data `{"bu", "note"}`.

**Model calls.** None.

**Preconditions.** The item is `submitted`; the actor is `Bid Manager`.

**Postconditions.** `validated`: the answer counts as "validated answer" in the go / no-go summary and appears in the final response outputs (see 04-api-view.md, section 14). `returned`: the unit can answer it again (section 12.4).

Real sequence (private copy, assignment 365):

| Request | Actor | Result |
|---|---|---|
| `{"ok": true}` | JetCool Product Manager | 403 `Only the Bid Manager validates or returns answers.` |
| `{"ok": false, "note": "  "}` | Bid Manager | 422 `Value error, Say why the answer is returned (note).` |
| `{"ok": false, "note": "Say which CDU size is offered."}` | Bid Manager | 200; status `returned` |
| (unit answers again) `{"ok": true, "note": ""}` | Bid Manager | 200; status `validated`, note cleared |
| `{"ok": true}` | Bid Manager | 409 `This item is validated; only submitted answers can be validated or returned.` |

**Called by.** My work screen, status cell of each `submitted` row, only for the Bid Manager:

- **Validate**: posts `{"ok": true, "note": ""}`; toast `<REQ> validated.`
- **Return**: opens a text area ("Why is it returned? The unit sees this note.") with **Return with note** (disabled until text is typed) and **Cancel**; posts `{"ok": false, "note": <text>}`; toast `<REQ> returned to the unit.`

The Bid Manager also sees "<n> submitted answer(s) waiting for validation." and, in the work-package switcher, "<n> to validate" per unit. See `images/10-inbox-BID.png` and `images/11-inbox-CROWN-as-PM.png`.

**Example.**

```bash
curl -s -X POST http://127.0.0.1:8000/api/assignments/139/validate -H 'X-Actor: Bid%20Manager' \
  -H 'Content-Type: application/json' -d '{"ok": false, "note": "Name the breaker model."}'
```

## 13. Knowledge Endpoints

Module `knowledge` (`app/modules/knowledge/controller.py`, `service.py`). Status: Implemented. Error mapping: `LookupError` → 404, `PermissionError` → 403, `ValueError` → 409.

People send a requirement, a validated answer or a decision rationale to the knowledge base; the curator (in the proof of concept, the person acting as **Bid Manager**) approves or rejects each item. Approved items are appended to `<STORE_DIR>/knowledge_learned.json` and join the long-term retrieval index used by catalog search, matching evidence and the response outline. Nothing enters the knowledge base without a person's approval.

The knowledge item object is described in section 17.

### 13.1 POST /api/knowledge

Queues one item for the curator.

Request body (`SendIn`):

| Field | Type | Required | Constraints | Meaning |
|---|---|---|---|---|
| `kind` | string | yes | `requirement`, `response`, `decision` | What is sent |
| `ref` | string | yes | 1..40 characters | `requirement`: a requirement ID; `response`: an assignment ID (validated answers only); `decision`: a decision ID |
| `note` | string | no | max 2000 | Why the sender thinks it is worth keeping |

What is captured per kind:
- `requirement`: the requirement text; source "`<req_id>`, `<source>`"; unit `BID`; empty response.
- `response`: the requirement text; response "`<Met | Partially met | Not met | Exception>`. `<answer>` Offered: `<product name>`."; the answering unit.
- `decision`: "Go/no-go decision (`<opp>`)" or "Participation decision (`<opp>`)"; response "`<outcome or unit list>`: `<rationale>`"; source "`<opp>`, decided by `<person>`".

Response 200 (the new item, status `queued`):

```json
{"id":1,"kb_id":"KB-0001","kind":"requirement","source_ref":"REQ-0001-0002","opportunity_id":"OPP-0001","bu":"BID","requirement":"Proposers must only contact the designated person or email regarding this procurement.","response":"","source":"REQ-0001-0002, p. 1, lines 8-11","note":"Standard restricted-contact clause; reuse the wording in future responses.","status":"queued","sent_by":"Bid Manager","sent_at":"...","reviewed_by":null,"reviewed_at":null,"review_note":""}
```

Errors: 404 `Requirement REQ-… not found.` / `Answer N not found.` / `Decision N not found.`; 409 `Only validated answers go to the knowledge base.`; 409 `This decision has no rationale to keep.`; 409 `Already queued as KB-0001.` (or `Already approved as …`; a rejected item may be sent again and gets a new ID); 422 validation.

Side effects: `knowledge_item` row with the next ID `KB-nnnn` (never reused); audit `sent` (entity `knowledge`, data `kind`, `ref`).

Called by: the **Send to knowledge base** link (component `SendToKnowledge`) on Traceability pane 2 (selected requirement), Traceability pane 3 (validated answers), the Response outline (validated answers) and the Bid decision screen (participation and go/no-go rationales); walkthrough one-click examples.

### 13.2 GET /api/knowledge

The curator's queue and the knowledge-base status.

Query parameter: `status` (optional): `queued`, `approved` or `rejected`; any other value returns 422.

Response 200:

```json
{"items":[{"id":1,"kb_id":"KB-0001","kind":"requirement","source_ref":"REQ-0001-0002","status":"queued","...":"other fields"}],
 "curator":"Bid Manager","learned":0,"index":"embeddings"}
```

`items` newest first; `learned` = number of approved items in the long-term index; `index` = the long-term index mode (`embeddings` or `keywords`).

Called by: Knowledge base screen (no status parameter; the tabs **Waiting**, **Approved**, **Rejected** filter in the browser).

### 13.3 GET /api/opportunities/{opp_id}/knowledge

What has already been sent from this opportunity, so the screens can show "sent" badges instead of the link.

Response 200: a map `"<kind>:<ref>" → status`, for example:

```json
{"requirement:REQ-0001-0002":"queued"}
```

An opportunity with nothing sent, or an unknown opportunity, returns `{}` (no 404).

Called by: Traceability, Bid decision and Response outline screens, alongside their main data and again after a successful send.

### 13.4 POST /api/knowledge/{kb_id}/review

The curator approves or rejects a queued item.

Request body (`ReviewIn`):

| Field | Type | Required | Constraints | Meaning |
|---|---|---|---|---|
| `approve` | boolean | yes | - | true approves, false rejects |
| `note` | string | no | max 2000 | Required (not blank) to reject |
| `response` | string or null | no | max 8000 | On approval, replaces the stored response (the curator may tidy it) |

Response 200: the item with `status` `approved` or `rejected`, `reviewed_by`, `reviewed_at`, `review_note`.

Errors: 404 `KB-0009 not found.`; 403 `Only the knowledge curator (in the PoC, the Bid Manager) approves knowledge.`; 409 `KB-0001 is already approved.`; 409 `A rejection needs a note saying why.`; 422 validation.

Side effects: audit `approved` or `rejected` (data `note`). On approval, after the commit, the item is appended to `knowledge_learned.json` and the long-term index cache is cleared, so the next search includes it as a past response (marked learned).

Called by: Knowledge base screen, per queued item: **Approve into the knowledge base** and **Reject** (visible only to the curator).

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/KB-0001/review -H 'X-Actor: Bid%20Manager' \
  -H 'Content-Type: application/json' -d '{"approve": true, "note": "Standard clause"}'
```

## 14. Consolidation Endpoints

Module `consolidation` (`app/modules/consolidation/controller.py`, `service.py`, `excel.py`, `agent.py`). Status: Implemented. This module has no table: everything is computed on each request from requirements, matches, assignments, the catalog and (for the outline) the frozen model answers. Unknown opportunity → 404 `Opportunity OPP-… not found.` Download file names use the opportunity ID with any character other than letters, digits and `-` replaced by `_`.

A requirement is **answered** when every assignment for it is validated; `pending` when it has assignments not all validated; `not_assigned` when it has none. Anything not answered blocks completion.

### 14.1 GET /api/opportunities/{opp_id}/consolidation

Coverage of the final response: one row per current requirement (groups and stand-alone items, not sub-requirements), in RFP order.

Response 200:

```json
{"rows":[{"requirement":{"req_id":"REQ-0001-0001","source":"p. 1, line 5","...":"requirement fields"},
          "match":{"id":1,"bu":null,"offering_type":"NONE","method":"rule","status":"proposed","...":"match fields without evidence"},
          "assignments":[{"id":1,"bu":"BID","owner":"Bid Manager","status":"assigned","...":"assignment fields"}],
          "state":"pending"},
         "... 348 rows in total"],
 "total":348,"answered":1,"blocking":["REQ-0001-0001","REQ-0001-0002","..."]}
```

The match's `evidence` field is removed here (it is shown on the Bid decision screen). A blank opportunity returns `{"rows":[],"total":0,"answered":0,"blocking":[]}`.

Called by: Final response screen (on load and on focus).

### 14.2 GET /api/opportunities/{opp_id}/compliance-matrix.csv

The compliance matrix as CSV for tracking: one row per assignment (a requirement without an assignment still gets one row with empty unit columns), in RFP order.

Response 200: `text/csv; charset=utf-8`, `Content-Disposition: attachment; filename="OPP-0001-compliance-matrix.csv"`. The file starts with a UTF-8 byte order mark (so Excel opens it as UTF-8). A cell that starts like a formula (`=`, `+`, `-`, `@`, tab, carriage return) is prefixed with `'` so it never runs as a formula.

Columns (14): `Requirement ID, Source, Category, Requirement, Quote, Business unit, Product, Offering type, Compliance, Response, Validated by, State, Assignment status, Responded by`. Source is `p. N, lines a-b`, prefixed with the file name when the requirement is anchored in a change document. Compliance holds the stored value (`met`, `partial`, `not_met`, `exception`).

```text
Requirement ID,Source,Category,Requirement,Quote,Business unit,Product,Offering type,Compliance,Response,Validated by,State,Assignment status,Responded by
REQ-0001-0001,"p. 1, line 5",schedule,"Proposals must be submitted by September 15, 2023, 4pm.","Submission Deadline: September 15, 2023 by 4pm",BID,,NONE,,,,pending,assigned,
REQ-0001-0887,"p. 55, lines 7-65",technical,Switchgear components and accessories,"This Specification covers ...",CROWN,CROWN-ARMV,ETO,met,Two-section 15 kV arc-resistant metal-clad lineup offered.,Bid Manager,answered,validated,Crown Design Engineer
```

Called by: Final response screen, link **CSV**.

### 14.3 GET /api/opportunities/{opp_id}/compliance-matrix.xlsx

The compliance matrix as an Excel workbook, written by code from the stored answers (never by a model). Every cell is written as text.

Response 200: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, attachment `OPP-0001-compliance-matrix.xlsx`.

Sheets:

| Sheet | Audience | Content |
|---|---|---|
| `Compliance matrix` | Customer | Row 1 title "Compliance matrix: `<title>`"; row 2 "Customer: … Prepared `<date>` Every requirement traces to its page and lines in the RFP."; header in row 4 (white on navy); columns Requirement ID, RFP reference, Requirement, RFP wording, Compliance, Response, Offered by; one row per requirement in RFP order, group rows bold, each approved sub-requirement indented below its group; Compliance in customer words (Comply, Partially comply, Does not comply, Exception) taking the worst validated answer, or **Open** until every unit's answer is validated, with a coloured fill; only validated answers shown; frozen panes and an auto-filter |
| `Tracking` | Internal | The 14 CSV columns, one row per unit answer, without the CSV's formula guard; frozen header and auto-filter |

Demo: OPP-0001 gives 955 data rows on the customer sheet (162 group rows, 607 sub-requirement rows; 5 Comply, 950 Open) and 348 rows on Tracking.

Called by: Final response screen, button **Download compliance matrix (Excel)**.

### 14.4 GET /api/opportunities/{opp_id}/response-outline

A first draft of the response, chapter by chapter, written by the response-outline agent only from validated answers, with what is still open and references from both retrieval indexes.

Chapters (one per group of requirement categories, empty chapters left out): `technical` "Technical response"; `compliance` "Compliance, legal and contract terms" (compliance, legal); `commercial` "Commercial terms and schedule" (commercial, schedule); `staffing` "Project team and staffing"; `submission` "Submission requirements"; `other` "Other requirements"; plus an executive summary drafted from the first 40 validated answers.

Response 200 (trimmed):

```json
{"opportunity":{"id":"OPP-0001","title":"Switchgear procurement (RFP 2023-20)","customer":"Syracuse Regional Airport Authority"},
 "total":348,"answered":1,"validated_answers":1,
 "summary":{"drafted":true,"paragraphs":[{"text":"Crown Technical Systems proposes to supply a two-section 15 kV arc-resistant metal-clad lineup ...","sources":["REQ-0001-0887"]}],"gaps":["Confirm compliance with all specific requirements stated in the RFP.","..."],"dropped":0,"note":""},
 "chapters":[{"id":"technical","title":"Technical response","total":146,"answered":1,
   "draft":{"drafted":true,"paragraphs":[{"text":"The proposer offers a two-section 15 kV arc-resistant metal-clad lineup ...","sources":["REQ-0001-0887"]}],"gaps":["..."],"dropped":0,"note":""},
   "material":[{"assignment_id":134,"req_id":"REQ-0001-0887","source":"p. 55, lines 7-65","bu":"CROWN","unit":"Crown Technical Systems","compliance":"Comply","product":"Arc-resistant metal-clad MV switchgear","requirement":"Switchgear components and accessories","wording":"This Specification covers ...","response":"Two-section 15 kV arc-resistant metal-clad lineup offered."}],
   "exceptions":[],
   "open":[{"req_id":"REQ-0001-0084","source":"p. 10, lines 27-30","text":"Proposer's approach to service management and planning will be evaluated.","state":"pending"},"... 145 in total"],
   "references":{"rfp":[{"page":25,"line_start":15,"line_end":18,"text":"..."}],"past":[],"mode":{"rfp":"embeddings","knowledge":"embeddings"}}},
   "... 5 chapters in total"],
 "note":"A first draft for the bid manager to edit, written only from validated answers; every paragraph cites its requirements. Writing the final response stays a human task."}
```

`draft.drafted` is false with a `note` when there is nothing to draft (`No validated answer yet.`) or no model answer is available offline (`Draft not refreshed: the model service is not connected in this demo, so the validated answers are shown as they are.`). A paragraph without a valid citation is dropped and counted in `dropped`. `exceptions` lists validated answers whose customer word is not "Comply".

Model calls: task `draft_outline`, one call per chapter with validated answers plus one for the summary (answered from the frozen cache when available). Synchronous.

Called by: Response outline screen (on load and focus).

### 14.5 GET /api/opportunities/{opp_id}/response-outline.md

The same outline as Markdown for the bid manager to edit (recomputed on each request).

Response 200: `text/markdown; charset=utf-8`, attachment `OPP-0001-response-outline.md`. Layout: `# Response outline: <title>`, a DRAFT line with the answered count, `## Executive summary`, then per chapter `## <n>. <title>`, "`<answered>` of `<total>` requirements answered.", the paragraphs with their requirement IDs in brackets (or "_Not drafted: …_"), "- To add or confirm: …" gaps, `### Validated answers` and `### Still open (<count>)` lists.

Called by: Response outline screen, button **Download outline (Markdown)**.

## 15. Trace Endpoints

Module `trace` (`app/modules/trace/controller.py`, `service.py`). Read-only; no table. Status: Implemented.

### 15.1 GET /api/portfolio

Every opportunity, newest first, with its requirement count and each unit's progress (assignments total, submitted, validated). This is the opportunity list of the system (there is no `GET /api/opportunities` list endpoint).

Response 200:

```json
[{"opp":{"id":"OPP-0002","title":"AI training campus, Phase 1 (multi-unit sample)","customer":"[Hyperscale Customer] (fictional)","customer_type":"hyperscaler","status":"dispatched","created_by":"Bid Manager","created_at":"2026-10-13T05:51:51.165775"},
  "requirements":10,
  "progress":{"CLOUD":{"total":1,"submitted":0,"validated":0},"BID":{"total":6,"submitted":1,"validated":0},"FPM":{"total":1,"submitted":0,"validated":0},"JETCOOL":{"total":1,"submitted":1,"validated":1},"ANORD":{"total":1,"submitted":1,"validated":0}}},
 {"opp":{"id":"OPP-0001","...":"..."},"requirements":348,"progress":{"BID":{"total":245,"submitted":0,"validated":0},"CROWN":{"total":98,"submitted":2,"validated":1},"EP2":{"total":5,"submitted":0,"validated":0}}}]
```

No parameters, no errors. Called by: Opportunities screen; My work screen (the unit switcher counts answers waiting for validation per unit).

### 15.2 GET /api/opportunities/{opp_id}/trace

Everything the three-pane Traceability screen needs: the RFP pages, every current requirement with its highlight boxes, its product match, the unit and product records, an illustrative bill of materials, the unit assignments and the sub-requirements.

Response 200 (top level): `opp` (opportunity row), `doc` (main document row or null), `rows`, `pages` (`[{page, width, height, unreviewed}]` of the main RFP), `docs` (the main RFP first, then each change document that a current requirement is anchored in: `{id, filename, role, pages}`), `progress` (per unit, as in 15.1).

Each row:

```json
{"req":{"req_id":"REQ-0001-0887","kind":"group","text":"Switchgear components and accessories","source":"p. 55, lines 7-65","bboxes":[[119.52,119.2,537.35,134.07],"... 9 boxes"],"...":"requirement fields"},
 "match":{"id":134,"bu":"CROWN","product_id":"CROWN-ARMV","offering_type":"ETO","method":"agent","status":"proposed","...":"match fields without evidence"},
 "product":{"id":"CROWN-ARMV","name":"Arc-resistant metal-clad MV switchgear","bu":"CROWN","offering_type":"ETO","...":"catalog product"},
 "unit":{"code":"CROWN","name":"Crown Technical Systems","...":"catalog unit"},
 "bom":[{"item":"Vacuum circuit breaker, 15 kV class (illustrative)","qty":"per position"},"... 5 items"],
 "assignments":[{"id":134,"bu":"CROWN","owner":"Crown Design Engineer","status":"validated","compliance":"met","product_ref":"CROWN-ARMV","response":"Two-section 15 kV arc-resistant metal-clad lineup offered.","responded_by":"Crown Design Engineer","validated_by":"Bid Manager","...":"..."}],
 "children":[{"req_id":"REQ-0001-0322","text":"Provide Metal Clad Switchgear and accessories for Syracuse Airport.","source":"p. 55, lines 7-8","document_id":"OPP-0001-893403680eda"},"... 4 in total"]}
```

`req.bboxes` is the screen highlight: for a group it is computed from its active sub-requirements on its own page (so a sub-requirement revised into an addendum or removed no longer marks its old lines). The match's `evidence` is removed. A blank opportunity returns `{"opp":{...},"doc":null,"rows":[],"pages":[],"docs":[],"progress":{}}`.

Known limit: `doc` here includes `path`, the server's absolute location of the stored PDF (the opportunities endpoints remove it).

Errors: 404 `Opportunity OPP-9999 not found.`

Called by: Traceability screen (on load, on focus, after **Match products**, after match decisions). Many screens link to `/opportunities/<id>/trace#<REQ-ID>`; the page selects that requirement on open.

## 16. Front-End Route Handler and Built-In Endpoints

### 16.1 GET /tour-session

Served by the Next.js web app (`web/app/tour-session/route.ts`), not by the API, on port 3000.

Response 200: `{"id":"<random UUID>"}` with `Cache-Control: no-store` (the route is forced dynamic). The ID is created once per web-server process start and kept on the server's global object, so it survives page compiles in development mode.

Purpose: the guided walkthrough compares this ID with the `session` stored in the browser's `localStorage` key `layer0.tour`. A different ID means a new server run: stored progress is reset and the welcome dialog is offered once; the same ID means the person already answered (skipped or done) or is part-way through (resume).

### 16.2 GET /docs, GET /redoc, GET /openapi.json

FastAPI built-ins on the API (port 8000): interactive Swagger UI, ReDoc, and the OpenAPI 3 document (`title` "Layer 0 API - opportunity workflow PoC", version 0.1.0; 48 paths, 51 operations, grouped by tags `opportunities`, `ingestion`, `requirements`, `catalog`, `matching`, `decisions`, `workpackages`, `consolidation`, `knowledge`, `changes`, `trace`).

Known limit: no endpoint declares a response model, so the OpenAPI document shows every 200 response as JSON with an empty schema, including the CSV, Excel, Markdown and PNG downloads. This document (sections 5 to 15 and 17) is the reference for response shapes.

They are not proxied by the web app (`/api/*` only); open them directly on the API port.

## 17. Shared Data Shapes

This section describes every object that more than one endpoint returns. Sections 5 to 16 refer to these shapes by name and describe only what is special to each endpoint. All shapes below are **Implemented**: they are produced by the code at commit 4c6d866, and every example is a real, trimmed answer from the isolated demo API (13 Oct 2026). Where an example is shortened, "..." marks the cut.

The shapes come from two places in the code:

- **Stored rows.** Most objects are a database row turned into JSON by the helper `row()` in `app/core/web.py`. The column definitions are in each module's `models.py`.
- **View objects.** A few objects are built by a service function for the screen: the change set view (`view()` and `item_view()` in `app/modules/changes/service.py`), the requirement history (`history()` in `app/modules/requirements/service.py`), the page layout (`app/modules/ingestion/service.py`) and the catalog entries (read from `data/knowledge_base/*.json` by `app/modules/catalog/service.py`).

### 17.1 How a Stored Row Becomes JSON

The helper `row(obj, *extra)` returns every column of the row's table, in the order the columns are declared in the model, and then any named property passed as `extra`. Only one property is ever added this way: `source` on a requirement (see 17.4). The rules below apply to every row-based shape in this section.

| Rule | Detail |
|---|---|
| Field order | The column order of the model class. Clients must not depend on it; JSON objects are unordered. |
| Date and time values | ISO 8601 text in UTC. A row read back from the database has **no** time-zone suffix (for example `"2026-10-13T05:50:59.097134"`), because SQLite stores the value without its offset. A row created in the same request still carries the offset (for example `"2026-10-13T08:01:33.158637+00:00"` from `POST /api/opportunities`). Treat both forms as UTC. |
| JSON columns | `bboxes`, `derived_from`, `units`, `evidence`, `criteria`, `candidates` and `result` are returned as JSON arrays or objects, never as encoded strings. |
| Missing values | `null`. Text columns that have a default (for example `customer`, `response`, `note`) are an empty string `""` rather than `null`. |
| Numbers | Identifiers of rows are integers (`id`). Business identifiers are strings (`OPP-0001`, `REQ-0001-0042`, `KB-0001`). `confidence` and `score` are decimal numbers. |
| Fields removed before sending | `path` of a document is removed by the opportunities endpoints (it is the server's file path). `evidence` of a match is removed by the trace and consolidation endpoints (it is large). The trace endpoint replaces a requirement's stored `bboxes` with the highlight it computes for the view. Each case is stated with the shape. |
| Extra fields added for one endpoint | For example `existing` on an uploaded document and `requirement` on an inbox item. They are stated with the shape. |

The front end keeps its own copy of these shapes in `web/lib/types.ts`. It types every status as a plain string, so that a new status value from the API never breaks a page.

### 17.2 Opportunity

One engagement: one customer RFP and its own workspace. Table `opportunity`, model `Opportunity` in `app/modules/opportunities/models.py`.

| Field | Type | Meaning |
|---|---|---|
| `id` | string, at most 20 characters | `OPP-` followed by four digits. The next number is the highest existing number plus one (`create()` in `app/modules/opportunities/service.py`). |
| `title` | string, at most 200 characters | Required. Stored with leading and trailing spaces removed. |
| `customer` | string, at most 120 characters | Free text; `""` when not given. |
| `customer_type` | string, at most 40 characters | Free text; `""` when not given. The model comment suggests utility, hyperscaler, neocloud, colocation and silicon; the demo data uses `"public sector"`, `"hyperscaler"`, `"Hyperscaler"` and `"Utility"`. Nothing validates it. |
| `status` | string | One of `new`, `reading`, `review`, `frozen`, `go`, `no_go`, `dispatched`, `consolidating`, `submitted` (`STATUSES`). Only four endpoints move it: reading the requirements sets `review`, freezing sets `frozen`, a go/no-go decision sets `go` or `no_go`, and dispatch sets `dispatched`. `reading`, `consolidating` and `submitted` are defined but no endpoint sets them. The status only moves forward, except that `no_go` can stop a bid and a later `go` resumes it. The transitions are in section 22. |
| `created_by` | string, at most 80 characters | The acting person (the `X-Actor` header; see section 3). |
| `created_at` | date-time | When the opportunity was created. |

Returned by: `POST /api/opportunities` (the new row), `GET /api/opportunities/{opp_id}` (field `opportunity`), `GET /api/portfolio` (field `opp` of each entry) and `GET /api/opportunities/{opp_id}/trace` (field `opp`). The hand-off and the response outline carry a three-field summary `{"id", "title", "customer"}` instead.

Example (`GET /api/opportunities/OPP-0001`, field `opportunity`):

```json
{
  "id": "OPP-0001",
  "title": "Switchgear procurement (RFP 2023-20)",
  "customer": "Syracuse Regional Airport Authority",
  "customer_type": "public sector",
  "status": "dispatched",
  "created_by": "Bid Manager",
  "created_at": "2026-10-13T05:50:59.097134"
}
```

### 17.3 Document

A file received in one opportunity: the main RFP, an addendum, answers to bidders' questions (Q&A), a change document or any other file. Table `document`, model `Document` in `app/modules/opportunities/models.py`. The bytes are stored once under their SHA-256 hash and never modified.

| Field | Type | Meaning |
|---|---|---|
| `id` | string, at most 40 characters | `<opportunity id>-<first 12 hex characters of the SHA-256>`, for example `OPP-0001-893403680eda`. The same file sent to two opportunities is two documents with two IDs. |
| `sha256` | string, 64 hex characters | Hash of the file's bytes. Uploading the same bytes again to the same opportunity returns the existing document instead of a new one. |
| `opportunity_id` | string | The owning opportunity. |
| `filename` | string, at most 255 characters | The name the file was uploaded with (or the sample's file name). |
| `role` | string, at most 20 characters | `main` (the RFP; at most one per opportunity), `addendum`, `qa`, `change` or `other`. The upload form offers these five values. The API does not validate the value of the `role` form field; the changes endpoints always store `change`. |
| `path` | string | Server file path under the store directory. **Removed** from the answers of the opportunities endpoints (`_doc()` in `app/modules/opportunities/controller.py`). It **is** present in the `doc` field of `GET /api/opportunities/{opp_id}/trace`, which returns the full row. |
| `status` | string | `uploaded` (stored, not read yet), `ingesting` (being read), `ingested` (read; layout stored), `failed` (the PDF could not be read; damaged or encrypted) or `unsupported` (not a `.pdf` file name: recorded, never read). |
| `page_count` | integer | `0` until the file has been read; then the number of pages. |
| `received_at` | date-time | When the file was first attached. |

Variants:

- **Upload answer.** `POST /api/opportunities/{opp_id}/documents` and `POST /api/opportunities/{opp_id}/documents/from-sample` return the document without `path`, plus `existing` (boolean): `true` when the same file was already attached, so nothing new was stored.
- **Trace document entry.** `GET /api/opportunities/{opp_id}/trace` also returns `docs`: a list of `{"id", "filename", "role", "pages"}` where `pages` is a list of page-size entries (17.13). The main RFP comes first, then each change document that a current requirement version is anchored in.

Returned by: `GET /api/opportunities/{opp_id}` (field `documents`, in the order received), the two upload endpoints above, and `GET /api/opportunities/{opp_id}/trace` (fields `doc` and `docs`).

Example (`POST /api/opportunities/OPP-0006/documents/from-sample` with `{"name": "hyperscale_rfp"}`, on an opportunity created for this document):

```json
{
  "id": "OPP-0006-c7749ef1bfc9",
  "sha256": "c7749ef1bfc98fabdd250e4f70de53841327a00646d8525352dfaccaa70702ae",
  "opportunity_id": "OPP-0006",
  "filename": "rfp_hyperscale_campus.pdf",
  "role": "main",
  "status": "uploaded",
  "page_count": 0,
  "received_at": "2026-10-13T08:11:44.387686+00:00",
  "existing": false
}
```

### 17.4 Requirement

One requirement line item with its exact source. Table `requirement`, model `Requirement` in `app/modules/requirements/models.py`. A requirement is stored as **versions**: the pair (`req_id`, `version`) is unique, and nothing is edited in place after a freeze. Every endpoint returns the **latest version** of each `req_id` unless stated otherwise.

| Field | Type | Meaning |
|---|---|---|
| `id` | integer | Database row ID of this version. Each version has its own `id`. |
| `req_id` | string, at most 20 characters | `REQ-<opportunity number>-<four digits>`, for example `REQ-0001-0042`. Unique across opportunities. Never reused: the next number is taken over every ID ever issued for the opportunity, including discarded drafts recorded only in the audit log. |
| `version` | integer | `1` for the original. A change document creates version 2, 3 and so on (a revision, or a removal). |
| `opportunity_id` | string | The owning opportunity. |
| `document_id` | string | The document this version is anchored in: the main RFP, or the change document for a requirement added or revised by a change document. A removal keeps the document of the version it removes. |
| `text` | string | Short plain-English restatement of the requirement. The reader agent writes at most about 25 words; a person may edit it before the freeze. A requirement added by a person (`POST .../requirements` or `.../requirements/from-lines`) stores the given text, or the quote when no text is given, cut to 200 characters; a split part without a text takes the first 200 characters of its quote. |
| `quote` | string | The verbatim source text. For a group or a merged requirement, the members' quotes joined with `" … "`. |
| `category` | string, at most 20 characters | One of `technical`, `compliance`, `commercial`, `schedule`, `submission`, `legal`, `staffing` (`CATEGORIES`). |
| `section` | string, at most 200 characters | The RFP section the reader agent saw (for example `"1.9 Submission Due Date"`); `""` for requirements added by a person. |
| `page` | integer or null | Page number in `document_id`, 1-based. `null` when the quote was not found. |
| `line_start`, `line_end` | integer or null | First and last line on that page, 1-based in reading order (headers and footers count as lines). `null` when not found. |
| `bboxes` | array of `[x0, y0, x1, y1]` | Highlight boxes, one per line, in PDF points (1/72 inch) with the origin at the top-left of the page, rounded to 0.01. A group or merged requirement holds the boxes of all its members. `[]` when not found. |
| `provenance` | string | `EXTRACTED`: the quote was found word for word on the page, so `page`, lines and boxes are exact. `UNANCHORED`: the quote was not found; the requirement is kept and flagged, never placed by guess. |
| `status` | string | `proposed` (draft, waiting for approve or reject), `approved`, `rejected`, `split` (replaced by its parts, also used for a group that was ungrouped), `merged` (merged into another requirement), `duplicate` (repeats an earlier quote; see `derived_from`), `removed` (removed by a change document, as a new version). `rejected`, `split`, `merged`, `duplicate` and `removed` are the inactive states. The front-end type lists the first six values only. |
| `derived_from` | array of strings | Requirement IDs this one came from: the original of a split part, the sources of a merge, or the first occurrence of a duplicate. `[]` otherwise. |
| `kind` | string | `item` (one obligation) or `group` (a requirement made of sub-requirements on one page). |
| `parent_id` | string or null | For a sub-requirement: the `req_id` of its group. `null` for groups and stand-alone items. A sub-requirement keeps its parent when a change document revises it. |
| `baseline` | integer or null | The number of the frozen baseline this version entered. `null` for a draft that was never frozen (for example a duplicate). Sub-requirements of an approved group are frozen with the group. |
| `created_by` | string | The person, or the agent and the person who started it: `"reader agent (Bid Manager)"`, `"grouping agent (Bid Manager)"`. The seeded demo data also uses `"reader agent (seed)"`. For a version created by a change document, the person who applied it. |
| `created_at` | date-time | When this version was created. |
| `source` | string (computed) | Not a column. `"p. 5, line 7"` for one line, `"p. 5, lines 6-8"` for several, `"not found in source"` when `page` is `null`. The page is a page of `document_id`. (The exports add the change document's file name in front; the API field does not.) |

How the variants differ:

| Variant | How to recognise it |
|---|---|
| Stand-alone item | `kind` `item`, `parent_id` `null`. |
| Group | `kind` `group`. Its sub-requirements have `parent_id` equal to its `req_id`. Approving or rejecting a group applies to its sub-requirements. |
| Sub-requirement | `kind` `item`, `parent_id` set. Listed by `GET /api/opportunities/{opp_id}/requirements`; left out of the trace rows (they appear as the group's `children`). |
| Revised by a change document | `version` above 1, `document_id` is the change document, `page` and lines point into the change document, `baseline` is the new baseline number. |
| Added by a change document | `version` 1, `document_id` is the change document, `status` `approved`, `baseline` is the new baseline number. |
| Removed by a change document | `version` above 1, `status` `removed`, other fields copied from the removed version. |

Returned by:

| Endpoint | What it returns |
|---|---|
| `GET /api/opportunities/{opp_id}/requirements` | Field `requirements`: the latest version of every requirement, active and inactive, groups and sub-requirements, in document order (main RFP, then change documents in the order received; then page, line, a group before its sub-requirements). |
| `POST /api/opportunities/{opp_id}/requirements`, `POST /api/opportunities/{opp_id}/requirements/from-lines`, `POST /api/opportunities/{opp_id}/requirements/merge` | The one new requirement. |
| `POST /api/requirements/{req_id}/review` | The requirement after the review (latest version). |
| `POST /api/requirements/{req_id}/split` | A list: the new parts. |
| `POST /api/requirements/{req_id}/ungroup` | A list: the released sub-requirements. |
| `GET /api/opportunities/{opp_id}/trace` | Field `req` of each row (active groups and stand-alone items only). Here `bboxes` is the view's highlight: for a group of version 1 that still has sub-requirements on record, the boxes of its active sub-requirements on its own page; otherwise the stored boxes. |
| `GET /api/inbox/{bu}` | Field `requirement` of each item (`null` if the requirement no longer exists). |
| `GET /api/opportunities/{opp_id}/consolidation` | Field `requirement` of each row. |

Example 1, a sub-requirement revised by Addendum No. 1 (`GET /api/opportunities/OPP-0001/requirements`, one element):

```json
{
  "id": 991,
  "req_id": "REQ-0001-0039",
  "version": 2,
  "opportunity_id": "OPP-0001",
  "document_id": "OPP-0001-180eb141aec2",
  "text": "Submit proposals by 09/29/2023 at 4:00 PM via email.",
  "quote": "Section 1.9, Submission Due Date, page 5: replace \"09/15/2023 by 4:00PM\" with \"09/29/2023 by 4:00PM\".",
  "category": "schedule",
  "section": "1.9 Submission Due Date",
  "page": 1,
  "line_start": 12,
  "line_end": 13,
  "bboxes": [[72.0, 270.71, 459.41, 285.14], [72.0, 285.71, 188.02, 300.14]],
  "provenance": "EXTRACTED",
  "status": "approved",
  "derived_from": [],
  "kind": "item",
  "parent_id": "REQ-0001-0824",
  "baseline": 2,
  "created_by": "Bid Manager",
  "created_at": "2026-10-13T06:56:17.174148",
  "source": "p. 1, lines 12-13"
}
```

Example 2, a requirement a person added whose quote is not in the RFP (`POST /api/opportunities/OPP-0006/requirements` with `{"quote": "Bidders shall hold a valid trade licence.", "category": "legal", "page": 1}`):

```json
{
  "id": 2949,
  "req_id": "REQ-0006-0002",
  "version": 1,
  "opportunity_id": "OPP-0006",
  "document_id": "OPP-0006-c7749ef1bfc9",
  "text": "Bidders shall hold a valid trade licence.",
  "quote": "Bidders shall hold a valid trade licence.",
  "category": "legal",
  "section": "",
  "page": null,
  "line_start": null,
  "line_end": null,
  "bboxes": [],
  "provenance": "UNANCHORED",
  "status": "proposed",
  "derived_from": [],
  "kind": "item",
  "parent_id": null,
  "baseline": null,
  "created_by": "Bid Manager",
  "created_at": "2026-10-13T08:13:55.187304+00:00",
  "source": "not found in source"
}
```

**Child entry.** The trace endpoint lists a group's active sub-requirements in the row field `children`, each as a four-field summary: `{"req_id", "text", "source", "document_id"}`. Example: `{"req_id": "REQ-0001-0004", "text": "Proposals must be submitted electronically via email before 4pm on September 15.", "source": "p. 1, lines 14-15", "document_id": "OPP-0001-893403680eda"}`.

**Requirement history.** `GET /api/requirements/{req_id}/history` returns a view rebuilt from the audit log, not a row: `req_id`, `quote`, `source`, `derived_from`, `versions` (a list of `{"n", "at", "by", "label", "text", "category"}` plus `reason` for later versions; `label` is `original`, `edited` or `revised`) and `events` (see 17.12). Section 7 describes it in full.

### 17.5 Baseline

A frozen set of requirements. Table `baseline`, model `Baseline` in `app/modules/requirements/models.py`. Freezing creates baseline 1; applying a change set creates the next one.

| Field | Type | Meaning |
|---|---|---|
| `id` | integer | Database row ID. |
| `opportunity_id` | string | The owning opportunity. |
| `number` | integer | 1, 2, 3 and so on within the opportunity. |
| `count` | integer | The approved groups and stand-alone items in that baseline (sub-requirements are not counted). For OPP-0001: 348 in baseline 1; 349 in baseline 2 (348 + 2 added - 1 removed). |
| `frozen_by` | string | The person who froze it, or who applied the change set that created it. |
| `frozen_at` | date-time | When. |

Returned by: `GET /api/opportunities/{opp_id}/requirements` (field `baseline`: the latest baseline, or `null` before the first freeze) and `POST /api/opportunities/{opp_id}/baselines` (the new row). `GET /api/opportunities/{opp_id}/changes` returns the two-field summary `{"number", "count"}` of the latest baseline.

Example (`GET /api/opportunities/OPP-0001/requirements`, field `baseline`):

```json
{"id": 3, "opportunity_id": "OPP-0001", "number": 2, "count": 349, "frozen_by": "Bid Manager", "frozen_at": "2026-10-13T06:56:17.297436"}
```

### 17.6 Match

The proposed (or chosen) business unit, product and offering type for one requirement. Table `match`, model `Match` in `app/modules/matching/models.py`. Rows are appended, never deleted: each run of the matcher and each manual choice adds a row, and accepting or rejecting changes the `status` of an existing row. The **latest row per requirement** counts; a requirement whose latest row is `rejected` counts as unmatched (`for_opportunity()` in `app/modules/matching/service.py`).

| Field | Type | Meaning |
|---|---|---|
| `id` | integer | Match ID. Used by `POST /api/matches/{match_id}/decide`. |
| `opportunity_id` | string | The opportunity. |
| `req_id` | string | The requirement. |
| `bu` | string or null | The main business unit (the first entry of `units`). `null` when the bid manager answers the requirement (the "bid desk"). |
| `product_id` | string or null | The main product (first entry of `units`), a product ID from the catalog (17.14). `null` for the bid desk. |
| `offering_type` | string | The main offering type: `CTO` (configure-to-order: a catalog product with options, quoted through the configure-price-quote tool), `SEMI_CUSTOM` (a configured product plus extra workshop work), `ETO` (engineered-to-order: designed for this requirement) or `NONE` (not a product item; the bid desk answers it). |
| `units` | array of unit entries | Every unit and product the requirement needs, the main one first (see below). `[]` for the bid desk. |
| `confidence` | number, 0 to 1 | The model's confidence for `method` `agent`; the retrieval score for `retrieval_only` (or `0.0` when routed to the bid desk); `1.0` for `rule` and `manual`. |
| `rationale` | string | Why. For `agent`: the model's one or two sentences citing catalog entries. For `rule`: `"A <category> requirement, not a product item: the bid manager answers it."`. For `retrieval_only`: `"Closest catalog entry <id> (retrieval score <score>)."` or `"Not matched to a product; the bid manager answers it."`, prefixed with `"Model answer [...] has no catalog product. "` when the model named only non-catalog products. For `manual`: `"Set by <person>."`. |
| `evidence` | array of search hits | The top five hits of the long-term index for the requirement's quote at matching time (17.7). `[]` for a manual match. **Removed** by the trace and consolidation endpoints. |
| `method` | string | `agent` (the matcher model answered), `rule` (a commercial, schedule, submission, legal or staffing requirement, routed to the bid desk without a model call), `retrieval_only` (no usable model answer: the top catalog hit, or the bid desk) or `manual` (a person chose). The model comment lists only `agent`, `retrieval_only` and `manual`; the code also writes `rule`, and 135 of the 349 current OPP-0001 matches use it. |
| `status` | string | `proposed` (the agent's proposal), `accepted` (a person accepted it) or `rejected` (a person rejected it). A manual match is stored as `accepted`. |
| `decided_by` | string or null | Who accepted, rejected or set it. |
| `created_at` | date-time | When the row was added. |

**Unit entry** (an element of `units`):

| Field | Type | Meaning |
|---|---|---|
| `bu` | string | Business-unit code, always taken from the product, so unit and product never disagree. |
| `product_id` | string | A product of an active unit. |
| `offering_type` | string | `CTO`, `SEMI_CUSTOM` or `ETO` (never `NONE`). |

An agent answer keeps at most three entries and one entry per product (`MAX_UNITS` in `app/modules/matching/agent.py`). A manual choice keeps one entry per product, with no upper limit.

Returned by: `GET /api/opportunities/{opp_id}/trace` (field `match` of each row, without `evidence`), `GET /api/opportunities/{opp_id}/consolidation` (field `match` of each row, without `evidence`) and `POST /api/opportunities/{opp_id}/requirements/{req_id}/match` (the new manual row, with `evidence` `[]`). `POST /api/opportunities/{opp_id}/match` returns counts only, and `POST /api/matches/{match_id}/decide` returns `{"ok": true}`. No endpoint returns the stored retrieval `evidence` of an agent match.

Example (`GET /api/opportunities/OPP-0002/consolidation`, field `match` of one row):

```json
{
  "id": 353,
  "opportunity_id": "OPP-0002",
  "req_id": "REQ-0002-0005",
  "bu": "JETCOOL",
  "product_id": "JETCOOL-PLATE",
  "offering_type": "CTO",
  "units": [
    {"bu": "JETCOOL", "product_id": "JETCOOL-PLATE", "offering_type": "CTO"},
    {"bu": "JETCOOL", "product_id": "JETCOOL-CDU", "offering_type": "SEMI_CUSTOM"}
  ],
  "confidence": 0.95,
  "rationale": "The requirement for 120 kW rack density with liquid cooling at rack and chip level matches the capabilities of JETCOOL-PLATE ... and JETCOOL-CDU ...",
  "method": "agent",
  "status": "proposed",
  "decided_by": null,
  "created_at": "2026-10-13T05:51:52.831002"
}
```

A bid-desk match routed by rule (`GET /api/opportunities/OPP-0001/trace`, field `match` of the first row):

```json
{"id": 1, "opportunity_id": "OPP-0001", "req_id": "REQ-0001-0001", "bu": null, "product_id": null,
 "offering_type": "NONE", "units": [], "confidence": 1.0,
 "rationale": "A schedule requirement, not a product item: the bid manager answers it.",
 "method": "rule", "status": "proposed", "decided_by": null, "created_at": "2026-10-13T05:51:49.765635"}
```

### 17.7 Search Hits and RFP Passages

The system has two kinds of retrieval index (`app/core/vectors.py`): the **long-term index** of the knowledge base (products, past responses, catalog items and knowledge approved by the curator) and one **short-term index** per RFP (its passages with page and line numbers). Every search returns hits with a `score`.

**Long-term index hit.** Built by `_index()` in `app/modules/catalog/service.py`. There are three kinds of hit:

| Field | `product` | `past_response` | `catalog_item` | Meaning |
|---|---|---|---|---|
| `kind` | yes | yes | yes | `"product"`, `"past_response"` or `"catalog_item"`. |
| `id` | yes | yes | yes | Product ID (`CROWN-ARMV`); past-response ID (`PAST-CROWN-001`), or the knowledge ID (`KB-0001`) for approved knowledge; catalog item ID (`CROWN-ARMV/Arc-Resistant Switchgear`). |
| `bu` | yes | yes | yes | Business-unit code (`BID` for approved knowledge that did not come from a unit's answer). |
| `offering_type` | yes | - | yes | The product's usual offering type; for a catalog item, its family's. |
| `family` | - | - | yes | The product ID the catalog item belongs to. |
| `learned` | - | approved knowledge only | - | `true` for an item approved by the knowledge curator (section 13). |
| `text` | yes | yes | yes | The indexed text: product name, description and keywords; past requirement and response; or item name, model and specifications. |
| `score` | yes | yes | yes | Cosine similarity, rounded to 3 decimals. Only hits scoring above 0 are returned, best first. |

Returned by: `GET /api/catalog` (field `results`: ten hits, only when `q` is given), `GET /api/catalog/search` (the list itself: `k` hits, 1 to 50, default 5), and stored in `Match.evidence` (five hits). The response outline lists up to three past-response hits per chapter as `{"id", "bu", "text"}`, with `text` cut to 300 characters (section 14).

Example (`GET /api/catalog/search?q=liquid%20cooling&k=3`, first element):

```json
{"kind": "product", "id": "JETCOOL-HYBRID", "bu": "JETCOOL", "offering_type": "CTO",
 "text": "Liquid-assisted air cooling (SmartPlate System). Self-contained liquid-assisted air cooling ...",
 "score": 0.365}
```

**RFP passage.** A passage is a run of consecutive body lines of one page, about one paragraph (up to about 500 characters), with headers and footers left out (`passages()` in `app/modules/ingestion/service.py`).

| Field | Type | Meaning |
|---|---|---|
| `page` | integer | Page of the main RFP. |
| `line_start`, `line_end` | integer | First and last line of the passage on that page. |
| `text` | string | The lines joined with spaces. |
| `score` | number | Cosine similarity, 3 decimals. |

Returned by: `GET /api/opportunities/{opp_id}/rfp-search` (field `passages`: 1 to 25 passages, default 8). The response outline lists up to three passages per chapter without `score`, with `text` cut to 300 characters.

**The `mode` value.** `GET /api/opportunities/{opp_id}/rfp-search` (field `mode`), `GET /api/knowledge` (field `index`) and the response outline (`references.mode`) report how an index was built: `"embeddings"` when vectors exist for its texts (frozen in `data/vector_cache`, or made by the embedding service), `"keywords"` when it falls back to keyword (TF-IDF) search. In offline (mock) mode a query cannot be turned into a vector, so ranking uses keyword scores even when the index reports `"embeddings"` (`search_many()` in `app/core/vectors.py`). An empty query returns no hits.

Example (`GET /api/opportunities/OPP-0001/rfp-search?q=arc%20resistant&k=2`, trimmed):

```json
{"mode": "embeddings",
 "passages": [
   {"page": 55, "line_start": 47, "line_end": 57, "text": "positions with protective relay and controls, ... 2. Switchgear shall be Arc-resistant Type 2B. ...", "score": 0.172},
   {"page": 53, "line_start": 1, "line_end": 29, "text": "Syracuse Hancock International Airport Landside Switchgear Relocation SPECIFICATION FOR METAL CLAD SWITCHGEAR ...", "score": 0.143}]}
```

### 17.8 Decision

A named person's participation or go/no-go decision, stored with the evidence shown at the time. Table `decision`, model `Decision` in `app/modules/decisions/models.py`. Layer 0 never decides; it records.

| Field | Type | Meaning |
|---|---|---|
| `id` | integer | Decision ID. Used as `ref` when the rationale is sent to the knowledge base (section 13). |
| `opportunity_id` | string | The opportunity. |
| `kind` | string | `participation` or `go_no_go`. |
| `outcome` | string | Always `"units"` for a participation decision; `"go"` or `"no_go"` for a go/no-go decision. |
| `units` | array of strings | Business-unit codes. For participation: the units the person chose (active units only). For go/no-go: the units of the latest participation decision at that moment (`[]` if there is none). |
| `evidence` | object | The evidence pack as it was when the decision was recorded (see below). A go/no-go decision also stores the go/no-go `summary` inside it. |
| `rationale` | string | The person's reason; `""` when none was given. |
| `criteria` | array of criterion entries | For go/no-go: the person's judgement per criterion (see below). `[]` for participation, and when no judgement was sent. |
| `decided_by` | string | The person. |
| `decided_at` | date-time | When. |

**Criterion entry** (an element of `criteria`; the request body of `POST /api/opportunities/{opp_id}/go-no-go` uses the same shape):

| Field | Type | Meaning |
|---|---|---|
| `id` | string | One of the twelve criterion IDs in `data/knowledge_base/go_no_go.json`: `scope_fit`, `all_matched`, `coverage`, `engineering_rules`, `open_questions`, `matches_reviewed`, `pending_acquisition`, `deviations`, `capacity`, `cost_budget`, `delivery`, `competitors`. |
| `status` | string | The person's judgement: `met`, `not_met` or `unknown`. |
| `note` | string | Optional note; `""` by default. |

The go/no-go summary computed by Layer 0 has its own criterion entries, with `id`, `name`, `question`, `status`, `detail` and, for the three criteria without data, `data: "not_available"`. Section 11 describes that summary.

**Evidence pack.** Built by `evidence()` in `app/modules/decisions/service.py`. It is returned live by `GET /api/opportunities/{opp_id}/decisions` (field `evidence`) and stored inside every decision row. Section 11 describes the nested objects in full. The top level is:

| Field | Type | Meaning |
|---|---|---|
| `requirements` | integer | Active groups and stand-alone items. |
| `frozen` | boolean | Whether the opportunity has a baseline. |
| `by_category` | object | Category to count. |
| `unanchored` | array of strings | Requirement IDs with provenance `UNANCHORED`. |
| `suggested_units` | object | Unit code to the number of requirements whose match names that unit. |
| `offering_mix` | object | Offering type to count, over the current matches. |
| `unmatched` | array of strings | Requirement IDs without a counted match. |
| `not_reviewed` | integer | Product matches still `proposed` (nobody accepted or changed them). |
| `checks` | object | Engineering checks: `requirements_checked`, `scope`, `facts`, `units_outside_scope`, `tier_flags`, `rules`, `solver`. |
| `deviations` | object | Data-sheet ratings against standard product ratings: `rows`, `checked`, `products`, `placeholder`, `note`. |
| `workload` | object | Open work per unit against capacity: `rows`, `placeholder`, `note`. |
| `summary` | object | Only inside a stored go/no-go decision: the go/no-go summary as shown (`rows`, `by_category`, `coverage`, `criteria`, `advice`). |

Returned by: `GET /api/opportunities/{opp_id}/decisions` (fields `participation` and `go_no_go`: the latest decision of each kind, or `null`), `POST /api/opportunities/{opp_id}/participation` and `POST /api/opportunities/{opp_id}/go-no-go` (the new row). The hand-off carries a summary `{"outcome", "decided_by", "decided_at"}` of the latest go/no-go decision.

Example (`GET /api/opportunities/OPP-0002/decisions`, field `go_no_go`, with `evidence` shortened):

```json
{
  "id": 4,
  "opportunity_id": "OPP-0002",
  "kind": "go_no_go",
  "outcome": "go",
  "units": ["CLOUD", "FPM", "JETCOOL", "ANORD"],
  "evidence": {"requirements": 10, "frozen": true, "...": "...", "summary": {"...": "..."}},
  "rationale": "In scope for the participating units.",
  "criteria": [],
  "decided_by": "Bid Manager",
  "decided_at": "2026-10-13T05:51:52.896831"
}
```

### 17.9 Assignment and Progress

**Assignment.** One requirement assigned to one business unit (or to the bid desk), with that unit's answer. Table `assignment`, model `Assignment` in `app/modules/workpackages/models.py`. The pair (`req_id`, `bu`) is unique. A unit's work package is the set of its assignments.

| Field | Type | Meaning |
|---|---|---|
| `id` | integer | Assignment ID. Used by the respond and validate endpoints, and as `ref` when a validated answer is sent to the knowledge base. |
| `opportunity_id` | string | The opportunity. |
| `req_id` | string | The requirement. |
| `bu` | string | Business-unit code, or `BID` for the bid desk (requirements the bid manager answers). |
| `owner` | string | The unit's design engineer (from `business_units.json`), or `"Bid Manager"` for the bid desk. |
| `status` | string | `assigned` (waiting for the unit), `submitted` (answered, waiting for validation), `validated` (accepted by the bid manager), `returned` (sent back with a note: by the bid manager, or because a change document changed the requirement) or `withdrawn` (no longer fits the matches or participation; kept with its earlier answer, and reopened if it fits again). Section 22 shows the transitions. |
| `compliance` | string or null | The unit's answer: `met`, `partial`, `not_met` or `exception`. `null` until answered. |
| `product_ref` | string or null | What meets it. At dispatch: the first product of that unit in the match. The unit may replace it with a non-empty value when answering. `null` for the bid desk until answered. |
| `response` | string | The unit's answer text; `""` until answered. |
| `responded_by` | string or null | Who answered. |
| `responded_at` | date-time or null | When. |
| `validated_by` | string or null | Who validated or returned it. When a change document returns the answer: the person who applied the change. |
| `validation_note` | string | The note given when validating or returning; for a change, `"Changed by <file name>: <what changed>"`. |
| `created_at` | date-time | When the assignment was created (dispatch). |

Returned by: `GET /api/inbox/{bu}` (field `items`: the unit's active work across all opportunities, each item with an extra field `requirement`, see 17.4), `GET /api/opportunities/{opp_id}/trace` (field `assignments` of each row) and `GET /api/opportunities/{opp_id}/consolidation` (field `assignments` of each row). These three leave out `withdrawn` assignments. `POST /api/assignments/{assignment_id}/respond` and `POST /api/assignments/{assignment_id}/validate` return `{"ok": true}`. The hand-off carries a summary `unit_answer` with `status`, `compliance`, `product_ref`, `response` (`null` when empty) and `validated_by`.

Example (`GET /api/opportunities/OPP-0001/trace`: an answer returned because Addendum No. 1 changed one of the group's sub-requirements):

```json
{
  "id": 134,
  "opportunity_id": "OPP-0001",
  "req_id": "REQ-0001-0887",
  "bu": "CROWN",
  "owner": "Crown Design Engineer",
  "status": "returned",
  "compliance": "met",
  "product_ref": "CROWN-ARMV",
  "response": "Two-section 15 kV arc-resistant metal-clad lineup offered.",
  "responded_by": "Crown Design Engineer",
  "responded_at": "2026-10-13T05:51:51.150031",
  "validated_by": "Bid Manager",
  "validation_note": "Changed by rfp_syracuse_addendum_1.pdf: sub-requirement REQ-0001-0332 now reads: Switchgear must include twenty (20) 15kV vacuum circuit breaker positions, meters, switches, VT’s, and CT’s.",
  "created_at": "2026-10-13T05:51:51.120144"
}
```

**Progress map.** Counts of active (not withdrawn) assignments per unit, built by `progress()` in `app/modules/workpackages/service.py`: an object from unit code to `{"total", "submitted", "validated"}`. `submitted` counts submitted **and** validated answers; `validated` counts validated answers only. Units without work are absent, so an opportunity that was never dispatched has `{}`.

Returned by: `GET /api/portfolio` (field `progress` of each entry) and `GET /api/opportunities/{opp_id}/trace` (field `progress`).

Example (`GET /api/opportunities/OPP-0002/trace`, field `progress`):

```json
{"CLOUD": {"total": 1, "submitted": 0, "validated": 0},
 "BID": {"total": 6, "submitted": 1, "validated": 0},
 "FPM": {"total": 1, "submitted": 0, "validated": 0},
 "JETCOOL": {"total": 1, "submitted": 1, "validated": 1},
 "ANORD": {"total": 1, "submitted": 1, "validated": 0}}
```

## 18. Error Catalogue

Every error body is `{"detail": "<message>"}`, except validation errors (422 from FastAPI and Pydantic), whose `detail` is a list of `{type, loc, msg, input}` objects. The web client shows the `detail` text (or the joined `msg` values of a list) in a toast or inline alert.

How each controller maps service exceptions:

| Module | LookupError | PermissionError | ValueError | Other |
|---|---|---|---|---|
| opportunities | 404 | - | 422 on create; 409 on documents and samples | Unknown opportunity on GET: 404 `<id> not found` |
| ingestion | 404 | - | - | - |
| requirements | 404 | - | 409 | - |
| changes | 404 | 403 | 409 | - |
| catalog | - | - | - | none (read-only) |
| matching | 404 | - | 422 (manual match) | - |
| decisions | 404 | - | 422 (participation), 409 (go/no-go) | 422 `Unknown criteria: [...]` checked in the controller |
| workpackages | 404 | 403 | 409 | 404 `Unit X not found.` for an unknown inbox; 422 from the `ValidateIn` model |
| knowledge | 404 | 403 | 409 | - |
| consolidation | 404 | - | - | - |
| trace | 404 | - | - | - |

### 18.1 Opportunities and documents

| Status | Message | Endpoint(s) | Cause | What to do |
|---|---|---|---|---|
| 422 | `A title is required.` | POST /api/opportunities | Blank title | Give a title |
| 422 | `Could not allocate an opportunity ID; try again.` | POST /api/opportunities | 20 ID clashes in a row | Retry |
| 404 | `<opp_id> not found` | GET /api/opportunities/{opp_id} | Unknown opportunity | Check the ID |
| 404 | `Opportunity <opp_id> not found.` | Most endpoints that take `opp_id` | Unknown opportunity | Check the ID |
| 409 | `This opportunity already has a main RFP; upload this file as an addendum, Q&A or other.` | POST …/documents, …/documents/from-sample | Second main document | Choose another role |
| 409 | `Unknown sample '<name>'; see /api/samples.` | …/documents/from-sample, …/changes/from-sample | Unknown sample name | Use a name from GET /api/samples |
| 409 | `Sample '<name>' is a change document, not an RFP.` / `… is an RFP, not a change document.` | the two from-sample endpoints | Sample of the wrong kind | Use the other endpoint |

### 18.2 Ingestion

| Status | Message | Endpoint(s) | Cause |
|---|---|---|---|
| 404 | `Document '<doc_id>' not found.` | POST …/ingest, GET …/pages/{n}, …/pages/{n}.png | Unknown document ID (or an ID with characters other than letters, digits and `-`) |
| 404 | `Document <doc_id> has not been read yet.` | GET …/pages/{n}(.png) | No layout file yet |
| 404 | `Page <n> not found; the document has <count> pages.` | GET …/pages/{n}(.png) | Page outside 1..count |
| 404 | `Not Found` | GET …/pages/abc | Page number not an integer (no route matches) |
| 404 | `The main RFP has not been read yet.` | GET …/rfp-search | No ingested main document |
| 200 | `{"document": …, "error": "<reason>"}` | POST …/ingest | File unreadable (document `failed`) or not a PDF (`unsupported file type; recorded but not read`) |

### 18.3 Requirements (all 409 unless stated)

| Message | Endpoint(s) | Cause |
|---|---|---|
| `Requirements are frozen in baseline <n>; later changes go through the changes module.` | every requirement write | A baseline exists |
| (same) + ` A requirement missed before the freeze now comes in through the Changes page.` | …/requirements/from-lines | A baseline exists |
| `Upload the main RFP and wait until it has been read.` | extract, add, from-lines, freeze | Main RFP missing or not ingested |
| `Review has started (<n> review actions); re-reading would lose that work. Add what is missing with 'Add a requirement' instead.` | extract | A person already reviewed items |
| `A requirement needs a quote copied from the RFP.` | add | Blank quote |
| `Unknown category '<c>'.` | add, from-lines, review (edit) | Category outside the seven |
| `Page <p> not found; the RFP has <n> pages.` | from-lines | Page outside the RFP |
| `Page <p> has no readable lines (not read; it needs OCR).` | from-lines | Page without text |
| `Choose lines between 1 and <last> on page <p>, the first line before the last.` | from-lines | Bad line range |
| `Select at most 40 lines; split a longer passage into several requirements.` | from-lines | More than 40 lines |
| `Only header or footer lines are selected; select the requirement's own lines.` | from-lines | Only furniture lines |
| 404 `<req_id> not found.` | review, split, ungroup, history, merge | Unknown requirement |
| `<req_id> is <status>; it can no longer be changed.` | split, merge, ungroup | Inactive item |
| `<req_id> is <split\|merged>; review its replacement instead.` | review | Item already replaced |
| `<req_id> is a group; use Ungroup to release its sub-requirements.` | split | Group |
| `A split needs at least two parts.` | split | Fewer than two non-blank quotes |
| `Give the merged requirement a short text.` | merge | Blank text |
| `A merge needs at least two line items.` | merge | Fewer than two distinct IDs |
| `Line items from another opportunity cannot be merged.` | merge | Mixed opportunities |
| `Groups and sub-requirements cannot be merged; ungroup first.` | merge | Group or member selected |
| `Only line items on the same page can be merged; keep cross-page items separate.` | merge | Several pages |
| `<req_id> is not a group.` | ungroup | Not a group |
| `<n> line items still need approve or reject before freezing.` | baselines | Undecided items |
| `Nothing is approved; a baseline needs at least one requirement.` | baselines | No approved item |
| 422 validation list | review (action outside approve / reject / edit), split (< 2 parts), merge (< 2 IDs), missing required fields | Body invalid |

### 18.4 Changes (409 unless stated)

| Message | Endpoint(s) | Cause |
|---|---|---|
| `Freeze the requirements first: a change document is compared with the frozen baseline.` | changes upload / from-sample | No baseline |
| `<file> (change set <n>) is still in review: apply or discard it first.` | upload | Another set in review |
| `Upload the change document as a PDF.` | upload | Name not ending in `.pdf` |
| `This file is the main RFP of <opp>, not a change document.` | upload | Same bytes as the main RFP |
| `<file> was already applied (change set <n>, baseline <m>).` | upload | Document applied before |
| `<file> could not be read: <error>` | upload | Ingestion failed |
| `No frozen answers exist for <file> in this offline demo; connect the model service to read new documents.` | upload | Offline mode, no frozen answer |
| `The change agent found no statements in <file>.` | upload | Nothing to classify |
| 404 `Change set <n> not found.` | decide, confirm-all, apply, discard | Unknown set |
| 404 `Item <i> is not in change set <n>.` | decide | Wrong item |
| `Change set <n> is <status>; only a set in review can be changed.` | decide, confirm-all, apply, discard | Set already applied or discarded |
| `Change set <n> was applied or discarded meanwhile; refresh the page.` | decide, confirm-all, apply, discard | Concurrent action (two tabs, double click) |
| `Name the baseline requirement this statement changes.` (`removes`, `leaves unchanged`) | decide | Missing target |
| `<req> is not an approved requirement of baseline <n>.` | decide, apply | Bad target |
| 403 `Only the Bid Manager applies a change set.` | apply | Acting person is not Bid Manager |
| 403 `Only the Bid Manager discards a change set.` | discard | Acting person is not Bid Manager |
| `<n> classification(s) still need a person's confirmation (items [..]).` | apply | Unconfirmed items |
| `Items [..] all change <req>: put the combined new wording in one of them and mark the others unchanged.` | apply | Two items on one target |
| `This set was read against baseline <n>, which is no longer the latest; discard it and upload the document again.` | apply | Baseline moved on |
| 422 validation list | decide | `kind` outside the five values; `target` over 20 or `text` over 2000 characters |

### 18.5 Matching, decisions and work packages

| Status | Message | Endpoint(s) | Cause |
|---|---|---|---|
| 404 | `Match <n> not found.` | POST /api/matches/{id}/decide | Unknown match |
| 422 | validation list | POST /api/matches/{id}/decide | `action` not `accept` / `reject`, or ID out of range |
| 404 | `<req> is not a requirement of <opp>.` | POST …/requirements/{req}/match | Wrong requirement |
| 422 | `<product> is not a product of an active business unit.` | POST …/requirements/{req}/match | Unknown or inactive product |
| 422 | `<type> is not an offering type.` | POST …/requirements/{req}/match | Offering type invalid |
| 404 | `<opp> not found.` | participation, go-no-go | Unknown opportunity |
| 422 | `Choose at least one active business unit; not active: [..].` | participation | Empty or inactive units |
| 422 | `Unknown criteria: [..].` | go-no-go | Criterion ID not in the go/no-go criteria file |
| 409 | `Freeze the requirements before deciding go or no-go (review page).` | go-no-go | No baseline |
| 409 | `Unknown criterion or judgement: <id> = <status>.` | go-no-go | Judgement outside the allowed values |
| 409 | `Freeze the requirements before dispatch (review page).` | dispatch | No baseline |
| 409 | `Dispatch needs a 'go' decision first (decisions page).` | dispatch | Latest go/no-go is not `go` |
| 409 | `Dispatch is already running for this opportunity; refresh and try again.` | dispatch | Concurrent dispatch |
| 404 | `Unit <bu> not found.` | GET /api/inbox/{bu} | Unknown unit code |
| 404 | `Assignment <n> not found.` | respond, validate | Unknown assignment |
| 403 | `Only <bu>'s product manager or design engineer can answer this item.` | respond | Wrong person (the bid desk's items: only the Bid Manager) |
| 409 | `This item is <status>; only assigned or returned items can be answered.` | respond | Already submitted, validated or withdrawn |
| 403 | `Only the Bid Manager validates or returns answers.` | validate | Wrong person |
| 409 | `This item is <status>; only submitted answers can be validated or returned.` | validate | Not submitted |
| 422 | `Value error, Say why the answer is returned (note).` | validate | `ok` false without a note |
| 404 | `<opp> not found.` / `No work for <bu> in <opp>.` | GET …/handoff/{bu} | Unknown opportunity, or no assignment for that unit |
| 409 | `The bid desk answers its items itself; it has no downstream system to hand off to.` | GET …/handoff/BID | Hand-off asked for the bid desk |

### 18.6 Knowledge

| Status | Message | Endpoint(s) |
|---|---|---|
| 404 | `Requirement <ref> not found.` / `Answer <ref> not found.` / `Decision <ref> not found.` | POST /api/knowledge |
| 409 | `Only validated answers go to the knowledge base.` | POST /api/knowledge |
| 409 | `This decision has no rationale to keep.` | POST /api/knowledge |
| 409 | `Already <queued\|approved> as <KB-nnnn>.` | POST /api/knowledge |
| 404 | `<kb_id> not found.` | POST /api/knowledge/{kb_id}/review |
| 403 | `Only the knowledge curator (in the PoC, the Bid Manager) approves knowledge.` | review |
| 409 | `<kb_id> is already <status>.` | review |
| 409 | `A rejection needs a note saying why.` | review |
| 422 | validation list (`kind`, `status` filter, length limits) | POST /api/knowledge, GET /api/knowledge |

### 18.7 Model unavailable and server errors

The model gateway raises `LLMUnavailable` with `No cached answer for <task>/<key>; set LLM_PROVIDER=azure to generate it.` (offline mode, no frozen answer), `Model refused: <reason>` or `Answer truncated at max_tokens; send a smaller chunk.` No endpoint returns this as an HTTP error of its own; each caller turns it into a visible result:

| Caller | What the client sees |
|---|---|
| Extract (7.2) | 200 with the pages listed in `problems`; nothing guessed |
| Matching (10.1) | 200; the requirement gets a retrieval-only proposal (method `retrieval`) for a person to check |
| Change upload (8.2) | 409 `No frozen answers exist for … in this offline demo; …` |
| Response outline (14.4) | 200; chapter `drafted: false` with the "Draft not refreshed …" note |

Other failures of the Azure service (network, authentication, rate limits) are not caught and reach the client as 500 `Internal Server Error` (Known limit). At start-up, a database older than the code stops the API with `The local database is older than the code (missing: …). Stop the API, then run '.venv\Scripts\python -m scripts.seed_demo --reset' (or reset-demo.cmd) to rebuild the demo data.`

## 19. Dependencies Between Endpoints

The API is synchronous and stateless per request; the dependencies below come from the state each call needs. Reads (GET) have no preconditions beyond an existing opportunity, except where noted.

```text
POST /opportunities
   |
   v
POST /opportunities/{id}/documents  (or .../documents/from-sample)
   |   background ingestion -> document "ingested"
   |   (GET /opportunities/{id} until then; GET .../rfp-search, GET /documents/{doc}/pages/{n}[.png] now work)
   v
POST /opportunities/{id}/requirements/extract   (optional: requirements can also be added by hand)
   |
   +--> POST /requirements/{req}/review | .../split | .../ungroup ; POST .../requirements/merge
   +--> POST .../requirements  |  POST .../requirements/from-lines        (add missed)
   v
POST /opportunities/{id}/baselines          (all decided, >= 1 approved)   => baseline 1, status "frozen"
   |
   +-----------------------------------------------+
   v                                               v
POST /opportunities/{id}/match                 POST /opportunities/{id}/changes  (or .../from-sample)
   |  POST /matches/{m}/decide                        |  POST /changes/{s}/items/{i} | .../confirm-all
   |  POST .../requirements/{req}/match               v
   v                                              POST /changes/{s}/apply (Bid Manager) | .../discard
POST /opportunities/{id}/participation                  => baseline N+1, answers returned, re-match, re-dispatch
   v
POST /opportunities/{id}/go-no-go          (needs baseline)  => status "go" | "no_go"
   v
POST /opportunities/{id}/dispatch          (needs baseline and latest go/no-go "go") => status "dispatched"
   |
   +--> GET /inbox/{bu} --> POST /assignments/{a}/respond (unit PM/DE; BID: Bid Manager)
   |                            v
   |                        POST /assignments/{a}/validate (Bid Manager)  -- returned --> respond again
   +--> GET /opportunities/{id}/handoff/{bu}
   v
GET .../consolidation, .../compliance-matrix.csv|.xlsx, .../response-outline[.md]
   |
   +--> POST /knowledge (validated answers, requirements, decision rationales) --> POST /knowledge/{kb}/review
```

Precondition matrix (mutating endpoints):

| Endpoint | Needs before | Error when called too early | State after success |
|---|---|---|---|
| POST /api/opportunities | - | - | Opportunity `new` |
| POST …/documents, …/documents/from-sample | Opportunity | 404 | Document `uploaded` → (background) `ingested` / `failed` |
| POST /api/documents/{doc}/ingest | Document | 404 | Layout and search index rebuilt |
| POST …/requirements/extract | Main RFP ingested; no baseline; no review yet | 409 messages of 18.3 | Drafts proposed; status `review` |
| POST …/requirements, …/from-lines | Main RFP ingested; no baseline | 409 | One `proposed` item |
| POST /api/requirements/{req}/review, /split, /ungroup; …/merge | Requirement exists; no baseline | 404 / 409 | Status changes |
| POST …/baselines | Main RFP ingested; every top-level item decided; ≥ 1 approved; no baseline yet | 409 | Baseline 1; status `frozen`; requirement writes closed |
| POST …/match | Approved requirements (frozen recommended: evidence, summary and dispatch only use frozen ones) | none (0 matched) | `proposed` matches |
| POST /api/matches/{m}/decide | Match ID from trace or consolidation | 404 | Match `accepted` / `rejected` |
| POST …/requirements/{req}/match | Requirement of the opportunity; active products | 404 / 422 | Accepted manual match; takes effect at the next dispatch |
| POST …/participation | ≥ 1 active unit | 422 | Participation decision |
| POST …/go-no-go | Baseline | 409 `Freeze the requirements before deciding go or no-go (review page).` | Decision; status `go` / `no_go` |
| POST …/dispatch | Baseline; latest go/no-go `go` | 409 | Assignments created / reopened / withdrawn; status `dispatched` |
| POST /api/assignments/{a}/respond | Assignment `assigned` or `returned`; acting person of that unit | 403 / 409 | `submitted` |
| POST /api/assignments/{a}/validate | Assignment `submitted`; Bid Manager | 403 / 409 / 422 | `validated` or `returned` |
| POST …/changes, …/changes/from-sample | Baseline; no set in review | 409 | Change set `review` |
| POST /api/changes/{s}/items/{i}, /confirm-all | Set in review | 404 / 409 | Items `confirmed` |
| POST /api/changes/{s}/apply | Set in review; all confirmed; Bid Manager; baseline unchanged | 403 / 409 | Set `applied`; baseline N+1 |
| POST /api/changes/{s}/discard | Set in review; Bid Manager | 403 / 409 | Set `discarded` |
| POST /api/knowledge | Source exists (validated answer; decision with a rationale) | 404 / 409 | Item `queued` |
| POST /api/knowledge/{kb}/review | Item `queued`; Bid Manager | 403 / 409 | `approved` (joins the long-term index) / `rejected` |

## 20. Calling Sequences

All examples use the demo IDs. The browser calls go through the web app's `/api` proxy with the `X-Actor` header; the diagrams use these participants:

```text
Browser (screen) | Web (Next.js, /api proxy) | API controller | Module services | Model gateway (frozen answers / Azure) | Store (SQLite, files)
```

### 20.1 Create an opportunity and attach the RFP

1. `POST /api/opportunities` `{"title": "...", "customer": "...", "customer_type": "..."}` → take `id` (for example `OPP-0004`).
2. `POST /api/opportunities/OPP-0004/documents` (multipart `file`, `role=main`) or `POST /api/opportunities/OPP-0004/documents/from-sample` `{"name":"hyperscale_rfp"}` → document `uploaded`, take `id`.
3. Repeat `GET /api/opportunities/OPP-0004` until the document's `status` is `ingested` (the screen polls every 5 seconds and offers **Refresh status**).

```text
Browser            Web proxy        opportunities ctl   opportunities svc    ingestion svc         Store
  | POST /opportunities ---------------> create() ---------> create() -------------------------> INSERT opportunity, audit
  |<------------------------------------ {id: OPP-0004} ...
  | POST /opportunities/OPP-0004/documents (file, role=main)
  |----------------------------------> upload() ---------> add_document() ---------------------> files/<sha>.pdf, INSERT document
  |<------------------------------------ {status: uploaded, existing: false}
  |                                       (background task) ------------------> ingest() --------> layouts/<doc>.json, status ingested
  | GET /opportunities/OPP-0004 (every 5 s) ------------------------------------------------------> documents[0].status
```

### 20.2 Read the RFP into requirements and review them

1. `POST /api/opportunities/OPP-0001/requirements/extract` → `{proposed, duplicates, groups, requirements, problems}`; status `review`.
2. `GET /api/opportunities/OPP-0001/requirements` → the list.
3. For each item: `POST /api/requirements/REQ-0001-0001/review` `{"action":"approve"}` (or `reject`, or `edit` with `text`/`category`); a group's approval covers its sub-requirements.
4. As needed: `POST /api/requirements/{req}/split` `{"parts":[{"quote":"..."},{"quote":"..."}]}`; `POST /api/opportunities/{opp}/requirements/merge` `{"req_ids":[...],"text":"..."}`; `POST /api/requirements/{group}/ungroup`; `GET /api/requirements/{req}/history`.
5. `GET …/requirements` after each action (the screen reloads).

```text
Browser        requirements ctl    requirements svc      reader agent / grouping agent      Model gateway
  | POST .../extract --> extract() -> checks (frozen? main read? review started?)
  |                                  -> agent.read(layout) ---- 4 parallel calls ---------> read_requirements (cache or Azure)
  |                                  -> anchoring.find() per quote (page, lines, boxes or UNANCHORED)
  |                                  -> grouping.duplicates() (text comparison, no model)
  |                                  -> grouping.group() ---- one call per page (>= 3 items) -> group_requirements
  |                                  -> opportunities.set_status("review")
  |<-- {proposed: 814, duplicates: 21, groups: 162, requirements: 348, problems: []}
```

### 20.3 Add a missed requirement

By selecting lines:
1. `GET /api/opportunities/{opp}` → the main document `id` and `page_count`.
2. `GET /api/documents/{doc}/pages/{n}` and `GET /api/documents/{doc}/pages/{n}.png` → lines and image.
3. `POST /api/opportunities/{opp}/requirements/from-lines` `{"page":1,"line_start":11,"line_end":11,"text":"...","category":"schedule"}`.

By pasting a quote: `POST /api/opportunities/{opp}/requirements` `{"quote":"...","category":"technical","page":1}`.

### 20.4 Freeze the baseline

`POST /api/opportunities/{opp}/baselines` → `{number: 1, count: 348}`; status `frozen`. The screen then raises `opp-status-changed`, and the header re-reads `GET /api/opportunities/{opp}`.

### 20.5 Match products

1. `POST /api/opportunities/OPP-0001/match` → `{matched, kept, calls, rule, agent, ...}` (bid-desk items routed by rule; one matcher call per page batch).
2. `GET /api/opportunities/OPP-0001/trace` → `rows[].match.id`.
3. Per row: `POST /api/matches/{match_id}/decide` `{"action":"accept"}` (or `reject`); or change the units: `GET /api/catalog` (product list), then `POST /api/opportunities/OPP-0001/requirements/REQ-0001-0887/match` `{"units":[{"product_id":"CROWN-ARMV","offering_type":"ETO"}]}`.
4. `GET …/trace` again.

```text
Browser       matching ctl     matching svc                     checks / catalog index        matcher agent -> gateway
  | POST .../match --> match() -> approved, undecided requirements
  |                             -> bid-desk rules (no model) ----> checks.py
  |                             -> evidence: catalog.search_many (long-term index, k=5)
  |                             -> per page batch (<= 15) -------------------------------> match_requirement (4 parallel)
  |                             -> no answer: retrieval-only proposal
  |<-- {matched, kept, calls, ...}
```

### 20.6 Bid decision

1. `GET /api/opportunities/OPP-0001/decisions` → `evidence.suggested_units`, `units`, `summary.criteria`, the latest `participation` and `go_no_go`.
2. `POST /api/opportunities/OPP-0001/participation` `{"units":["CROWN","EP2"],"rationale":"..."}`.
3. `POST /api/opportunities/OPP-0001/go-no-go` `{"outcome":"go","rationale":"...","criteria":[{"id":"<criterion id>","status":"<judgement>","note":"..."}]}` → status `go` (`no_go` stops the bid; a later `go` resumes at the status the stop replaced).
4. `GET …/decisions` again.

### 20.7 Dispatch, answer, validate and hand off

1. `POST /api/opportunities/OPP-0001/dispatch` → `{"created": 348}`; status `dispatched`. One work package per participating unit; requirements with no unit go to the bid desk `BID`. Repeat after a match or participation change (new work created, removed work withdrawn, earlier work reopened).
2. As the unit's product manager or design engineer: `GET /api/inbox/CROWN` → `items[].id`; `POST /api/assignments/134/respond` `{"compliance":"met","product_ref":"CROWN-ARMV","response":"..."}` → `submitted`.
3. As the Bid Manager: `GET /api/inbox/BID` (the bid desk's own items) and `POST /api/assignments/134/validate` `{"ok":true}` → `validated`, or `{"ok":false,"note":"..."}` → `returned` (back to step 2).
4. Any time after dispatch: `GET /api/opportunities/OPP-0001/handoff/CROWN` → the unit's JSON hand-off file.

```text
Bid Manager        workpackages            Unit (PM / DE)              Bid Manager
  dispatch -----> assignments "assigned" --> GET /inbox/CROWN
                                            POST /assignments/{a}/respond --> "submitted"
                                                                             GET /inbox/BID (or trace pane 3)
                                                                             POST /assignments/{a}/validate
                                     <-- "returned" + note (ok=false) ------|
                                                         "validated" (ok=true) -> counts as answered
```

### 20.8 Consolidate the final response

1. `GET /api/opportunities/OPP-0001/consolidation` → `blocking` (requirements not answered).
2. `GET …/compliance-matrix.xlsx` (customer sheet and tracking sheet) and/or `GET …/compliance-matrix.csv`.
3. `GET …/response-outline` (chapters drafted from validated answers) and `GET …/response-outline.md` (download).

### 20.9 Knowledge loop

1. `GET /api/opportunities/{opp}/knowledge` → what was already sent.
2. `POST /api/knowledge` `{"kind":"response","ref":"134","note":"..."}` (or `requirement` with a requirement ID, `decision` with a decision ID from `GET …/decisions`).
3. As the Bid Manager: `GET /api/knowledge` → `items[].kb_id`; `POST /api/knowledge/KB-0001/review` `{"approve":true}` or `{"approve":false,"note":"..."}`.
4. Effect: an approved item appears in `GET /api/catalog/search?q=...` results (as a learned past response), in later matching evidence and in outline references.

### 20.10 Handle a change document

1. `GET /api/opportunities/OPP-0001/changes` → `baseline` must not be null.
2. `POST /api/opportunities/OPP-0001/changes` (multipart `file`) or `POST …/changes/from-sample` `{"name":"syracuse_addendum_1"}` → set `1`, status `review`, 8 items.
3. Per item `POST /api/changes/1/items/{item_id}` `{"kind":"modified","target":"REQ-0001-0039","text":"..."}`, or `POST /api/changes/1/confirm-all`.
4. As the Bid Manager: `POST /api/changes/1/apply` → `result` `{"baseline":2,"added":[...],"modified":[...],"removed":[...],"returned":2,"dispatched":2,"note":""}`; or `POST /api/changes/1/discard`.
5. `GET …/requirements` (new versions and IDs), `GET /api/requirements/REQ-0001-0039/history` (label `revised`), `GET …/trace` (the addendum appears in `docs`).

```text
Browser      changes ctl   changes svc                      ingestion / agents / gateway          requirements / matching / workpackages
  | POST .../changes --> upload() -> store as role "change" -> ingest -> read_changes -> rank (TF-IDF) -> classify_change
  |<-- set (review, 8 items proposed)
  | POST /changes/1/confirm-all --> all items confirmed
  | POST /changes/1/apply (Bid Manager) --> apply() -------------------------------------------> apply_change(): versions, new IDs, baseline 2
  |                                                                                          -> return_for_change() (answers returned)
  |                                                                                          -> match(req_ids = added + modified)
  |                                                                                          -> dispatch() (if dispatched before and "go")
  |<-- set (applied, result)
```

### 20.11 Search the RFP

`GET /api/opportunities/OPP-0001/rfp-search?q=short-circuit%20rating&k=8` → passages with page and lines; the screen links each to its place.

### 20.12 Walkthrough one-click examples

The guided walkthrough calls the same endpoints as the screens. Its examples use bundled samples by name: `POST …/documents/from-sample` `{"name":"syracuse_rfp"}` then a refresh of `GET /api/opportunities/{id}`; `POST …/changes/from-sample` `{"name":"syracuse_addendum_1"}` on OPP-0001; `GET …/rfp-search` with "what short-circuit rating is required?"; `POST /api/knowledge` (treating `Already queued as …` as success). The walkthrough's own state comes from `GET /tour-session` (web app).

### 20.13 Portfolio and traceability views

`GET /api/portfolio` lists every opportunity with unit progress; opening one goes to `GET /api/opportunities/{id}/trace` (plus page images `GET /api/documents/{doc}/pages/{n}.png` for each page shown, and `GET /api/opportunities/{id}/knowledge` for the "sent" badges).

## 21. Screen Load Sequences

Every screen uses the `useApi` hook: it fetches on open, and again whenever the browser tab regains focus or becomes visible, so a page left open never shows stale state. Actions call `post()` and then `reload()` the affected data. Every request carries `X-Actor` from the `actor` cookie.

| Screen (route) | Calls on open (parallel unless stated) | Actions and the calls they make | Re-fetched after the action |
|---|---|---|---|
| Global shell (every page) | `GET /api/people` (Acting as list); `GET /tour-session` (walkthrough) | Change **Acting as**: cookie written, page reloaded | Everything (page reload) |
| Opportunity header and step bar (every opportunity page) | `GET /api/opportunities/{id}`; again every 5 s, on route change and on `opp-status-changed` | - | - |
| Opportunities (`/portfolio`) | `GET /api/portfolio` | Links only | - |
| New opportunity (`/opportunities/new`) | none | **Create**: `POST /api/opportunities` | Navigates to the RFP step |
| RFP (`/opportunities/{id}`) | `GET /api/opportunities/{id}` | Upload: `POST …/documents`; **Refresh status**: `GET /api/opportunities/{id}`; **Search**: `GET …/rfp-search?q=`; reader: `POST …/requirements/extract` | Opportunity; opens Requirements after a clean read |
| Requirements (`…/requirements`) | `GET …/requirements` | review, split, merge, ungroup, history, add, from-lines, baselines (line picker: `GET /api/opportunities/{id}`, `GET /api/documents/{doc}/pages/{n}`, `…/{n}.png`) | `GET …/requirements`; after freeze, `opp-status-changed` |
| Traceability (`…/trace`) | `GET …/trace`; `GET …/knowledge`; page images on demand | **Match products**: `POST …/match`; Accept / Reject: `POST /api/matches/{m}/decide`; Change: `GET /api/catalog` then `POST …/requirements/{req}/match`; Send to knowledge base: `POST /api/knowledge` | `GET …/trace`; `GET …/knowledge` |
| Bid decision (`…/decisions`) | `GET …/decisions`; `GET …/knowledge` | `POST …/participation`; `POST …/go-no-go`; `POST …/dispatch`; Send to knowledge base | `GET …/decisions`; `opp-status-changed` |
| Final response (`…/consolidation`) | `GET …/consolidation` | Downloads (`…/compliance-matrix.csv`, `.xlsx`) open in the browser | - |
| Response outline (`…/consolidation/outline`) | `GET …/response-outline`; `GET …/knowledge` | Download `…/response-outline.md`; Send to knowledge base | `GET …/knowledge` |
| Changes (`…/changes`) | `GET …/changes`; change-document page images on demand | `POST …/changes`; `POST /api/changes/{s}/items/{i}`; `…/confirm-all`; `…/apply`; `…/discard` | `GET …/changes`; `opp-status-changed` |
| My work (`/inbox/{bu}`) | `GET /api/inbox/{bu}`; `GET /api/portfolio` (unit switcher counts) | `POST /api/assignments/{a}/respond`; `POST /api/assignments/{a}/validate`; hand-off link `GET …/handoff/{bu}` | `GET /api/inbox/{bu}` |
| My work redirect (`/inbox`) | `GET /api/people` (the acting person's unit) | Redirect to `/inbox/<unit>` (or `/inbox/BID`) | - |
| Product catalog (`/catalog`) | `GET /api/catalog?q=` | **Search**: `GET /api/catalog?q=<text>` | - |
| Knowledge base (`/knowledge`) | `GET /api/knowledge` | `POST /api/knowledge/{kb}/review` | `GET /api/knowledge` |

## 22. State Machines Driven by the API

### 22.1 Opportunity (`opportunity.status`)

```text
 new --(extract)--> review --(baselines)--> frozen --(go-no-go: go)--> go --(dispatch)--> dispatched
                                               \--(go-no-go: no_go)--> no_go --(go-no-go: go)--> resumes the status before the stop
 (reading, consolidating, submitted are defined but never set by any endpoint)
```

| Transition | Endpoint |
|---|---|
| → `new` | POST /api/opportunities |
| → `review` | POST …/requirements/extract |
| → `frozen` | POST …/baselines |
| → `go` / `no_go` | POST …/go-no-go |
| → `dispatched` | POST …/dispatch |

Moves are forward only; `no_go` can stop the bid at any point before submission, and `go` after `no_go` resumes at the status that the stop replaced. Adding requirements by hand or applying a change set does not change the status.

### 22.2 Document (`document.status`)

```text
 uploaded --(background ingest / POST .../ingest)--> ingesting --> ingested | failed
 unsupported (not a PDF; never read)
```

### 22.3 Requirement (`requirement.status`)

```text
            review: approve                 review: reject
 proposed ------------------> approved <------------------> rejected
    |   \                        |  ^                          |
    |    \ extract (duplicate)   |  | review: approve (restore)|
    |     v                      |  |                          |
    |   duplicate ---------------+--+--------------------------+
    | split / merge / ungroup (group)
    v
 split | merged   (terminal; review their replacement)
 approved (in a baseline) --(change apply: removed)--> removed (new version)
 approved (in a baseline) --(change apply: modified)--> approved, version + 1, baseline N+1
```

Provenance: `EXTRACTED` or `UNANCHORED`. Baseline: null while a draft; 1 after POST …/baselines; N+1 for versions and IDs created by a change set.

### 22.4 Baseline

`POST …/baselines` creates number 1 (once). `POST /api/changes/{s}/apply` creates number N+1 when the set changed anything.

### 22.5 Match (`match.status`)

```text
 (POST .../match) proposed --(decide: accept)--> accepted
                           --(decide: reject)--> rejected   (never re-proposed)
 (POST .../requirements/{req}/match) --> accepted (method manual)
```

### 22.6 Decision

Records, never updated: each `POST …/participation` or `POST …/go-no-go` adds a row; the latest of each kind counts. Kinds `participation` (outcome `units`) and `go_no_go` (outcome `go` or `no_go`).

### 22.7 Assignment (`assignment.status`)

```text
 (dispatch) assigned --(respond)--> submitted --(validate ok)--> validated
                ^                       |
                |                       +--(validate ok=false + note)--> returned --(respond)--> submitted
 (dispatch: unit no longer participates) --> withdrawn --(dispatch: fits again)--> reopened as assigned
 (change apply: requirement modified or removed) validated/submitted --> returned (note "Changed by ...")
```

### 22.8 Change set and change item

```text
 change_set:  (POST .../changes) review --(apply, Bid Manager)--> applied
                                        --(discard, Bid Manager)--> discarded
 change_item: proposed --(items/{i} or confirm-all)--> confirmed  (can be decided again while the set is in review)
```

### 22.9 Knowledge item

```text
 (POST /knowledge) queued --(review approve)--> approved (joins the long-term index)
                          --(review reject + note)--> rejected (may be sent again as a new item)
```
