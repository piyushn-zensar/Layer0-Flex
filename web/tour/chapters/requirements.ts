// Walkthrough chapter 5: Requirements review and freezing (app/opportunities/[id]/requirements).  Owner: Piyush.
// Targets are data-tour ids on the requirements page and the line picker. The first row in view carries the
// row-level ids (req-row-*, req-action-*), so the action steps always work on the first line item "To review".
// The demo opportunity (OPP-0001) is already frozen: its action steps are skipped and the explain steps fall back.
import { openDetails, present, statusIn } from "../helpers";
import type { TourChapter, TourCtx, TourStep } from "../types";

const ROUTE = "/opportunities/{opp}/requirements";
/** After the freeze nothing on this page can change: action steps do not apply. */
const LOCKED = statusIn("frozen", "go", "no_go", "dispatched", "consolidating", "submitted");

type Field = HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
const field = (ctx: TourCtx, id: string) => ctx.el(id) as Field | null;
const tick = (ms = 150) => new Promise<void>((r) => setTimeout(r, ms));

/** Set a form control's value so React sees it: the native setter, then input and change events. */
const setValue = (el: Field | null, value: string) => {
  if (!el) return;
  const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype
    : el instanceof HTMLSelectElement ? HTMLSelectElement.prototype : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value")?.set?.call(el, value);
  el.dispatchEvent(new Event("input", { bubbles: true }));
  el.dispatchEvent(new Event("change", { bubbles: true }));
};

/** Wait until an element with this data-tour id is on the page (a details just opened, a fetch just finished). */
const waitFor = async (ctx: TourCtx, id: string, ms = 5000) => {
  const until = Date.now() + ms;
  while (!ctx.el(id) && Date.now() < until) await tick(100);
  return ctx.el(id);
};

/** The count on a filter chip ("Approved 12" -> 12); -1 while the page has not rendered the chips. */
const chipCount = (ctx: TourCtx, key: string) => {
  const m = /(\d+)\s*$/.exec((ctx.el(`req-filter-${key}`)?.textContent ?? "").trim());
  return m ? Number(m[1]) : -1;
};
const chipSelected = (ctx: TourCtx, key: string) => ctx.el(`req-filter-${key}`)?.getAttribute("aria-selected") === "true";

/** Show a filter: the one named, else the list the review works on ("To review", or "All" once frozen). */
const showList = (key?: string) => (ctx: TourCtx) => {
  const want = key ?? (ctx.el("req-baseline") ? "all" : "review");
  if (!chipSelected(ctx, want)) ctx.el(`req-filter-${want}`)?.click();
};
const clearSearch = (ctx: TourCtx) => { const s = field(ctx, "req-search"); if (s && s.value) setValue(s, ""); };

/** A chip count remembered the first time it can be read, so Previous / Next does not move the comparison point. */
const rememberCount = (ctx: TourCtx, key: string, chip: string) => {
  const kept = ctx.get<number>(key);
  if (kept !== undefined && kept >= 0) return kept;
  const now = chipCount(ctx, chip);
  if (now >= 0) ctx.set(key, now);
  return now;
};

/** The first row in view: its ID and short text, as the DOM shows them. */
const firstRow = (ctx: TourCtx) => {
  const id = ctx.el("req-row-id")?.textContent?.trim();
  const text = ctx.el("req-row-text")?.textContent?.trim();
  return id ? { id, text: text ?? "" } : undefined;
};

const explain = (s: Omit<TourStep, "route">): TourStep => ({ route: ROUTE, kind: "explain", ...s });
const action = (s: Omit<TourStep, "route" | "kind">): TourStep => ({ route: ROUTE, kind: "action", skipIf: LOCKED, ...s });

const chapter: TourChapter = {
  id: "requirements",
  order: 5,
  title: "Requirements review and freezing",
  summary: "Check the reader agent's line items against the RFP page they came from: approve, reject, edit, split, merge "
    + "and add what it missed. Then freeze baseline 1, the requirement set every later step works from.",
  entryRoute: ROUTE,
  steps: [
    explain({
      id: "requirements-intro",
      title: "The Requirements screen",
      body: [
        "This is where a person turns the reader agent's **proposals** into the opportunity's **requirements**. On the RFP step the agent "
        + "read the main document page by page and proposed one line item per obligation it found (for the Syracuse RFP: 814 line items, "
        + "21 of them marked as duplicates, 162 groups of related items, 348 requirements to decide). Nothing here was written by a person yet.",
        "Every line item carries the **exact words of the RFP** (the quote) and where they stand (page and lines). The agent never invents a "
        + "location: a quote it could not find on a page is shown as *unanchored* and the person checks it by hand. The reader runs offline from "
        + "frozen answers in this PoC, so a re-read gives the same proposals.",
        "What you do here: approve what is a real requirement, reject what is not (boilerplate, a heading, a duplicate), fix a short text, "
        + "split one item that holds several obligations, merge several that are one, and add anything the agent missed. "
        + "When every item is decided you **freeze the baseline**: the approved set becomes baseline 1 and later RFP changes run as a delta against it.",
        "Before leaving: every item decided, the baseline frozen. The next screens (Traceability, matching, the bid decision, the unit inboxes) "
        + "work only on frozen, approved requirements.",
      ],
      fallback: "The requirements table appears once the main RFP has been read on the RFP step.",
    }),
    explain({
      id: "requirements-head",
      title: "The header: counts, what is left, the Freeze button",
      target: "req-help",
      placement: "bottom",
      body: [
        "The line under the title counts the **active requirements** (not rejected, not replaced by a split or merge, duplicates left out) and "
        + "reminds you that related line items are grouped. On the right, **\"N still to decide\"** counts the items still *proposed*: the "
        + "**Freeze baseline** button stays disabled until that number is zero, and its tooltip says why.",
        "Once frozen, this line changes to *\"Baseline 1 frozen by Bid Manager (348 items)\"* with a link to the Changes step, and every "
        + "editing control on the page disappears: the checkboxes, the Actions column and the \"Add a requirement\" section.",
      ],
      fallback: "On a frozen opportunity the header shows the baseline line instead (\"Baseline 1 frozen by … (N items)\").",
    }),
    explain({
      id: "requirements-filters",
      title: "Filters and search",
      target: "req-filters",
      placement: "bottom",
      body: [
        "The chips filter the table by status; the number on each chip is the count over the whole list, whichever chip is active. "
        + "**To review** shows the items still *proposed*: it is the default while reviewing, and it empties as you decide. "
        + "**Approved** and **Rejected** hold your decisions. **Duplicates** are items the agent found twice (same quote): they stay out of the "
        + "way unless you approve one to keep it. **Ungrouped / split / merged** lists the originals that were replaced by new items. "
        + "**All** shows everything; it is the default once the baseline is frozen.",
        "**Unanchored** is special: it filters by provenance, not status, and shows the active items whose quote the reader could not find on a page "
        + "(32 of them in the Syracuse read). Each of those deserves a look at the source before approving.",
        "The search box matches the **ID, short text or quote** (case does not matter) inside the active filter; a group also matches when one of its "
        + "sub-requirements does. Example: `C37.20.7` finds the arc-resistance item on page 55.",
      ],
      fallback: "The filter chips sit above the table once requirements exist.",
    }),
    explain({
      id: "requirements-table",
      title: "The table, in document order",
      target: "req-table",
      placement: "top",
      body: [
        "Rows follow the **order of the RFP**: page, then line; items the reader could not place come last. A group sits just before its own "
        + "sub-requirements, so the page reads like the document does.",
        "Columns: a **checkbox** for bulk actions (while reviewing), **ID** with the category tag, **Source** (page and lines, or the unanchored badge), "
        + "**Requirement** (short text, quote, group toggle), **Status** with a History link, and **Actions**. The next steps take them one by one on the first row.",
        "Greyed rows are inactive (rejected, duplicate, replaced by a split or merge): they are kept for the record and never go to the units.",
      ],
      fallback: "The table appears once the RFP has been read.",
    }),
    explain({
      id: "requirements-col-id",
      title: "ID and category",
      target: "req-row-id",
      placement: "right",
      onEnter: showList(),
      body: [
        "IDs read `REQ-<opportunity number>-<running number>`, for example **REQ-0001-0333**. They are issued in reading order and **never reused**: "
        + "a split, a merge or an added item always gets the next free number, even after a re-read discarded drafts. Items created later by a split, "
        + "merge or grouping therefore carry higher numbers than their place in the document suggests.",
        "The tag under the ID is the **category** the reader assigned: `technical`, `compliance`, `commercial`, `schedule`, `submission`, `legal` or "
        + "`staffing`. It can be changed in Edit. The matching step uses it to tell product obligations from paperwork, so a wrong category is worth fixing.",
      ],
      fallback: "Each row starts with the ID (REQ-0001-0333 style) and the category tag.",
    }),
    explain({
      id: "requirements-col-source",
      title: "Source: page and lines",
      target: "req-row-source",
      placement: "right",
      body: [
        "**\"p. 1, line 5\"** or **\"p. 55, lines 52-53\"**: the page of the main RFP and the lines the quote was found on. The reader anchors a quote by "
        + "matching its normalised words against the page's text lines (rule R1: a location is found or left empty, never guessed). The link opens the "
        + "Traceability screen on that item, with the lines highlighted on the page image.",
        "When the quote could not be located the cell shows an **unanchored** badge instead (hover it for the reason). Such an item still has its quote, "
        + "and you can keep it; but there is no highlight behind it, so check it against the document yourself.",
      ],
      fallback: "The Source column shows the page and lines, or an unanchored badge.",
    }),
    explain({
      id: "requirements-col-text",
      title: "Short text and quote",
      target: "req-row-text",
      placement: "right",
      body: [
        "Each item has two texts. The **short text** (bold line) is the reader's one-sentence rendering of the obligation, for example "
        + "*\"Proposals must be submitted by September 15, 2023, 4pm.\"*; it is what the units see in their inbox and what you can edit (200 characters at most).",
        "The **quote** underneath, in quotation marks, is the RFP's own wording, verbatim: *\"Submission Deadline: September 15, 2023 by 4pm\"*. "
        + "It is never edited, because the source anchoring and the matcher's frozen answers are keyed on it. A merged item shows its quotes joined by \" … \"; "
        + "an item that came from a split or merge says *\"From REQ-…\"* under the text.",
      ],
      fallback: "The Requirement column shows the short text with the verbatim quote under it.",
    }),
    explain({
      id: "requirements-groups",
      title: "Groups and sub-requirements",
      target: "req-group-expand",
      placement: "right",
      onEnter: (ctx) => {
        const btn = ctx.el("req-group-expand");
        if (btn && btn.getAttribute("aria-expanded") !== "true") btn.click();
        btn?.scrollIntoView({ block: "center", behavior: "smooth" });
      },
      body: [
        "After reading, a **grouping agent** looked at each page and gathered line items that are parts of one obligation (a list of standards, the "
        + "parts of one submission package) into a **group**: one requirement with a title such as *\"Submission requirements for proposals\"* and "
        + "its members as **sub-requirements**. A group needs at least two members and never crosses a page; the agent never rewrites or drops an item.",
        "The **\"▸ N sub-requirements\"** toggle expands a group; the indented rows are its members, each with its own quote and lines. The group keeps all "
        + "their highlights. **A decision on the group covers its members**: approving a group approves its undecided sub-requirements, rejecting it rejects "
        + "all of them, and approving a rejected group restores them.",
        "Groups and sub-requirements cannot be split or merged; **Ungroup** releases the members as stand-alone requirements (the group row becomes "
        + "inactive, status *split*). The units answer a group as one work item, so keep groups where one answer fits all members.",
      ],
      fallback: "A group row shows a \"▸ N sub-requirements\" toggle; none is in the current view.",
    }),
    explain({
      id: "requirements-unanchored",
      title: "Unanchored items",
      target: "req-badge-unanchored",
      placement: "right",
      onEnter: showList("unanchored"),
      body: [
        "This view holds the active items whose quote was **not found on any page**, so the Source cell shows a badge instead of page and lines. "
        + "Typical causes: the reader paraphrased instead of quoting, the text runs across two pages, or a table cell was read in another order. "
        + "Example from the Syracuse read: *\"Non-compliance may lead to penalties or contract enforcement\"*.",
        "What to do: open the RFP (Traceability) and look for the passage. If it is real, approve it: it stays in the baseline without a highlight. "
        + "If you want an exact source, reject it and add the passage again with the line picker below the table, which anchors it to the lines you select. "
        + "If it is not a requirement, reject it.",
      ],
      fallback: "No unanchored item is in view: every quote of this opportunity was located on a page.",
    }),
    explain({
      id: "requirements-duplicates",
      title: "Duplicates",
      target: "req-row-duplicate",
      placement: "right",
      onEnter: showList("duplicates"),
      body: [
        "While reading, the same obligation is sometimes proposed twice (an RFP repeats itself, or a passage was read in two chunks). Items whose quote "
        + "equals an earlier one are marked **duplicate** and listed here with *\"Duplicate of REQ-…\"*. They are inactive: not counted, not frozen, not sent to units.",
        "Nothing to do for them normally. If the repeat is deliberate in the RFP and you want it answered separately, **Approve** restores it as a "
        + "requirement in its own right. In the Syracuse read 21 items are duplicates.",
      ],
      fallback: "No duplicates were found in this opportunity.",
    }),
    explain({
      id: "requirements-status",
      title: "Status badges",
      target: "req-row-status",
      placement: "left",
      onEnter: showList(),
      body: [
        "**proposed**: the reader's draft, waiting for a decision. **approved**: part of the next baseline. **rejected**: kept for the record only; it can be "
        + "approved again (restored) until the freeze. **duplicate**: same quote as an earlier item. **split** and **merged**: replaced by new items "
        + "(a group that was ungrouped is also *split*). After a change document, **removed** marks an item the customer deleted.",
        "Every change of status is written to the audit log with who did it and when; **History** next to the badge shows that record for the row.",
      ],
      fallback: "The Status column shows one badge per row and a History link.",
    }),
    explain({
      id: "requirements-actions",
      title: "Per-row actions",
      target: "req-row-actions",
      placement: "left",
      body: [
        "**Approve** and **Reject** decide the item; the same click twice changes nothing and writes no event. A rejected item keeps an Approve button, "
        + "so a decision can be reversed until the freeze. **Edit** opens the short text and category in place (Save or Cancel). "
        + "**Split** turns one item into several, one quote per line. A group shows **Ungroup** instead of Split.",
        "Merging is done from the **bulk bar**: select two or more items with the checkboxes and choose *Merge into one*. All of this is refused once the "
        + "baseline is frozen; after that, requirements change only through a change document on the Changes step.",
      ],
      fallback: "The Actions column is shown while the opportunity is in review; it disappears after the freeze.",
    }),
    action({
      id: "requirements-approve",
      title: "Approve one item",
      target: "req-action-approve",
      placement: "left",
      onEnter: (ctx) => { showList("review")(ctx); rememberCount(ctx, "req.approvedBefore", "approved"); },
      body: [
        "The first item to review is the submission deadline (*\"Proposals must be submitted by September 15, 2023, 4pm.\"*, p. 1, line 5, category "
        + "`schedule`). Its quote matches the page, the category fits, the short text is a fair rendering: a real requirement.",
        "Approving records an `approve` event by the acting person (the Bid Manager here) and moves the row out of *To review* into *Approved*. "
        + "The chip counts update at once; the \"still to decide\" count in the header drops by one.",
      ],
      instruction: "Press Approve on the first row.",
      done: (ctx) => { const before = rememberCount(ctx, "req.approvedBefore", "approved"); return before >= 0 && chipCount(ctx, "approved") > before; },
      fallback: "No row with an Approve button is in view; choose the To review filter.",
    }),
    action({
      id: "requirements-reject",
      title: "Reject one item",
      target: "req-action-reject",
      placement: "left",
      onEnter: (ctx) => { showList("review")(ctx); rememberCount(ctx, "req.rejectedBefore", "rejected"); },
      body: [
        "Rejecting is for line items that are not obligations on the bidder: a heading the reader took for a sentence, a note to the Authority's own staff, "
        + "a duplicate it did not catch. The item is kept, greyed out, under *Rejected*; it is never frozen and never dispatched.",
        "For the exercise, reject the first row now (it is a real requirement, so the next step restores it). Nothing is lost: a rejected item keeps "
        + "its Approve button until the freeze.",
      ],
      instruction: "Press Reject on the first row.",
      done: (ctx) => { const before = rememberCount(ctx, "req.rejectedBefore", "rejected"); return before >= 0 && chipCount(ctx, "rejected") > before; },
      fallback: "No row with a Reject button is in view; choose the To review filter.",
    }),
    action({
      id: "requirements-restore",
      title: "Restore it: approve the rejected item",
      target: "req-action-approve",
      placement: "left",
      onEnter: (ctx) => { showList("rejected")(ctx); rememberCount(ctx, "req.rejectedAtRestore", "rejected"); },
      body: [
        "The **Rejected** view shows the item you just rejected, with its Approve button. Approving a rejected item **restores** it: status *approved*, "
        + "a second event in its history (`reject`, then `approve`), the same ID. For a rejected group this also restores the sub-requirements that were "
        + "rejected with it.",
        "This is how a wrong decision is undone before the freeze; after the freeze a decision can only be revisited through a change document.",
      ],
      instruction: "Press Approve on the row in the Rejected view.",
      done: (ctx) => { const at = rememberCount(ctx, "req.rejectedAtRestore", "rejected"); return at > 0 && chipCount(ctx, "rejected") < at; },
      fallback: "The Rejected view is empty: nothing to restore.",
    }),
    action({
      id: "requirements-edit",
      title: "Edit a short text",
      target: "req-action-edit",
      placement: "bottom", // the form opens in the row itself, left of the button: keep the bubble off it
      onEnter: (ctx) => {
        showList("review")(ctx);
        if (!ctx.get("req.editRow") && chipSelected(ctx, "review")) { const row = firstRow(ctx); if (row) ctx.set("req.editRow", row); }
      },
      body: [
        "**Edit** opens the short text and the category in the row. Change only the **short text** here: it is what the units read, so make it a clear "
        + "one-line obligation. The quote is not editable and the category should stay as it is (the matcher's frozen answers are keyed on category and quote).",
        "The first row now is *\"All inquiries must be sent via email to bids@syrairport.org.\"* (p. 1, lines 12-13). A tighter wording: "
        + "**Send every inquiry by email only, to bids@syrairport.org.** Save writes an `edit` event with the text before and after, and History then lists "
        + "two versions (*original* and *edited*). A Save that changes nothing writes nothing.",
      ],
      instruction: "Press Edit on the first row, change the short text, then press Save.",
      example: {
        label: "Fill in the example wording",
        apply: async (ctx) => {
          if (!ctx.el("req-edit-text")) { ctx.el("req-action-edit")?.click(); await waitFor(ctx, "req-edit-text", 2000); }
          const el = field(ctx, "req-edit-text");
          if (!el) return;
          const id = ctx.el("req-row-id")?.textContent?.trim() ?? "";
          const text = id.endsWith("-0003") ? "Send every inquiry by email only, to bids@syrairport.org."
            : `${el.value.replace(/\.\s*$/, "")} (wording checked against the source).`;
          setValue(el, text);
          el.focus();
        },
      },
      done: (ctx) => {
        let kept = ctx.get<{ id: string; text: string }>("req.editRow");
        if (!kept && chipSelected(ctx, "review") && !ctx.el("req-edit-form")) { kept = firstRow(ctx); if (kept) ctx.set("req.editRow", kept); return false; }
        const now = firstRow(ctx);
        return !!kept && !!now && now.id === kept.id && now.text !== "" && now.text !== kept.text;
      },
      fallback: "No editable row is in view; choose the To review filter.",
    }),
    explain({
      id: "requirements-split",
      title: "Split: one item, several obligations",
      target: "req-action-split",
      placement: "left",
      onEnter: showList(),
      body: [
        "When one line item holds two or more obligations (\"The switchgear shall be arc-resistant Type 2B. The switchgear shall meet IEEE C37.20.7.\"), "
        + "**Split** opens the quote in a text box: put **each part on its own line** and press Split. Each part becomes a new item with the next free ID, "
        + "the same category and page, *\"From REQ-…\"* under its text, and is **anchored again** on the page from its own words. The original turns *split* (inactive).",
        "Rules: at least two non-empty lines; a part that is not found on the page becomes unanchored; the new items are *proposed*, so decide them as well. "
        + "Sub-requirements and groups cannot be split. Nothing to split in this walkthrough; the line items of the Syracuse read are already one obligation each.",
      ],
      fallback: "Split appears on stand-alone items while reviewing; none is in view.",
    }),
    explain({
      id: "requirements-select",
      title: "Checkboxes and Select all",
      target: "req-select-all",
      placement: "right",
      body: [
        "Each active, top-level row has a **checkbox**; the box in the table header **selects every selectable row in the current view** (the active filter "
        + "and search), and clears them again. Selection is how you act on many items at once and how you **merge**. Sub-requirements are selected through "
        + "their group; inactive rows cannot be selected.",
        "Tip: filter first, then select all. *To review* plus Select all selects exactly what is still undecided, which is what the final approval step uses. "
        + "A search narrows the selection the same way (for example every item that mentions `AutoCAD`).",
      ],
      fallback: "The checkbox column is shown while the opportunity is in review.",
    }),
    explain({
      id: "requirements-bulkbar",
      title: "The bulk bar: approve, reject, merge",
      target: "req-bulkbar",
      placement: "bottom",
      onEnter: (ctx) => {
        showList("review")(ctx);
        if (!ctx.el("req-bulkbar")) { const box = field(ctx, "req-row-check") as HTMLInputElement | null; if (box && !box.checked) box.click(); }
      },
      body: [
        "As soon as something is selected a bar appears above the table: **\"N selected\"**, **Approve**, **Reject**, **Merge into one**, **Clear**. "
        + "Approve and Reject send one review call per item (the toast then says *\"N line items approved.\"*). Clear drops the selection.",
        "**Merge into one** needs at least two stand-alone items **on the same page**: it opens a field for the one-line text of the merged requirement; "
        + "the result gets a new ID, the quotes joined by \" … \", all the highlights, the first item's category, and *\"From REQ-…, REQ-…\"* under its text. "
        + "The originals turn *merged*. Groups and sub-requirements cannot be merged (ungroup first); items on different pages are refused with a clear message.",
        "The row ticked here was selected to show the bar; the next step clears it.",
      ],
      fallback: "The bulk bar appears while reviewing, as soon as one row is selected.",
    }),
    action({
      id: "requirements-history-open",
      title: "Open the history of a line item",
      target: "req-action-history",
      placement: "left",
      onEnter: (ctx) => { ctx.el("req-bulk-clear")?.click(); showList("review")(ctx); },
      skipIf: undefined, // History works after the freeze too
      body: [
        "Every row has a **History** link next to its status badge. It opens a panel under the row with two parts: the **versions** of the wording and the "
        + "**timeline** of everything that happened to the item. Both are rebuilt from the append-only audit log, which is the source of truth; nothing here can be edited.",
        "Open it for the first row, which you edited a moment ago, so that two versions show. On the demo opportunity any row will do.",
      ],
      instruction: "Press History on the first row.",
      done: present("req-history"),
      fallback: "A History link sits next to every status badge.",
    }),
    explain({
      id: "requirements-history-versions",
      title: "Versions",
      target: "req-history-versions",
      placement: "top",
      body: [
        "**Versions (N)** lists the wording over time: *v1 · original by reader agent (Bid Manager)*, then one entry per Edit that changed the text or the "
        + "category (*edited by Bid Manager*), with the date and, later, one per revision by a change document (*revised*, with the document as reason). "
        + "Under the list: the **source** (page and lines) and the verbatim quote, and *\"Created from …\"* for an item that came from a split or merge.",
        "This is the answer to \"who changed this requirement, and what did it say before?\": useful in a dispute with a unit, or when an addendum modifies "
        + "an item and you want to see the chain.",
      ],
      fallback: "The Versions list is the left part of an open History panel.",
    }),
    explain({
      id: "requirements-history-timeline",
      title: "Timeline",
      target: "req-history-timeline",
      placement: "top",
      body: [
        "The **Timeline** is every audit event on the item in order: `proposed` (with provenance and category), `approve`, `reject`, `edit`, `split` "
        + "(with the new IDs), `merged into`, `duplicate of`, `grouped`, each **baseline** it was frozen into (`frozen`, with the count), and after a change "
        + "document `revised` or `removed`. Each line names the person or agent and the time.",
        "Press History again to close the panel. The panel is read-only; the same data backs the audit views elsewhere in the application.",
      ],
      fallback: "The Timeline is the right part of an open History panel.",
    }),
    explain({
      id: "requirements-add-intro",
      title: "Add a requirement the agent missed",
      target: "req-add-summary",
      placement: "top",
      onEnter: (ctx) => {
        const history = ctx.el("req-action-history");
        if (history?.getAttribute("aria-expanded") === "true") history.click(); // close the panel opened above
        openDetails("req-add-summary")(ctx);
      },
      body: [
        "The reader is good but not complete. Below the table a collapsible section lets a person add what it missed, in two ways: **select the lines on the "
        + "RFP page** (the quote is those lines, verbatim, so the source is exact), or **paste the quote** (the system then searches the pages for it). "
        + "Either way the new item arrives as *proposed*, with the next free ID, and is reviewed like the others.",
        "A re-read of the RFP is refused once review has started (it would discard decisions), so this section is the only way to add before the freeze. "
        + "After the freeze, additions come through a change document on the Changes step.",
      ],
      fallback: "The \"Add a requirement the agent missed\" section sits under the table while reviewing; after the freeze it is gone.",
    }),
    explain({
      id: "requirements-lp-pager",
      title: "The line picker: choosing the page",
      target: "lp-pager",
      placement: "bottom",
      onEnter: async (ctx) => { openDetails("req-add-summary")(ctx); await waitFor(ctx, "lp-pager"); ctx.el("lp-pager")?.scrollIntoView({ block: "center", behavior: "smooth" }); },
      body: [
        "The picker shows one page of the main RFP as an image with its text lines laid over it. The **pager** moves through the document: ◀ ▶ or type a page "
        + "number (1 to 101 for the Syracuse RFP). It opens on the page of a selected requirement, else on the page of the first row in view.",
        "A page with no text layer (a scanned drawing) shows *\"No text layer: this page was not read (needs OCR)\"*: nothing can be selected there. "
        + "The page image comes from the same rendering the Traceability screen uses.",
      ],
      fallback: "The line picker loads once the section is open and the main RFP has been read.",
    }),
    explain({
      id: "requirements-lp-lines",
      title: "Selecting lines on the page",
      target: "lp-page",
      placement: "right",
      body: [
        "Every text line of the page is a clickable box. **Click the first line** of the requirement, then **shift-click its last line**: the range is selected. "
        + "A plain click starts a new range. Hover a box to read its line number and text.",
        "Colours (see the legend under the page): **blue** is your selection; **yellow** lines are already covered by an active requirement, so adding them again "
        + "makes a second item for the same words; **grey** lines are page furniture (headers and footers repeated on at least three pages, such as "
        + "*\"Specification for Metal Clad Switchgear\"* or *\"Page 3 of 19\"*): they can be inside a range but are **left out of the quote**, as the reader leaves them out.",
      ],
      fallback: "The page image with its selectable lines is the left part of the line picker.",
    }),
    explain({
      id: "requirements-lp-range",
      title: "From line / To line",
      target: "lp-range",
      placement: "left",
      body: [
        "The two number fields are the keyboard way to select, and they mirror your clicks. **From line** alone selects one line; **To line** extends it. "
        + "Line numbers are those of the page (page 55 has 72 lines, numbered from the header). **Clear** empties the selection.",
        "Checks, shown in orange as you type: numbers start at 1; the first line must come before the last; the range must exist on the page "
        + "(*\"Page 55 has 72 lines.\"*); **at most 40 lines** (a requirement is a sentence or a paragraph, not a page: split a longer passage into several); "
        + "and a range made only of header or footer lines is refused. The Add button stays disabled while a check fails.",
      ],
      fallback: "The From line / To line fields are in the form beside the page.",
    }),
    explain({
      id: "requirements-lp-preview",
      title: "The quote that will be stored",
      target: "lp-preview",
      placement: "left",
      body: [
        "Once a range is valid the form shows **\"Quote that will be stored (p. 55, lines 52-53)\"** and the text, built from the selected body lines joined by "
        + "a space: that exact string becomes the item's quote and it is **anchored to those lines only**, never to the same words elsewhere in the document. "
        + "So an item added this way is always *EXTRACTED*, with a highlight in Traceability.",
        "Under it: **Short text** (optional, 200 characters at most; the quote is used when left empty) and **Category**. Then **Add requirement**.",
      ],
      fallback: "The quote preview appears under the line fields once a valid range is selected.",
    }),
    action({
      id: "requirements-lp-add",
      title: "Add an item from page 55, lines 52-53",
      target: "lp-add",
      placement: "left",
      onEnter: async (ctx) => { openDetails("req-add-summary")(ctx); await waitFor(ctx, "lp-add"); ctx.el("lp-side")?.scrollIntoView({ block: "center", behavior: "smooth" }); },
      body: [
        "Example: page 55 of the Syracuse RFP, lines 52-53: *\"Switchgear shall be Arc-resistant Type 2B. The switchgear shall meet or exceed the most "
        + "conservative interpretation of standard IEEE C37.20.7.\"* Go to page 55, select lines 52 and 53 (click 52, shift-click 53, or type them), "
        + "give a short text, and press **Add requirement**.",
        "You will notice the lines are already **yellow**: the reader did capture them (as REQ-…-0333, category `compliance`). Adding them again is what a person "
        + "would do for a passage the reader missed; here it makes a second item for the same words, which the next steps reject again so the approved set stays "
        + "as the reader proposed it (the product matcher's frozen answers depend on that).",
        "The green message *\"REQ-… added (p. 55, lines 52-53); it is in the list, to review like the others.\"* confirms it; the table reloads with the new row.",
      ],
      instruction: "Set page 55, lines 52 to 53, then press Add requirement.",
      example: {
        label: "Page 55, lines 52-53",
        apply: async (ctx) => {
          openDetails("req-add-summary")(ctx);
          const pageInput = await waitFor(ctx, "lp-page-input");
          if (!pageInput) return;
          setValue(pageInput as HTMLInputElement, "55");
          await tick(200);
          setValue(field(ctx, "lp-from"), "52");
          setValue(field(ctx, "lp-to"), "53");
          setValue(field(ctx, "lp-text"), "Arc-resistant Type 2B switchgear per IEEE C37.20.7 (added by hand).");
          setValue(field(ctx, "lp-category"), "compliance");
          ctx.el("lp-side")?.scrollIntoView({ block: "center", behavior: "smooth" });
        },
      },
      done: (ctx) => {
        if (ctx.get("req.addedId")) return true;
        const m = /REQ-\d+-\d+/.exec(ctx.el("lp-added")?.textContent ?? "");
        if (!m) return false;
        ctx.set("req.addedId", m[0]);
        return true;
      },
      fallback: "The Add requirement button is in the line picker form, under the quote preview.",
    }),
    explain({
      id: "requirements-lp-result",
      title: "What was added",
      target: "lp-added",
      placement: "left",
      body: [
        "The new item got the **next free ID** (it was never used, even by a discarded draft), the source **p. 55, lines 52-53**, provenance *EXTRACTED*, "
        + "status **proposed**, and *Bid Manager* as its author in History (`proposed` event). It sits in the table at its place in document order, between the "
        + "other page 55 items, and in the *To review* filter. On the page the two lines are now covered twice.",
        "Limits worth knowing: one item lives on one page (a passage over a page break is two items); 40 lines at most; the quote is exactly the lines, so a "
        + "sentence that starts mid-line brings the whole line with it. The short text is yours to tidy.",
      ],
      fallback: "After an add, a green confirmation names the new ID and its source.",
    }),
    action({
      id: "requirements-reject-added",
      title: "Reject the added item again",
      target: "req-action-reject",
      placement: "left",
      onEnter: async (ctx) => {
        showList("review")(ctx);
        const id = ctx.get<string>("req.addedId");
        if (id) { await tick(100); setValue(field(ctx, "req-search"), id); }
        ctx.el("req-table")?.scrollIntoView({ block: "start", behavior: "smooth" });
      },
      body: [
        "The search box now holds the new ID, so the table shows only that row (search works inside the active filter, *To review*). Reject it: the words of "
        + "page 55, lines 52-53 stay covered by the reader's own item, and the approved set of that page is unchanged, which keeps the product matcher's frozen "
        + "answers valid in the next chapter.",
        "In real use you would of course keep what you added; the reject here is only to leave the demo data as the reader proposed it.",
      ],
      instruction: "Press Reject on the row shown.",
      done: async (ctx) => {
        const id = ctx.get<string>("req.addedId");
        if (!id) return true;
        try {
          const h = await ctx.api<{ events: { action: string }[] }>(`/api/requirements/${id}/history`);
          return h.events.some((e) => e.action === "reject");
        } catch { return false; }
      },
      fallback: "The added item is found by typing its ID in the search box; reject it from its row.",
    }),
    explain({
      id: "requirements-paste",
      title: "The other way: paste the quote",
      target: "req-paste-form",
      placement: "top",
      onEnter: (ctx) => { clearSearch(ctx); openDetails("req-paste-form")(ctx); },
      body: [
        "When the passage is easier to copy than to point at (from a PDF viewer, an e-mail with the RFP text), paste it in **Quote, copied from the RFP**. "
        + "On Add, the system **searches the pages for those words** (normalised: case, spaces and curly quotes do not matter; a trailing full stop is forgiven) "
        + "and anchors the item where it finds them; the optional **Page** field says where to look first. If the words are not found the item is still created, "
        + "as *unanchored*: you can keep it, or redo it with the line picker.",
        "**Short text** is optional (the quote is used when empty, cut at 200 characters) and **Category** is required. *Use example* fills the form with "
        + "line 37 of page 55 (*\"Drawings, instructions, and test reports shall be in English.\"*); you do not need to press Add. If you do, reject the new "
        + "item afterwards, as you just did for the line-picker one.",
      ],
      example: {
        label: "Fill in the example (page 55, line 37)",
        apply: async (ctx) => {
          openDetails("req-paste-form")(ctx);
          await tick(100);
          setValue(field(ctx, "req-paste-quote"), "All drawings, instructions, and test reports shall be in English.");
          setValue(field(ctx, "req-paste-text"), "Provide drawings, instructions and test reports in English.");
          setValue(field(ctx, "req-paste-category"), "submission");
          setValue(field(ctx, "req-paste-page"), "55");
          ctx.el("req-paste-form")?.scrollIntoView({ block: "center", behavior: "smooth" });
        },
      },
      fallback: "The paste form is the second part of the \"Add a requirement\" section, shown while reviewing.",
    }),
    action({
      id: "requirements-select-all",
      title: "Select everything that is left",
      target: "req-select-all",
      placement: "bottom",
      onEnter: (ctx) => { clearSearch(ctx); showList("review")(ctx); ctx.el("req-table")?.scrollIntoView({ block: "start", behavior: "smooth" }); },
      body: [
        "In a real review every item gets a look. For the walkthrough, accept the reader's remaining proposals in one go. First the selection: with *To review* "
        + "active, the header checkbox selects every undecided item in view (about 346 in this walkthrough; sub-requirements go with their group), and the "
        + "bulk bar appears above the table with the count.",
        "Duplicates are not in this view, so they stay duplicates; the item you rejected stays rejected.",
      ],
      instruction: "Tick the header checkbox.",
      done: (ctx) => { const bar = ctx.el("req-bulkbar"); return !!bar && /(\d+) selected/.test(bar.textContent ?? "") && Number(/(\d+) selected/.exec(bar.textContent ?? "")![1]) > 1; },
      fallback: "The header checkbox is shown while the opportunity is in review.",
    }),
    action({
      id: "requirements-approve-all",
      title: "Approve everything that is left",
      target: "req-bulk-approve",
      placement: "bottom",
      onEnter: (ctx) => { if (!ctx.el("req-bulkbar")) { showList("review")(ctx); const box = field(ctx, "req-select-all") as HTMLInputElement | null; if (box && !box.checked) box.click(); } },
      body: [
        "**Approve** in the bulk bar sends one review call per selected item, each written to the audit log by the acting person. Expect a few seconds and the toast "
        + "*\"N line items approved.\"*; the *To review* chip then reads 0 and *\"still to decide\"* disappears from the header, which enables **Freeze baseline**.",
        "Groups are approved with their undecided sub-requirements. Nothing is sent to anyone yet: approval only says which line items are real requirements.",
      ],
      instruction: "Press Approve in the bulk bar.",
      done: (ctx) => chipCount(ctx, "review") === 0,
      fallback: "The bulk bar with its Approve button appears above the table as soon as rows are selected.",
    }),
    action({
      id: "requirements-freeze",
      title: "Freeze the baseline",
      target: "req-freeze",
      placement: "bottom",
      body: [
        "With nothing left to decide the **Freeze baseline** button is enabled. It opens a confirmation: *\"The 348 approved requirements become the baseline "
        + "the units work from. Later changes to the RFP run as a delta against it.\"*, with **Cancel** and **Freeze baseline**. Freezing needs a read main RFP, "
        + "every item decided and at least one approved item; otherwise the API refuses with the reason.",
        "On confirm, every approved requirement (and the approved sub-requirements of approved groups) is stamped **baseline 1**, a `frozen` event is written, "
        + "the opportunity's status becomes **frozen** (the stepper updates at once), and this page becomes read-only. There is exactly one freeze; from now on "
        + "requirements change only through a change document, which produces baseline 2, 3, …",
      ],
      instruction: "Press Freeze baseline, then confirm in the dialog.",
      done: present("req-baseline"),
      fallback: "The Freeze baseline button is in the header while the opportunity is in review.",
    }),
    explain({
      id: "requirements-frozen",
      title: "The frozen state",
      target: "req-baseline",
      placement: "bottom",
      onEnter: showList("all"), // the "To review" chip chosen for the approvals would show an empty table now
      body: [
        "The header now reads **\"Baseline 1 frozen by Bid Manager (348 items)\"**: the baseline number, who froze it, and the number of top-level requirements "
        + "in it (sub-requirements count with their group). The link goes to the Changes step, where an addendum is compared with this baseline.",
        "What changed on the page: the default filter is **All**; the checkbox and Actions columns are gone, and so is the \"Add a requirement\" section. "
        + "Filters, search and History still work; the Source links still open Traceability. Every write to a requirement is now refused with "
        + "*\"Requirements are frozen in baseline 1; later changes go through the changes module.\"*",
        "Next: the **Traceability** screen shows each frozen requirement on its page, and the product matcher proposes which unit and product answer it.",
      ],
      fallback: "Once frozen, the header shows the baseline number, who froze it and the item count.",
    }),
  ],
};

export default chapter;
