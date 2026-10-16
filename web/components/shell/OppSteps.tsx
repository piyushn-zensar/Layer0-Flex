"use client";
// Bid header: breadcrumb, title, status and the workflow stepper.  Owner: Janvia.
// A page that changes the status (freeze, go/no-go, dispatch, apply/discard a change set) refreshes this header at once with
//   window.dispatchEvent(new Event("opp-status-changed"))
// right after its own reload(); otherwise the header catches up on the next poll (5 s).
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useEffect } from "react";
import { useApi } from "@/lib/api";
import type { Opportunity } from "@/lib/types";
import StatusBadge from "@/components/ui/StatusBadge";

// Workflow order: RFP, Requirements, Traceability, Bid decision, Compliance matrix (Changes is a separate link).
// A step is ticked once the bid status has moved past it. `tour` is the walkthrough's data-tour id.
// The /decisions page holds the evidence, participation, go/no-go and dispatch, so it is the one "Bid decision" step. When the
// separate Assessment page lands (A-16, route /assessment), add an "Assessment" step before it (technical-architecture 16.2).
const STEPS = [
  { suffix: "", label: "RFP", doneFrom: "reading", tour: "step-rfp" },
  { suffix: "/requirements", label: "Requirements", doneFrom: "frozen", tour: "step-requirements" },
  { suffix: "/trace", label: "Traceability", doneFrom: "go", tour: "step-trace" },
  { suffix: "/decisions", label: "Bid decision", doneFrom: "go", tour: "step-decisions" },
  { suffix: "/consolidation", label: "Compliance matrix", doneFrom: "submitted", tour: "step-consolidation" },
];
const ORDER = ["new", "reading", "review", "frozen", "go", "no_go", "dispatched", "consolidating", "submitted"];
const rank = (s: string) => (s === "no_go" ? ORDER.indexOf("go") : ORDER.indexOf(s));

export const STATUS_EVENT = "opp-status-changed";

export default function OppSteps() {
  const { id } = useParams<{ id: string }>();
  const path = usePathname();
  const { data, reload } = useApi<{ opportunity: Opportunity }>(`/api/bids/${id}`);
  // Status changes when a page acts (freeze, go, dispatch): refresh on every step change, on the page's event, and every few seconds.
  useEffect(() => { reload(); }, [path, reload]);
  useEffect(() => { const t = setInterval(reload, 5000); return () => clearInterval(t); }, [reload]);
  useEffect(() => {
    const h = () => reload();
    window.addEventListener(STATUS_EVENT, h);
    return () => window.removeEventListener(STATUS_EVENT, h);
  }, [reload]);
  const base = `/opportunities/${id}`;
  const status = data?.opportunity.status ?? "new";
  const onChanges = path === base + "/changes";
  const onActivity = path === base + "/consolidation/activity"; // J-13: a side page of the matrix, not the matrix step itself

  return (
    <div className="opp-head" data-tour="opp-head">
      <div className="opp-title">
        <nav className="crumbs" aria-label="Breadcrumb"><Link href="/portfolio">Bids</Link><span aria-hidden>›</span><span className="mono">{id}</span></nav>
        <h1>{data?.opportunity.title ?? id} {data && <span data-tour="opp-status"><StatusBadge status={status} kind="opp" className="opp-status lg" label={status.replace("_", "-")} /></span>}</h1>
      </div>
      <nav aria-label="Workflow steps">
        <ol className="stepper" data-tour="stepper">
          {STEPS.map((s, i) => {
            const current = !(s.suffix === "/consolidation" && onActivity) && (path === base + s.suffix || (s.suffix !== "" && path.startsWith(base + s.suffix + "/"))); // sub-pages too
            const done = rank(status) >= rank(s.doneFrom);
            return (
              <li key={s.label} className={`${current ? "current" : ""} ${done ? "done" : ""}`} data-tour={s.tour}>
                <Link href={base + s.suffix} aria-current={current ? "step" : undefined} title={done ? `${s.label}: done` : undefined}>
                  <span className="step-no" aria-hidden>{done ? "✓" : i + 1}</span>{s.label}{done && <span className="sr-only"> (done)</span>}
                </Link>
              </li>
            );
          })}
        </ol>
        <div className="step-side">
        <Link className={`step-later ${onChanges ? "current" : ""}`} href={`${base}/changes`} aria-current={onChanges ? "page" : undefined} data-tour="step-changes">
          <span className="step-no" aria-hidden>Δ</span>Changes
        </Link>
        <Link className={`step-later ${onActivity ? "current" : ""}`} href={`${base}/consolidation/activity`} aria-current={onActivity ? "page" : undefined} data-tour="step-activity">
          <span className="step-no" aria-hidden>≡</span>Activity
        </Link>
        </div>
      </nav>
    </div>
  );
}
