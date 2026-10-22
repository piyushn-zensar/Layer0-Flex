// Walkthrough chapter 1: Welcome and overview. Centred steps, no page targets.  Owner: Janvia (J-15).
import type { TourChapter } from "../types";

const chapter: TourChapter = {
  id: "welcome",
  order: 1,
  title: "Welcome and overview",
  summary: "What Layer 0 is for, the two demo bids, the five steps of a bid, how agents and people share the work, and how this walkthrough runs.",
  steps: [
    {
      id: "welcome-purpose",
      title: "What Layer 0 is",
      body: [
        "Layer 0 is the bridge between the CRM, where a bid is first logged, and CPQ (Configure, Price, Quote), which can only start once someone has read the RFP and typed structured requirements. For engineered power and cooling bids that reading is the slow, manual, unrecorded part: an RFP often runs past 100 pages and mixes standard items with items that need new engineering.",
        "This proof of concept takes **one bid** from the moment the RFP arrives to the final response. The RFP is read into requirements **anchored to a page and lines** of the source, each requirement is matched to a business unit's proposed solution, the participating units are chosen and sent their work, each unit answers its checklist, the bid manager decides go or no-go on the evidence, and the answers are consolidated into a compliance matrix that traces back to every requirement.",
        "The demo focuses on cloud and power infrastructure with two scenarios. **RC-1 Grid-to-Chip** (bid **OPP-0003**) is a synthetic RFP for a 120 MW AI campus bought in six lots, from the utility connection and 800 V DC power to the racks and liquid cooling; it has been worked through to the go decision. The **Syracuse** switchgear procurement (bid **OPP-0001**) is a real public RFP (RFP 2023-20, 101 pages) with a saved focus on its power electronics requirements: read by the agents it becomes 818 candidate line items, of which 312 requirements stand in the register.",
      ],
    },
    {
      id: "welcome-steps",
      title: "The five steps of a bid",
      body: [
        "Every bid moves through the same five steps, shown as a stepper under its title: **RFP** (the document and what the reader covered), **Requirement Traceability** (the original RFP, the requirement register and the proposed solutions side by side), **Assessment Summary** (the bid manager's first stage: business relevance, which units take part, routing, sending the work to the units, and the teams' delivery feasibility), **Compliance matrix** (every requirement with its unit's answer) and **Bid decision** (the evidence, the reviewed compliance outcomes, the compliance position and the go/no-go).",
        "Two side tracks sit beside the steps: **Changes**, where an addendum is compared with the frozen requirements and a person confirms each change, and **Activity**, the bid's audit log.",
        "The bid status follows the work: **New** → **In review** → **Requirements frozen** → **Sent to units** → **Go recorded** or **No-go recorded** → **Go: response in preparation** (every answer validated after a go) → **Submitted**. It only moves forward; a **No-go** can stop a bid and a later **Go** resumes it.",
      ],
    },
    {
      id: "welcome-agents",
      title: "Agents propose, people decide",
      body: [
        "Three agents do the reading: the **reader** turns RFP pages into line items with the exact quote and its page and line numbers, the **grouping** agent folds line items into requirements, and the **matcher** proposes a solution (unit and solution area) and type of offer per requirement. A **change** agent compares an addendum with the frozen requirements. None of them decides anything: every proposal stays *proposed* until a named person accepts, rejects, corrects or confirms it, and that person's name goes into the audit trail.",
        "The model answers used in this demo are **frozen**: every answer for the sample RFPs is cached and replayed, so the demo runs offline, gives the same result every time and costs nothing. If you upload a different PDF in this mode, the pages the reader has no answer for are reported instead of guessed.",
        "Everything a person or an agent does is written to an **append-only audit log**. You will meet it as the History of a requirement or an answer, and as the **Activity** page of a bid.",
      ],
    },
    {
      id: "welcome-you",
      title: "What you will do",
      body: [
        "The walkthrough runs on the Syracuse bid **OPP-0001**, because its steps use that RFP's pages, requirements and sample addendum. It is already read, frozen and sent to the units, and no go/no-go is recorded yet, so it shows a bid while the units are assessing it. You will see the list of bids, open its RFP, read the Requirement Traceability workspace (and rearrange it), see the Assessment Summary, answer a unit's item as the unit and validate it, read the Compliance matrix, the Activity log and the Bid decision, look at the Product catalog, and finally apply an addendum under Changes.",
        "Afterwards, open **OPP-0003** (RC-1 Grid-to-Chip) to see the same screens at the end of the workflow: every unit answer validated, all four compliance outcomes used, the teams' delivery estimates accepted and the go recorded.",
        "Nothing destructive runs without an explicit instruction. Expect about **25 to 30 minutes** end to end.",
      ],
    },
    {
      id: "welcome-controls",
      title: "How this walkthrough works",
      body: [
        "Each step highlights one part of the screen and explains it in this bubble. **Next** and **Previous** move through the steps (the arrow keys work too), **Esc** or **Exit** closes the walkthrough without losing your place, and the **Walkthrough** button in the top bar brings it back with Resume, Restart and a chapter list. **Chapters** at the bottom of this bubble jumps straight to a chapter.",
        "The bubble stays beside the part of the screen it explains. If it is ever in your way, **Minimise** shrinks it to a small tab at the bottom of the screen; the tab brings it back. On a phone the bubble sits at the bottom of the screen and the highlighted part is scrolled above it.",
        "Steps that ask you to do something show a **Do this now** line; Next stays disabled until the page shows the result, and **Continue anyway** lets you move on regardless. Many of those steps offer **Use example**. Your progress is saved in this browser, so a refresh or a change of signed-in person continues at the same step.",
      ],
      instruction: "Press Next to begin with the list of bids.",
    },
  ],
};
export default chapter;
