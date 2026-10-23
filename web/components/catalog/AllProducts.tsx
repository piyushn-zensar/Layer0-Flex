"use client";
// "All products" tab of the Product catalog (J-19, C-60): every product (spreadsheet parts and web catalog entries) in one table with
// search, filters, sort, pages, a column picker, and source / document / conflict / image badges.  Owner: Janvia.
// The logic is in products.ts (checked by products.check.mjs); the data is loaded by useProducts.ts.
import Link from "next/link";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import type { ProductRow } from "@/lib/types";
import { Alert, EmptyState, Skeleton } from "@/components/ui";
import ProductThumb from "./ProductThumb";
import { useProducts } from "./useProducts";
import {
  COLUMNS, DEFAULT_COLUMNS, DEFAULT_PAGE_SIZE, NO_FILTERS, PAGE_SIZES, SOURCE_LABEL, TYPE_LABEL, activeFilters, conflictsOf, documentsOf,
  facets, filterRows, paginate, parseColumns, range, sortRows,
  type Column, type ColumnId, type Filters, type MediaIndex, type Tri,
} from "./products";

const COLUMNS_KEY = "layer0.catalog.columns.v1";
const SIZE_KEY = "layer0.catalog.pagesize.v1";
const store = {
  get: (k: string) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k: string, v: string) => { try { localStorage.setItem(k, v); } catch { /* blocked: the choice lasts for this visit only */ } },
};

const Unknown = () => <span className="muted" title="Not in the data">—</span>;
const num = (v: number | null) => (v === null ? <Unknown /> : String(v));

function SourceBadge({ source }: { source: ProductRow["source"] }) {
  const tone = source === "both" ? "t-ok" : source === "web" ? "t-info" : "t-neutral";
  const why = source === "both" ? "Specifications from the Flex Power Modules spreadsheet, the series also listed on the Flex web pages"
    : source === "web" ? "Listed on the Flex web pages only; no spreadsheet rows for it" : "From the Flex Power Modules spreadsheet; the series is not on the Flex web pages";
  return <span className={`badge ${tone}`} title={why}>{SOURCE_LABEL[source]}</span>;
}

function DocumentsCell({ row, idx, ready }: { row: ProductRow; idx: MediaIndex; ready: boolean }) {
  const docs = documentsOf(row, idx);
  if (!docs.length) return ready || !row.family_key ? <span className="muted" title="No supplied document is linked to this product">None</span> : <span className="muted" title="Loading">…</span>;
  const tip = docs.map((d) => `${d.title} (${d.doc_type.replace("_", " ")}${d.applies === "general" ? ", portfolio document" : ""})`).join("\n");
  return <span className="badge t-info" title={tip} aria-label={`${docs.length} document${docs.length > 1 ? "s" : ""}: ${docs.map((d) => d.title).join("; ")}`}>{docs.length}</span>;
}

function ConflictsCell({ row, idx }: { row: ProductRow; idx: MediaIndex }) {
  if (!row.has_conflict) return <span className="muted" title="The spreadsheet and the web pages agree, or only one of them gives a value">None</span>;
  const list = conflictsOf(row, idx);
  const n = list.length || 1;
  const tip = list.length ? list.map((c) => `${c.field}: spreadsheet ${c.spreadsheet}, web ${c.web}`).join("\n") : "Spreadsheet and web page disagree";
  return <span className="badge t-pending" title={tip} aria-label={`${n} conflict${n > 1 ? "s" : ""}: ${list.map((c) => c.field).join(", ") || "details loading"}`}>{n}</span>;
}

const cell: Record<ColumnId, (r: ProductRow, idx: MediaIndex, ready: boolean) => React.ReactNode> = {
  image: (r, idx, ready) => <ProductThumb row={r} idx={idx} ready={ready} />,
  part: (r) => <><Link className="mono" href={`/catalog/product?part=${encodeURIComponent(r.key)}`} title="Open the product details">{r.part_number}</Link>
    {r.product_type === "web_listing" && <div className="muted mono">{r.key}</div>}</>,  // J-20: the details page
  family: (r) => r.family ? <>{r.family}{r.family_key && r.product_type !== "web_listing" && <div className="muted mono">{r.family_key}</div>}</> : <Unknown />,
  series: (r) => r.series ?? <Unknown />,
  type: (r) => <span className={`badge ${r.product_type === "web_listing" ? "t-info" : r.product_type === "evaluation_board" ? "t-pending" : "t-neutral"}`}>{TYPE_LABEL[r.product_type]}</span>,
  status: (r) => r.status ?? <Unknown />,
  vin: (r) => range(r.vin_min_v, r.vin_max_v) === "—" ? <Unknown /> : range(r.vin_min_v, r.vin_max_v),
  vout: (r) => range(r.vout_min_v, r.vout_max_v) === "—" ? <Unknown /> : range(r.vout_min_v, r.vout_max_v),
  power: (r) => num(r.power_w),
  current: (r) => num(r.current_a),
  efficiency: (r) => num(r.efficiency_pct),
  interfaces: (r) => r.interfaces.length ? r.interfaces.join(", ") : <Unknown />,
  source: (r) => <SourceBadge source={r.source} />,
  documents: (r, idx, ready) => <DocumentsCell row={r} idx={idx} ready={ready} />,
  conflicts: (r, idx) => <ConflictsCell row={r} idx={idx} />,
  family_key: (r) => r.family_key ? <span className="mono">{r.family_key}</span> : <Unknown />,
};

function ColumnPicker({ shown, onChange }: { shown: ColumnId[]; onChange: (c: ColumnId[]) => void }) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const button = useRef<HTMLButtonElement>(null);
  const panel = useId();
  useEffect(() => {
    if (!open) return;
    const away = (e: MouseEvent) => { if (!box.current?.contains(e.target as Node)) setOpen(false); };
    const key = (e: KeyboardEvent) => { if (e.key === "Escape") { setOpen(false); button.current?.focus(); } };
    document.addEventListener("mousedown", away); document.addEventListener("keydown", key);
    return () => { document.removeEventListener("mousedown", away); document.removeEventListener("keydown", key); };
  }, [open]);
  const toggle = (c: Column) => onChange(COLUMNS.map((x) => x.id).filter((id) => (id === c.id ? !shown.includes(id) : shown.includes(id))));
  const isDefault = shown.length === DEFAULT_COLUMNS.length && shown.every((c) => DEFAULT_COLUMNS.includes(c));
  return (
    <div className="col-picker" ref={box} data-tour="catalog-all-columns">
      <button ref={button} type="button" className="secondary" aria-expanded={open} aria-controls={panel} onClick={() => setOpen(!open)}>
        Columns <span className="muted">{shown.length} of {COLUMNS.length}</span></button>
      {open && (
        <div id={panel} className="col-panel card" role="group" aria-label="Choose the columns to show">
          {COLUMNS.map((c) => (
            <label key={c.id} className="check"><input type="checkbox" checked={shown.includes(c.id)} disabled={c.locked}
              onChange={() => toggle(c)} />{c.label}{c.locked && <span className="muted"> (always shown)</span>}</label>))}
          <div className="col-actions">
            <button type="button" className="secondary" disabled={isDefault} onClick={() => onChange(DEFAULT_COLUMNS)}>Reset to default</button>
            <button type="button" className="secondary" onClick={() => onChange(COLUMNS.map((c) => c.id))}>Show all</button>
          </div>
        </div>)}
    </div>
  );
}

function Select({ label, value, onChange, options, anyLabel, disabled, title, tour }:
  { label: string; value: string; onChange: (v: string) => void; options: { value: string; label: string }[]; anyLabel: string; disabled?: boolean; title?: string; tour?: string }) {
  return (
    <label className="filter-field" title={title}>{label}
      <select value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)} data-tour={tour}>
        <option value="">{anyLabel}</option>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  );
}

export default function AllProducts() {
  const { rows, idx, ready, progress, error, retry } = useProducts();
  const [filters, setFilters] = useState<Filters>(NO_FILTERS);
  const [sort, setSort] = useState<{ id: ColumnId; dir: "asc" | "desc" }>({ id: "part", dir: "asc" });
  const [page, setPage] = useState(1);
  const [size, setSize] = useState<number>(DEFAULT_PAGE_SIZE);
  const [shown, setShown] = useState<ColumnId[]>(DEFAULT_COLUMNS);
  useEffect(() => {                                    // saved choices are read after the first render, so server and browser agree
    setShown(parseColumns(store.get(COLUMNS_KEY)));
    const s = Number(store.get(SIZE_KEY));
    if ((PAGE_SIZES as readonly number[]).includes(s)) setSize(s);
  }, []);

  const change = (f: Partial<Filters>) => { setFilters((cur) => ({ ...cur, ...f })); setPage(1); };
  const all = rows ?? [];
  const f = useMemo(() => facets(all), [all]);
  const result = useMemo(() => sortRows(filterRows(all, filters, idx), sort.id, sort.dir, idx), [all, filters, sort, idx]);
  const pg = paginate(result, page, size);
  const columns = COLUMNS.filter((c) => shown.includes(c.id));
  const nFilters = activeFilters(filters);
  const opts = (xs: { value: string; n: number }[], label = (v: string) => v) => xs.map((x) => ({ value: x.value, label: `${label(x.value)} (${x.n})` }));
  const tri = (key: "image" | "documents" | "conflicts", label: string, yes: string, no: string, wait?: boolean) => (
    <Select label={label} value={filters[key]} onChange={(v) => change({ [key]: v as Tri })} anyLabel="Any" disabled={wait}
      title={wait ? "Available once the documents and images have loaded" : undefined} options={[{ value: "yes", label: yes }, { value: "no", label: no }]} />);

  const sortBy = (id: ColumnId) => { setSort((s) => ({ id, dir: s.id === id && s.dir === "asc" ? "desc" : "asc" })); setPage(1); };
  const setColumns = (c: ColumnId[]) => { setShown(c); store.set(COLUMNS_KEY, JSON.stringify(c)); };
  const setPageSize = (n: number) => { setSize(n); setPage(1); store.set(SIZE_KEY, String(n)); };

  if (error) return <Alert kind="error">{error} <button type="button" className="secondary" onClick={retry}>Try again</button></Alert>;
  if (!rows) return <Skeleton lines={6} />;
  if (all.length === 0) return <EmptyState title="The catalog has no products yet" hint="The spreadsheet import and the web catalog are both empty." />;

  return (
    <section data-tour="catalog-all">
      <p className="muted catalog-provenance">
        {all.length} products: {all.filter((r) => r.source !== "web").length} parts from the Flex Power Modules spreadsheet ({all.filter((r) => r.source === "both").length} of
        them in a series the Flex web pages list) and {all.filter((r) => r.product_type === "web_listing").length} products listed on the Flex web pages. Documents and images come from the supplied product PDFs and belong to a product's series, not to each part.
        {!ready && <> Loading documents and images ({progress[0]} of {progress[1]})…</>}
      </p>
      <div className="catalog-controls" data-tour="catalog-all-filters">
        <form role="search" className="inline catalog-search" onSubmit={(e) => e.preventDefault()} data-tour="catalog-all-search">
          <label><span className="sr-only">Search products by part number, family, series or catalog ID</span>
            <input type="search" value={filters.q} onChange={(e) => change({ q: e.target.value })} placeholder="Search part number, series, family, catalog ID" /></label>
        </form>
        <Select label="Family" value={filters.family} onChange={(v) => change({ family: v })} anyLabel={`All (${f.family.length})`} options={opts(f.family)} />
        <Select label="Type" value={filters.type} onChange={(v) => change({ type: v })} anyLabel="All" options={opts(f.type, (v) => TYPE_LABEL[v as ProductRow["product_type"]])} />
        <Select label="Source" value={filters.source} onChange={(v) => change({ source: v })} anyLabel="All" options={opts(f.source, (v) => SOURCE_LABEL[v as ProductRow["source"]])} />
        <Select label="Status" value={filters.status} onChange={(v) => change({ status: v })} anyLabel="All" options={opts(f.status)} />
        {f.interface.length > 0 && <Select label="Interface" value={filters.interface} onChange={(v) => change({ interface: v })} anyLabel="All" options={opts(f.interface)} />}
        {tri("image", "Image", "With a verified image", "Without", !ready)}
        {tri("documents", "Documents", "With documents", "Without", !ready)}
        {tri("conflicts", "Conflicts", "With conflicts", "Without conflicts")}
        <button type="button" className="secondary" disabled={nFilters === 0} onClick={() => { setFilters(NO_FILTERS); setPage(1); }}>Clear filters{nFilters > 0 && ` (${nFilters})`}</button>
        <ColumnPicker shown={shown} onChange={setColumns} />
      </div>

      <div className="toolbar">
        <p className="muted" role="status" aria-live="polite" data-tour="catalog-all-count">
          {pg.total === 0 ? "No product matches" : `Showing ${pg.from}–${pg.to} of ${pg.total} product${pg.total > 1 ? "s" : ""}`}{nFilters > 0 && ` (filtered from ${all.length})`}</p>
        <label className="inline">Rows per page
          <select value={size} onChange={(e) => setPageSize(Number(e.target.value))}>{PAGE_SIZES.map((n) => <option key={n} value={n}>{n}</option>)}</select></label>
      </div>

      {pg.total === 0 ? (
        <EmptyState title="No product matches" hint="Try fewer filters or another search word.">
          <button type="button" onClick={() => { setFilters(NO_FILTERS); setPage(1); }}>Clear filters</button>
        </EmptyState>
      ) : (
        <div className="table-scroll catalog-table-wrap" role="region" aria-label="Products table (scrolls sideways when the columns do not fit)" tabIndex={0} data-tour="catalog-all-table">
          <table className="dense catalog-table">
            <thead><tr>{columns.map((c) => (
              <th key={c.id} scope="col" className={`${c.num ? "num" : ""} ${c.id === "part" ? "sticky-col" : ""}`.trim()}
                aria-sort={sort.id === c.id ? (sort.dir === "asc" ? "ascending" : "descending") : "none"}>
                <button type="button" className="th-sort" onClick={() => sortBy(c.id)} title={`Sort by ${c.label}`}>
                  {c.label}<span aria-hidden="true" className="th-arrow">{sort.id === c.id ? (sort.dir === "asc" ? "▲" : "▼") : ""}</span></button>
              </th>))}</tr></thead>
            <tbody>{pg.items.map((r) => (
              <tr key={r.key}>{columns.map((c) => (
                <td key={c.id} className={`${c.num ? "num" : ""} ${c.id === "part" ? "sticky-col" : ""}`.trim()}>{cell[c.id](r, idx, ready)}</td>))}</tr>))}
            </tbody>
          </table>
        </div>)}

      {pg.total > 0 && (
        <nav className="pager" aria-label="Product pages" data-tour="catalog-all-pager">
          <button type="button" className="secondary" disabled={pg.page <= 1} onClick={() => setPage(1)} aria-label="First page">«</button>
          <button type="button" className="secondary" disabled={pg.page <= 1} onClick={() => setPage(pg.page - 1)}>Previous</button>
          <span>Page {pg.page} of {pg.pages}</span>
          <button type="button" className="secondary" disabled={pg.page >= pg.pages} onClick={() => setPage(pg.page + 1)}>Next</button>
          <button type="button" className="secondary" disabled={pg.page >= pg.pages} onClick={() => setPage(pg.pages)} aria-label="Last page">»</button>
        </nav>)}
    </section>
  );
}
