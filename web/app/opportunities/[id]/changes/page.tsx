"use client";
// Changes (P-11): read an addendum, Q&A answers or a change request against the frozen baseline; a person confirms each
// change, then the Bid Manager applies it.  Owner: Piyush.
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { post, useApi } from "@/lib/api";
import type { Changes } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import ChangeSetCard from "@/components/changes/ChangeSetCard";

export default function ChangesPage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, reload } = useApi<Changes>(`/api/opportunities/${id}/changes`);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState<string>();

  // onSubmit, not a form action: React holds state updates made inside an action until it ends, so the busy text and
  // the disabled button would only appear after the upload; a failed upload also keeps the chosen file.
  async function upload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const file = new FormData(form); // before the input is disabled below
    setBusy("Reading the change document…"); setMessage(undefined);
    try { await post(`/api/opportunities/${id}/changes`, file); form.reset(); await reload(); }
    catch (err) { setMessage(err instanceof Error ? err.message : String(err)); } finally { setBusy(""); }
  }
  if (error) return <p className="warn">{error}</p>;
  if (!data) return <p>Loading…</p>;
  const inReview = data.sets.some((s) => s.status === "review");

  return (
    <>
      <PageHead level={2} title="Changes"
        help="Addenda, Q&A answers and change requests are read like the RFP and compared with the frozen baseline. A person confirms each change; applying creates new requirement versions and returns the affected answers to the units." />
      {data.baseline ? <p>Current baseline <strong>{data.baseline.number}</strong>: {data.baseline.count} requirements.</p>
        : <p className="warn">The requirements must be frozen first: freeze the baseline on the <Link href={`/opportunities/${id}/requirements`}>Requirements</Link> page, then read change documents against it.</p>}
      {message && <div className="card warn" role="alert"><p>{message}</p></div>}
      {data.baseline && (
        <form className="card form" onSubmit={upload} aria-busy={!!busy}>
          <label>Change document (PDF) <input type="file" name="file" accept=".pdf,application/pdf" required disabled={inReview || !!busy} /></label>
          <button disabled={!!busy || inReview}>Read the change document</button>
          <span className="muted" role="status">{busy || (inReview ? "Apply or discard the change set in review first." : "An addendum, Q&A answers or a change request.")}</span>
        </form>)}
      {data.sets.length === 0 ? <p className="muted">No change documents read yet.</p>
        : data.sets.map((s) => <ChangeSetCard key={s.id} set={s} oppId={id} threshold={data.drastic_threshold} onChanged={reload} />)}
    </>
  );
}
