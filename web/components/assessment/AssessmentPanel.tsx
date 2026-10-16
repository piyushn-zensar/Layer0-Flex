"use client";
// "Assessment" executive summary on the Assessment step (P-38, C-23): four measures of how well the bid fits (domain alignment,
// product-evidence coverage, specialist-review progress, preliminary feasibility), the evidence gaps behind them, and the run they
// come from. A preliminary assessment, never a probability. Reassessing is the bid manager's.  Owner: Atharv.
import Link from "next/link";
import { useState } from "react";
import { BID_MANAGER_ONLY, errorMessage, isBidManager, post, useApi, useMe } from "@/lib/api";
import type { AssessmentMeasure, AssessmentScore } from "@/lib/types";
import { Alert, Busy, Skeleton, useToast } from "@/components/ui";

const day = (iso?: string | null) => (iso ? iso.slice(0, 10) : "");
const share = (m: AssessmentMeasure) => (m.n === null || m.of <= 0 ? "" : `${Math.round((m.n / m.of) * 100)}% of ${m.of}`);

function ReqLinks({ oppId, ids, summary }: { oppId: string; ids: string[]; summary: string }) {
  return (
    <details>
      <summary>{summary}</summary>
      <p className="row">{ids.map((r) => <Link key={r} className="mono" href={`/opportunities/${oppId}/trace#${r}`}>{r}</Link>)}</p>
    </details>
  );
}

function Tile({ oppId, m }: { oppId: string; m: AssessmentMeasure }) {
  const ids = m.req_ids ?? [];
  return (
    <div className="card" style={{ flex: "1 1 220px", margin: 0, minWidth: 0 }}>
      <h3 style={{ marginTop: 0 }}>{m.label}</h3>
      {m.n === null
        ? <p style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>Not assessed yet</p>
        : <p style={{ fontSize: "2rem", fontWeight: 700, margin: 0 }}>{m.n} of {m.of}</p>}
      <p className="muted" style={{ margin: 0 }}>{share(m) || " "}</p>
      <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>{m.explain}</p>
      {ids.length > 0 && <ReqLinks oppId={oppId} ids={ids} summary={`Requirements (${ids.length})`} />}
      {m.formula && <details><summary>How this is computed</summary><p className="muted">{m.formula}</p></details>}
    </div>
  );
}

export default function AssessmentPanel({ oppId }: { oppId: string }) {
  const toast = useToast();
  const bm = isBidManager(useMe());
  const { data, error, reload } = useApi<AssessmentScore>(`/api/bids/${oppId}/assessment-score`);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string>();
  if (error) return <section className="card"><Alert kind="error" title="Could not load the assessment.">{error}</Alert></section>;
  if (!data) return <section className="card"><Skeleton lines={3} /></section>;

  const reassess = (form: FormData) => {
    const reason = String(form.get("reason") ?? "").trim();
    if (!reason) { setFormError("Give a short reason."); return; }
    setBusy(true); setFormError(undefined);
    post(`/api/bids/${oppId}/reassessments`, { reason })
      .then(() => { toast.success("Assessment run recorded."); return reload(); },
        (e) => { setFormError(errorMessage(e)); toast.error(errorMessage(e)); })
      .finally(() => setBusy(false));
  };
  const hasRun = data.run !== null;
  const m = data.measures;

  return (
    <section className="card" data-tour="asm-score">
      <div className="card-head"><h2>Assessment</h2></div>
      <p className="muted">{data.note}</p>

      <div className="row" style={{ alignItems: "stretch" }}>
        {[m.domain_alignment, m.product_evidence, m.review_progress, m.preliminary_feasibility].map((x) => <Tile key={x.label} oppId={oppId} m={x} />)}
      </div>

      <h3>Evidence gaps</h3>
      {data.gaps.length === 0 ? <p className="muted">No evidence gaps</p> : (
        <ul className="per-req">{data.gaps.map((g) => (
          <li key={g.kind}>
            {g.req_ids.length > 0
              ? <ReqLinks oppId={oppId} ids={g.req_ids} summary={`${g.label}: ${g.req_ids.length}`} />
              : <>{g.label}: 0</>}
          </li>))}
        </ul>)}

      <p className="muted" data-tour="asm-score-run">{hasRun
        ? `Assessment run ${data.run}, ${day(data.run_at)}; catalog version ${data.catalog_version ?? "none"}`
        : "No assessment run yet"}</p>
      <form className="form" action={reassess}>
        <div className="row">
          <label><span className="sr-only">Reason for the assessment</span>
            <input name="reason" required placeholder={hasRun ? "Why reassess?" : "Why assess now?"} disabled={!bm || busy} /></label>
          <button className={hasRun ? "secondary sm" : "sm"} disabled={!bm || busy} title={bm ? undefined : BID_MANAGER_ONLY}>
            {hasRun ? "Reassess" : "Assess with the knowledge base"}</button>
          {busy && <Busy label="Assessing…" />}
          {!bm && <span className="muted">{BID_MANAGER_ONLY}</span>}
        </div>
      </form>
      <Alert kind="error">{formError}</Alert>
    </section>
  );
}
