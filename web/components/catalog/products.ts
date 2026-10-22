// All-products table logic (J-19, C-60): search, filters, stable sort and pages over the rows of GET /api/catalog/products,
// joined with the documents / images and conflicts that only the detail call carries.  Pure functions, no React:
// `node web/components/catalog/products.check.mjs` runs the checks (Node 22.18+ runs .ts files).  Owner: Janvia.
import type { ProductConflict, ProductDocument, ProductImage, ProductRow } from "@/lib/types";

/** What the table knows about a row beyond the list call: filled from GET /api/catalog/product, per family and per conflicting part. */
export interface Media { documents: ProductDocument[]; images: ProductImage[]; conflicts: ProductConflict[] }
/** family_key -> its documents / images; part key -> its conflicts. A key that is absent has not loaded yet. */
export interface MediaIndex { family: Map<string, Pick<Media, "documents" | "images">>; conflicts: Map<string, ProductConflict[]> }

export const TYPE_LABEL: Record<ProductRow["product_type"], string> = { power_module: "Module", evaluation_board: "Evaluation board", web_listing: "Web series" };
export const SOURCE_LABEL: Record<ProductRow["source"], string> = { spreadsheet: "Spreadsheet", web: "Web", both: "Spreadsheet + web" };

/** The documents that apply to a row: those linked to its family (series) key. A part's own part number is not named in any document today. */
export const documentsOf = (row: ProductRow, idx: MediaIndex): ProductDocument[] =>
  (row.family_key ? idx.family.get(row.family_key)?.documents : undefined) ?? [];
/** The image shown for a row: the first verified image of its family; null shows the placeholder (none, or none verified). */
export const imageOf = (row: ProductRow, idx: MediaIndex): ProductImage | null =>
  ((row.family_key ? idx.family.get(row.family_key)?.images : undefined) ?? []).find((i) => i.verified) ?? null;
/** Whether the family has an image file that is not verified (the placeholder says so). */
export const hasUnverifiedImage = (row: ProductRow, idx: MediaIndex): boolean =>
  ((row.family_key ? idx.family.get(row.family_key)?.images : undefined) ?? []).some((i) => !i.verified);
export const conflictsOf = (row: ProductRow, idx: MediaIndex): ProductConflict[] => idx.conflicts.get(row.key) ?? [];
/** Conflict count: the fields in disagreement, known once the part's detail has loaded; a flagged part counts at least 1 until then. */
export const conflictCount = (row: ProductRow, idx: MediaIndex): number => (row.has_conflict ? Math.max(1, conflictsOf(row, idx).length) : 0);

// ---- columns -------------------------------------------------------------------------------------------------------

export type ColumnId = "image" | "part" | "family" | "series" | "type" | "status" | "vin" | "vout" | "power" | "current" | "efficiency"
  | "interfaces" | "source" | "documents" | "conflicts" | "family_key";
export interface Column { id: ColumnId; label: string; num?: boolean; on: boolean; locked?: boolean; sortable?: boolean }
export const COLUMNS: Column[] = [
  { id: "image", label: "Image", on: true, sortable: true },
  { id: "part", label: "Part number", on: true, locked: true, sortable: true },
  { id: "family", label: "Family", on: true, sortable: true },
  { id: "series", label: "Series", on: true, sortable: true },
  { id: "type", label: "Type", on: true, sortable: true },
  { id: "status", label: "Status", on: false, sortable: true },
  { id: "vin", label: "Input (V)", on: true, num: true, sortable: true },
  { id: "vout", label: "Output (V)", on: true, num: true, sortable: true },
  { id: "power", label: "Power (W)", on: true, num: true, sortable: true },
  { id: "current", label: "Current (A)", on: false, num: true, sortable: true },
  { id: "efficiency", label: "Efficiency (%)", on: true, num: true, sortable: true },
  { id: "interfaces", label: "Interface", on: false, sortable: true },
  { id: "source", label: "Source", on: true, sortable: true },
  { id: "documents", label: "Documents", on: true, num: true, sortable: true },
  { id: "conflicts", label: "Conflicts", on: true, num: true, sortable: true },
  { id: "family_key", label: "Catalog ID of the family", on: false, sortable: true },
];
export const DEFAULT_COLUMNS: ColumnId[] = COLUMNS.filter((c) => c.on).map((c) => c.id);

/** A saved column choice, or the default when it is missing, damaged, or would leave the table without its part number. */
export function parseColumns(raw: string | null | undefined): ColumnId[] {
  try {
    const v = JSON.parse(raw ?? "null");
    const known = new Set(COLUMNS.map((c) => c.id));
    if (Array.isArray(v) && v.every((x) => known.has(x)) && v.includes("part")) return COLUMNS.map((c) => c.id).filter((id) => v.includes(id));
  } catch { /* not JSON */ }
  return DEFAULT_COLUMNS;
}

// ---- values for search and sort --------------------------------------------------------------------------------------

type Cell = string | number | null;
/** The value a column sorts by; null (unknown) always sorts last, in either direction, as the API does. */
export function sortValue(row: ProductRow, id: ColumnId, idx: MediaIndex): Cell {
  switch (id) {
    case "image": return imageOf(row, idx) ? 2 : hasUnverifiedImage(row, idx) ? 1 : 0;
    case "part": return row.part_number.toLowerCase();
    case "family": return row.family?.toLowerCase() ?? null;
    case "series": return row.series?.toLowerCase() ?? null;
    case "type": return TYPE_LABEL[row.product_type];
    case "status": return row.status?.toLowerCase() ?? null;
    case "vin": return row.vin_min_v;
    case "vout": return row.vout_min_v;
    case "power": return row.power_w;
    case "current": return row.current_a;
    case "efficiency": return row.efficiency_pct;
    case "interfaces": return row.interfaces.length ? row.interfaces.join(", ").toLowerCase() : null;
    case "source": return SOURCE_LABEL[row.source];
    case "documents": return documentsOf(row, idx).length;
    case "conflicts": return conflictCount(row, idx);
    case "family_key": return row.family_key?.toLowerCase() ?? null;
  }
}

/** Stable sort: rows that compare equal keep the order they came in, and unknown values come last whichever way it sorts. */
export function sortRows(rows: ProductRow[], id: ColumnId, dir: "asc" | "desc", idx: MediaIndex): ProductRow[] {
  const keyed = rows.map((r, i) => ({ r, i, v: sortValue(r, id, idx) }));
  const sign = dir === "asc" ? 1 : -1;
  keyed.sort((a, b) => {
    if (a.v === null || b.v === null) return a.v === b.v ? a.i - b.i : a.v === null ? 1 : -1;
    const c = typeof a.v === "number" && typeof b.v === "number" ? a.v - b.v : String(a.v).localeCompare(String(b.v), "en", { numeric: true });
    return c === 0 ? a.i - b.i : c * sign;
  });
  return keyed.map((k) => k.r);
}

// ---- search and filters ----------------------------------------------------------------------------------------------

/** Everything a search covers: part number, series, family name, family and catalog ID, type, status, interfaces. */
const haystack = (r: ProductRow) =>
  [r.part_number, r.key, r.series, r.family, r.family_key, TYPE_LABEL[r.product_type], r.status, r.interfaces.join(" ")].filter(Boolean).join(" ").toLowerCase();
/** Search: every word must appear somewhere in the row (so "bmr316 active" finds Active parts of BMR316). */
export const matchesQuery = (r: ProductRow, q: string): boolean => q.toLowerCase().split(/\s+/).filter(Boolean).every((w) => haystack(r).includes(w));

export type Tri = "" | "yes" | "no";
export interface Filters { q: string; family: string; type: string; source: string; status: string; interface: string; image: Tri; documents: Tri; conflicts: Tri }
export const NO_FILTERS: Filters = { q: "", family: "", type: "", source: "", status: "", interface: "", image: "", documents: "", conflicts: "" };
export const activeFilters = (f: Filters): number => Object.values(f).filter(Boolean).length;
const tri = (t: Tri, has: boolean) => !t || (t === "yes") === has;

/** All filters combine with AND. */
export function filterRows(rows: ProductRow[], f: Filters, idx: MediaIndex): ProductRow[] {
  return rows.filter((r) => matchesQuery(r, f.q) && (!f.family || r.family === f.family) && (!f.type || r.product_type === f.type)
    && (!f.source || r.source === f.source) && (!f.status || r.status === f.status) && (!f.interface || r.interfaces.includes(f.interface))
    && tri(f.image, !!imageOf(r, idx)) && tri(f.documents, documentsOf(r, idx).length > 0) && tri(f.conflicts, r.has_conflict));
}

/** The values a filter offers, taken from the data with their counts: a value that no row has is never listed. */
export function facets(rows: ProductRow[]) {
  const count = (get: (r: ProductRow) => string | null | string[]) => {
    const m = new Map<string, number>();
    for (const r of rows) for (const v of [get(r)].flat()) if (v) m.set(v, (m.get(v) ?? 0) + 1);
    return [...m].sort((a, b) => a[0].localeCompare(b[0], "en", { numeric: true })).map(([value, n]) => ({ value, n }));
  };
  return { family: count((r) => r.family), type: count((r) => r.product_type), source: count((r) => r.source), status: count((r) => r.status), interface: count((r) => r.interfaces) };
}

// ---- pages -----------------------------------------------------------------------------------------------------------

export const PAGE_SIZES = [25, 50, 100, 200] as const;
export const DEFAULT_PAGE_SIZE = 50;
export function paginate<T>(rows: T[], page: number, size: number) {
  const pages = Math.max(1, Math.ceil(rows.length / size));
  const p = Math.min(Math.max(1, page), pages);
  return { page: p, pages, total: rows.length, from: rows.length ? (p - 1) * size + 1 : 0, to: Math.min(rows.length, p * size), items: rows.slice((p - 1) * size, p * size) };
}

/** Voltage range for a table cell: "38 – 60", one number when min and max agree, an em dash when unknown. */
export function range(lo: number | null, hi: number | null): string {
  if (lo === null && hi === null) return "—";
  if (lo === null || hi === null || lo === hi) return String(lo ?? hi);
  return `${lo} – ${hi}`;
}
