# Architecture rules (modular monolith, modular MVC)

Applies to all code under `app/` (API) and `web/` (Next.js views).

## Module shape

Each module in `app/modules/<name>/` has:
- `models.py` — its tables (SQLAlchemy 2, `Mapped[...]`). Every table has `opportunity_id` unless it is catalog data.
- `service.py` — business logic and the **public contract**, listed in the module docstring. Keep that list current.
- `controller.py` — FastAPI JSON routes (mounted under `/api`); serialise rows with `app.core.web.row`.
- `agent.py` — only if the module calls the model: system prompt, JSON schema, one function.
- Views: the module's pages in `web/app/...` (Next.js, client components using `web/lib/api.ts`). Add response
  shapes to `web/lib/types.ts`. The web app holds no business logic.

## Boundaries

- Module A may import `app.modules.B.service` only. Never B's models, agent or controller. `tests/test_smoke.py` enforces this.
- No ORM relationships across modules; store the other record's ID (`req_id`, `opportunity_id`).
- `app/core` is shared: config, db, audit, llm (model gateway), web. Do not add business logic there.
- New module? Add it to `MODULES` in `app/main.py` (owner: Piyush) and to the ownership map.

## Behaviour rules (from the design, sections 3 and 6)

- **R1 Trace to source:** requirements carry page, line range, boxes and the verbatim quote. Never invent a location; unfound quotes are `UNANCHORED`.
- **R2 Freeze:** model answers go through `app.core.llm.complete_json`, which caches them in `data/llm_cache/`. Do not call any model SDK (Azure OpenAI) anywhere else. Do not bypass or hand-edit the cache.
- **R4 Agents propose, people decide:** participation, go/no-go, freeze and validation are recorded with the acting person (`app.core.web.actor`).
- **R5 Unknown never passes:** report missing answers, unreadable pages and unanchored items. **No regex or keyword fallback for identifying requirements.** (Retrieval-only matching is an allowed, labelled fallback for routing.)
- **R6 Separate engagements:** requirement IDs are `REQ-<opp number>-<seq>`; every query is scoped by opportunity.
- **R7 Data, not code:** business units, products, past responses, thresholds live in `data/knowledge_base/`.
- **R8 Audit:** every write calls `app.core.audit.record(...)` in the same transaction.
- **Any stage runs:** keep the app runnable end to end. Improve a module behind its unchanged contract.

## Parsing

- RFP parsing (ingestion) runs fully only on the parsing machine (Tesseract). OCR must be optional: if
  `config.TESSERACT_CMD` does not exist, flag the page unreviewed with the reason; never crash.
- Parsed layouts of sample RFPs are frozen in `data/layout_cache/` via `scripts/freeze_layout.py` and committed.
