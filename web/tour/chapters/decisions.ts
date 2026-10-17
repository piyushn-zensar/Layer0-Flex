// Walkthrough chapter 7: Assessment and Bid decision (app/opportunities/[id]/assessment, app/opportunities/[id]/decisions).  Owner: Janvia (J-15).
// Since A-16 / P-32 the participating units, the routing and "Send for assessment" are on the Assessment step, and the Bid
// decision is go / no-go only, taken after the units have assessed the bid. Explain-only: OPP-0001 is already sent to the
// units and has a recorded decision.
import type { TourChapter } from "../types";

const ASM = "/opportunities/{opp}/assessment";
const DEC = "/opportunities/{opp}/decisions";

const chapter: TourChapter = {
  id: "decisions",
  order: 7,
  title: "Assessment and Bid decision",
  summary: "The Assessment step (bid summary, assessment score, open questions, participating units, routing, sending the work, schedule and approvals), then the Bid decision (evidence, engineering checks, criteria, go or no-go).",
  entryRoute: ASM,
  steps: [
    {
      id: "decisions-assessment", route: ASM, target: "asm-summary", placement: "bottom",
      title: "Assessment: the bid at a glance",
      body: [
        "**Assessment** is the third step. It turns the frozen register into a plan: the **bid summary**, what is still open, which units take part, how every requirement is routed, and when the units say they will be done. The go/no-go comes after it, once the units have answered.",
        "The summary counts the 312 requirements by category (technical 148, compliance 66, submission 61, legal 12, schedule 9, commercial 8, staffing 8) and by offering type (ETO 85, CTO 11, Semi-custom 3, none 213), names the major sections of the RFP, and lists the **suggested units** from the matches: Crown 93 and EP² 6.",
      ],
      fallback: "The bid summary is shown once the assessment has loaded.",
    },
    {
      id: "decisions-score", route: ASM, target: "asm-score", placement: "bottom",
      title: "The assessment score: four measures, never a probability",
      body: [
        "The panel under the summary shows four measures: **Domain alignment** (technical requirements matched to a participating unit's catalog product, 99 of 214 here), **Product-evidence coverage** (requirements with reviewed, published product evidence), **Specialist-review progress** (items sent to the units whose answers are validated, 1 of 222) and **Preliminary feasibility**. A measure that has not been assessed says *Not assessed yet* rather than guessing.",
        "It is a count of what is known, not a model's opinion or a probability, and each measure opens the requirements behind it. The **evidence gaps** below list what is missing, for example 115 technical requirements matched to no unit's product and 12 requirements whose source is not verified.",
      ],
      fallback: "The assessment panel is shown once the assessment has loaded.",
    },
    {
      id: "decisions-score-run", route: ASM, target: "asm-score-run", placement: "top",
      title: "Assess with the knowledge base",
      body: [
        "**Assess with the knowledge base** (bid manager) records an **assessment run**: the evidence from the published product catalog and the approved reference documents is retrieved for the bid's requirements, and the run keeps what it used, the catalog version and the reason you gave. Later runs are numbered and earlier ones stay; a run never changes the requirements. Evidence from other bids is never used.",
      ],
      fallback: "The run line and the Assess button are at the bottom of the assessment panel.",
    },
    {
      id: "decisions-open-questions", route: ASM, target: "asm-open-questions", placement: "top",
      title: "Open questions",
      body: [
        "Everything that needs a person before the bid can be trusted: requirements whose **source is not verified** (link them to their lines or dismiss them in pane 2 of Traceability), product requirements that **need an owner** (115), engineering **rule warnings** (R-003, redundancy class not stated) and questions not yet closed. Each row links to the requirement.",
        "A product requirement that no participating unit can take is never lost: assign a unit in Traceability pane 3, or record a **capability gap** with the reason no unit can offer it. The count here feeds the Bid decision.",
      ],
      fallback: "The open questions are listed once the assessment has loaded.",
    },
    {
      id: "decisions-participation", route: ASM, target: "asm-participation", placement: "top",
      title: "1. Which business units take part?",
      body: [
        "The bid manager records the participating units with a rationale; the matcher's suggestion is pre-selected (here Electrical Power Products (EP²) and Crown Technical Systems). The record shows who decided and when. A unit that is not chosen receives no work, and EPC Power is shown as not offered because its acquisition is pending.",
      ],
      fallback: "The participation card is shown once the assessment has loaded.",
    },
    {
      id: "decisions-routing", route: ASM, target: "asm-routing", placement: "top",
      title: "Routing: who answers what",
      body: [
        "The routing card shows where every requirement goes: **124 to units**, **73 to the bid desk**, 0 capability gaps and 115 that need an owner. Open it to see each requirement, its unit and its specialists. The rules are in `workflow.json`, not in code: **technical** items go to the unit's designers / engineers; **schedule, commercial and staffing** items to the unit managers of the participating units; only the high-level, consolidated **submission and legal** items stay with the bid manager.",
      ],
      fallback: "The routing card is shown once the assessment has loaded.",
    },
    {
      id: "decisions-send", route: ASM, target: "asm-send", placement: "top",
      title: "2. Send for assessment",
      body: [
        "**Send for assessment** (bid manager) gives each participating unit its work: one item per requirement, shown in that unit's **My work**. It can be repeated after changing matches or participation: new work is sent and work that no longer fits is withdrawn, with earlier answers kept. Sending is what moves the bid to `dispatched`; the register is already frozen, so there is no Publish step.",
        "Under it, **Progress per unit** counts items, answered and validated: Crown 118 items (2 answered, 1 validated), EP² 31 and the bid desk 73. Until the bid is sent, the Response column in Traceability stays empty.",
      ],
      fallback: "The send card is shown once the assessment has loaded.",
    },
    {
      id: "decisions-schedule", route: ASM, target: "asm-schedule", placement: "top",
      title: "Schedule and approvals",
      body: [
        "Each unit manager gives an **estimated completion date** for the unit in My work. The bid manager sets the RFP **due date** and the consolidation days (a placeholder, 5), and the card shows the **planned submission date** once every unit has a date, with a warning when it falls after the due date. The **high-level compliance** table counts each unit's fully, partially and non-compliant answers.",
        "The bid manager then **approves the schedule** (refused until every participating unit has a date) and **approves the compliance position**. An approval is reopened automatically if a date or the counts change later; the schedule also feeds the *Schedule* criterion of the go/no-go.",
      ],
      fallback: "The schedule card is at the bottom of the Assessment page.",
    },
    {
      id: "decisions-evidence", route: DEC, target: "dec-evidence", placement: "bottom",
      title: "Bid decision: evidence first, then a person decides",
      body: [
        "**Bid decision** is the fifth step, for go or no-go only: once the units have assessed the bid, the bid manager reviews the evidence and their answers and decides. Everything above the decision is advice built live from the register, the matches and the unit answers; the decision is a named person's, recorded with the evidence as it was shown.",
        "**Evidence** repeats the requirement counts, the offering mix, the suggested units, the requirements whose source is not verified and the product matches nobody has accepted or changed yet (99 on Syracuse).",
      ],
      fallback: "The evidence card is shown once the page has loaded.",
    },
    {
      id: "decisions-engineering", route: DEC, target: "dec-eng-checks", placement: "top",
      title: "Engineering checks",
      body: [
        "Ported from the earlier prototype and **illustrative until confirmed with engineering**: which of the six layers the RFP covers (Utility / Facility Electrical and Power Distribution here, from keyword hits in the requirements), whether the suggested units sit outside those layers, four rules (R-001 voltage architecture pass, R-002 cooling n/a, **R-003 redundancy class not stated: warn**, R-004 no dependency on the pending acquisition), offering types below a unit's default tier (11 need an engineer's confirmation) and a low-voltage solver that reports *not solvable* for medium-voltage equipment rather than guessing.",
      ],
      fallback: "The engineering checks are shown once the page has loaded.",
    },
    {
      id: "decisions-portfolio", route: DEC, target: "dec-portfolio", placement: "top",
      title: "Bid and portfolio checks",
      body: [
        "Two more pieces of evidence, never decisions. **Deviations from the standard product** compares the RFP's own data sheet with the standard ratings of the matched products: the Syracuse data sheet asks for 2000/1200 A continuous current where the standard Crown product is rated 600 A, a *high* deviation (page 74). **Workload across bids** compares each unit's open work, here and on other bids, with a placeholder capacity. Standard ratings and capacities are placeholders marked as such.",
      ],
      fallback: "The bid and portfolio checks are shown once the page has loaded.",
    },
    {
      id: "decisions-criteria", route: DEC, target: "dec-criteria", placement: "top",
      title: "Criteria: Layer 0's assessment and your judgement",
      body: [
        "Ten criteria, each with the question it answers: assessment complete, compliance, schedule, scope fit, every requirement routed, engineering rules, open questions, no pending-acquisition dependency, deviations from the standard product, capacity. **Layer 0's assessment** is computed from the evidence (*met*, *not met* or *not known*, with the detail); **Your judgement** is a select per criterion, pre-set to Layer 0's assessment, with an optional note. You may disagree with any of them.",
        "The line above summarises it as advice (*5 of 9 assessable criteria met; 1 not known yet. The bid manager decides.*). Advice never decides: the criteria you judged are stored with the decision.",
      ],
      fallback: "The criteria table is shown once the page has loaded.",
    },
    {
      id: "decisions-gonogo", route: DEC, target: "dec-gonogo", placement: "top",
      title: "Go / no-go",
      body: [
        "The bid manager writes a **rationale** and presses **Go** or **No-go**. The decision is stored with the evidence as shown, the criteria judgements and the participating units, and the card header shows who decided and when (here *Decision go by Bid Manager*). **No-go** ends the bid and asks for confirmation first; a later **Go** resumes it. If the units have not finished, a warning says so, but the decision can still be recorded.",
        "A decision rationale carries **Nominate as a reviewed example**, like a requirement or a validated answer, so a good rationale can be reused after review in Knowledge review.",
      ],
      fallback: "The Go / no-go card is shown once the page has loaded.",
    },
  ],
};
export default chapter;
