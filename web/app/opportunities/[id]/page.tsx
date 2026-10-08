"use client";
// Documents: upload the RFP, see ingestion status, run the reader agent.  Owner: Piyush.
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { post, useApi } from "@/lib/api";
import type { Doc, Opportunity } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";

export default function DocumentsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data, reload } = useApi<{ opportunity: Opportunity; documents: Doc[] }>(`/api/opportunities/${id}`);
  const [busy, setBusy] = useState("");

  async function upload(form: FormData) {
    setBusy("Uploading…");
    await post(`/api/opportunities/${id}/documents`, form);
    setBusy("");
    reload();
  }
  async function extract() {
    setBusy("Reader agent running…");
    await post(`/api/opportunities/${id}/requirements/extract`).catch((e) => alert(e));
    router.push(`/opportunities/${id}/requirements`);
  }

  return (
    <>
      <PageHead level={2} title="RFP documents"
        help={`${data?.opportunity.customer || "Customer not set"} · ${data?.opportunity.customer_type || "customer type not set"}. Upload the RFP, then let the reader agent break it into requirements.`} />
      <table>
        <thead><tr><th>File</th><th>Role</th><th>Pages</th><th>Status</th><th>SHA-256</th></tr></thead>
        <tbody>
          {data?.documents.map((d) => (
            <tr key={d.id}><td>{d.filename}</td><td>{d.role}</td><td>{d.page_count}</td>
              <td><span className="badge">{d.status}</span></td><td className="mono">{d.sha256.slice(0, 12)}</td></tr>
          ))}
          {data?.documents.length === 0 && <tr><td colSpan={5} className="muted">No documents yet.</td></tr>}
        </tbody>
      </table>
      <form className="card form" action={upload}>
        <label>RFP file (PDF) <input type="file" name="file" required /></label>
        <label>Role <select name="role">{["main", "addendum", "qa", "change", "other"].map((r) => <option key={r}>{r}</option>)}</select></label>
        <button disabled={!!busy}>Upload and read</button>
        <button type="button" className="secondary" onClick={reload}>Refresh status</button>
      </form>
      <button disabled={!!busy} onClick={extract}>Run the reader agent → requirements</button> <span className="muted">{busy}</span>
    </>
  );
}
