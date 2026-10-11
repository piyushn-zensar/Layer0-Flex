"use client";
// Knowledge-base queue (A-11): the curator approves or rejects what people sent. Approved items join the long-term
// retrieval index used by matching evidence, the response outline and catalog search.  Owner: Atharv.
import Link from "next/link";
import { useState } from "react";
import { currentActor, errorMessage, post, useApi } from "@/lib/api";
import PageHead from "@/components/shell/PageHead";
import { Alert, Busy, EmptyState, Skeleton, StatusBadge, useToast } from "@/components/ui";

type Item = {
  kb_id: string; kind: string; source_ref: string; opportunity_id: string; bu: string; requirement: string; response: string;
  source: string; note: string; status: string; sent_by: string; sent_at: string; reviewed_by: string | null; review_note: string;
};
type Data = { items: Item[]; curator: string; learned: number; index: string };
const TABS = [{ key: "queued", label: "Waiting" }, { key: "approved", label: "Approved" }, { key: "rejected", label: "Rejected" }] as const;
const KIND = { requirement: "Requirement", response: "Validated answer", decision: "Decision rationale" } as Record<string, string>;

function Review({ item, onDone, first }: { item: Item; onDone: () => void; first?: boolean }) {
  const toast = useToast();
  const [busy, setBusy] = useState<"approve" | "reject">();
  const [error, setError] = useState<string>();
  async function act(form: FormData, approve: boolean) {
    const note = String(form.get("note") ?? "").trim();
    if (!approve && !note) { setError("Give a note so the sender knows why it was rejected."); return; }
    setBusy(approve ? "approve" : "reject"); setError(undefined);
    try {
      await post(`/api/knowledge/${item.kb_id}/review`, { approve, note, response: String(form.get("response") ?? "") });
      toast.success(approve ? `${item.kb_id} approved into the knowledge base.` : `${item.kb_id} rejected.`);
      onDone();
    } catch (e) { setError(errorMessage(e)); } finally { setBusy(undefined); }
  }
  return (
    <form className="form compact kb-review" onSubmit={(e) => { e.preventDefault(); act(new FormData(e.currentTarget), true); }} data-tour={first ? "kb-review-form" : undefined}>
      <label data-tour={first ? "kb-review-response" : undefined}>Response to keep <span className="field-hint">(tidy it if needed)</span><textarea name="response" defaultValue={item.response} rows={3} /></label>
      <label data-tour={first ? "kb-review-note" : undefined}>Note <span className="field-hint">(required to reject)</span><input name="note" aria-invalid={error && !busy ? true : undefined} /></label>
      <div className="inline">
        <button disabled={!!busy} data-tour={first ? "kb-approve" : undefined}>Approve into the knowledge base</button>
        <button type="button" className="danger secondary" disabled={!!busy} data-tour={first ? "kb-reject" : undefined}
          onClick={(e) => act(new FormData(e.currentTarget.form!), false)}>Reject</button>
        {busy && <Busy label={busy === "approve" ? "Approving…" : "Rejecting…"} />}
      </div>
      <Alert kind="error">{error}</Alert>
    </form>
  );
}

export default function KnowledgePage() {
  const [tab, setTab] = useState<(typeof TABS)[number]["key"]>("queued");
  const { data, error, reload } = useApi<Data>("/api/knowledge");
  if (error) return <div className="content"><PageHead title="Knowledge base" /><Alert kind="error">{error}</Alert></div>;
  if (!data) return <div className="content"><PageHead title="Knowledge base" /><Skeleton lines={4} /></div>;
  const shown = data.items.filter((i) => i.status === tab);
  const curator = currentActor() === data.curator;

  return (
    <div className="content">
      <PageHead title="Knowledge base"
        help="Requirements, validated answers and decision rationales that people sent from an opportunity. The curator approves what the next bids should learn from; approved items are found by matching, the response outline and catalog search." />
      <p data-tour="kb-learned">{data.learned} approved item(s) in the long-term index, next to the illustrative past responses of the <Link href="/catalog">product catalog</Link>.</p>
      {!curator && <div data-tour="kb-curator-note"><Alert kind="info">Only the curator ({data.curator}) approves or rejects; switch with “Acting as” in the top bar.</Alert></div>}
      <div className="row kb-tabs" role="group" aria-label="Filter by status" data-tour="kb-tabs">
        {TABS.map((t) => (
          <button key={t.key} type="button" className="chip" aria-pressed={tab === t.key} onClick={() => setTab(t.key)} data-tour={`kb-tab-${t.key}`}>
            {t.label} <span>{data.items.filter((i) => i.status === t.key).length}</span></button>))}
      </div>
      {shown.length === 0 && (tab === "queued"
        ? <div data-tour="kb-empty"><EmptyState title="Nothing waiting" hint="Use “Send to knowledge base” in Traceability, the response outline or the bid decision to queue an item." /></div>
        : <div data-tour="kb-empty"><EmptyState title={`No ${tab} items`} /></div>)}
      {shown.map((i, n) => (
        <section key={i.kb_id} className="card kb-item" data-tour={n === 0 ? "kb-item-first" : `kb-item-${i.kb_id}`}>
          <div className="card-head">
            <h3><span className="mono">{i.kb_id}</span> {KIND[i.kind] ?? i.kind}</h3>
            <span className="muted">from <Link href={`/opportunities/${i.opportunity_id}/trace`}>{i.opportunity_id}</Link>, {i.source}</span>
            <StatusBadge status={i.status} />
          </div>
          <p className="muted">Sent by {i.sent_by}{i.note && <>: “{i.note}”</>}{i.bu !== "BID" && <> · unit {i.bu}</>}</p>
          <p><strong>Asked:</strong> {i.requirement}</p>
          {i.status === "queued" && curator ? <Review item={i} onDone={reload} first={n === 0} /> : <>
            {i.response && <p><strong>Answer:</strong> {i.response}</p>}
            {i.reviewed_by && <p className="muted">{i.status === "approved" ? "Approved" : "Rejected"} by {i.reviewed_by}{i.review_note && <>: {i.review_note}</>}</p>}
          </>}
        </section>
      ))}
    </div>
  );
}
