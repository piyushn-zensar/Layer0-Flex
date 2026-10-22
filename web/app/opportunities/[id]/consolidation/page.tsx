"use client";
// Compliance matrix: what still needs an answer, and one row per requirement and unit answer, with filters.  Owner: Janvia.
// Rows come from GET /api/bids/{id}/compliance-matrix (J-11). Filtering is in the browser (a few hundred rows);
// only the first PAGE rows are drawn, "Show more" adds the next ones.
import Link from "next/link";
import { useParams } from "next/navigation";
import { memo, useCallback, useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import { useApi } from "@/lib/api";
import { categoryLabel, complianceLabel, docTypeLabel } from "@/lib/types";
import type { Doc } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { Alert, EmptyState, Skeleton, StatusBadge } from "@/components/ui";
import ComplianceBadge from "./_components/ComplianceBadge";
import DetailPanel from "./_components/DetailPanel";
import { rowKey, type MatrixRow } from "./_components/types";

type Matrix = { rows: MatrixRow[]; total: number; answered: number; blocking: string[] };

// Why a requirement is not answered yet, in the order the groups are shown.
const REASONS = [
  { key: "validation", label: "Waiting for validation" },
  { key: "unit", label: "Waiting for the unit" },
  { key: "returned", label: "Returned" },
  { key: "unassigned", label: "Not assigned" },
] as const;
type Reason = (typeof REASONS)[number]["key"];

// Derived from a requirement's rows. A returned response outranks an unanswered one, which outranks a submitted one.
function reasonOf(rows: MatrixRow[]): Reason | null {
  const { state, assignments } = rows[0];
  if (state === "answered") return null;
  if (assignments === 0) return "unassigned";
  const status = rows.map((r) => r.status);
  if (status.includes("returned")) return "returned";
  if (status.includes("assigned")) return "unit";
  return "validation";
}

const SHOWN = 10;  // links shown per blocker group before "more"
const PAGE = 100;  // table rows drawn at first, and added by each "Show more"
const NONE = "__none";
const STATES = [{ value: "answered", label: "Answered" }, { value: "pending", label: "Pending" }, { value: "not_assigned", label: "Not assigned" }];
const HELP = "Every requirement must be answered by its business unit and validated before the response is complete.";
const NO_FILTER = { q: "", unit: "", compliance: "", state: "", category: "", onlyOpen: false };
type Filters = typeof NO_FILTER;

// A row is a button for the keyboard: Enter or Space on the row itself selects it (links, badges and buttons inside keep their own keys).
const Row = memo(function Row({ row, href, selected, onSelect }: { row: MatrixRow; href: string; selected: boolean; onSelect: (key: string, history?: boolean) => void }) {
  const key = rowKey(row);
  return (
    <tr data-key={key} tabIndex={0} aria-current={selected ? "true" : undefined}
      className={`${row.state !== "answered" ? "blocking" : ""}${selected ? " selected" : ""}`.trim()}
      onClick={(e) => { if (!(e.target as HTMLElement).closest("a")) onSelect(key); }}
      onKeyDown={(e) => { if (e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); onSelect(key); } }}>
      <td className="mono"><Link href={href} title="Open in Traceability">{row.req_id}</Link></td>
      <td>{row.requirement}</td>
      <td data-label="Category"><span className="tag">{categoryLabel(row.category)}</span></td>
      <td data-label="Unit">{row.unit
        ? <><strong>{row.unit}</strong><div className="muted">{row.unit_name}</div>{row.solution?.area && <div className="muted">{row.solution.area}</div>}</>
        : <span className="muted">not assigned</span>}</td>
      <td data-label="Response">{row.status ? <StatusBadge status={row.status} /> : <StatusBadge status={row.state} />}
        {row.response && <div className="muted cons-response" title={row.response}>{row.response}</div>}
        {row.assignment_id != null && <button type="button" className="link row-history" onClick={(e) => { e.stopPropagation(); onSelect(key, true); }}
          aria-label={`Show the history of ${row.req_id} for ${row.unit}`}>History</button>}</td>
      <td data-label="Compliance">{row.compliance ? <ComplianceBadge row={row} /> : <span className="muted">{row.unit ? "No compliance yet" : ""}</span>}</td>
      <td className="muted" data-label="Source">{row.source}</td>
    </tr>
  );
});

export default function ConsolidationPage() {
  const { id } = useParams<{ id: string }>();
  const { data: matrix, error } = useApi<Matrix>(`/api/bids/${id}/compliance-matrix`);
  const [f, setFilters] = useState<Filters>(NO_FILTER);
  const [limit, setLimit] = useState(PAGE);
  const q = useDeferredValue(f.q).trim().toLowerCase();
  const rows = matrix?.rows;
  const { data: opp } = useApi<{ documents: Doc[] }>(`/api/bids/${id}`); // file names for the detail's source line
  const [selectedKey, setSelectedKey] = useState<string>();
  const headingRef = useRef<HTMLHeadingElement>(null);
  const [historyOpen, setHistoryOpen] = useState(false); // the table's "History" link opens the row with its history showing
  const select = useCallback((key: string, history = false) => { setSelectedKey(key); setHistoryOpen(history); }, []);
  const selected = useMemo(() => rows?.find((r) => rowKey(r) === selectedKey), [rows, selectedKey]);
  const close = useCallback(() => {
    const key = selectedKey;
    setSelectedKey(undefined);
    // back to the row that was open (the table may have changed meanwhile: then focus simply stays where it is)
    requestAnimationFrame(() => document.querySelector<HTMLElement>(`tr[data-key="${key}"]`)?.focus());
  }, [selectedKey]);
  useEffect(() => { if (selectedKey) headingRef.current?.focus({ preventScroll: false }); }, [selectedKey]); // the panel announces itself
  useEffect(() => {
    if (!selectedKey) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape" && !e.defaultPrevented) close(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [selectedKey, close]);

  // Per requirement: its rows, and why it is open. Search text is lower-cased once per row, not on every keystroke.
  const byReq = useMemo(() => {
    const m = new Map<string, MatrixRow[]>();
    for (const r of rows ?? []) m.set(r.req_id, [...(m.get(r.req_id) ?? []), r]);
    return m;
  }, [rows]);
  const reasons = useMemo(() => new Map([...byReq].map(([k, v]) => [k, reasonOf(v)] as const)), [byReq]);
  const haystack = useMemo(() => (rows ?? []).map((r) => [r.req_id, r.requirement, r.quote, r.source, r.unit, r.unit_name, r.solution?.area, r.response, r.category]
    .filter(Boolean).join(" ").toLowerCase()), [rows]);
  const options = useMemo(() => {
    const units = new Map<string, string>();
    for (const r of rows ?? []) if (r.unit) units.set(r.unit, r.unit_name);
    const compliance = ["met", "partial", "deviation", "not_met", "exception"].filter((c) => rows?.some((r) => r.compliance === c));
    return { units: [...units].sort(([a], [b]) => a.localeCompare(b)), compliance, categories: [...new Set((rows ?? []).map((r) => r.category))].sort(),
      unassigned: !!rows?.some((r) => !r.unit), unanswered: !!rows?.some((r) => r.unit && !r.compliance) };
  }, [rows]);

  const head = <PageHead level={2} title="Compliance matrix" help={HELP} />;
  if (error) return <>{head}<Alert kind="error">{error}</Alert></>;
  if (!matrix || !rows) return <>{head}<Skeleton lines={4} /></>;

  const set = (patch: Partial<Filters>) => { setFilters((p) => ({ ...p, ...patch })); setLimit(PAGE); };
  const filtered = rows.filter((r, i) =>
    (!f.onlyOpen || reasons.get(r.req_id)) && (!q || haystack[i].includes(q)) && (!f.category || r.category === f.category) &&
    (!f.state || r.state === f.state) &&
    (!f.unit || (f.unit === NONE ? !r.unit : r.unit === f.unit)) &&
    (!f.compliance || (f.compliance === NONE ? !r.compliance : r.compliance === f.compliance)));
  const filtering = JSON.stringify(f) !== JSON.stringify(NO_FILTER);
  const drawn = filtered.slice(0, limit);

  const openIds = [...reasons].filter(([, why]) => why);
  const groups = REASONS.map((g) => ({ ...g, ids: openIds.filter(([, why]) => why === g.key).map(([k]) => k) })).filter((g) => g.ids.length);
  const traceHref = (reqId: string) => `/opportunities/${id}/trace#${reqId}`;
  const link = (reqId: string) => <Link key={reqId} className="mono" href={traceHref(reqId)} title="Open in Traceability">{reqId}</Link>;

  return (
    <>
      {/* UX-12: the downloads and the outline are page actions, not part of the sentence */}
      <PageHead level={2} title="Compliance matrix" help={HELP}>
        <Link className="button secondary" href={`/opportunities/${id}/consolidation/outline`} data-tour="cons-outline-link">Response outline (draft)</Link>
        <Link className="button secondary" href={`/opportunities/${id}/consolidation/activity`} data-tour="cons-activity-link">Activity log</Link>
        <a className="button secondary" href={`/api/bids/${id}/compliance-matrix.csv`} data-tour="cons-csv">CSV</a>
        <a className="button" href={`/api/bids/${id}/compliance-matrix.xlsx`} data-tour="cons-xlsx">Download compliance matrix (Excel)</a>
      </PageHead>
      <p className="cons-summary" data-tour="cons-summary"><strong>{matrix.answered} / {matrix.total}</strong> requirements answered.{" "}
        {matrix.blocking.length ? <span className="warn">{matrix.blocking.length} still need an answer.</span> : <span className="ok">Every requirement is answered.</span>}</p>

      {groups.length > 0 && (
        <section className="cons-blockers" aria-label="Requirements that still need an answer" data-tour="cons-blockers">
          <h3>Needs an answer</h3>
          {groups.map((g) => (
            <div key={g.key} className="cons-group">
              <span className="cons-group-label">{g.label} <span>({g.ids.length})</span></span>
              <span className="cons-ids">
                {g.ids.slice(0, SHOWN).map(link)}
                {g.ids.length > SHOWN && <details className="cons-more"><summary>{g.ids.length - SHOWN} more</summary><span className="cons-ids">{g.ids.slice(SHOWN).map(link)}</span></details>}
              </span>
            </div>
          ))}
        </section>
      )}

      {rows.length === 0 ? (
        <div data-tour="cons-empty">
          <EmptyState title="No frozen requirements yet" hint="Read the RFP first: its register is frozen then, and the coverage check runs against them.">
            <Link className="button secondary" href={`/opportunities/${id}/trace`}>Requirement Traceability</Link>
          </EmptyState>
        </div>
      ) : (
        <>
          <div className="matrix-filters" role="search" aria-label="Filter the compliance matrix" data-tour="cons-filter">
            <label className="mf-search">Search
              <input type="search" value={f.q} placeholder="Requirement, ID, unit, proposed solution, response…" onChange={(e) => set({ q: e.target.value })} />
            </label>
            <label>Unit
              <select value={f.unit} onChange={(e) => set({ unit: e.target.value })}>
                <option value="">All units</option>
                {options.units.map(([code, name]) => <option key={code} value={code}>{code} · {name}</option>)}
                {options.unassigned && <option value={NONE}>Not assigned</option>}
              </select>
            </label>
            <label>Compliance
              <select value={f.compliance} onChange={(e) => set({ compliance: e.target.value })}>
                <option value="">All</option>
                {options.compliance.map((c) => <option key={c} value={c}>{complianceLabel(c)}</option>)}
                {(options.unanswered || options.unassigned) && <option value={NONE}>No compliance yet</option>}
              </select>
            </label>
            <label>State
              <select value={f.state} onChange={(e) => set({ state: e.target.value })}>
                <option value="">All</option>
                {STATES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            </label>
            <label>Category
              <select value={f.category} onChange={(e) => set({ category: e.target.value })}>
                <option value="">All</option>
                {options.categories.map((c) => <option key={c} value={c}>{categoryLabel(c)}</option>)}
              </select>
            </label>
            <div className="mf-actions">
              <button type="button" className="chip" aria-pressed={f.onlyOpen} onClick={() => set({ onlyOpen: !f.onlyOpen })}>Open only <span>{openIds.length}</span></button>
              <button type="button" className="secondary sm" disabled={!filtering} onClick={() => { setFilters(NO_FILTER); setLimit(PAGE); }}>Clear filters</button>
            </div>
          </div>
          <p className="muted matrix-count" role="status" aria-live="polite">
            {filtering ? `${filtered.length} of ${rows.length} rows match` : `${rows.length} rows`}
            {drawn.length < filtered.length && `, showing the first ${drawn.length}`}
          </p>

          <div className={`matrix-layout${selected ? " has-detail" : ""}`}>
          <div className="matrix-main">
          <div className="table-scroll">
            <table className="cons-table stack-sm" data-tour="cons-table">
              <thead><tr>
                <th className="col-id">ID</th><th>Requirement</th><th className="col-cat">Category</th>
                <th className="col-units" data-tour="cons-col-units">Unit</th>
                <th className="col-state" data-tour="cons-col-state">Response</th>
                <th className="col-comp">Compliance</th><th className="col-src">Source</th>
              </tr></thead>
              <tbody>
                {drawn.map((r) => <Row key={rowKey(r)} row={r} href={traceHref(r.req_id)} selected={rowKey(r) === selectedKey} onSelect={select} />)}
                {filtered.length === 0 && (
                  <tr><td colSpan={7} className="matrix-empty">
                    {filtering ? <>No rows match these filters. <button type="button" className="link" onClick={() => { setFilters(NO_FILTER); setLimit(PAGE); }}>Clear filters</button></>
                      : "Every requirement is answered."}
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
          {drawn.length < filtered.length && (
            <p className="matrix-more"><button type="button" className="secondary" onClick={() => setLimit(limit + PAGE)}>
              Show {Math.min(PAGE, filtered.length - drawn.length)} more ({filtered.length - drawn.length} not shown)</button></p>
          )}
          </div>
          {selected && (() => {
            const doc = opp?.documents.find((d) => d.id === selected.document_id);
            return <DetailPanel ref={headingRef} row={selected} traceHref={traceHref(selected.req_id)} onClose={close} historyOpen={historyOpen}
              activityHref={`/opportunities/${id}/consolidation/activity?req_id=${encodeURIComponent(selected.req_id)}`}
              docName={doc ? `${doc.filename}${doc.role !== "main" ? ` (${docTypeLabel(doc.role)})` : ""}` : "RFP document"} />;
          })()}
          </div>
        </>
      )}
    </>
  );
}
