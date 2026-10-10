"use client";
// "Send to knowledge base" (A-11): puts a requirement, a validated answer or a decision rationale in the curator's
// queue, with an optional note. Shows the state once sent.  Owner: Atharv.
import { useState } from "react";
import { post } from "@/lib/api";

type Kind = "requirement" | "response" | "decision";

export default function SendToKnowledge({ kind, refId, status, onSent }:
  { kind: Kind; refId: string | number; status?: string; onSent?: () => void }) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  if (status && status !== "rejected")
    return <span className={`badge ${status === "approved" ? "status-approved" : "status-proposed"}`}>{status === "approved" ? "in knowledge base" : "sent to knowledge base"}</span>;
  if (!open)
    return <button type="button" className="link" onClick={(e) => { e.stopPropagation(); setOpen(true); }}>Send to knowledge base</button>;

  async function send(form: FormData) {
    setBusy(true); setError(undefined);
    try {
      await post("/api/knowledge", { kind, ref: String(refId), note: String(form.get("note") ?? "") });
      setOpen(false); onSent?.();
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); } finally { setBusy(false); }
  }
  return (
    <form className="kb-send" action={send} onClick={(e) => e.stopPropagation()}>
      <input name="note" placeholder="Why keep it? (optional)" maxLength={2000} aria-label="Note for the curator" autoFocus />
      <button disabled={busy}>Send</button>
      <button type="button" className="secondary" onClick={() => setOpen(false)}>Cancel</button>
      {error && <span className="warn">{error}</span>}
    </form>
  );
}
