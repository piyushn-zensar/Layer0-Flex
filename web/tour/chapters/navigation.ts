// Walkthrough chapter 3: Navigation, roles and the workflow stepper.  Owner: tour engine.
// The first part spotlights the top bar (on whatever page the person is on); the second part opens the walkthrough
// opportunity ({opp}: the one created in chapter 4, else OPP-0001) to explain the opportunity header and stepper.
import type { TourChapter } from "../types";

const chapter: TourChapter = {
  id: "navigation",
  order: 3,
  title: "Navigation, roles and the workflow stepper",
  summary: "The top bar, the four destinations, New opportunity, the acting person and what each role may do; then the opportunity header, its status badge and the six-step stepper.",
  entryRoute: "/portfolio",
  steps: [
    {
      id: "navigation-brand",
      title: "The top bar is the same on every screen",
      target: "shell-brand",
      placement: "bottom",
      body: [
        "The dark bar stays at the top of every page. From left to right: the **Layer 0** mark (a link back to the Opportunities list), the four main destinations, and on the right **New opportunity**, the **Acting as** picker and the **Walkthrough** button you are using now.",
        "There is no sign-in in this proof of concept: the person acting is chosen in the bar and sent with every request, which is why the picker sits where a user menu would be.",
      ],
      fallback: "The top bar is above the page content; this step describes its left end.",
    },
    {
      id: "navigation-nav",
      title: "Four destinations",
      target: "shell-nav",
      placement: "bottom",
      body: [
        "**Opportunities** is the portfolio: every bid with its customer, status and progress; it is also where you land from an opportunity's breadcrumb. **My work** is the inbox of the business units: each unit's work packages, the checklist of requirements it must answer, and the bid manager's validation of those answers.",
        "**Product catalog** lists the business units and the products the matcher can choose from (Crown switchgear, Anord Mardix busway, EP² control buildings and so on), with their offering type: configure-to-order, semi-custom or engineered-to-order. **Knowledge base** is the curator's queue: requirements, validated answers and decision rationales that people send there for reuse in later bids, approved or rejected by the curator.",
        "The highlighted link shows where you are. Inside an opportunity, **Opportunities** stays highlighted because every opportunity page belongs to the portfolio.",
      ],
      fallback: "The four links sit in the top bar next to the Layer 0 mark.",
    },
    {
      id: "navigation-new",
      title: "New opportunity",
      target: "shell-new-opportunity",
      placement: "bottom",
      body: [
        "Every bid starts here. The form asks for a **title**, the **customer** and the **customer type** (for example public sector, hyperscaler or utility; the type is only a label in this proof of concept). Saving creates the opportunity with the next free id (`OPP-0001`, `OPP-0002`, …), status `new`, and opens its RFP page so the document can be uploaded.",
        "Chapter 4 uses this button to create the walkthrough opportunity. Creating one is cheap and never touches the others, so it is also the way to try the app on a second RFP later.",
      ],
      fallback: "The New opportunity button is on the right of the top bar.",
    },
    {
      id: "navigation-actor",
      title: "Acting as: the three roles",
      target: "shell-actor",
      placement: "bottom",
      body: [
        "This picker says **who is acting**. The name is kept in a cookie, sent as the `X-Actor` header with every request and recorded on everything that person does. Changing it reloads the page so every screen re-fetches as that person. The list is the **Bid Manager** plus, for each business unit, its **Product Manager** and **Design Engineer** (for example `EP² Product Manager`, `Crown Design Engineer`); the names are role placeholders until real people are named.",
        "What each role may do is enforced by the server: only a unit's product manager or design engineer answers **that unit's** work-package items; only the Bid Manager **validates or returns** answers, **applies or discards** a change set and **approves knowledge** (the curator role, in the PoC the Bid Manager). Uploading documents, approving and freezing requirements, recording the bid decision, dispatching work, deciding and confirming change items are open to anyone in this PoC, with the actor's name on the audit record.",
        "Stay as **Bid Manager** for most of the walkthrough; the inbox chapter asks you to switch to a unit's product manager to answer a work package, and back again to validate.",
      ],
      fallback: "The Acting as picker is in the right half of the top bar.",
    },
    {
      id: "navigation-help",
      title: "The Walkthrough button",
      target: "shell-help",
      placement: "bottom",
      body: [
        "This button reopens the walkthrough at any time. It shows **Resume** when you left part-way (Esc, Exit, or a closed browser tab), **Restart** to begin again from chapter 1, and the **chapter list** with ticks for the chapters you have finished, so you can jump to one screen.",
        "Progress is stored in this browser for the current server session; after the development server restarts the welcome dialog is offered once more.",
      ],
      fallback: "The Walkthrough button is at the far right of the top bar.",
    },
    {
      id: "navigation-opp-head",
      title: "Inside an opportunity: the header",
      route: "/opportunities/{opp}",
      target: "opp-head",
      placement: "bottom",
      body: [
        "Every page of an opportunity shares this header. The **breadcrumb** goes back to Opportunities and shows the id; the **title** is the one given at creation (for the seeded demo: “Switchgear procurement (RFP 2023-20)”); the **status badge** next to it is the opportunity's position in the workflow; the **stepper** below links the five step pages, and **Changes** on the right opens the addenda page.",
        "The header refreshes itself: every five seconds, on every step change, and immediately when a page changes the status (freeze, go/no-go, dispatch, apply a change set), so the badge and the ticks are always current.",
      ],
      fallback: "Open an opportunity from the Opportunities list to see this header above its pages.",
    },
    {
      id: "navigation-status",
      title: "The status badge",
      route: "/opportunities/{opp}",
      target: "opp-status",
      placement: "bottom",
      body: [
        "The badge shows one of nine statuses, in workflow order: `new` (just created), `reading` (an RFP is uploaded and being read), `review` (line items proposed, a person is checking them), `frozen` (the requirement baseline is fixed), `go` or `no-go` (the bid decision), `dispatched` (work packages sent to the units), `consolidating` (the bid manager is assembling answers) and `submitted` (the final response went out).",
        "The colour follows the tone used across the app: grey for inactive, amber for waiting on someone, blue for handed over, green for done and red for a stop (`no-go`). The status **only moves forward**; a repeated action (re-reading a draft, deciding go again after dispatch) never sends it back. `no-go` is the exception: it can stop a bid at any point before submission, and a later `go` resumes at the status the stop replaced.",
        "The seeded demo `OPP-0001` sits at `dispatched`; a freshly created opportunity shows `new` until its RFP is read. In the current code the reader answers in one call, so `reading` is in the vocabulary but you will not see it: `new` goes straight to `review`.",
      ],
      fallback: "The status badge appears next to the opportunity title once the opportunity has loaded.",
    },
    {
      id: "navigation-stepper",
      title: "The stepper: where the bid stands",
      route: "/opportunities/{opp}",
      target: "stepper",
      placement: "bottom",
      body: [
        "The five entries are the step pages of this opportunity. The **current** page is underlined in blue with a blue number; a step shows a green **tick** once the status has moved past it: RFP from `reading`, Requirements from `frozen`, Traceability and Bid decision from `go`, Final response only at `submitted`. Ticks are derived from the status, not from visiting a page.",
        "You can open any step at any time, in any order: the pages themselves say what is still missing (for example Traceability lists the frozen requirements only, and the inbox shows nothing until work is dispatched). The walkthrough follows the natural order.",
      ],
      fallback: "The stepper is the row of numbered links under the opportunity title.",
    },
    {
      id: "navigation-step-rfp",
      title: "Steps 1 and 2: RFP and Requirements",
      route: "/opportunities/{opp}",
      target: "step-rfp",
      placement: "bottom",
      body: [
        "**1 RFP** is the document page: upload the main RFP (or load a built-in sample), see its ingestion status and page count, search the text, upload addenda and other documents, and run the **reader agent**, which turns the pages into line items. For the Syracuse RFP that is about 810 line items from 101 pages, each with its exact quote, page and lines.",
        "**2 Requirements** is the review table: every proposed line item against its source passage, grouped into requirements by the grouping agent. A person approves, rejects, edits the short text, merges or splits, adds a missed requirement by page and lines, and finally **freezes** the baseline. The matcher only works on the frozen set, so nothing downstream exists before this freeze.",
      ],
      fallback: "The first two stepper entries are RFP and Requirements.",
    },
    {
      id: "navigation-step-trace",
      title: "Steps 3 and 4: Traceability and Bid decision",
      route: "/opportunities/{opp}",
      target: "step-trace",
      placement: "bottom",
      body: [
        "**3 Traceability** is the three-pane view: the RFP text with the anchored lines highlighted, the requirement, and the matcher's proposal (product, business unit, offering type, confidence). It is the proof that every requirement traces back to a page and lines and forward to a unit and product; the heat of the colours tells you where engineering effort concentrates.",
        "**4 Bid decision** records participation per business unit and the go/no-go with its rationale and criteria, as a named person's decision, and then **dispatches** one work package per participating unit. Dispatch moves the status to `dispatched` and fills the units' inboxes.",
      ],
      fallback: "The third and fourth stepper entries are Traceability and Bid decision.",
    },
    {
      id: "navigation-step-final",
      title: "Step 5: Final response",
      route: "/opportunities/{opp}",
      target: "step-consolidation",
      placement: "bottom",
      body: [
        "**5 Final response** is the bid manager's consolidation: every requirement with the unit's answer (compliance met, partial, not met or exception, the response text and the product offered), what is still pending, what the engineering rules flagged, and the outline of the response document. Validated answers come from the inbox; the bid manager cannot finish while answers are missing.",
        "Its tick appears only at `submitted`, the last status.",
      ],
      fallback: "The last stepper entry is Final response.",
    },
    {
      id: "navigation-changes",
      title: "Changes: addenda after the freeze",
      route: "/opportunities/{opp}",
      target: "step-changes",
      placement: "left",
      body: [
        "**Changes** is not a step but a side track available once the baseline is frozen. An addendum uploaded here is compared with the current baseline by the change agent, which proposes a **change set**: requirements added, modified, removed or unchanged, each with its evidence. A person confirms each item; the Bid Manager then **applies** the set, which creates a new baseline and keeps the earlier wording in each requirement's history, or **discards** it.",
        "The walkthrough's Changes chapter always runs on the seeded `OPP-0001`, because the sample addendum's frozen answers match that requirement set.",
      ],
      instruction: "Press Next to continue with creating the walkthrough opportunity.",
      fallback: "The Changes link is at the right end of the stepper row.",
    },
  ],
};
export default chapter;
