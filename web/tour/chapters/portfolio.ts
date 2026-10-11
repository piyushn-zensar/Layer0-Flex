// Walkthrough chapter 2: the Opportunities screen (web/app/portfolio/page.tsx).  Owner: G1 (overview and intake).
// Targets: data-tour="portfolio-*" on the page. Explain-only: nothing here writes.
import type { TourChapter } from "../types";
import { DEMO_OPP } from "../types";

const chapter: TourChapter = {
  id: "portfolio",
  order: 2,
  title: "The Opportunities screen",
  summary: "Every RFP in progress on one table: status, requirement count and how far each business unit has answered, with a link into every unit's work package.",
  entryRoute: "/portfolio",
  steps: [
    {
      id: "portfolio-intro",
      title: "Opportunities: the portfolio view",
      route: "/portfolio",
      target: "portfolio-table",
      placement: "bottom",
      fallback: "The table appears once the API answers; with no data yet the page offers to create an opportunity or to run the demo seed.",
      body: [
        "This is the home screen of Layer 0. One row per **opportunity**, and one opportunity per RFP: it is the workspace where that RFP's documents, requirements, matches, decisions, unit answers and final response live.",
        "The table comes from `GET /api/portfolio`: the opportunity record, the number of current requirements and each unit's progress on its work package. Newest opportunity first.",
        "From here you open an opportunity (its RFP documents or its Traceability view), jump straight into a unit's inbox, or start a new one. Nothing on this screen changes data: it is a read-only overview that refreshes whenever you come back to the tab.",
      ],
    },
    {
      id: "portfolio-columns",
      title: "ID, Title, Customer",
      route: "/portfolio",
      target: "portfolio-col-id",
      placement: "bottom",
      body: [
        "**ID** is allocated by the server as `OPP-0001`, `OPP-0002`, … (the next free number; two people creating at once never get the same one). It is the key used in every URL, in requirement IDs (`REQ-0001-0324` belongs to OPP-0001) and in hand-off files. Clicking it opens the RFP documents page, step 1 of the workflow.",
        "**Title** is what you typed when you created the opportunity; it becomes the heading of every page inside it. Clicking the title opens Traceability, the page most people work from once requirements exist.",
        "**Customer** is optional at creation and shows *not set* until filled in. It is recorded on the opportunity and repeated in the opportunity header; it does not drive any automatic behaviour.",
      ],
    },
    {
      id: "portfolio-status",
      title: "Status chips: where each bid is in the workflow",
      route: "/portfolio",
      target: `portfolio-status-${DEMO_OPP}`,
      placement: "right",
      fallback: "Each row has a status chip; the demo opportunities read \"dispatched\".",
      body: [
        "The chip is the opportunity's lifecycle status, which only moves forward: **new** (created) → **review** (the reader agent has proposed requirements) → **frozen** (the approved requirements became baseline 1) → **go** or **no-go** (the bid decision) → **dispatched** (work packages sent to the units) → **consolidating** (the final response is being assembled) → **submitted**.",
        "Because it only moves forward, repeating a step later (re-deciding \"go\" after dispatch, say) never sends an opportunity back. The exceptions are deliberate: **no-go** can stop a bid at any point before submission, and a later **go** resumes exactly where the bid stopped.",
        "Colours follow the app's five tones: grey for new, amber for review (someone has to act), blue for frozen / go / dispatched / consolidating, red for no-go, green for submitted. The same stepper appears in the header of every opportunity page, so you always know which step is next.",
      ],
    },
    {
      id: "portfolio-requirements",
      title: "Requirements: how many line items survived review",
      route: "/portfolio",
      target: `portfolio-reqs-${DEMO_OPP}`,
      placement: "left",
      fallback: "The Requirements column shows 348 for the Syracuse demo and 10 for the hyperscale sample.",
      body: [
        "This number is the count of **current** requirements: groups and stand-alone items the workflow works on. Sub-requirements inside a group, rejected items, duplicates and anything replaced by a split or a merge are not counted.",
        "For the Syracuse RFP it reads **348**: the reader agent proposed 814 line items from 101 pages, 21 were marked as duplicates and the grouping agent folded related items into 162 groups, leaving 348 requirements for people to review. Before the reader agent has run the column shows 0.",
        "If the number looks wrong, the Requirements page (chapter 5) is where it changes: approve, reject, edit, split, merge or add a missed item, then freeze.",
      ],
    },
    {
      id: "portfolio-units",
      title: "Unit responses: validated / total, per business unit",
      route: "/portfolio",
      target: `portfolio-units-${DEMO_OPP}`,
      placement: "left",
      fallback: "The column shows one line per business unit with a two-segment progress bar; \"not dispatched\" when the opportunity has no work packages yet.",
      body: [
        "After dispatch every approved requirement is assigned to the business unit(s) the matching step chose, or to the **BID** bid desk when no unit matched (commercial, legal and submission items the bid manager answers). Each line here is one unit: its code links to that unit's inbox, then **validated / total**, then a bar.",
        "The bar has two segments: green for answers the bid manager has **validated**, blue for answers **awaiting validation** (submitted but not yet checked). The rest of the bar is work not answered yet. Hover a line for the exact numbers, e.g. \"1 validated, 1 awaiting validation, 94 not answered\" for Crown on the Syracuse demo.",
        "Reading the demo: Syracuse went to **BID** (245 items), **CROWN** (96) and **EP2** (7). A unit that shows *not dispatched* has no assignments yet, either because the opportunity has not reached dispatch or because the unit did not take part in this bid.",
        "Returned answers (the bid manager sent them back with a note) count as not answered until the unit submits again, so the bar is an honest view of what is still open.",
      ],
    },
    {
      id: "portfolio-syracuse",
      title: "OPP-0001: the Syracuse switchgear RFP",
      route: "/portfolio",
      target: `portfolio-row-${DEMO_OPP}`,
      placement: "bottom",
      fallback: "OPP-0001 is the Syracuse Regional Airport Authority RFP 2023-20, Switchgear Procurement.",
      body: [
        "The first seeded opportunity is a real public RFP: **Syracuse Regional Airport Authority, RFP 2023-20 Switchgear Procurement**, 101 pages, customer type *public sector*. It asks for a 15 kV two-section arc-resistant metal-clad switchgear lineup with relays, controls and accessories.",
        "The seed ran the same services a person would use: the RFP was read, 348 requirements were approved and frozen, matching proposed Crown Technical Systems (switchgear) and EP² (relays and controls), the bid decision is **go**, and the work was dispatched. Two sample answers were attached to Crown's rows, one of them validated, so you can see every state at once.",
        "Everything the agents produced for this RFP comes from **frozen answers**: the model's replies were recorded once and are replayed, so the demo is repeatable offline and identical on every machine. The walkthrough will create a copy of this opportunity in chapter 4 so you can go through the steps yourself.",
      ],
    },
    {
      id: "portfolio-hyperscale",
      title: "OPP-0002: the multi-unit sample",
      route: "/portfolio",
      target: "portfolio-row-OPP-0002",
      placement: "bottom",
      fallback: "OPP-0002 is a fictional one-page RFP for an AI training campus; it shows the multi-unit case.",
      body: [
        "The second row, **AI training campus, Phase 1**, is a fictional one-page RFP for a 48 MW hyperscale site (800 VDC distribution, liquid cooling). Its customer is marked *(fictional)* and its type is *hyperscaler*.",
        "It exists to show the multi-unit case: ten requirements were matched across **Anord Mardix** (power distribution), **JetCool** (liquid cooling), **Flex Power Modules** (rack power) and the bid desk, so one requirement can carry several work-package rows and the hand-off per unit differs.",
        "Unlike Syracuse it has no frozen reader answers, so uploading it to a new opportunity and reading it would need the model connection. In the walkthrough we only look at it.",
      ],
    },
    {
      id: "portfolio-open",
      title: "Opening an opportunity",
      route: "/portfolio",
      target: `portfolio-open-${DEMO_OPP}`,
      placement: "left",
      fallback: "Each row ends with an Open button that leads to the opportunity's Traceability page.",
      body: [
        "**Open** takes you to Traceability (`/opportunities/<id>/trace`): the RFP page images on the left, the requirements with their matches and unit answers on the right. The ID in the first column goes to the RFP documents page instead, and the opportunity header's stepper lets you move between RFP, Requirements, Traceability, Bid decision, Final response and Changes.",
        "You can open an opportunity at any status: pages that are not yet applicable say what has to happen first (for example, dispatch needs a frozen baseline and a \"go\").",
      ],
    },
    {
      id: "portfolio-new",
      title: "New opportunity",
      route: "/portfolio",
      target: "portfolio-new",
      placement: "left",
      fallback: "The New opportunity button is at the top right of the page (and in the empty state when there is no data).",
      body: [
        "**New opportunity** opens the one-page creation form. One opportunity per RFP: the form takes a title, an optional customer and a customer type, then sends you to the RFP documents page to upload the RFP.",
        "Chapter 4 does exactly that, either by creating **Walkthrough: Syracuse switchgear** with the bundled Syracuse RFP or, if you prefer, by continuing on the demo opportunity OPP-0001.",
      ],
    },
  ],
};
export default chapter;
