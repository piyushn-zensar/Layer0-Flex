// Walkthrough chapter 3: Navigation, sign-in, roles and the workflow stepper.  Owner: Janvia (J-15).
// The first part spotlights the top bar (on whatever page the person is on); the second part opens the walkthrough bid
// ({opp}, the seeded OPP-0001) to explain the bid header and the stepper.
import type { TourChapter } from "../types";

const chapter: TourChapter = {
  id: "navigation",
  order: 3,
  title: "Navigation, sign-in, roles and the stepper",
  summary: "The top bar, who is signed in and what each role may do, sign-up; then the bid header, its status badge and the five-step stepper.",
  entryRoute: "/portfolio",
  steps: [
    {
      id: "navigation-brand",
      title: "The top bar is the same on every screen",
      target: "shell-brand",
      placement: "bottom",
      body: [
        "The dark bar stays at the top of every page. From left to right: the **Layer 0** mark (a link back to the list of bids), the three main destinations, and on the right **New bid**, the signed-in person (name, role and unit) with **Sign out**, and the **Walkthrough** button you are using now.",
      ],
      fallback: "The top bar is above the page content; this step describes its left end.",
    },
    {
      id: "navigation-nav",
      title: "Three destinations",
      target: "shell-nav",
      placement: "bottom",
      body: [
        "**Bids** is the list of every bid with its status and progress; it stays highlighted inside a bid because every bid page belongs to it. **My work** is the person's own work: a unit's work package, the bid desk's items, the unit manager's completion dates and the **Knowledge review** list.",
        "**Product catalog** lists the business units and the products the matcher can choose from, the reference documents behind them (Sources) and the catalog read from the Flex web pages (Published catalog). Knowledge has no page of its own: a requirement, a validated answer or a decision is **nominated as a reviewed example** where it appears, and the right reviewer approves it in Knowledge review in My work.",
      ],
      fallback: "The three links sit in the top bar next to the Layer 0 mark.",
    },
    {
      id: "navigation-new",
      title: "New bid",
      target: "shell-new-opportunity",
      placement: "bottom",
      body: [
        "Every bid starts here (bid manager only). The form asks for a **title**, the **customer** and the **customer type**, creates the bid with the next free ID and opens its RFP page, where the document is uploaded. Chapter 4 shows the form.",
      ],
      fallback: "The New bid button is on the right of the top bar.",
    },
    {
      id: "navigation-actor",
      title: "Signed in as: name, role and unit",
      target: "shell-actor",
      placement: "bottom",
      body: [
        "Everyone signs in on the sign-in page; there is no picker for \"acting as\". The bar shows **who is signed in**: the name, then the **role** and the **unit**. The name is recorded on everything that person does. **Sign out** ends the session and returns to the sign-in page.",
        "The roles are **Bid manager** (no unit), **Unit manager** and **Unit designer / engineer** (both belong to a unit) and **Administrator** (reads everything, changes nothing). New people use **Sign up** on the sign-in page: they choose a role (never Administrator), a unit for the unit roles, and a password of at least 10 characters. In this proof of concept anyone can sign up as bid manager.",
        "The server enforces what each role may do. Technical items are answered by a unit's designers / engineers, schedule, commercial and staffing items by the unit manager, who also validates the unit's answers; the bid manager answers the bid desk items, decides go or no-go, sends the work and applies changes.",
      ],
      fallback: "The signed-in name, role, unit and Sign out are in the right half of the top bar.",
    },
    {
      id: "navigation-help",
      title: "The Walkthrough button",
      target: "shell-help",
      placement: "bottom",
      body: [
        "This button reopens the walkthrough at any time: **Resume** when you left part-way, **Restart**, and the **chapter list** with ticks for the chapters you have finished. Progress is stored in this browser for the current server session.",
      ],
      fallback: "The Walkthrough button is at the far right of the top bar.",
    },
    {
      id: "navigation-opp-head",
      title: "Inside a bid: the header",
      route: "/opportunities/{opp}",
      target: "opp-head",
      placement: "bottom",
      body: [
        "Every page of a bid shares this header: the **breadcrumb** back to Bids with the ID, the **title**, the **status badge** and the **stepper**. The header refreshes itself, so the badge and the ticks follow every action.",
      ],
      fallback: "Open a bid from the list to see this header above its pages.",
    },
    {
      id: "navigation-status",
      title: "The status badge",
      route: "/opportunities/{opp}",
      target: "opp-status",
      placement: "bottom",
      body: [
        "The badge shows the bid's position in the workflow: `new`, `review`, `frozen` (the register is baseline 1), `go` or `no-go` (the decision), `dispatched` (work sent to the units), `consolidating` and `submitted`. It only moves forward; `no-go` can stop a bid at any point before submission, and a later `go` resumes it.",
        "The seeded Syracuse bid sits at `dispatched`. A new bid is frozen automatically as soon as its main RFP has been read completely; there is no Publish or Freeze button any more.",
      ],
      fallback: "The status badge appears next to the bid title once the bid has loaded.",
    },
    {
      id: "navigation-stepper",
      title: "The stepper: where the bid stands",
      route: "/opportunities/{opp}",
      target: "stepper",
      placement: "bottom",
      body: [
        "The five entries are the step pages. The **current** page is underlined; a step shows a green **tick** once the status has moved past it (RFP from reading, Requirement Traceability from `frozen`, Assessment from `dispatched`, Compliance matrix and Bid decision at `submitted`). Ticks come from the status, not from visiting a page, and you can open any step at any time.",
      ],
      fallback: "The stepper is the row of links under the bid title.",
    },
    {
      id: "navigation-step-rfp",
      title: "RFP and Requirement Traceability",
      route: "/opportunities/{opp}",
      target: "step-rfp",
      placement: "bottom",
      body: [
        "**RFP** is the document page: the files, what the reader covered, and a search over the RFP text. **Requirement Traceability** is the main working page: the original RFP page with highlights, the requirement register and the product mapping side by side, in panes you can rearrange (chapter 6).",
      ],
      fallback: "The first two stepper entries are RFP and Requirement Traceability.",
    },
    {
      id: "navigation-step-assessment",
      title: "Assessment, Compliance matrix and Bid decision",
      route: "/opportunities/{opp}",
      target: "step-assessment",
      placement: "bottom",
      body: [
        "**Assessment** chooses the participating units, shows how every requirement is routed, sends the work to the units and plans the schedule. **Compliance matrix** is the bid manager's consolidation: every requirement with the unit's answer. **Bid decision** records go or no-go on the evidence, after the units have assessed the bid.",
      ],
      fallback: "The next three stepper entries are Assessment, Compliance matrix and Bid decision.",
    },
    {
      id: "navigation-changes",
      title: "Changes and Activity",
      route: "/opportunities/{opp}",
      target: "step-changes",
      placement: "left",
      body: [
        "**Changes** is a side track: an addendum is compared with the frozen baseline and a person confirms each proposed change before the bid manager applies it as a new baseline. **Activity**, next to it, lists everything done on the bid, newest first. Chapters 9 and 11 use them.",
      ],
      instruction: "Press Next to continue with the RFP page.",
      fallback: "The Changes and Activity links are at the right end of the stepper row.",
    },
  ],
};
export default chapter;
