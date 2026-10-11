// Walkthrough chapter 7: The bid decision and dispatch (app/opportunities/[id]/decisions).
// Targets are data-tour ids on the decisions page ("dec-*"). Action steps are skipped when the decision is already taken
// (the seeded demo OPP-0001 is dispatched) and when the requirements are not frozen (the forms are disabled then).
import type { TourChapter, TourCtx } from "../types";
import { present, statusIn, openDetails } from "../helpers";

const ROUTE = "/opportunities/{opp}/decisions";
const FROZEN = ["frozen", "go", "no_go", "dispatched", "consolidating", "submitted"];
const DECIDED = ["go", "no_go", "dispatched", "consolidating", "submitted"];
const notFrozen = async (ctx: TourCtx) => !(await statusIn(...FROZEN)(ctx));
const decidedOrNotFrozen = async (ctx: TourCtx) => (await notFrozen(ctx)) || (await statusIn(...DECIDED)(ctx));

/** Set an input's value the way React sees it (native setter + input event); the forms here are uncontrolled, so .value alone would also do. */
const setValue = (el: HTMLInputElement | HTMLSelectElement | null | undefined, value: string) => {
  if (!el) return;
  const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), "value")?.set;
  if (setter) setter.call(el, value); else el.value = value;
  el.dispatchEvent(new Event("input", { bubbles: true }));
  el.dispatchEvent(new Event("change", { bubbles: true }));
};
const input = (ctx: TourCtx, card: string, name: string) =>
  ctx.el(card)?.querySelector<HTMLInputElement | HTMLSelectElement>(`[name="${name}"]`);

const chapter: TourChapter = {
  id: "decisions",
  order: 7,
  title: "The bid decision and dispatch",
  summary: "Read the evidence pack and the checks, choose the participating units, record go or no-go with your judgement on each criterion, then send each unit its work.",
  entryRoute: ROUTE,
  steps: [
    {
      id: "decisions-intro", route: ROUTE,
      title: "Bid decision: evidence first, then a person decides",
      body: [
        "This is the **Bid decision** screen, step 4 of the workflow. It is built live from the frozen requirements and the current matches of the Traceability page: an **Evidence** card with counts, the **Engineering checks** and the **Bid and portfolio checks**, then three numbered cards for the decisions themselves: **1. Which business units take part?**, **2. Go / no-go** with Layer 0's summary and your judgement per criterion, and, after a go, **3. Send the work to the units** (dispatch).",
        "Why it exists: a go/no-go must be taken on evidence that can be traced, by a named person, and recorded with that evidence. Everything on this page is advice; the advice line says so explicitly: *A person decides*. The decision stores the evidence pack as it was shown, so it can be audited later.",
        "What to finish before leaving: participation recorded, go or no-go recorded with a rationale, and after a go, work dispatched. The header's status badge and stepper move from *frozen* to *go* (or *no-go*) and then to *dispatched* as you do.",
      ],
    },
    {
      id: "decisions-evidence", route: ROUTE, target: "dec-evidence-counts", placement: "bottom",
      title: "Evidence: counts by category",
      body: [
        "The Evidence card starts with the number of current requirements and how many fall in each category, for the Syracuse RFP: **348 requirements · technical 146, submission 87, compliance 66, legal 18, commercial 11, staffing 11, schedule 9**. Only technical and compliance items are product items; the rest will be answered by the bid desk.",
        "The counts are computed from the live requirement list, so a split, a merge or a rejection on the Requirements page changes them at once; matches of items that no longer exist are not counted.",
      ],
    },
    {
      id: "decisions-offering-mix", route: ROUTE, target: "dec-offering-mix", placement: "bottom",
      title: "Offering mix",
      body: [
        "One badge per offering type with the number of matches: for the demo **ETO 96, CTO 5, Semi-custom 2, NONE 245**. NONE is the bid desk (not a product item). A mix dominated by ETO, as here, means engineering effort rather than catalog quoting; the summary below counts ETO and Semi-custom as *partly* satisfied until a unit confirms.",
        "Before matching this line is empty: run **Match products** on the Traceability page first.",
      ],
    },
    {
      id: "decisions-suggested-units", route: ROUTE, target: "dec-suggested-units", placement: "bottom",
      title: "Suggested units",
      body: [
        "Each business unit that appears in at least one match, with the number of requirements it is matched to: **CROWN (96) EP2 (7)** for the Syracuse switchgear RFP. A requirement with several units counts once for each. Rejected matches do not count.",
        "These suggestions pre-tick the participation checkboxes below. They are the matcher's view; the participation decision is yours.",
      ],
    },
    {
      id: "decisions-unanchored", route: ROUTE, target: "dec-unanchored", placement: "bottom", onEnter: openDetails("dec-unanchored"),
      title: "Unanchored requirements",
      body: [
        "Requirements whose quote could not be located on an RFP page: **32** in the Syracuse read. Expand the line to see their IDs. They are matched and dispatched like any other, but a reviewer cannot check them against a highlight, which is why they count as open questions in the summary.",
      ],
      fallback: "Every requirement of this opportunity is anchored to a page, so this line is not shown.",
    },
    {
      id: "decisions-unmatched", route: ROUTE, target: "dec-unmatched", placement: "bottom",
      title: "Not yet matched",
      body: [
        "Requirements without any match, including the bid desk. It appears only when the matcher has not run over every approved requirement (for example after new requirements were added by an addendum). The criterion *Every requirement routed* fails while this is above zero; run **Match products** again to clear it.",
      ],
      fallback: "Every requirement has a match, so this line is not shown.",
    },
    {
      id: "decisions-not-reviewed", route: ROUTE, target: "dec-not-reviewed", placement: "bottom",
      title: "Product matches nobody has reviewed",
      body: [
        "The number of product matches still *proposed*: nobody has accepted or changed them on the Traceability page (pane 3). Bid-desk routings are not counted. The demo starts at **103**; each Accept or Change on the Traceability page lowers it. The criterion *Matches reviewed* is met only at zero.",
      ],
      fallback: "Every product match has been accepted or changed, so this line is not shown.",
    },
    {
      id: "decisions-not-frozen", route: ROUTE, target: "dec-not-frozen", placement: "bottom", skipIf: statusIn(...FROZEN),
      title: "The requirements must be frozen first",
      body: [
        "Go/no-go needs a baseline: the engineering checks, the portfolio checks and the summary are computed over the **frozen** approved requirements, and the Go and No-go buttons stay disabled until then. Freeze on the Requirements page (chapter 5), then come back: the checks and the summary appear here.",
        "Participation can be recorded before freezing; the matcher can run before freezing too.",
      ],
      fallback: "The requirements are frozen: the checks and the summary are available.",
    },
    {
      id: "decisions-eng", route: ROUTE, target: "dec-eng-checks", placement: "top", skipIf: notFrozen,
      title: "Engineering checks",
      body: [
        "Four checks ported from the earlier code line (v0.3.0) and run over the frozen requirements, with no model call: **scope** (which grid-to-chip layers the RFP covers), **rules** R-001 to R-004, **offering type against each unit's default tier**, and the **low-voltage solver**. They are keyword-based and illustrative, marked to be confirmed with SpinCo engineering; they never decide anything.",
        "Each finding cites the requirement IDs it was read from (links back to Traceability), and a fact the RFP does not state is reported as *warn*, never *pass*.",
      ],
      fallback: "The engineering checks appear once the requirements are frozen.",
    },
    {
      id: "decisions-eng-scope", route: ROUTE, target: "dec-eng-scope", placement: "top", skipIf: notFrozen,
      title: "Scope: the layers this RFP covers",
      body: [
        "SpinCo's offer is modelled as six layers from grid to chip: 1 Grid Interface (EPC), 2 Utility / Facility Electrical (Crown, EP², Anord Mardix), 3 Power Distribution (Anord Mardix), 4 Rack & Board Power (FPM, EPC), 5 Thermal Management (JetCool), 6 Compute + Integration (Cloud). A layer is **in scope** on weight of evidence in the quotes: at least 3 keyword hits, or 2 distinct terms, or one decisive term such as \"metal clad switchgear\" or \"direct-to-chip\".",
        "For Syracuse, layer 2 is in scope by decisive term (\"switchgear\" ×66, \"metal clad switchgear\" ×19, \"protective relay\" ×7) and layer 3 by 5 hits of \"prefabricated\"; the others have no evidence. If no layer meets a threshold the full scope is assumed: no evidence is not evidence of a narrow scope.",
        "A warning lists units suggested although nothing in the RFP points to their layers (none here). That feeds the criterion *Scope fit*.",
      ],
      fallback: "The scope check appears once the requirements are frozen.",
    },
    {
      id: "decisions-eng-rules", route: ROUTE, target: "dec-eng-rules", placement: "top", skipIf: notFrozen,
      title: "Rules R-001 to R-004",
      body: [
        "**R-001** 800 V DC: if any layer specifies 800 V DC, every power-path layer (1, 3, 4) must be compatible; here it passes because the stated architecture is 125 V DC (`REQ-0001-0953`). **R-002** cooling: a rack density of 100 kW or more needs direct-to-chip cooling (JETCOOL-PLATE among the matches); n/a here, layer 5 is not in scope. **R-003** redundancy: 2N at utility level needs a utility-grade unit (EP² or Crown); *warn* here because the RFP does not state its redundancy class. **R-004** EPC Power is a pending acquisition: any match relying on it is a supply-timeline risk; it passes, no match depends on EPC.",
        "Statuses are **pass**, **warn**, **fail** and **n/a** (the layer is not in scope). A rule about a fact the RFP does not state is *warn* with \"Clarify before quoting\". Any *fail* makes the criterion *Engineering rules* not met; every *warn* is an open question.",
      ],
      fallback: "The rules appear once the requirements are frozen.",
    },
    {
      id: "decisions-eng-tiers", route: ROUTE, target: "dec-eng-tiers", placement: "top", skipIf: notFrozen, onEnter: openDetails("dec-eng-tiers"),
      title: "Offering type against each unit's default tier",
      body: [
        "Each unit has a default automation tier: Anord Mardix, FPM, JetCool and Cloud are **CTO_AUTOMATE** (catalog, configure), Crown and EP² are **ETO_GUIDED** (Semi-custom by default), EPC is **ETO_EXCEPTION**. A match whose offering type is below the unit's default is flagged, fail-safe: the most conservative reading wins and a person must confirm. The demo flags 5 items, all \"CTO is below CROWN's default ETO_GUIDED: an engineer must confirm this part is genuinely standard\" (`CROWN-ACC` accessories).",
        "Component keywords in a quote can raise the tier at once (for example a bespoke item) or only suggest a lower tier, held until an engineer confirms. Nothing is applied automatically; it is a list for an engineer.",
      ],
      fallback: "The tier check appears once the requirements are frozen.",
    },
    {
      id: "decisions-eng-solver", route: ROUTE, target: "dec-eng-solver", placement: "top", skipIf: notFrozen,
      title: "Low-voltage solver",
      body: [
        "For low-voltage distribution RFPs (layers 3 and 4) the solver does the power arithmetic with every step and its reference: usable UPS capacity after continuous-load derating, real power at the assumed power factor, capacity per rack, derated capacity per branch circuit, circuits per rack; it warns when branch circuits fall short of the UPS or give no A/B redundancy.",
        "Refusing is a first-class result. For Syracuse it is **not solvable**: \"Medium-voltage equipment (`REQ-0001-0887`) needs protection coordination and an arc-flash study, not arithmetic.\" It also refuses when the inputs (UPS kVA, rack count) are not stated: it never assumes values. The hyperscale sample opportunity shows a solved case.",
      ],
      fallback: "The solver appears once the requirements are frozen.",
    },
    {
      id: "decisions-portfolio", route: ROUTE, target: "dec-portfolio", placement: "top", skipIf: notFrozen,
      title: "Bid and portfolio checks",
      body: [
        "Two checks ported from the v1.1 demo onto real data: **deviations** of the RFP's data sheet from the standard ratings of the products offered, and **workload** of each unit across every opportunity in Layer 0 against its capacity. Both standards and capacities are **placeholders** (portfolio.json) to be confirmed with each unit; the notes under each table say so.",
      ],
      fallback: "The portfolio checks appear once the requirements are frozen.",
    },
    {
      id: "decisions-deviations", route: ROUTE, target: "dec-deviations", placement: "top", skipIf: notFrozen,
      title: "Deviations from the standard product",
      body: [
        "The RFP's own data sheet is read from the ruled tables of the layout (label, value, unit) and compared with the standard ratings of each matched product that has them. A value above the standard (for frequency: different from it) is a deviation: **high** for voltage, current and frequency, **medium** for impulse level and momentary rating. Each row cites its source, for example **CROWN-ARMV, Rated continuous current, RFP asks 2000/1200 A rms, standard 600 A, high, p. 74 data sheet row 8**; 5 ratings were checked for the demo.",
        "A high or medium deviation makes the criterion *Deviations from the standard product* not met: it says the customer asks for more than the catalog product, so engineering or a different product is needed. Reading a number from a data-sheet cell is value parsing; it does not create requirements.",
      ],
      fallback: "The deviations table appears once the requirements are frozen.",
    },
    {
      id: "decisions-workload", route: ROUTE, target: "dec-workload", placement: "top", skipIf: notFrozen,
      title: "Workload across opportunities",
      body: [
        "Per unit: open work on this opportunity (what dispatch would create, or has created), open work elsewhere with the competing opportunity IDs, the total and the placeholder capacity (Crown 150, EP² 60, Anord Mardix 100, FPM 100, JetCool 80, Cloud 80, bid desk 400). An *over* badge appears when the total exceeds capacity, and the criterion *Capacity and portfolio conflicts* is then not met.",
        "Open work means assigned, submitted or returned items; validated and withdrawn ones are done. The demo shows BID 249/400 (also in OPP-0002), CROWN 95/150, EP2 7/60.",
      ],
      fallback: "The workload table appears once the requirements are frozen.",
    },
    {
      id: "decisions-participation", route: ROUTE, target: "dec-participation", placement: "top",
      title: "1. Which business units take part?",
      body: [
        "The first decision: which units will be asked to answer. It is recorded with the evidence pack, your name (the *Acting as* person) and a rationale, and the latest record wins. Once recorded, the card header shows *Recorded by <person>: CROWN, EP2* and the rationale with its own *Send to knowledge base* link.",
        "Participation decides who receives work at dispatch: a requirement matched to a unit that does not take part falls to the bid desk instead. It can be recorded again later; the next dispatch applies the change.",
      ],
    },
    {
      id: "decisions-units", route: ROUTE, target: "dec-units", placement: "top",
      title: "The unit checkboxes",
      body: [
        "One checkbox per **active** business unit: Electrical Power Products (EP²), Crown Technical Systems, Anord Mardix, Flex Power Modules, JetCool, Cloud (in-house). EPC Power is pending and not offered. The boxes are pre-ticked from the suggested units (Crown and EP² for Syracuse) or from the last recorded participation.",
        "At least one unit is required; the API refuses an empty or inactive selection. Ticking a unit that has no match gives it nothing at dispatch (there is nothing to send); unticking a matched unit sends its requirements to the bid desk.",
      ],
    },
    {
      id: "decisions-part-rationale", route: ROUTE, target: "dec-part-rationale", placement: "top",
      title: "Participation rationale",
      body: [
        "A free-text reason for the record. Keep it short and factual; it is shown on this card, stored with the decision and can be sent to the knowledge base as a reusable precedent (\"for switchgear RFPs of this kind, Crown leads and EP² supplies protection panels\").",
      ],
      example: {
        label: "Fill an example rationale",
        apply: (ctx) => setValue(input(ctx, "dec-participation", "rationale"),
          "Crown Technical Systems leads the 15 kV metal-clad switchgear; EP² supplies the relay and protection panels. No other unit is in scope."),
      },
    },
    {
      id: "decisions-part-record", route: ROUTE, target: "dec-part-record", placement: "top", kind: "action",
      title: "Record the participation",
      body: [
        "Click **Record participation**. A *Recording…* indicator shows briefly, a toast confirms *Participation recorded.* and the card header shows who recorded it and which units. The opportunity status does not change yet: that happens with go/no-go.",
      ],
      instruction: "Click Record participation.",
      done: present("dec-part-recorded"),
      skipIf: statusIn(...DECIDED),
      fallback: "The Record participation button is at the bottom of card 1.",
    },
    {
      id: "decisions-gonogo", route: ROUTE, target: "dec-gonogo", placement: "top",
      title: "2. Go / no-go",
      body: [
        "The second decision. The card shows, when the requirements are frozen, Layer 0's **summary**: an advice line, a table of how the requirements are satisfied, a per-requirement list, and a criteria table where you record your own judgement. Under it, a rationale and the **Go** and **No-go** buttons.",
        "Recording go or no-go sets the opportunity status (*go* or *no-go*), stores the summary as shown with the decision and, after a go, reveals card 3 for dispatch. A later decision can overrule an earlier one; the latest counts.",
      ],
    },
    {
      id: "decisions-advice", route: ROUTE, target: "dec-advice", placement: "bottom", skipIf: notFrozen,
      title: "The advice line",
      body: [
        "\"Advice from Layer 0: 6 of 9 assessable criteria met; 3 cannot be assessed yet (data not available). **A person decides.**\" That is the whole of Layer 0's opinion: a count of criteria it could assess, never a recommendation to bid or not. The three it cannot assess (cost against budget, delivery against the RFP schedule, competitor information) wait for data the PoC does not have.",
      ],
      fallback: "The advice line appears once the requirements are frozen.",
    },
    {
      id: "decisions-by-category", route: ROUTE, target: "dec-by-category", placement: "top", skipIf: notFrozen,
      title: "How the requirements are satisfied",
      body: [
        "Per category, how many requirements are **fully**, **partly** or **not** satisfied, and how many go to the **bid desk**. Where a unit has answered, its compliance wins (met = fully, partial = partly, not met or exception = not; with several units the weakest answer counts). Otherwise the level is estimated from the match: CTO = fully, Semi-custom and ETO = partly, no match = not, no units = bid desk.",
        "For the demo: technical 7 fully, 94 partly, 45 bid desk; compliance 2 partly, 64 bid desk; every other category entirely bid desk. **Coverage** is the share of product requirements fully or partly satisfied: 100% of 103 here, against a placeholder threshold of 80%.",
      ],
      fallback: "The table appears once the requirements are frozen.",
    },
    {
      id: "decisions-per-req", route: ROUTE, target: "dec-per-req", placement: "top", skipIf: notFrozen, onEnter: openDetails("dec-per-req"),
      title: "Per requirement",
      body: [
        "Expand the list to see every frozen requirement with its level, its basis (*validated answer*, *answer, not yet validated*, *match* or *no match*) and the units involved. Each ID links to the Traceability page with that requirement selected, so an estimate can be checked against the RFP page in one click.",
      ],
      fallback: "The per-requirement list appears once the requirements are frozen.",
    },
    {
      id: "decisions-criteria", route: ROUTE, target: "dec-criteria", placement: "top", skipIf: notFrozen,
      title: "Criteria: Layer 0's assessment and your judgement",
      body: [
        "Twelve criteria from go_no_go.json, each with the question it answers. **Layer 0's assessment** is computed from the evidence: *met* or *not met* with the detail (for example *Open questions*: \"Rule warnings: R-003; unanchored requirements: 32\", *Matches reviewed*: \"103 product match(es) not yet accepted or changed by a person\", *Deviations*: the 2000/1200 A vs 600 A row). Three are *not known*: data not yet available.",
        "**Your judgement** is a select per criterion (met, not met, not known), pre-set to Layer 0's assessment, plus an optional note. You may disagree with any assessment; what you choose is stored with the decision, and the recorded line later shows \"Criteria judged: n met, n not met, n not known\". Thresholds (80% coverage, capacities, standard ratings) are placeholders to be agreed with the bid manager.",
      ],
      fallback: "The criteria table appears once the requirements are frozen.",
    },
    {
      id: "decisions-gng-rationale", route: ROUTE, target: "dec-gng-rationale", placement: "top",
      title: "Go/no-go rationale",
      body: [
        "The reason for the decision, in your words; it is shown under the card header once recorded and can be sent to the knowledge base. The example also marks *Open questions* as not met with a note, which is how you record a reservation without blocking the bid.",
      ],
      example: {
        label: "Fill an example rationale and a note",
        apply: (ctx) => {
          setValue(input(ctx, "dec-gonogo", "rationale"),
            "In scope for Crown and EP². Clarify the redundancy class (R-003) and the 2000 A continuous-current rating before quoting.");
          setValue(input(ctx, "dec-gonogo", "crit-open_questions"), "not_met");
          setValue(input(ctx, "dec-gonogo", "note-open_questions"), "R-003 and 32 unanchored items to be checked with the customer.");
        },
      },
    },
    {
      id: "decisions-no-go", route: ROUTE, target: "dec-no-go", placement: "top",
      title: "No-go and its confirmation",
      body: [
        "**No-go** records the opposite decision. Because it ends the bid, a confirmation dialog asks first: *Record no-go?* with the message \"The opportunity is marked no-go. Nothing is sent to the units; a later go decision can still overrule it.\" Confirming sets the status to *no-go*; the dispatch card is not shown. Esc or Cancel keeps everything as it was.",
        "Both buttons are disabled until the requirements are frozen (\"Freeze the requirements first.\") and while another action is running, so a double click cannot record two decisions.",
      ],
    },
    {
      id: "decisions-go", route: ROUTE, target: "dec-go", placement: "top", kind: "action",
      title: "Record go",
      body: [
        "Click **Go**. The decision is stored with the evidence pack, the summary as shown, your criteria judgements and the participating units (taken from the latest participation record). A toast says *Decision recorded: go.*, the status badge in the header turns to *go*, the stepper ticks Traceability and Bid decision, and card 3 appears below.",
      ],
      instruction: "Click Go.",
      done: present("dec-gng-recorded"),
      skipIf: decidedOrNotFrozen,
      fallback: "The Go button is under the criteria table; it is enabled once the requirements are frozen.",
    },
    {
      id: "decisions-gng-recorded", route: ROUTE, target: "dec-gng-recorded", placement: "bottom",
      title: "The recorded decision",
      body: [
        "The card header now shows **Decision go by <person>**, the rationale under it with *Criteria judged: n met, n not met, n not known* when judgements were recorded, and a *Send to knowledge base* link for the rationale. The demo opportunity was decided by the Bid Manager: \"In scope for the participating units.\"",
        "The summary and the criteria table stay live: they keep following the current matches and answers, while the stored decision keeps the evidence exactly as it was when you decided.",
      ],
      fallback: "No go/no-go decision is recorded yet for this opportunity.",
    },
    {
      id: "decisions-dispatch", route: ROUTE, target: "dec-dispatch", placement: "top",
      title: "3. Send the work to the units",
      body: [
        "Dispatch creates the work packages: for every frozen approved requirement, **one assignment per participating unit it is matched to** (with the unit's first product as the reference), or, when none of its units takes part or it is not a product item, one assignment for the **bid desk**. Each unit's assignments are owned by its design engineer; the bid desk's by the Bid Manager. For the demo that was 348 assignments: Crown 96, EP² 7, bid desk 245.",
        "It is repeatable: after changing matches or participation, dispatch again. New work is sent, work that no longer fits is **withdrawn**, and withdrawn work that fits again is **reopened** with its earlier answer kept for reference. Existing assignments are never duplicated.",
        "Preconditions: frozen requirements and a latest decision of *go*. The opportunity status becomes *dispatched*.",
      ],
      fallback: "The dispatch card appears only after a go decision.",
    },
    {
      id: "decisions-dispatch-run", route: ROUTE, target: "dec-dispatch-button", placement: "top", kind: "action",
      title: "Dispatch the work packages",
      body: [
        "Click **Dispatch work packages to units**. A *Dispatching…* indicator shows while the assignments are written; then a toast reports the result and the header status turns to *dispatched*.",
      ],
      instruction: "Click Dispatch work packages to units and wait for the toast.",
      done: statusIn("dispatched", "consolidating", "submitted"),
      skipIf: statusIn("no_go", "dispatched", "consolidating", "submitted"),
      fallback: "The dispatch button appears only after a go decision.",
    },
    {
      id: "decisions-dispatch-result", route: ROUTE, target: "dec-dispatch", placement: "top",
      title: "What dispatch produced",
      body: [
        "The toast reads **\"N new assignment(s) sent to the units.\"** (348 on a fresh Syracuse opportunity) or, when nothing changed since the last dispatch, *\"Nothing new to send: every unit already has its work.\"* The status badge shows *dispatched*; on the Traceability page the Response column of every row now shows its assignments as *assigned*, and the toolbar counts them per unit (CROWN 0/96 validated, EP2 0/7, BID 0/245).",
        "Next: the units' **Inbox** (chapter 8), where each unit's product manager or design engineer answers their items with a compliance level and text, and the bid manager validates or returns them. Those answers flow back into pane 3 here and into the summary's *fully / partly / not* counts.",
      ],
      fallback: "Dispatch has not run yet on this opportunity.",
    },
  ],
};
export default chapter;
