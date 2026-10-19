// Filters and sorting on Requirement Traceability (A-27, C-32, C-20), kept in the page address so a link opens a view:
// ?category=technical&offering=ETO&unit=CROWN&response=submitted&compliance=partial&source=verified&origin=correction
// &from=50&to=60&q=breaker&sort=unit. A-24's summary links (?category= / ?offering=) open these views.  Owner: Atharv.
import type { TraceRow } from "@/lib/types";

export const FILTER_KEYS = ["category", "offering", "unit", "response", "compliance", "source", "origin", "from", "to", "q", "sort"] as const;
export type FilterKey = (typeof FILTER_KEYS)[number];
export type Filters = Partial<Record<FilterKey, string>>;

export const SORTS: Record<string, string> = { rfp: "RFP order", id: "ID", category: "Category", unit: "Unit", compliance: "Compliance", changed: "Last change" };
export const RESPONSES: Record<string, string> = { not_sent: "Not sent", assigned: "Assigned", submitted: "Submitted", returned: "Returned", validated: "Validated" };

export function readFilters(search: string): Filters {
  const p = new URLSearchParams(search);
  return Object.fromEntries(FILTER_KEYS.filter((k) => p.get(k)).map((k) => [k, p.get(k)!])) as Filters;
}

/** The page address for these filters, keeping the selected requirement (#REQ-...). */
export function filtersUrl(pathname: string, f: Filters, hash: string): string {
  const qs = new URLSearchParams(Object.entries(f).filter(([, v]) => v) as [string, string][]).toString();
  return `${pathname}${qs ? `?${qs}` : ""}${hash}`;
}

const unitsOf = (r: TraceRow) => new Set([...(r.match?.units ?? []).map((u) => u.bu), ...(r.match?.bu ? [r.match.bu] : []), ...r.assignments.map((a) => a.bu)]);
const COMPLIANCE_ORDER = ["not_met", "partial", "met"]; // weakest first, as the go/no-go summary reads them

function matches(r: TraceRow, f: Filters): boolean {
  const req = r.req;
  if (f.category && req.category !== f.category) return false;
  if (f.offering && (r.match?.offering_type ?? "unmatched") !== f.offering) return false;
  if (f.unit && !unitsOf(r).has(f.unit)) return false;
  if (f.response && !(f.response === "not_sent" ? r.assignments.length === 0 : r.assignments.some((a) => a.status === f.response))) return false;
  if (f.compliance && !r.assignments.some((a) => a.compliance === f.compliance)) return false;
  if (f.source && (req.provenance === "EXTRACTED") !== (f.source === "verified")) return false;
  if (f.origin && (req.origin ?? "extraction") !== f.origin) return false;
  if (f.from && (req.page ?? 0) < Number(f.from)) return false;
  if (f.to && (req.page ?? Infinity) > Number(f.to)) return false;
  if (f.q) {
    const q = f.q.toLowerCase();
    const text = `${req.req_id} ${req.text} ${req.quote} ${r.children.map((k) => k.text).join(" ")}`.toLowerCase();
    if (!text.includes(q)) return false;
  }
  return true;
}

function key(r: TraceRow, sort: string): string | number {
  switch (sort) {
    case "id": return r.req.req_id;
    case "category": return r.req.category;
    case "unit": return r.match?.bu ?? "~"; // unmatched last
    case "compliance": {
      const ranks = r.assignments.map((a) => COMPLIANCE_ORDER.indexOf(a.compliance ?? "")).filter((i) => i >= 0);
      return ranks.length ? Math.min(...ranks) : COMPLIANCE_ORDER.length; // weakest answer first, unanswered last
    }
    case "changed": return -Date.parse((r.req as { created_at?: string }).created_at ?? "") || 0; // newest version first
    default: return 0;
  }
}

/** The rows that pass the filters, in the chosen order (RFP order = the trace API's document order). */
export function applyFilters(rows: TraceRow[], f: Filters): TraceRow[] {
  const kept = rows.filter((r) => matches(r, f));
  const sort = f.sort && f.sort !== "rfp" ? f.sort : "";
  if (!sort) return kept;
  const indexed = kept.map((r, i) => ({ r, i, k: key(r, sort) }));
  indexed.sort((a, b) => (a.k < b.k ? -1 : a.k > b.k ? 1 : a.i - b.i)); // stable: ties keep RFP order
  return indexed.map((x) => x.r);
}

export const isFiltered = (f: Filters) => FILTER_KEYS.some((k) => k !== "sort" && f[k]) || (!!f.sort && f.sort !== "rfp");

// 19 Oct client review: a dropdown offers only what the bid has, and the other filters narrow it (faceted search).
export const FACETS = ["category", "offering", "unit", "response", "compliance", "source", "origin"] as const;
export type Facet = (typeof FACETS)[number];

function valuesOf(r: TraceRow, k: Facet): string[] {
  switch (k) {
    case "category": return [r.req.category];
    case "offering": return [r.match?.offering_type ?? "unmatched"];
    case "unit": return [...unitsOf(r)];
    case "response": return r.assignments.length ? [...new Set(r.assignments.map((a) => a.status))] : ["not_sent"];
    case "compliance": return [...new Set(r.assignments.map((a) => a.compliance).filter((c): c is string => !!c))];
    case "source": return [r.req.provenance === "EXTRACTED" ? "verified" : "not_verified"];
    case "origin": return [r.req.origin ?? "extraction"];
  }
}

/** For each facet, the values present among the rows that pass every other filter, with how many rows have each. */
export function facets(rows: TraceRow[], f: Filters): Record<Facet, Map<string, number>> {
  const out = {} as Record<Facet, Map<string, number>>;
  for (const k of FACETS) {
    const others: Filters = { ...f, [k]: undefined };
    const m = new Map<string, number>();
    for (const r of rows) if (matches(r, others)) for (const v of valuesOf(r, k)) m.set(v, (m.get(v) ?? 0) + 1);
    out[k] = m;
  }
  return out;
}
