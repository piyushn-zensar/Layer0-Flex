// Walkthrough chapter 10: the Product catalog (web/app/catalog). The Knowledge base page it used to share was removed
// (P-41, C-33): reviewed examples are nominated where they arise and reviewed in Knowledge review in My work.
import type { TourChapter, TourCtx } from "../types";
import { present } from "../helpers";

type Field = HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;

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

const chapter: TourChapter = {
  id: "catalog",
  order: 10,
  title: "Product catalog",
  summary: "The business units and their products with their types of offer, the search over the long-term index, the reference documents (Sources) and the catalog read from the Flex web pages (Published catalog).",
  entryRoute: "/catalog",
  steps: [
    {
      id: "catalog-intro",
      title: "Product catalog: units, products and the index",
      route: "/catalog",
      target: "catalog-search",
      placement: "bottom",
      body: [
        "The **Product catalog** is the knowledge the matcher and the units work from: the business units, their product families with their types of offer and their published models, and the illustrative past responses, all read from `data/knowledge_base/*.json` (rules as data). The line at the top says it plainly: families and models come from **public Flex web pages (retrieved 12 Oct 2026), to be confirmed with each unit**.",
        "At the top, a search box over the long-term index; below, one card per unit. Nothing on this page writes; it is the reference the other screens link to (solution areas in Traceability, BOM lines in the hand-off, people who can sign in).",
      ],
    },
    {
      id: "catalog-tabs",
      title: "Three views of the catalog",
      route: "/catalog",
      target: "catalog-tabs",
      placement: "bottom",
      body: [
        "**Products** is the business units and their products, with the search below. **Sources** is the reference documents behind the evidence (engineering references, vendor and market context), registered and reviewed. **Published catalog** is what the official Flex product pages say today, read automatically. The next steps look at the first, then the other two.",
      ],
    },
    {
      id: "catalog-unit",
      title: "A business unit card",
      route: "/catalog",
      target: "catalog-unit-head-CROWN",
      placement: "bottom",
      fallback: "Each card names a unit with its code, pillar and status, its focus, and its unit manager and unit designer / engineer.",
      body: [
        "Each card: the unit's name and **code** (`CROWN` is what requirement rows, inboxes and hand-off files use), its **pillar** (Critical Power, Embedded Power, Thermal Management, Cloud) and a **status** badge. *Active* units take part in matching, sending the work and the people picker; a *pending* unit such as EPC Power is listed for completeness but excluded until confirmed.",
        "Then the unit's **focus** in one sentence, and its **unit manager** and **unit designer / engineer**: these two names are the people allowed to answer the unit's work package, and the names of their sign-in accounts. The seven units are EP², Crown Technical Systems, Anord Mardix, Flex Power Modules, JetCool, Cloud (in-house) and EPC Power (pending).",
      ],
    },
    {
      id: "catalog-products",
      title: "Products and types of offer",
      route: "/catalog",
      target: "catalog-products-CROWN",
      placement: "top",
      fallback: "Under each unit, its products: id, name and a type-of-offer badge (CTO, Semi-custom, ETO).",
      body: [
        "Each product line: its **id** (`CROWN-ARMV`, kept as the reference in matches and hand-off items), its name (shown as the **solution area** of a proposed solution; published models are examples), and the **type of offer** badge: **CTO** (green, configure-to-order: hand-off route A, a CPQ configuration seed with the product's BOM lines), **Semi-custom** (amber: route B, basis of design) and **ETO** (red, engineer-to-order: route B, or route C when the unit's usual type of offer asks for a specialist first).",
        "Crown's are the ARMV arc-resistant metal-clad switchgear (ETO), ACC accessories (CTO) and the E-house (ETO). A product's description and keywords are what the index embeds, so the search below finds products by meaning, not only by name.",
      ],
    },
    {
      id: "catalog-search",
      title: "Search products and past responses",
      route: "/catalog",
      target: "catalog-search",
      placement: "bottom",
      kind: "action",
      instruction: "Type a requirement in your own words and press Search, or press Use example.",
      fallback: "The search box is at the top of the catalog page.",
      body: [
        "The box queries `GET /api/catalog?q=…`: the **long-term index** of product descriptions, seeded past responses and approved reviewed examples, the best hits (at most ten). It is the same retrieval the matcher uses for its evidence, so you can see for yourself why a requirement was sent to a unit.",
        "Ranking: when embeddings are available, the query and every entry are compared by **meaning** (cosine similarity of the frozen vectors in `data/vector_cache`; new learned entries need the embedding service once, or fall back); without them it is a **keyword** score. The score column shows the number used for ranking.",
        "Example: \"arc resistant 15kV metal clad switchgear\" ranks PAST-CROWN-001 (a past Crown answer) and the product CROWN-ARMV at the top, then the Arc-Resistant Switchgear model of CROWN-ARMV and the family CROWN-MCSG, with other units' entries far below.",
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
        "**Score** is the ranking number (higher is closer). **Kind** is *product* or *past_response*: an approved reviewed example (nominated where it arose, approved in Knowledge review in My work) appears as a past response of its unit. **Unit** and **ID** tell you where it comes from; **Text** is the beginning of what was indexed.",
        "A result is evidence, not a decision: in matching, the agent sees these hits and proposes a unit and solution area with a confidence and a rationale, and a person (for a technical item, the matched unit's designer / engineer) accepts or rejects the match. Remember the data is illustrative: the real product list, descriptions and past answers are to be confirmed with each unit before the scores mean anything commercially.",
        "**Clear** empties the query and brings the plain catalog back.",
      ],
    },
    {
      id: "catalog-sources",
      title: "Sources: the reference documents",
      route: "/catalog",
      target: "sources-filters",
      placement: "bottom",
      onEnter: (ctx) => { const t = ctx.el("catalog-tab-sources"); if (t && t.getAttribute("aria-selected") !== "true") t.click(); },
      fallback: "The Sources tab lists the registered reference documents with collection, status, pages, passages and version.",
      body: [
        "Filter the list by **collection** and **status**. Each source is a document with its **collection** (engineering references, past responses, market and vendor context and others), status, pages, **passages** and **version**. Documents are read through the same layout model as an RFP, so every passage keeps its page and lines, and a model annotates each passage once (frozen). Embedded Document and Instance IDs mean the same file is never registered twice, and a newer version retires the earlier one.",
        "A source becomes **evidence only after review** by the collection's reviewers (the ten public references here are still *Draft*), and market and vendor context is **never used as verified evidence**. Evidence for one bid is never visible to another.",
      ],
    },
    {
      id: "catalog-published",
      title: "Published catalog: read from flex.com",
      route: "/catalog",
      target: "published-refresh",
      placement: "bottom",
      onEnter: (ctx) => { const t = ctx.el("catalog-tab-published"); if (t && t.getAttribute("aria-selected") !== "true") t.click(); },
      fallback: "The Published catalog tab shows the last refresh and the products read from the Flex pages.",
      body: [
        "On server start and every 24 hours Layer 0 reads the official Flex product pages (power and cooling, power modules, Anord Mardix, Crown, EP², JetCool) respecting `robots.txt`, and keeps each product's name, category, key features and link. A **renamed product keeps every earlier name** in its history, and a failed page keeps the last good catalog. **Refresh now** (bid manager) runs it on demand.",
        "This view shows what is published; it is **not compliance evidence** and does not change the matching. Each assessment run records the catalog version it used, so a later change of the pages never rewrites an earlier assessment.",
      ],
    },
  ],
};
export default chapter;
