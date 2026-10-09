"use client";
// Coverage check and compliance matrix.  Owner: Janvia.
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useApi } from "@/lib/api";
import type { Assignment, Requirement } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";

type Row = { requirement: Requirement; assignments: Assignment[]; state: string };
type Coverage = { rows: Row[]; total: number; answered: number; blocking: string[] };

// Why a requirement is not answered yet, in the order the groups are shown.
const REASONS = [
  { key: "validation", label: "Waiting for validation" },
  { key: "unit", label: "Waiting for the unit" },
  { key: "returned", label: "Returned" },
  { key: "unassigned", label: "Not assigned" },
] as const;
type Reason = (typeof REASONS)[number]["key"];

// Derived from the row, so the backend contract is unchanged. A returned response outranks an unanswered one, which outranks a submitted one.
function reasonOf({ state, assignments }: Row): Reason | null {
  if (state === "answered") return null;
  if (assignments.length === 0) return "unassigned";
  const status = assignments.map((a) => a.status);
  if (status.includes("returned")) return "returned";
  if (status.includes("assigned")) return "unit";
  return "validation";
}

const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "unknown";
const SHOWN = 10; // links shown per group before "more"

export default function ConsolidationPage() {
  const { id } = useParams<{ id: string }>();
  const { data: cov, error } = useApi<Coverage>(`/api/opportunities/${id}/consolidation`);
  const [onlyOpen, setOnlyOpen] = useState(false);
  if (error) return <p className="warn">{error}</p>;
  if (!cov) return <p>Loading…</p>;

  const open = cov.rows.filter((r) => reasonOf(r));
  const groups = REASONS.map((g) => ({ ...g, ids: open.filter((r) => reasonOf(r) === g.key).map((r) => r.requirement.req_id) })).filter((g) => g.ids.length);
  const reasonLabel = (r: Row) => REASONS.find((g) => g.key === reasonOf(r))?.label;
  const traceHref = (reqId: string) => `/opportunities/${id}/trace#${reqId}`;
  const link = (reqId: string) => <Link key={reqId} className="mono" href={traceHref(reqId)} title="Open in Traceability">{reqId}</Link>;

  return (
    <>
      <PageHead level={2} title="Final response" help="Every requirement must be answered by its business unit and validated before the response is complete." />
      <p><strong>{cov.answered} / {cov.total}</strong> requirements answered.{" "}
        {cov.blocking.length ? <span className="warn">{cov.blocking.length} still need an answer.</span> : <span className="ok">Every requirement is answered.</span>}{" "}
        <a className="button" href={`/api/opportunities/${id}/compliance-matrix.csv`}>Download compliance matrix (CSV)</a></p>

      {groups.length > 0 && (
        <section className="cons-blockers" aria-label="Requirements that still need an answer">
          <h3>Needs an answer</h3>
          {groups.map((g) => (
            <div key={g.key} className="cons-group">
              <span className="cons-group-label">{g.label} <span>({g.ids.length})</span></span>
              <span className="cons-ids">
                {g.ids.slice(0, SHOWN).map(link)}
                {g.ids.length > SHOWN && <details className="cons-more"><summary>{g.ids.length - SHOWN} more</summary><span className="cons-ids">{g.ids.slice(SHOWN).map(link)}</span></details>}
              </span>
            </div>
          ))}
        </section>
      )}

      <div className="filters">
        <button type="button" className={`chip${onlyOpen ? "" : " on"}`} aria-pressed={!onlyOpen} onClick={() => setOnlyOpen(false)}>All <span>{cov.total}</span></button>
        <button type="button" className={`chip${onlyOpen ? " on" : ""}`} aria-pressed={onlyOpen} onClick={() => setOnlyOpen(true)}>Open <span>{open.length}</span></button>
      </div>

      <table>
        <thead><tr><th>ID</th><th>Requirement</th><th>Units and responses</th><th>State</th></tr></thead>
        <tbody>
          {cov.rows.filter((r) => !onlyOpen || reasonOf(r)).map((row) => {
            const { requirement: r, assignments, state } = row;
            return (
              <tr key={r.req_id} className={reasonOf(row) ? "blocking" : ""}>
                <td className="mono"><Link href={traceHref(r.req_id)} title="Open in Traceability">{r.req_id}</Link><div className="muted">{r.source}</div></td>
                <td>{r.text}</td>
                <td>{assignments.map((a) => <div key={a.id}><strong>{a.bu}</strong> {a.compliance ?? "—"}{a.product_ref ? ` · ${a.product_ref}` : ""} <span className={`badge cons-status cons-status-${slug(a.status)}`}>{a.status}</span></div>)}
                  {assignments.length === 0 && <span className="muted">not assigned</span>}</td>
                <td><span className={`badge cons-state cons-state-${slug(state)}`}>{state.replace(/_/g, " ")}</span>
                  {reasonLabel(row) && <div className="muted">{reasonLabel(row)}</div>}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </>
  );
}
