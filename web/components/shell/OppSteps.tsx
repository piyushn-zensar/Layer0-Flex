"use client";
// Opportunity header: breadcrumb, title, status and the workflow stepper.  Owner: Janvia.
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useEffect } from "react";
import { useApi } from "@/lib/api";
import type { Opportunity } from "@/lib/types";

// Workflow order. A step is ticked once the opportunity status has moved past it.
const STEPS = [
  { suffix: "", label: "RFP", doneFrom: "reading" },
  { suffix: "/requirements", label: "Requirements", doneFrom: "frozen" },
  { suffix: "/trace", label: "Traceability", doneFrom: "go" },
  { suffix: "/decisions", label: "Bid decision", doneFrom: "go" },
  { suffix: "/consolidation", label: "Final response", doneFrom: "submitted" },
];
const ORDER = ["new", "reading", "review", "frozen", "go", "no_go", "dispatched", "consolidating", "submitted"];
const rank = (s: string) => (s === "no_go" ? ORDER.indexOf("go") : ORDER.indexOf(s));

export default function OppSteps() {
  const { id } = useParams<{ id: string }>();
  const path = usePathname();
  const { data, reload } = useApi<{ opportunity: Opportunity }>(`/api/opportunities/${id}`);
  // Status changes when a page acts (freeze, go, dispatch): refresh on every step change and every few seconds.
  useEffect(() => { reload(); }, [path, reload]);
  useEffect(() => { const t = setInterval(reload, 5000); return () => clearInterval(t); }, [reload]);
  const base = `/opportunities/${id}`;
  const status = data?.opportunity.status ?? "new";

  return (
    <div className="opp-head">
      <div className="opp-title">
        <nav className="crumbs" aria-label="Breadcrumb"><Link href="/portfolio">Opportunities</Link> <span aria-hidden>›</span> {id}</nav>
        <h1>{data?.opportunity.title ?? id} {data && <span className="badge">{status.replace("_", "-")}</span>}</h1>
      </div>
      <nav aria-label="Workflow steps">
        <ol className="stepper">
          {STEPS.map((s, i) => {
            const current = path === base + s.suffix || (s.suffix !== "" && path.startsWith(base + s.suffix + "/")); // sub-pages too
            const done = rank(status) >= rank(s.doneFrom);
            return (
              <li key={s.label} className={`${current ? "current" : ""} ${done ? "done" : ""}`}>
                <Link href={base + s.suffix} aria-current={current ? "step" : undefined}>
                  <span className="step-no" aria-hidden>{done ? "✓" : i + 1}</span>{s.label}
                </Link>
              </li>
            );
          })}
        </ol>
        <Link className={`step-later ${path === base + "/changes" ? "current" : ""}`} href={`${base}/changes`}>Changes (planned)</Link>
      </nav>
    </div>
  );
}
