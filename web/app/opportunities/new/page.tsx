"use client";
// New opportunity.  Owner: Piyush.
import { useRouter } from "next/navigation";
import { useState } from "react";
import { errorMessage, post } from "@/lib/api";
import type { Opportunity } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { Alert, Busy } from "@/components/ui";

const CUSTOMER_TYPES = ["utility", "hyperscaler", "neocloud", "colocation", "silicon provider", "public sector"];

export default function NewOpportunityPage() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string>();
  // QA-02: a blank or whitespace-only title is caught here and a failed request shows its message instead of the route error page.
  async function create(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const title = String(form.get("title") ?? "").trim();
    if (!title) { setMessage("A title is required."); return; }
    setBusy(true); setMessage(undefined);
    try {
      const opp = await post<Opportunity>("/api/opportunities", { ...Object.fromEntries(form), title });
      router.push(`/opportunities/${opp.id}`);
    } catch (err) { setMessage(errorMessage(err)); setBusy(false); }
  }
  return (
    <div className="content">
      <PageHead title="New opportunity" help="One opportunity per RFP. Upload the RFP on the next page." />
      <form className="card form" onSubmit={create} aria-busy={busy} data-tour="intake-form">
        <label data-tour="intake-title">Title <input name="title" required placeholder="e.g. Syracuse switchgear procurement" aria-invalid={message === "A title is required." ? true : undefined} disabled={busy} /></label>
        <label data-tour="intake-customer">Customer <input name="customer" placeholder="optional" disabled={busy} /></label>
        <label data-tour="intake-customer-type">Customer type
          <select name="customer_type" disabled={busy}><option value="">—</option>{CUSTOMER_TYPES.map((t) => <option key={t}>{t}</option>)}</select>
        </label>
        <button disabled={busy} data-tour="intake-create">Create</button>
        {busy && <Busy label="Creating…" />}
      </form>
      <Alert kind="error">{message}</Alert>
    </div>
  );
}
