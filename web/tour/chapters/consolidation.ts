// Walkthrough chapter 9: Final response (coverage check, compliance matrix exports) and the Response outline.
// Runs on the walkthrough opportunity ({opp}); every step reads the page as it is, so it works at any stage
// (nothing frozen, open requirements, or every requirement answered).  Owner: consolidation/changes page group.
import type { TourChapter, TourCtx } from "../types";
import { onRoute, openDetails, present } from "../helpers";

const CONS = "/opportunities/{opp}/consolidation";
const OUTLINE = "/opportunities/{opp}/consolidation/outline";
const missing = (id: string) => (ctx: TourCtx) => ctx.el(id) === null;
const pressed = (tourId: string, nth: number) => (ctx: TourCtx) =>
  ctx.el(tourId)?.querySelectorAll(".chip")[nth]?.getAttribute("aria-pressed") === "true";

const chapter: TourChapter = {
  id: "consolidation",
  order: 9,
  title: "Final response, exports and the outline",
  summary: "The coverage check that says which requirements are answered and why the rest are not, the compliance matrix as Excel and CSV, and the drafting agent's response outline with its citations.",
  entryRoute: CONS,
  steps: [
    {
      id: "consolidation-intro",
      title: "Final response: is every requirement answered?",
      route: CONS,
      body: [
        "This screen is the **coverage check** for the final response. It runs against the frozen baseline (the requirements approved on the Requirements page) and against the unit answers that came back through the Inbox.",
        "The rule is strict and simple: a requirement is **answered** only when every assignment for it is **validated** by the Bid Manager. An answer that is still with the unit, submitted but not validated, or returned, blocks completion. Nothing is estimated: the page counts states, it does not judge content.",
        "From here you download the compliance matrix (Excel for the customer, CSV for tracking) and open the Response outline, the drafting agent's first draft. Before leaving, know how many requirements are still open and who holds them: that is the work left before submission.",
      ],
    },
    {
      id: "consolidation-count",
      title: "The answered count",
      route: CONS,
      target: "cons-summary",
      placement: "bottom",
      fallback: "The summary line reads 'answered / total requirements answered' and, in red, how many still need an answer. It is not shown until the baseline is frozen.",
      body: [
        "**answered / total**: the total is the number of requirements in the frozen baseline (348 for the Syracuse RFP); answered counts the rows whose assignments are all validated. In the seeded demo that is **1 / 348**, with **347 still need an answer** in red. When nothing is left, the line turns green: *Every requirement is answered.*",
        "The same numbers feed the opportunity header, the portfolio and the Response outline, so they always agree. The count changes only through the Inbox (a unit submits, the Bid Manager validates) or through Changes (an addendum returns answers for review).",
      ],
    },
    {
      id: "consolidation-blockers",
      title: "Needs an answer: the blockers by reason",
      route: CONS,
      target: "cons-blockers",
      placement: "bottom",
      skipIf: missing("cons-blockers"),
      fallback: "The 'Needs an answer' panel only appears while some requirement is open.",
      body: [
        "Every open requirement is grouped by **why** it is open, derived from its assignments: **Waiting for validation** (a unit submitted, the Bid Manager has not validated), **Waiting for the unit** (still assigned), **Returned** (sent back to the unit with a note) and **Not assigned** (no work package yet: dispatch has not run, or the requirement was added after it).",
        "A requirement with several units takes the most urgent reason: returned outranks waiting for the unit, which outranks waiting for validation. Each group lists up to 10 requirement IDs; a **'N more'** toggle shows the rest.",
        "Every ID is a link into **Traceability** (`/trace#REQ-…`), which opens the requirement on its RFP page with its units and answers: the quickest way from 'what is missing' to 'who do I ask'.",
      ],
    },
    {
      id: "consolidation-filter",
      title: "All or Open",
      route: CONS,
      target: "cons-filter",
      placement: "bottom",
      kind: "action",
      skipIf: missing("cons-filter"),
      instruction: "Click Open to show only the requirements that still need an answer.",
      done: pressed("cons-filter", 1),
      fallback: "The All / Open filter sits above the table once the baseline is frozen.",
      body: [
        "Two chips with their counts: **All** (every requirement of the baseline, in RFP order) and **Open** (only the rows that still block completion). The pressed chip is the active one; the filter is per visit and changes nothing on the server.",
        "Use Open when preparing the chase list before a deadline; use All when checking a finished response end to end.",
      ],
    },
    {
      id: "consolidation-table",
      title: "The coverage table",
      route: CONS,
      target: "cons-table",
      placement: "top",
      skipIf: missing("cons-table"),
      fallback: "The table lists one row per requirement of the frozen baseline.",
      body: [
        "One row per requirement of the frozen baseline, in RFP order. **ID** links to Traceability and shows the source underneath (*p. 55, lines 7-65*: the page and lines the requirement is anchored to; a requirement revised by an addendum names that file first). **Requirement** is the short text the reader agent wrote and a person approved.",
        "Rows that still block completion carry a light warning background, so the open ones stand out even in the All view. Sub-requirements of a group are not separate rows here: the group is answered as one.",
      ],
    },
    {
      id: "consolidation-units",
      title: "Units and responses",
      route: CONS,
      target: "cons-col-units",
      placement: "bottom",
      skipIf: missing("cons-col-units"),
      fallback: "The 'Units and responses' column shows each unit's answer and status.",
      body: [
        "One line per assignment: the **unit code** (CROWN, for example), the **compliance** the unit chose (*met*, *partial*, *not met*, *exception*; grey *no compliance yet* until it answers), the **product** it offers when it named one, and the assignment **status** badge: *assigned*, *submitted*, *validated*, *returned* or *withdrawn*.",
        "A requirement dispatched to two units shows two lines and is answered only when both are validated. *not assigned* in grey means no work package exists for it yet.",
      ],
    },
    {
      id: "consolidation-state",
      title: "State and reason",
      route: CONS,
      target: "cons-col-state",
      placement: "left",
      skipIf: missing("cons-col-state"),
      fallback: "The State column holds the computed state: answered, pending or not assigned.",
      body: [
        "The computed state: **answered** (green) when every assignment is validated, **pending** (amber) while any is not, **not assigned** when there is none. Under a pending state the reason label repeats the group from the blockers panel (*Waiting for validation*, *Waiting for the unit*, *Returned*).",
        "This state is what the exports write in their *State* column and what the Response outline uses to decide which requirements may be drafted and which are listed as still open.",
      ],
    },
    {
      id: "consolidation-xlsx",
      allowInteraction: true, // the point of this step is a link or download inside the spotlight
      title: "Download compliance matrix (Excel)",
      route: CONS,
      target: "cons-xlsx",
      placement: "bottom",
      fallback: "The Excel download is the primary button in the page header.",
      body: [
        "The workbook `OPP-xxxx-compliance-matrix.xlsx` is written by code from the stored answers, never by a model. It has two sheets.",
        "**Compliance matrix** is for the customer: one row per requirement in RFP order, a group's sub-requirements listed under it with their own RFP reference, and the compliance in customer words: *Comply*, *Partially comply*, *Does not comply*, *Exception*, or **Open** until every unit's answer is validated. When two units answered, the worst word wins. Only validated responses are written; open rows have no response text.",
        "**Tracking** is internal: the same columns as the CSV, one row per unit answer, including who responded and who validated. Every cell is plain text, so a value that starts like a formula (`=`, `+`, `-`, `@`) cannot run when the file is opened.",
      ],
    },
    {
      id: "consolidation-csv",
      allowInteraction: true, // the point of this step is a link or download inside the spotlight
      title: "CSV export",
      route: CONS,
      target: "cons-csv",
      placement: "bottom",
      fallback: "The CSV download sits next to the Excel button.",
      body: [
        "`OPP-xxxx-compliance-matrix.csv`: one row per assignment (a requirement without one still gets a row) with the columns *Requirement ID, Source, Category, Requirement, Quote, Business unit, Product, Offering type, Compliance, Response, Validated by, State, Assignment status, Responded by*. The last two were appended later, so earlier column positions never moved.",
        "The file starts with a UTF-8 byte order mark so Excel reads accents correctly, and cells that start like a formula are quoted. Use it for pivot tables and progress tracking; the Excel workbook is the one to send.",
      ],
    },
    {
      id: "consolidation-empty",
      title: "Nothing frozen yet",
      route: CONS,
      target: "cons-empty",
      placement: "bottom",
      skipIf: missing("cons-empty"),
      fallback: "When the baseline is not frozen the page shows 'No requirements in the baseline yet'.",
      body: [
        "This opportunity has no frozen baseline, so there is nothing to check coverage against. Approve the requirements and **Freeze baseline** on the Requirements page; the coverage check, the exports and the outline all read the frozen baseline, never the proposed list.",
      ],
    },
    {
      id: "consolidation-to-outline",
      title: "Open the Response outline",
      route: CONS,
      target: "cons-outline-link",
      placement: "bottom",
      kind: "action",
      instruction: "Click 'Response outline (draft)'.",
      done: onRoute(OUTLINE),
      fallback: "The 'Response outline (draft)' button is in the page header.",
      body: [
        "The outline is the drafting agent's first draft of the response, chapter by chapter, written **only from validated answers**. It is marked *draft* on purpose: writing the final response stays a human task, and the outline gives the bid manager a sourced starting point rather than a blank page.",
      ],
    },
    {
      id: "outline-intro",
      title: "Response outline: a first draft with its sources",
      route: OUTLINE,
      target: "outline-summary",
      placement: "bottom",
      fallback: "The summary line shows the Draft badge and 'answered / total requirements answered and validated'.",
      body: [
        "The **Draft** badge and the line *answered / total requirements answered and validated (N validated answers)* set the scope: the agent sees only validated answers (one in the seeded demo, on REQ-0001-0887), nothing from answers still in review, and nothing it invents.",
        "How it works: one model call per chapter that has validated answers, plus one for the executive summary. The prompt holds the numbered answers with the RFP's own wording and two past responses per unit for tone only. The answer must cite the numbers each paragraph rests on; a paragraph without a valid citation is **dropped** by a guard, never shown. No requirement ID is in the prompt, so the frozen answer stays valid when IDs change.",
        "What to do here: read each chapter, follow the citations into Traceability, use *To add or confirm* as the to-do list, then download the Markdown and edit it in the proposal template. Nothing on this page writes to the server.",
      ],
    },
    {
      id: "outline-exec",
      title: "Executive summary",
      route: OUTLINE,
      target: "outline-exec",
      placement: "bottom",
      fallback: "The executive summary is the first card of the outline.",
      body: [
        "Drafted in one small call from the first validated answers in RFP order (at most 40), in the third person (*the proposer*), in plain formal English, keeping the customer's terms from the RFP wording. It states only what those answers say: no product, rating, standard, date or price that an answer does not contain, and never a partial answer promoted to full compliance.",
        "If no answer is validated yet, or the model has no answer for this exact material (mock mode), the card says *Not drafted* with the reason instead of guessing.",
      ],
    },
    {
      id: "outline-drafted",
      title: "Paragraphs and their citations",
      route: OUTLINE,
      target: "outline-drafted",
      placement: "bottom",
      skipIf: missing("outline-drafted"),
      fallback: "A drafted chapter shows its paragraphs followed by the requirement IDs they cite.",
      body: [
        "Each paragraph ends with its sources in brackets, e.g. **[REQ-0001-0887]**: the requirements whose validated answers the paragraph rests on, as links into Traceability. In the demo the technical chapter says the proposer offers a two-section 15 kV arc-resistant metal-clad lineup, because that is what Crown Technical Systems answered and the Bid Manager validated.",
        "Citations are the guard: the agent answers with answer numbers, the service maps them back to requirement IDs, and a paragraph whose numbers are missing or out of range is dropped (the count of dropped paragraphs appears in the note under the chapter). A citation you cannot verify in Traceability is a reason to rewrite the paragraph, not to trust it.",
      ],
    },
    {
      id: "outline-gaps",
      title: "To add or confirm",
      route: OUTLINE,
      target: "outline-gaps",
      placement: "bottom",
      skipIf: missing("outline-gaps"),
      fallback: "'To add or confirm' lists what the bid manager still has to add before a chapter can go to the customer.",
      body: [
        "Up to four short items per chapter: what the bid manager still has to add or confirm before the chapter can go to the customer, e.g. *Confirm compliance with all specific accessory requirements mentioned in the RFP* or *Verify the inclusion of protective relay and controls in the proposed lineup*.",
        "These are the agent's view of what the validated answers do not cover; treat them as a checklist for the human writer, and expect them to shrink as more answers are validated.",
      ],
    },
    {
      id: "outline-not-drafted",
      title: "Not drafted: nothing is guessed",
      route: OUTLINE,
      target: "outline-not-drafted",
      placement: "bottom",
      skipIf: missing("outline-not-drafted"),
      fallback: "A chapter without validated answers, or without a model answer, reads 'Not drafted: …'.",
      body: [
        "A chapter reads **Not drafted** with its reason in two cases: it has no validated answer yet (most chapters of the demo, where 347 requirements are still open), or the model service has no answer for this exact material (offline mock mode with an answer that was never frozen). In both cases the validated answers are still listed below as they are.",
        "This is deliberate: a draft that invents content to fill a chapter would be worse than an empty one. Validate more answers in the Inbox and the chapter fills in.",
      ],
    },
    {
      id: "outline-chapter",
      title: "Chapters follow the requirement categories",
      route: OUTLINE,
      target: "outline-chapter-1",
      placement: "top",
      skipIf: missing("outline-chapter-1"),
      fallback: "Chapters appear once the baseline is frozen; each one covers one category group.",
      body: [
        "The chapters are fixed by category, not by the model: **Technical response** (technical), **Compliance, legal and contract terms** (compliance, legal), **Commercial terms and schedule** (commercial, schedule), **Project team and staffing** (staffing), **Submission requirements** (submission) and **Other requirements**. A chapter appears only when the baseline has requirements in it; the heading shows *answered of total* for that chapter (the demo's technical chapter: 1 of 146).",
        "Under the draft, each chapter has the same expandable blocks: the validated answers it rests on, what is still open, and related passages from both retrieval indexes.",
      ],
    },
    {
      id: "outline-exceptions",
      title: "Not full compliance",
      route: OUTLINE,
      target: "outline-exceptions",
      placement: "bottom",
      skipIf: missing("outline-exceptions"),
      fallback: "A warning lists validated answers whose compliance is not 'Comply', when there are any.",
      body: [
        "An amber **Not full compliance** warning lists every validated answer in the chapter whose compliance is not *Comply*: *REQ-… Unit: Partially comply / Does not comply / Exception*. The drafting agent is told never to turn these into full compliance; the warning makes sure the writer does not either.",
      ],
    },
    {
      id: "outline-answers",
      title: "Validated answers",
      route: OUTLINE,
      target: "outline-answers",
      placement: "top",
      skipIf: missing("outline-answers"),
      onEnter: openDetails("outline-answers"),
      fallback: "'Validated answers (N)' expands to the table of answers the chapter was drafted from.",
      body: [
        "The material behind the draft: one row per validated answer with the **Requirement** ID and its source, the **Unit** and the product it named, the **Compliance** badge and the **Answer** text as the unit wrote it. In the demo: REQ-0001-0887 (p. 55, lines 7-65), Crown Technical Systems, Comply, *Two-section 15 kV arc-resistant metal-clad lineup offered.*",
        "The last column, **Knowledge base**, sends a good answer to the house knowledge base so later bids can reuse it; the Knowledge chapter shows that flow.",
      ],
    },
    {
      id: "outline-open",
      title: "Still open",
      route: OUTLINE,
      target: "outline-open",
      placement: "top",
      skipIf: missing("outline-open"),
      onEnter: openDetails("outline-open"),
      fallback: "'Still open (N)' lists the chapter's requirements that have no validated answer yet.",
      body: [
        "The chapter's requirements without a validated answer, with ID, source and short text: the first 8, then *and N more: see Final response*. These are exactly the pending and not-assigned rows of the coverage table for this category.",
        "Nothing is drafted for them, so the chapter's draft is only as complete as this list is short.",
      ],
    },
    {
      id: "outline-refs",
      title: "Related passages from both indexes",
      route: OUTLINE,
      target: "outline-refs",
      placement: "top",
      skipIf: missing("outline-refs"),
      onEnter: openDetails("outline-refs"),
      fallback: "'Related passages' shows search hits from the RFP index and the knowledge base for the chapter's topic.",
      body: [
        "Two searches for the chapter's title and first requirements, shown beside the draft but **never put in the prompt** (so the frozen draft does not depend on retrieval): **In this RFP** returns up to three passages with *p. N, lines a-b* from the RFP's own index; **Past responses** returns up to three house answers from the knowledge base, marked *illustrative*.",
        "The label in brackets (*embeddings search* or *keyword search*) names how each index runs right now. Use these to check the draft against the RFP's wording and the house style before editing.",
      ],
    },
    {
      id: "outline-download",
      allowInteraction: true, // the point of this step is a link or download inside the spotlight
      title: "Download outline (Markdown)",
      route: OUTLINE,
      target: "outline-download",
      placement: "bottom",
      fallback: "The Markdown download is the primary button in the page header.",
      body: [
        "`OPP-xxxx-response-outline.md` is the same outline as text to paste into the proposal template: a title, a *DRAFT for the bid manager to edit* line with the answered count, *## Executive summary*, then one *## N. Chapter* section each with its paragraphs and `[REQ-…]` citations, *- To add or confirm:* items, *### Validated answers* and *### Still open*.",
        "A chapter that was not drafted says so in italics in the file too. The download is regenerated on each click from the current answers, so re-download after more answers are validated.",
      ],
    },
    {
      id: "outline-back",
      title: "Where this leads",
      route: OUTLINE,
      target: "outline-back",
      placement: "bottom",
      fallback: "'Back to Final response' returns to the coverage check.",
      body: [
        "The loop is: Inbox validates answers → Final response shows what is still open → the outline drafts what is validated → the Markdown goes into the proposal. When a customer issues an addendum, the Changes page (chapter 11) revises the baseline and returns the affected answers, and both pages here follow automatically.",
        "Next: the Knowledge base, where validated answers and documents are kept for the next bid.",
      ],
    },
  ],
};
export default chapter;
