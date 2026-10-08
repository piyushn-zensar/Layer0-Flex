"use client";
// Coverage check and compliance matrix.  Owner: Janvia.
import Link from "next/link";
import { useParams } from "next/navigation";
import { useApi } from "@/lib/api";
import type { Assignment, Requirement } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";

type Row = { requirement: Requirement; assignments: Assignment[]; state: string };
type Coverage = { rows: Row[]; total: number; answered: number; blocking: string[] };

export default function ConsolidationPage() {
  const { id } = useParams<{ id: string }>();
  const { data: cov } = useApi<Coverage>(`/api/opportunities/${id}/consolidation`);
  if (!cov) return <p>Loading…</p>;
  return (
    <>
      <PageHead level={2} title="Final response" help="Every requirement must be answered by its business unit and validated before the response is complete." />
      <p><strong>{cov.answered} / {cov.total}</strong> requirements answered.{" "}
        {cov.blocking.length ? <span className="warn">{cov.blocking.length} still need an answer.</span> : <span className="ok">Every requirement is answered.</span>}{" "}
        <a className="button" href={`/api/opportunities/${id}/compliance-matrix.csv`}>Download compliance matrix (CSV)</a></p>
      <table>
        <thead><tr><th>ID</th><th>Requirement</th><th>Units and responses</th><th>State</th></tr></thead>
        <tbody>
          {cov.rows.map(({ requirement: r, assignments, state }) => (
            <tr key={r.req_id}>
              <td className="mono"><Link href={`/opportunities/${id}/trace#${r.req_id}`}>{r.req_id}</Link><div className="muted">{r.source}</div></td>
              <td>{r.text}</td>
              <td>{assignments.map((a) => <div key={a.id}><strong>{a.bu}</strong> {a.compliance ?? "—"} · {a.product_ref} <span className="badge">{a.status}</span></div>)}
                {assignments.length === 0 && <span className="muted">not assigned</span>}</td>
              <td><span className="badge">{state}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
