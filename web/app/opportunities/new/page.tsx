"use client";
// New bid.  Owner: Piyush.
import { useRouter } from "next/navigation";
import { useState } from "react";
import { errorMessage, isBidManager, post, useMe } from "@/lib/api";
import type { Opportunity } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { Alert, Busy } from "@/components/ui";

const CUSTOMER_TYPES = ["utility", "hyperscaler", "neocloud", "colocation", "silicon provider", "public sector"];

export default function NewOpportunityPage() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string>();
  const me = useMe();
  const bm = isBidManager(me); // creating a bid is the bid manager's (section 16.6); the API checks too
  // QA-02: a blank or whitespace-only title is caught here and a failed request shows its message instead of the route error page.
  async function create(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const title = String(form.get("title") ?? "").trim();
    if (!title) { setMessage("A title is required."); return; }
    setBusy(true); setMessage(undefined);
    try {
      const opp = await post<Opportunity>("/api/bids", { ...Object.fromEntries(form), title });
      router.push(`/opportunities/${opp.id}`);
    } catch (err) { setMessage(errorMessage(err)); setBusy(false); }
  }
  return (
    <div className="content">
      <PageHead title="New bid" help="One bid per RFP. Upload the RFP on the next page." />
      <form className="card form" onSubmit={create} aria-busy={busy} data-tour="intake-form">
        <label data-tour="intake-title">Title <input name="title" required placeholder="e.g. Syracuse switchgear procurement" aria-invalid={message === "A title is required." ? true : undefined} disabled={busy} /></label>
        <label data-tour="intake-customer">Customer <input name="customer" placeholder="optional" disabled={busy} /></label>
        <label data-tour="intake-customer-type">Customer type
          <select name="customer_type" disabled={busy}><option value="">—</option>{CUSTOMER_TYPES.map((t) => <option key={t}>{t}</option>)}</select>
        </label>
        <button disabled={busy || !bm} data-tour="intake-create">Create</button>
        {busy && <Busy label="Creating…" />}
      </form>
      {me && !bm && <Alert kind="info">Only the bid manager creates bids; you are signed in as {me.name}.</Alert>}
      <Alert kind="error">{message}</Alert>
    </div>
  );
}
