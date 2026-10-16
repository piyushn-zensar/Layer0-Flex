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
  summary: "The business units, their products and offering types, and the searchable long-term index of products, illustrative past responses and approved reviewed examples.",
  entryRoute: "/catalog",
  steps: [
    {
      id: "catalog-intro",
      title: "Product catalog: units, products and the index",
      route: "/catalog",
      target: "catalog-search",
      placement: "bottom",
      body: [
        "The **Product catalog** is the knowledge the matcher and the units work from: the business units, their product families with offering types and their published models, and the illustrative past responses, all read from `data/knowledge_base/*.json` (rules as data). The line at the top says it plainly: families and models come from **public Flex web pages (retrieved 12 Oct 2026), to be confirmed with each unit**.",
        "At the top, a search box over the long-term index; below, one card per unit. Nothing on this page writes; it is the reference the other screens link to (product names in Traceability, BOM lines in the hand-off, people who can sign in).",
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
        "Each card: the unit's name and **code** (`CROWN` is what requirement rows, inboxes and hand-off files use), its **pillar** (Critical Power, Embedded Power, Thermal Management, Cloud) and a **status** badge. *Active* units take part in matching, dispatch and the people picker; a *pending* unit such as EPC Power is listed for completeness but excluded until confirmed.",
        "Then the unit's **focus** in one sentence, and its **unit manager** and **unit designer / engineer**: these two names are the people allowed to answer the unit's work package, and the names of their sign-in accounts. The seven units are EP², Crown Technical Systems, Anord Mardix, Flex Power Modules, JetCool, Cloud (in-house) and EPC Power (pending).",
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
        "A result is evidence, not a decision: in matching, the agent sees these hits and proposes a unit and product with a confidence and a rationale, and a person accepts or rejects the match. Remember the data is illustrative: the real product list, descriptions and past answers are to be confirmed with each unit before the scores mean anything commercially.",
        "**Clear** empties the query and brings the plain catalog back. This closes the catalog chapter; chapter 11 shows what happens when the customer issues an addendum.",
      ],
    },
  ],
};
export default chapter;
