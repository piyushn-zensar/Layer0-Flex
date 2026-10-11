// Walkthrough chapter 11: Changes (P-11): an addendum read against the frozen baseline, each change confirmed by a
// person, applied by the Bid Manager. ALWAYS runs on the seeded demo OPP-0001, whatever ctx.oppId is: the sample
// addendum's frozen change-agent answers are keyed by the demo's approved line items, so on any other opportunity the
// offline model has no answer (the sample route answers 409).  Owner: consolidation/changes page group.
import { DEMO_OPP, type TourChapter, type TourCtx } from "../types";
import { openDetails, present } from "../helpers";
import type { ChangeSet, Changes } from "@/lib/types";

const OPP = DEMO_OPP;
const ROUTE = `/opportunities/${OPP}/changes`;
const TRACE = `/opportunities/${OPP}/trace`;
const SAMPLE = "syracuse_addendum_1";
const SAMPLE_FILE = "rfp_syracuse_addendum_1.pdf";
const BID_MANAGER = "Bid Manager";

/** The newest change set of OPP-0001 (the API lists newest first), or null. */
async function latest(ctx: TourCtx): Promise<ChangeSet | null> {
  try { return (await ctx.api<Changes>(`/api/opportunities/${OPP}/changes`)).sets[0] ?? null; } catch { return null; }
}
const inReview = async (ctx: TourCtx) => (await latest(ctx))?.status === "review";
const notInReview = async (ctx: TourCtx) => !(await inReview(ctx));
/** A set in review or applied exists: the example upload would be refused (409), so the upload steps are skipped. */
const setExists = async (ctx: TourCtx) => { const s = await latest(ctx); return !!s && s.status !== "discarded"; };
const noResult = async (ctx: TourCtx) => !(await latest(ctx))?.result;
const missing = (id: string) => (ctx: TourCtx) => ctx.el(id) === null;

/** Set a form control's value the way React sees it (native setter + input/change events). */
function setValue(el: Element | null, value: string) {
  if (!(el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement || el instanceof HTMLSelectElement)) return;
  const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), "value")?.set;
  if (setter) setter.call(el, value); else el.value = value;
  el.dispatchEvent(new Event("input", { bubbles: true }));
  el.dispatchEvent(new Event("change", { bubbles: true }));
}
/** Make the Changes page (and the opportunity header) re-fetch after an API call made by the walkthrough. */
function refreshPage() {
  window.dispatchEvent(new Event("focus")); // useApi re-fetches when the tab regains focus
  window.dispatchEvent(new Event("opp-status-changed")); // the opportunity header's baseline / status
}
/** Remember the apply result's IDs for the Traceability step. */
async function remember(ctx: TourCtx) {
  const s = await latest(ctx);
  if (!s?.result) return;
  ctx.set("changes.setId", s.id);
  ctx.set("changes.added", s.result.added);
  ctx.set("changes.modified", s.result.modified);
  ctx.set("changes.removed", s.result.removed);
}

const chapter: TourChapter = {
  id: "changes",
  order: 11,
  title: "Addenda and change handling",
  summary: "Read Addendum No. 1 against the frozen Syracuse baseline, confirm each change the agent proposes, apply it as the Bid Manager, and follow a revised requirement back to the addendum page in Traceability. Always on the demo opportunity OPP-0001.",
  entryRoute: ROUTE,
  steps: [
    {
      id: "changes-intro",
      title: "Changes: when the customer moves the goalposts",
      route: ROUTE,
      body: [
        "After an RFP is issued, customers send **addenda**, **answers to bidders' questions** and **change requests**. Each one can change requirements that units are already answering. This screen reads such a document like the RFP, compares every statement in it with the **frozen baseline**, and lets a person confirm each change before the Bid Manager applies it as the next baseline.",
        "This chapter always runs on the seeded demo **OPP-0001** (Syracuse switchgear), not on your walkthrough opportunity: the sample addendum's frozen change-agent answers are keyed by the demo's approved line items, so the offline model only has answers for that requirement set. On any other opportunity the example would be refused.",
        "What you will do: read *Addendum No. 1* with one click, inspect the 8 statements the agent found and how it classified them, override one wording, confirm the rest, apply as the Bid Manager, then follow a revised requirement into Traceability, where pane 1 shows the addendum page. Finish with the result block: it names what was added, revised, removed, returned and dispatched.",
      ],
    },
    {
      id: "changes-baseline",
      title: "The current baseline",
      route: ROUTE,
      target: "chg-baseline",
      placement: "bottom",
      fallback: "Without a frozen baseline the page shows a warning instead: freeze the requirements first.",
      body: [
        "*Current baseline 1: 348 requirements.* A baseline is the frozen, numbered set of approved requirements. Change documents are always compared with the **latest** baseline, and applying a change set freezes the next one (baseline 2) without editing anything in place: every change is a new version or a new ID, so baseline 1 stays readable in each requirement's history.",
        "If the requirements were not frozen, the page would show a warning and no upload form: there is nothing to compare with yet.",
      ],
    },
    {
      id: "changes-upload-form",
      title: "Read a change document",
      route: ROUTE,
      target: "chg-upload",
      placement: "bottom",
      fallback: "The upload form takes one PDF: an addendum, Q&A answers or a change request.",
      body: [
        "One PDF at a time (`.pdf` only). The file is stored with the role *change* and read by the same layout model and anchoring as the RFP, so every statement gets a page and lines. Then two frozen model tasks run: **read_changes** lists the statements (a verbatim quote, the requirement as it reads *after* the change, a category, and what the document says it does: add, modify, delete, clarify or info); **classify_change** compares each statement with up to five candidate baseline requirements (ranked by TF-IDF, labelled A to E so no requirement ID is in the prompt) and proposes *added*, *modified*, *removed*, *unchanged* or *not a requirement*, with a confidence and a rationale.",
        "*info* statements (cover text, signatures, 'acknowledge receipt') are *not a requirement* by rule, without a model call. Without a model answer nothing is guessed: the upload fails with a message and no set is created.",
        "Rules the form enforces: only **one set in review** at a time (the input is disabled with *Apply or discard the change set in review first*), the main RFP is refused as a change document, and a file that was already applied cannot be applied twice.",
      ],
    },
    {
      id: "changes-read-example",
      title: "Read Addendum No. 1",
      route: ROUTE,
      target: "chg-upload-button",
      placement: "bottom",
      kind: "action",
      skipIf: setExists,
      instruction: "Click 'Use example' to read the sample addendum, or choose data/RFP/samples/rfp_syracuse_addendum_1.pdf in the file input and click 'Read the change document'. Then wait for the change set card.",
      example: {
        label: "Use example: Addendum No. 1 (Syracuse)",
        apply: async (ctx) => {
          const set = await ctx.post<ChangeSet>(`/api/opportunities/${OPP}/changes/from-sample`, { name: SAMPLE });
          ctx.set("changes.setId", set.id);
          refreshPage();
        },
      },
      done: present("chg-set"),
      fallback: "The 'Read the change document' button is in the upload form; it is disabled while a set is in review.",
      body: [
        "The sample is an **illustrative** Addendum No. 1 to the Syracuse RFP (one page, written for this PoC): two modifications (a new submission date, twenty instead of eighteen breaker positions), two additions (seismic qualification, a 60-month warranty), one deletion (AutoCAD drawings), one question and answer that confirms the RFP, and two lines of cover text.",
        "*Use example* calls `POST /api/opportunities/OPP-0001/changes/from-sample` with `{\"name\": \"syracuse_addendum_1\"}`, which stores and reads the same PDF the file input would. Reading takes a few seconds offline (frozen answers); the card appears below the form when it is done.",
      ],
    },
    {
      id: "changes-set-card",
      title: "The change set card",
      route: ROUTE,
      target: "chg-set-head",
      placement: "bottom",
      fallback: "Each change document read becomes one card: file name, status and the confirmed count.",
      body: [
        "One card per change document, newest first: the **file name** (*rfp_syracuse_addendum_1.pdf*), the set's **status** pill (*in review*: a person is confirming; *applied*: it became a baseline; *discarded*: dropped, baseline unchanged) and **confirmed / total**: how many of its statements a person has confirmed (0 / 8 right after reading).",
        "A set is a unit of work: everything in it is applied together, or not at all.",
      ],
    },
    {
      id: "changes-set-meta",
      title: "Who read it, against what",
      route: ROUTE,
      target: "chg-set-meta",
      placement: "bottom",
      fallback: "Under the title: who read the document, when, and against which baseline.",
      body: [
        "*Read by Bid Manager on … against baseline 1.* The baseline number matters: a set can only be applied while that baseline is still the latest. If another set is applied first, this one is refused with *discard it and upload the document again*, because its comparison would be stale.",
        "After apply the line continues with *Applied by … : baseline 2*; a discarded set says so with no baseline change.",
      ],
    },
    {
      id: "changes-share",
      title: "How much of the baseline changes: the drastic rule",
      route: ROUTE,
      target: "chg-set-share",
      placement: "bottom",
      fallback: "A line under the card title says what share of the baseline is modified or removed.",
      body: [
        "*0.9% of the baseline is modified or removed (drastic above 25%, placeholder)*: 3 of 348 requirements (two modified, one removed; additions do not count). Above the threshold the line becomes a red **Drastic change** alert: *consider a new opportunity linked to this one. A person decides.*",
        "The 25% is a **placeholder** awaiting confirmation; Layer 0 never opens or closes an opportunity by itself, it only flags the share so the decision is taken by a person, in the open.",
      ],
    },
    {
      id: "changes-filters",
      title: "Counts by kind, as filters",
      route: ROUTE,
      target: "chg-set-filters",
      placement: "bottom",
      fallback: "Chips above the table count the statements per kind and filter the table.",
      body: [
        "*All 8 · Added 2 · Modified 2 · Removed 1 · Unchanged 1 · Not a requirement 2*. Each chip filters the table to that kind; click it again to clear. The kind of a row is the person's decision once confirmed, else the agent's proposal, so an override moves a row between chips.",
        "A statement the document itself calls a deletion can still end up *unchanged* if the person decides the baseline never required it, and the counts follow.",
      ],
    },
    {
      id: "changes-document",
      title: "The change document with highlights",
      route: ROUTE,
      target: "chg-doc",
      placement: "top",
      onEnter: openDetails("chg-doc"),
      fallback: "'Change document (1 page)' expands to the page image with one highlight box per statement.",
      body: [
        "The addendum's page image with one **highlight box** per statement, drawn from the same line boxes as Traceability pane 1: the statement's location was found by matching its verbatim quote in the document's lines, never from the model's own page claim. Click a box to select its row in the table (the filter is cleared if the row was hidden); click a row's **Source** link to open the document at its page.",
        "The pager steps through pages for longer documents; this addendum has one. Hover a box to see *Change N*.",
      ],
    },
    {
      id: "changes-table",
      title: "One row per change statement",
      route: ROUTE,
      target: "chg-items",
      placement: "top",
      fallback: "The table has one row per statement the change agent found.",
      body: [
        "Eight rows in document order, numbered **#1 to #8**: the two modifications (1-2), the two additions (3-4), the deletion (5), the Q&A (6) and the two cover lines (7-8). Clicking a row selects it and shows its page in the document above; the row's columns go from what the document says (source, quote) to what the agent proposes (kind, target, wording, rationale) to the person's decision.",
      ],
    },
    {
      id: "changes-col-quote",
      title: "Source and Quote",
      route: ROUTE,
      target: "chg-col-quote",
      placement: "bottom",
      fallback: "The Source and Quote columns tie each statement to its page and lines and to its verbatim text.",
      body: [
        "**Source** is *p. 1, lines 12-13* and so on: the page and lines where the quote was located; it is a button that opens the document there. **Quote** is the statement copied character for character from the document, e.g. *Section 1.9, Submission Due Date, page 5: replace \"09/15/2023 by 4:00PM\" with \"09/29/2023 by 4:00PM\".*",
        "The quote is the evidence and the anchor: when the change is applied, the new requirement version is anchored to these lines of the addendum, and every export names the addendum before the page.",
      ],
    },
    {
      id: "changes-col-proposed",
      title: "Proposed kind, confidence and rationale",
      route: ROUTE,
      target: "chg-col-proposed",
      placement: "bottom",
      fallback: "The Proposed column shows the agent's kind as a coloured pill with its confidence.",
      body: [
        "The agent's classification as a pill (added green, modified amber, removed red, unchanged and not a requirement grey) with its **confidence** (95% for the due date, 90% for the breaker count). The **Rationale** column says why in one sentence: *The change document specifies a new submission due date, which modifies the existing requirement in candidate A.*",
        "The kinds: **added** (no candidate covers it), **modified** (changes or replaces one candidate), **removed** (deletes one), **unchanged** (repeats or confirms one without changing what the bidder must do: the Type 2B question), **not a requirement** (cover text: rows 7 and 8, by rule, 100%). A candidate is chosen only when it is the same obligation; a similar topic is not enough.",
      ],
    },
    {
      id: "changes-col-target",
      title: "Target in the baseline",
      route: ROUTE,
      target: "chg-col-target",
      placement: "bottom",
      fallback: "The Target column names the baseline requirement a statement changes, removes or confirms.",
      body: [
        "For modified, removed and unchanged: the baseline requirement the statement acts on, as a link into Traceability, with its short text and source: row 1 targets **REQ-0001-0039** (*Submit proposals by 09/15/2023 at 4:00 PM via email.*), row 2 **REQ-0001-0332** (the breaker positions, a sub-requirement of the switchgear group), row 5 **REQ-0001-0130** (AutoCAD drawings), row 6 **REQ-0001-0333** (Arc-resistant Type 2B). Added rows show *new requirement*.",
        "After apply, a modified target reads *Revised in baseline 2; the earlier wording is in its history (Requirements page)* and a removed one is plain text, because it has left Traceability.",
      ],
    },
    {
      id: "changes-col-wording",
      title: "New wording and category",
      route: ROUTE,
      target: "chg-col-wording",
      placement: "bottom",
      fallback: "The New wording column holds the requirement as it reads after the change, for added and modified rows.",
      body: [
        "Only for added and modified rows: the requirement **as it reads after the change**, in plain English, with its category tag (*schedule*, *technical*, *compliance*): *Submit proposals by 09/29/2023 at 4:00 PM via email.* This text becomes the new version's short text when applied; the quote stays the addendum's own sentence.",
        "Removed, unchanged and not-a-requirement rows show a dash: nothing new is written for them.",
      ],
    },
    {
      id: "changes-decision-form",
      title: "The decision: a person confirms every classification",
      route: ROUTE,
      target: "chg-decide-form",
      placement: "left",
      skipIf: notInReview,
      onEnter: (ctx) => ctx.el("chg-row-1")?.scrollIntoView({ block: "center", behavior: "smooth" }),
      fallback: "While a set is in review, each undecided row ends with a small form: Change, Baseline requirement, New wording, Confirm.",
      body: [
        "Rule R4 of this PoC: agents propose, a person confirms. Every row in review ends with a form prefilled with the proposal. **Change** picks one of the five kinds. **Baseline requirement** (for modified, removed, unchanged) lists the agent's candidates A to E with the proposed one first, plus *Another requirement ID…* for a requirement the agent did not offer: it must be an approved line item of the current baseline, otherwise the confirm is refused with the reason in red.",
        "**New wording** (for added and modified) can be edited; it is only sent when it differs from the proposal. **Confirm** records the decision with your name; a confirmed row shows the kind, the target and *Confirmed by …* with a *Change* link to reopen it. Anyone may confirm; only applying is reserved to the Bid Manager.",
      ],
    },
    {
      id: "changes-override",
      title: "Override one wording and confirm",
      route: ROUTE,
      target: "chg-decide-form",
      placement: "left",
      kind: "action",
      skipIf: async (ctx) => !(await inReview(ctx)) || ctx.el("chg-decide-form") === null,
      instruction: "In the first row (the submission due date), change the New wording, e.g. append '(per Addendum No. 1)', keep Modified and REQ-0001-0039, then click Confirm.",
      example: {
        label: "Fill the new wording",
        apply: (ctx) => {
          const text = ctx.el("chg-decide-text") as HTMLTextAreaElement | null;
          if (!text) throw new Error("The decision form of the first row is not on the page (already confirmed?).");
          const base = text.value.replace(/\s*\(per Addendum No\. 1\)\s*$/, "").trim();
          setValue(text, `${base} (per Addendum No. 1)`);
          text.focus();
        },
      },
      done: present("chg-decided"),
      fallback: "The first row is already decided; use 'Change' on any row to reopen its form.",
      body: [
        "A small, safe override: keep the agent's kind (*Modified*) and target (*REQ-0001-0039*) and only adjust the wording. On apply, this text becomes version 2 of REQ-0001-0039, anchored to lines 12-13 of the addendum, and the earlier wording stays in its history.",
        "Any other override works the same way: switch the kind to *Unchanged* to keep a requirement as it is, or pick another candidate as the target. Changing a target to a requirement that is already changed by another row is caught at apply time (*Items … all change REQ-…*): combine them into one row and mark the others unchanged.",
      ],
    },
    {
      id: "changes-decided",
      title: "A confirmed row",
      route: ROUTE,
      target: "chg-decided",
      placement: "left",
      skipIf: missing("chg-decided"),
      fallback: "A confirmed row shows its kind pill, the target ID and 'Confirmed by …'.",
      body: [
        "The row now shows the decided kind, the target ID and *Confirmed by Bid Manager* (whoever is acting). The card header counts it (*1 / 8 confirmed*) and the chips follow the decision. **Change** reopens the form while the set is in review; after apply, decisions are read-only history.",
      ],
    },
    {
      id: "changes-confirm-all",
      title: "Confirm all proposals",
      route: ROUTE,
      target: "chg-confirm-all",
      placement: "top",
      kind: "action",
      skipIf: async (ctx) => { const s = await latest(ctx); return !s || s.status !== "review" || s.confirmed >= s.total; },
      instruction: "Click 'Confirm all proposals'.",
      done: (ctx) => { const b = ctx.el("chg-confirm-all") as HTMLButtonElement | null; return !b || (b.disabled && !b.closest('[aria-busy="true"]')); },
      fallback: "'Confirm all proposals' is in the action row of a set in review.",
      body: [
        "Confirms every still-proposed row **as proposed** (rows already decided keep their decision). It is a shortcut for the usual case where the agent's proposals are right; the audit log still records who confirmed. Apply is only enabled once *confirmed = total*, and the row of grey text under the buttons counts what is left.",
      ],
    },
    {
      id: "changes-discard",
      title: "Discard",
      route: ROUTE,
      target: "chg-discard",
      placement: "top",
      fallback: "Discard is only shown while a set is in review (this set is already applied or discarded): it drops the set and leaves the baseline as it is.",
      body: [
        "The other way out of review: **Discard** (Bid Manager only, with a confirmation dialog) drops the change set and every decision in it; the baseline stays as it is and the document can be read again later. Use it when a document was uploaded by mistake, or when the comparison went stale because another set was applied first.",
        "Nothing in this chapter asks you to discard: the next step applies the set, which is the state the rest of the walkthrough builds on. After apply (or discard) the button is gone and the card is read-only history.",
      ],
    },
    {
      id: "changes-apply",
      title: "Apply to requirements (Bid Manager only)",
      route: ROUTE,
      target: "chg-apply",
      placement: "top",
      kind: "action",
      skipIf: notInReview,
      instruction: "Acting as Bid Manager, click 'Apply to requirements' and wait for the green result block.",
      example: {
        label: "Act as Bid Manager",
        apply: (ctx) => { if (ctx.actor !== BID_MANAGER) ctx.setActor(BID_MANAGER); },
      },
      done: present("chg-set-result"),
      fallback: "'Apply to requirements' is in the action row of a set in review; it is enabled for the Bid Manager once every row is confirmed.",
      body: [
        "Only the **Bid Manager** applies or discards (the button is disabled for anyone else and the API checks the acting person too; switch with *Acting as* in the header). Apply refuses if any row is unconfirmed, if two rows change the same requirement, or if the baseline moved since the upload.",
        "What it does, in one transaction: each **added** statement becomes a new, approved requirement with a new ID anchored in the addendum; each **modified** one becomes **version 2** of its target with the new wording and the addendum's quote and lines; each **removed** one gets a version with status *removed* (removing a group removes its sub-requirements); then **baseline 2** is frozen with the new count. Then the follow-up: the unit answers of changed requirements are **returned** for review with a note (*Changed by rfp_syracuse_addendum_1.pdf: now reads: …*), only the added and modified requirements are **re-matched** (re-matching everything would change the frozen page batches of untouched ones), and if work was dispatched before and the latest go/no-go is *go*, **dispatch** runs: new assignments go out and removed work is withdrawn.",
        "A failure after the baseline is committed (for example the model service) is reported in the result's note, not raised: the baseline stands, and matching or dispatch can be run from their own pages.",
      ],
    },
    {
      id: "changes-result",
      title: "What the apply did",
      route: ROUTE,
      target: "chg-set-result",
      placement: "bottom",
      skipIf: noResult,
      onEnter: remember,
      fallback: "After apply a green block 'Baseline 2 frozen with the changes' lists the added, modified and removed IDs, the returned answers and the dispatched work.",
      body: [
        "**Baseline 2 frozen with the changes.** *Added*: two new IDs (seismic qualification, warranty), links into Traceability where pane 1 shows the addendum. *Modified (new version)*: REQ-0001-0039 and REQ-0001-0332, now at version 2. *Removed*: REQ-0001-0130, shown as plain text because it has left Traceability (its history is on the Requirements page).",
        "*2 unit answer(s) returned for review*: both modified requirements are sub-requirements, so the answers of their groups go back to the units (the submission group REQ-0001-0824 and the switchgear group REQ-0001-0887, whose validated answer from Crown Technical Systems is now back for review) with a note of what changed; the Final response count drops until they are answered again. *2 new assignment(s) sent*: the added requirements dispatched to the units matching proposed, because the demo had dispatched before and its go/no-go is *go*. When that is not the case the note says *Not dispatched: …* and why.",
        "The header now reads baseline 2; the upload form is enabled again for the next addendum; the whole set is read-only history with every decision and who took it.",
      ],
    },
    {
      id: "changes-trace",
      title: "Follow a revised requirement into Traceability",
      route: TRACE,
      target: "trace-pane-1",
      placement: "right",
      skipIf: noResult,
      onEnter: async (ctx) => {
        // Added requirements first: they are top-level rows anchored in the addendum. A modified sub-requirement
        // (REQ-0001-0039, -0332 in the demo) has no row of its own: its group is the row, and the group stays in the RFP.
        const ids = [...(ctx.get<string[]>("changes.added") ?? []), ...(ctx.get<string[]>("changes.modified") ?? [])];
        if (!ids.length) return;
        for (let i = 0; i < 40; i++) { // the trace page loads its rows after the pane is on the page
          for (const id of ids) {
            const row = document.querySelector<HTMLElement>(`tr[data-req="${id}"]`);
            if (row) { row.click(); row.scrollIntoView({ block: "center", behavior: "smooth" }); return; }
          }
          await new Promise((r) => setTimeout(r, 250));
        }
      },
      fallback: "Open /opportunities/OPP-0001/trace#REQ-0001-0977 (the first added requirement): pane 1 switches to the addendum and highlights lines 17-19.",
      body: [
        "This is Traceability with the first **added** requirement of the result selected (REQ-0001-0977 in the demo: the seismic qualification; the same link the result block offers). Pane 1 shows a **document switch** (*RFP* / *rfp_syracuse_addendum_1.pdf*) and opens the **addendum page** with the requirement's lines highlighted: it is anchored to the addendum, p. 1, lines 17-19, not to the RFP, and every export writes its source as *rfp_syracuse_addendum_1.pdf, p. 1, lines 17-19*.",
        "The two modified requirements are **sub-requirements** of groups (REQ-0001-0039 belongs to the submission group REQ-0001-0824, REQ-0001-0332 to the switchgear group REQ-0001-0887): a link to them opens their group's row, where pane 2 lists them at version 2 with the new wording (the earlier text is in the history on the Requirements page), and pane 3 shows the group's answers, including the one returned with the change note. The removed REQ-0001-0130 is no longer listed here.",
        "That closes the loop: a customer change arrives as a document, becomes confirmed decisions, a new baseline, returned work, and stays traceable to its page and lines. Next: the recap.",
      ],
    },
  ],
};
export default chapter;
