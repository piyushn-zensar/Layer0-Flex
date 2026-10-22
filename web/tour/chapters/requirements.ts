// Walkthrough chapter 5: the requirement register, pane 2 of Requirement Traceability (components/requirements/Register).  Owner: Janvia (J-15).
// A-26 moved the register, the exception queue, the corrections and the history into pane 2; the Requirements page, the
// approve steps and the Freeze baseline button are gone (P-22, P-32): a complete read freezes the register at once and every
// later fix is a correction with a reason. Explain-only; all targets are in the main window.
import { openDetails } from "../helpers";
import type { TourChapter, TourCtx } from "../types";

const ROUTE = "/opportunities/{opp}/trace";

/** Show the Register or the Exceptions tab of pane 2 (idempotent: the engine calls onEnter more than once). */
const showTab = (which: "register" | "exceptions") => (ctx: TourCtx) => {
  const tab = ctx.el(`req-tab-${which}`);
  if (tab && tab.getAttribute("aria-selected") !== "true") tab.click();
};

/** On a phone (docked bubble, under 700 px) the panes stack and pane 1's page image loads after the engine has scrolled,
 * pushing pane 2 down under the bubble: once the image is in, bring the target's top back to the top of the screen. */
const topOnPhone = (tourId: string) => async (ctx: TourCtx) => {
  if (window.innerWidth >= 700) return;
  const images = () => Array.from(document.querySelectorAll<HTMLImageElement>('[data-tour="trace-pane-1"] img'));
  for (let i = 0; i < 20 && images().some((im) => !im.complete); i++) await new Promise((r) => setTimeout(r, 250));
  const top = ctx.el(tourId)?.getBoundingClientRect().top;
  if (top !== undefined && Math.abs(top - 16) > 40) window.scrollBy({ top: top - 16, behavior: "smooth" });
};

const chapter: TourChapter = {
  id: "requirements",
  order: 5,
  title: "The requirement register",
  summary: "Pane 2 of Requirement Traceability: the register and its filters, a requirement's source, the requirements that need a source check, corrections with a reason, history and missed requirements.",
  entryRoute: ROUTE,
  steps: [
    {
      id: "requirements-register", route: ROUTE, target: "trace-pane-2", placement: "left",
      onEnter: (ctx) => { showTab("register")(ctx); return topOnPhone("trace-pane-2")(ctx); },
      title: "Pane 2: the requirement register",
      body: [
        "The requirements used to have a page of their own; they now live in **pane 2** of Requirement Traceability, next to the RFP page and the proposed solutions. It shows what the reader found in the RFP: **312 requirements** for Syracuse, each with its ID, category, source, wording, quote and status.",
        "Nothing needs approving first. The register is **frozen automatically** the moment a main RFP has been read completely, so matching, assessment and the units all work from one fixed set. People then **correct** it; they do not re-read the RFP.",
      ],
      fallback: "Pane 2 is not on the page yet (the register is still loading).",
    },
    {
      id: "requirements-baseline", route: ROUTE, target: "req-baseline", placement: "bottom",
      title: "Frozen version 1, frozen automatically",
      body: [
        "The line above the tabs names the frozen version: *Frozen version 1, frozen automatically when Bid Manager read the RFP (312 items)*. A frozen version is the numbered, frozen set of requirements; customer changes (addenda, Q&A, change requests) create frozen version 2 and so on through the Changes page, never by editing frozen version 1 in place.",
      ],
      fallback: "The frozen-version line is shown once the register has loaded.",
    },
    {
      id: "requirements-coverage", route: ROUTE, target: "req-coverage", placement: "bottom",
      title: "What the reader covered",
      body: [
        "This line sums up **RFP reading 1**, the first reading: *818 statements read, grouped into 312 requirements (161 groups); 12 need a source check; 27 duplicates*. Open it for the detail: 101 pages, 100 read, 1 skipped, the reader calls and the candidates in the register. It is append-only. It tells a reviewer how complete the reading was before trusting the numbers: unread pages and failed calls would show here, never be hidden.",
      ],
      fallback: "The coverage line is shown once the register has loaded.",
    },
    {
      id: "requirements-tabs", route: ROUTE, target: "req-tabs", placement: "bottom", onEnter: showTab("register"),
      title: "Register and Needs a source check",
      body: [
        "**Register** holds the requirements that stand: every quote was found on its page. **Needs a source check** holds reader items whose quote could not be matched word for word (12 for Syracuse); they are never silently approved and never silently dropped. The next steps look at each.",
      ],
      fallback: "The two tabs are above the filters in pane 2.",
    },
    {
      id: "requirements-filters", route: ROUTE, target: "req-filters", placement: "bottom", onEnter: showTab("register"),
      title: "In register, Excluded, Duplicates, Ungrouped, All",
      body: [
        "The chips filter the register. **In register** is the live set (312). **Excluded** holds items a person excluded as not a requirement, with the reason; **Duplicates** the 27 near-identical candidates the grouping agent set aside; **Ungrouped / split / merged** the originals replaced by a correction; **All** everything (339 here). Nothing is deleted: an excluded or duplicate item can be restored.",
        "These chips filter pane 2 only. The filter bar above the panes (category, type of offer, business unit, unit response, unit compliance, RFP source check, added by, pages, text, sort) filters all three panes the same way and is kept in the page address.",
      ],
      fallback: "The filter chips are shown once the register has loaded.",
    },
    {
      id: "requirements-row", route: ROUTE, target: "req-row-first", placement: "left", onEnter: showTab("register"),
      title: "One requirement",
      body: [
        "The register has three columns so it fits a pane: a selection box, **ID** and **Requirement**. Under the stable ID `REQ-<bid>-<number>` sit its **category** (Technical, Compliance, Commercial, Submission, Legal, Schedule or Staffing) and its **source** (page and lines). The Requirement column holds the short **requirement text** with the exact **quote** from the RFP beneath it, then the **status** badge, **History** and the correction actions. Related items are grouped: expand a group to see its sub-requirements, each with its own source.",
        "Selecting a row selects it in all three panes: pane 1 turns to its page and highlights its lines, pane 3 shows its proposed solution and the units' answers.",
      ],
      fallback: "The first requirement row is shown once the register has loaded.",
    },
    {
      id: "requirements-source", route: ROUTE, target: "req-row-source", placement: "left",
      title: "Source: page and lines",
      body: [
        "The source, under the ID, states where the quote was found, for example **p. 1, line 5**. Layer 0 never invents a location: the reader's quote is checked against the page, and only a verified quote enters the register. An item whose quote cannot be found keeps its page hint and waits in Needs a source check.",
      ],
      fallback: "The source is shown under each ID once the register has loaded.",
    },
    {
      id: "requirements-actions", route: ROUTE, target: "req-row-actions", placement: "left",
      title: "Corrections: Exclude, Edit, Split",
      body: [
        "A person corrects the register with three actions under a requirement: **Exclude: not a requirement**, **Edit** (wording or category) and **Split** (one item that holds several). **Merge** several selected rows and **Add** a missed requirement work the same way. Each action asks for a **reason** and is saved as a **correction**: a new version of the requirement with the old one kept, so the frozen version never changes silently.",
        "Corrections made after the freeze flow on to matching, the units and the compliance matrix like any other change, and stay in the history below.",
      ],
      fallback: "The correction actions are shown under the first requirement once the register has loaded.",
    },
    {
      id: "requirements-history", route: ROUTE, target: "req-action-history", placement: "left",
      title: "History",
      body: [
        "**History** opens every version of the requirement and a timeline: the original reading, each correction with who made it, when and why, and the frozen version it belongs to. It is read from the audit log, so it cannot be edited.",
      ],
      fallback: "The History link is under the status badge of a row.",
    },
    {
      id: "requirements-exceptions", route: ROUTE, target: "req-exceptions", placement: "left", onEnter: showTab("exceptions"),
      title: "Needs a source check",
      body: [
        "Each item shows the reader's wording and where it probably is (\"100% of its words are on page 21, lines 25-27\"). A person either **links it to the lines** (picking them on the RFP page in pane 1, which then verifies the quote) or **dismisses** it with a reason. Open items are counted on the Assessment Summary page as *Needs a source check* and as an open question for the go/no-go.",
      ],
      fallback: "The requirements that need a source check are on the Needs a source check tab of pane 2.",
    },
    {
      id: "requirements-add", route: ROUTE, target: "req-add-summary", placement: "top", onEnter: (ctx) => { showTab("register")(ctx); openDetails("req-add-summary")(ctx); },
      title: "Add a requirement the reader missed",
      body: [
        "**Add a requirement the agent missed**: select its lines on the RFP page (click and shift-click lines, or give the line numbers) and add it. The quote is taken verbatim from those lines, so it is anchored without anyone pasting text. The addition is saved as a correction with a reason and carries the tag *Correction*.",
      ],
      fallback: "The Add a requirement the agent missed section is at the bottom of pane 2.",
    },
    {
      id: "requirements-nominate", route: ROUTE, target: "trace-send-knowledge", placement: "left",
      title: "Nominate as a reviewed example",
      onEnter: (ctx) => { showTab("register")(ctx); ctx.el("req-row-first")?.click(); },
      body: [
        "The selected row carries **Nominate as a reviewed example**. A short form asks what the item teaches (requirement, preference, background, partial compliance, insufficient evidence), when it holds and when it does not. It then reads *Waiting for review*, and *Reviewed example* once approved in **Knowledge review** in My work. Nothing becomes reusable without that approval.",
      ],
      fallback: "Select a requirement in pane 2: the link appears under the selected row.",
    },
  ],
};
export default chapter;
