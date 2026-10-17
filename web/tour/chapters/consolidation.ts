// Walkthrough chapter 9: Compliance matrix (coverage, filters, detail, exports), the Response outline and the Activity log.
// Runs on the walkthrough bid ({opp}); every step reads the page as it is, so it works at any stage.  Owner: Janvia (J-15).
import type { TourChapter, TourCtx } from "../types";
import { onRoute, openDetails, present } from "../helpers";

const CONS = "/opportunities/{opp}/consolidation";
const OUTLINE = "/opportunities/{opp}/consolidation/outline";
const ACT = "/opportunities/{opp}/consolidation/activity";
const missing = (id: string) => (ctx: TourCtx) => ctx.el(id) === null;
const pressed = (tourId: string, nth: number) => (ctx: TourCtx) =>
  ctx.el(tourId)?.querySelectorAll(".chip")[nth]?.getAttribute("aria-pressed") === "true";

const chapter: TourChapter = {
  id: "consolidation",
  order: 9,
  title: "Compliance matrix, outline and Activity",
  summary: "The compliance matrix and its blockers, filters, row detail and history, the Excel and CSV exports, the response outline with its citations, and the Activity log.",
  entryRoute: CONS,
  steps: [
    {
      id: "consolidation-intro",
      title: "Compliance matrix: is every requirement answered?",
      route: CONS,
      body: [
        "The **Compliance matrix** is the fourth step and the bid manager's consolidation: every requirement with the answer of the unit that owns it. It runs against the frozen baseline and the answers that came back through My work.",
        "The rule is strict: a requirement is **answered** only when every item for it is **validated** (by the unit manager, or by the bid manager for the bid desk's items). An item still with the unit, submitted but not validated, or returned blocks completion. Nothing is estimated: the page counts states, it does not judge content.",
        "From here you open the Response outline (the drafting agent's first draft), the Activity log, and download the matrix as Excel for the customer or CSV for tracking.",
      ],
    },
    {
      id: "consolidation-count",
      title: "The answered count",
      route: CONS,
      target: "cons-summary",
      placement: "bottom",
      fallback: "The summary line reads 'answered / total requirements answered' and, in red, how many still need an answer.",
      body: [
        "**answered / total**: the total is the number of requirements in the baseline (312 for the Syracuse RFP); answered counts requirements whose items are all validated. In the seeded demo that is **1 / 312**, with **311 still need an answer** in red. When nothing is left, the line turns green. The count changes through My work (a unit submits, the unit manager validates) or through Changes (an addendum returns answers for review).",
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
        "Every open requirement is grouped by **why** it is open: **Waiting for validation** (1 on the demo), **Waiting for the unit** (195, still assigned), **Returned** (sent back with a note) and **Not assigned** (115 product requirements no participating unit holds; assign a unit in Traceability or record a capability gap on the Assessment page). A requirement with several units takes the most urgent reason.",
        "Each group lists up to ten requirement IDs, with a toggle for the rest. Every ID links into **Requirement Traceability**: the quickest way from \"what is missing\" to \"who do I ask\".",
      ],
    },
    {
      id: "consolidation-filter",
      title: "Search and filters",
      route: CONS,
      target: "cons-filter",
      placement: "bottom",
      body: [
        "Search by requirement text, ID, unit, product or response, and filter by **unit**, **compliance** (Fully, Partially, Non-compliant), **state** and **category**. **Open only** (311) shows what still needs an answer; **Clear filters** resets everything. The count beside it says how many rows match and that the table shows the first 100.",
      ],
    },
    {
      id: "consolidation-table",
      title: "The matrix: one row per requirement and unit answer",
      route: CONS,
      target: "cons-table",
      placement: "top",
      body: [
        "Each row is a requirement and one unit's answer to it, with the requirement's **category**, the **unit**, the **response** state, the **compliance** and the **source** page and lines. A requirement owned by two units appears twice: the schedule, commercial and staffing items go to the unit managers of both Crown and EP², so the 312 requirements make 337 rows. The ID links to the requirement in Traceability.",
        "**Click a row** to open its detail panel: the unit's **Reason**, **Conditions**, **Workaround** and **Next steps** (*Not provided* when blank), the source page with the highlighted lines, a link to Traceability and the answer's history. Hovering a *Partially compliant* or *Non-compliant* badge shows the reason.",
      ],
    },
    {
      id: "consolidation-units",
      title: "Unit",
      route: CONS,
      target: "cons-col-units",
      placement: "bottom",
      body: [
        "The unit column gives the code (**BID** for the bid desk, **CROWN**, **EP2**) and the unit's name. A requirement nobody holds reads *not assigned*.",
      ],
    },
    {
      id: "consolidation-state",
      title: "Response state and History",
      route: CONS,
      target: "cons-col-state",
      placement: "bottom",
      body: [
        "The state is *assigned*, *submitted*, *validated* or *returned*, or *not assigned*. Rows with an assignment have a **History** link: every change to that answer with who, when, the note and the before-and-after, read from the audit log.",
      ],
    },
    {
      id: "consolidation-xlsx",
      allowInteraction: true,
      title: "Download the compliance matrix (Excel)",
      route: CONS,
      target: "cons-xlsx",
      placement: "bottom",
      body: [
        "The Excel workbook has two sheets. The **customer sheet** has a title block, a frozen header row, filters and wrapped text, and carries only **validated** answers: Fully, Partially or Non-compliant, with Reason, Conditions, Workaround and Next steps, the source page and lines and the offering type colours; everything else reads *Open*. The **Tracking sheet** is the internal view with the CSV columns. It is built deterministically, with no model call.",
      ],
    },
    {
      id: "consolidation-csv",
      allowInteraction: true,
      title: "Download the CSV",
      route: CONS,
      target: "cons-csv",
      placement: "bottom",
      body: [
        "The CSV is the same rows for tracking and analysis, with the assignment status and who responded, and a byte order mark so Excel reads non-ASCII text correctly. Cells that could be read as formulas are quoted.",
      ],
    },
    {
      id: "consolidation-activity-link",
      title: "Activity log",
      route: CONS,
      target: "cons-activity-link",
      placement: "bottom",
      body: [
        "**Activity log** opens the bid's audit log; the last steps of this chapter look at it. The same page is linked as **Activity** in the bid header.",
      ],
    },
    {
      id: "consolidation-to-outline",
      title: "Response outline (draft)",
      route: CONS,
      target: "cons-outline-link",
      placement: "bottom",
      body: [
        "**Response outline (draft)** opens the drafting agent's first outline of the response, built only from **validated** answers, each paragraph citing the requirements behind it. Nothing is invented: requirements without a validated answer are listed as open, never drafted.",
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
        "The **Draft** badge and the line *answered / total requirements answered and validated (N validated answers)* set the scope: the agent sees only validated answers (one in the seeded demo, on REQ-0001-0885), nothing from answers still in review, and nothing it invents.",
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
        "Each paragraph ends with its sources in brackets, e.g. **[REQ-0001-0885]**: the requirements whose validated answers the paragraph rests on, as links into Traceability. In the demo the technical chapter says the proposer offers a two-section 15 kV arc-resistant metal-clad lineup, because that is what Crown Technical Systems answered and the Bid Manager validated.",
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
        "A chapter reads **Not drafted** with its reason in two cases: it has no validated answer yet (most chapters of the demo, where most requirements are still open), or the model service has no answer for this exact material (offline mock mode with an answer that was never frozen). In both cases the validated answers are still listed below as they are.",
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
      fallback: "Chapters appear once the register has been read; each one covers one category group.",
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
        "The material behind the draft: one row per validated answer with the **Requirement** ID and its source, the **Unit** and the product it named, the **Compliance** badge and the **Answer** text as the unit wrote it. In the demo: REQ-0001-0885 (p. 55, lines 16-62), Crown Technical Systems, Comply, *Two-section 15 kV arc-resistant metal-clad lineup offered.*",
        "The last column nominates a good answer as a **reviewed example** so later bids can reuse it; the unit's reviewer approves it in Knowledge review in My work.",
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
        "The chapter's requirements without a validated answer, with ID, source and short text: the first 8, then *and N more: see Compliance matrix*. These are exactly the pending and not-assigned rows of the coverage table for this category.",
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
      fallback: "'Back to Compliance matrix' returns to the matrix.",
      body: [
        "The loop is: the unit manager validates answers in My work → the Compliance matrix shows what is still open → the outline drafts what is validated → the Markdown goes into the proposal. When a customer issues an addendum, the Changes page (chapter 11) revises the baseline and returns the affected answers, and both pages here follow automatically.",
        "Next: the Activity log of this bid, then the Product catalog.",
      ],
    },
    {
      id: "activity-intro",
      title: "Activity: the audit log of the bid",
      route: ACT,
      target: "act-count",
      placement: "bottom",
      fallback: "The Activity page lists the bid's events, newest first.",
      body: [
        "**Activity** (also reached from the matrix and the bid header) lists everything done on the bid, newest first: reads, corrections, matches, participation, sends, answers, validations, returns, decisions and changes, each with the person and the time. It is read-only and comes from the append-only audit log, so it cannot be edited.",
      ],
    },
    {
      id: "activity-filters",
      title: "Filters",
      route: ACT,
      target: "act-filters",
      placement: "bottom",
      body: [
        "Filter by **type** of event, **requirement**, **unit** and **person**. The filters are kept in the page address, so a filtered view can be shared. *Show older events* pages back without repeating rows.",
      ],
    },
    {
      id: "activity-table",
      title: "Events and answer history",
      route: ACT,
      target: "act-table",
      placement: "top",
      body: [
        "Each row names the event, the requirement it concerns, who did it and when. The same facts appear as **History** on a requirement (pane 2 of Traceability) and on an answer in the matrix, where a row's detail panel also links to *All activity for REQ-…*.",
      ],
    },
  ],
};
export default chapter;
