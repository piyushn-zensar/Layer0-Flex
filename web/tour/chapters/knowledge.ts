// Walkthrough chapter 10: Knowledge base queue and the Product catalog (web/app/knowledge, web/app/catalog).  Owner: G1.
// Sending from Traceability is covered by the trace chapter; here a validated inbox answer is queued through the API
// ("Use example"), then approved with a tidied response, then a requirement is queued and rejected with a note.
import type { TourChapter, TourCtx } from "../types";
import { present } from "../helpers";

type Field = HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
type KbItem = { kb_id: string; kind: string; status: string; source_ref: string };
type Kb = { items: KbItem[]; curator: string; learned: number; index: string };
type Row = { id: number; opportunity_id: string; req_id: string; status: string };
const BM = "Bid Manager";

function setValue(el: Field | null | undefined, value: string) {
  if (!el) return;
  const proto = el instanceof HTMLSelectElement ? HTMLSelectElement.prototype
    : el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value")?.set?.call(el, value);
  el.dispatchEvent(new Event(el instanceof HTMLSelectElement ? "change" : "input", { bubbles: true }));
}
const field = (ctx: TourCtx, tourId: string): Field | null => {
  const el = ctx.el(tourId);
  if (!el) return null;
  return el.matches("input, select, textarea") ? (el as Field) : el.querySelector<Field>("input, select, textarea");
};
const kb = async (ctx: TourCtx): Promise<Kb | null> => { try { return await ctx.api<Kb>("/api/knowledge"); } catch { return null; } };
const refetch = () => window.dispatchEvent(new Event("focus"));  // useApi reloads on focus
const kbIdIn = (message: string) => /KB-\d{4}/.exec(message)?.[0];
/** POST /api/knowledge; an "Already queued as KB-0007" refusal is treated as success for that id. */
async function send(ctx: TourCtx, kind: string, ref: string, note: string): Promise<string | undefined> {
  try { return (await ctx.post<{ kb_id: string }>("/api/knowledge", { kind, ref, note })).kb_id; }
  catch (e) {
    const id = kbIdIn(e instanceof Error ? e.message : String(e));
    if (id) return id;
    throw e;
  } finally { refetch(); }
}

const chapter: TourChapter = {
  id: "knowledge",
  order: 10,
  title: "Knowledge base and catalog",
  summary: "What the next bid learns from: the curator's queue of requirements, validated answers and decision rationales, and the product catalog with its searchable long-term index.",
  entryRoute: "/knowledge",
  steps: [
    {
      id: "knowledge-intro",
      title: "Knowledge base: what the next bids learn from",
      route: "/knowledge",
      target: "kb-tabs",
      placement: "bottom",
      body: [
        "Every bid produces knowledge worth keeping: a well-phrased requirement, a validated answer, the reasoning behind a go or no-go. People send those from an opportunity with **Send to knowledge base**; this page is the **curator's queue** where each item is approved or rejected. Nothing enters the knowledge base without a person's approval.",
        "Approved items join the **long-term retrieval index** next to the catalog's products and illustrative past responses. That index is what the matching evidence, the response outline and the catalog search query: so an approved answer from this bid can be found as evidence in the next one.",
        "Three tabs filter by status; the line under the title counts what has been approved so far in this installation.",
      ],
    },
    {
      id: "knowledge-learned",
      title: "Approved items in the long-term index",
      route: "/knowledge",
      target: "kb-learned",
      placement: "bottom",
      body: [
        "\"n approved item(s) in the long-term index\" is the number of entries in `knowledge_learned.json`, the file the curator's approvals are written to in this installation's store (next to the database, not in the repository). A fresh demo starts at 0.",
        "The illustrative **past responses** of the product catalog (eight seeded answers such as PAST-CROWN-001) sit in the same index but are seed data; the learned entries are the ones this team added.",
      ],
    },
    {
      id: "knowledge-tabs",
      title: "Waiting, Approved, Rejected",
      route: "/knowledge",
      target: "kb-tabs",
      placement: "bottom",
      body: [
        "**Waiting** (status *queued*) is the curator's to-do list; **Approved** and **Rejected** are the record, each with who decided and the note. The counts in the chips are over everything ever sent. The list is newest first.",
        "A rejected item can be sent again later (perhaps reworded); an item that is queued or approved cannot be sent twice: the API answers \"Already queued as KB-0001\" and the sending button shows the state instead.",
      ],
    },
    {
      id: "knowledge-send",
      title: "Where items come from",
      route: "/knowledge",
      target: "kb-tabs",
      placement: "bottom",
      kind: "action",
      instruction: "Press Use example to queue a validated Crown answer from the inbox, or send something yourself from Traceability.",
      skipIf: async (ctx) => ((await kb(ctx))?.items.length ?? 0) > 0,
      body: [
        "Three kinds can be sent, each by the small **Send to knowledge base** link next to it: a **requirement** (from Traceability, when its row is selected), a **validated answer** (from Traceability's answers or the response outline: only *validated* answers are accepted, a submitted one is refused), and a **decision rationale** (from the bid decision page, when the decision has a rationale). An optional note tells the curator why it is worth keeping.",
        "The item is stored with what it says at that moment, read from the module that owns it: for an answer, \"Met. <the unit's text> Offered: <product name>.\" plus the requirement text and its source (REQ, page and lines).",
        "**Use example** does the same through the API for the first validated Crown answer (`POST /api/knowledge {kind: \"response\", ref: <assignment id>, note}`), so the queue has something to curate.",
      ],
      example: {
        label: "Queue a validated Crown answer",
        apply: async (ctx) => {
          const items = (await ctx.api<{ items: Row[] }>("/api/inbox/CROWN")).items;
          const v = items.find((a) => a.status === "validated" && a.opportunity_id === ctx.oppId) ?? items.find((a) => a.status === "validated");
          if (!v) throw new Error("No validated Crown answer yet: validate one in the inbox chapter first.");
          const id = await send(ctx, "response", String(v.id), "Reusable wording for 15 kV arc-resistant metal-clad lineups.");
          if (id) ctx.set("kbResponse", id);
        },
      },
      done: async (ctx) => ((await kb(ctx))?.items.length ?? 0) > 0,
    },
    {
      id: "knowledge-item",
      title: "Anatomy of a queued item",
      route: "/knowledge",
      target: "kb-item-first",
      placement: "top",
      onEnter: (ctx) => ctx.el("kb-tab-queued")?.click(),
      fallback: "Each card shows the KB id, the kind, the opportunity and source it came from, who sent it and why, the requirement (\"Asked\") and the answer.",
      body: [
        "The card head: the id (`KB-0001`, allocated in order), the kind (*Requirement*, *Validated answer* or *Decision rationale*), \"from OPP-… , REQ-…, p. N, lines a-b\" (a link back to the opportunity's Traceability) and the status badge.",
        "Then who sent it, their note in quotes, and the unit for a unit's answer. **Asked** is the requirement text; **Answer** is what will be kept. A queued item seen by the curator shows the review form instead of the answer.",
      ],
    },
    {
      id: "knowledge-curator",
      title: "Who curates",
      route: "/knowledge",
      target: "kb-curator-note",
      placement: "bottom",
      kind: "action",
      skipIf: (ctx) => ctx.actor === BM,
      instruction: "Switch \"Acting as\" to Bid Manager (the curator), or press Use example.",
      fallback: "When the acting person is not the curator a blue note says so; the review form is only shown to the curator.",
      body: [
        "In the PoC the curator is the **Bid Manager**; a named knowledge-curator role arrives with sign-in. Anyone can read the queue, but `POST /api/knowledge/<id>/review` is refused for everyone else (\"Only the knowledge curator (in the PoC, the Bid Manager) approves knowledge.\").",
      ],
      example: { label: "Act as Bid Manager", apply: (ctx) => ctx.setActor(BM) },
      done: (ctx) => ctx.actor === BM,
    },
    {
      id: "knowledge-review-form",
      title: "The review form",
      route: "/knowledge",
      target: "kb-review-form",
      placement: "top",
      onEnter: (ctx) => ctx.el("kb-tab-queued")?.click(),
      fallback: "On a queued item the curator sees \"Response to keep\", a Note field, Approve into the knowledge base, and Reject.",
      body: [
        "**Response to keep** is pre-filled with the answer as sent; the curator may tidy it (remove bid-specific prices or names, fix wording) because this is the sentence future bids will retrieve. **Note** is optional for an approval and **required for a rejection**, so the sender learns why.",
        "Two buttons: **Approve into the knowledge base** (the form's submit) and **Reject**. Both act on this one item; the card then moves to the Approved or Rejected tab with the curator's name and note.",
      ],
    },
    {
      id: "knowledge-approve",
      title: "Approve with a tidied response",
      route: "/knowledge",
      target: "kb-approve",
      placement: "top",
      kind: "action",
      instruction: "Tidy the response if you like (Use example does), then press \"Approve into the knowledge base\".",
      skipIf: async (ctx) => { const k = await kb(ctx); return !!k && k.items.length > 0 && !k.items.some((i) => i.status === "queued"); },
      fallback: "The Approve button is at the bottom of the first queued item's review form.",
      body: [
        "Approval stores the decision (status *approved*, reviewed by, note, the edited response) and then calls the catalog's **learn**: the entry (`id`, unit, opportunity, requirement, response, source, approved_by) is appended to `knowledge_learned.json` and the long-term index is rebuilt, so **catalog search**, the **matching evidence** and the **response outline** can retrieve it from now on.",
        "What approval does **not** do: it never changes the matcher's fixed prompt part (the catalog and the seeded past responses). That part is what the frozen matching answers were recorded against, so keeping it stable is what keeps the demo repeatable; learned knowledge reaches the matcher as retrieved evidence instead.",
      ],
      example: {
        label: "Tidy the response",
        apply: (ctx) => {
          const t = field(ctx, "kb-review-response");
          if (t) setValue(t, t.value.replace(/\s+/g, " ").trim().replace(/^Met\.\s*/, "Met. ") + (t.value.includes("IEEE") ? "" : " Lineup type-tested to IEEE C37.20.7."));
          setValue(field(ctx, "kb-review-note"), "Standard answer; reusable for 15 kV arc-resistant lineups.");
        },
      },
      done: async (ctx) => {
        const k = await kb(ctx);
        const id = ctx.get<string>("kbResponse");
        return !!k && (id ? k.items.some((i) => i.kb_id === id && i.status === "approved") : k.items.some((i) => i.status === "approved"));
      },
    },
    {
      id: "knowledge-approved",
      title: "Result: in the long-term index",
      route: "/knowledge",
      target: "kb-tab-approved",
      placement: "bottom",
      onEnter: (ctx) => ctx.el("kb-tab-approved")?.click(),
      body: [
        "The **Approved** tab shows the card with its kept answer and \"Approved by Bid Manager: <note>\"; the counter under the title now reads one more approved item. Back in Traceability the sending link reads *in knowledge base*.",
        "Try it on the catalog page in a moment: a search for the requirement's words now returns the learned entry as a past response of unit CROWN, ranked with the seeded ones.",
      ],
    },
    {
      id: "knowledge-reject",
      title: "Reject with a note",
      route: "/knowledge",
      target: "kb-reject",
      placement: "top",
      kind: "action",
      onEnter: (ctx) => ctx.el("kb-tab-queued")?.click(),
      instruction: "Use example queues a requirement; then in the Waiting tab type a note and press Reject.",
      skipIf: async (ctx) => !!(await kb(ctx))?.items.some((i) => i.status === "rejected"),
      fallback: "Reject sits next to Approve in the review form of a queued item.",
      body: [
        "Not everything sent is worth keeping: a requirement that is specific to one customer, an answer that quotes a price, a rationale that repeats the criteria. **Reject** records the decision with the required note (\"Give a note so the sender knows why it was rejected.\" if it is empty) and nothing is added to the index.",
        "**Use example** queues the first requirement of the walkthrough opportunity as a *Requirement* item so you have something to reject (a bid-specific line is a typical reject).",
      ],
      example: {
        label: "Queue a requirement to reject",
        apply: async (ctx) => {
          const r = await ctx.api<{ requirements: { req_id: string; status: string }[] }>(`/api/opportunities/${ctx.oppId}/requirements`);
          const req = r.requirements.find((q) => q.status === "approved") ?? r.requirements[0];
          if (!req) throw new Error("This opportunity has no requirements yet.");
          const id = await send(ctx, "requirement", req.req_id, "Customer-specific wording; probably not reusable.");
          if (id) ctx.set("kbRequirement", id);
          ctx.el("kb-tab-queued")?.click();
          // the page re-fetches after the send: wait for the new item's review form before filling its note
          for (let i = 0; i < 30 && !field(ctx, "kb-review-note"); i++) await new Promise((r) => setTimeout(r, 200));
          setValue(field(ctx, "kb-review-note"), "Specific to this customer's site; not reusable.");
        },
      },
      done: async (ctx) => !!(await kb(ctx))?.items.some((i) => i.status === "rejected"),
    },
    {
      id: "catalog-intro",
      title: "Product catalog: units, products and the index",
      route: "/catalog",
      target: "catalog-search",
      placement: "bottom",
      body: [
        "The **Product catalog** is the knowledge the matcher and the units work from: the business units, their products with offering types, and the illustrative past responses, all read from `data/knowledge_base/*.json` (rules as data). The help line says it plainly: **illustrative seed data, to be confirmed with each unit**.",
        "At the top, a search box over the long-term index; below, one card per unit. Nothing on this page writes; it is the reference the other screens link to (product names in Traceability, BOM lines in the hand-off, people in \"Acting as\").",
      ],
    },
    {
      id: "catalog-unit",
      title: "A business unit card",
      route: "/catalog",
      target: "catalog-unit-head-CROWN",
      placement: "bottom",
      fallback: "Each card names a unit with its code, pillar and status, its focus, and its product manager and design engineer.",
      body: [
        "Each card: the unit's name and **code** (`CROWN` is what requirement rows, inboxes and hand-off files use), its **pillar** (Critical Power, Embedded Power, Thermal Management, Cloud) and a **status** badge. *Active* units take part in matching, dispatch and the people picker; a *pending* unit such as EPC Power is listed for completeness but excluded until confirmed.",
        "Then the unit's **focus** in one sentence, and its **product manager** and **design engineer**: these two names are the people allowed to answer the unit's work package, and the names you see in \"Acting as\". The seven units are EP², Crown Technical Systems, Anord Mardix, Flex Power Modules, JetCool, Cloud (in-house) and EPC Power (pending).",
      ],
    },
    {
      id: "catalog-products",
      title: "Products and offering types",
      route: "/catalog",
      target: "catalog-products-CROWN",
      placement: "top",
      fallback: "Under each unit, its products: id, name and an offering-type badge (CTO, Semi-custom, ETO).",
      body: [
        "Each product line: its **id** (`CROWN-ARMV`, used as the product reference in matches, inboxes and hand-off items), its name, and the **offering type** badge: **CTO** (green, configure-to-order: hand-off route A, a CPQ configuration seed with the product's BOM lines), **Semi-custom** (amber: route B, basis of design) and **ETO** (red, engineer-to-order: route B, or route C when the unit's tier asks for a specialist first).",
        "The seed holds 16 products across the six active units; Crown's are the ARMV arc-resistant metal-clad switchgear (ETO), ACC accessories (CTO) and the E-house (ETO). A product's description and keywords are what the index embeds, so the search below finds products by meaning, not only by name.",
      ],
    },
    {
      id: "catalog-search",
      title: "Search the knowledge base",
      route: "/catalog",
      target: "catalog-search",
      placement: "bottom",
      kind: "action",
      instruction: "Type a requirement in your own words and press Search, or press Use example.",
      fallback: "The search box is at the top of the catalog page.",
      body: [
        "The box queries `GET /api/catalog?q=…`: the **long-term index** of product descriptions, seeded past responses and curator-approved knowledge, the best hits (at most ten). It is the same retrieval the matcher uses for its evidence, so you can see for yourself why a requirement was sent to a unit.",
        "Ranking: when embeddings are available, the query and every entry are compared by **meaning** (cosine similarity of the frozen vectors in `data/vector_cache`; new learned entries need the embedding service once, or fall back); without them it is a **keyword** score. The score column shows the number used for ranking.",
        "Example: \"arc resistant 15kV metal clad switchgear\" ranks PAST-CROWN-001 (a past Crown answer) and the product CROWN-ARMV at the top, then Crown's other products and an EP² relay response far below.",
      ],
      example: {
        label: "Search: arc resistant 15kV metal clad switchgear",
        apply: (ctx) => {
          setValue(field(ctx, "catalog-search-input"), "arc resistant 15kV metal clad switchgear");
          (ctx.el("catalog-search") as HTMLFormElement | null)?.requestSubmit();
        },
      },
      done: present("catalog-results"),
    },
    {
      id: "catalog-results",
      title: "Reading the results",
      route: "/catalog",
      target: "catalog-results",
      placement: "bottom",
      fallback: "After a search, a card lists the matches best first: score, kind, unit, id and the first 160 characters of the text.",
      body: [
        "**Score** is the ranking number (higher is closer). **Kind** is *product* or *past_response*: a learned entry approved on the Knowledge base page appears as a past response of its unit. **Unit** and **ID** tell you where it comes from; **Text** is the beginning of what was indexed.",
        "A result is evidence, not a decision: in matching, the agent sees these hits and proposes a unit and product with a confidence and a rationale, and a person accepts or rejects the match. Remember the data is illustrative: the real product list, descriptions and past answers are to be confirmed with each unit before the scores mean anything commercially.",
        "**Clear** empties the query and brings the plain catalog back. This closes the knowledge chapter; chapter 11 shows what happens when the customer issues an addendum.",
      ],
    },
  ],
};
export default chapter;
