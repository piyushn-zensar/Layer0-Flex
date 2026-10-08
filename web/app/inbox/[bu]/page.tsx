"use client";
// A business unit's work package: checklist response per requirement, then validation.  Owner: Atharv.
import Link from "next/link";
import { useParams } from "next/navigation";
import { post, useApi } from "@/lib/api";
import type { Assignment, Requirement, Unit } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";

type Item = Assignment & { requirement: Requirement };
type Data = { bu: string; unit: Unit | null; compliance: string[]; items: Item[] };

export default function InboxPage() {
  const { bu } = useParams<{ bu: string }>();
  const { data, reload } = useApi<Data>(`/api/inbox/${bu}`);
  if (!data) return <p className="content">Loading…</p>;

  const respond = (a: Item, form: FormData) =>
    post(`/api/assignments/${a.id}/respond`, Object.fromEntries(form)).then(reload, alert);
  const validate = (a: Item, ok: boolean) => post(`/api/assignments/${a.id}/validate`, { ok, note: "" }).then(reload, alert);

  return (
    <div className="content">
      <PageHead title={`My work: ${data.unit?.name ?? "Bid desk (bid manager)"}`} />
      <p className="page-help">Each line is a requirement assigned to this unit. Mark it met, partly met, not met or an exception,
        say what meets it, then submit. The bid manager validates.</p>
      <table>
        <thead><tr><th>Opportunity</th><th>Requirement</th><th>Response</th><th>Status</th></tr></thead>
        <tbody>
          {data.items.map((a) => (
            <tr key={a.id}>
              <td className="mono"><Link href={`/opportunities/${a.opportunity_id}/trace#${a.req_id}`}>{a.opportunity_id}<br />{a.req_id}</Link></td>
              <td>{a.requirement.text}<div className="quote">“{a.requirement.quote}” — {a.requirement.source}</div></td>
              <td>
                <form className="form compact" action={(f) => respond(a, f)}>
                  <select name="compliance" defaultValue={a.compliance ?? "met"}>{data.compliance.map((c) => <option key={c}>{c}</option>)}</select>
                  <input name="product_ref" defaultValue={a.product_ref ?? ""} placeholder="Product / configuration" />
                  <textarea name="response" rows={2} defaultValue={a.response} placeholder="How it is met" />
                  <button>Submit</button>
                </form>
              </td>
              <td><span className="badge">{a.status}</span>{a.validated_by && <div className="muted">by {a.validated_by}</div>}
                {a.status === "submitted" && <div className="inline">
                  <button onClick={() => validate(a, true)}>Validate</button>
                  <button className="secondary" onClick={() => validate(a, false)}>Return</button>
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
