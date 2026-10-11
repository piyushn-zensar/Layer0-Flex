// Walkthrough chapter 4: New opportunity and the RFP documents page (web/app/opportunities/new, web/app/opportunities/[id]).
// Owner: G1 (overview and intake). Creates "Walkthrough: Syracuse switchgear" and stores its id in ctx.oppId; the person
// may instead choose the demo opportunity (ctx data "demo" = true, oppId = DEMO_OPP) and the creation steps are skipped.
import type { TourChapter, TourCtx } from "../types";
import { DEMO_OPP } from "../types";
import { openDetails, statusIn } from "../helpers";

type Field = HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
type Detail = { opportunity: { id: string; status: string }; documents: { id: string; role: string; status: string; page_count: number }[] };

/** Set a form control the way a person would, so React (uncontrolled or controlled) sees the value. */
function setValue(el: Field | null | undefined, value: string) {
  if (!el) return;
  const proto = el instanceof HTMLSelectElement ? HTMLSelectElement.prototype
    : el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value")?.set?.call(el, value);
  el.dispatchEvent(new Event(el instanceof HTMLSelectElement ? "change" : "input", { bubbles: true }));
}
/** The control inside (or at) a data-tour element. */
const field = (ctx: TourCtx, tourId: string): Field | null => {
  const el = ctx.el(tourId);
  if (!el) return null;
  return el.matches("input, select, textarea") ? (el as Field) : el.querySelector<Field>("input, select, textarea");
};
const demo = (ctx: TourCtx) => ctx.get<boolean>("demo") === true;
const detail = async (ctx: TourCtx) => { try { return await ctx.api<Detail>(`/api/opportunities/${ctx.oppId}`); } catch { return null; } };
const mainDoc = async (ctx: TourCtx) => (await detail(ctx))?.documents.find((d) => d.role === "main") ?? null;
const READ_STATUSES = ["review", "frozen", "go", "no_go", "dispatched", "consolidating", "submitted"];
/** The page does not poll: when the API says the main RFP is ingested but the table still shows an older status
 * (the sample is read from the frozen layout in a few seconds), press Refresh status so the search card and the
 * reader-agent button appear. Returns true when the main document is ingested. */
const syncDocs = async (ctx: TourCtx) => {
  const d = await mainDoc(ctx);
  if (d?.status !== "ingested") return false;
  const shown = (ctx.el("rfp-doc-status")?.textContent ?? "").toLowerCase();
  if (!shown.includes("ingested")) { ctx.set("rfpRefreshed", true); ctx.el("rfp-refresh")?.click(); }
  return true;
};

const chapter: TourChapter = {
  id: "intake",
  order: 4,
  title: "New opportunity and the RFP",
  summary: "Create the walkthrough opportunity, attach the Syracuse RFP, watch it being read into a page-and-line layout, then run the reader agent that turns 101 pages into requirements.",
  entryRoute: "/opportunities/new",
  steps: [
    {
      id: "intake-intro",
      title: "New opportunity: one workspace per RFP",
      route: "/opportunities/new",
      target: "intake-form",
      placement: "right",
      body: [
        "An opportunity is the container for everything about one RFP: its documents, the requirements read out of them, the matches to business units, the bid decision, the units' answers, the final response and later changes. It is kept for the life of the project.",
        "Creating one is a single form: `POST /api/opportunities` with a title, an optional customer and a customer type. The server allocates the next free ID (`OPP-0003` if two exist), records who created it (the \"Acting as\" person, sent as the `X-Actor` header) and starts it in status **new**.",
        "On success you land on the opportunity's RFP documents page; nothing is read until a main RFP is attached there.",
      ],
    },
    {
      id: "intake-choose",
      title: "Two ways to follow along",
      route: "/opportunities/new",
      target: "intake-form",
      placement: "right",
      body: [
        "The walkthrough prefers to **create its own opportunity**, \"Walkthrough: Syracuse switchgear\", and attach the bundled Syracuse RFP. Reading it works offline from frozen answers and takes about a minute; the rest of the walkthrough then runs on your copy, so approving, freezing, deciding and dispatching are yours to do.",
        "If you would rather not create anything, press **Use the demo opportunity instead**: the walkthrough switches to OPP-0001, which is already frozen, decided and dispatched. Steps that need an earlier state are skipped or explain what they would do. (Chapter 11, Changes, always uses OPP-0001 either way.)",
        "To create your own, just press Next.",
      ],
      example: {
        label: "Use the demo opportunity instead",
        apply: (ctx) => { ctx.set("demo", true); ctx.set("oppId", DEMO_OPP); ctx.oppId = DEMO_OPP; },
      },
    },
    {
      id: "intake-title",
      title: "Title",
      route: "/opportunities/new",
      target: "intake-title",
      placement: "right",
      skipIf: demo,
      body: [
        "The **title** is required (blank or whitespace is refused before any request is sent: \"A title is required.\"). It is trimmed and becomes the heading of every page inside the opportunity and the Title column of the Opportunities table. Keep it short and recognisable: the RFP's own name or number works well.",
        "**Use example** fills all three fields for the walkthrough: title \"Walkthrough: Syracuse switchgear\", customer \"Syracuse Regional Airport Authority\", type \"public sector\".",
      ],
      example: {
        label: "Fill the form for the walkthrough",
        apply: (ctx) => {
          setValue(field(ctx, "intake-title"), "Walkthrough: Syracuse switchgear");
          setValue(field(ctx, "intake-customer"), "Syracuse Regional Airport Authority");
          setValue(field(ctx, "intake-customer-type"), "public sector");
        },
      },
    },
    {
      id: "intake-customer",
      title: "Customer",
      route: "/opportunities/new",
      target: "intake-customer",
      placement: "right",
      skipIf: demo,
      body: [
        "**Customer** is optional. It is stored on the opportunity, shown in the Opportunities table (\"not set\" when empty) and repeated in the help line of the RFP documents page together with the customer type.",
        "It carries no behaviour in this PoC: matching, routing and the go/no-go evidence read the RFP and the catalog, not this field. Treat it as the label people will search for later.",
      ],
    },
    {
      id: "intake-customer-type",
      title: "Customer type",
      route: "/opportunities/new",
      target: "intake-customer-type",
      placement: "right",
      skipIf: demo,
      body: [
        "**Customer type** is one of six segments: *utility*, *hyperscaler*, *neocloud*, *colocation*, *silicon provider*, *public sector*, or left as \"—\". The Syracuse airport authority is *public sector*; the hyperscale sample is *hyperscaler*.",
        "Like the customer it is recorded and displayed (opportunity header, Opportunities table) but does not change what the agents do. It is there so the portfolio can be read by segment and so a later version can use it, for example to pick default participating units.",
      ],
    },
    {
      id: "intake-create",
      title: "Create the opportunity",
      route: "/opportunities/new",
      target: "intake-create",
      placement: "right",
      kind: "action",
      skipIf: demo,
      instruction: "Press Create. The page moves to the new opportunity's RFP documents page.",
      fallback: "The Create button is at the bottom of the form.",
      body: [
        "Pressing **Create** posts the form. While the request runs the fields and the button are disabled (\"Creating…\") so a second click cannot create a duplicate; an error from the API is shown under the form and the values stay.",
        "The walkthrough reads the new ID from the URL (`/opportunities/OPP-00xx`) and uses it for every later chapter.",
      ],
      done: (ctx) => {
        const m = ctx.pathname.match(/^\/opportunities\/(OPP-\d{4})$/);
        if (!m) return false;
        if (ctx.oppId !== m[1]) { ctx.oppId = m[1]; ctx.set("oppId", m[1]); }
        return true;
      },
    },
    {
      id: "intake-rfp-intro",
      title: "RFP documents: step 1 of the workflow",
      route: "/opportunities/{opp}",
      target: "rfp-docs-table",
      placement: "bottom",
      body: [
        "This is the first step in the opportunity header's stepper (RFP → Requirements → Traceability → Bid decision → Final response, plus Changes). Its job: receive the RFP files, read them into a **layout model** (every line with its page, line number and box on the page) and then let the **reader agent** break the main RFP into requirement line items.",
        "The help line repeats the customer and customer type you entered. Below it: the documents table, the upload form, a search box over the read RFP, and the button that runs the reader agent.",
        "Finish before leaving: one document with role **main** in status *ingested*, and the reader agent run (status moves from new to **review**). Addenda and Q&A can be added at any time later.",
      ],
    },
    {
      id: "intake-docs-table",
      title: "The documents table",
      route: "/opportunities/{opp}",
      target: "rfp-docs-table",
      placement: "bottom",
      body: [
        "**File** is the original name. **Role** is what the document is to this bid: *main* (the RFP itself, exactly one per opportunity), *addendum*, *qa* (questions and answers), *change* or *other*. A second *main* is refused with \"This opportunity already has a main RFP; upload this file as an addendum, Q&A or other.\"",
        "**Pages** is filled once the file has been read. **Status** goes *uploaded* → *ingesting* → **ingested**; *failed* means a damaged or encrypted PDF (reported, never skipped), *unsupported* a non-PDF such as Word or CAD: it is recorded but never read.",
        "**Received** shows the date; hover it for the file's **SHA-256 fingerprint**. The bytes are stored once under that hash and never modified, the document ID is `<opportunity>-<first 12 hex of the hash>`, and the same file sent to two opportunities is two documents. Uploading the identical file twice to one opportunity adds nothing.",
      ],
    },
    {
      id: "intake-upload-form",
      title: "The upload form",
      route: "/opportunities/{opp}",
      target: "rfp-upload-form",
      placement: "top",
      onEnter: openDetails("rfp-upload-form"),
      fallback: "The upload form sits under the table; once review has started it folds into \"Add another document\".",
      body: [
        "**RFP file (PDF)** takes one file; **Role** defaults to *main* for a fresh opportunity and to *addendum* once requirement review has started. **Upload and read** posts the file as `multipart/form-data` to `/api/opportunities/{opp}/documents`: the server stores it and answers at once, then reads it in the background.",
        "The page does not poll: press **Refresh status** to see *ingesting* turn into *ingested* (the walkthrough does this for you in the next steps). While an uploaded main RFP is still being read the reader-agent button is disabled with \"Waiting for the main RFP to be read\"; with no document at all, pressing it only returns the API's message \"Upload the main RFP and wait until it has been read.\"",
        "You can upload the Syracuse RFP manually from `data/RFP/RFP-2023-20-Switchgear-Procurement-Final.pdf`, or let the next step attach the bundled copy through the sample route: same storage, same reading, same JSON.",
      ],
    },
    {
      id: "intake-add-another",
      title: "Add another document (later)",
      route: "/opportunities/{opp}",
      target: "rfp-add-another",
      placement: "top",
      fallback: "This fold appears once requirement review has started: the upload form moves into a collapsed \"Add another document (addendum, Q&A, change)\" card, with the role defaulting to addendum.",
      body: [
        "Once review has started (status *review* and beyond) the upload form is secondary: it folds into **Add another document** with the role preset to *addendum*, and the main RFP is never re-read (\"Requirement review has started, so the RFP is not re-read. Missed items can be added on the Requirements page.\").",
        "A document added here is stored and read like the main one, so Traceability can show its pages. Comparing an addendum with the frozen baseline (what changed, which answers to revisit) is a separate upload on the **Changes** page, chapter 11.",
      ],
    },
    {
      id: "intake-use-example",
      title: "Attach the Syracuse RFP",
      route: "/opportunities/{opp}",
      target: "rfp-upload-form",
      placement: "top",
      kind: "action",
      skipIf: async (ctx) => (await mainDoc(ctx)) !== null,
      instruction: "Press \"Use example\" to attach the bundled Syracuse RFP as the main document, or upload the PDF yourself with role main.",
      fallback: "The upload form is under the documents table.",
      body: [
        "**Use example** calls `POST /api/opportunities/{opp}/documents/from-sample` with `{\"name\": \"syracuse_rfp\"}`. The server takes the bundled file (`RFP-2023-20-Switchgear-Procurement-Final.pdf`, 101 pages) from a whitelist (`GET /api/samples` lists the three samples: this RFP, the hyperscale RFP and the Syracuse addendum), stores it as role *main* and starts reading it, exactly as a manual upload would.",
        "Only the Syracuse RFP has **frozen reader answers**, so it is the one new RFP that can be read offline. Any other PDF is stored and laid out the same way, but the reader agent then needs the model connection.",
      ],
      example: {
        label: "Use example: syracuse_rfp",
        apply: async (ctx) => {
          await ctx.post(`/api/opportunities/${ctx.oppId}/documents/from-sample`, { name: "syracuse_rfp" });
          ctx.set("rfpRefreshed", false);
          ctx.el("rfp-refresh")?.click();
        },
      },
      done: async (ctx) => (await mainDoc(ctx)) !== null,
    },
    {
      id: "intake-wait-read",
      title: "Reading the RFP (about a minute)",
      route: "/opportunities/{opp}",
      target: "rfp-doc-status",
      placement: "right",
      kind: "wait",
      skipIf: syncDocs,
      fallback: "The main document's status cell shows uploaded, then ingesting, then ingested.",
      body: [
        "Meanwhile the ingestion service builds the **layout model**. Each page's text layer is read with PyMuPDF line by line, in reading order, with the box of every line in page points. A page with no usable text layer (a scan, or unmapped characters) is rendered at 300 dpi and sent to **Tesseract OCR**; if OCR is not installed the page is marked *unreviewed* with the reason, never silently skipped.",
        "Then: headers and footers repeated on three or more pages are **marked as furniture** (kept, so line numbers stay stable), contents pages are flagged, and **ruled tables** are found with pdfplumber and kept beside the lines: a line inside a cell gets its table, row and column, so the data sheet can be read later without changing any anchor.",
        "For the Syracuse RFP the whole parse is **frozen** in `data/layout_cache/<sha256>.json`, so every machine gets identical lines, line numbers and highlights without the OCR stack. Finally the RFP is cut into about 566 passages of up to 500 characters (page and line range kept) for the search box below.",
        "The walkthrough polls the document status and presses Refresh status for you when it reads *ingested*.",
      ],
      done: async (ctx) => {
        const d = await mainDoc(ctx);
        if (d?.status !== "ingested") return false;
        if (!ctx.get<boolean>("rfpRefreshed")) { ctx.set("rfpRefreshed", true); ctx.el("rfp-refresh")?.click(); }
        return true;
      },
    },
    {
      id: "intake-doc-ingested",
      title: "Result: 101 pages, ingested",
      route: "/opportunities/{opp}",
      target: "rfp-doc-main",
      placement: "bottom",
      onEnter: async (ctx) => { await syncDocs(ctx); },
      fallback: "The main document row shows the file name, role main, 101 pages, status ingested and today's date.",
      body: [
        "The main row now reads **101** pages and **ingested** (green). Hover the Received cell: the SHA-256 is the same on every installation because it is a hash of the file bytes, which is how the frozen layout and the frozen reader answers are found.",
        "Two things became available: the **Search this RFP** box (the short-term index is built every time the RFP is read) and the **Run the reader agent** button (enabled now that the main RFP is read).",
      ],
    },
    {
      id: "intake-search",
      title: "Search this RFP",
      route: "/opportunities/{opp}",
      target: "rfp-search",
      placement: "top",
      onEnter: async (ctx) => { await syncDocs(ctx); },
      fallback: "The search card appears once the main RFP is ingested.",
      body: [
        "Ask in plain words; `GET /api/opportunities/{opp}/rfp-search?q=…` returns the best passages with **page and line range**, so a bid manager can check a question against the source without opening the PDF. \"What short-circuit rating is required?\" brings back p. 63, lines 11-17 (bus bracing for short-circuit currents) and p. 64, lines 3-25 (\"Short-circuit current at rated max kV: (18,000)\", close and latch 62,000 A peak).",
        "The small print under the results says how it searched: **Meaning-based search** when embeddings are available (the Syracuse passages' vectors are frozen in `data/vector_cache`, so this works offline), otherwise **Keyword search** as the fallback. Headers and footers are left out of the passages.",
        "This index is short-term and per opportunity: it answers questions about *this* RFP. The long-term knowledge base (products, past responses, approved knowledge) is a different index, shown in chapter 10.",
      ],
      example: {
        label: "Search: what short-circuit rating is required?",
        apply: (ctx) => {
          const input = field(ctx, "rfp-search-input");
          setValue(input, "what short-circuit rating is required?");
          (ctx.el("rfp-search-form") as HTMLFormElement | null)?.requestSubmit();
        },
      },
    },
    {
      id: "intake-extract",
      title: "Run the reader agent",
      route: "/opportunities/{opp}",
      target: "rfp-extract",
      placement: "top",
      kind: "action",
      skipIf: statusIn(...READ_STATUSES),
      onEnter: async (ctx) => { await syncDocs(ctx); },
      instruction: "Press \"Run the reader agent → requirements\" and wait; the page moves to the Requirements step when it is done (about a minute).",
      fallback: "The button is below the search card while the opportunity is new; it disappears once review has started.",
      body: [
        "`POST /api/opportunities/{opp}/requirements/extract` runs two agents over the layout model, never over raw PDF text. The **reader agent** goes page by page and proposes **line items**: each has a short requirement text, a category, and a **verbatim quote** that is then located on the page. A quote found on its lines is *EXTRACTED* (anchored to page, lines and boxes); one that cannot be located is kept as *UNANCHORED* for a person to check, never dropped.",
        "Then exact-duplicate quotes are marked **duplicate**, and the **grouping agent** folds related items of a page into **groups** with sub-requirements. For the Syracuse RFP both agents answer from frozen replies (no model call); their proposals are drafts in status *proposed*, created by \"reader agent (Bid Manager)\".",
        "Rules: it needs the main RFP in *ingested*; it only runs while the opportunity is *new* or *review* and before any review action (afterwards re-reading would lose that work, so the API refuses and you add missed items on the Requirements page instead); a re-run replaces only the agents' unreviewed drafts and keeps anything a person added. On success the status becomes **review** and the page opens Requirements; if some pages could not be read, the problems are listed here instead.",
      ],
      done: statusIn(...READ_STATUSES),
    },
    {
      id: "intake-result",
      title: "Result: 814 line items, 348 requirements",
      body: [
        "For the Syracuse RFP the reader agent proposed **814 line items** from 101 pages with no unread pages. **21** were exact duplicates of an earlier line (marked, kept as evidence, not reviewed again) and the grouping agent formed **162 groups**, so the Requirements page starts with **348 requirements** to review: groups and stand-alone items, every one pointing to its page and lines.",
        "A requirement ID like `REQ-00xx-0324` carries the opportunity number and a sequence that is never reused, even for discarded drafts, so a unit's answer can never land on a different requirement. Categories come from the catalog's list (technical, commercial, …) and can be changed during review.",
        "Next, chapter 5: review the proposals (approve, reject, edit the short text, split, merge, add a missed line from the page), then **freeze** them as baseline 1. Nothing after this point changes a requirement except a change document.",
      ],
    },
  ],
};
export default chapter;
