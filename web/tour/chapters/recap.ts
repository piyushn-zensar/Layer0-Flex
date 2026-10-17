// Walkthrough chapter 12: Recap and completion.  Owner: Janvia (J-15).
// The first step revisits the stepper of the walkthrough bid; the rest are centred. The last step is the last step
// overall, so the bubble's Next becomes Finish and marks the walkthrough done for this session.
import type { TourChapter } from "../types";

const chapter: TourChapter = {
  id: "recap",
  order: 12,
  title: "Recap and completion",
  summary: "How the pieces connect from RFP to compliance matrix, where the audit trail lives, what is illustrative in the demo data, and how to explore on your own.",
  entryRoute: "/opportunities/{opp}",
  steps: [
    {
      id: "recap-flow",
      title: "From RFP to compliance matrix",
      route: "/opportunities/{opp}",
      target: "stepper",
      placement: "bottom",
      body: [
        "One chain runs through everything you saw. The **RFP** is read into requirements, each with a quote anchored to a page and lines, and the register is **frozen automatically** as baseline 1. In **Requirement Traceability** the original page, the register and the matcher's product proposals sit side by side, in panes you can rearrange and open in windows of their own. The **Assessment** chooses the participating units, routes every requirement and sends the work.",
        "Units answer their checklist in **My work**; the unit manager validates each answer, and the bid manager may return one with a question. The **Compliance matrix** collects the validated answers against every requirement, so the last check, that nothing from the RFP is unanswered, is a table rather than a reading exercise. The **Bid decision** records go or no-go on that evidence. Each later object keeps the ID of the earlier one, which is why the trace holds in both directions.",
      ],
      fallback: "The stepper under the bid title is the map of this chain.",
    },
    {
      id: "recap-changes",
      title: "Change handling keeps the chain intact",
      body: [
        "An addendum does not restart the work. The change agent compares it with the **current baseline** and proposes added, modified and removed requirements with evidence; people confirm item by item, and applying the set creates **baseline 2** while the earlier wording stays in each requirement's history and the IDs stay stable, so matches, assignments and answers keep pointing at the right rows.",
        "Removed requirements leave Requirement Traceability but keep their history in pane 2; modified ones show \"Revised in baseline n\" where they are used, so a unit knows to look again.",
      ],
    },
    {
      id: "recap-audit",
      title: "Where the audit trail lives",
      body: [
        "Every create, correction, match decision, participation, send, answer, validation, return, decision and change confirmation appends a row to the **append-only** audit log with the actor, the action, the entity, the bid and a before/after payload; database triggers reject updates and deletes.",
        "On screen you meet it as **History** on a requirement (pane 2) and on an answer (the matrix and My work), as the before/after on each change-set item, and as the **Activity** page of the bid with its filters.",
      ],
    },
    {
      id: "recap-placeholders",
      title: "What is illustrative in this demo",
      body: [
        "The **business units** are a working list marked as needing confirmation, and the people are role placeholders such as *Crown Product Manager*. The engineering rules, standard ratings, capacities and the placeholder thresholds (the 25% change threshold, the 80% compliance threshold, the 5 consolidation days) are marked as placeholders where they appear. The seeded past responses are **illustrative** and never treated as verified evidence; the reference documents in Sources are drafts until reviewed.",
        "The agents' answers are **frozen** for the sample RFPs, so the demo is repeatable and offline. Sign-in is a simple token with a sign-up that lets anyone choose a bid-manager role (a known limit of the proof of concept). There is no pricing, no CPQ or CRM connection, and the response outline is an outline with validated answers, not a formatted proposal.",
      ],
    },
    {
      id: "recap-explore",
      title: "Exploring on your own",
      body: [
        "Rearrange the panes of **Requirement Traceability** and open one in a new window; filter by category or response and share the address. Sign in as a unit's designer / engineer to see My work from their side and what the server refuses to that role. Open the **Logan City** bid (OPP-0002) to see a second RFP read from its own frozen answers. Look at the **Sources** and **Published catalog** tabs of the Product catalog.",
        "To put the demo data back to its starting state, close the app and run `reset-demo.cmd`; it reseeds both bids from the frozen answers. The **Walkthrough** button lets you reopen any chapter later.",
      ],
    },
    {
      id: "recap-finish",
      title: "You have completed the walkthrough",
      body: [
        "You saw a bid from its RFP to the compliance matrix: how it is read and frozen, how the register is corrected and traced, how the work is assessed, routed and sent, how a unit answers and validates, how the decision is taken on the evidence, how an addendum is handled, and where every step is recorded. That is the whole Layer 0 loop: agents propose, a named person decides, and every requirement traces back to its page and lines.",
        "Press **Finish** to close the walkthrough. It will not open again by itself in this server session; the Walkthrough button in the top bar restarts it or opens a single chapter whenever you want.",
      ],
      instruction: "Press Finish to mark the walkthrough as done.",
    },
  ],
};
export default chapter;
