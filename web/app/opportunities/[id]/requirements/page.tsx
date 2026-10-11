"use client";
// Requirement review: approve, reject, edit, split, merge, ungroup, add missed (select lines or paste a quote); then
// freeze the baseline.  Owner: Piyush.
// Requirements are shown in document order; a group lists its sub-requirements when expanded.
import Link from "next/link";
import { useParams } from "next/navigation";
import { Fragment, useMemo, useState } from "react";
import PageHead from "@/components/shell/PageHead";
import LinePicker from "@/components/requirements/LinePicker"; // P-15
import { Alert, Busy, EmptyState, Skeleton, StatusBadge, useConfirm, useToast } from "@/components/ui";
import { errorMessage, post, useApi } from "@/lib/api";
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
const MAX_TEXT = 200; // as the API (add and split cap the short text at 200)
type FilterKey = keyof typeof FILTERS;

export default function RequirementsPage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, reload } = useApi<{ requirements: Requirement[]; baseline: Baseline | null }>(`/api/opportunities/${id}/requirements`);
  const toast = useToast();
  const [ask, confirmDialog] = useConfirm();
  const [chosen, setFilter] = useState<FilterKey>();
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [editing, setEditing] = useState<{ id: string; mode: "edit" | "split" }>();
  const [merging, setMerging] = useState(false); // the merge text field is open in the bulk bar
  const [formError, setFormError] = useState<{ at: string; text: string }>(); // shown inside the form it came from
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
  if (error) return <Alert kind="error" title="Requirements could not be loaded.">{error}</Alert>;
  if (!data) return <Skeleton lines={6} />;

  const frozen = !!data.baseline;
  const undecided = all.filter(FILTERS.review.test).length;
  const activeCount = all.filter((r) => !INACTIVE.has(r.status)).length;
  const done = (msg?: string) => { setSelected(new Set()); setEditing(undefined); setMerging(false); if (msg) toast.success(msg); return reload(); };
  // One action at a time. A failure inside a form stays in that form (at = its key) with the API's message; elsewhere it is a toast.
  const act = (p: Promise<unknown>, msg?: string, at?: string) => {
    setBusy(true); setFormError(undefined);
    return p.then(() => done(msg), (e) => { const text = errorMessage(e); if (at) setFormError({ at, text }); else toast.error(text); })
      .finally(() => setBusy(false));
  };
  const review = (reqId: string, body: object, msg?: string, at?: string) => act(post(`/api/requirements/${reqId}/review`, body), msg, at);
  const bulk = (action: string) => {
    const n = selected.size;
    return act(Promise.all([...selected].map((r) => post(`/api/requirements/${r}/review`, { action }))), `${n} line items ${action === "approve" ? "approved" : "rejected"}.`);
  };
  const merge = (text: string) => act(post(`/api/opportunities/${id}/requirements/merge`, { req_ids: [...selected], text }), `${selected.size} line items merged into one.`, "merge");
  // QA-10: check the part count here so the message is ours, not the validator's
  const split = (r: Requirement, raw: string) => {
    const parts = raw.split("\n").map((q) => ({ quote: q.trim() })).filter((p) => p.quote);
    if (parts.length < 2) { setFormError({ at: r.req_id, text: "A split needs at least two parts: one quote per line." }); return; }
    return act(post(`/api/requirements/${r.req_id}/split`, { parts }), `${r.req_id} split into ${parts.length} line items.`, r.req_id);
  };
  const freeze = async () => {
    const ok = await ask({ title: "Freeze the baseline?", confirmLabel: "Freeze baseline",
      message: `The ${activeCount} approved requirements become the baseline the units work from. Later changes to the RFP run as a delta against it.` });
    if (!ok) return;
    await act(post(`/api/opportunities/${id}/baselines`), "Baseline frozen.");
    window.dispatchEvent(new Event("opp-status-changed")); // the stepper and status badge update at once
  };
  const flip = (set: Set<string>, reqId: string) => { const n = new Set(set); if (n.has(reqId)) n.delete(reqId); else n.add(reqId); return n; };
  const toggle = (reqId: string) => setSelected((s) => flip(s, reqId));
  const openForm = (next?: { id: string; mode: "edit" | "split" }) => { setFormError(undefined); setEditing(next); };
  const errorAt = (at: string) => formError?.at === at && <p className="warn form-error" role="alert">{formError.text}</p>;
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
          {/* UX-14: an unanchored item says so once, as a badge, instead of a source line plus a warning */}
          <td>{r.provenance === "UNANCHORED"
            ? <StatusBadge status="medium" kind="severity" label="unanchored" title="Quote not located on the page; check the source manually" />
            : r.page ? <Link href={`/opportunities/${id}/trace#${r.parent_id ?? r.req_id}`}>{r.source}</Link> : r.source}</td>
          <td>
            {isEditing && editing.mode === "edit" ? (
              <form className="form compact" aria-label={`Edit ${r.req_id}`}
                action={(f) => review(r.req_id, { action: "edit", text: f.get("text"), category: f.get("category") }, `${r.req_id} saved.`, r.req_id)}>
                <input name="text" defaultValue={r.text} aria-label="Requirement text" required maxLength={MAX_TEXT} autoFocus />
                <select name="category" defaultValue={r.category} aria-label="Category">{CATEGORIES.map((c) => <option key={c}>{c}</option>)}</select>
                {errorAt(r.req_id)}
                <span className="inline"><button disabled={busy}>{busy ? "Saving…" : "Save"}</button><button type="button" className="secondary" onClick={() => openForm()}>Cancel</button></span>
              </form>
            ) : isEditing && editing.mode === "split" ? (
              <form className="form compact" aria-label={`Split ${r.req_id}`} action={(f) => split(r, String(f.get("parts")))}>
                <label>Put each part of the quote on its own line
                  <textarea name="parts" rows={4} defaultValue={r.quote} autoFocus /></label>
                {errorAt(r.req_id)}
                <span className="inline"><button disabled={busy}>{busy ? "Splitting…" : "Split"}</button><button type="button" className="secondary" onClick={() => openForm()}>Cancel</button></span>
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
          <td className="status-cell"><StatusBadge status={r.status} />
            <button type="button" className="link" aria-expanded={historyOf === r.req_id}
              onClick={() => setHistoryOf(historyOf === r.req_id ? undefined : r.req_id)}>History</button></td>
          {!frozen && <td>{(active || r.status === "duplicate") && !isEditing && (
            <div className="row-actions">
              {r.status !== "approved" && <button disabled={busy} onClick={() => review(r.req_id, { action: "approve" })}>Approve</button>}
              {active && r.status !== "rejected" && <button className="secondary" disabled={busy} onClick={() => review(r.req_id, { action: "reject" })}>Reject</button>}
              {active && <button className="secondary" disabled={busy} onClick={() => openForm({ id: r.req_id, mode: "edit" })}>Edit</button>}
              {active && !group && !child && <button className="secondary" disabled={busy} onClick={() => openForm({ id: r.req_id, mode: "split" })}>Split</button>}
              {active && group && <button className="secondary" disabled={busy}
                onClick={() => act(post(`/api/requirements/${r.req_id}/ungroup`), `${r.req_id} ungrouped: its ${kids.length} sub-requirements stand on their own.`)}>Ungroup</button>}
            </div>)}</td>}
        </tr>
        {historyOf === r.req_id && <tr className="history-row"><td colSpan={cols}><History reqId={r.req_id} /></td></tr>}
        {group && open.has(r.req_id) && kids.map((k) => line(k, true))}
      </Fragment>
    );
  };

  return (
    <>
      {confirmDialog}
      <PageHead level={2} title="Requirements"
        help={frozen ? <>Baseline {data.baseline!.number} frozen by {data.baseline!.frozen_by} ({data.baseline!.count} items).
            Later changes run as a delta on the <Link href={`/opportunities/${id}/changes`}>Changes</Link> step.</>
          : `${activeCount} requirements; related line items are grouped (expand a group to see its sub-requirements). Check each against its source, then freeze the baseline.`}>
        {busy && <Busy label="Saving…" />}
        {!frozen && undecided > 0 && <span className="muted nowrap">{undecided} still to decide</span>}
        {!frozen && <button disabled={busy || undecided > 0} title={undecided ? `${undecided} line items still need a decision` : ""} onClick={freeze}>Freeze baseline</button>}
      </PageHead>

      {all.length === 0 ? (
        <EmptyState title="No requirements yet" hint="The reader proposes line items here once the main RFP has been read.">
          <Link className="button secondary" href={`/opportunities/${id}`}>Go to the RFP step</Link>
        </EmptyState>
      ) : (<>
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
            <button disabled={busy} onClick={() => bulk("approve")}>Approve</button>
            <button className="secondary" disabled={busy} onClick={() => bulk("reject")}>Reject</button>
            <button className="secondary" disabled={busy || selected.size < 2 || merging} onClick={() => { setFormError(undefined); setMerging(true); }}>Merge into one</button>
            <button className="secondary" disabled={busy} onClick={() => { setSelected(new Set()); setMerging(false); }}>Clear</button>
            {merging && selected.size >= 2 && (
              <form className="form bulk-merge" aria-label="Merge the selected line items" action={(f) => merge(String(f.get("text")))}>
                <label className="grow">One-line text for the merged requirement ({selected.size} items)
                  <input name="text" required maxLength={MAX_TEXT} autoFocus /></label>
                <span className="inline"><button disabled={busy}>{busy ? "Merging…" : "Merge"}</button>
                  <button type="button" className="secondary" onClick={() => { setMerging(false); setFormError(undefined); }}>Cancel</button></span>
                {errorAt("merge")}
              </form>
            )}
          </div>
        )}

        <table className="req-table">
          <thead><tr>
            {!frozen && <th className="col-check"><span className="sr-only">Select</span></th>}
            <th className="col-id">ID</th><th className="col-src">Source</th><th>Requirement</th><th className="col-status">Status</th>{!frozen && <th className="col-actions">Actions</th>}
          </tr></thead>
          <tbody>
            {rows.map((r) => line(r))}
            {rows.length === 0 && <tr><td colSpan={cols} className="muted">
              {query ? <>Nothing in “{FILTERS[filter].label}” matches “{query}”.</> : filter === "review" ? "Nothing left to review." : `No line items under “${FILTERS[filter].label}”.`}
            </td></tr>}
          </tbody>
        </table>
      </>)}

      {!frozen && (
        <details className="card" onToggle={(e) => setAdding(e.currentTarget.open)}>
          <summary><strong>Add a requirement the agent missed</strong> <span className="muted">select its lines on the RFP page, or paste the quote</span></summary>
          <h3 className="lp-heading">Select its lines on the RFP page</h3>
          {adding && <LinePicker oppId={id} startPage={startPage} categories={CATEGORIES} onAdded={reload}
            requirements={(data.requirements ?? []).filter((r) => !INACTIVE.has(r.status))} />}
          <h3 className="lp-heading">Or paste the quote</h3>
          <form className="form" aria-label="Add a requirement from a pasted quote" action={(f) => act(post(`/api/opportunities/${id}/requirements`, {
            quote: f.get("quote"), text: f.get("text"), category: f.get("category"), page: Number(f.get("page")) || null }),
            "Requirement added; it is in the list, to review like the others.", "add")}>
            <label className="grow">Quote, copied from the RFP <textarea name="quote" rows={2} required /></label>
            <label>Short text <span className="field-hint">(optional; default: the quote)</span> <input name="text" maxLength={MAX_TEXT} /></label>
            <label>Category <select name="category">{CATEGORIES.map((c) => <option key={c}>{c}</option>)}</select></label>
            <label>Page <span className="field-hint">(optional)</span> <input name="page" type="number" min={1} className="narrow" /></label>
            <button disabled={busy}>{busy ? "Adding…" : "Add"}</button>
          </form>
          {errorAt("add")}
        </details>
      )}
    </>
  );
}

/** Every version of a line item (who, when, what changed) and everything that happened to it, from the audit log. */
function History({ reqId }: { reqId: string }) {
  const { data, error } = useApi<RequirementHistory>(`/api/requirements/${reqId}/history`);
  if (error) return <Alert kind="error">{error}</Alert>;
  if (!data) return <Skeleton lines={3} />;
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
