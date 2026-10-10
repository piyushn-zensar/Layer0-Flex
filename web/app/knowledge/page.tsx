"use client";
// Knowledge-base queue (A-11): the curator approves or rejects what people sent. Approved items join the long-term
// retrieval index used by matching evidence, the response outline and catalog search.  Owner: Atharv.
import Link from "next/link";
import { useState } from "react";
import { currentActor, post, useApi } from "@/lib/api";
import PageHead from "@/components/shell/PageHead";

type Item = {
  kb_id: string; kind: string; source_ref: string; opportunity_id: string; bu: string; requirement: string; response: string;
  source: string; note: string; status: string; sent_by: string; sent_at: string; reviewed_by: string | null; review_note: string;
};
type Data = { items: Item[]; curator: string; learned: number; index: string };
const TABS = [{ key: "queued", label: "Waiting" }, { key: "approved", label: "Approved" }, { key: "rejected", label: "Rejected" }] as const;
const KIND = { requirement: "Requirement", response: "Validated answer", decision: "Decision rationale" } as Record<string, string>;

function Review({ item, onDone }: { item: Item; onDone: () => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  async function act(form: FormData, approve: boolean) {
    setBusy(true); setError(undefined);
    try {
      await post(`/api/knowledge/${item.kb_id}/review`, { approve, note: String(form.get("note") ?? ""), response: String(form.get("response") ?? "") });
      onDone();
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); } finally { setBusy(false); }
  }
  return (
    <form className="form compact" onSubmit={(e) => { e.preventDefault(); act(new FormData(e.currentTarget), true); }}>
      <label>Response to keep (tidy it if needed)<textarea name="response" defaultValue={item.response} rows={3} /></label>
      <label>Note <input name="note" placeholder="Required to reject" /></label>
      <p className="inline">
        <button disabled={busy}>Approve into the knowledge base</button>
        <button type="button" className="secondary" disabled={busy}
          onClick={(e) => act(new FormData(e.currentTarget.form!), false)}>Reject</button>
        {error && <span className="warn">{error}</span>}
      </p>
    </form>
  );
}

export default function KnowledgePage() {
  const [tab, setTab] = useState<(typeof TABS)[number]["key"]>("queued");
  const { data, error, reload } = useApi<Data>("/api/knowledge");
  if (error) return <div className="content"><p className="warn">{error}</p></div>;
  if (!data) return <div className="content"><p>Loading…</p></div>;
  const shown = data.items.filter((i) => i.status === tab);
  const curator = currentActor() === data.curator;

  return (
    <div className="content">
      <PageHead title="Knowledge base"
        help="Requirements, validated answers and decision rationales that people sent from an opportunity. The curator approves what the next bids should learn from; approved items are found by matching, the response outline and catalog search." />
      <p>{data.learned} approved item(s) in the long-term index, next to the illustrative past responses of the <Link href="/catalog">product catalog</Link>.
        {!curator && <span className="muted"> Only the curator ({data.curator}) approves; switch with Acting as.</span>}</p>
      <p className="inline" role="group" aria-label="Filter by status">
        {TABS.map((t) => (
          <button key={t.key} type="button" className={`chip${tab === t.key ? " on" : ""}`} aria-pressed={tab === t.key} onClick={() => setTab(t.key)}>
            {t.label} <span>{data.items.filter((i) => i.status === t.key).length}</span></button>))}
      </p>
      {shown.length === 0 && <p className="muted">{tab === "queued" ? "Nothing waiting. Use \"Send to knowledge base\" in Traceability, the response outline or the bid decision." : "None."}</p>}
      {shown.map((i) => (
        <section key={i.kb_id} className="card">
          <h3><span className="mono">{i.kb_id}</span> {KIND[i.kind] ?? i.kind} <span className="muted">from <Link href={`/opportunities/${i.opportunity_id}/trace`}>{i.opportunity_id}</Link>, {i.source}</span></h3>
          <p className="muted">Sent by {i.sent_by}{i.note && <>: “{i.note}”</>}{i.bu !== "BID" && <> · unit {i.bu}</>}</p>
          <p><strong>Asked:</strong> {i.requirement}</p>
          {i.status === "queued" && curator ? <Review item={i} onDone={reload} /> : <>
            {i.response && <p><strong>Answer:</strong> {i.response}</p>}
            {i.reviewed_by && <p className="muted">{i.status === "approved" ? "Approved" : "Rejected"} by {i.reviewed_by}{i.review_note && <>: {i.review_note}</>}</p>}
          </>}
        </section>
      ))}
    </div>
  );
}
