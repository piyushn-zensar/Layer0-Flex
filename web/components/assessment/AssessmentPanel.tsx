"use client";
// "Assessment Summary" on the Assessment Summary step (P-38, P-43; C-36, C-38, C-39): three separate measures, the first two over the
// technical requirements only (technical requirement match, reviewed by design engineers), the third over every requirement sent to
// the units (specialist review progress); the standards items
// listed beside them, the evidence gaps, and the run they come from. Never a probability. Reassessing is the bid manager's.  Owner: Atharv.
import Link from "next/link";
import { useState } from "react";
import { BID_MANAGER_ONLY, errorMessage, isBidManager, post, useApi, useMe } from "@/lib/api";
import { formatDate, type AssessmentMeasure, type AssessmentScore } from "@/lib/types";
import { Alert, Busy, Skeleton, useToast } from "@/components/ui";


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
      {m.corrected !== undefined && <p className="muted" style={{ margin: 0 }}>{m.confirmed} confirmed as proposed, {m.other_solution} with another
        solution named, {m.not_compliant_answer} answered other than Compliant (a requirement can be in both of the last two groups)</p>}
      <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>{m.explain}</p>
      {ids.length > 0 && <ReqLinks oppId={oppId} ids={ids} summary={`Requirements (${ids.length})`} />}
    </div>
  );
}

// decided: the go/no-go is recorded; without a knowledge-base run the empty state and its button are no longer offered
export default function AssessmentPanel({ oppId, decided = false }: { oppId: string; decided?: boolean }) {
  const toast = useToast();
  const bm = isBidManager(useMe());
  const { data, error, reload } = useApi<AssessmentScore>(`/api/bids/${oppId}/assessment-score`);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string>();
  if (error) return <section className="card"><Alert kind="error" title="Could not load the Assessment Summary.">{error}</Alert></section>;
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
      <div className="card-head"><h2>Three measures</h2></div>
      <p className="muted">{data.note}</p>

      <div className="row" style={{ alignItems: "stretch" }}>
        {[m.technical_match, m.engineer_reviewed, m.review_progress].map((x) => <Tile key={x.label} oppId={oppId} m={x} />)}
      </div>
      {data.standards.req_ids.length > 0 && <div className="muted">
        <ReqLinks oppId={oppId} ids={data.standards.req_ids} summary={`${data.standards.label}: ${data.standards.req_ids.length}`} /></div>}

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
        ? `Knowledge-base assessment ${data.run}, ${formatDate(data.run_at, true)}; catalog version ${data.catalog_version ?? "none"}`
        : decided ? "No knowledge-base assessment was run: the bid was decided on the units' reviewed answers." : "No knowledge-base assessment run yet"}</p>
      {(hasRun || !decided) && <form className="form" action={reassess}>
        <div className="row">
          <label><span className="sr-only">Reason for the assessment</span>
            <input name="reason" required placeholder={hasRun ? "Why reassess?" : "Why assess now?"} disabled={!bm || busy} /></label>
          <button className={hasRun ? "secondary sm" : "sm"} disabled={!bm || busy} title={bm ? undefined : BID_MANAGER_ONLY}>
            {hasRun ? "Reassess" : "Assess with the knowledge base"}</button>
          {busy && <Busy label="Assessing…" />}
          {!bm && <span className="muted">{BID_MANAGER_ONLY}</span>}
        </div>
      </form>}
      <Alert kind="error">{formError}</Alert>
    </section>
  );
}
