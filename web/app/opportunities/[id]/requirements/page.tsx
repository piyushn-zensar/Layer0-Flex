"use client";
// Requirement register and exception queue: exclude (with a reason), restore, edit, split, merge, ungroup, add missed (select lines or paste a quote); exceptions
// (source not verified) are linked to lines or dismissed; then freeze the baseline.  Owner: Piyush.
// Requirements are shown in document order; a group lists its sub-requirements when expanded.
import Link from "next/link";
import { useParams } from "next/navigation";
import { Fragment, useMemo, useState } from "react";
import PageHead from "@/components/shell/PageHead";
import LinePicker from "@/components/requirements/LinePicker"; // P-15
import { Alert, Busy, EmptyState, Skeleton, StatusBadge, useConfirm, useToast } from "@/components/ui";
import { errorMessage, post, useApi } from "@/lib/api";
import { sourceLabel, statusLabel, type Baseline, type Requirement, type RequirementException, type RequirementHistory } from "@/lib/types";

const CATEGORIES = ["technical", "compliance", "commercial", "schedule", "submission", "legal", "staffing"];
const FILTERS = {
  register: { label: "In register", test: (r: Requirement) => !INACTIVE.has(r.status) },
  rejected: { label: "Excluded", test: (r: Requirement) => r.status === "rejected" },
  duplicates: { label: "Duplicates", test: (r: Requirement) => r.status === "duplicate" },
  replaced: { label: "Ungrouped / split / merged", test: (r: Requirement) => r.status === "split" || r.status === "merged" },
  all: { label: "All", test: () => true },
} as const;
const INACTIVE = new Set(["rejected", "split", "merged", "duplicate", "removed", "exception", "dismissed"]); // removed: by a change document (P-11)
const OUTSIDE = new Set(["exception", "dismissed"]); // outside the register: shown on the Exceptions tab only
const MAX_TEXT = 200; // as the API (add and split cap the short text at 200)
type FilterKey = keyof typeof FILTERS;

export default function RequirementsPage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, reload } = useApi<{ requirements: Requirement[]; baseline: Baseline | null; exceptions: number }>(`/api/opportunities/${id}/requirements`);
  const { data: exc, error: excError, reload: reloadExc } = useApi<RequirementException[]>(`/api/opportunities/${id}/requirements/exceptions`);
  const [tab, setTab] = useState<"register" | "exceptions">("register");
  const toast = useToast();
  const [ask, confirmDialog] = useConfirm();
  const [chosen, setFilter] = useState<FilterKey>();
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [editing, setEditing] = useState<{ id: string; mode: "edit" | "split" | "exclude" }>();
  const [merging, setMerging] = useState(false); // the merge text field is open in the bulk bar
  const [formError, setFormError] = useState<{ at: string; text: string }>(); // shown inside the form it came from
  const [historyOf, setHistoryOf] = useState<string>();
  const [open, setOpen] = useState<Set<string>>(new Set());
  const [adding, setAdding] = useState(false); // the "add missed" section is open: its page viewer loads only then

  const filter: FilterKey = chosen ?? "register";
  const all = useMemo(() => (data?.requirements ?? []).filter((r) => !r.parent_id && !OUTSIDE.has(r.status)), [data]); // requirements, not sub-requirements
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
  const activeCount = all.filter(FILTERS.register.test).length;
  const done = (msg?: string) => { setSelected(new Set()); setEditing(undefined); setMerging(false); if (msg) toast.success(msg); return Promise.all([reload(), reloadExc()]).then(() => undefined); };
  // One action at a time. A failure inside a form stays in that form (at = its key) with the API's message; elsewhere it is a toast.
  const act = (p: Promise<unknown>, msg?: string, at?: string) => {
    setBusy(true); setFormError(undefined);
    return p.then(() => done(msg), (e) => { const text = errorMessage(e); if (at) setFormError({ at, text }); else toast.error(text); })
      .finally(() => setBusy(false));
  };
  const review = (reqId: string, body: object, msg?: string, at?: string) => act(post(`/api/requirements/${reqId}/review`, body), msg, at);
  const merge = (text: string) => act(post(`/api/opportunities/${id}/requirements/merge`, { req_ids: [...selected], text }), `${selected.size} line items merged into one.`, "merge");
  // QA-10: check the part count here so the message is ours, not the validator's
  const split = (r: Requirement, raw: string) => {
    const parts = raw.split("\n").map((q) => ({ quote: q.trim() })).filter((p) => p.quote);
    if (parts.length < 2) { setFormError({ at: r.req_id, text: "A split needs at least two parts: one quote per line." }); return; }
    return act(post(`/api/requirements/${r.req_id}/split`, { parts }), `${r.req_id} split into ${parts.length} line items.`, r.req_id);
  };
  const freeze = async () => {
    const ok = await ask({ title: "Freeze the baseline?", confirmLabel: "Freeze baseline",
      message: `The ${activeCount} requirements in the register become the baseline the units work from. Later changes to the RFP run as a delta against it.` });
    if (!ok) return;
    await act(post(`/api/opportunities/${id}/baselines`), "Baseline frozen.");
    window.dispatchEvent(new Event("opp-status-changed")); // the stepper and status badge update at once
  };
  const flip = (set: Set<string>, reqId: string) => { const n = new Set(set); if (n.has(reqId)) n.delete(reqId); else n.add(reqId); return n; };
  const toggle = (reqId: string) => setSelected((s) => flip(s, reqId));
  const openForm = (next?: { id: string; mode: "edit" | "split" | "exclude" }) => { setFormError(undefined); setEditing(next); };
  const errorAt = (at: string) => formError?.at === at && <p className="warn form-error" role="alert">{formError.text}</p>;
  const cols = frozen ? 4 : 6;
  const exceptions = data.exceptions ?? exc?.length ?? 0;
  // P-15: the line picker opens on the page of a selected requirement, else of the first one in view
  const startPage = (all.find((r) => selected.has(r.req_id) && r.page) ?? rows.find((r) => r.page))?.page ?? 1;
  // Select every selectable row in the current view (the filter and search) at once; the bulk bar then acts on them.
  const selectable = rows.filter((r) => !INACTIVE.has(r.status) && r.baseline === null).map((r) => r.req_id);
  const allSelected = selectable.length > 0 && selectable.every((rid) => selected.has(rid));
  // Walkthrough targets (data-tour): the first row in view carries the row-level ids, and the first row of each kind
  // (group, unanchored, duplicate, sub-requirement, splittable item) carries its own, so a step can spotlight one.
  const marked = new Set<string>();
  const first = (tourId: string) => (marked.has(tourId) ? undefined : (marked.add(tourId), tourId));

  const line = (r: Requirement, child = false) => {
    const active = !INACTIVE.has(r.status) && r.baseline === null;
    const isEditing = editing?.id === r.req_id;
    const kids = kidsOf.get(r.req_id) ?? [];
    const group = r.kind === "group";
    const lead = !child && first("req-row-first") !== undefined; // the first row in view
    const at = (tourId: string) => (lead ? tourId : undefined);
    return (
      <Fragment key={r.req_id}>
        <tr data-tour={lead ? "req-row-first" : child ? first("req-row-child") : undefined}
          className={`${INACTIVE.has(r.status) ? "inactive" : ""} ${child ? "child" : ""} ${group ? "group" : ""}`}>
          {!frozen && <td>{active && !child && <input type="checkbox" data-tour={at("req-row-check")} aria-label={`Select ${r.req_id}`} checked={selected.has(r.req_id)} onChange={() => toggle(r.req_id)} />}</td>}
          <td><div className="mono" data-tour={at("req-row-id")}>{r.req_id}</div><span className="tag" data-tour={at("req-row-category")}>{r.category}</span></td>
          {/* UX-14: an unanchored item (shown as "source not verified") says so once, as a badge, instead of a source line plus a warning */}
          <td data-tour={at("req-row-source")}>{r.provenance === "UNANCHORED"
            ? <span data-tour={first("req-badge-unanchored")}><StatusBadge status="medium" kind="severity" label={sourceLabel(r.provenance).toLowerCase()} title="Quote not located on the page; check the source manually" /></span>
            : r.page ? <Link href={`/opportunities/${id}/trace#${r.parent_id ?? r.req_id}`}>{r.source}</Link> : r.source}</td>
          <td>
            {isEditing && editing.mode === "edit" ? (
              <form className="form compact" data-tour="req-edit-form" aria-label={`Edit ${r.req_id}`}
                action={(f) => review(r.req_id, { action: "edit", text: f.get("text"), category: f.get("category") }, `${r.req_id} saved.`, r.req_id)}>
                <input name="text" data-tour="req-edit-text" defaultValue={r.text} aria-label="Requirement text" required maxLength={MAX_TEXT} autoFocus />
                <select name="category" data-tour="req-edit-category" defaultValue={r.category} aria-label="Category">{CATEGORIES.map((c) => <option key={c}>{c}</option>)}</select>
                {errorAt(r.req_id)}
                <span className="inline"><button data-tour="req-edit-save" disabled={busy}>{busy ? "Saving…" : "Save"}</button><button type="button" className="secondary" onClick={() => openForm()}>Cancel</button></span>
              </form>
            ) : isEditing && editing.mode === "split" ? (
              <form className="form compact" data-tour="req-split-form" aria-label={`Split ${r.req_id}`} action={(f) => split(r, String(f.get("parts")))}>
                <label>Put each part of the quote on its own line
                  <textarea name="parts" data-tour="req-split-parts" rows={4} defaultValue={r.quote} autoFocus /></label>
                {errorAt(r.req_id)}
                <span className="inline"><button disabled={busy}>{busy ? "Splitting…" : "Split"}</button><button type="button" className="secondary" onClick={() => openForm()}>Cancel</button></span>
              </form>
            ) : isEditing && editing.mode === "exclude" ? (
              <ReasonForm label={`Why is ${r.req_id} not a requirement?`} submit="Exclude" busy={busy} error={errorAt(r.req_id)} tour="req-exclude-form"
                onSubmit={(reason) => review(r.req_id, { action: "reject", reason }, `${r.req_id} excluded.`, r.req_id)} onCancel={() => openForm()} />
            ) : (<>
              <div className={group ? "group-title" : ""} data-tour={at("req-row-text")}>{r.text}</div>
              {group ? (
                <button type="button" className="link expand" data-tour={first("req-group-expand")} aria-expanded={open.has(r.req_id)} onClick={() => setOpen((s) => flip(s, r.req_id))}>
                  {open.has(r.req_id) ? "▾" : "▸"} {kids.length} sub-requirements</button>
              ) : <div className="quote" data-tour={at("req-row-quote")}>“{r.quote}”</div>}
              {r.status === "duplicate" ? <div className="muted" data-tour={first("req-row-duplicate")}>Duplicate of {r.derived_from.join(", ")}: restore it to keep it anyway</div>
                : r.derived_from?.length > 0 && <div className="muted" data-tour={first("req-row-derived")}>From {r.derived_from.join(", ")}</div>}
            </>)}
          </td>
          <td className="status-cell" data-tour={at("req-row-status")}><StatusBadge status={r.status} label={statusLabel(r.status)} />
            <button type="button" className="link" data-tour={at("req-action-history")} aria-expanded={historyOf === r.req_id}
              onClick={() => setHistoryOf(historyOf === r.req_id ? undefined : r.req_id)}>History</button></td>
          {/* an excluded item or a duplicate keeps Restore: it goes back in the register (service contract) */}
          {!frozen && <td>{(active || r.status === "duplicate" || r.status === "rejected") && !isEditing && (
            <div className="row-actions" data-tour={at("req-row-actions")}>
              {(r.status === "duplicate" || r.status === "rejected") && <button data-tour={at("req-action-restore")} disabled={busy} onClick={() => review(r.req_id, { action: "approve" }, `${r.req_id} restored to the register.`)}>Restore</button>}
              {active && <button className="secondary" data-tour={at("req-action-exclude")} disabled={busy} onClick={() => openForm({ id: r.req_id, mode: "exclude" })}>Exclude: not a requirement</button>}
              {active && <button className="secondary" data-tour={at("req-action-edit")} disabled={busy} onClick={() => openForm({ id: r.req_id, mode: "edit" })}>Edit</button>}
              {active && !group && !child && <button className="secondary" data-tour={first("req-action-split")} disabled={busy} onClick={() => openForm({ id: r.req_id, mode: "split" })}>Split</button>}
              {active && group && <button className="secondary" data-tour={first("req-action-ungroup")} disabled={busy}
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
        help={frozen ? <span data-tour="req-baseline">Baseline {data.baseline!.number} frozen by {data.baseline!.frozen_by} ({data.baseline!.count} items).
            Later changes run as a delta on the <Link href={`/opportunities/${id}/changes`}>Changes</Link> step.</span>
          : <span data-tour="req-help">{activeCount} requirements in the register; related line items are grouped (expand a group to see its sub-requirements). Each was verified against its source; exclude anything that is not a requirement, then freeze the baseline.</span>}>
        {busy && <Busy label="Saving…" />}
        {!frozen && <button data-tour="req-freeze" disabled={busy || activeCount === 0} onClick={freeze}>Freeze baseline</button>}
      </PageHead>

      <div className="filters" role="tablist" aria-label="Requirements view" data-tour="req-tabs">
        <button role="tab" data-tour="req-tab-register" aria-selected={tab === "register"} className={`chip ${tab === "register" ? "on" : ""}`} onClick={() => setTab("register")}>Register <span>{activeCount}</span></button>
        <button role="tab" data-tour="req-tab-exceptions" aria-selected={tab === "exceptions"} className={`chip ${tab === "exceptions" ? "on" : ""}`} onClick={() => setTab("exceptions")}>Exceptions <span>{exceptions}</span></button>
      </div>

      {tab === "exceptions" ? (
        <Exceptions bidId={id} rows={exc} error={excError} frozen={frozen} busy={busy} act={act} done={done} requirements={data.requirements} />
      ) : all.length === 0 ? (
        <EmptyState title="No requirements yet" hint="The reader proposes line items here once the main RFP has been read.">
          <Link className="button secondary" href={`/opportunities/${id}`}>Go to the RFP step</Link>
        </EmptyState>
      ) : (<>
        <div className="filters" role="tablist" aria-label="Filter line items" data-tour="req-filters">
          {(Object.keys(FILTERS) as FilterKey[]).map((k) => (
            <button key={k} role="tab" data-tour={`req-filter-${k}`} aria-selected={filter === k} className={`chip ${filter === k ? "on" : ""}`} onClick={() => setFilter(k)}>
              {FILTERS[k].label} <span>{all.filter(FILTERS[k].test).length}</span>
            </button>
          ))}
          <input type="search" data-tour="req-search" placeholder="Search ID or text" value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Search line items" />
        </div>

        {!frozen && selected.size > 0 && (
          <div className="bulkbar" role="region" aria-label="Selected line items" data-tour="req-bulkbar">
            <strong>{selected.size} selected</strong>
            <button className="secondary" data-tour="req-bulk-merge" disabled={busy || selected.size < 2 || merging} onClick={() => { setFormError(undefined); setMerging(true); }}>Merge into one</button>
            <button className="secondary" data-tour="req-bulk-clear" disabled={busy} onClick={() => { setSelected(new Set()); setMerging(false); }}>Clear</button>
            {merging && selected.size >= 2 && (
              <form className="form bulk-merge" data-tour="req-merge-form" aria-label="Merge the selected line items" action={(f) => merge(String(f.get("text")))}>
                <label className="grow">One-line text for the merged requirement ({selected.size} items)
                  <input name="text" data-tour="req-merge-text" required maxLength={MAX_TEXT} autoFocus /></label>
                <span className="inline"><button disabled={busy}>{busy ? "Merging…" : "Merge"}</button>
                  <button type="button" className="secondary" onClick={() => { setMerging(false); setFormError(undefined); }}>Cancel</button></span>
                {errorAt("merge")}
              </form>
            )}
          </div>
        )}

        <table className="req-table" data-tour="req-table">
          <thead><tr>
            {!frozen && <th className="col-check" data-tour="req-col-check">
              <input type="checkbox" data-tour="req-select-all" aria-label="Select all line items in view" disabled={selectable.length === 0}
                checked={allSelected} onChange={() => setSelected(allSelected ? new Set() : new Set(selectable))} /></th>}
            <th className="col-id" data-tour="req-col-id">ID</th><th className="col-src" data-tour="req-col-source">Source</th><th data-tour="req-col-text">Requirement</th>
            <th className="col-status" data-tour="req-col-status">Status</th>{!frozen && <th className="col-actions" data-tour="req-col-actions">Actions</th>}
          </tr></thead>
          <tbody>
            {rows.map((r) => line(r))}
            {rows.length === 0 && <tr><td colSpan={cols} className="muted">
              {query ? <>Nothing in “{FILTERS[filter].label}” matches “{query}”.</> : `No line items under “${FILTERS[filter].label}”.`}
            </td></tr>}
          </tbody>
        </table>
      </>)}

      {!frozen && tab === "register" && (
        <details className="card" data-tour="req-add" onToggle={(e) => setAdding(e.currentTarget.open)}>
          <summary data-tour="req-add-summary"><strong>Add a requirement the agent missed</strong> <span className="muted">select its lines on the RFP page, or paste the quote</span></summary>
          <h3 className="lp-heading">Select its lines on the RFP page</h3>
          {adding && <LinePicker oppId={id} startPage={startPage} categories={CATEGORIES} onAdded={reload}
            requirements={(data.requirements ?? []).filter((r) => !INACTIVE.has(r.status))} />}
          <h3 className="lp-heading">Or paste the quote</h3>
          <form className="form" data-tour="req-paste-form" aria-label="Add a requirement from a pasted quote" action={(f) => act(post(`/api/opportunities/${id}/requirements`, {
            quote: f.get("quote"), text: f.get("text"), category: f.get("category"), page: Number(f.get("page")) || null }),
            "Requirement added; it is in the register.", "add")}>
            <label className="grow">Quote, copied from the RFP <textarea name="quote" data-tour="req-paste-quote" rows={2} required /></label>
            <label>Short text <span className="field-hint">(optional; default: the quote)</span> <input name="text" data-tour="req-paste-text" maxLength={MAX_TEXT} /></label>
            <label>Category <select name="category" data-tour="req-paste-category">{CATEGORIES.map((c) => <option key={c}>{c}</option>)}</select></label>
            <label>Page <span className="field-hint">(optional)</span> <input name="page" type="number" data-tour="req-paste-page" min={1} className="narrow" /></label>
            <button data-tour="req-paste-add" disabled={busy}>{busy ? "Adding…" : "Add"}</button>
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
    <div className="history" data-tour="req-history">
      <div data-tour="req-history-versions">
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
      <div data-tour="req-history-timeline">
        <h3>Timeline</h3>
        <ul className="timeline">
          {data.events.map((e, i) => (
            <li key={i}><span className="muted">{when(e.at)}</span> <strong>{e.action.replace("_", " ")}</strong> by {e.by}
              {Object.entries(e.details).filter(([, v]) => v !== "" && !(Array.isArray(v) && v.length === 0)).map(([k, v]) =>
                <span key={k} className="muted"> · {k === "provenance" ? sourceLabel(String(v)).toLowerCase() : <>{k.replace("_", " ")}: {Array.isArray(v) ? v.join(", ") : String(v)}</>}</span>)}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

/** A short required-reason form: used to exclude a requirement and to dismiss an exception. */
function ReasonForm({ label, submit, busy, error, tour, onSubmit, onCancel }: {
  label: string; submit: string; busy: boolean; error: React.ReactNode; tour: string; onSubmit: (reason: string) => unknown; onCancel: () => void;
}) {
  return (
    <form className="form compact" data-tour={tour} aria-label={label} action={(f) => { const reason = String(f.get("reason")).trim(); if (reason) onSubmit(reason); }}>
      <label>{label} <input name="reason" required maxLength={500} autoFocus /></label>
      {error}
      <span className="inline"><button disabled={busy}>{busy ? "Saving…" : submit}</button><button type="button" className="secondary" onClick={onCancel}>Cancel</button></span>
    </form>
  );
}

/** The exception queue: text the reader proposed whose source could not be verified. Link it to lines on the RFP, or dismiss it with a reason. */
function Exceptions({ bidId, rows, error, frozen, busy, act, done, requirements }: {
  bidId: string; rows: RequirementException[] | undefined; error?: string; frozen: boolean; busy: boolean;
  act: (p: Promise<unknown>, msg?: string, at?: string) => unknown; done: (msg?: string) => unknown; requirements: Requirement[];
}) {
  const [mode, setMode] = useState<{ id: string; kind: "link" | "dismiss" }>();
  if (error) return <Alert kind="error" title="Exceptions could not be loaded.">{error}</Alert>;
  if (!rows) return <Skeleton lines={4} />;
  if (rows.length === 0) return <EmptyState title="No exceptions" hint="No exceptions: every proposed requirement has a verified source." />;
  const active = requirements.filter((r) => !INACTIVE.has(r.status));
  return (
    <ul className="exceptions" data-tour="req-exceptions">
      {rows.map((r) => (
        <li key={r.req_id} className="card" data-tour="req-exception-row">
          <div><span className="mono">{r.req_id}</span> <span className="tag">{r.category}</span> <StatusBadge status="medium" kind="severity" label="Source not verified" /></div>
          <div>{r.text}</div>
          <div className="quote">“{r.quote}”</div>
          <div className="muted">{r.suggested_page ? `Suggested page ${r.suggested_page}` : "No page suggested"} · {r.reason}</div>
          {!frozen && mode?.id !== r.req_id && (
            <div className="row-actions">
              <button data-tour="req-exception-link" disabled={busy} onClick={() => setMode({ id: r.req_id, kind: "link" })}>Link to lines</button>
              <button className="secondary" data-tour="req-exception-dismiss" disabled={busy} onClick={() => setMode({ id: r.req_id, kind: "dismiss" })}>Dismiss</button>
            </div>)}
          {mode?.id === r.req_id && mode.kind === "link" && (<>
            <LinePicker oppId={bidId} startPage={r.suggested_page ?? 1} categories={CATEGORIES} requirements={active}
              resolve={{ reqId: r.req_id, text: r.text, category: r.category }} onAdded={() => { setMode(undefined); return done(); }} />
            <button type="button" className="secondary" onClick={() => setMode(undefined)}>Close</button>
          </>)}
          {mode?.id === r.req_id && mode.kind === "dismiss" && (
            <ReasonForm label={`Why is ${r.req_id} dismissed?`} submit="Dismiss" busy={busy} error={null} tour="req-dismiss-form" onCancel={() => setMode(undefined)}
              onSubmit={(reason) => act(post(`/api/requirements/${r.req_id}/dismiss`, { reason }), `${r.req_id} dismissed.`)} />)}
        </li>
      ))}
    </ul>
  );
}
