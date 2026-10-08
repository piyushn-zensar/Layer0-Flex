---
paths:
  - "Documents/**"
---

# Client-facing documents (`Documents/`)

Everything in `Documents/` is shared with the client point of contact and is the project's source of truth.

- **Neutral voice.** Never name meeting participants (client or Zensar team). No "he said", no "the sponsor", no
  dialogue, no quoted speech. Phrase meeting content impersonally: "The review meeting of 8 Oct 2026 described…".
  In question tables write "Client point of contact".
- **Labels.** Use the existing status labels: **Intended**, **Expected (review meetings)**, **Proposed (inferred
  design)**, **Implemented (by code line)**, **Needs confirmation**. Never present an expectation as built.
- **Keep history.** Mark superseded content as history; do not delete it.
- **Plain English**, short sentences, terms explained on first use, absolute dates (8 Oct 2026, not "tomorrow").
- **Consistency.** Build details live in `technical-architecture.md`; other documents link to it rather than repeat it.
- Team names, task IDs and dates for people belong in `team/`, never in `Documents/`.
- After editing, grep the changed files for team and client names; the result must be empty.
