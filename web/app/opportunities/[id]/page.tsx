"use client";
// Documents: upload the RFP, see ingestion status, run the reader agent.  Owner: Piyush.
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { api, errorMessage, post, useApi } from "@/lib/api";
import type { Doc, Opportunity } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { Alert, Busy, Skeleton, StatusBadge, useToast } from "@/components/ui";

type Received = Doc & { received_at?: string }; // the API row carries received_at; the shared Doc type does not list it yet

export default function DocumentsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const toast = useToast();
  const { data, error, reload } = useApi<{ opportunity: Opportunity; documents: Received[] }>(`/api/opportunities/${id}`);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState<{ text: string; problems?: string[] }>();
  type Passage = { page: number; line_start: number; line_end: number; text: string; score: number };
  const [found, setFound] = useState<{ mode: string; passages: Passage[] }>();
  const [searching, setSearching] = useState(false);
  const search = (form: FormData) => {
    setSearching(true);
    return api<{ mode: string; passages: Passage[] }>(`/api/opportunities/${id}/rfp-search?q=${encodeURIComponent(String(form.get("q") ?? ""))}`)
      .then(setFound, fail).finally(() => setSearching(false));
  };
  const fail = (e: unknown) => setMessage({ text: errorMessage(e) });

  // onSubmit, not a form action: React holds state updates made inside an action until it ends, so the busy text and
  // the disabled button would only appear after the read (a second click uploaded again); a failure keeps the file.
  async function upload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const file = new FormData(form); // before the inputs are disabled below
    setBusy("Uploading and reading the RFP… (about a minute for a 100-page RFP)"); setMessage(undefined);
    try { await post(`/api/opportunities/${id}/documents`, file); form.reset(); await reload(); toast.success("Document received and read."); } catch (err) { fail(err); }
    finally { setBusy(""); }
  }
  async function extract() {
    setBusy("Reader agent running… (about a minute for a 100-page RFP)"); setMessage(undefined);
    try {
      const r = await post<{ proposed: number; problems: string[] }>(`/api/opportunities/${id}/requirements/extract`);
      if (r.problems.length) setMessage({ text: `${r.proposed} line items proposed, but some pages were not read:`, problems: r.problems });
      else router.push(`/opportunities/${id}/requirements`);
    } catch (e) { fail(e); } finally { setBusy(""); }
  }
  const status = data?.opportunity.status;
  const canRead = status === "new" || status === "review";
  const unread = data?.documents.find((d) => d.role === "main" && d.status !== "ingested");
  const started = !!data && !canRead; // UX-17: once review has started the upload form is secondary
  const received = (d: Received) => d.received_at ? new Date(d.received_at).toLocaleDateString() : "";

  const form = (
    <form className={started ? "form" : "card form"} onSubmit={upload} aria-busy={!!busy}>
      <label>RFP file (PDF) <input type="file" name="file" required disabled={!!busy} /></label>
      <label>Role <select name="role" defaultValue={started ? "addendum" : "main"} disabled={!!busy}>{["main", "addendum", "qa", "change", "other"].map((r) => <option key={r}>{r}</option>)}</select></label>
      <button disabled={!!busy}>Upload and read</button>
      <button type="button" className="secondary" disabled={!!busy} onClick={reload}>Refresh status</button>
      {busy && !canRead && <Busy label={busy} />} {/* else shown by the reader button */}
    </form>);

  return (
    <>
      <PageHead level={2} title="RFP documents"
        help={`${data?.opportunity.customer || "Customer not set"} · ${data?.opportunity.customer_type || "customer type not set"}. Upload the RFP, then let the reader agent break it into requirements.`} />
      <Alert kind="error">{error}</Alert>
      {message && <Alert kind="error" onClose={() => setMessage(undefined)}><p>{message.text}</p>
        {message.problems && <ul>{message.problems.map((p) => <li key={p}>{p}</li>)}</ul>}</Alert>}
      {!data && !error && <Skeleton lines={3} />}
      {data && (
        <table className="docs">
          <thead><tr><th>File</th><th>Role</th><th className="num">Pages</th><th>Status</th><th>Received</th></tr></thead>
          <tbody>
            {data.documents.map((d) => (
              <tr key={d.id}><td>{d.filename}</td><td>{d.role}</td><td className="num">{d.page_count}</td>
                <td><StatusBadge status={d.status} /></td>
                <td title={`SHA-256 ${d.sha256}`}>{received(d) || <span className="mono">{d.sha256.slice(0, 12)}</span>}</td></tr>
            ))}
            {data.documents.length === 0 && <tr><td colSpan={5} className="muted">No documents yet. Upload the RFP below.</td></tr>}
          </tbody>
        </table>)}
      {data && (started
        ? <details className="card"><summary><strong>Add another document</strong> <span className="muted">(addendum, Q&amp;A, change)</span></summary>{form}</details>
        : form)}
      {data?.documents.some((d) => d.role === "main" && d.status === "ingested") && (
        <section className="card">
          <div className="card-head"><h2>Search this RFP</h2><span className="muted">Ask in plain words; the best passages come back with page and lines.</span></div>
          <form className="inline rfp-search" role="search" action={search}>
            <label><span className="sr-only">Question</span>
              <input type="search" name="q" required placeholder="e.g. what short-circuit rating is required?" className="wide" /></label>
            <button disabled={searching}>Search</button>
            {searching && <Busy label="Searching…" />}
          </form>
          {found && (<>
            <p className="muted">{found.mode === "embeddings" ? "Meaning-based search" : "Keyword search (no embedding service: offline)"} over the RFP&apos;s passages.</p>
            <ol className="passages">{found.passages.map((p) => (
              <li key={`${p.page}-${p.line_start}`}><span className="mono">p. {p.page}, lines {p.line_start}-{p.line_end}</span> {p.text}</li>))}
              {found.passages.length === 0 && <li className="muted">Nothing found.</li>}</ol>
          </>)}
        </section>)}
      {data && (canRead ? (<div className="row">
        <button disabled={!!busy || !!unread} onClick={extract}>Run the reader agent → requirements</button>
        {busy ? <Busy label={busy} /> : unread && <span className="muted" role="status">Waiting for the main RFP to be read; use Refresh status.</span>}</div>)
        : <p className="muted">Requirement review has started, so the RFP is not re-read. Missed items can be added on the Requirements page.</p>)}
    </>
  );
}
