// Walkthrough chapter 8: unit inboxes, answers and validation (web/app/inbox, web/app/inbox/[bu]).  Owner: G1.
// Runs on /inbox/CROWN: the bid manager's view first, then as "Crown Product Manager" to answer one row, then back to the
// bid manager to validate. The inbox gathers a unit's work across every opportunity, so the first open row may belong to
// OPP-0001 rather than the walkthrough opportunity; the steps say so.
import type { TourChapter, TourCtx } from "../types";
import { present } from "../helpers";

type Field = HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
type Row = { id: number; opportunity_id: string; req_id: string; status: string; product_ref: string | null; validated_by: string | null };
const BM = "Bid Manager";
const CROWN_PM = "Crown Product Manager";

function setValue(el: Field | null | undefined, value: string) {
  if (!el) return;
  const proto = el instanceof HTMLSelectElement ? HTMLSelectElement.prototype
    : el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value")?.set?.call(el, value);
  el.dispatchEvent(new Event(el instanceof HTMLSelectElement ? "change" : "input", { bubbles: true }));
}
const field = (ctx: TourCtx, tourId: string): Field | null => {
  const el = ctx.el(tourId);
  if (!el) return null;
  return el.matches("input, select, textarea") ? (el as Field) : el.querySelector<Field>("input, select, textarea");
};
const crown = async (ctx: TourCtx): Promise<Row[]> => {
  try { return (await ctx.api<{ items: Row[] }>("/api/inbox/CROWN")).items; } catch { return []; }
};
/** Remember which assignment the first open row's form belongs to (its data-assignment attribute). */
const rememberRow = (ctx: TourCtx) => {
  const id = Number(ctx.el("inbox-form")?.getAttribute("data-assignment"));
  if (id) ctx.set("inboxAssignment", id);
};
const rowStatus = async (ctx: TourCtx) => {
  const id = ctx.get<number>("inboxAssignment");
  return id ? (await crown(ctx)).find((a) => a.id === id)?.status : undefined;
};
/** Ask the page to re-fetch (useApi reloads on focus) after the walkthrough changed data behind its back. */
const refetch = () => window.dispatchEvent(new Event("focus"));

const chapter: TourChapter = {
  id: "inbox",
  order: 8,
  title: "Unit inboxes, answers and validation",
  summary: "My work and the unit work packages: answer a requirement as Crown's product manager, submit it, then validate or return it as the bid manager, and download the unit's hand-off file.",
  entryRoute: "/inbox/BID",
  steps: [
    {
      id: "inbox-mywork",
      title: "My work: the inbox of the person acting",
      route: "/inbox/BID",
      target: "inbox-table",
      placement: "top",
      fallback: "The bid desk inbox lists the requirements no unit matched; it is empty until an opportunity has been dispatched.",
      body: [
        "**My work** in the top bar opens `/inbox`, which looks the acting person up in `/api/people` and redirects to their unit's work package: a Crown engineer lands on `/inbox/CROWN`, the **Bid Manager** on `/inbox/BID`, the **bid desk**.",
        "A work package is one business unit's assignments across *every* opportunity: after dispatch each approved requirement was assigned to the unit(s) the matching step chose, and to **BID** when no unit matched (commercial, submission and legal items). On the Syracuse demo the bid desk holds 245 of the 348 requirements; the Bid Manager answers those personally.",
        "This chapter uses Crown's package. Rows from several opportunities sit together, ordered by opportunity then requirement; the walkthrough highlights the first open row of **your** opportunity (the one you created, or OPP-0001 if you chose the demo), so what you answer and validate here shows up on its Final response.",
      ],
    },
    {
      id: "inbox-bm-view",
      title: "Crown's work package, seen by the bid manager",
      route: "/inbox/CROWN",
      target: "inbox-table",
      placement: "top",
      fallback: "The Crown table lists the 96 Syracuse rows assigned to Crown Technical Systems.",
      body: [
        "You are still acting as the Bid Manager. On a unit's package the bid manager cannot type answers (only the unit's own **product manager** or **design engineer** can, the API answers 403 otherwise) but sees everything, and gets **Validate / Return** buttons on submitted rows plus a line \"n submitted answer(s) waiting for validation\".",
        "A third person, say EP²'s product manager, would see the blue banner \"You are acting as …: you can read this work package but not answer it.\" Reading is open to everyone in the PoC; writing is tied to the role.",
        "The title names the unit (\"My work: Crown Technical Systems\"); the help line states the contract of the page: mark each line met, partly met, not met or an exception, say what meets it, submit; the bid manager validates or returns it with a note.",
      ],
    },
    {
      id: "inbox-links",
      allowInteraction: true, // the point of this step is a link or download inside the spotlight
      title: "Open the RFP, and the hand-off file",
      route: "/inbox/CROWN",
      target: "inbox-links",
      placement: "bottom",
      fallback: "Above the table: one \"Open the RFP\" button per opportunity and, for a real unit, one hand-off download per opportunity.",
      body: [
        "**Open the RFP** has one button per opportunity in this package; it opens that opportunity's Traceability page, where the unit reads the requirement next to the highlighted lines of the PDF. The requirement IDs in the first column do the same for a single row (`/trace#REQ-…`).",
        "**Hand-off for this unit's systems** downloads `GET /api/opportunities/<opp>/handoff/CROWN` as `<opp>-CROWN-handoff.json`: the unit's assignments grouped into three routes for its own tools. It is explained at the end of this chapter, once an answer has been validated. The bid desk has no hand-off (it has no downstream system).",
      ],
    },
    {
      id: "inbox-columns",
      title: "The four columns",
      route: "/inbox/CROWN",
      target: "inbox-table",
      placement: "top",
      body: [
        "**Opportunity**: the opportunity ID and the requirement ID, linking to that requirement in Traceability. **Requirement**: the short text, the **verbatim quote** from the RFP in italics, and either `p. 12, lines 4-6: show highlighted source` or an amber *unanchored* badge when the quote could not be located on the page (check the source manually). If a requirement was removed by a change document after dispatch the cell says so.",
        "**Response**: a small form on rows the acting person may answer (status *assigned* or *returned*), otherwise the answer as text: compliance in bold, the product reference in monospace, the explanation underneath, or \"not answered yet\".",
        "**Status**: *assigned* (amber, open), *submitted* (blue, waiting for the bid manager), *validated* (green, with \"by Bid Manager\"), *returned* (red, back with the unit). *Withdrawn* rows (the match or participation changed) are hidden; if they fit again at a later dispatch they reopen with their earlier answer kept.",
      ],
    },
    {
      id: "inbox-switch-crown",
      title: "Act as Crown's product manager",
      route: "/inbox/CROWN",
      target: "inbox-table",
      placement: "top",
      kind: "action",
      instruction: "Switch \"Acting as\" to Crown Product Manager (top bar), or press Use example.",
      skipIf: (ctx) => ctx.actor === CROWN_PM,
      body: [
        "The PoC has no sign-in. **Acting as** in the top bar writes an `actor` cookie; every API call sends it as the `X-Actor` header, the backend records that name on each event (who proposed, approved, answered, validated) and enforces the few role rules: only a unit's product manager or design engineer answers its rows, only the Bid Manager validates, dispatches, freezes and curates.",
        "The people in the list come from the catalog: the Bid Manager plus each active unit's product manager and design engineer. A real identity provider and named roles replace the picker later; the audit trail and the rules stay as they are.",
      ],
      example: { label: "Act as Crown Product Manager", apply: (ctx) => ctx.setActor(CROWN_PM) },
      done: (ctx) => ctx.actor === CROWN_PM,
    },
    {
      id: "inbox-open-count",
      title: "Open rows",
      route: "/inbox/CROWN",
      target: "inbox-open-count",
      placement: "bottom",
      fallback: "As an answering person the page says how many rows are open, e.g. \"94 open row(s)\" for Crown on the demo.",
      body: [
        "Now the page is yours to answer: the header gains **Submit all answered rows** and the line \"n open row(s)\" counts what is *assigned* or *returned*. On the Syracuse demo Crown has 96 rows: 94 open, one already submitted and one validated by the seed.",
        "Rows keep their place in the table whatever their status, so a unit works top to bottom and the bid manager sees the same order.",
      ],
    },
    {
      id: "inbox-row-form",
      title: "Answering a row",
      route: "/inbox/CROWN",
      target: "inbox-form",
      placement: "left",
      onEnter: rememberRow,
      fallback: "Each open row carries a compact form: a compliance select, a product field and a \"How it is met\" text box.",
      body: [
        "**Compliance** is one of four values: **met** (the offer satisfies the line as written), **partial** (part of it, say which), **not_met** (it cannot be offered), **exception** (offered differently, to be negotiated: a deviation the response must declare). It is the field the final response is built from, so choose it honestly rather than optimistically.",
        "**Product / configuration** is pre-filled with the product the match proposed (here `CROWN-ARMV`, the arc-resistant metal-clad lineup); change it if another product or a configuration reference meets the line. **How it is met** is free text in the unit's words; it is what the bid manager validates and what the response outline quotes.",
        "The highlighted row is the first open Crown row of your opportunity (on the demo data: `REQ-0001-0324`, \"Provide one 15kV two-section Metal Clad Switchgear lineup.\"). **Use example** fills a plausible answer for that row; edit it as you like before submitting.",
      ],
      example: {
        label: "Fill an example answer",
        apply: (ctx) => {
          rememberRow(ctx);
          setValue(field(ctx, "inbox-compliance"), "met");
          const product = field(ctx, "inbox-product");
          if (product && !product.value) setValue(product, "CROWN-ARMV");
          setValue(field(ctx, "inbox-response"),
            "Met with the CROWN-ARMV arc-resistant metal-clad lineup: factory-assembled two-section 15 kV lineup per the one-line diagram, type-tested to IEEE C37.20.7; shop drawings for approval before fabrication.");
        },
      },
    },
    {
      id: "inbox-submit",
      title: "Submit the answer",
      route: "/inbox/CROWN",
      target: "inbox-submit",
      placement: "left",
      kind: "action",
      onEnter: rememberRow,
      instruction: "Press Submit on the row you filled in.",
      fallback: "The Submit button sits under the row's text box.",
      body: [
        "**Submit** posts the three fields to `/api/assignments/<id>/respond`. The row becomes **submitted**, records who answered and when, and leaves the unit's open count. The form is replaced by the answer as text: the unit cannot edit a submitted row; only a return by the bid manager (or a change document) reopens it.",
        "While the request runs the button is disabled (\"Sending…\"); on failure the typed text stays and the API's message appears as a toast.",
      ],
      done: async (ctx) => {
        const s = await rowStatus(ctx);
        if (s) return s !== "assigned" && s !== "returned";
        return ctx.el("inbox-form") === null;  // no stored row: the first open row's form has gone
      },
    },
    {
      id: "inbox-submitted",
      title: "Result: submitted, waiting for validation",
      route: "/inbox/CROWN",
      target: "inbox-row-submitted",
      placement: "top",
      fallback: "The submitted row now shows the compliance in bold, the product reference and the text, with a blue \"submitted\" badge.",
      body: [
        "The row shows the compliance in bold, the product in monospace and the explanation, with a blue **submitted** badge. In the Opportunities table the Crown bar gained a blue \"awaiting validation\" segment, and the bid manager's view of this package now counts one more answer to validate.",
        "Nothing else moves yet: the final response, the knowledge base and the hand-off treat an answer as the unit's position only once it is **validated**.",
      ],
    },
    {
      id: "inbox-submit-all",
      title: "Submit all answered rows",
      route: "/inbox/CROWN",
      target: "inbox-submit-all",
      placement: "left",
      fallback: "The header button \"Submit all answered rows\" appears while the acting person has open rows.",
      body: [
        "Units usually answer many rows in one sitting. Type into any number of open rows, then press **Submit all answered rows**: every open row whose \"How it is met\" is filled in is sent one after the other; rows with an empty text box are skipped, so partially prepared work is never submitted by accident.",
        "Each sent row shows *sent*, a failed one shows *not sent: <reason>* and keeps its text; a toast summarises (\"12 row(s) submitted for validation.\", or how many were not sent). With nothing typed anywhere it only says so.",
      ],
    },
    {
      id: "inbox-source-link",
      title: "Show highlighted source",
      route: "/inbox/CROWN",
      target: "inbox-source-link",
      placement: "bottom",
      fallback: "Rows whose quote was located on the page carry a \"p. N, lines a-b: show highlighted source\" link; rows whose quote was not located show an amber \"unanchored\" badge instead (the first open demo row is one of those).",
      body: [
        "Every requirement remembers its **source**: the page and line range (and the boxes) where its quote was found. The grey link under the quote opens Traceability with that requirement selected and its lines highlighted on the page image, so the unit never has to search the PDF.",
        "Rows marked **unanchored** are requirements whose quote the anchoring step could not locate; they are kept because dropping them would lose a requirement (rule: never silently skip). For those the unit reads the quote and checks the RFP by hand.",
      ],
    },
    {
      id: "inbox-switch-bm",
      title: "Back to the bid manager",
      route: "/inbox/CROWN",
      target: "inbox-table",
      placement: "top",
      kind: "action",
      instruction: "Switch \"Acting as\" back to Bid Manager, or press Use example.",
      skipIf: (ctx) => ctx.actor === BM,
      body: [
        "Validation is the bid manager's step: `POST /api/assignments/<id>/validate` is refused for anyone else (\"Only the Bid Manager validates or returns answers.\"). Switch back and the same page shows **Validate** and **Return** on every submitted row.",
      ],
      example: { label: "Act as Bid Manager", apply: (ctx) => ctx.setActor(BM) },
      done: (ctx) => ctx.actor === BM,
    },
    {
      id: "inbox-validate",
      title: "Validate the answer",
      route: "/inbox/CROWN",
      target: "inbox-validate",
      placement: "left",
      kind: "action",
      instruction: "Press Validate on the first submitted row.",
      fallback: "Submitted rows show Validate and Return buttons in the Status column.",
      body: [
        "**Validate** marks the answer as the unit's position for this bid: status **validated**, \"by Bid Manager\" under the badge. From now on it counts in the green segment of the portfolio bar, it can be sent to the knowledge base (chapter 10), the response outline quotes it, and the hand-off file carries it with `status: validated`.",
        "Validation checks substance, not form: is the compliance claim defensible against the quote, is the product right, would the customer understand the sentence. A doubtful answer is **returned** instead.",
        "The highlighted row is the one you just sent (the first submitted Crown row of your opportunity). On the demo opportunity the seed's `REQ-0001-0889` (\"Standard catalog termination kit.\") is submitted as well; validating it too is fine.",
      ],
      done: async (ctx) => {
        const s = await rowStatus(ctx);
        if (s) return s === "validated";
        return ctx.el("inbox-validate") === null;
      },
    },
    {
      id: "inbox-return",
      title: "Return with a required note",
      route: "/inbox/CROWN",
      target: "inbox-return",
      placement: "left",
      fallback: "While a row is submitted, Return opens a note box next to Validate; with no submitted rows left there is nothing to return right now.",
      body: [
        "**Return** opens a note box: \"Why is it returned? The unit sees this note.\" The note is **required**, the button \"Return with note\" stays disabled until something is typed, and the API refuses an empty one (\"A returned answer needs a note saying why\").",
        "A returned row goes back to status **returned** (red): it reopens for the unit with an amber *Returned by Bid Manager: <note>* box above the form, pre-filled with the previous answer, and counts as open again in the portfolio bar. The unit edits and submits again; the bid manager validates or returns again. A change document does the same automatically for answers whose requirement changed, with the change as the note.",
        "You may try it on another submitted row now (Return, type a note, Return with note) or leave it; the walkthrough does not do it for you.",
      ],
    },
    {
      id: "inbox-validated",
      title: "Result: validated",
      route: "/inbox/CROWN",
      target: "inbox-links",
      placement: "bottom",
      body: [
        "The row carries a green **validated** badge with the validator's name. On the Opportunities screen the Crown line now reads one more validated; in Traceability the requirement's row shows the unit's answer; in the response outline (chapter 9) the sentence is available verbatim.",
        "Every state change here was recorded in the audit log with the acting person and the time (responded, validated, returned), which is what the history and the consolidation checks read.",
      ],
    },
    {
      id: "inbox-handoff",
      allowInteraction: true, // the point of this step is a link or download inside the spotlight
      title: "The hand-off file",
      route: "/inbox/CROWN",
      target: "inbox-links",
      placement: "bottom",
      skipIf: (ctx) => !present("inbox-links")(ctx),
      body: [
        "The **hand-off** buttons download one JSON per unit and opportunity. It holds the opportunity and unit, the go/no-go decision, `stated_facts` (ratings read from the frozen requirements, each citing its REQ), and the unit's assignments grouped into three **routes**: **A `cpq_seed`** for CTO products (a configuration seed with the product's BOM lines, to start the configurator), **B `basis_of_design`** for semi-custom and ETO products (the captured requirement, `spec_claimed: false`), **C `specialist_queue`** when the unit's tier says an engineer must look first.",
        "Each item carries `req_id`, `source` (page and lines), the quote, the product and offering type, any engineering flags from the evidence checks, and `unit_answer` (status, compliance, product, response, validated_by). The payload says `requires_human_completion: true` and repeats it in words: Layer 0 seeds the configurator and briefs design engineering; it does not configure or design anything.",
        "Validated answers travel in it as the unit's position; open or submitted ones travel with their status, so a downstream team can see what is still unsettled. The file is regenerated on every download from the current data.",
      ],
    },
  ],
};
export default chapter;
