"use client";
// Changes (P-11): read an addendum, Q&A answers or a change request against the frozen baseline; a person confirms each
// change, then the Bid Manager applies it.  Owner: Piyush.
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { BID_MANAGER_ONLY, errorMessage, isBidManager, post, useApi, useMe } from "@/lib/api";
import { DOC_TYPES, type Changes } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { STATUS_EVENT } from "@/components/shell/OppSteps";
import { Alert, Busy, EmptyState, Skeleton, useToast } from "@/components/ui";
import ChangeSetCard from "@/components/changes/ChangeSetCard";

const HELP = "Addenda, Q&A answers and change requests are read like the RFP and compared with the frozen requirements. A person confirms each change; applying creates new requirement versions and returns the affected answers to the units.";

export default function ChangesPage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, reload } = useApi<Changes>(`/api/bids/${id}/changes`);
  const bm = isBidManager(useMe()); // reading change documents is the bid manager's (section 16.6)
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState<string>();
  const toast = useToast();

  // onSubmit, not a form action: React holds state updates made inside an action until it ends, so the busy text and
  // the disabled button would only appear after the upload; a failed upload also keeps the chosen file.
  async function upload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const file = new FormData(form); // before the input is disabled below
    setBusy("Reading the change document…"); setMessage(undefined);
    try { await post(`/api/bids/${id}/changes`, file); form.reset(); await reload(); toast.success("Change document read. Confirm each change below."); }
    catch (err) { setMessage(errorMessage(err)); } finally { setBusy(""); }
  }
  // Apply or discard changes the baseline, so the header refreshes too.
  const changed = () => reload().then(() => window.dispatchEvent(new Event(STATUS_EVENT)));
  const head = <PageHead level={2} title="Changes" help={HELP} />;
  if (error) return <>{head}<Alert kind="error">{error}</Alert></>;
  if (!data) return <>{head}<Skeleton lines={4} /></>;
  const inReview = data.sets.some((s) => s.status === "review");

  return (
    <>
      {head}
      {data.baseline ? <p data-tour="chg-baseline">Current frozen version <strong>{data.baseline.number}</strong>: {data.baseline.count} requirements.</p>
        : <div data-tour="chg-no-baseline"><Alert kind="warn">The register is not frozen yet: it is frozen when the RFP has been read on the <Link href={`/opportunities/${id}`}>RFP</Link> step; change documents are read against it.</Alert></div>}
      {data.baseline && (
        <form className="card chg-upload" onSubmit={upload} aria-busy={!!busy} data-tour="chg-upload">
          <div className="card-head"><h3>Read a change document</h3><span className="muted">An addendum, Q&A answers or a change request, as a PDF.</span></div>
          <div className="form">
            <label htmlFor="chg-file">Change document (PDF)</label>
            <input id="chg-file" type="file" name="file" accept=".pdf,application/pdf" required disabled={inReview || !!busy} aria-describedby="chg-file-hint" data-tour="chg-file" />
            <label htmlFor="chg-role">Document type</label>
            <select id="chg-role" name="role" required defaultValue="" disabled={inReview || !!busy} data-tour="chg-role">
              <option value="" disabled>Choose a type…</option>
              {(["addendum", "qa", "change"] as const).map((v) => <option key={v} value={v}>{DOC_TYPES[v]}</option>)}
            </select>
            <button disabled={!!busy || inReview || !bm} title={bm ? "" : BID_MANAGER_ONLY} data-tour="chg-upload-button">Read the change document</button>
            {busy ? <Busy label={busy} /> : <span id="chg-file-hint" className="muted">{inReview ? "Apply or discard the change set in review first." : "Read against the current frozen version."}</span>}
          </div>
          <Alert kind="error" onClose={() => setMessage(undefined)}>{message}</Alert>
        </form>)}
      {data.sets.length === 0 ? (
        <div data-tour="chg-empty"><EmptyState title="No change documents read yet" hint={data.baseline ? "Read an addendum, Q&A answers or a change request above; each change statement is compared with the frozen requirements." : "Read the RFP first: its register is frozen when it is read."} /></div>
      ) : data.sets.map((s, i) => <ChangeSetCard key={s.id} set={s} oppId={id} threshold={data.drastic_threshold} onChanged={changed} tour={i === 0} />)}
    </>
  );
}
