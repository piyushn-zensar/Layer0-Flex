"use client";
// Documents: upload the RFP, see ingestion status, run the reader agent.  Owner: Piyush.
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { BID_MANAGER_ONLY, api, errorMessage, isBidManager, post, useApi, useMe } from "@/lib/api";
import { DOC_TYPES, docTypeLabel, snapshotName, type Doc, type Opportunity, type Snapshot } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { Alert, Busy, Skeleton, StatusBadge, useToast } from "@/components/ui";

type Received = Doc & { received_at?: string }; // the API row carries received_at; the shared Doc type does not list it yet

export default function DocumentsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const toast = useToast();
  const { data, error, reload } = useApi<{ opportunity: Opportunity; documents: Received[] }>(`/api/opportunities/${id}`);
  const { data: snapshots } = useApi<Snapshot[]>(`/api/opportunities/${id}/extraction`);
  const bm = isBidManager(useMe()); // uploading and reading are the bid manager's (section 16.6)
  const readBefore = (snapshots?.length ?? 0) > 0; // a snapshot exists: reading again needs a reason (E2, E3...)
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
  async function extract(reason?: string) {
    setBusy("Reader agent running… (about a minute for a 100-page RFP)"); setMessage(undefined);
    try {
      const r = await post<{ proposed: number; problems: string[]; snapshot?: number; exceptions?: number }>(`/api/opportunities/${id}/requirements/extract`, reason ? { reason } : {});
      const saved = r.snapshot ? ` Saved as extraction snapshot ${snapshotName(r.snapshot)}${r.exceptions !== undefined ? `; ${r.exceptions} exception${r.exceptions === 1 ? "" : "s"}` : ""}.` : "";
      if (r.problems.length) setMessage({ text: `${r.proposed} line items proposed.${saved} Some pages were not read:`, problems: r.problems });
      else { if (saved) toast.success(`${r.proposed} line items proposed.${saved}`); router.push(`/opportunities/${id}/requirements`); }
    } catch (e) { fail(e); } finally { setBusy(""); }
  }
  const status = data?.opportunity.status;
  const canRead = status === "new" || status === "review";
  const unread = data?.documents.find((d) => d.role === "main" && d.status !== "ingested");
  const started = !!data && !canRead; // UX-17: once review has started the upload form is secondary
  const received = (d: Received) => d.received_at ? new Date(d.received_at).toLocaleDateString() : "";

  const form = (
    <form className={started ? "form" : "card form"} onSubmit={upload} aria-busy={!!busy} data-tour="rfp-upload-form">
      <label data-tour="rfp-file">RFP file (PDF) <input type="file" name="file" required disabled={!!busy} /></label>
      <label data-tour="rfp-role">Document type <select name="role" defaultValue={started ? "addendum" : "main"} disabled={!!busy}>{Object.entries(DOC_TYPES).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
      <button disabled={!!busy || !bm} title={bm ? "" : BID_MANAGER_ONLY} data-tour="rfp-upload">Upload and read</button>
      <button type="button" className="secondary" disabled={!!busy} onClick={reload} data-tour="rfp-refresh">Refresh status</button>
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
        <table className="docs" data-tour="rfp-docs-table">
          <thead><tr><th>File</th><th>Document type</th><th className="num">Pages</th><th>Status</th><th>Received</th></tr></thead>
          <tbody>
            {data.documents.map((d) => (
              <tr key={d.id} data-tour={d.role === "main" ? "rfp-doc-main" : `rfp-doc-${d.id}`}><td>{d.filename}</td><td>{docTypeLabel(d.role)}</td><td className="num">{d.page_count}</td>
                <td data-tour={d.role === "main" ? "rfp-doc-status" : undefined}><StatusBadge status={d.status} /></td>
                <td title={`SHA-256 ${d.sha256}`} data-tour={d.role === "main" ? "rfp-doc-received" : undefined}>{received(d) || <span className="mono">{d.sha256.slice(0, 12)}</span>}</td></tr>
            ))}
            {data.documents.length === 0 && <tr><td colSpan={5} className="muted">No documents yet. Upload the RFP below.</td></tr>}
          </tbody>
        </table>)}
      {data && (started
        ? <details className="card" data-tour="rfp-add-another"><summary><strong>Add another document</strong> <span className="muted">(addendum, clarification / Q&amp;A, change request)</span></summary>{form}</details>
        : form)}
      {data?.documents.some((d) => d.role === "main" && d.status === "ingested") && (
        <section className="card" data-tour="rfp-search">
          <div className="card-head"><h2>Search this RFP</h2><span className="muted">Ask in plain words; the best passages come back with page and lines.</span></div>
          <form className="inline rfp-search" role="search" action={search} data-tour="rfp-search-form">
            <label><span className="sr-only">Question</span>
              <input type="search" name="q" required placeholder="e.g. what short-circuit rating is required?" className="wide" data-tour="rfp-search-input" /></label>
            <button disabled={searching}>Search</button>
            {searching && <Busy label="Searching…" />}
          </form>
          {found && (<div data-tour="rfp-search-results">
            <p className="muted">{found.mode === "embeddings" ? "Meaning-based search" : "Keyword search (no embedding service: offline)"} over the RFP&apos;s passages.</p>
            <ol className="passages">{found.passages.map((p) => (
              <li key={`${p.page}-${p.line_start}`}><span className="mono">p. {p.page}, lines {p.line_start}-{p.line_end}</span> {p.text}</li>))}
              {found.passages.length === 0 && <li className="muted">Nothing found.</li>}</ol>
          </div>)}
        </section>)}
      {data && (canRead ? (<div className="row" data-tour="rfp-extract-row">
        {readBefore ? (
          <form className="form" data-tour="rfp-reread-form" onSubmit={(e) => { e.preventDefault(); const reason = String(new FormData(e.currentTarget).get("reason")).trim(); if (reason) extract(reason); }}>
            <label>Why read the RFP again? <span className="field-hint">(the earlier snapshots are kept)</span> <input name="reason" required maxLength={500} disabled={!!busy} /></label>
            <button disabled={!!busy || !!unread || !bm} title={bm ? "" : BID_MANAGER_ONLY} data-tour="rfp-extract">Read again</button>
          </form>
        ) : <button disabled={!!busy || !!unread || !bm} title={bm ? "" : BID_MANAGER_ONLY} onClick={() => extract()} data-tour="rfp-extract">Run the reader agent → requirements</button>}
        {!bm && <span className="muted">Only the bid manager uploads documents and runs the reader.</span>}
        {busy ? <Busy label={busy} /> : unread && <span className="muted" role="status">Waiting for the main RFP to be read; use Refresh status.</span>}</div>)
        : <p className="muted" data-tour="rfp-started-note">Requirement review has started, so the RFP is not re-read. Missed items can be added on the Requirements page.</p>)}
    </>
  );
}
