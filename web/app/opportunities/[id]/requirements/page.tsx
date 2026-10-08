"use client";
// Requirement review: approve / reject line items, then freeze the baseline.  Owner: Piyush.
import { useParams } from "next/navigation";
import { post, useApi } from "@/lib/api";
import type { Baseline, Requirement } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";

export default function RequirementsPage() {
  const { id } = useParams<{ id: string }>();
  const { data, reload } = useApi<{ requirements: Requirement[]; baseline: Baseline | null }>(`/api/opportunities/${id}/requirements`);
  const review = (reqId: string, action: string) => post(`/api/requirements/${reqId}/review`, { action }).then(reload, alert);
  const freeze = () => post(`/api/opportunities/${id}/baselines`).then(reload, alert);
  const b = data?.baseline;

  return (
    <>
      <PageHead level={2} title="Requirements" />
      <p className="page-help">{b ? `Baseline ${b.number} frozen by ${b.frozen_by} (${b.count} items). Later changes run as a delta.`
        : "Draft. Approve or reject each line item against its source, then freeze."}</p>
      <table>
        <thead><tr><th>ID</th><th>Source</th><th>Category</th><th>Requirement</th><th>Status</th><th /></tr></thead>
        <tbody>
          {data?.requirements.map((r) => (
            <tr key={r.req_id} className={r.status}>
              <td className="mono">{r.req_id}</td>
              <td>{r.source}{r.provenance === "UNANCHORED" && <div className="warn">UNANCHORED</div>}</td>
              <td>{r.category}</td>
              <td>{r.text}<div className="quote">“{r.quote}”</div></td>
              <td><span className="badge">{r.status}</span></td>
              <td>{r.baseline === null && <span className="inline">
                <button onClick={() => review(r.req_id, "approve")}>Approve</button>
                <button className="secondary" onClick={() => review(r.req_id, "reject")}>Reject</button>
              </span>}</td>
            </tr>
          ))}
          {data?.requirements.length === 0 && <tr><td colSpan={6} className="muted">No requirements yet. Upload the RFP and run the reader agent.</td></tr>}
        </tbody>
      </table>
      {data && !b && <p><button onClick={freeze}>Freeze approved requirements as baseline</button></p>}
    </>
  );
}
