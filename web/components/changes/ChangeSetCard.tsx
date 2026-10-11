"use client";
// One change set (P-11): counts, the drastic-change warning, each change statement with the agent's proposal and the
// person's decision, the change document with highlights, then apply or discard; after apply, what it did.  Owner: Piyush.
import Link from "next/link";
import { useRef, useState } from "react";
import { currentActor, errorMessage, post } from "@/lib/api";
import type { ChangeItem, ChangeKind, ChangeSet } from "@/lib/types";
import { Alert, Busy, StatusBadge, useConfirm, useToast } from "@/components/ui";
import ChangeDecision, { KINDS, KindBadge } from "@/components/changes/ChangeDecision";
import ChangeDocument from "@/components/changes/ChangeDocument";

const BID_MANAGER = "Bid Manager"; // only the bid manager applies or discards; the API checks too
const STATUS_LABEL = { review: "in review", applied: "applied", discarded: "discarded" } as const;
const when = (t: string) => new Date(t.endsWith("Z") || t.includes("+") ? t : `${t}Z`).toLocaleString();
const pct = (x: number) => `${x > 0 && x < 0.1 ? (x * 100).toFixed(1) : Math.round(x * 100)}%`; // 0.009 -> 0.9%, not 1%
const kindOf = (i: ChangeItem) => i.kind ?? i.proposed_kind; // the person's decision, else the proposal
const WORDING = new Set<ChangeKind>(["added", "modified"]); // the kinds that carry a new wording

export default function ChangeSetCard({ set, oppId, threshold, onChanged }:
  { set: ChangeSet; oppId: string; threshold: number; onChanged: () => void }) {
  const [filter, setFilter] = useState<ChangeKind>();
  const [selected, setSelected] = useState<number>();
  const [pageNo, setPageNo] = useState(set.items.find((i) => i.page)?.page ?? 1);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState<string>();
  const [ask, confirmDialog] = useConfirm();
  const toast = useToast();
  const docRef = useRef<HTMLDetailsElement>(null);
  const review = set.status === "review";
  const applied = set.status === "applied";
  const bidManager = currentActor() === BID_MANAGER;
  const items = set.items.filter((i) => !filter || kindOf(i) === filter);
  const r = set.result;

  const trace = (reqId: string) => <Link key={reqId} className="mono" href={`/opportunities/${oppId}/trace#${reqId}`} title="Open in Traceability">{reqId}</Link>;
  // A removed requirement is no longer on the Traceability page: its ID only, its history is on the Requirements page.
  const gone = (reqId: string) => <span key={reqId} className="mono" title={`Removed in baseline ${set.baseline_to}: see its history on the Requirements page`}>{reqId}</span>;
  const ids = (list: string[], link = trace) => list.length ? list.map((x, i) => <span key={x}>{i > 0 && ", "}{link(x)}</span>) : <span className="muted">none</span>;
  const run = (action: string, label: string, done: string) => {
    setBusy(label); setError(undefined);
    post(`/api/changes/${set.id}/${action}`).then(() => { toast.success(done); onChanged(); }, (e) => setError(errorMessage(e))).finally(() => setBusy(""));
  };
  const discard = async () => {
    if (await ask({ title: "Discard this change set?", message: `The changes read from ${set.filename} are dropped; the baseline stays as it is.`, confirmLabel: "Discard", danger: true }))
      run("discard", "Discarding…", "Change set discarded; the baseline is unchanged.");
  };
  // A row selects its page in the change document; its source opens the document; a highlight scrolls to its row.
  const select = (item: ChangeItem, show = false) => {
    setSelected(item.id);
    if (item.page) setPageNo(item.page);
    if (show && docRef.current) { docRef.current.open = true; docRef.current.scrollIntoView({ block: "nearest", behavior: "smooth" }); }
  };
  const fromPage = (item: ChangeItem) => {
    setSelected(item.id);
    if (filter && kindOf(item) !== filter) setFilter(undefined); // its row is filtered out: show every row again
    requestAnimationFrame(() => document.querySelector(`tr[data-change="${item.id}"]`)?.scrollIntoView({ block: "nearest", behavior: "smooth" }));
  };

  return (
    <section className="card chg-set" aria-labelledby={`change-set-${set.id}`}>
      <div className="card-head">
        <h3 id={`change-set-${set.id}`}>{set.filename} <StatusBadge status={set.status} label={STATUS_LABEL[set.status]} /></h3>
        <span className="muted">{set.confirmed} / {set.total} confirmed</span>
      </div>
      <p className="muted">Read by {set.created_by} on {when(set.created_at)}, against baseline {set.baseline_from}.
        {applied && set.applied_at && <> Applied by {set.applied_by} on {when(set.applied_at)}: baseline {set.baseline_to}.</>}
        {set.status === "discarded" && <> Discarded{set.applied_by && ` by ${set.applied_by}`}{set.applied_at && ` on ${when(set.applied_at)}`}: nothing was applied.</>}</p>

      {set.drastic ? (
        <Alert kind="error" title="Drastic change"><strong>{pct(set.share)} of the baseline is modified or removed</strong> (threshold {pct(threshold)}, placeholder):
          consider a new opportunity linked to this one. A person decides.</Alert>
      ) : <p className="muted">{pct(set.share)} of the baseline is modified or removed (drastic above {pct(threshold)}, placeholder).</p>}

      {r && (
        <Alert kind="success" title={`Baseline ${r.baseline} frozen with the changes.`}>
          <ul>
            <li>Added: {ids(r.added)}</li>
            <li>Modified (new version): {ids(r.modified)}</li>
            <li>Removed: {ids(r.removed, gone)}</li>
            <li>{r.returned} unit answer(s) returned for review; {r.dispatched} new assignment(s) sent to the units.</li>
          </ul>
          {r.note && <p className="muted">{r.note}</p>}
        </Alert>)}

      <div className="filters" role="group" aria-label={`Filter the change statements of ${set.filename}`}>
        <button type="button" className="chip" aria-pressed={!filter} onClick={() => setFilter(undefined)}>All <span>{set.total}</span></button>
        {(Object.keys(KINDS) as ChangeKind[]).map((k) => (
          <button key={k} type="button" className="chip" aria-pressed={filter === k}
            onClick={() => setFilter(filter === k ? undefined : k)}>{KINDS[k]} <span>{set.counts[k] ?? 0}</span></button>))}
      </div>

      {set.pages.length > 0 && (
        <details ref={docRef} className="chg-doc">
          <summary>Change document ({set.pages.length} page{set.pages.length === 1 ? "" : "s"})</summary>
          <ChangeDocument set={set} pageNo={pageNo} onPage={setPageNo} selected={selected} onSelect={fromPage} />
        </details>)}

      <div className="chg-scroll">
      <table className="chg-items">
        <thead><tr>
          <th className="col-n">#</th><th className="col-src">Source</th><th>Quote</th><th className="col-kind">Proposed</th>
          <th>Target in the baseline</th><th>New wording</th><th>Rationale</th><th className="col-decide">Decision</th>
        </tr></thead>
        <tbody>
          {items.map((i) => {
            const target = i.status === "confirmed" ? i.target : i.proposed_target;
            const kind = kindOf(i);
            // After apply the API sends the target's latest version: for a modified one that is the new wording, not
            // the baseline it was compared with, so it is not shown as such; a removed one has left Traceability.
            const revised = applied && kind === "modified";
            return (
              // The row itself is focusable so the keyboard can select a change (Enter); its own controls keep their keys.
              <tr key={i.id} data-change={i.id} className={i.id === selected ? "selected" : ""} tabIndex={0}
                onClick={() => select(i)} onKeyDown={(e) => { if (e.key === "Enter" && e.target === e.currentTarget) select(i, true); }}>
                <td className="mono">{i.n}</td>
                <td>{i.page ? <button type="button" className="link" title="Show on the change document"
                  onClick={(e) => { e.stopPropagation(); select(i, true); }}>{i.source}</button> : <span className="muted">{i.source}</span>}</td>
                <td><div className="quote">“{i.quote}”</div></td>
                <td><KindBadge kind={i.proposed_kind} />
                  <div className="muted">{pct(i.confidence)} confidence</div></td>
                <td>{target ? (<>{applied && kind === "removed" ? gone(target) : trace(target)}
                  {revised ? <div className="muted">Revised in baseline {set.baseline_to}; the earlier wording is in its history (Requirements page).</div> : (<>
                    {i.target_text && <div>{i.target_text}</div>}
                    {i.target_source && <div className="muted">{i.target_source}</div>}</>)}</>)
                  : <span className="muted">{kind === "added" ? "new requirement" : "—"}</span>}</td>
                <td>{WORDING.has(kind) ? <>{i.text}<div><span className="tag">{i.category}</span></div></> : <span className="muted">—</span>}</td>
                <td className="muted">{i.rationale}</td>
                <td><ChangeDecision setId={set.id} item={i} editable={review} onDone={onChanged} /></td>
              </tr>
            );
          })}
          {items.length === 0 && <tr><td colSpan={8} className="muted">{filter ? `No change statement classified as ${KINDS[filter].toLowerCase()}.` : "No change statements found in this document."}</td></tr>}
        </tbody>
      </table>
      </div>

      {review && (
        <div className="chg-actions" aria-busy={!!busy}>
          <button type="button" className="secondary" disabled={!!busy || set.confirmed === set.total} onClick={() => run("confirm-all", "Confirming…", "Every proposal confirmed.")}>Confirm all proposals</button>
          <button type="button" disabled={!!busy || !bidManager || set.confirmed < set.total}
            onClick={() => run("apply", "Applying: new versions, matching and dispatch…", "Changes applied: a new baseline is frozen and the affected answers are back with the units.")}>Apply to requirements</button>
          <button type="button" className="danger secondary" disabled={!!busy || !bidManager} onClick={discard}>Discard</button>
          {busy && <Busy label={busy} />}
          <span className="muted">{set.confirmed < set.total ? `${set.total - set.confirmed} change(s) still need a person's confirmation. ` : ""}
            Only the Bid Manager applies or discards{bidManager ? "" : "; switch with Acting as"}. Applying creates the new versions, freezes a new baseline and returns the affected answers to the units.</span>
          <Alert kind="error" className="chg-error" onClose={() => setError(undefined)}>{error}</Alert>
        </div>)}
      {confirmDialog}
    </section>
  );
}
