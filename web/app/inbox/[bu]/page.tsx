"use client";
// A business unit's work package: checklist response per requirement, then validation.  Owner: Atharv.
// The unit's product manager / design engineer answers (bid desk: the Bid Manager); only the Bid Manager validates.
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { currentActor, post, useApi } from "@/lib/api";
import type { Assignment, Requirement, Unit } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";

type Item = Assignment & { requirement: Requirement | null };
type Data = { bu: string; unit: Unit | null; compliance: string[]; items: Item[] };

const BID_MANAGER = "Bid Manager";

export default function InboxPage() {
  const { bu } = useParams<{ bu: string }>();
  const { data, error, reload } = useApi<Data>(`/api/inbox/${bu}`);
  const [busy, setBusy] = useState<number>();  // the assignment being saved: no double submit
  if (error) return <p className="content warn">Could not load this work package: {error}</p>;
  if (!data) return <p className="content">Loading…</p>;

  const me = currentActor();
  const canAnswer = data.unit ? [data.unit.product_manager, data.unit.design_engineer].includes(me) : me === BID_MANAGER;
  const canValidate = me === BID_MANAGER;
  const run = (a: Item, request: () => Promise<unknown>) => {
    setBusy(a.id);
    request().then(reload, alert).finally(() => setBusy(undefined));  // on failure the typed answer stays in the form
  };
  const respond = (a: Item, form: FormData) => run(a, () => post(`/api/assignments/${a.id}/respond`, Object.fromEntries(form)));
  const validate = (a: Item, ok: boolean) => run(a, () => post(`/api/assignments/${a.id}/validate`, { ok, note: "" }));

  return (
    <div className="content">
      <PageHead title={`My work: ${data.unit?.name ?? "Bid desk (bid manager)"}`} />
      <p className="page-help">Each line is a requirement assigned to this unit. Mark it met, partly met, not met or an exception,
        say what meets it, then submit. The bid manager validates.</p>
      {!canAnswer && !canValidate && <p className="muted">You are acting as {me}: you can read this work package but not answer it.</p>}
      <table>
        <thead><tr><th>Opportunity</th><th>Requirement</th><th>Response</th><th>Status</th></tr></thead>
        <tbody>
          {data.items.map((a) => (
            <tr key={a.id}>
              <td className="mono"><Link href={`/opportunities/${a.opportunity_id}/trace#${a.req_id}`}>{a.opportunity_id}<br />{a.req_id}</Link></td>
              <td>{a.requirement ? <>{a.requirement.text}<div className="quote">“{a.requirement.quote}” — {a.requirement.source}</div></>
                : <span className="warn">This requirement no longer exists in the opportunity.</span>}</td>
              <td>
                {canAnswer && (a.status === "assigned" || a.status === "returned") ? (
                  <form className="form compact" onSubmit={(e) => { e.preventDefault(); respond(a, new FormData(e.currentTarget)); }}>
                    <label><span className="sr-only">Compliance</span>
                      <select name="compliance" defaultValue={a.compliance ?? "met"}>{data.compliance.map((c) => <option key={c}>{c}</option>)}</select></label>
                    <label><span className="sr-only">Product or configuration</span>
                      <input name="product_ref" defaultValue={a.product_ref ?? ""} placeholder="Product / configuration" /></label>
                    <label><span className="sr-only">How it is met</span>
                      <textarea name="response" rows={2} defaultValue={a.response} placeholder="How it is met" /></label>
                    {a.validation_note && <div className="warn">Returned: {a.validation_note}</div>}
                    <button disabled={busy === a.id}>Submit</button>
                  </form>
                ) : (
                  <div>{a.compliance && <strong>{a.compliance}</strong>} {a.product_ref}
                    {a.response && <div className="muted">{a.response}</div>}
                    {!a.compliance && <span className="muted">not answered yet</span>}</div>
                )}
              </td>
              <td><span className="badge">{a.status}</span>{a.validated_by && <div className="muted">by {a.validated_by}</div>}
                {canValidate && a.status === "submitted" && <div className="inline">
                  <button disabled={busy === a.id} onClick={() => validate(a, true)}>Validate</button>
                  <button disabled={busy === a.id} className="secondary" onClick={() => validate(a, false)}>Return</button>
                </div>}
              </td>
            </tr>
          ))}
          {data.items.length === 0 && <tr><td colSpan={4} className="muted">Nothing assigned.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
