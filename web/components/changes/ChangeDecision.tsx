"use client";
// One change statement's decision (P-11): a person confirms or overrides the agent's classification and baseline target.  Owner: Piyush.
import { useState } from "react";
import { errorMessage, post } from "@/lib/api";
import type { ChangeItem, ChangeKind } from "@/lib/types";
import { StatusBadge } from "@/components/ui";

export const KINDS: Record<ChangeKind, string> = {
  added: "Added", modified: "Modified", removed: "Removed", unchanged: "Unchanged", not_a_requirement: "Not a requirement",
};
/** The kind as a coloured pill (added green, modified amber, removed red, the rest grey: the app's one status scheme). */
export const KindBadge = ({ kind }: { kind: ChangeKind }) => <StatusBadge status={kind} label={KINDS[kind]} />;
export const NEEDS_TARGET = new Set<ChangeKind>(["modified", "removed", "unchanged"]);
const OTHER = "other"; // a baseline requirement the agent did not offer
const short = (s: string) => (s.length > 70 ? `${s.slice(0, 70)}…` : s);

function DecisionForm({ setId, item, onDone, onCancel, tour = false }:
  { setId: number; item: ChangeItem; onDone: () => void; onCancel?: () => void; tour?: boolean }) {
  const t = (id: string) => (tour ? id : undefined); // walkthrough targets, only on the row the tour points at
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
    } catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  }
  // onSubmit, not action: a failed confirm keeps what was typed.
  return (
    <form className="form compact chg-decide" aria-label={`Decision for change ${item.n}`} aria-busy={busy} data-tour={t("chg-decide-form")}
      onSubmit={(e) => { e.preventDefault(); confirm(new FormData(e.currentTarget)); }}>
      <label>Change <select value={kind} onChange={(e) => setKind(e.target.value as ChangeKind)} data-tour={t("chg-decide-kind")}>
        {(Object.keys(KINDS) as ChangeKind[]).map((k) => <option key={k} value={k}>{KINDS[k]}</option>)}</select></label>
      {needsTarget && <label>Baseline requirement <select value={target} onChange={(e) => setTarget(e.target.value)} data-tour={t("chg-decide-target")}>
        {options.map((c) => <option key={c.req_id} value={c.req_id}>{c.req_id} — {short(c.text)}</option>)}
        <option value={OTHER}>Another requirement ID…</option></select></label>}
      {needsTarget && target === OTHER && <label>Requirement ID <input name="other" required maxLength={20} placeholder="REQ-…" aria-invalid={error ? true : undefined} data-tour={t("chg-decide-other")} /></label>}
      {wording && <label>New wording <textarea name="text" rows={2} maxLength={2000} defaultValue={item.text} data-tour={t("chg-decide-text")} /></label>}
      <span className="inline">
        <button className="sm" disabled={busy} data-tour={t("chg-decide-confirm")}>{busy ? "Confirming…" : "Confirm"}</button>
        {onCancel && <button type="button" className="secondary sm" disabled={busy} onClick={onCancel}>Cancel</button>}
      </span>
      {error && <span className="warn" role="alert">{error}</span>}
    </form>
  );
}

export default function ChangeDecision({ setId, item, editable, onDone, tour = false }:
  { setId: number; item: ChangeItem; editable: boolean; onDone: () => void; tour?: boolean }) {
  const [open, setOpen] = useState(false);
  if (editable && (item.status === "proposed" || open))
    return <DecisionForm setId={setId} item={item} onDone={() => { setOpen(false); onDone(); }} onCancel={open ? () => setOpen(false) : undefined} tour={tour} />;
  if (item.status === "proposed" || !item.kind) return <span className="muted">Not decided</span>;
  return (
    <div data-tour={tour ? "chg-decided" : undefined}>
      <KindBadge kind={item.kind} />{item.target && <span className="mono">{item.target}</span>}
      <div className="muted">Confirmed by {item.decided_by}
        {editable && <button type="button" className="link" onClick={() => setOpen(true)} data-tour={tour ? "chg-decided-change" : undefined}>Change</button>}</div>
    </div>
  );
}
