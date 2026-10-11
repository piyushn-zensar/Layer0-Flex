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
      id: "trace-intro", route: ROUTE, target: "trace-panes", placement: "top",
      title: "Traceability: three linked panes",
      body: [
        "This is the **Traceability** screen, the third step of the workflow. It shows the same requirements as the Requirements page, but in their context: pane 1 is the original RFP page with the requirement's lines highlighted, pane 2 is the requirement breakdown (ID, source, category, text and quote), and pane 3 is the product mapping and the units' responses.",
        "It exists because every answer in a bid must be traceable back to the customer's own words. Selecting a requirement in any pane selects it in all three and turns pane 1 to its source page, so a reviewer can check in seconds whether a line item, a product choice or a unit's answer really corresponds to what the RFP says.",
        "What you do here: run **Match products** once the requirements are approved, then review each proposal (accept, reject or change it) and read what the units answered after dispatch. Before leaving for the Bid decision, every product match should have been looked at by a person: the decision page counts the ones that have not.",
      ],
      fallback: "The three panes are not on the page yet (the trace is still loading, or this opportunity has no requirements).",
    },
    {
      id: "trace-pane-1", route: ROUTE, target: "trace-pane-1", placement: "right",
      title: "Pane 1: the original RFP page",
      body: [
        "Pane 1 renders one page of the RFP as an image (`/api/documents/<doc>/pages/<n>.png`) and draws a highlight box over every requirement anchored on that page. The boxes come from the reader: each requirement stores its page and the bounding boxes of the lines it was quoted from, so the highlight sits exactly on the customer's text, not on an approximation.",
        "The highlight of the selected requirement is drawn in the selected style; the others are faint. Click any highlight to select that requirement: panes 2 and 3 scroll to it. A group (a requirement merged from several line items) is highlighted through its sub-requirements on the same page.",
        "Requirements with no highlight on any page are **unanchored**: the reader identified them but could not locate the quote on the page. They are listed with a badge in pane 2 and counted on the decision page.",
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
      id: "trace-unreviewed", route: ROUTE, target: "trace-unreviewed-warning", placement: "bottom",
      title: "Pages without a text layer",
      body: [
        "When the current page has no text layer (a scanned page), the pager shows **No text layer: page not read (needs OCR)**. The reader works on the PDF's own text, so nothing on such a page became a requirement: a person must read it, or add its requirements by hand on the Requirements page (they will be unanchored).",
        "Every page of the Syracuse RFP has a text layer, so you will not see this warning on the walkthrough opportunity; the Requirements page's unreviewed-page filter shows the same pages for other RFPs.",
      ],
      fallback: "No warning is shown: the current page has a text layer. Every page of the Syracuse RFP does; the warning appears on scanned pages of other RFPs.",
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
      title: "Pane 2: the requirement breakdown",
      body: [
        "Pane 2 lists every current requirement of the opportunity in document order: 348 for the Syracuse RFP. It is the same list the Requirements page shows, after approval and freezing, but here each row is a link into the other two panes. The selected row is marked and keeps the keyboard focus (Enter or Space selects a row).",
        "Three columns: **ID** with the category underneath, **Source** (page and lines, or the unanchored badge), and the **Requirement** (the short text, then the exact quote or the sub-requirements of a group). The next steps look at each of them on the selected row.",
      ],
      fallback: "No requirements yet: nothing has been extracted from the RFP for this opportunity.",
    },
    {
      id: "trace-sel-id", route: ROUTE, target: "trace-sel-id", placement: "right",
      title: "ID and category",
      body: [
        "Each requirement keeps a stable ID of the form `REQ-<opportunity>-<number>` (for example `REQ-0001-0887`), assigned when the reader identified it. The ID is in the URL hash of this page, in the per-requirement lists of the decision page, and in the work items each unit receives, so one requirement can be followed through the whole bid.",
        "The tag under the ID is the category: **technical**, **compliance**, **commercial**, **submission**, **legal**, **schedule** or **staffing**. It matters for matching: only technical and compliance requirements are product items that go to the matcher; every other category is routed to the bid desk by rule.",
      ],
      fallback: "Select a requirement in pane 2 to see its ID and category.",
    },
    {
      id: "trace-sel-source", route: ROUTE, target: "trace-sel-source", placement: "right",
      title: "Source: page and lines",
      body: [
        "The Source column states where the quote was found, for example **p. 55, lines 7-65**. It is the anchor that pane 1 highlights and that the matcher reads for context (the page's header block tells it which specification the line belongs to).",
        "Groups show the source of each sub-requirement next to it. When a change document revised the requirement, the document's name appears here as a tag and the page number refers to that document.",
      ],
      fallback: "Select a requirement in pane 2 to see its source.",
    },
    {
      id: "trace-unanchored", route: ROUTE, target: "trace-unanchored", placement: "right", onEnter: openDetails("trace-unanchored"),
      title: "The unanchored badge",
      body: [
        "An **unanchored** badge replaces the source when the quote could not be located on the page (the text was rephrased by a person, or came from a scanned page). The requirement is still valid and still matched; it just has no highlight in pane 1, so check its source manually. The Syracuse read has 32 of them out of 348.",
        "Unanchored requirements count against the **Open questions** criterion of the go/no-go summary, so it is worth resolving the important ones (edit the quote on the Requirements page so it anchors again, or accept them as they are).",
      ],
      fallback: "No requirement of this opportunity is unanchored: every quote was located on its page.",
    },
    {
      id: "trace-sel-text", route: ROUTE, target: "trace-sel-text", placement: "left",
      title: "Short text and quote",
      body: [
        "The first line is the requirement as a short, normalised statement written by the reader (for example \"Proposals must be submitted by September 15, 2023, 4pm.\"). Below it, in quotation marks, is the **exact quote** from the RFP (\"Submission Deadline: September 15, 2023 by 4pm\"). The quote is what the matcher and the units see; the short text is what people read in lists.",
        "The quotes are also the key of the matcher's frozen answers: the prompt holds the page header and the page's approved quotes (no requirement IDs), so the same page of quotes gets the same proposals in any opportunity made from this RFP, which is why the walkthrough works offline.",
      ],
      fallback: "Select a requirement in pane 2 to see its text and quote.",
    },
    {
      id: "trace-group", route: ROUTE, target: "trace-group", placement: "left", onEnter: openDetails("trace-group"),
      title: "Groups with sub-requirements",
      body: [
        "Some rows list sub-requirements instead of a quote: these are **groups**, made on the Requirements page by merging several line items that belong together (a heading and its bullet points, for instance). The Syracuse read has 162 groups. Each sub-requirement keeps its own source so the group still traces back to every line.",
        "A group is matched and dispatched as one item. Its highlight in pane 1 is the union of its sub-requirements' lines on that page.",
      ],
      fallback: "This opportunity has no grouped requirements.",
    },
    {
      id: "trace-send-knowledge", route: ROUTE, target: "trace-send-knowledge", placement: "left",
      title: "Send a requirement to the knowledge base",
      body: [
        "The selected requirement carries a **Send to knowledge base** link. It puts the requirement in the curator's queue (chapter 10) with an optional note on why it is worth keeping, for example a recurring clause future bids will meet again. Once sent, the link turns into a badge: *sent to knowledge base*, then *in knowledge base* once a curator approves it.",
        "Validated unit answers (pane 3) and decision rationales (Bid decision page) have the same link. Nothing is added to the knowledge base without a curator's approval.",
      ],
      fallback: "Select a requirement in pane 2: the link appears under the selected row.",
    },
    {
      id: "trace-pane-3", route: ROUTE, target: "trace-pane-3", placement: "left",
      title: "Pane 3: product mapping and responses",
      body: [
        "Pane 3 has one row per requirement, aligned with pane 2. The **Unit · product** column shows the business unit, the product and its offering type, the rationale, the bill of materials and the match actions. The **Response** column shows the work item of each unit after dispatch, with its status and the unit's answer.",
        "Before matching, every row reads *not matched yet*; after matching, a product item shows its unit and product, and a non-product item reads *Bid manager (not a product item)*. Before dispatch the Response column reads *not dispatched*.",
      ],
      fallback: "Nothing to map yet: product mappings and unit responses appear once requirements exist.",
    },
    {
      id: "trace-legend", route: ROUTE, target: "trace-legend", placement: "bottom",
      title: "Offering types: CTO, Semi-custom, ETO",
      body: [
        "Every product match carries an offering type. **CTO** (configure-to-order) is a catalog product with options, quoted through CPQ. **Semi-custom** is a configured product plus workshop work for this customer. **ETO** (engineered-to-order) is designed for this requirement.",
        "The type is proposed by the matcher from the catalog's usual type for the product and the wording of the requirement; a person can change it. It drives the decision page: CTO counts as *fully* satisfied, Semi-custom and ETO as *partly* until a unit answers, and an offering type below a unit's default tier (for example CTO for Crown, whose default is guided ETO) is flagged for an engineer.",
      ],
    },
    {
      id: "trace-unit-responses", route: ROUTE, target: "trace-unit-responses", placement: "bottom",
      title: "Unit responses at a glance",
      body: [
        "The toolbar sums up the units' work on this opportunity: one badge per unit with *validated / total*, for example **CROWN 1/96 validated**; hover to see how many answers were submitted. The badge is green when everything is validated, blue while answers are coming in, amber while items are still only assigned. BID is the bid desk.",
        "Before dispatch it reads *not sent to units yet*. The same numbers appear on the portfolio page and feed the consolidation step.",
      ],
    },
    {
      id: "trace-match-explain", route: ROUTE, target: "trace-match-button", placement: "bottom",
      title: "What Match products does",
      body: [
        "**Match products** runs the matching agent over every approved requirement that nobody has decided yet. It proposes, for each one, the business unit(s), the product and the offering type, with a rationale; accepted, manually set and rejected matches are a person's decision and are kept as they are (the toast reports them as *kept*).",
        "How it works: requirements outside the product categories (anything but technical and compliance) go to the bid desk **by rule**, without a model call. The rest are sent **one page at a time** (at most 15 per call) with the page's header block and the whole product catalog and past responses in the prompt; the answer may only name catalog products, the unit is taken from the product, and at most three units are kept per requirement. An empty answer means *not a product item*.",
        "When no model answer exists, the fallback is **retrieval only**: the closest catalog entry by text similarity, labelled as such in the row (\"closest catalog entry (no agent answer)\"), or the bid desk when nothing is close enough. For the Syracuse RFP the frozen answers give 348 matches in 61 page calls: 212 by the agent, 136 by rule; Crown 96, EP2 7, bid desk 245.",
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
        "For the Syracuse RFP: 103 product matches (Crown Technical Systems 96, EP² 7), of which 96 ETO, 5 CTO and 2 Semi-custom; 245 go to the bid desk. The walkthrough selected the first matched product row so the next steps can read it.",
        "Limitations to keep in mind: the agent only sees the page's text and the catalog, so a product it does not know cannot be proposed; and *proposed* means exactly that: nothing is sent to a unit until a person decides and dispatches.",
      ],
    },
    {
      id: "trace-sel-unit", route: ROUTE, target: "trace-sel-unit", placement: "left", onEnter: selectRow(hasUnit),
      title: "Unit, product and offering type",
      body: [
        "The first line is the business unit by name (for example **Crown Technical Systems**), the second the catalog product with its offering badge (**Arc-resistant metal-clad MV switchgear**, ETO). The unit always comes from the product: a product belongs to exactly one unit, so the two never disagree.",
        "When a requirement needs products from several units, the main unit is shown here and the others on an *Also:* line underneath; at dispatch each participating unit gets its own work item for the requirement.",
      ],
      fallback: "The selected requirement has no product match (it is a bid-desk item or not matched yet). Select a technical requirement in pane 2 to see a unit and product.",
    },
    {
      id: "trace-sel-rationale", route: ROUTE, target: "trace-sel-rationale", placement: "left", onEnter: selectRow(hasUnit),
      title: "The rationale",
      body: [
        "The rationale is the agent's one- or two-sentence explanation citing the catalog entries it used, for example for `REQ-0001-0887`: \"The requirement specifies a Metal Clad Switchgear lineup with 15kV vacuum circuit breakers, protective relays, and other features. The CROWN-ARMV product matches this description…\". Read it as a reviewer would: does the cited product really cover the quoted text?",
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
        "The decision page compares the RFP's own data sheet with the standard ratings of these products (Deviations from the standard product).",
      ],
      fallback: "The selected product has no bill of materials in the catalog.",
    },
    {
      id: "trace-match-actions", route: ROUTE, target: "match-buttons", placement: "left", onEnter: selectRow(isProposed),
      title: "Accept, Reject, Change",
      body: [
        "Under each match are its actions. **Accept** confirms the proposal: the match becomes *accepted* and records who decided. **Reject** marks it *rejected*: the row then reads \"rejected: choose a unit with Change\", the requirement no longer counts for any unit, and a re-run of the matcher does not propose it again (a person's decision). **Change** opens a form to set the units yourself.",
        "Accept and Reject are shown only while the match is *proposed*; Change is always available. The decision page counts product matches nobody has accepted or changed (criterion *Matches reviewed*), so reviewing them here is part of the job before go/no-go.",
      ],
      fallback: "Select a matched requirement in pane 3 to see its actions.",
    },
    {
      id: "trace-match-accept", route: ROUTE, target: "match-accept", placement: "left", kind: "action", onEnter: selectRow(isProposed),
      title: "Accept this match",
      body: [
        "Click **Accept** on the selected row. The status badge turns to *accepted* and a toast confirms \"<ID>: match accepted.\" Nothing else changes: the unit gets the work only at dispatch. Accepting is reversible in practice: Change lets you pick another unit at any time.",
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
        "Removing every line and saving means *No unit: the bid manager answers it*. Several units give several work items at dispatch, one per participating unit, each with its first product as the reference.",
        "If the requirement was already sent to the units, a warning explains that the change takes effect at the next dispatch: added units get the work (if they take part), removed units have theirs withdrawn.",
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
        "Try the link between the panes: click a highlight in pane 1 (or any row in pane 2 or 3). The row is selected in both tables, they scroll to it, pane 1 turns to its page and the URL hash becomes its ID, so the link can be shared or opened from the decision page's per-requirement list.",
      ],
      instruction: "Click a highlight on the RFP page, or a different row in pane 2.",
      done: (ctx) => currentReq() !== "" && currentReq() !== ctx.get<string>("trace-sync-from"),
      fallback: "Click any row in pane 2 or pane 3 to select a different requirement.",
    },
    {
      id: "trace-sel-response", route: ROUTE, target: "trace-sel-response", placement: "left",
      title: "Assignments and their statuses",
      body: [
        "The Response column lists the work items created at dispatch for the selected requirement: one per participating unit that is matched to it, else the bid desk (**BID**). Each shows the unit, a status badge and, once answered, a compliance badge and the unit's text.",
        "Statuses: **assigned** (sent, no answer yet), **submitted** (the unit answered), **returned** (the bid manager sent it back with a note; the unit answers again), **validated** (the bid manager accepted the answer). Withdrawn items (after a change of match or participation) are hidden. Compliance: **met**, **partial**, **not met**, **exception**. In the demo opportunity, `REQ-0001-0887` has a validated Crown answer: \"Two-section 15 kV arc-resistant metal-clad lineup offered.\"",
        "A validated answer carries its own *Send to knowledge base* link. Before dispatch the column reads *not dispatched*; dispatch happens on the Bid decision page, next.",
      ],
      fallback: "Select a requirement to see its assignments; before dispatch every row reads not dispatched.",
    },
    {
      id: "trace-done", route: ROUTE,
      title: "Before you leave Traceability",
      body: [
        "Checklist: the matcher has run, the product matches you care about are accepted or changed, unanchored requirements have been checked against their page, and multi-unit requirements list the right units. Everything else can wait: the Bid decision page reads this state live and tells you what is still open.",
        "Next: **Bid decision**, where the evidence pack, the engineering and portfolio checks and the go/no-go summary are built from exactly these matches, and where dispatch sends each unit its work.",
      ],
    },
  ],
};
export default chapter;
