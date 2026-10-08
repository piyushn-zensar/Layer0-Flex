"use client";
// Requirement review: approve, reject, edit, split, merge, add missed; then freeze the baseline.  Owner: Piyush.
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import PageHead from "@/components/shell/PageHead";
import { post, useApi } from "@/lib/api";
import type { Baseline, Requirement } from "@/lib/types";

const CATEGORIES = ["technical", "compliance", "commercial", "schedule", "submission", "legal", "staffing"];
const FILTERS = {
  review: { label: "To review", test: (r: Requirement) => r.status === "proposed" },
  unanchored: { label: "Unanchored", test: (r: Requirement) => r.provenance === "UNANCHORED" && !INACTIVE.has(r.status) },
  approved: { label: "Approved", test: (r: Requirement) => r.status === "approved" },
  rejected: { label: "Rejected", test: (r: Requirement) => r.status === "rejected" },
  replaced: { label: "Split / merged", test: (r: Requirement) => r.status === "split" || r.status === "merged" },
  all: { label: "All", test: () => true },
} as const;
const INACTIVE = new Set(["rejected", "split", "merged"]);
type FilterKey = keyof typeof FILTERS;

export default function RequirementsPage() {
  const { id } = useParams<{ id: string }>();
  const { data, reload } = useApi<{ requirements: Requirement[]; baseline: Baseline | null }>(`/api/opportunities/${id}/requirements`);
  const [filter, setFilter] = useState<FilterKey>("review");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [editing, setEditing] = useState<{ id: string; mode: "edit" | "split" }>();

  const all = useMemo(() => data?.requirements ?? [], [data]);
  const rows = useMemo(() => all.filter((r) => FILTERS[filter].test(r)
    && (!query || `${r.req_id} ${r.text} ${r.quote}`.toLowerCase().includes(query.toLowerCase()))), [all, filter, query]);
  if (!data) return <p>Loading…</p>;

  const frozen = !!data.baseline;
  const undecided = all.filter(FILTERS.review.test).length;
  const done = () => { setSelected(new Set()); setEditing(undefined); return reload(); };
  const act = (p: Promise<unknown>) => p.then(done, (e) => alert(e));
  const review = (reqId: string, body: object) => act(post(`/api/requirements/${reqId}/review`, body));
  const bulk = (action: string) => act(Promise.all([...selected].map((r) => post(`/api/requirements/${r}/review`, { action }))));
  const merge = () => {
    const text = prompt(`One-line text for the merged requirement (${selected.size} items):`);
    if (text) act(post(`/api/opportunities/${id}/requirements/merge`, { req_ids: [...selected], text }));
  };
  const toggle = (reqId: string) => setSelected((s) => { const n = new Set(s); if (n.has(reqId)) n.delete(reqId); else n.add(reqId); return n; });

  return (
    <>
      <PageHead level={2} title="Requirements"
        help={frozen ? `Baseline ${data.baseline!.number} frozen by ${data.baseline!.frozen_by} (${data.baseline!.count} items). Later changes run as a delta.`
          : "Check each line item against its source: approve, reject, edit, split or merge. Then freeze the baseline."}>
        {!frozen && <button disabled={undecided > 0} title={undecided ? `${undecided} line items still need a decision` : ""}
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
          {rows.map((r) => {
            const active = !INACTIVE.has(r.status) && r.baseline === null;
            const isEditing = editing?.id === r.req_id;
            return (
              <tr key={r.req_id} className={INACTIVE.has(r.status) ? "inactive" : ""}>
                {!frozen && <td>{active && <input type="checkbox" aria-label={`Select ${r.req_id}`} checked={selected.has(r.req_id)} onChange={() => toggle(r.req_id)} />}</td>}
                <td><div className="mono">{r.req_id}</div><span className="tag">{r.category}</span></td>
                <td>{r.page ? <Link href={`/opportunities/${id}/trace#${r.req_id}`}>{r.source}</Link> : r.source}
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
                    <div>{r.text}</div>
                    <div className="quote">“{r.quote}”</div>
                    {r.derived_from?.length > 0 && <div className="muted">From {r.derived_from.join(", ")}</div>}
                  </>)}
                </td>
                <td><span className={`badge status-${r.status}`}>{r.status}</span></td>
                {!frozen && <td>{active && !isEditing && (
                  <div className="row-actions">
                    {r.status !== "approved" && <button onClick={() => review(r.req_id, { action: "approve" })}>Approve</button>}
                    {r.status !== "rejected" && <button className="secondary" onClick={() => review(r.req_id, { action: "reject" })}>Reject</button>}
                    <button className="secondary" onClick={() => setEditing({ id: r.req_id, mode: "edit" })}>Edit</button>
                    <button className="secondary" onClick={() => setEditing({ id: r.req_id, mode: "split" })}>Split</button>
                  </div>)}</td>}
              </tr>
            );
          })}
          {rows.length === 0 && <tr><td colSpan={6} className="muted">No line items in this view.</td></tr>}
        </tbody>
      </table>

      {!frozen && (
        <details className="card">
          <summary><strong>Add a requirement the agent missed</strong></summary>
          <form className="form" action={(f) => act(post(`/api/opportunities/${id}/requirements`, {
            quote: f.get("quote"), text: f.get("text"), category: f.get("category"), page: Number(f.get("page")) || null }))}>
            <label className="grow">Quote, copied from the RFP <textarea name="quote" rows={2} required /></label>
            <label>Short text <input name="text" /></label>
            <label>Category <select name="category">{CATEGORIES.map((c) => <option key={c}>{c}</option>)}</select></label>
            <label>Page (optional) <input name="page" type="number" min={1} className="narrow" /></label>
            <button>Add</button>
          </form>
        </details>
      )}
    </>
  );
}
