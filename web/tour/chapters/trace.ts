// Walkthrough chapter 6: Traceability and product matching (app/opportunities/[id]/trace, components/matching/MatchActions).
// Targets are data-tour ids on the trace page; "trace-sel-*" and "match-*" sit on the selected row only.
import type { TourChapter, TourCtx } from "../types";
import { present, statusIn, textIn, openDetails } from "../helpers";

const ROUTE = "/opportunities/{opp}/trace";
/** Statuses in which matching has already been run and acted on (the seeded demo is "dispatched"). */
const DECIDED = ["go", "no_go", "dispatched", "consolidating", "submitted"];

// Rows of pane 3 (the same requirement order as pane 2); selecting one selects it in all three panes.
const rows3 = (ctx: TourCtx) => Array.from(ctx.el("trace-table-3")?.querySelectorAll<HTMLElement>("tr[data-req]") ?? []);
const selectedRow = (ctx: TourCtx) => rows3(ctx).find((tr) => tr.classList.contains("selected"));
const hasUnit = (tr: HTMLElement) => tr.querySelector(".trace-unit") !== null;
const isProposed = (tr: HTMLElement) => hasUnit(tr) && (tr.querySelector(".match-meta")?.textContent ?? "").includes("proposed");
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
  title: "Traceability and product matching",
  summary: "Follow every requirement from the RFP page to the unit and product that will answer it: run the matcher, read a match, accept or change it.",
  entryRoute: ROUTE,
  steps: [
    {
      id: "trace-intro", route: ROUTE,
      title: "Requirement Traceability: three panes",
      body: [
        "This is **Requirement Traceability**, the second step of the workflow and the page most people work from. Pane 1 is the original RFP page with the requirement's lines highlighted, pane 2 is the requirement register (chapter 5) and pane 3 is the product mapping with the units' responses.",
        "It exists because every answer in a bid must trace back to the customer's own words. Selecting a requirement in any pane selects it in all three, and every pane that is **Linked** follows it (pane 1 turns to its source page), so a reviewer can check in seconds whether a requirement, a product choice or a unit's answer really corresponds to what the RFP says.",
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
        "A requirement with no highlight on a page is an **exception**: the reader found it but its quote could not be matched word for word, so it waits on the Exceptions tab of pane 2 instead of the register.",
      ],
      fallback: "Pane 1 is empty: this opportunity has no readable RFP page (no main document, or it is still being read).",
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
        "Pane 2 lists every current requirement in document order: 312 for the Syracuse RFP. Each row is a link into the other two panes; the selected row is marked and keeps the keyboard focus (Enter or Space selects a row). The register, its Exceptions tab, corrections and history were the subject of chapter 5; **enlarge** this pane to work in it at full width.",
      ],
      fallback: "No requirements yet: nothing has been extracted from the RFP for this bid.",
    },
    {
      id: "trace-pane-3", route: ROUTE, target: "trace-pane-3", placement: "left",
      title: "Pane 3: product mapping and responses",
      body: [
        "Pane 3 has one row per requirement, aligned with pane 2. The **Unit · product** column shows the business unit, the product and its offering type, the rationale, the bill of materials and the match actions. The **Response** column shows the work item of each unit after dispatch, with its status and the unit's answer.",
        "Before matching, every row reads *not matched yet*; after matching, a product item shows its unit and product, and a non-product item reads *Bid manager (not a product item)*. Until the bid is sent for assessment the Response column reads *Responses appear once the bid is sent for assessment*; once it is sent, a requirement without work reads *not dispatched*.",
      ],
      fallback: "Nothing to map yet: product mappings and unit responses appear once requirements exist.",
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
      title: "Offering types: CTO, Semi-custom, ETO",
      body: [
        "Every product match carries an offering type. **CTO** (configure-to-order) is a catalog product with options, quoted through CPQ. **Semi-custom** is a configured product plus workshop work for this customer. **ETO** (engineered-to-order) is designed for this requirement.",
        "The type is proposed by the matcher from the catalog's usual type for the product and the wording of the requirement; a person can change it. It drives the Bid decision page: CTO counts as *fully* satisfied, Semi-custom and ETO as *partly* until a unit answers, and an offering type below a unit's default tier (for example CTO for Crown, whose default is guided ETO) is flagged for an engineer.",
      ],
    },
    {
      id: "trace-unit-responses", route: ROUTE, target: "trace-unit-responses", placement: "bottom",
      title: "Unit responses at a glance",
      body: [
        "The toolbar sums up the units' work on this opportunity: one badge per unit with *validated / total*, for example **CROWN 1/93 validated**; hover to see how many answers were submitted. The badge is green when everything is validated, blue while answers are coming in, amber while items are still only assigned. BID is the bid desk.",
        "Until the bid is sent for assessment it reads *Not sent for assessment yet* and shows no badges. The same numbers appear on the portfolio page and feed the consolidation step.",
      ],
    },
    {
      id: "trace-match-explain", route: ROUTE, target: "trace-match-button", placement: "bottom",
      title: "What Match products does",
      body: [
        "**Match products** runs the matching agent over every approved requirement that nobody has decided yet. It proposes, for each one, the business unit(s), the product and the offering type, with a rationale; accepted, manually set and rejected matches are a person's decision and are kept as they are (the toast reports them as *kept*).",
        "How it works: requirements outside the product categories (anything but technical and compliance) go to the bid desk **by rule**, without a model call. The rest are sent **one page at a time** (at most 15 per call) with the page's header block and the whole product catalog and past responses in the prompt; the answer may only name catalog products, the unit is taken from the product, and at most three units are kept per requirement. An empty answer means *not a product item*.",
        "When no model answer exists, the fallback is **retrieval only**: the closest catalog entry by text similarity, labelled as such in the row (\"closest catalog entry (no agent answer)\"), or the bid desk when nothing is close enough. For the Syracuse RFP the frozen answers give 312 matches in 64 page calls: 214 by the agent, 98 by rule; Crown 93, EP2 6, bid desk 213.",
      ],
    },
    {
      id: "trace-match-run", route: ROUTE, target: "trace-match-button", placement: "bottom", kind: "action",
      title: "Run the matcher",
      body: [
        "Click **Match products**. A *Matching…* indicator shows while it runs; on the walkthrough opportunity the answers are frozen, so it takes a few seconds. When it finishes a toast reports *Matching done: N requirement(s) matched, M kept as decided* and the page reloads with pane 3 filled.",
        "Running it again later only refreshes proposals that nobody has accepted, rejected or changed; a person's decisions always win over the agent (rule R4).",
      ],
      instruction: "Click Match products and wait for the toast.",
      done: matched,
      skipIf: statusIn(...DECIDED),
      fallback: "The Match products button is in the page header, on the right.",
    },
    {
      id: "trace-match-result", route: ROUTE, target: "trace-pane-3", placement: "left", onEnter: selectRow(hasUnit),
      title: "What appeared in pane 3",
      body: [
        "Every row now has a match. Product items show their unit, product and offering badge; the other rows read *Bid manager (not a product item)* with the rationale \"A schedule requirement, not a product item: the bid manager answers it\" (or legal, commercial, submission, staffing). Each match also shows its status badge (**proposed**) and how it came about: *proposed by the matching agent* or *routed to the bid desk by rule*.",
        "For the Syracuse RFP: 99 product matches (Crown Technical Systems 93, EP² 6), of which 85 ETO, 11 CTO and 3 Semi-custom; 213 go to the bid desk. The walkthrough selected the first matched product row so the next steps can read it.",
        "Limitations to keep in mind: the agent only sees the page's text and the catalog, so a product it does not know cannot be proposed; and *proposed* means exactly that: nothing is sent to a unit until the bid manager sends the work on the Assessment step.",
      ],
    },
    {
      id: "trace-sel-unit", route: ROUTE, target: "trace-sel-unit", placement: "left", onEnter: selectRow(hasUnit),
      title: "Unit, product and offering type",
      body: [
        "The first line is the business unit by name (for example **Crown Technical Systems**), the second the catalog product with its offering badge (**Arc-resistant metal-clad MV switchgear**, ETO). The unit always comes from the product: a product belongs to exactly one unit, so the two never disagree.",
        "When a requirement needs products from several units, the main unit is shown here and the others on an *Also:* line underneath; when the work is sent each participating unit gets its own work item for the requirement.",
      ],
      fallback: "The selected requirement has no product match (it is a bid-desk item or not matched yet). Select a technical requirement in pane 2 to see a unit and product.",
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
      title: "Bill of materials",
      body: [
        "When the catalog has a bill of materials for the product, a collapsible **Bill of materials (n lines)** lists its items and quantities (the arc-resistant switchgear has 5 lines). It comes from the catalog, not from the RFP: it tells the reviewer what the standard product contains so deviations asked by the RFP stand out.",
        "The Bid decision page compares the RFP's own data sheet with the standard ratings of these products (Deviations from the standard product).",
      ],
      fallback: "The selected product has no bill of materials in the catalog.",
    },
    {
      id: "trace-match-actions", route: ROUTE, target: "match-buttons", placement: "left", onEnter: selectRow(isProposed),
      title: "Accept, Reject, Change",
      body: [
        "Under each match are its actions. **Accept** confirms the proposal: the match becomes *accepted* and records who decided. **Reject** marks it *rejected*: the row then reads \"rejected: choose a unit with Change\", the requirement no longer counts for any unit, and a re-run of the matcher does not propose it again (a person's decision). **Change** opens a form to set the units yourself.",
        "Accept and Reject are shown only while the match is *proposed*; Change is always available. The Bid decision page counts product matches nobody has accepted or changed, so reviewing them here is part of the job before go/no-go.",
      ],
      fallback: "Select a matched requirement in pane 3 to see its actions.",
    },
    {
      id: "trace-match-accept", route: ROUTE, target: "match-accept", placement: "left", kind: "action", onEnter: selectRow(isProposed),
      title: "Accept this match",
      body: [
        "Click **Accept** on the selected row. The status badge turns to *accepted* and a toast confirms \"<ID>: match accepted.\" Nothing else changes: the unit gets the work only when the bid manager sends it. Accepting is reversible in practice: Change lets you pick another unit at any time.",
      ],
      instruction: "Click Accept on the selected row.",
      done: textIn("match-meta", "accepted"),
      fallback: "No proposed match is selected (all matches of this opportunity may already be decided). Use Continue.",
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
      title: "Choosing units, products and offering types",
      body: [
        "Each line of the form is one unit: a product selector grouped by business unit (only **active** units are offered: EPC Power is a pending acquisition and cannot be chosen), an offering type selector (CTO, Semi-custom, ETO) and **Remove**. **Add unit** adds a line for requirements that need several units; **Save** stores your choice as a *manual* match with status accepted (\"set by <you>\"); **Cancel** discards the draft.",
        "Removing every line and saving means *No unit: the bid manager answers it*. Several units give several work items when the work is sent, one per participating unit, each with its first product as the reference.",
        "If the requirement was already sent to the units, a warning explains that the change takes effect the next time the work is sent: added units get the work (if they take part), removed units have theirs withdrawn.",
      ],
      fallback: "The Change form is closed. Click Change on a selected row to open it.",
    },
    {
      id: "trace-match-cancel", route: ROUTE, target: "match-cancel", placement: "left", kind: "action",
      title: "Close the form without saving",
      body: ["Press **Cancel** to leave the match as it is. (Saving would be fine too: on the walkthrough opportunity you may change any match you like.)"],
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
        "Statuses: **assigned** (sent, no answer yet), **submitted** (the unit answered), **returned** (sent back with a question; the unit answers again) and **validated** (the unit manager accepted the answer). Compliance reads **Fully**, **Partially** or **Non-compliant**. Until the bid is sent for assessment the column holds only *Responses appear once the bid is sent for assessment*; sending happens on the **Assessment** step, next.",
      ],
      fallback: "Select a requirement to see its assignments; before the bid is sent for assessment every row reads: Responses appear once the bid is sent for assessment.",
    },
    {
      id: "trace-done", route: ROUTE,
      title: "Before you leave Requirement Traceability",
      body: [
        "Checklist: the matcher has run, the product matches you care about are accepted or changed, register exceptions are linked or dismissed, and multi-unit requirements list the right units. Everything else can wait: the Assessment page reads this state live and tells you what is still open.",
        "Next: **Assessment**, where the participating units are chosen, the routing is checked and the work is sent to the units.",
      ],
    },
  ],
};
export default chapter;
