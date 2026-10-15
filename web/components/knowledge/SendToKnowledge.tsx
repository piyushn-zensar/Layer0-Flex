"use client";
// "Nominate as a reviewed example" (A-11, P-36): offers a requirement, a validated answer, a decision rationale or a correction
// as a reviewed example, with its type, when it holds, when it does not apply and why it is worth keeping. The person who may
// review it decides (My work, "Knowledge review"). Shows the state once nominated.  Owner: Atharv.
import { useState } from "react";
import { errorMessage, post } from "@/lib/api";
import { KB_EXAMPLE_TYPES, type KbItem } from "@/lib/types";
import { StatusBadge, useToast } from "@/components/ui";

type Kind = "requirement" | "response" | "decision" | "correction";
const STATE: Record<string, string> = { queued: "Waiting for review", approved: "Reviewed example", retired: "Replaced by a newer version" };
const FULL = "Nominate as a reviewed example";

export default function SendToKnowledge({ kind, refId, status, onSent, short }:
  { kind: Kind; refId: string | number; status?: string; onSent?: () => void; short?: boolean }) {
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  if (status && status !== "rejected") return <StatusBadge status={status} label={STATE[status] ?? status} className="kb-sent" />;
  if (!open)
    return <button type="button" className="link" data-tour="kb-send-button" title={FULL} onClick={(e) => { e.stopPropagation(); setOpen(true); }}>{short ? "Nominate" : FULL}</button>;

  async function send(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const text = (k: string) => String(f.get(k) ?? "").trim();
    setBusy(true); setError(undefined);
    try {
      const item = await post<KbItem>("/api/knowledge", { kind, ref: String(refId), example_type: text("example_type"), conditions: text("conditions"), limits: text("limits"), note: text("note") });
      setOpen(false); onSent?.(); toast.success(`Nominated as ${item.kb_id}; waiting for review.`);
    } catch (err) { setError(errorMessage(err)); } finally { setBusy(false); }
  }
  return (
    <form className="form compact" onSubmit={send} onClick={(e) => e.stopPropagation()} onKeyDown={(e) => e.stopPropagation()} data-tour="kb-send-form">
      <label>Example type
        <select name="example_type" defaultValue={kind === "requirement" ? "requirement" : "other"} disabled={busy} autoFocus>
          {Object.entries(KB_EXAMPLE_TYPES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
      <label>When does this example hold? <input name="conditions" maxLength={2000} disabled={busy} /></label>
      <label>When does it not apply? <input name="limits" maxLength={2000} disabled={busy} /></label>
      <label>Why keep it? <input name="note" maxLength={2000} disabled={busy} data-tour="kb-send-note" /></label>
      <div className="inline">
        <button className="sm" disabled={busy} data-tour="kb-send-submit">{busy ? "Nominating…" : "Nominate"}</button>
        <button type="button" className="secondary sm" disabled={busy} onClick={() => setOpen(false)}>Cancel</button>
      </div>
      {error && <span className="warn" role="alert">{error}</span>}
    </form>
  );
}
