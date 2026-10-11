// Walkthrough chapter 12: Recap and completion.  Owner: tour engine.
// The first step revisits the stepper of the walkthrough opportunity; the rest are centred. The last step is the
// last step overall, so the bubble's Next becomes Finish and marks the walkthrough done for this session.
import type { TourChapter } from "../types";

const chapter: TourChapter = {
  id: "recap",
  order: 12,
  title: "Recap and completion",
  summary: "How the pieces connect from RFP to final response, where the audit trail lives, what is illustrative in the demo data, and how to explore on your own.",
  entryRoute: "/opportunities/{opp}",
  steps: [
    {
      id: "recap-flow",
      title: "From RFP to final response",
      route: "/opportunities/{opp}",
      target: "stepper",
      placement: "bottom",
      body: [
        "One chain runs through everything you saw. The **RFP** is read into line items, each with a quote anchored to a page and lines. A person turns them into an approved, **frozen** baseline of requirements with stable ids. The matcher proposes a product, a business unit and an offering type per requirement, shown in **Traceability** next to the source text. The **Bid decision** records who participates and whether to bid, and dispatch cuts one work package per unit.",
        "Units answer their checklist in **My work**; the bid manager validates each answer or returns it with a note. **Final response** collects the validated answers against every requirement, so the last check, that nothing from the RFP is unanswered, is a table rather than a reading exercise. Each later object keeps the id of the earlier one, which is why the trace holds in both directions.",
      ],
      fallback: "The stepper under the opportunity title is the map of this chain.",
    },
    {
      id: "recap-changes",
      title: "Change handling keeps the chain intact",
      body: [
        "An addendum does not restart the work. The change agent compares it with the **current baseline** and proposes a change set of added, modified, removed and unchanged requirements with evidence from the new document. People confirm item by item; applying the set creates **baseline 2** (and so on) while the earlier wording stays in each requirement's history and the requirement ids stay stable, so matches, assignments and answers keep pointing at the right rows.",
        "Removed requirements disappear from Traceability but keep their history on the Requirements page; modified ones show “Revised in baseline n” where they are used, so a unit knows to look again.",
      ],
    },
    {
      id: "recap-audit",
      title: "Where the audit trail lives",
      body: [
        "Every create, approve, reject, freeze, match decision, participation, go/no-go, dispatch, answer, validation, change confirmation and knowledge approval calls one function, `audit.record`, which appends a row to the `audit_event` table with the actor, the action, the entity, the opportunity and a before/after payload. The table is **append-only**: SQLite triggers reject updates and deletes.",
        "On screen you meet it as **History** on a requirement row (its wording, status and baseline changes with who and when), as the before/after shown on each change-set item, and as the actor and timestamp on decisions, answers and validations. The API exposes a requirement's history at `/api/requirements/{id}/history`.",
      ],
    },
    {
      id: "recap-placeholders",
      title: "What is illustrative in this demo",
      body: [
        "The **business units** (EP², Crown Technical Systems, Anord Mardix, Flex Power Modules, JetCool, Cloud; EPC Power pending and not offered) are a working list marked “Needs confirmation”, and the people are role placeholders such as `EP² Product Manager`. The **product catalog**, engineering rules and past responses are small hand-written knowledge-base files, enough to make the matcher meaningful on the sample RFPs, not the real catalogue.",
        "The agents' answers are **frozen** for the sample RFPs (`LLM_PROVIDER=mock`), so the demo is repeatable and offline; a live model would be used for new RFPs. There is no sign-in (the Acting as picker stands in), no pricing, no CPQ or CRM connection, and the final response is an outline with validated answers, not a formatted proposal. The seeded `OPP-0002` is a synthetic hyperscale campus RFP used to show a multi-unit bid.",
      ],
    },
    {
      id: "recap-explore",
      title: "Exploring on your own",
      body: [
        "Create another opportunity with **New opportunity** and load the other built-in sample (the hyperscale campus RFP) from the RFP page's *Use example* path, or upload any PDF to see how the reader reports pages it has no frozen answer for instead of guessing. Switch **Acting as** to a unit's design engineer to see the inbox from their side and what the server refuses to that role. Open **Traceability** on `OPP-0001` and click through the colour legend to see where the engineered-to-order work concentrates.",
        "To put the demo data back to its starting state, close the app and run `reset-demo.cmd` (it reseeds `OPP-0001` and `OPP-0002` from the frozen answers). Your walkthrough opportunity is removed with it. The **Walkthrough** button lets you reopen any chapter later.",
      ],
    },
    {
      id: "recap-finish",
      title: "You have completed the walkthrough",
      body: [
        "You created an opportunity, loaded and read an RFP, reviewed and froze requirements, read the trace, recorded a bid decision and dispatched work, answered and validated a work package, consolidated the response, visited the knowledge queue and handled an addendum. That is the whole Layer 0 loop: agents propose, a named person decides, and every requirement traces back to its page and lines.",
        "Press **Finish** to close the walkthrough. It will not open again by itself in this server session; the Walkthrough button in the top bar restarts it or opens a single chapter whenever you want.",
      ],
      instruction: "Press Finish to mark the walkthrough as done.",
    },
  ],
};
export default chapter;
