"use client";
// Portfolio: every opportunity with unit progress.  Owner: Janvia.
import Link from "next/link";
import { useApi } from "@/lib/api";
import type { Opportunity, Progress } from "@/lib/types";

type Item = { opp: Opportunity; requirements: number; progress: Progress };

export default function PortfolioPage() {
  const { data, error } = useApi<Item[]>("/api/portfolio");
  return (
    <div className="content">
      <h1>Opportunities</h1>
      {error && <p className="warn">{error}</p>}
      <table>
        <thead><tr><th>ID</th><th>Title</th><th>Customer</th><th>Status</th><th>Requirements</th><th>Unit responses (validated / total)</th><th /></tr></thead>
        <tbody>
          {data?.map(({ opp, requirements, progress }) => (
            <tr key={opp.id}>
              <td className="mono">{opp.id}</td><td>{opp.title}</td><td>{opp.customer}</td>
              <td><span className="badge">{opp.status}</span></td><td>{requirements}</td>
              <td>{Object.entries(progress).map(([bu, p]) => <span key={bu} className="tag">{bu} {p.validated}/{p.total}</span>)}</td>
              <td><Link className="button" href={`/opportunities/${opp.id}/trace`}>Open</Link></td>
            </tr>
          ))}
          {data?.length === 0 && <tr><td colSpan={7} className="muted">No opportunities. Create one, or run <span className="mono">python -m scripts.seed_demo</span>.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
