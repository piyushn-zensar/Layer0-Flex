// Walkthrough chapter 4: New bid and the RFP page (web/app/opportunities/new, web/app/opportunities/[id]).  Owner: Janvia (J-15).
// Explain-only: the walkthrough runs on the seeded OPP-0001, which holds the Syracuse RFP. Since P-32 the same RFP file
// cannot be read twice: uploading it into a new bid opens the bid that already holds it.
import type { TourChapter } from "../types";

const chapter: TourChapter = {
  id: "intake",
  order: 4,
  title: "New bid and the RFP",
  summary: "The New bid form, then the RFP page: the files, what the reader covered, the automatic freeze, the search over the RFP text and the saved focus on the power electronics requirements.",
  entryRoute: "/opportunities/new",
  steps: [
    {
      id: "intake-new",
      title: "New bid: one workspace per RFP",
      route: "/opportunities/new",
      target: "intake-form",
      placement: "right",
      fallback: "The form is on the page when you are signed in as the bid manager.",
      body: [
        "A bid is the container for everything about one RFP: its documents, requirements, matches, assessment, decision, unit answers and compliance matrix. Only the **bid manager** creates bids.",
        "The **title** is required and becomes the heading of every page in the bid. **Customer** is optional and only labels the bid. **Customer type** (utility, hyperscaler, neocloud, colocation, silicon provider, public sector) is a label in this proof of concept; the agents read the RFP, not this field. **Create** opens the new bid's RFP page.",
        "The walkthrough does not create a bid: it works on **OPP-0001**, the Syracuse RFP, which is already read.",
      ],
    },
    {
      id: "intake-rfp-docs",
      title: "The RFP page: documents",
      route: "/opportunities/{opp}",
      target: "rfp-docs-table",
      placement: "bottom",
      fallback: "The table lists the files stored in this bid.",
      body: [
        "This is the first step of a bid. The table lists every file with its **document type** (Main RFP, Addendum, Clarification / Q&A, Change request, Other), page count, reading status and the date it was received. The Syracuse RFP is one 101-page main RFP, status *Read*. Word and Excel files are read too (RC-1 is a Word file with 19 tables; table rows are kept as text).",
        "Files are stored once under their SHA-256 fingerprint and never modified. On a **new** bid this page also holds the upload form for the main RFP and the button that reads it.",
      ],
    },
    {
      id: "intake-known",
      title: "One RFP is read once",
      route: "/opportunities/{opp}",
      body: [
        "Every uploaded file is identified by the **Document ID and Instance ID** embedded in it (PDF, Word), with a SHA-256 fingerprint when the file has none. If the same file is uploaded into a new bid, Layer 0 does not read it again: it **opens the bid that already holds it**, with its stored, frozen requirements, and says so. A *newer instance* of a known RFP names the bid that holds the earlier one and offers to add it there as a change document.",
        "**Add another document** takes addenda, clarification / Q&A answers and change requests after the freeze; they are compared with the frozen requirements on the Changes page (chapter 11), not merged silently.",
      ],
    },
    {
      id: "intake-coverage",
      title: "What the reader covered",
      route: "/opportunities/{opp}",
      target: "rfp-coverage",
      placement: "top",
      fallback: "The coverage card shows RFP reading 1, the first reading of the bid.",
      body: [
        "**RFP reading 1** records exactly what the reader did and is never altered: 101 pages = 100 read + 0 failed + 1 skipped (contents, blank) + 0 not readable; 818 statements read, grouped into 312 requirements (161 groups); 12 need a source check; 27 duplicates. Unread pages and quotes that could not be located are reported, never hidden.",
        "A read that completes with no failed page **freezes the register at once** as frozen version 1. After that the RFP is not read again: edits, splits, merges, exclusions and missed requirements are saved as **corrections with a reason**, each a new version, and customer changes come in through Changes.",
      ],
    },
    {
      id: "intake-search",
      title: "Search this RFP",
      route: "/opportunities/{opp}",
      target: "rfp-search",
      placement: "top",
      fallback: "The search box asks a question in plain words and returns passages with page and lines.",
      body: [
        "A short-term index is built per RFP: ask in plain words (for example \"what short-circuit rating is required?\") and the best passages come back with page and lines. When embeddings are not available it falls back to keyword ranking and says so. The index is private to this bid.",
      ],
    },
    {
      id: "intake-focus",
      title: "Focus: the power electronics requirements",
      route: "/opportunities/{opp}",
      target: "rfp-saved-views",
      placement: "bottom",
      fallback: "For the Syracuse RFP a Focus line above the documents links to its power electronics requirements.",
      body: [
        "For the Syracuse RFP the page offers a saved **Focus** view: **Power electronics requirements (Crown, EP², Anord Mardix)**. It opens Requirement Traceability filtered to the technical requirements of those three units, so the demo can concentrate on the power electronics part of a switchgear procurement. It is only a filter link; nothing in the register changes.",
      ],
      instruction: "Press Next to open Requirement Traceability.",
    },
  ],
};
export default chapter;
