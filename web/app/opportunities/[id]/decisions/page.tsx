"use client";
// Bid decision: the evidence pack and the go/no-go (participation and dispatch moved to the Assessment step, A-16).  Owner: Atharv.
import { useParams } from "next/navigation";
import { useState } from "react";
import { errorMessage, isBidManager, post, useApi, useMe } from "@/lib/api";
import { TERMS, categoryLabel, complianceLabel, oppStatusLabel, type Unit } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { STATUS_EVENT } from "@/components/shell/OppSteps"; // the header listens for it after go/no-go and dispatch
import { Alert, Busy, Skeleton, StatusBadge, offeringLabel, useConfirm, useToast } from "@/components/ui";
import SendToKnowledge from "@/components/knowledge/SendToKnowledge"; // A-11
import ScheduleCard from "@/components/schedule/ScheduleCard"; // P-44: the compliance position is approved here (C-41)

type Judgement = "met" | "not_met" | "unknown";
type Decision = { id: number; outcome: string; units: string[]; rationale: string; decided_by: string; criteria?: { id: string; status: Judgement; note: string }[] };
type Criterion = { id: string; name: string; question: string; status: Judgement; detail: string };
type Summary = {
  rows: { req_id: string; category: string; text: string; level: string; basis: string; units: string[] }[];
  by_category: Record<string, Record<"fully" | "partly" | "changes" | "not" | "bid_desk", number>>;
  assessment: { items: number; validated: number }; criteria: Criterion[]; advice: string;
  compliance: Record<Outcome, string[]>; // C-43: product requirements with validated answers, by their weakest answer
  needs_owner: { req_id: string; text: string; category: string; suggested: string[] }[]; // C-08: not dispatched
};
type Outcome = "met" | "partial" | "deviation" | "not_met";
const OUTCOMES: Outcome[] = ["met", "partial", "deviation", "not_met"];
const JUDGEMENT: Record<Judgement, string> = { met: "met", not_met: "not met", unknown: "not known" };
// How a requirement is satisfied (decisions.summary levels), in the compliance words of technical-architecture 16.2. bid_desk: a
// commercial or submission item without an answer yet (once answered it counts by its answer), so its column shows only while one is open.
const LEVEL: Record<string, string> = { fully: complianceLabel("met"), partly: complianceLabel("partial"), changes: complianceLabel("deviation"),
  not: complianceLabel("not_met"), bid_desk: "Bid desk item, not answered yet" };
type Level = "fully" | "partly" | "changes" | "not" | "bid_desk";

// Go/no-go summary (task A-12): how each requirement is satisfied, the criteria, and advice; the person judges each criterion.
function GoNoGoSummary({ s, oppId }: { s: Summary; oppId: string }) {
  const rows = Object.entries(s.by_category);
  const levels = (["fully", "partly", "changes", "not", "bid_desk"] as Level[]).filter((l) => l !== "bid_desk" || rows.some(([, n]) => n.bid_desk > 0));
  return (
    <>
      <div data-tour="dec-advice"><Alert kind="info"><strong>{s.advice}</strong></Alert></div>
      <div data-tour="dec-outcomes"><p>Reviewed compliance outcomes, per product requirement (technical and standards items with a validated
        answer, each counted once by its weakest answer; a capability gap (not offered) counts as non-compliant):</p>
        {OUTCOMES.map((k) => <details key={k}><summary>{s.compliance[k].length} {complianceLabel(k)}</summary>
          <p className="row">{s.compliance[k].map((r) => <a key={r} className="mono" href={`/opportunities/${oppId}/trace#${r}`}>{r}</a>)}</p></details>)}</div>
      <h3>How the requirements are satisfied <span className="muted">(per requirement, every category: {s.rows.length})</span></h3>
      <table className="dense stack-sm" data-tour="dec-by-category">
        <thead><tr><th>Category</th>{levels.map((l) => <th key={l} className="num">{LEVEL[l]}</th>)}</tr></thead>
        <tbody>{rows.map(([cat, n]) => (
          <tr key={cat}><td><a href={`/opportunities/${oppId}/trace?category=${encodeURIComponent(cat)}`}><strong>{categoryLabel(cat)}</strong></a></td>
            {levels.map((l) => <td key={l} className="num" data-label={LEVEL[l]}>{n[l]}</td>)}</tr>))}</tbody>
      </table>
      <details data-tour="dec-per-req"><summary>Per requirement ({s.rows.length}): from the unit&apos;s answer where there is one, otherwise estimated from the match</summary>
        <ul className="per-req">{s.rows.map((r) => <li key={r.req_id}><a className="mono" href={`/opportunities/${oppId}/trace#${r.req_id}`}>{r.req_id}</a>{" "}
          <strong>{r.level === "not" && r.units.join() === "BID" ? TERMS.capability_gap : LEVEL[r.level] ?? r.level}</strong>{" "}
          <span className="muted">({r.basis}{r.units.length ? `: ${r.units.map((u) => (u === "BID" ? "bid desk" : u)).join(", ")}` : ""})</span> {r.text}</li>)}</ul>
      </details>
    </>
  );
}
type Layer = { n: number; name: string; in_scope: boolean; basis: string; terms: { term: string; count: number; req_ids: string[] }[] };
type Checks = {
  requirements_checked: number; scope: { in_scope: number[]; layers: Layer[] }; units_outside_scope: Record<string, string[]>;
  tier_flags: { req_id: string; bu: string; product_id: string; kind: string; note: string }[];
  rules: { id: string; rule: string; status: "pass" | "warn" | "fail" | "n/a"; note: string }[];
  solver: { status: string; reasons: string[]; warnings: string[]; working: { step: string; expression: string; result: number; unit: string; reference: string }[] };
};
type Evidence = {
  requirements: number; frozen: boolean; by_category: Record<string, number>; unanchored: string[];
  suggested_units: Record<string, number>; offering_mix: Record<string, number>; unmatched: string[]; not_reviewed: number;
  checks: Checks;
  deviations: { rows: { product_id: string; field: string; rfp: string; standard: string; severity: string; source: string }[];
    checked: number; products: string[]; note: string };
  workload: { rows: { bu: string; open_here: number; open_elsewhere: number; other_opportunities: string[]; total: number;
    capacity: number | null; over: boolean }[]; note: string };
};

// Bid and portfolio checks ported from v1.1 onto real data (task A-10): evidence, never a decision.
function PortfolioChecks({ ev }: { ev: Evidence }) {
  const d = ev.deviations, w = ev.workload;
  return (
    <section className="card" data-tour="dec-portfolio">
      <div className="card-head"><h2>Bid and portfolio checks</h2><span className="muted">Evidence for the bid manager, never a decision.</span></div>
      <h3>Deviations from the standard product</h3>
      {d.rows.length === 0 ? <p className="ok" data-tour="dec-deviations">{d.checked ? `${d.checked} data-sheet ratings are within the standard products.` : "No data-sheet rating to compare."}</p> : (
        <table className="dense" data-tour="dec-deviations"><thead><tr><th>Product</th><th>Rating</th><th>RFP asks</th><th>Standard</th><th>Severity</th><th>Source</th></tr></thead>
          <tbody>{d.rows.map((r, i) => (
            <tr key={i}><td className="mono">{r.product_id}</td><td>{r.field}</td><td>{r.rfp}</td><td>{r.standard}</td>
              <td><StatusBadge status={r.severity} kind="severity" /></td><td>{r.source}</td></tr>))}
          </tbody></table>)}
      <p className="muted">{d.note}</p>
      <h3>Workload across bids</h3>
      <table className="dense" data-tour="dec-workload"><thead><tr><th>Unit</th><th className="num">This bid</th><th>Other bids</th><th className="num">Total open</th><th>Capacity</th></tr></thead>
        <tbody>{w.rows.map((r) => (
          <tr key={r.bu}><td>{r.bu}</td><td className="num">{r.open_here}</td>
            <td>{r.open_elsewhere}{r.other_opportunities.length > 0 && <span className="muted"> ({r.other_opportunities.join(", ")})</span>}</td>
            <td className="num">{r.total}</td><td>{r.capacity ?? "—"} {r.over && <StatusBadge status="over" />}</td></tr>))}
        </tbody></table>
      <p className="muted">{w.note}</p>
    </section>
  );
}

// The engineering rules in plain sentences (engineering_rules.json keeps the original wording; shown when an id is not here)
const RULE: Record<string, string> = {
  "R-001": "When 800 VDC is specified, every product in the power path must be 800 VDC-compatible.",
  "R-002": "Racks of 100 kW or more need direct-to-chip liquid cooling, not air cooling alone.",
  "R-003": "2N redundancy at utility level needs a utility-grade protection unit (EP² or Crown), not Anord Mardix alone.",
  "R-004": "EPC Power is a pending acquisition: a design that relies on it carries a supply-timeline risk.",
};
type Judged = { id: string; status: Judgement; note: string }[] | undefined;
const judgedNote = (criteria: Judged, id: string) => criteria?.find((c) => c.id === id && c.status === "met")?.note;

// Engineering checks ported from v0.3.0 (task A-06): evidence for the bid manager, never a decision.
function EngineeringChecks({ c, oppId, judged }: { c: Checks; oppId: string; judged: Judged }) {
  const req = (id: string, i: number) => <span key={id}>{i > 0 && ", "}<a className="mono" href={`/opportunities/${oppId}/trace#${id}`}>{id}</a></span>;
  const scopeChecked = judgedNote(judged, "scope_fit");
  const outside = Object.entries(c.units_outside_scope);
  return (
    <section className="card" data-tour="dec-eng-checks">
      <div className="card-head"><h2>Engineering checks</h2>
        <span className="muted">Over {c.requirements_checked} requirements in the published register. Illustrative rules and capacities for the demo; to be confirmed with each unit.</span></div>
      <h3>Scope: layers this RFP covers</h3>
      <ul className="dec-layers" data-tour="dec-eng-scope">{c.scope.layers.map((l) => (
        <li key={l.n}><StatusBadge status={l.in_scope ? "pass" : "n/a"} label={l.in_scope ? "in scope" : "not in scope"} />
          {" "}{l.n}. {l.name} <span className="muted">({l.basis})</span>
          {l.terms.length > 0 && <div className="muted">{l.terms.map((t) => <span key={t.term}>“{t.term}” ×{t.count} in {t.req_ids.map(req)}; </span>)}</div>}
        </li>))}</ul>
      {outside.length > 0 && <div data-tour="dec-eng-outside"><Alert kind={scopeChecked ? "info" : "warn"}>Suggested although nothing in the RFP points to their layers: {outside.map(([bu, ids]) => `${bu} (${ids.length})`).join(", ")}.
        {scopeChecked ? <> Checked by the bid manager: {scopeChecked}</> : " Check these matches."}</Alert></div>}
      <h3>Rules</h3>
      <table className="dense dec-rules" data-tour="dec-eng-rules"><tbody>{c.rules.map((r) => (
        <tr key={r.id}><td><StatusBadge status={r.status} /></td>
          <td>{RULE[r.id] ?? r.rule}<div className="muted">{r.note}</div></td></tr>))}</tbody></table>
      <h3>Type of offer against each unit&apos;s usual type of offer</h3>
      {c.tier_flags.length === 0 ? <p className="muted" data-tour="dec-eng-tiers">No flags.</p> : (
        <details data-tour="dec-eng-tiers"><summary>{c.tier_flags.length} item(s) need an engineer&apos;s confirmation</summary>
          <ul className="per-req">{c.tier_flags.map((f, i) => <li key={i}>{req(f.req_id, 0)} {f.bu}: {f.note}</li>)}</ul></details>)}
      {c.solver.status !== "NOT_SOLVABLE" && <div data-tour="dec-eng-solver">
      <h3>Low-voltage solver</h3>
      <p><StatusBadge status={c.solver.status === "NOT_SOLVABLE" ? "n/a" : "pass"} label={c.solver.status.replace(/_/g, " ").toLowerCase()} /></p>
      {c.solver.reasons.length > 0 && <ul>{c.solver.reasons.map((r) => <li key={r} className="muted">{r}</li>)}</ul>}
      {c.solver.working.length > 0 && <table className="dense"><tbody>{c.solver.working.map((w) => (
        <tr key={w.step}><td>{w.step}</td><td className="mono">{w.expression} = {w.result} {w.unit}</td><td className="muted">{w.reference}</td></tr>))}</tbody></table>}
      {c.solver.warnings.map((w) => <p key={w} className="warn">{w}</p>)}
      </div>}
    </section>
  );
}
type Data = { evidence: Evidence; summary: Summary | null; units: Unit[]; participation: Decision | null; go_no_go: Decision | null };

export default function DecisionsPage() {
  const { id } = useParams<{ id: string }>();
  const toast = useToast();
  const [ask, confirmDialog] = useConfirm();
  const { data, error, reload } = useApi<Data>(`/api/bids/${id}/decisions`);
  const { data: sent, reload: reloadSent } = useApi<Record<string, string>>(`/api/bids/${id}/knowledge`); // A-11
  const [busy, setBusy] = useState<string>(); // what is running: one action at a time
  const [reopen, setReopen] = useState(false); // a recorded decision shows read-only until "Change decision"
  const bm = isBidManager(useMe()); // the bid manager makes the final go/no-go call (technical-architecture 16.5)
  if (error) return <Alert kind="error" title="Could not load the bid decision.">{error}</Alert>;
  if (!data) return <Skeleton lines={5} />;
  const { evidence: ev, go_no_go: go } = data;

  // one action at a time: a double click must not record two decisions
  const run = <T,>(label: string, request: Promise<T>, done: (r: T) => void = () => {}) => {
    setBusy(label);
    request.then((r) => { done(r); return reload(); }, (e) => toast.error(errorMessage(e))).finally(() => setBusy(undefined));
  };
  const statusChanged = () => window.dispatchEvent(new Event(STATUS_EVENT)); // header stepper and badge
  const decide = async (outcome: string, form: HTMLFormElement) => {
    const f = new FormData(form);
    const criteria = (data.summary?.criteria ?? []).map((c) => ({ id: c.id, status: f.get(`crit-${c.id}`), note: f.get(`note-${c.id}`) ?? "" }));
    if (outcome === "no_go" && !await ask({ title: "Record no-go?", confirmLabel: "Record no-go", danger: true,
      message: "The bid is marked no-go: dispatch stops and the units' open work is withdrawn (submitted and validated answers stay). A later go decision can still overrule it." })) return;
    run("decision", post<{ withdrawn: number }>(`/api/bids/${id}/go-no-go`, { outcome, rationale: f.get("rationale"), criteria }),
      (r) => { toast.success(outcome === "go" ? "Decision recorded: go." : `Decision recorded: no-go. ${r.withdrawn} open item(s) withdrawn from the units.`); setReopen(false); statusChanged(); });
  };

  return (
    <div className="decisions">
      <PageHead level={2} title="Bid decision" help="Go/no-go only: once the units have assessed the bid (Assessment Summary step), review the evidence and their answers; the bid manager decides go or no-go." />
      <section className="card" data-tour="dec-evidence">
        <div className="card-head"><h2>Evidence</h2>
          <span className="muted" data-tour="dec-evidence-counts">{ev.requirements} requirements · {Object.entries(ev.by_category).map(([k, v]) => `${categoryLabel(k)} ${v}`).join(", ")}</span></div>
        <p className="row" data-tour="dec-offering-mix">Types of offer: {Object.entries(ev.offering_mix).map(([k, v]) => <StatusBadge key={k} status={k} kind="offering" label={`${offeringLabel(k)} ${v}`} />)}</p>
        <p data-tour="dec-suggested-units">Suggested units: {Object.entries(ev.suggested_units).map(([k, v], i) => <span key={k}>{i > 0 && " · "}<strong>{k} ({v})</strong></span>)}
          {Object.keys(ev.suggested_units).length === 0 && "none yet: run matching"}</p>
        {ev.unanchored.length > 0 && <details className="dec-unanchored" data-tour="dec-unanchored"><summary className="warn">Source not verified: {ev.unanchored.length} requirement(s) without a place in the RFP</summary>
          <p className="muted mono">{ev.unanchored.join(", ")}</p></details>}
        {ev.unmatched.length > 0 && <p className="muted" data-tour="dec-unmatched">Not yet matched: {ev.unmatched.length}</p>}
        {ev.not_reviewed > 0 && <p className="muted" data-tour="dec-not-reviewed">Technical matches the units' designers / engineers have not confirmed yet: {ev.not_reviewed} (Traceability, pane 3)</p>}
        {!ev.frozen && <div data-tour="dec-not-frozen"><Alert kind="warn">The requirement register is not frozen yet: read the RFP on the RFP step (the register freezes when the read is complete) before deciding go or no-go.</Alert></div>}
      </section>

      {ev.frozen && <EngineeringChecks c={ev.checks} oppId={id} judged={go?.criteria} />}
      {ev.frozen && <PortfolioChecks ev={ev} />}

      <div data-tour="dec-assessment-link"><Alert kind="info">Participation, routing (the unit only) and sending the work are on the{" "}
        <a href={`/opportunities/${id}/assessment`}>Assessment Summary</a> step; decide here once the units have answered.</Alert></div>

      {ev.frozen && <ScheduleCard oppId={id} part="compliance" />}

      <section className="card" data-tour="dec-gonogo">
        <div className="card-head"><h2>Go / no-go</h2>
          {go && <span className="muted" data-tour="dec-gng-recorded">Decision <StatusBadge status={go.outcome} kind="opp" label={oppStatusLabel(go.outcome)} /> by <strong>{go.decided_by}</strong></span>}</div>
        {go && <p>{go.rationale}
          {go.criteria && go.criteria.length > 0 && <span className="muted"> Criteria judged: {(["met", "not_met", "unknown"] as Judgement[])
            .map((j) => `${go.criteria!.filter((c) => c.status === j).length} ${JUDGEMENT[j]}`).join(", ")}.</span>}
          {go.rationale && <> <SendToKnowledge kind="decision" refId={go.id} status={sent?.[`decision:${go.id}`]} onSent={reloadSent} /></>}</p>}
        {data.summary && data.summary.assessment.validated < data.summary.assessment.items && <div data-tour="dec-assessment-warning">
          <Alert kind="warn">Assessment incomplete: {data.summary.assessment.validated} of {data.summary.assessment.items} item(s) sent to the units have a validated answer. You can still record go or no-go.</Alert></div>}
        {data.summary && data.summary.assessment.items === 0 && <div data-tour="dec-assessment-warning">
          <Alert kind="warn">Nothing has been sent to the units yet: a decision now is made without their assessment.</Alert></div>}
        {data.summary && <GoNoGoSummary s={data.summary} oppId={id} />}
        {go && !reopen ? (
          <div data-tour="dec-criteria">
            <div className="table-scroll"><table className="dec-criteria stack-sm">
              <thead><tr><th>Criterion</th><th>Layer 0&apos;s assessment</th><th>Bid manager&apos;s judgement</th><th>Note</th></tr></thead>
              <tbody>{(data.summary?.criteria ?? []).map((c) => { const j = go.criteria?.find((x) => x.id === c.id); return (
                <tr key={c.id}>
                  <td><strong>{c.name}</strong><div className="muted">{c.question}</div></td>
                  <td data-label="Layer 0's assessment"><StatusBadge status={c.status} kind="compliance" label={JUDGEMENT[c.status]} /><div className="muted">{c.detail}</div></td>
                  <td data-label="Bid manager's judgement">{j ? <StatusBadge status={j.status} kind="compliance" label={j.status === c.status ? JUDGEMENT[j.status] : `${JUDGEMENT[j.status]} (judged by the bid manager)`} />
                    : <span className="muted">not recorded</span>}</td>
                  <td data-label="Note">{j?.note && j.note !== c.detail ? j.note : <span className="muted">as assessed</span>}</td>
                </tr>); })}</tbody>
            </table></div>
            {bm && <div className="row"><button type="button" className="secondary" onClick={() => setReopen(true)} data-tour="dec-change">Change decision</button></div>}
          </div>
        ) : (
        <form className="form compact" onSubmit={(e) => e.preventDefault()}>
          {data.summary && <div className="table-scroll" data-tour="dec-criteria"><table className="dec-criteria stack-sm">
            <thead><tr><th>Criterion</th><th>Layer 0&apos;s assessment</th><th>Your judgement</th><th>Note</th></tr></thead>
            <tbody>{data.summary.criteria.map((c) => (
              <tr key={c.id}>
                <td><strong>{c.name}</strong><div className="muted">{c.question}</div></td>
                <td data-label="Layer 0's assessment"><StatusBadge status={c.status} kind="compliance" label={JUDGEMENT[c.status]} />
                  <div className="muted">{c.detail}</div></td>
                <td data-label="Your judgement"><label><span className="sr-only">Your judgement on {c.name}</span>
                  <select name={`crit-${c.id}`} defaultValue={go?.criteria?.find((x) => x.id === c.id)?.status ?? c.status}>
                    {(Object.keys(JUDGEMENT) as Judgement[]).map((j) => <option key={j} value={j}>{JUDGEMENT[j]}</option>)}</select></label></td>
                <td data-label="Note"><label><span className="sr-only">Note on {c.name}</span><input name={`note-${c.id}`} placeholder="optional" defaultValue={go?.criteria?.find((x) => x.id === c.id)?.note ?? ""} /></label></td>
              </tr>))}</tbody>
          </table></div>}
          <label data-tour="dec-gng-rationale">Rationale <input name="rationale" defaultValue={go?.rationale ?? ""} /></label>
          <div className="row">
            <button type="button" disabled={!ev.frozen || !!busy || !bm} onClick={(e) => decide("go", e.currentTarget.form!)} data-tour="dec-go">Go</button>
            <button type="button" disabled={!ev.frozen || !!busy || !bm} className="danger secondary" onClick={(e) => decide("no_go", e.currentTarget.form!)} data-tour="dec-no-go">No-go</button>
            {busy === "decision" && <Busy label="Recording…" />}
            {!ev.frozen && <span className="muted">Read the RFP first.</span>}
            {ev.frozen && !bm && <span className="muted">Only the bid manager records go or no-go.</span>}
            {go && <button type="button" className="secondary" disabled={!!busy} onClick={() => setReopen(false)}>Cancel</button>}
          </div>
        </form>)}
      </section>

      {confirmDialog}
    </div>
  );
}
