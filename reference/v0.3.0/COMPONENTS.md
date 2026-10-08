# Component Manifest — v0.3.0

**Read this before building anything.** This file exists because a component
(the model-change guard) was once rebuilt from scratch because nobody knew it
already existed. Check here first. If a capability is listed as BUILT, do not
re-implement it — extend it.

| ID | Component | File(s) | Status | Since |
|----|-----------|---------|--------|-------|
| M1 | Ingestion + boundary classifier | `ingestion/ingest.py` | BUILT & TESTED | 0.2 |
| M2 | Extraction | `agents/understand_agent.py` | BUILT & TESTED | 0.1 |
| M3 | Scope detection | `agents/understand_agent.py::_detect_layers_in_scope` | BUILT & TESTED | 0.2 |
| M4 | Tier classification | `agents/tier_classifier.py` | BUILT & TESTED | 0.2 |
| M5 | Validation (deterministic rules) | `agents/validation_agent.py` + `knowledge_base/engineering_rules.json` | BUILT; physical bounds are generic NEC/IEC | 0.1 |
| M6 | Evidence / explainability contract | every agent returns `explanation` + `evidence` | BUILT & TESTED | 0.1 |
| M7 | Orchestration + approval gate (6 stages) | `orchestration/pipeline.py`, `orchestration/state_store.py` | BUILT & TESTED | 0.2 |
| M8 | Routing payload adapters | `routing/*.py` | 3 of 4 files WRITTEN, NOT WIRED | 0.2 |
| M9 | Connector abstraction | `connectors/*.py` | INTERFACE STUBS only | 0.1 |
| M10 | Model runtime adapter (the only LLM seam) | `agents/base_agent.py` | BUILT & TESTED | 0.1 |
| M11 | Provenance (span anchors, 3 classes) | `provenance/anchors.py` | BUILT & TESTED | 0.2 |
| M13 | Solver (LV power arithmetic) | `agents/solver.py` | BUILT & TESTED | 0.2 |
| M14 | Coverage map | `agents/coverage.py` | BUILT & wired; segmentation weak on full PDFs | 0.2 |
| M15 | Proposal checker | `agents/coverage.py::check_proposal` | BUILT & TESTED, NOT WIRED to UI | 0.2 |
| M16 | Model-change guard | `agents/model_guard.py` + `knowledge_base/accepted_extractions.json` | BUILT & TESTED | 0.3 |
| M17 | REQ-xxxx requirement registry | `models/registry.py`, `models/registry_builder.py` | BUILT & TESTED, NOT WIRED to UI | 0.3 |
| — | Frontend (upload, tiers, scope evidence, solver, coverage, anchors) | `frontend/index.html` | BUILT | 0.2 |
| — | Version single-source | `VERSION`, `_version.py` | BUILT | 0.3 |

## Not built (deliberately deferred — do not assume these exist)

- OCR for scanned pages
- Live connector integrations (QuoteWin / SAP / Infor LN / aPriori)
- Addenda / clarification handling; the case ledger
- Human split/merge/edit of requirements (schema supports it; ops not built)
- Layout-aware + LLM clause segmentation (the real fix for M14 on full PDFs)
- Hybrid/GraphRAG retrieval (RAG is TF-IDF only)

## How to check before you build

```bash
cat COMPONENTS.md              # is it already here?
cat CHANGELOG.md               # what changed recently?
grep -rl "keyword" --include="*.py" .   # does something already do this?
```
