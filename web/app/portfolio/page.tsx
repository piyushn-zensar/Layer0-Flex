"use client";
// Portfolio: every opportunity with unit progress.  Owner: Janvia.
import Link from "next/link";
import { useApi } from "@/lib/api";
import type { Opportunity, Progress } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";

type Item = { opp: Opportunity; requirements: number; progress: Progress };

// Opportunity status -> chip class; the text shown is the stored status ("no_go" reads "no-go").
const statusClass = (s: string) => `opp-status-${s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "unknown"}`;

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
      <PageHead title="Opportunities" help="Every RFP in progress, with how far each business unit has answered." />
      {error && <p className="warn">{error}</p>}
      <table>
        <thead><tr><th>ID</th><th>Title</th><th>Customer</th><th>Status</th><th>Requirements</th><th>Unit responses (validated / total)</th><th /></tr></thead>
        <tbody>
          {data?.map(({ opp, requirements, progress }) => (
            <tr key={opp.id}>
              <td className="mono">{opp.id}</td><td>{opp.title}</td><td>{opp.customer}</td>
              <td><span className={`badge opp-status ${statusClass(opp.status)}`}>{opp.status.replace("_", "-")}</span></td><td>{requirements}</td>
              <td><UnitProgress progress={progress} /></td>
              <td><Link className="button" href={`/opportunities/${opp.id}/trace`}>Open</Link></td>
            </tr>
          ))}
          {data?.length === 0 && <tr><td colSpan={7} className="muted">No opportunities. Create one, or run <span className="mono">python -m scripts.seed_demo</span>.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
