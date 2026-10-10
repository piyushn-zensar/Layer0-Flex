"use client";
// One change statement's decision (P-11): a person confirms or overrides the agent's classification and baseline target.  Owner: Piyush.
import { useState } from "react";
import { post } from "@/lib/api";
import type { ChangeItem, ChangeKind } from "@/lib/types";

export const KINDS: Record<ChangeKind, string> = {
  added: "Added", modified: "Modified", removed: "Removed", unchanged: "Unchanged", not_a_requirement: "Not a requirement",
};
export const KIND_CLASS: Record<ChangeKind, string> = {
  added: "status-approved", modified: "status-proposed", removed: "sev-high", unchanged: "", not_a_requirement: "status-rejected",
};
export const NEEDS_TARGET = new Set<ChangeKind>(["modified", "removed", "unchanged"]);
const OTHER = "other"; // a baseline requirement the agent did not offer
const short = (s: string) => (s.length > 70 ? `${s.slice(0, 70)}…` : s);

function DecisionForm({ setId, item, onDone, onCancel }: { setId: number; item: ChangeItem; onDone: () => void; onCancel?: () => void }) {
  const first = item.target ?? item.proposed_target ?? item.candidates[0]?.req_id ?? "";
  const [kind, setKind] = useState<ChangeKind>(item.kind ?? item.proposed_kind);
  const [target, setTarget] = useState(first || OTHER);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  // The current target first when the agent's candidates do not include it.
  const options = !first || item.candidates.some((c) => c.req_id === first) ? item.candidates
    : [{ req_id: first, text: item.target_text ?? "", source: item.target_source ?? "" }, ...item.candidates];
  const needsTarget = NEEDS_TARGET.has(kind);
  const wording = kind === "added" || kind === "modified";

  async function confirm(form: FormData) {
    setBusy(true); setError(undefined);
    const chosen = target === OTHER ? String(form.get("other") ?? "").trim() : target;
    const text = String(form.get("text") ?? "").trim();
    try {
      await post(`/api/changes/${setId}/items/${item.id}`,
        { kind, target: needsTarget ? chosen || null : null, text: wording && text && text !== item.text ? text : null });
      onDone();
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); } finally { setBusy(false); }
  }
  // onSubmit, not action: a failed confirm keeps what was typed.
  return (
    <form className="form compact chg-decide" onSubmit={(e) => { e.preventDefault(); confirm(new FormData(e.currentTarget)); }}>
      <label>Change <select value={kind} onChange={(e) => setKind(e.target.value as ChangeKind)}>
        {(Object.keys(KINDS) as ChangeKind[]).map((k) => <option key={k} value={k}>{KINDS[k]}</option>)}</select></label>
      {needsTarget && <label>Baseline requirement <select value={target} onChange={(e) => setTarget(e.target.value)}>
        {options.map((c) => <option key={c.req_id} value={c.req_id}>{c.req_id} — {short(c.text)}</option>)}
        <option value={OTHER}>Another requirement ID…</option></select></label>}
      {needsTarget && target === OTHER && <label>Requirement ID <input name="other" required maxLength={20} placeholder="REQ-…" /></label>}
      {wording && <label>New wording <textarea name="text" rows={2} maxLength={2000} defaultValue={item.text} /></label>}
      <span className="inline">
        <button disabled={busy}>Confirm</button>
        {onCancel && <button type="button" className="secondary" onClick={onCancel}>Cancel</button>}
      </span>
      {error && <span className="warn" role="alert">{error}</span>}
    </form>
  );
}

export default function ChangeDecision({ setId, item, editable, onDone }: { setId: number; item: ChangeItem; editable: boolean; onDone: () => void }) {
  const [open, setOpen] = useState(false);
  if (editable && (item.status === "proposed" || open))
    return <DecisionForm setId={setId} item={item} onDone={() => { setOpen(false); onDone(); }} onCancel={open ? () => setOpen(false) : undefined} />;
  if (item.status === "proposed" || !item.kind) return <span className="muted">Not decided</span>;
  return (
    <div>
      <span className={`badge ${KIND_CLASS[item.kind]}`}>{KINDS[item.kind]}</span>{item.target && <span className="mono">{item.target}</span>}
      <div className="muted">Confirmed by {item.decided_by}
        {editable && <button type="button" className="link" onClick={() => setOpen(true)}>Change</button>}</div>
    </div>
  );
}
