// Walkthrough chapter 7: Assessment and Bid decision (app/opportunities/[id]/assessment, app/opportunities/[id]/decisions).  Owner: Janvia (J-15).
// Since A-16 / P-32 the participating units, the routing and "Send for assessment" are on the Assessment step, and the Bid
// decision is go / no-go only, taken after the units have assessed the bid. P-44 (C-41): the Assessment Summary is the bid
// manager's first stage (no technical approval); the compliance position is approved on the Bid decision. Explain-only:
// OPP-0001 is already sent to the units and has no go/no-go yet (seed_demo, iteration 4), so the Assessment Summary forms
// are open; once a go/no-go is recorded they fold behind "Change participation…", "Send again…" and "Change…" (ChangeGate).
import type { TourChapter } from "../types";

const ASM = "/opportunities/{opp}/assessment";
const DEC = "/opportunities/{opp}/decisions";

const chapter: TourChapter = {
  id: "decisions",
  order: 7,
  title: "Assessment Summary and Bid decision",
  summary: "The Assessment Summary step, the bid manager's first stage (business relevance: bid summary, three measures and open questions; participating units, routing, sending the work, the teams' delivery feasibility), then the Bid decision (evidence, engineering checks, compliance position, the four reviewed outcomes, criteria, go or no-go).",
  entryRoute: ASM,
  steps: [
    {
      id: "decisions-assessment", route: ASM, target: "asm-summary", placement: "bottom",
      title: "Assessment Summary: the bid at a glance",
      body: [
        "**Assessment Summary** is the third step and the bid manager's first stage: is the bid relevant to the business, which units take part, and how is the work routed to their teams? It turns the frozen register into a plan: the **bid summary**, three measures, what is still open, the participating units, the routing, sending the work, and the teams' delivery feasibility. The bid manager approves no technical requirement here; the go/no-go comes later, once the units have answered.",
        "The summary counts the 312 requirements by category (Technical 148, Compliance 66, Submission 61, Legal 12, Schedule 9, Commercial 8, Staffing 8) and by type of offer (ETO 85, CTO 11, Semi-custom 3, Bid desk 213), and lists the **suggested units** from the matches: Crown 93 and EP² 6. Each count opens Requirement Traceability filtered to it.",
      ],
      fallback: "The bid summary is shown once the Assessment Summary has loaded.",
    },
    {
      id: "decisions-score", route: ASM, target: "asm-score", placement: "bottom",
      title: "The Assessment Summary: three measures, never a probability",
      body: [
        "The panel under the summary shows **three measures**, kept separate on purpose. **Technical Requirement Matching** is system-generated: of the technical requirements, how many the system's first proposal matched to a participating unit's solution. **Reviewed by design engineers**: of the same technical requirements, how many the unit's designer / engineer has answered and the unit manager validated, split into *confirmed* (the proposed solution, answered Compliant) and *corrected* (another solution named, or an answer other than Compliant). **Specialist review progress**: of the requirements sent to the units, how many have all their answers validated (the bid desk's own items are not counted).",
        "The first two count **technical requirements only**: the **standards and regulatory items** are listed beside them and are not in the percentage, and legal, commercial, schedule and submission items never count. Each measure is a count of what is known, never a model's opinion or a probability, and opens the requirements behind it. The **evidence gaps** below list what is missing, for example technical requirements with no unit's proposed solution and requirements whose text needs a source check.",
      ],
      fallback: "The Assessment Summary panel is shown once the assessment has loaded.",
    },
    {
      id: "decisions-score-run", route: ASM, target: "asm-score-run", placement: "top",
      title: "Assess with the knowledge base",
      body: [
        "**Assess with the knowledge base** (bid manager, optional) records an **assessment run**: the evidence from the published product catalog and the approved reference documents is retrieved for the bid's requirements, and the run keeps what it used, the catalog version and the reason you gave. Later runs are numbered and earlier ones stay; a run never changes the requirements. Evidence from other bids is never used. The three measures do not depend on a run; once a bid is decided without one, the line says so and the button is no longer offered.",
      ],
      fallback: "The run line and the Assess button are at the bottom of the Assessment Summary panel.",
    },
    {
      id: "decisions-open-questions", route: ASM, target: "asm-open-questions", placement: "top",
      title: "Open questions",
      body: [
        "Everything that needs a person before the bid can be trusted: requirements that **need a source check** (link them to their lines or dismiss them on the Needs a source check tab in pane 2 of Traceability), product requirements that **need an owner** (115), engineering **rule warnings** (R-003, redundancy class not stated) and questions not yet closed. Each row links to the requirement.",
        "A product requirement that no participating unit can take is never lost: it stays under **Needs an owner** until the bid manager routes it or records a capability gap (next step). The count here feeds the Bid decision.",
      ],
      fallback: "The open questions are listed once the Assessment Summary has loaded.",
    },
    {
      id: "decisions-capability-gap", route: ASM, target: "asm-needs-owner", placement: "top",
      title: "Needs an owner, or a capability gap",
      body: [
        "Each product requirement no participating unit holds is listed here and is not sent. The bid manager has three ways out: route it to a unit under Routing below, let the matched unit take part, or **Record capability gap** with the reason no unit can offer it.",
        "A capability gap is stated honestly, not hidden: the requirement goes to the bid desk and reads **Capability gap: not offered** in pane 3 of Traceability, in the Bid decision's per-requirement list and in the response outline. In the compliance matrix it is the bid desk's **Non-compliant** answer with the reason, and it counts as Non-compliant in the reviewed compliance outcomes on the Bid decision.",
      ],
      fallback: "Needs an owner is listed under Open questions only while some product requirement has no participating unit.",
    },
    {
      id: "decisions-participation", route: ASM, target: "asm-participation", placement: "top",
      title: "1. Which business units take part?",
      body: [
        "The bid manager records the participating units with a rationale; the matcher's suggestion is pre-selected (here Electrical Power Products (EP²) and Crown Technical Systems). The record shows who decided and when. A unit that is not chosen receives no work, and EPC Power is shown as not offered because its acquisition is pending.",
        "Once the go/no-go is recorded, this form and the send button fold away and the recorded state shows: the bid manager reopens them with **Change participation…** and **Send again…**, and a person who cannot act sees only what was recorded.",
      ],
      fallback: "The participation card is shown once the Assessment Summary has loaded.",
    },
    {
      id: "decisions-routing", route: ASM, target: "asm-routing", placement: "top",
      title: "2. Route requirements to teams",
      body: [
        "The routing card shows where every requirement goes: **124 to units**, **73 to the bid desk**, 0 capability gaps and 115 that need an owner. Open it to see each requirement, its unit and its specialists. The rules are in `workflow.json`, not in code: **technical** items go to the unit's designers / engineers; **schedule, commercial and staffing** items to the unit managers of the participating units; only the high-level, consolidated **submission and legal** items stay with the bid manager.",
        "The bid manager changes only the **unit** of a requirement here (**Change unit**). The solution and the technical answer are for the unit's designers / engineers, who accept or correct the match in Traceability; the bid manager approves no technical requirement at this stage.",
      ],
      fallback: "The routing card is shown once the Assessment Summary has loaded.",
    },
    {
      id: "decisions-send", route: ASM, target: "asm-send", placement: "top",
      title: "3. Send for assessment",
      body: [
        "**Send for assessment** (bid manager) gives each participating unit its work: one item per requirement, shown in that unit's **My work**. It can be repeated after changing matches, routing or participation: new work is sent and work that no longer fits is withdrawn, with earlier answers kept. Sending is what moves the bid to **Sent to units**; the register is already frozen, so there is no Publish step.",
        "Under it, **Progress per unit** counts items, answered and validated: Crown 118 items (2 answered, 1 validated), EP² 31 and the bid desk 73. Until the bid is sent, the Response column in Traceability stays empty.",
      ],
      fallback: "The send card is shown once the Assessment Summary has loaded.",
    },
    {
      id: "decisions-schedule", route: ASM, target: "asm-schedule", placement: "top",
      title: "Delivery feasibility from the teams",
      body: [
        "Each unit manager gives the unit's **estimate** in My work and reports five **delivery factors**: people, skills, manufacturing capacity, materials and cost, each *no constraint* or a *constraint* with a note. Technical feasibility is the designers' / engineers' answers. The bid manager sets only the RFP **due date** and the consolidation days (a placeholder, 5); the card shows the latest estimate and the **planned submission date**, with a warning when it falls after the due date.",
        "The bid manager then **accepts the teams' estimates** (refused until every participating unit has its estimate and all five factors) and does not set the units' dates. The acceptance reopens automatically when an estimate or a factor changes; the estimates and the constraints feed the schedule criterion of the go/no-go. There is no resource plan. Once the go/no-go is recorded, the accepted estimates and the settings show as recorded and the bid manager reopens them with **Change…**. The compliance position is not approved here: it is on the Bid decision, once the units have answered.",
      ],
      fallback: "The delivery feasibility card is at the bottom of the Assessment Summary page.",
    },
    {
      id: "decisions-evidence", route: DEC, target: "dec-evidence", placement: "bottom",
      title: "Bid decision: evidence first, then a person decides",
      body: [
        "**Bid decision** is the fifth step, for go or no-go only: once the units have assessed the bid, the bid manager reviews the evidence and their answers and decides. Everything above the decision is advice built live from the register, the matches and the unit answers; the decision is a named person's, recorded with the evidence as it was shown.",
        "**Evidence** repeats the requirement counts, the types of offer, the suggested units, the requirements that need a source check and the technical matches the units' designers / engineers have not confirmed yet (99 on Syracuse).",
      ],
      fallback: "The evidence card is shown once the page has loaded.",
    },
    {
      id: "decisions-engineering", route: DEC, target: "dec-eng-checks", placement: "top",
      title: "Engineering checks",
      body: [
        "Ported from the earlier prototype and **illustrative until confirmed with engineering**: which of the six layers the RFP covers (Utility / Facility Electrical and Power Distribution here, from keyword hits in the requirements), whether the suggested units sit outside those layers, four rules (R-001 voltage architecture pass, R-002 cooling n/a, **R-003 redundancy class not stated: warn**, R-004 no dependency on the pending acquisition), types of offer below a unit's usual type of offer (11 need an engineer's confirmation) and a low-voltage solver that reports *not solvable* for medium-voltage equipment rather than guessing.",
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
      id: "decisions-compliance", route: DEC, target: "dec-compliance", placement: "top",
      title: "Compliance position",
      body: [
        "Once at least one unit answer is validated, this card counts each unit's validated answers by outcome (Compliant, Partially compliant, Compliant with changes, Non-compliant) and those still open; the bid desk row also holds the capability gaps. The bid manager presses **Approve compliance position** here, after the units have answered, not on the Assessment Summary; each unit validates its own answers. The approval reopens automatically when the counts change.",
      ],
      fallback: "The compliance position appears once a unit answer has been validated.",
    },
    {
      id: "decisions-outcomes", route: DEC, target: "dec-outcomes", placement: "top",
      title: "Reviewed compliance outcomes: four answers",
      body: [
        "A unit answers each requirement with one of four outcomes. **Compliant**: met as asked. **Partially compliant**: met in part; a reason is required. **Compliant with changes**: met with a deviation from the requested specification; a reason and the **proposed change** are both required. **Non-compliant**: cannot be met; a reason is required.",
        "This line counts the product requirements with validated answers, each once by its weakest answer (a capability gap counts as Non-compliant). Each count opens to its requirement IDs, linked to Traceability, and the same four counts feed the compliance criterion below.",
      ],
      fallback: "The reviewed compliance outcomes are listed in the Go / no-go card once the page has loaded.",
    },
    {
      id: "decisions-criteria", route: DEC, target: "dec-criteria", placement: "top",
      title: "Criteria: Layer 0's assessment and your judgement",
      body: [
        "Ten criteria, each with the question it answers: assessment complete, compliance, schedule, scope fit, every requirement routed, engineering rules, open questions, no pending-acquisition dependency, deviations from the standard product, capacity. **Layer 0's assessment** is computed from the evidence (*met*, *not met* or *not known*, with the detail); **Your judgement** is a select per criterion, pre-set to Layer 0's assessment, with an optional note. You may disagree with any of them.",
        "The line above summarises it as advice (for example *5 of 9 assessable criteria met; 1 not known yet. The bid manager decides.*). Advice never decides: the criteria you judged are stored with the decision. The **compliance** criterion counts the four reviewed outcomes separately, and the **schedule** criterion reads the teams' accepted estimates and the constraints they reported.",
      ],
      fallback: "The criteria table is shown once the page has loaded.",
    },
    {
      id: "decisions-gonogo", route: DEC, target: "dec-gonogo", placement: "top",
      title: "Go / no-go",
      body: [
        "The bid manager writes a **rationale** and presses **Go** or **No-go**. The decision is stored with the evidence as shown, the criteria judgements and the participating units; the card header then shows who decided, the criteria become read-only with **Change decision**, and the bid reads **Go recorded** (or **No-go recorded**). On Syracuse no decision is recorded yet, because the units are still answering; RC-1 (OPP-0003) shows a recorded go. **No-go** ends the bid and asks for confirmation first; a later **Go** resumes it. If the units have not finished, a warning says so, but the decision can still be recorded.",
        "A decision rationale carries **Nominate as a reviewed example**, like a requirement or a validated answer, so a good rationale can be reused after review in Knowledge review.",
      ],
      fallback: "The Go / no-go card is shown once the page has loaded.",
    },
  ],
};
export default chapter;
