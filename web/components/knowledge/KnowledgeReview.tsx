"use client";
// "Knowledge review" on My work (P-36): examples people nominated that the signed-in person may approve or reject.
// Approving may tidy the response first; rejecting needs a note.  Owner: Atharv.
import { useState } from "react";
import { errorMessage, post, useApi } from "@/lib/api";
import { KB_EXAMPLE_TYPES, type KbItem, type KbList } from "@/lib/types";
import { Alert, Busy, Skeleton, useToast } from "@/components/ui";

const KIND: Record<string, string> = { requirement: "Requirement", response: "Validated answer", decision: "Decision rationale", correction: "Correction" };
const when = (iso?: string | null) => (iso ? iso.slice(0, 16).replace("T", " ") : "");

function Review({ item, onDone }: { item: KbItem; onDone: () => void }) {
  const toast = useToast();
  const [busy, setBusy] = useState<"approve" | "reject">();
  const [error, setError] = useState<string>();
  async function act(form: HTMLFormElement, approve: boolean) {
    const f = new FormData(form);
    const note = String(f.get("note") ?? "").trim();
    if (!approve && !note) { setError("Give a note so the person who nominated it knows why it was rejected."); return; }
    setBusy(approve ? "approve" : "reject"); setError(undefined);
    try {
      const edited = String(f.get("response") ?? "");
      await post(`/api/knowledge/${item.kb_id}/review`, { approve, note, response: approve && edited !== item.response ? edited : null });
      toast.success(approve ? `${item.kb_id} approved as a reviewed example.` : `${item.kb_id} rejected.`);
      onDone();
    } catch (e) { setError(errorMessage(e)); } finally { setBusy(undefined); }
  }
  const row = (k: string, v?: string) => v ? <div><strong>{k}:</strong> {v}</div> : null;
  return (
    <li className="card stack">
      <div className="card-head">
        <h3><span className="mono">{item.kb_id}</span> {KB_EXAMPLE_TYPES[item.example_type] ?? item.example_type}</h3>
        <span className="muted">{KIND[item.kind] ?? item.kind} · from {item.opportunity_id}{item.source && <>, {item.source}</>}</span>
      </div>
      {row("Requirement", item.requirement)}
      {row("Response", item.response)}
      {row("When it holds", item.conditions)}
      {row("When it does not apply", item.limits)}
      {row("Why keep it", item.note)}
      <div className="muted">Nominated by {item.sent_by}, {when(item.sent_at)}</div>
      <form className="form compact" onSubmit={(e) => { e.preventDefault(); act(e.currentTarget, true); }}>
        <label>Response to keep <span className="field-hint">(tidy it if needed)</span><textarea name="response" defaultValue={item.response} rows={3} disabled={!!busy} /></label>
        <label>Note <span className="field-hint">(required to reject)</span><input name="note" disabled={!!busy} /></label>
        <div className="inline">
          <button className="sm" disabled={!!busy}>Approve</button>
          <button type="button" className="danger secondary sm" disabled={!!busy} onClick={(e) => act(e.currentTarget.form!, false)}>Reject</button>
          {busy && <Busy label={busy === "approve" ? "Approving…" : "Rejecting…"} />}
        </div>
        <Alert kind="error">{error}</Alert>
      </form>
    </li>
  );
}

export default function KnowledgeReview() {
  const { data, error, reload } = useApi<KbList>("/api/knowledge?status=queued&reviewable=true");
  return (
    <details className="card" open={!!data?.items.length || undefined} data-tour="kb-review-section">
      <summary><strong>Knowledge review{data && data.items.length > 0 && ` (${data.items.length})`}</strong></summary>
      {error ? <Alert kind="error">{error}</Alert> : !data ? <Skeleton lines={2} /> : (<>
        <p className="muted">Approved examples become reusable knowledge. {data.curator}</p>
        {data.items.length === 0 ? <p className="muted">No examples are waiting for your review.</p>
          : <ul className="stack" style={{ listStyle: "none", padding: 0 }}>{data.items.map((i) => <Review key={i.kb_id} item={i} onDone={reload} />)}</ul>}
      </>)}
    </details>
  );
}
