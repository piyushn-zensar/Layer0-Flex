// Walkthrough chapter 8: My work: unit work packages, answers and validation (web/app/inbox, web/app/inbox/[bu]).  Owner: Janvia (J-15).
// Runs on /inbox/CROWN as "Crown Product Manager" (the unit manager answers the unit's schedule, commercial and staffing
// items and validates its designers' / engineers' technical answers), then back to the bid manager, who validates the unit
// manager's answer (workflow.json, 19 Oct 2026: nobody validates their own answer). The first open row of the walkthrough
// bid is the highlighted one. Roles come from data/knowledge_base/workflow.json.
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
const rowStatus = async (ctx: TourCtx, key = "inboxAssignment") => {
  const id = ctx.get<number>(key);
  return id ? (await crown(ctx)).find((a) => a.id === id)?.status : undefined;
};
/** Remember the row whose Validate is lit: the first submitted row of the bid, which on the demo bid can be an answer
 * submitted before the walkthrough rather than the one just submitted. Its first cell reads "OPP-xxxxREQ-xxxx-xxxx". */
const rememberValidate = async (ctx: TourCtx) => {
  const m = ctx.el("inbox-validate")?.closest("tr")?.querySelector("td")?.textContent?.match(/(OPP-\d+)\s*(REQ-\d+-\d+)/);
  const row = m && (await crown(ctx)).find((a) => a.opportunity_id === m[1] && a.req_id === m[2]);
  if (row) ctx.set("inboxValidate", row.id);
};

const chapter: TourChapter = {
  id: "inbox",
  order: 8,
  title: "My work: unit answers and validation",
  summary: "My work and the unit work packages: sign in as Crown's unit manager, give the unit's delivery estimate and its five factors, answer a requirement with one of the four outcomes and submit it, then validate it as the bid manager, and download the unit's hand-off file.",
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
        "The bid desk holds the high-level, consolidated items answered once for the whole bid: on Syracuse the **73** submission and legal requirements, plus any recorded capability gaps. The bid manager answers and validates those personally. The units hold the rest: technical items for their designers / engineers, schedule, commercial and staffing items for their unit managers.",
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
        "Each person signs in; **Sign out** in the top bar leads to the sign-in page. The sign-in token travels in a cookie with every request, the server records the signed-in name on every event and enforces the role rules from `workflow.json`: a unit's **designers / engineers** answer its technical items and its **unit manager** validates them; the unit manager answers the other items and the **bid manager** validates those, so nobody validates their own answer. The bid manager may also return any answer with a question.",
        "Crown Product Manager is Crown Technical Systems' **Unit manager**. Reading is open to everyone; writing is tied to the role and the unit.",
      ],
      example: { label: "Sign in as Crown Product Manager", apply: (ctx) => ctx.signInAs("crown.pm") },
      done: (ctx) => ctx.actor === CROWN_PM,
    },
    {
      id: "inbox-completion",
      title: "Your unit's delivery estimates",
      route: "/inbox/CROWN",
      target: "inbox-completion",
      placement: "bottom",
      fallback: "The unit manager sees one row per bid with the unit's estimate and its five delivery factors.",
      body: [
        "This is **delivery feasibility from the team**. The unit manager states **when the unit expects to finish each bid** and reports five factors that could limit delivery: **people, skills, manufacturing capacity, materials and cost**, each *No constraint* or *Constraint* with a note on what limits delivery (the note is required for a constraint). Technical feasibility is the designers' / engineers' answers.",
        "The bid manager accepts these estimates on the Assessment Summary, which shows each unit's constraints and warns when the planned date falls after the RFP's due date; the units set the dates, not the bid manager, and no resource plan is needed.",
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
        "The chips switch between work packages, with a count of answers waiting for the signed-in person's validation. A unit's people see only their own unit here; the bid manager and the administrator see the bid desk and every unit with work. Only a package's own people act on it, and a blue banner says so when you are only reading.",
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
        "**Open the RFP** has one button per bid; it opens that bid's Requirement Traceability page, where the unit reads the requirement next to the highlighted lines of the PDF. **Download hand-off file** (one button per bid) downloads a JSON of the unit's items grouped into routes for its own tools (explained at the end of the chapter).",
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
      fallback: "Each row you may answer carries a compact form: a compliance select, the proposed solution and a \"How it is met\" text box.",
      body: [
        "**Compliance** has four outcomes: **Compliant**, **Partially compliant**, **Compliant with changes** (a deviation from the requested specification) or **Non-compliant**. It is what the compliance matrix and the go/no-go are built from, so choose it honestly. For a technical item, the **Proposed solution** (unit · solution area, with example models) is shown above the answer; say in **How it is met** which configuration you offer. **How it is met** is the answer in the unit's words.",
        "Unless the answer is Compliant, a **Reason** (what is not met or what changes, and why) is **required**; for Compliant with changes the **Proposed change** is required too; **Conditions** and **Next steps** are optional and appear in the matrix and its exports. The highlighted row is the first open row of the bid that the unit manager may answer (a schedule, commercial or staffing item). **Use example** fills a plausible answer.",
      ],
      example: {
        label: "Fill an example answer",
        apply: (ctx) => {
          rememberRow(ctx);
          setValue(field(ctx, "inbox-compliance"), "met");
          setValue(field(ctx, "inbox-response"),
            "Compliant. Crown Technical Systems will meet the dates in the RFP; the unit's estimate and delivery factors are entered under Your unit's delivery estimates.");
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
        "The row shows the compliance in bold and the explanation, with a **submitted** badge. On the Bids screen the Crown bar gained a blue \"awaiting validation\" segment. Nothing else moves until it is validated (here by the bid manager, because the unit manager gave it): the compliance matrix and the exports treat an answer as the unit's position only once it is **validated**.",
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
      id: "inbox-switch-bm",
      title: "Back to the bid manager to validate",
      route: "/inbox/CROWN",
      target: "inbox-table",
      placement: "top",
      kind: "action",
      instruction: "Sign out and sign in again as bid.manager, or press Use example.",
      skipIf: (ctx) => ctx.actor === BM,
      body: [
        "Nobody validates their own answer. A unit manager's schedule, commercial or staffing answer is validated by the **bid manager**; a designer's / engineer's technical answer by the **unit manager**. Sign in again as the Bid Manager to validate the unit manager's submitted answers. The next chapters are the bid manager's too: the compliance matrix, the activity log, the catalog and changes.",
      ],
      example: { label: "Sign in as Bid Manager", apply: (ctx) => ctx.signInAs("bid.manager") },
      done: (ctx) => ctx.actor === BM,
    },
    {
      id: "inbox-validate",
      title: "Validate the answer",
      route: "/inbox/CROWN",
      target: "inbox-validate",
      placement: "left",
      kind: "action",
      onEnter: rememberValidate,
      instruction: "Press Validate on the highlighted row (as the bid manager): the first answer of this bid waiting for validation, on the demo bid possibly one given before yours.",
      fallback: "Submitted rows show Validate and Return in the Status column to the person who validates them: the bid manager for the unit manager's answers, the unit manager for technical answers.",
      body: [
        "**Validate** marks the answer as the unit's position for this bid (status **validated**, with the validator's name). The bid manager validates the unit manager's answers, as here; the unit manager validates the designers' / engineers' technical answers, which is what **Reviewed by design engineers** on the Assessment Summary counts. From then on the answer counts in the green segment of the Bids bar, in the compliance matrix and its exports, in the reviewed compliance outcomes of the Bid decision, and can be nominated as a reviewed example.",
        "Validation checks substance: is the claim defensible against the quote, is the outcome right, is the proposed solution or the proposed change right. A doubtful answer is **returned**.",
      ],
      done: async (ctx) => {
        const s = (await rowStatus(ctx, "inboxValidate")) ?? (await rowStatus(ctx));
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
        "**Return** (next to Validate, for the person who validates) opens a note box; the note is **required** and the unit sees it. The row goes back to **returned**, reopens for the unit with the note above its form, and counts as open again. The **bid manager** can also return any answer with a **question**, without validating it, which is how a bid-level question reaches a unit; questions and comments stay on the row until closed.",
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
        "The **hand-off** buttons download one JSON per unit and bid: the bid, the unit, the go/no-go decision, `stated_facts` (ratings read from the requirements, each citing its REQ) and the unit's items grouped into three routes: a **CPQ seed** for configure-to-order products, a **basis of design** for semi-custom ones and a **specialist queue** for engineered-to-order work. Each item carries its source, quote, proposed solution (unit · solution area, example models; the catalog family ID is kept for the unit's systems), type of offer, engineering flags and the unit's answer with its status.",
        "The file says `requires_human_completion: true`: Layer 0 seeds the configurator and briefs engineering; it does not configure or design anything. It is regenerated from the current data on every download.",
      ],
    },
  ],
};
export default chapter;
