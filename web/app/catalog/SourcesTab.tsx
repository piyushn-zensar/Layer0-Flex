"use client";
// Sources view (P-35): reference documents are registered, reviewed, then read passage by passage.
// The detail is the same tab with ?ks=KS-0001, so both the list and a source can be linked.
import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { errorMessage, isBidManager, BID_MANAGER_ONLY, post, useApi, useMe } from "@/lib/api";
import type { KnowledgeSource, SourceDetail, SourceList } from "@/lib/types";
import { Alert, Busy, EmptyState, Skeleton, StatusBadge, useConfirm, useToast } from "@/components/ui";

const STATUS: Record<string, string> = { draft: "Draft", published: "Published", rejected: "Rejected", retired: "Retired" };
const REGISTER_ROLES = ["bid_manager", "product_manager", "design_engineer"];
const when = (iso?: string | null) => (iso ? iso.slice(0, 16).replace("T", " ") : "");
const Status = ({ s }: { s: string }) => <StatusBadge status={s} label={STATUS[s] ?? s} />;

function Register({ meta, onDone }: { meta: SourceList; onDone: (ks: string) => void }) {
  const toast = useToast();
  const me = useMe();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const allowed = !me || REGISTER_ROLES.includes(me.role);
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    setBusy(true); setError(undefined);
    try {
      const src = await post<KnowledgeSource & { existing?: boolean }>("/api/knowledge/sources", new FormData(form));
      if (src.existing) toast.info(`Already registered as ${src.ks_id}`);
      else { toast.success(`${src.ks_id} registered as a draft for review.`); form.reset(); }
      onDone(src.ks_id);
    } catch (err) { setError(errorMessage(err)); } finally { setBusy(false); }
  }
  return (
    <details className="card" data-tour="sources-register">
      <summary><strong>Register a source</strong></summary>
      <form className="form" onSubmit={submit}>
        <label className="grow">File <span className="field-hint">(PDF, Word, Excel, HTML, Markdown or text)</span>
          <input type="file" name="file" required accept=".pdf,.docx,.xlsx,.html,.htm,.md,.txt" /></label>
        <label>Collection
          <select name="collection" required defaultValue="">
            <option value="" disabled>Choose…</option>
            {Object.entries(meta.collections).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label className="grow">Title <input name="title" /></label>
        <label>Publisher <input name="publisher" /></label>
        <label className="narrow">Revision <input name="revision" /></label>
        <label>Scope <input name="scope" /></label>
        <label className="narrow">Permissions <input name="permissions" defaultValue="public" /></label>
        <label className="grow">Source URL <input type="url" name="url" placeholder="https://" /></label>
        <label className="narrow">Bid <span className="field-hint">(Current bid evidence only)</span> <input name="bid" placeholder="OPP-0001" pattern="OPP-[0-9]+" /></label>
        <div className="inline">
          <button disabled={busy || !allowed} title={allowed ? undefined : "Your role cannot register sources."}>Register</button>
          {busy && <Busy label="Reading the file…" />}
        </div>
        {!allowed && <p className="muted">Your role cannot register sources; ask the bid manager, a unit manager or a unit designer / engineer.</p>}
        <Alert kind="error">{error}</Alert>
      </form>
    </details>
  );
}

function Detail({ ks, meta, back }: { ks: string; meta: SourceList; back: () => void }) {
  const toast = useToast();
  const me = useMe();
  const [ask, confirmDialog] = useConfirm();
  const { data, error, reload } = useApi<SourceDetail>(`/api/knowledge/sources/${ks}`);
  const [busy, setBusy] = useState<string>();
  const [fail, setFail] = useState<string>();
  const [q, setQ] = useState("");
  if (error) return <><button className="link" onClick={back}>← All sources</button><Alert kind="error">{error}</Alert></>;
  if (!data) return <Skeleton lines={4} />;
  const { source: s, passages } = data;
  const canReview = !!me && (meta.reviewers[s.collection] ?? []).includes(me.role);
  const hint = canReview ? undefined : "Only the reviewers for this collection can do this.";

  async function run(what: string, work: () => Promise<unknown>, done: string) {
    setBusy(what); setFail(undefined);
    try { await work(); toast.success(done); reload(); } catch (e) { setFail(errorMessage(e)); } finally { setBusy(undefined); }
  }
  const review = (approve: boolean, note: string) =>
    run(approve ? "approve" : "reject", () => post(`/api/knowledge/sources/${ks}/review`, { approve, note }), approve ? `${ks} published.` : `${ks} rejected.`);
  async function approve() {
    if (await ask({ title: `Publish ${ks}?`, message: "It becomes usable as evidence, and the earlier published version of the same document is retired.", confirmLabel: "Approve and publish" })) review(true, "");
  }
  function reject(form: HTMLFormElement) {
    const note = String(new FormData(form).get("note") ?? "").trim();
    if (!note) { setFail("Give a note so the person who registered it knows why it was rejected."); return; }
    review(false, note);
  }
  const needle = q.trim().toLowerCase();
  const shown = needle ? passages.filter((p) => [p.heading, p.text, ...(p.annotations?.topics ?? [])].some((t) => t.toLowerCase().includes(needle))) : passages;
  const row = (k: string, v: React.ReactNode) => <div><dt className="muted">{k}</dt><dd>{v || <span className="muted">-</span>}</dd></div>;

  return (
    <>
      {confirmDialog}
      <button className="link" onClick={back}>← All sources</button>
      <section className="card" data-tour="source-detail">
        <div className="card-head">
          <h2><span className="mono">{s.ks_id}</span> {s.title}</h2>
          <span className="muted">version {s.version}</span><Status s={s.status} />
        </div>
        <dl className="grid-2">
          {row("Collection", meta.collections[s.collection] ?? s.collection)}
          {row("Publisher", s.publisher)}
          {row("Revision", s.revision)}
          {row("Scope", s.scope)}
          {row("Permissions", s.permissions)}
          {row("Source URL", s.url && <a href={s.url} target="_blank" rel="noopener noreferrer">{s.url}</a>)}
          {row("File", s.file_name)}
          {row("Document ID", <><span className="mono">{s.document_id}</span> <span className="muted">({s.id_source === "embedded" ? "embedded in the file" : "taken from the file fingerprint"})</span></>)}
          {row("Instance ID", <span className="mono">{s.instance_id}</span>)}
          {row("Registered", `${s.registered_by}, ${when(s.registered_at)}`)}
          {row("Pages and passages", `${s.pages} pages, ${s.passages} passages, ${s.annotated} annotated`)}
        </dl>
        <details><summary className="muted">Details</summary><p>File fingerprint: <span className="mono">{s.sha256}</span></p></details>
        {s.reviewed_by && <p>{STATUS[s.status]} by {s.reviewed_by}, {when(s.reviewed_at)}{s.review_note && <>: {s.review_note}</>}</p>}

        {s.status === "draft" && (
          <form className="form compact" onSubmit={(e) => e.preventDefault()}>
            <label>Note <span className="field-hint">(required to reject)</span><input name="note" /></label>
            <div className="inline">
              <button type="button" disabled={!canReview || !!busy} title={hint} onClick={approve}>Approve</button>
              <button type="button" className="danger secondary" disabled={!canReview || !!busy} title={hint}
                onClick={(e) => reject(e.currentTarget.form!)}>Reject</button>
              {busy === "approve" || busy === "reject" ? <Busy label="Saving…" /> : null}
            </div>
            {!canReview && <p className="muted">{hint}</p>}
          </form>)}
        <div className="inline">
          <button type="button" className="secondary" disabled={!isBidManager(me) || !!busy} title={isBidManager(me) ? undefined : BID_MANAGER_ONLY}
            onClick={() => run("annotate", async () => { const r = await post<{ annotated: number }>(`/api/knowledge/sources/${ks}/annotate`); toast.info(`${r.annotated} passage(s) annotated.`); }, "Annotation finished.")}>
            Annotate with the model</button>
          {busy === "annotate" && <Busy label="Annotating, this can take a while…" />}
        </div>
        <Alert kind="error">{fail}</Alert>
      </section>

      <section className="card" data-tour="source-passages">
        <div className="card-head"><h2>Passages</h2><span className="muted">{shown.length} of {passages.length}</span></div>
        <input type="search" aria-label="Filter passages" placeholder="Filter passages by text, heading or topic" value={q} onChange={(e) => setQ(e.target.value)} />
        {shown.length === 0 && <EmptyState title={passages.length ? "No passage matches" : "No passages"} hint={passages.length ? "Try another word." : "Nothing could be read from this file."} />}
        {shown.map((p) => (
          <article key={p.id} className="stack" style={{ borderTop: "1px solid var(--line)", paddingTop: "var(--s3)", marginTop: "var(--s3)" }}>
            <div className="row">
              <strong>p. {p.page}, lines {p.line_start}-{p.line_end}</strong>
              {p.heading && <span className="muted">{p.heading}</span>}
              {p.table && <span className="tag" title={p.table}>Table</span>}
            </div>
            <p style={{ whiteSpace: "pre-wrap" }}>{p.text}</p>
            {p.annotations && (
              <div className="stack muted">
                <div className="row">{p.annotations.topics.map((t) => <span key={t} className="chip">{t}</span>)}
                  {p.annotations.content_type && <span>Content type: {p.annotations.content_type}</span>}</div>
                {p.annotations.attributes.length > 0 && (
                  <ul>{p.annotations.attributes.map((a, i) => (
                    <li key={i}>{a.name}: {a.value}{a.unit && ` ${a.unit}`}{a.conditions && ` (${a.conditions})`}</li>))}</ul>)}
                {p.annotations.applicability && <span>Applies to: {p.annotations.applicability}</span>}
                {p.annotations.ambiguities.length > 0 && <span className="warn">Unclear: {p.annotations.ambiguities.join("; ")}</span>}
              </div>)}
          </article>))}
      </section>
    </>
  );
}

export default function SourcesTab() {
  const router = useRouter();
  const params = useSearchParams();
  const ks = params.get("ks") ?? "";
  const collection = params.get("collection") ?? "";
  const status = params.get("status") ?? "";
  const qs = `collection=${encodeURIComponent(collection)}&status=${encodeURIComponent(status)}`;
  const { data, error, reload } = useApi<SourceList>(`/api/knowledge/sources?${qs}`);
  const go = (patch: Record<string, string>) => {
    const next = new URLSearchParams(params.toString());
    for (const [k, v] of Object.entries(patch)) { if (v) next.set(k, v); else next.delete(k); }
    router.replace(`/catalog?${next}`);
  };
  if (error) return <Alert kind="error">{error}</Alert>;
  if (!data) return <Skeleton lines={4} />;
  if (ks) return <Detail ks={ks} meta={data} back={() => { go({ ks: "" }); reload(); }} />;

  return (
    <>
      <p className="muted">Sources become evidence only after review. Market and vendor context is never used as verified evidence.</p>
      <Register meta={data} onDone={(id) => { reload(); go({ ks: id }); }} />
      <div className="filters" data-tour="sources-filters">
        <label><span className="sr-only">Collection</span>
          <select value={collection} onChange={(e) => go({ collection: e.target.value })}>
            <option value="">All collections</option>
            {Object.entries(data.collections).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label><span className="sr-only">Status</span>
          <select value={status} onChange={(e) => go({ status: e.target.value })}>
            <option value="">Any status</option>
            {data.statuses.map((s) => <option key={s} value={s}>{STATUS[s] ?? s}</option>)}</select></label>
      </div>
      {data.sources.length === 0 ? <EmptyState title="No sources" hint={collection || status ? "Nothing matches these filters." : "Register a reference document to get started."} /> : (
        <table className="dense" data-tour="sources-table">
          <thead><tr><th>Title</th><th>Collection</th><th>Status</th><th className="num">Pages</th><th className="num">Passages</th><th className="num">Version</th><th>Registered</th></tr></thead>
          <tbody>{data.sources.map((s) => (
            <tr key={s.ks_id}>
              <td><button className="link" onClick={() => go({ ks: s.ks_id })}>{s.title || s.file_name}</button>
                <div className="muted">{[s.publisher, s.revision].filter(Boolean).join(" · ")}</div></td>
              <td>{data.collections[s.collection] ?? s.collection}</td>
              <td><Status s={s.status} /></td>
              <td className="num">{s.pages}</td><td className="num">{s.passages}</td><td className="num">{s.version}</td>
              <td>{s.registered_by}<div className="muted">{when(s.registered_at)}</div></td>
            </tr>))}</tbody>
        </table>)}
    </>
  );
}
