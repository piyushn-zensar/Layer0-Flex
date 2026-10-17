// Walkthrough chapter 2: the Bids screen (web/app/portfolio/page.tsx).  Owner: Janvia (J-15).
// Targets: data-tour="portfolio-*" on the page. Explain-only: nothing here writes.
import type { TourChapter } from "../types";
import { DEMO_OPP } from "../types";

const chapter: TourChapter = {
  id: "portfolio",
  order: 2,
  title: "The Bids screen",
  summary: "Every bid in progress on one table: status, requirement count and how far each business unit has answered.",
  entryRoute: "/portfolio",
  steps: [
    {
      id: "portfolio-intro",
      title: "Bids: the home screen",
      route: "/portfolio",
      target: "portfolio-table",
      placement: "bottom",
      fallback: "The table appears once the API answers; with no bids yet the page offers to create one.",
      body: [
        "This is the home screen of Layer 0. One row per **bid**, and one bid per RFP: it is the workspace where that RFP's documents, requirements, matches, assessment, decision, unit answers and compliance matrix live.",
        "From here you open a bid, jump straight into a unit's work, or start a new bid. Nothing on this screen changes data; it refreshes whenever you come back to the tab.",
      ],
    },
    {
      id: "portfolio-columns",
      title: "ID, Title, Customer",
      route: "/portfolio",
      target: "portfolio-col-id",
      placement: "bottom",
      body: [
        "**ID** is allocated by the server as `OPP-0001`, `OPP-0002`, … It appears in every URL and in requirement IDs (`REQ-0001-0324` belongs to OPP-0001). **Title** is what was typed when the bid was created and becomes the heading of every page inside it. **Customer** is optional.",
      ],
    },
    {
      id: "portfolio-status",
      title: "Status: where each bid is in the workflow",
      route: "/portfolio",
      target: `portfolio-status-${DEMO_OPP}`,
      placement: "right",
      fallback: "Each row has a status chip; the Syracuse bid reads \"dispatched\".",
      body: [
        "The chip is the bid's lifecycle status, which only moves forward: **new** → **review** → **frozen** (the register became baseline 1) → **go** or **no-go** → **dispatched** (the work was sent to the units) → **consolidating** → **submitted**. The same status shows in the header of every page of the bid.",
        "A bid is **frozen automatically** when its main RFP has been read completely, so the Syracuse bid is already beyond review; later corrections are versioned, not re-reads.",
      ],
    },
    {
      id: "portfolio-requirements",
      title: "Requirements: how many stand in the register",
      route: "/portfolio",
      target: `portfolio-reqs-${DEMO_OPP}`,
      placement: "left",
      fallback: "The Requirements column shows 312 for the Syracuse bid.",
      body: [
        "This is the count of **current** requirements. For the Syracuse RFP it reads **312**: the reader proposed 818 line items from 101 pages, 779 entered the register as 312 requirements after grouping (161 groups), 27 were marked duplicates and 12 wait in the exception queue because their quote could not be matched word for word.",
      ],
    },
    {
      id: "portfolio-units",
      title: "Unit responses: validated / total",
      route: "/portfolio",
      target: `portfolio-units-${DEMO_OPP}`,
      placement: "left",
      fallback: "The column shows one line per unit with a progress bar; \"not dispatched\" when no work has been sent yet.",
      body: [
        "After the work is sent, every item goes to a unit or to the **BID** bid desk. Each line is one unit: its code links to that unit's work, then **validated / total**, then a bar: green for answers the unit manager has validated, blue for answers awaiting validation.",
        "On Syracuse: **CROWN** 118 items, **EP2** 31 and **BID** 73. Crown and EP² also receive the schedule, commercial and staffing items for their managers; the bid desk keeps the high-level submission and legal items.",
      ],
    },
    {
      id: "portfolio-independent",
      title: "OPP-0002: the independent RFP",
      route: "/portfolio",
      target: "portfolio-row-OPP-0002",
      placement: "bottom",
      fallback: "OPP-0002 is Logan City Light & Power's RFP for 15 kV switchgear at Substation 6.",
      body: [
        "The second row is a public RFP from another issuer: **Logan City Light & Power (Utah), 15 kV switchgear for Substation 6**, 46 pages. It is there to check the pipeline on a document it was not tuned on: 167 requirements, 4 quotes waiting in the exception queue. It is frozen and not yet sent to units, so it has no unit bars.",
      ],
    },
    {
      id: "portfolio-open",
      title: "Open and New bid",
      route: "/portfolio",
      target: `portfolio-open-${DEMO_OPP}`,
      placement: "left",
      fallback: "Each row ends with an Open button that leads to the bid's Requirement Traceability page.",
      body: [
        "**Open** takes you to Requirement Traceability, the page most people work from. The ID in the first column goes to the RFP page instead, and the stepper in the bid header moves between steps.",
        "**New bid** (top right, bid manager only) starts a bid for another RFP; chapter 4 shows the form.",
      ],
    },
  ],
};
export default chapter;
