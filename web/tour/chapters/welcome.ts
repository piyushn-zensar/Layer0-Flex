// Walkthrough chapter 1: Welcome and overview. Centred steps, no page targets.  Owner: tour engine.
import type { TourChapter } from "../types";

const chapter: TourChapter = {
  id: "welcome",
  order: 1,
  title: "Welcome and overview",
  summary: "What Layer 0 is for, the six steps of a bid, how agents and people share the work, and how this walkthrough runs.",
  steps: [
    {
      id: "welcome-purpose",
      title: "What Layer 0 is",
      body: [
        "Layer 0 is the bridge between the CRM, where an opportunity is first logged, and CPQ (Configure, Price, Quote), which can only start once someone has read the RFP and typed structured requirements. For engineered power and cooling bids that reading is the slow, manual, unrecorded part: an RFP often runs past 100 pages and mixes standard items with items that need new engineering.",
        "This proof of concept takes **one bid opportunity** from the moment the RFP arrives to the final response. The RFP is read into requirement **line items anchored to a page and lines** of the source, each line item is matched to a business unit's product, the go/no-go decision is recorded, each participating unit gets one work package, and the bid manager validates and consolidates the answers into a response that traces back to every requirement.",
        "The demo data is a real public RFP: the Syracuse Regional Airport Authority's switchgear procurement (RFP 2023-20, 101 pages). Read by the agents it becomes about 810 line items, grouped into about 350 requirements.",
      ],
    },
    {
      id: "welcome-steps",
      title: "The six steps of a bid",
      body: [
        "Every opportunity moves through the same six steps, shown as a stepper under its title: **1 RFP** (upload the document, the reader agent extracts line items), **2 Requirements** (a person checks each line item against its source, approves, then freezes the baseline), **3 Traceability** (each frozen requirement is matched to a unit's product and an offering type: configure-to-order, semi-custom or engineered-to-order), **4 Bid decision** (participation per unit and go/no-go with a written rationale, then dispatch), **5 Unit work** (each unit answers its work package as a checklist from the My work inbox) and **6 Final response** (the bid manager validates every answer and consolidates them).",
        "Alongside the steps sits **Changes**: when an addendum arrives after the freeze, the change agent compares it with the current baseline and proposes added, modified and removed requirements; a person confirms each one and the bid manager applies a new baseline.",
        "The opportunity status follows the steps: `new` → `reading` → `review` → `frozen` → `go` or `no-go` → `dispatched` → `consolidating` → `submitted`. The status only moves forward; a `no-go` can stop a bid before submission and a later `go` resumes it. (`reading` is defined but not used by the current reader, which answers in one call.)",
      ],
    },
    {
      id: "welcome-agents",
      title: "Agents propose, people decide",
      body: [
        "Three agents do the reading: the **reader** turns RFP pages into line items with the exact quote and its page and line numbers, the **grouping** agent folds the line items into requirements, and the **matcher** proposes a product and offering type per requirement. A **change** agent compares an addendum with the baseline. None of them decides anything: every proposal stays `proposed` until a named person approves, rejects, edits or confirms it, and that person's name goes into the audit trail.",
        "The language model answers used in this demo are **frozen**: every answer the agents gave for the sample RFPs is cached under `data/llm_cache` and replayed, so the demo runs offline (`LLM_PROVIDER=mock`), gives the same result every time and costs nothing. If you upload a different PDF in this offline mode, the document is still stored and parsed, but the reader reports the pages it could not read (no cached answer and no provider) instead of guessing, and the matcher falls back to retrieval only.",
        "Everything a person or an agent does is written to an **append-only audit log** (the `audit_event` table; database triggers reject updates and deletes). You will see it as the History of a requirement and in the before/after of a change set.",
      ],
    },
    {
      id: "welcome-you",
      title: "What you will do",
      body: [
        "In the next chapters you will walk through every screen in the order a bid uses them. You will create a new opportunity called **Walkthrough: Syracuse switchgear**, load the Syracuse RFP from the built-in samples, review a few requirements and freeze the baseline, read the traceability view, record a bid decision and dispatch work, answer a work package as a unit, validate and consolidate as the bid manager, visit the knowledge base queue, and finally handle an addendum on the seeded demo opportunity.",
        "Where a step needs the opportunity in an earlier state than the one you have, the walkthrough skips it or explains what would happen instead. Nothing destructive runs without an explicit instruction, and you can also choose **Use the demo opportunity instead** in chapter 4 to work on the seeded `OPP-0001`, which is already frozen, decided and dispatched.",
        "Expect about **25 to 30 minutes** end to end; reading the Syracuse RFP into line items takes about a minute of that.",
      ],
    },
    {
      id: "welcome-controls",
      title: "How this walkthrough works",
      body: [
        "Each step highlights one part of the screen and explains it in this bubble. **Next** and **Previous** move through the steps (the arrow keys work too), **Esc** or **Exit** closes the walkthrough without losing your place, and the **Walkthrough** button in the top bar brings it back with Resume, Restart and a chapter list. **Chapters** at the bottom of this bubble jumps straight to a chapter.",
        "Steps that ask you to do something show a highlighted **Do this now** line; Next stays disabled until the page shows the result (it is checked every half second), and **Continue anyway** lets you move on regardless. Many of those steps offer **Use example**, which fills the form with sample values or loads a built-in sample file so you can keep going with one click.",
        "Your progress is saved in this browser, so a page refresh or switching the acting person continues at the same step. A restart of the development server offers the walkthrough again.",
      ],
      instruction: "Press Next to begin with the Opportunities screen.",
    },
  ],
};
export default chapter;
