"use client";
// Portfolio: every opportunity with unit progress.  Owner: Janvia.
import Link from "next/link";
import { useApi } from "@/lib/api";
import type { Opportunity, Progress } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { Alert, EmptyState, Skeleton, StatusBadge } from "@/components/ui";

type Item = { opp: Opportunity; requirements: number; progress: Progress };

// One line per unit: link to its work package, the count, and a two-segment bar (validated, then awaiting validation).
function UnitProgress({ progress }: { progress: Progress }) {
  const units = Object.entries(progress);
  if (units.length === 0) return <span className="muted">not dispatched</span>;
  return (
    <div className="unit-progress">
      {units.map(([bu, p]) => {
        const waiting = p.submitted - p.validated; // "submitted" already includes the validated ones
        const note = `${p.validated} validated, ${waiting} awaiting validation, ${p.total - p.submitted} not answered`;
        const pct = (n: number) => `${p.total ? (n / p.total) * 100 : 0}%`; // widths are data, so inline
        return (
          <div key={bu} className="unit-row" title={note}>
            <Link href={`/inbox/${bu}`} aria-label={`${bu} work package: ${note}`}>{bu}</Link>
            <span className="unit-count">{p.validated}/{p.total} validated</span>
            <span className="unit-bar" aria-hidden="true">
              <span className="done" style={{ width: pct(p.validated) }} />
              <span className="wait" style={{ width: pct(waiting) }} />
            </span>
          </div>
        );
      })}
    </div>
  );
}

export default function PortfolioPage() {
  const { data, error } = useApi<Item[]>("/api/portfolio");
  return (
    <div className="content">
      <PageHead title="Opportunities" help="Every RFP in progress, with how far each business unit has answered.">
        <Link className="button" href="/opportunities/new">New opportunity</Link>
      </PageHead>
      <Alert kind="error">{error}</Alert>
      {!data && !error && <Skeleton lines={4} />}
      {data?.length === 0 && (
        <EmptyState title="No opportunities yet" hint={<>Create one, or run <span className="mono">python -m scripts.seed_demo</span> for the demo data.</>}>
          <Link className="button" href="/opportunities/new">New opportunity</Link>
        </EmptyState>)}
      {data && data.length > 0 && (
        <table className="portfolio">
          <thead><tr><th>ID</th><th>Title</th><th>Customer</th><th>Status</th><th className="num">Requirements</th><th>Unit responses (validated / total)</th><th scope="col" aria-label="Open" /></tr></thead>
          <tbody>
            {data.map(({ opp, requirements, progress }) => (
              <tr key={opp.id}>
                <td className="mono"><Link href={`/opportunities/${opp.id}`}>{opp.id}</Link></td>
                <td><Link href={`/opportunities/${opp.id}/trace`} className="portfolio-title">{opp.title}</Link></td>
                <td>{opp.customer || <span className="muted">not set</span>}</td>
                <td><StatusBadge status={opp.status} kind="opp" /></td><td className="num">{requirements}</td>
                <td><UnitProgress progress={progress} /></td>
                <td><Link className="button secondary sm" href={`/opportunities/${opp.id}/trace`} aria-label={`Open ${opp.id}`}>Open</Link></td>
              </tr>
            ))}
          </tbody>
        </table>)}
    </div>
  );
}
