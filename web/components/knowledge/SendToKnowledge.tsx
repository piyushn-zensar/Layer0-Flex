"use client";
// "Send to knowledge base" (A-11): puts a requirement, a validated answer or a decision rationale in the curator's
// queue, with an optional note. Shows the state once sent.  Owner: Atharv.
import { useState } from "react";
import { errorMessage, post } from "@/lib/api";
import { StatusBadge, useToast } from "@/components/ui";

type Kind = "requirement" | "response" | "decision";

export default function SendToKnowledge({ kind, refId, status, onSent }:
  { kind: Kind; refId: string | number; status?: string; onSent?: () => void }) {
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  if (status && status !== "rejected")
    return <StatusBadge status={status} label={status === "approved" ? "in knowledge base" : "sent to knowledge base"} className="kb-sent" />;
  if (!open)
    return <button type="button" className="link" data-tour="kb-send-button" onClick={(e) => { e.stopPropagation(); setOpen(true); }}>Send to knowledge base</button>;

  async function send(form: FormData) {
    setBusy(true); setError(undefined);
    try {
      await post("/api/knowledge", { kind, ref: String(refId), note: String(form.get("note") ?? "") });
      setOpen(false); onSent?.(); toast.success("Sent to the knowledge base for curation.");
    } catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  }
  return (
    <form className="kb-send" action={send} onClick={(e) => e.stopPropagation()} onKeyDown={(e) => e.stopPropagation()} data-tour="kb-send-form">
      <input name="note" placeholder="Why keep it? (optional)" maxLength={2000} aria-label="Note for the curator" autoFocus disabled={busy} data-tour="kb-send-note" />
      <button className="sm" disabled={busy} data-tour="kb-send-submit">{busy ? "Sending…" : "Send"}</button>
      <button type="button" className="secondary sm" disabled={busy} onClick={() => setOpen(false)}>Cancel</button>
      {error && <span className="warn" role="alert">{error}</span>}
    </form>
  );
}
