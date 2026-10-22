// Walkthrough chapter 6: Traceability and proposed solutions (app/opportunities/[id]/trace, components/matching/MatchActions).
// Targets are data-tour ids on the trace page; "trace-sel-*" and "match-*" sit on the selected row only. "trace-match-button"
// (Propose solutions) is shown only to the bid manager before the go/no-go is recorded; the steps fall back to text otherwise.
import type { TourChapter, TourCtx } from "../types";
import { present, statusIn, textIn, openDetails } from "../helpers";

const ROUTE = "/opportunities/{opp}/trace";
/** Statuses in which matching has already been run and acted on (the seeded demo is "dispatched"). */
const DECIDED = ["go", "no_go", "dispatched", "consolidating", "submitted"];

// Rows of pane 3 (the same requirement order as pane 2); selecting one selects it in all three panes.
const rows3 = (ctx: TourCtx) => Array.from(ctx.el("trace-table-3")?.querySelectorAll<HTMLElement>("tr[data-req]") ?? []);
const selectedRow = (ctx: TourCtx) => rows3(ctx).find((tr) => tr.classList.contains("selected"));
const hasUnit = (tr: HTMLElement) => tr.querySelector(".trace-unit") !== null;
/** P-44: a proposed match the signed-in user may act on (its Accept is enabled: the API's can_change). */
const canAct = (tr: HTMLElement) => [...tr.querySelectorAll<HTMLButtonElement>(".row-actions button")].some((b) => b.textContent === "Accept" && !b.disabled);
/** Select the first row that satisfies `pick` unless the selected row already does (a click on the row = the page's select()). */
const selectRow = (pick: (tr: HTMLElement) => boolean) => (ctx: TourCtx) => {
  const current = selectedRow(ctx);
  if (current && pick(current)) return;
  rows3(ctx).find(pick)?.click();
};
const matched = (ctx: TourCtx) => rows3(ctx).some((tr) => tr.querySelector(".match-meta") !== null);
const currentReq = () => decodeURIComponent(window.location.hash.slice(1));

const chapter: TourChapter = {
  id: "trace",
  order: 6,
  title: "Traceability and proposed solutions",
  summary: "Follow every requirement from the RFP page to the unit and its proposed solution that will answer it: propose solutions, read a match; the unit's designer / engineer accepts or corrects it.",
  entryRoute: ROUTE,
  steps: [
    {
      id: "trace-intro", route: ROUTE,
      title: "Requirement Traceability: three panes",
      body: [
        "This is **Requirement Traceability**, the second step of the workflow and the page most people work from. Pane 1 is the original RFP page with the requirement's lines highlighted, pane 2 is the requirement register (chapter 5) and pane 3 is the proposed solution with the units' responses.",
        "It exists because every answer in a bid must trace back to the customer's own words. Selecting a requirement in any pane selects it in all three, and every pane that is **Linked** follows it (pane 1 turns to its source page), so a reviewer can check in seconds whether a requirement, a proposed solution or a unit's answer really corresponds to what the RFP says.",
        "The panes are a workspace: you can enlarge one, drag them into another order, resize them and open any of them in a window of its own for a second screen. The next steps show each of these.",
      ],
      fallback: "The three panes are not on the page yet (the trace is still loading, or this bid has no requirements).",
    },
    {
      id: "trace-pane-1", route: ROUTE, target: "trace-pane-1", placement: "right",
      title: "Pane 1: the original RFP page",
      body: [
        "Pane 1 renders one page of the RFP as an image (`/api/documents/<doc>/pages/<n>.png`) and draws a highlight box over every requirement anchored on that page. The boxes come from the reader: each requirement stores its page and the bounding boxes of the lines it was quoted from, so the highlight sits exactly on the customer's text, not on an approximation.",
        "The highlight of the selected requirement is drawn in the selected style; the others are faint. Click any highlight to select that requirement: the linked panes 2 and 3 scroll to it. A group (a requirement merged from several line items) is highlighted through its sub-requirements on the same page.",
        "A requirement with no highlight on a page **needs a source check**: the reader found it but its quote could not be matched word for word, so it waits on the Needs a source check tab of pane 2 instead of the register.",
      ],
      fallback: "Pane 1 is empty: this bid has no readable RFP page (no main document, or it is still being read).",
    },
    {
      id: "trace-pager", route: ROUTE, target: "trace-pager", placement: "bottom",
      title: "The pager",
      body: [
        "Use the arrows or type a page number to move through the document; the Syracuse RFP has 101 pages, so valid values are 1 to 101 (anything else is clamped). Moving pages does not change the selected requirement; selecting a requirement does move the pager to its page.",
        "Tip: when you review page by page, the highlights tell you at a glance which lines became requirements and which did not. A page with no highlight was either furniture (headers, tables of contents) or text the reader judged not to be a requirement.",
      ],
      fallback: "The pager is shown only when an RFP page is available.",
    },
    {
      id: "trace-docs", route: ROUTE, target: "trace-docs", placement: "bottom",
      title: "Which document is shown",
      body: [
        "The line above the pager names the document in pane 1: **RFP** is the main document. Once an addendum or a Q&A document has been applied (chapter 11, Changes), requirements revised by it are anchored in that document instead, and a document switch appears here with one chip per document.",
        "Selecting a requirement that lives in a change document switches pane 1 to that document automatically, and pane 2 shows the document's name as a tag in the Source column. Until then only the RFP is listed and there is nothing to switch.",
      ],
      fallback: "The document line is shown only when an RFP page is available.",
    },
    {
      id: "trace-pane-2", route: ROUTE, target: "trace-pane-2", placement: "left",
      title: "Pane 2: the requirement register",
      body: [
        "Pane 2 lists every current requirement in document order: 312 for the Syracuse RFP, in three columns (selection, ID, Requirement). Each row is a link into the other two panes; the selected row is marked and keeps the keyboard focus (Enter or Space selects a row). The register, its Needs a source check tab, corrections and history were the subject of chapter 5; **enlarge** this pane to work in it at full width.",
      ],
      fallback: "No requirements yet: nothing has been extracted from the RFP for this bid.",
    },
    {
      id: "trace-pane-3", route: ROUTE, target: "trace-pane-3", placement: "left",
      title: "Pane 3: proposed solution and responses",
      body: [
        "Pane 3 has one row per requirement, aligned with pane 2. The **Proposed solution** column shows the business unit and the solution area (unit · solution area), with published models only as examples, the type of offer, the rationale, an example bill of materials and the match actions. It assesses the unit's solution for the requirement, not a part number. The **Response** column shows the work item of each unit once the work is sent, with its status and the unit's answer.",
        "Before solutions are proposed, every row reads *Not matched yet*. Afterwards a product item shows its proposed solution; a non-product item reads *Bid desk (not a product item)* or *Not a product item: answered by the unit managers* with their units; a product item no participating unit takes reads *Needs an owner* until the bid manager routes it or records a gap, then *Capability gap: not offered*. Until the bid is sent for assessment the Response column reads *Responses appear once the bid is sent for assessment*; once it is sent, a requirement without work reads *Not sent to units*.",
      ],
      fallback: "Nothing to map yet: proposed solutions and unit responses appear once requirements exist.",
    },
    {
      id: "trace-pane-controls", route: ROUTE, target: "trace-link-2", placement: "bottom",
      title: "Linked or Unlinked",
      body: [
        "Each pane heading has a **Linked** button. A linked pane follows the selected requirement: pane 1 opens its page, panes 2 and 3 scroll to its row. Click it to make the pane **Unlinked**: it keeps its page or scroll position while you select requirements elsewhere (the selected row is still highlighted). Click it again and the pane catches up with the selection at once.",
        "This is how you read pane 1 at one page while you go through the register, or keep pane 3 on a unit while you read pane 2.",
      ],
      fallback: "The Linked button sits in the heading of each pane.",
    },
    {
      id: "trace-enlarge", route: ROUTE, target: "trace-enlarge-2", placement: "bottom",
      title: "Enlarge or Restore",
      body: [
        "**Enlarge** shows one pane across the whole width and hides the other two (they stay loaded); **Restore**, or **Esc**, brings the three panes back. The selection is kept and linked panes catch up on restore. Use it to read the RFP page in full, to work through a long register, or to scan the matches.",
      ],
      fallback: "The Enlarge button sits in the heading of each pane.",
    },
    {
      id: "trace-reorder", route: ROUTE, target: "trace-arrange-2", placement: "bottom",
      title: "Reorder the panes",
      body: [
        "Drag a pane by its **grip** (the six dots) onto another pane: it **moves** into that pane's place and the others shift along. The **◀ ▶ buttons** next to the grip move it one place left or right and also work from the keyboard. Pane titles keep their numbers, so \"pane 2\" always means the register. The new order is remembered in this browser.",
        "The grip and arrows are shown on wide screens; below 1100 pixels the panes stack in the saved order.",
      ],
      fallback: "The grip and arrows are shown on wide screens, to the left of each pane title.",
    },
    {
      id: "trace-resize", route: ROUTE, target: "trace-split-1", placement: "bottom",
      title: "Resize the panes",
      body: [
        "Drag the **bar** between two panes to give one more width and the other less (mouse or touch); with the bar focused, the arrow keys resize it, **Shift** takes bigger steps and **Home** / **End** go to the limits. A small label shows the two shares while you drag. No pane can get narrower than a readable minimum.",
      ],
      fallback: "The resize bars are between the panes on wide screens.",
    },
    {
      id: "trace-new-window", route: ROUTE, target: "trace-detach-1", placement: "bottom",
      title: "New window: a pane on another screen",
      body: [
        "**New window** opens the pane in a window of its own, without the top bar or the bid header, for a second monitor. The main window shows a notice (\"Pane 2 is open in another window\") with **Show window** and **Return to main window**; closing the window, or its own **Return to main window** button, puts the pane back.",
        "The windows stay in step: selecting a requirement, the Linked setting, the filters and any change you save (an accepted match, a correction) reach all of them. If your browser blocks the new window, allow pop-ups for this site and try **New window** again. The walkthrough itself stays in the main window.",
      ],
      fallback: "New window is in each pane heading on wide screens.",
    },
    {
      id: "trace-reset", route: ROUTE, target: "trace-reset-layout", placement: "bottom",
      title: "Reset layout",
      body: [
        "The arrangement of the panes (order and widths) is remembered per browser. **Reset layout** returns to the original order and widths; it is greyed out while the layout is the default.",
      ],
      fallback: "Reset layout is in the toolbar above the filters.",
    },
    {
      id: "trace-legend", route: ROUTE, target: "trace-legend", placement: "bottom",
      title: "Types of offer: CTO, Semi-custom, ETO",
      body: [
        "Every product match carries a type of offer. **CTO** (configure-to-order) is a catalog product with options, quoted through CPQ. **Semi-custom** is a configured product plus workshop work for this customer. **ETO** (engineered-to-order) is designed for this requirement.",
        "The type is proposed by the matcher from the catalog's usual type for the product and the wording of the requirement; a person can change it. It drives the Bid decision page: until a unit answers, CTO counts as *Compliant*, Semi-custom and ETO as *Partially compliant*, and a type of offer below a unit's usual type of offer (for example CTO for Crown, whose usual type is guided ETO) is flagged for an engineer.",
      ],
    },
    {
      id: "trace-unit-responses", route: ROUTE, target: "trace-unit-responses", placement: "bottom",
      title: "Unit responses at a glance",
      body: [
        "The toolbar sums up the units' work on this bid: one badge per unit with *validated / total*, for example **CROWN 1/118 validated**; hover to see how many answers were submitted. The badge is green when everything is validated, blue while answers are coming in, amber while items are still only assigned. BID is the bid desk.",
        "Until the bid is sent for assessment it reads *Not sent for assessment yet* and shows no badges. The same numbers appear on the Bids page and feed the Compliance matrix.",
      ],
    },
    {
      id: "trace-match-explain", route: ROUTE, target: "trace-match-button", placement: "bottom",
      title: "What Propose solutions does",
      body: [
        "**Propose solutions** runs the matching agent over every requirement that nobody has decided yet. It proposes, for each one, the business unit(s), the solution area and the type of offer, with a rationale; accepted, manually set, routed and rejected matches are a person's decision and are kept as they are (the toast reports them as *kept as decided*). The button is the bid manager's and is shown only until the go/no-go is recorded: after that the solutions are the units' answers.",
        "How it works: requirements outside the product categories (anything but technical and compliance) are routed **by rule**, without a model call. The rest are sent **one page at a time** (at most 15 per call) with the page's header block and the whole product catalog and past responses in the prompt; the answer may only name catalog solution areas, the unit is taken from the solution area, and at most three units are kept per requirement. An empty answer means *not a product item*.",
        "When no model answer exists, the fallback is **retrieval only**: the closest catalog entry by text similarity, labelled as such in the row (\"closest catalog entry (no agent answer)\"), or the bid desk when nothing is close enough. For the Syracuse RFP the frozen answers give 312 proposals in 64 page calls: 214 by the agent, 98 by rule; Crown 93, EP2 6, and 213 that are not product items.",
      ],
      fallback: "Propose solutions is shown in the page header to the bid manager only, until the go/no-go is recorded.",
    },
    {
      id: "trace-match-run", route: ROUTE, target: "trace-match-button", placement: "bottom", kind: "action",
      title: "Propose solutions",
      body: [
        "Click **Propose solutions**. A *Proposing solutions…* indicator shows while it runs; on the demo bids the answers are frozen, so it takes a few seconds. When it finishes a toast reports *Solutions proposed for N requirement(s); M kept as decided.* and pane 3 fills in.",
        "Running it again later only refreshes proposals that nobody has accepted, rejected or changed; a person's decisions always win over the agent (rule R4).",
      ],
      instruction: "Click Propose solutions and wait for the toast.",
      done: matched,
      skipIf: statusIn(...DECIDED),
      fallback: "Propose solutions is in the page header, on the right, for the bid manager until the go/no-go is recorded.",
    },
    {
      id: "trace-match-result", route: ROUTE, target: "trace-pane-3", placement: "left", onEnter: selectRow(hasUnit),
      title: "What appeared in pane 3",
      body: [
        "Every row now has a match. Product items show their proposed solution (unit · solution area) and type-of-offer badge, with a status badge (**proposed**) and how it came about: *proposed by the matching agent*. The other rows are routed by rule and need no acceptance: submission and legal items read *Bid desk (not a product item)*, and schedule, commercial and staffing items, once sent, read *Not a product item: answered by the unit managers* of the participating units.",
        "For the Syracuse RFP: 99 product matches (Crown Technical Systems 93, EP² 6), of which 85 ETO, 11 CTO and 3 Semi-custom; 213 are not product items. The walkthrough selected the first matched product row so the next steps can read it.",
        "Limitations to keep in mind: the agent only sees the page's text and the catalog, so a product it does not know cannot be proposed; and *proposed* means exactly that: nothing is sent to a unit until the bid manager sends the work on the Assessment Summary.",
      ],
    },
    {
      id: "trace-sel-unit", route: ROUTE, target: "trace-sel-unit", placement: "left", onEnter: selectRow(hasUnit),
      title: "Proposed solution and type of offer",
      body: [
        "The first line reads **Proposed solution: Crown Technical Systems · Arc-resistant metal-clad MV switchgear**: the business unit and the solution area (the product family). Under it, *For example:* names the published models of that family when the catalog lists any, then the type-of-offer badge (ETO). The match assesses the unit's solution for the requirement; a model is an example, not a part number.",
        "When a requirement needs several units, each unit has its own Proposed solution line, main unit first; when the work is sent each participating unit gets its own work item for the requirement. A unit the bid manager routed reads *solution to be set by the unit's designer / engineer* until the engineer chooses one.",
      ],
      fallback: "The selected requirement has no product match (it is a bid-desk item or not matched yet). Select a technical requirement in pane 2 to see a proposed solution.",
    },
    {
      id: "trace-sel-rationale", route: ROUTE, target: "trace-sel-rationale", placement: "left", onEnter: selectRow(hasUnit),
      title: "The rationale",
      body: [
        "The rationale is the agent's one- or two-sentence explanation citing the catalog entries it used, for example for `REQ-0001-0885`: \"The requirement specifies a 15kV Metal Clad Switchgear lineup with arc-resistant Type 2B construction, meeting IEEE C37.20.7 standards. The catalog entry for CROWN-ARMV matches this description…\". Read it as a reviewer would: does the cited product really cover the quoted text?",
        "The agent also returns a confidence (0.95 for that example) which is stored with the match and its retrieval evidence; the trace keeps the payload small and shows the rationale, the status and the method line below it.",
      ],
      fallback: "The selected requirement has no product match, so there is no rationale to show.",
    },
    {
      id: "trace-sel-bom", route: ROUTE, target: "trace-sel-bom", placement: "left",
      onEnter: (ctx) => { selectRow(hasUnit)(ctx); openDetails("trace-sel-bom")(ctx); },
      title: "Example bill of materials",
      body: [
        "When the catalog has a bill of materials for the solution area, a collapsible **Example bill of materials (n lines)** lists its items and quantities (the arc-resistant switchgear has 5 lines). It comes from the catalog, not from the RFP: it tells the reviewer what the family's standard build contains so deviations asked by the RFP stand out.",
        "The Bid decision page compares the RFP's own data sheet with the standard ratings of these products (Deviations from the standard product).",
      ],
      fallback: "The selected product has no bill of materials in the catalog.",
    },
    {
      id: "trace-match-actions", route: ROUTE, target: "match-buttons", placement: "left", onEnter: selectRow(canAct),
      title: "Accept, Reject, Change",
      body: [
        "Under each match are its actions. **Accept** confirms the proposal: the match becomes *accepted* and records who decided. **Reject** marks it *rejected*: the requirement no longer counts for any unit and a re-run of the matcher does not propose it again (a person's decision). **Change** opens a form to set the units and solutions yourself.",
        "On a **technical** match these actions belong to the designer / engineer of the matched unit: the buttons are shown only to them, and the server refuses the bid manager (403). The bid manager's first stage is business relevance and routing, not technical approval. Non-technical items stay with the bid manager. Reject hands the requirement back to the bid manager, who routes it on the Assessment Summary (Needs an owner); the bid manager only changes the unit there, never the solution.",
        "Accept and Reject are shown only while the match is *proposed*. The Bid decision page counts the technical matches the units' designers / engineers have not confirmed yet, so reviewing them here is part of their job before go/no-go.",
      ],
      example: { label: "Sign in as Crown Design Engineer", apply: (ctx) => (ctx.actor !== "Crown Design Engineer" ? ctx.signInAs("crown.de") : undefined) },
      fallback: "Select a matched requirement in pane 3 to see its actions.",
    },
    {
      id: "trace-match-accept", route: ROUTE, target: "match-accept", placement: "left", kind: "action", onEnter: selectRow(canAct),
      title: "Accept this match",
      body: [
        "Click **Accept** on the selected row. The status badge turns to *accepted* and a toast confirms \"<ID>: match accepted.\" This is the engineer confirming the proposed solution; once the unit's answer is validated as Compliant, the requirement counts as *confirmed* under **Reviewed by design engineers** on the Assessment Summary. Nothing else changes: the unit gets the work only when the bid manager sends it. Accepting is reversible in practice: Change lets the engineer pick another solution at any time.",
      ],
      instruction: "Click Accept on the selected row.",
      done: textIn("match-meta", "accepted"),
      fallback: "Sign in as a unit's designer / engineer (Use example on the previous step) and select one of that unit's proposed matches. If all matches of this bid are already decided, use Continue.",
    },
    {
      id: "trace-match-change", route: ROUTE, target: "match-change", placement: "left", kind: "action",
      title: "Open the Change form",
      body: [
        "Click **Change** to see how a person overrides a match. Nothing is saved until you press Save; Cancel closes the form.",
      ],
      instruction: "Click Change on the selected row.",
      done: present("match-form"),
      fallback: "Select a requirement in pane 3 and click its Change button.",
    },
    {
      id: "trace-match-form", route: ROUTE, target: "match-form", placement: "left",
      title: "Choosing units, solution areas and types of offer",
      body: [
        "Each line of the form is one unit: a solution-area selector grouped by business unit (only **active** units are offered: EPC Power is a pending acquisition and cannot be chosen), a type-of-offer selector (CTO, Semi-custom, ETO) and **Remove**. **Add unit** adds a line for requirements that need several units; **Save** stores your choice as a *manual* match with status accepted (\"set by <you>\"); **Cancel** discards the draft.",
        "Removing every line and saving hands a technical item back to the bid manager (Needs an owner on the Assessment Summary); for a non-technical item it means the bid manager answers it. Several units give several work items when the work is sent, one per participating unit, each with its solution area as the reference.",
        "If the requirement was already sent to the units, a warning explains that the change takes effect the next time the work is sent: added units get the work (if they take part), removed units have theirs withdrawn.",
      ],
      fallback: "The Change form is closed. Click Change on a selected row to open it.",
    },
    {
      id: "trace-match-cancel", route: ROUTE, target: "match-cancel", placement: "left", kind: "action",
      title: "Close the form without saving",
      body: ["Press **Cancel** to leave the match as it is. A saved change is a correction by the engineer: once the unit's answer is validated, the requirement counts as *corrected* (another solution named) under **Reviewed by design engineers** on the Assessment Summary."],
      instruction: "Click Cancel.",
      done: (ctx) => !present("match-form")(ctx),
      fallback: "The form is already closed.",
    },
    {
      id: "trace-sync", route: ROUTE, target: "trace-page-image", placement: "right", kind: "action", allowInteraction: true,
      onEnter: (ctx) => ctx.set("trace-sync-from", currentReq()),
      title: "Selection follows you across the panes",
      body: [
        "Try the link between the panes: click a highlight in pane 1 (or any row in pane 2 or 3). The row is selected in both tables; the panes that are **Linked** follow it (the tables scroll to it, pane 1 turns to its page) and the URL hash becomes its ID, so the link can be shared or opened from the Bid decision page's per-requirement list.",
      ],
      instruction: "Click a highlight on the RFP page, or a different row in pane 2.",
      done: (ctx) => currentReq() !== "" && currentReq() !== ctx.get<string>("trace-sync-from"),
      fallback: "Click any row in pane 2 or pane 3 to select a different requirement.",
    },
    {
      id: "trace-sel-response", route: ROUTE, target: "trace-sel-response", placement: "left",
      title: "Assignments and their statuses",
      body: [
        "The Response column lists the work items sent to the units for the selected requirement: one per participating unit it is routed to, else the bid desk (**BID**). Each shows the unit, a status badge and, once answered, the compliance and the unit's text.",
        "Statuses: **assigned** (sent, no answer yet), **submitted** (the unit answered), **returned** (sent back with a question; the unit answers again) and **validated** (accepted: a technical answer by the unit manager, the unit manager's own answers by the bid manager). Compliance reads **Compliant**, **Partially compliant**, **Compliant with changes** or **Non-compliant**. Until the bid is sent for assessment the column holds only *Responses appear once the bid is sent for assessment*; sending happens on the **Assessment Summary** step, next.",
      ],
      fallback: "Select a requirement to see its assignments; before the bid is sent for assessment every row reads: Responses appear once the bid is sent for assessment.",
    },
    {
      id: "trace-done", route: ROUTE,
      title: "Before you leave Requirement Traceability",
      body: [
        "Checklist: solutions have been proposed, the matched units' designers / engineers have accepted or corrected their technical matches, requirements that need a source check are linked or dismissed, and multi-unit requirements list the right units. Everything else can wait: the Assessment Summary page reads this state live and tells you what is still open.",
        "Next: **Assessment Summary**, where the bid manager chooses the units, routes requirements and sends the work.",
      ],
      example: { label: "Sign in as Bid Manager", apply: (ctx) => ctx.signInAs("bid.manager") },
    },
  ],
};
export default chapter;
