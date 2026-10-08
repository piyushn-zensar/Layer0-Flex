# Reference code (read-only)

Code from the earlier PoC lines, copied here so everyone can port from it without the old folders.
**Do not import from `reference/`.** Port the piece you need into your module, fix its known defects,
and note the port in your tracker. The module-to-module map is in `team/PLAN.md` (section "Port map").

| Folder | From | Use |
|---|---|---|
| `v0.3.0/` | `layer0-delivery/code/spinco-agentic-cpq` (modules M1-M17, see `COMPONENTS.md`) | ingestion, anchors, registry, tiers, solver, validation, coverage, proposal checker, routing payloads, connectors, model guard |
| `v1.1/` | `CPQ/.../Layer0_Production_Release_20260924_v1.1/CODEBASE` | bid / execution / portfolio rule checks for go/no-go evidence (constants are invented placeholders) |

Known defects to fix while porting are listed in `Documents/architecture-overview.md`.
