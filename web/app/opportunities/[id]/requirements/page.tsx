"use client";
// Requirement review: approve, reject, edit, split, merge, ungroup, add missed (select lines or paste a quote); then
// freeze the baseline.  Owner: Piyush.
// Requirements are shown in document order; a group lists its sub-requirements when expanded.
import Link from "next/link";
import { useParams } from "next/navigation";
import { Fragment, useMemo, useState } from "react";
import PageHead from "@/components/shell/PageHead";
import LinePicker from "@/components/requirements/LinePicker"; // P-15
import { post, useApi } from "@/lib/api";
import type { Baseline, Requirement, RequirementHistory } from "@/lib/types";

const CATEGORIES = ["technical", "compliance", "commercial", "schedule", "submission", "legal", "staffing"];
const FILTERS = {
  review: { label: "To review", test: (r: Requirement) => r.status === "proposed" },
  unanchored: { label: "Unanchored", test: (r: Requirement) => r.provenance === "UNANCHORED" && !INACTIVE.has(r.status) },
  approved: { label: "Approved", test: (r: Requirement) => r.status === "approved" },
  rejected: { label: "Rejected", test: (r: Requirement) => r.status === "rejected" },
  duplicates: { label: "Duplicates", test: (r: Requirement) => r.status === "duplicate" },
  replaced: { label: "Ungrouped / split / merged", test: (r: Requirement) => r.status === "split" || r.status === "merged" },
  all: { label: "All", test: () => true },
} as const;
const INACTIVE = new Set(["rejected", "split", "merged", "duplicate", "removed"]); // removed: by a change document (P-11)
type FilterKey = keyof typeof FILTERS;

export default function RequirementsPage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, reload } = useApi<{ requirements: Requirement[]; baseline: Baseline | null }>(`/api/opportunities/${id}/requirements`);
  const [chosen, setFilter] = useState<FilterKey>();
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [editing, setEditing] = useState<{ id: string; mode: "edit" | "split" }>();
  const [historyOf, setHistoryOf] = useState<string>();
  const [open, setOpen] = useState<Set<string>>(new Set());
  const [adding, setAdding] = useState(false); // the "add missed" section is open: its page viewer loads only then

  const filter: FilterKey = chosen ?? (data?.baseline ? "all" : "review"); // frozen: nothing left to review
  const all = useMemo(() => (data?.requirements ?? []).filter((r) => !r.parent_id), [data]); // requirements, not sub-requirements
  const kidsOf = useMemo(() => {
    const m = new Map<string, Requirement[]>();
    for (const r of data?.requirements ?? []) if (r.parent_id) m.set(r.parent_id, [...(m.get(r.parent_id) ?? []), r]);
    return m;
  }, [data]);
  const rows = useMemo(() => {
    const q = query.toLowerCase();
    const hit = (r: Requirement) => `${r.req_id} ${r.text} ${r.quote}`.toLowerCase().includes(q);
    return all.filter((r) => FILTERS[filter].test(r) && (!q || hit(r) || (kidsOf.get(r.req_id) ?? []).some(hit)));
  }, [all, kidsOf, filter, query]);
  if (error) return <p className="warn">{error}</p>;
  if (!data) return <p>Loading…</p>;

  const frozen = !!data.baseline;
  const undecided = all.filter(FILTERS.review.test).length;
  const done = () => { setSelected(new Set()); setEditing(undefined); return reload(); };
  // One action at a time; on failure the form stays open with what was typed, and the API's message is shown.
  const act = (p: Promise<unknown>) => { setBusy(true); return p.then(done, (e) => alert(e instanceof Error ? e.message : e)).finally(() => setBusy(false)); };
  const review = (reqId: string, body: object) => act(post(`/api/requirements/${reqId}/review`, body));
  const bulk = (action: string) => act(Promise.all([...selected].map((r) => post(`/api/requirements/${r}/review`, { action }))));
  const merge = () => {
    const text = prompt(`One-line text for the merged requirement (${selected.size} items):`);
    if (text) act(post(`/api/opportunities/${id}/requirements/merge`, { req_ids: [...selected], text }));
  };
  const flip = (set: Set<string>, reqId: string) => { const n = new Set(set); if (n.has(reqId)) n.delete(reqId); else n.add(reqId); return n; };
  const toggle = (reqId: string) => setSelected((s) => flip(s, reqId));
  const cols = frozen ? 4 : 6;
  // P-15: the line picker opens on the page of a selected requirement, else of the first one in view
  const startPage = (all.find((r) => selected.has(r.req_id) && r.page) ?? rows.find((r) => r.page))?.page ?? 1;

  const line = (r: Requirement, child = false) => {
    const active = !INACTIVE.has(r.status) && r.baseline === null;
    const isEditing = editing?.id === r.req_id;
    const kids = kidsOf.get(r.req_id) ?? [];
    const group = r.kind === "group";
    return (
      <Fragment key={r.req_id}>
        <tr className={`${INACTIVE.has(r.status) ? "inactive" : ""} ${child ? "child" : ""} ${group ? "group" : ""}`}>
          {!frozen && <td>{active && !child && <input type="checkbox" aria-label={`Select ${r.req_id}`} checked={selected.has(r.req_id)} onChange={() => toggle(r.req_id)} />}</td>}
          <td><div className="mono">{r.req_id}</div><span className="tag">{r.category}</span></td>
          <td>{r.page ? <Link href={`/opportunities/${id}/trace#${r.parent_id ?? r.req_id}`}>{r.source}</Link> : r.source}
            {r.provenance === "UNANCHORED" && <div className="warn">Not found on the page</div>}</td>
          <td>
            {isEditing && editing.mode === "edit" ? (
              <form className="form compact" action={(f) => review(r.req_id, { action: "edit", text: f.get("text"), category: f.get("category") })}>
                <input name="text" defaultValue={r.text} aria-label="Requirement text" />
                <select name="category" defaultValue={r.category} aria-label="Category">{CATEGORIES.map((c) => <option key={c}>{c}</option>)}</select>
                <span className="inline"><button>Save</button><button type="button" className="secondary" onClick={() => setEditing(undefined)}>Cancel</button></span>
              </form>
            ) : isEditing && editing.mode === "split" ? (
              <form className="form compact" action={(f) => act(post(`/api/requirements/${r.req_id}/split`, {
                parts: String(f.get("parts")).split("\n").map((q) => ({ quote: q.trim() })).filter((p) => p.quote) }))}>
                <label>Put each part of the quote on its own line
                  <textarea name="parts" rows={4} defaultValue={r.quote} /></label>
                <span className="inline"><button>Split</button><button type="button" className="secondary" onClick={() => setEditing(undefined)}>Cancel</button></span>
              </form>
            ) : (<>
              <div className={group ? "group-title" : ""}>{r.text}</div>
              {group ? (
                <button type="button" className="link expand" aria-expanded={open.has(r.req_id)} onClick={() => setOpen((s) => flip(s, r.req_id))}>
                  {open.has(r.req_id) ? "▾" : "▸"} {kids.length} sub-requirements</button>
              ) : <div className="quote">“{r.quote}”</div>}
              {r.status === "duplicate" ? <div className="muted">Duplicate of {r.derived_from.join(", ")}: approve to keep it anyway</div>
                : r.derived_from?.length > 0 && <div className="muted">From {r.derived_from.join(", ")}</div>}
            </>)}
          </td>
          <td><span className={`badge status-${r.status}`}>{r.status}</span>
            <button type="button" className="link" aria-expanded={historyOf === r.req_id}
              onClick={() => setHistoryOf(historyOf === r.req_id ? undefined : r.req_id)}>History</button></td>
          {!frozen && <td>{(active || r.status === "duplicate") && !isEditing && (
            <div className="row-actions">
              {r.status !== "approved" && <button onClick={() => review(r.req_id, { action: "approve" })}>Approve</button>}
              {active && r.status !== "rejected" && <button className="secondary" onClick={() => review(r.req_id, { action: "reject" })}>Reject</button>}
              {active && <button className="secondary" onClick={() => setEditing({ id: r.req_id, mode: "edit" })}>Edit</button>}
              {active && !group && !child && <button className="secondary" onClick={() => setEditing({ id: r.req_id, mode: "split" })}>Split</button>}
              {active && group && <button className="secondary" onClick={() => act(post(`/api/requirements/${r.req_id}/ungroup`))}>Ungroup</button>}
            </div>)}</td>}
        </tr>
        {historyOf === r.req_id && <tr className="history-row"><td colSpan={cols}><History reqId={r.req_id} /></td></tr>}
        {group && open.has(r.req_id) && kids.map((k) => line(k, true))}
      </Fragment>
    );
  };

  return (
    <>
      <PageHead level={2} title="Requirements"
        help={frozen ? `Baseline ${data.baseline!.number} frozen by ${data.baseline!.frozen_by} (${data.baseline!.count} items). Later changes run as a delta.`
          : `${all.filter((r) => !INACTIVE.has(r.status)).length} requirements; related line items are grouped (expand a group to see its sub-requirements). Check each against its source, then freeze the baseline.`}>
        {!frozen && <button disabled={busy || undecided > 0} title={undecided ? `${undecided} line items still need a decision` : ""}
          onClick={() => act(post(`/api/opportunities/${id}/baselines`))}>Freeze baseline</button>}
      </PageHead>

      <div className="filters" role="tablist" aria-label="Filter line items">
        {(Object.keys(FILTERS) as FilterKey[]).map((k) => (
          <button key={k} role="tab" aria-selected={filter === k} className={`chip ${filter === k ? "on" : ""}`} onClick={() => setFilter(k)}>
            {FILTERS[k].label} <span>{all.filter(FILTERS[k].test).length}</span>
          </button>
        ))}
        <input type="search" placeholder="Search ID or text" value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Search line items" />
      </div>

      {!frozen && selected.size > 0 && (
        <div className="bulkbar" role="region" aria-label="Selected line items">
          <strong>{selected.size} selected</strong>
          <button onClick={() => bulk("approve")}>Approve</button>
          <button className="secondary" onClick={() => bulk("reject")}>Reject</button>
          <button className="secondary" disabled={selected.size < 2} onClick={merge}>Merge into one</button>
          <button className="secondary" onClick={() => setSelected(new Set())}>Clear</button>
        </div>
      )}

      <table className="req-table">
        <thead><tr>
          {!frozen && <th className="col-check"><span className="sr-only">Select</span></th>}
          <th className="col-id">ID</th><th className="col-src">Source</th><th>Requirement</th><th className="col-status">Status</th>{!frozen && <th className="col-actions" />}
        </tr></thead>
        <tbody>
          {rows.map((r) => line(r))}
          {rows.length === 0 && <tr><td colSpan={cols} className="muted">No requirements in this view.</td></tr>}
        </tbody>
      </table>

      {!frozen && (
        <details className="card" onToggle={(e) => setAdding(e.currentTarget.open)}>
          <summary><strong>Add a requirement the agent missed</strong></summary>
          <h3 className="lp-heading">Select its lines on the RFP page</h3>
          {adding && <LinePicker oppId={id} startPage={startPage} categories={CATEGORIES} onAdded={reload}
            requirements={(data.requirements ?? []).filter((r) => !INACTIVE.has(r.status))} />}
          <h3 className="lp-heading">Or paste the quote</h3>
          <form className="form" action={(f) => act(post(`/api/opportunities/${id}/requirements`, {
            quote: f.get("quote"), text: f.get("text"), category: f.get("category"), page: Number(f.get("page")) || null }))}>
            <label className="grow">Quote, copied from the RFP <textarea name="quote" rows={2} required /></label>
            <label>Short text <input name="text" /></label>
            <label>Category <select name="category">{CATEGORIES.map((c) => <option key={c}>{c}</option>)}</select></label>
            <label>Page (optional) <input name="page" type="number" min={1} className="narrow" /></label>
            <button disabled={busy}>Add</button>
          </form>
        </details>
      )}
    </>
  );
}

/** Every version of a line item (who, when, what changed) and everything that happened to it, from the audit log. */
function History({ reqId }: { reqId: string }) {
  const { data, error } = useApi<RequirementHistory>(`/api/requirements/${reqId}/history`);
  if (error) return <p className="warn">{error}</p>;
  if (!data) return <p className="muted">Loading history…</p>;
  const when = (t: string) => new Date(t.endsWith("Z") || t.includes("+") ? t : `${t}Z`).toLocaleString();
  return (
    <div className="history">
      <div>
        <h3>Versions ({data.versions.length})</h3>
        <ol className="versions">
          {data.versions.map((v) => (
            <li key={v.n}>
              <div className="muted">v{v.n} · {v.label} by <strong>{v.by}</strong> · {when(v.at)}{v.reason ? ` · reason: ${v.reason}` : ""}</div>
              <div>{v.text} <span className="tag">{v.category}</span></div>
            </li>
          ))}
        </ol>
        <p className="quote">Source ({data.source}): “{data.quote}”</p>
        {data.derived_from.length > 0 && <p className="muted">Created from {data.derived_from.join(", ")}</p>}
      </div>
      <div>
        <h3>Timeline</h3>
        <ul className="timeline">
          {data.events.map((e, i) => (
            <li key={i}><span className="muted">{when(e.at)}</span> <strong>{e.action.replace("_", " ")}</strong> by {e.by}
              {Object.entries(e.details).filter(([, v]) => v !== "" && !(Array.isArray(v) && v.length === 0)).map(([k, v]) =>
                <span key={k} className="muted"> · {k.replace("_", " ")}: {Array.isArray(v) ? v.join(", ") : String(v)}</span>)}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
