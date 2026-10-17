// Walkthrough chapter 8: My work: unit work packages, answers and validation (web/app/inbox, web/app/inbox/[bu]).  Owner: Janvia (J-15).
// Runs on /inbox/CROWN as "Crown Product Manager" (the unit manager answers the unit's schedule, commercial and staffing
// items and validates the unit's answers), then back to the bid manager. The first open row of the walkthrough bid is the
// highlighted one. Roles come from data/knowledge_base/workflow.json.
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

const chapter: TourChapter = {
  id: "inbox",
  order: 8,
  title: "My work: unit answers and validation",
  summary: "My work and the unit work packages: sign in as Crown's unit manager, answer a requirement, submit and validate it, see the completion dates and Knowledge review, and download the unit's hand-off file.",
  entryRoute: "/inbox/BID",
  steps: [
    {
      id: "inbox-mywork",
      title: "My work: the signed-in person's work",
      route: "/inbox/BID",
      target: "inbox-table",
      placement: "top",
      fallback: "The bid desk lists the items no unit takes; it is empty until a bid has been sent to the units.",
      body: [
        "**My work** opens the work of the signed-in person: a unit's people land on their unit's work package, the **Bid Manager** on the **bid desk** (`/inbox/BID`). A work package is one unit's items across every bid, ordered by bid then requirement.",
        "The bid desk holds the high-level, consolidated items answered once for the whole bid: on Syracuse the **73** submission and legal requirements. The bid manager answers and validates those personally. The units hold the rest: technical items for their designers / engineers, schedule, commercial and staffing items for their unit managers.",
      ],
    },
    {
      id: "inbox-switch-crown",
      title: "Sign in as Crown's unit manager",
      route: "/inbox/CROWN",
      target: "inbox-table",
      placement: "top",
      kind: "action",
      instruction: "Sign out in the top bar and sign in as crown.pm, or press Use example.",
      skipIf: (ctx) => ctx.actor === CROWN_PM,
      body: [
        "Each person signs in; **Sign out** in the top bar leads to the sign-in page. The sign-in token travels in a cookie with every request, the server records the signed-in name on every event and enforces the role rules from `workflow.json`: a unit's **designers / engineers** answer its technical items, its **unit manager** answers the other items and **validates** the unit's answers, and the **bid manager** may return any answer with a question.",
        "Crown Product Manager is Crown Technical Systems' **Unit manager**. Reading is open to everyone; writing is tied to the role and the unit.",
      ],
      example: { label: "Sign in as Crown Product Manager", apply: (ctx) => ctx.signInAs("crown.pm") },
      done: (ctx) => ctx.actor === CROWN_PM,
    },
    {
      id: "inbox-completion",
      title: "Your unit's completion dates",
      route: "/inbox/CROWN",
      target: "inbox-completion",
      placement: "bottom",
      fallback: "The unit manager sees one row per bid with a date field for the unit's estimated completion.",
      body: [
        "The unit manager states **when the unit expects to finish each bid**: a date and an optional note, saved per bid. The bid manager plans the submission from these dates on the Assessment page, which warns when the planned date falls after the RFP's due date.",
      ],
    },
    {
      id: "inbox-knowledge-review",
      title: "Knowledge review",
      route: "/inbox/CROWN",
      target: "kb-review-section",
      placement: "bottom",
      onEnter: (ctx) => { const d = ctx.el("kb-review-section") as HTMLDetailsElement | null; if (d && !d.open) d.open = true; },
      fallback: "Knowledge review lists reviewed examples waiting for this person's decision; it is empty when nothing is waiting.",
      body: [
        "People nominate requirements, validated answers, decisions and corrections as **reviewed examples** where they appear. The right reviewer approves or rejects each one here: a unit's manager or designer / engineer for its answers, the bid manager for bid-level items. Approved examples become evidence for later bids with their conditions and limits; illustrative ones are never treated as verified.",
      ],
    },
    {
      id: "inbox-units",
      title: "Work packages",
      route: "/inbox/CROWN",
      target: "inbox-units",
      placement: "bottom",
      body: [
        "The chips switch between work packages: the bid desk and each unit with work, with a count of answers waiting for validation. Anyone can read a package; only its own people act on it, and a blue banner says so when you are only reading.",
      ],
    },
    {
      id: "inbox-links",
      allowInteraction: true, // the point of this step is a link or download inside the spotlight
      title: "Open the RFP, and the hand-off file",
      route: "/inbox/CROWN",
      target: "inbox-links",
      placement: "bottom",
      fallback: "Above the table: one button per bid to open its RFP and, for a unit, one hand-off download per bid.",
      body: [
        "**Open the RFP** has one button per bid; it opens that bid's Requirement Traceability page, where the unit reads the requirement next to the highlighted lines of the PDF. **Hand-off for this unit's systems** downloads a JSON of the unit's items grouped into routes for its own tools (explained at the end of the chapter).",
      ],
    },
    {
      id: "inbox-open-count",
      title: "Open rows",
      route: "/inbox/CROWN",
      target: "inbox-open-count",
      placement: "bottom",
      fallback: "As an answering person the page says how many rows are open for you.",
      body: [
        "For a person who may answer, the page counts the rows still open (*assigned* or *returned*) and offers **Submit all answered rows**. Crown holds 118 items; the unit manager's own are the schedule, commercial and staffing ones (25 on Syracuse), the rest wait for Crown's designers / engineers.",
      ],
    },
    {
      id: "inbox-columns",
      title: "The columns",
      route: "/inbox/CROWN",
      target: "inbox-table",
      placement: "top",
      body: [
        "**Bid** gives the bid and requirement ID, linking to the requirement in Traceability. **Requirement** shows the short text, the **verbatim quote** and *show highlighted source*. **Response** is a form on rows you may answer, otherwise the answer as text. **Status** is *assigned*, *submitted* (waiting for validation), *validated* or *returned*, with **History** showing every change with who, when and why.",
      ],
    },
    {
      id: "inbox-row-form",
      title: "Answering a row",
      route: "/inbox/CROWN",
      target: "inbox-form",
      placement: "left",
      onEnter: rememberRow,
      fallback: "Each row you may answer carries a compact form: a compliance select, a product field and a \"How it is met\" text box.",
      body: [
        "**Compliance** is **Fully compliant**, **Partially compliant** or **Non-compliant**; it is what the compliance matrix is built from, so choose it honestly. **Product / configuration** is pre-filled from the match when there is one. **How it is met** is the answer in the unit's words.",
        "For partial or non-compliant answers a **Reason** (what is not met and why) is **required**; **Conditions**, **Workaround** and **Next steps** are optional and appear in the matrix and its exports. The highlighted row is the first open row of the bid (`REQ-0001-0001`, the submission deadline). **Use example** fills a plausible answer.",
      ],
      example: {
        label: "Fill an example answer",
        apply: (ctx) => {
          rememberRow(ctx);
          setValue(field(ctx, "inbox-compliance"), "met");
          setValue(field(ctx, "inbox-response"),
            "Met. Crown Technical Systems will meet the submission dates in the RFP; the unit's estimated completion date is entered under Your unit's completion dates.");
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
      fallback: "The Submit button sits under the row's form.",
      body: [
        "**Submit** sends the answer. The row becomes **submitted**, records who answered and when, and leaves the unit's open count. The unit cannot edit a submitted row; only a return, or a change document, reopens it.",
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
      fallback: "The submitted row now shows the compliance in bold, the text and a blue \"submitted\" badge.",
      body: [
        "The row shows the compliance in bold and the explanation, with a **submitted** badge. On the Bids screen the Crown bar gained a blue \"awaiting validation\" segment. Nothing else moves until the unit manager validates it: the compliance matrix and the exports treat an answer as the unit's position only once it is **validated**.",
      ],
    },
    {
      id: "inbox-submit-all",
      title: "Submit all answered rows",
      route: "/inbox/CROWN",
      target: "inbox-submit-all",
      placement: "left",
      fallback: "The header button \"Submit all answered rows\" appears while you have open rows.",
      body: [
        "Units usually answer many rows in one sitting. Type into any number of open rows, then press **Submit all answered rows**: every open row whose \"How it is met\" is filled in is sent, rows with an empty box are skipped, and a toast reports how many were sent and how many were not.",
      ],
    },
    {
      id: "inbox-source-link",
      title: "Show highlighted source",
      route: "/inbox/CROWN",
      target: "inbox-source-link",
      placement: "bottom",
      fallback: "Rows whose quote was located carry a \"p. N, lines a-b: show highlighted source\" link.",
      body: [
        "Every requirement remembers its **source**. The grey link under the quote opens Requirement Traceability with that requirement selected and its lines highlighted on the page image, so the unit never has to search the PDF.",
      ],
    },
    {
      id: "inbox-validate",
      title: "Validate the answer",
      route: "/inbox/CROWN",
      target: "inbox-validate",
      placement: "left",
      kind: "action",
      instruction: "Press Validate on the submitted row (as the unit manager).",
      fallback: "Submitted rows show Validate and Return in the Status column for the unit manager.",
      body: [
        "In this workflow the **unit manager validates** the unit's answers: **Validate** marks the answer as the unit's position for this bid (status **validated**, with the validator's name). From then on it counts in the green segment of the Bids bar, in the compliance matrix and its exports, and can be nominated as a reviewed example.",
        "Validation checks substance: is the claim defensible against the quote, is the product right. A doubtful answer is **returned**.",
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
      fallback: "While a row is submitted, Return opens a note box next to Validate; with no submitted rows left there is nothing to return.",
      body: [
        "**Return** opens a note box; the note is **required** and the unit sees it. The row goes back to **returned**, reopens for the unit with the note above its form, and counts as open again. The **bid manager** can also return any answer with a **question**, without validating it, which is how a bid-level question reaches a unit; questions and comments stay on the row until closed.",
      ],
    },
    {
      id: "inbox-switch-bm",
      title: "Back to the bid manager",
      route: "/inbox/CROWN",
      target: "inbox-table",
      placement: "top",
      kind: "action",
      instruction: "Sign out and sign in again as bid.manager, or press Use example.",
      skipIf: (ctx) => ctx.actor === BM,
      body: [
        "The next chapters are the bid manager's: the compliance matrix, the activity log, the catalog and changes. Sign in again as the Bid Manager.",
      ],
      example: { label: "Sign in as Bid Manager", apply: (ctx) => ctx.signInAs("bid.manager") },
      done: (ctx) => ctx.actor === BM,
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
        "The **hand-off** buttons download one JSON per unit and bid: the bid, the unit, the go/no-go decision, `stated_facts` (ratings read from the requirements, each citing its REQ) and the unit's items grouped into three routes: a **CPQ seed** for configure-to-order products, a **basis of design** for semi-custom ones and a **specialist queue** for engineered-to-order work. Each item carries its source, quote, product, offering type, engineering flags and the unit's answer with its status.",
        "The file says `requires_human_completion: true`: Layer 0 seeds the configurator and briefs engineering; it does not configure or design anything. It is regenerated from the current data on every download.",
      ],
    },
  ],
};
export default chapter;
