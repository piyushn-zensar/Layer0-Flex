"use client";
// Evidence pack, participation, go/no-go and one-step dispatch.  Owner: Atharv.
import { useParams } from "next/navigation";
import { useState } from "react";
import { errorMessage, post, useApi } from "@/lib/api";
import type { Unit } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { STATUS_EVENT } from "@/components/shell/OppSteps"; // the header listens for it after go/no-go and dispatch
import { Alert, Busy, Skeleton, StatusBadge, offeringLabel, useConfirm, useToast } from "@/components/ui";
import SendToKnowledge from "@/components/knowledge/SendToKnowledge"; // A-11

type Judgement = "met" | "not_met" | "unknown";
type Decision = { id: number; outcome: string; units: string[]; rationale: string; decided_by: string; criteria?: { id: string; status: Judgement; note: string }[] };
type Criterion = { id: string; name: string; question: string; status: Judgement; detail: string };
type Summary = {
  rows: { req_id: string; category: string; text: string; level: string; basis: string; units: string[] }[];
  by_category: Record<string, Record<"fully" | "partly" | "not" | "bid_desk", number>>;
  coverage: number; criteria: Criterion[]; advice: string;
};
const JUDGEMENT: Record<Judgement, string> = { met: "met", not_met: "not met", unknown: "not known" };

// Go/no-go summary (task A-12): how each requirement is satisfied, the criteria, and advice; the person judges each criterion.
function GoNoGoSummary({ s, oppId }: { s: Summary; oppId: string }) {
  return (
    <>
      <Alert kind="info"><strong>{s.advice}</strong></Alert>
      <h3>How the requirements are satisfied</h3>
      <table className="dense">
        <thead><tr><th>Category</th><th className="num">Fully</th><th className="num">Partly</th><th className="num">Not</th><th className="num">Bid desk</th></tr></thead>
        <tbody>{Object.entries(s.by_category).map(([cat, n]) => (
          <tr key={cat}><td>{cat}</td><td className="num">{n.fully}</td><td className="num">{n.partly}</td><td className="num">{n.not}</td><td className="num">{n.bid_desk}</td></tr>))}</tbody>
      </table>
      <details><summary>Per requirement ({s.rows.length}): from the unit&apos;s answer where there is one, otherwise estimated from the match</summary>
        <ul className="per-req">{s.rows.map((r) => <li key={r.req_id}><a className="mono" href={`/opportunities/${oppId}/trace#${r.req_id}`}>{r.req_id}</a>{" "}
          <strong>{r.level.replace("_", " ")}</strong> <span className="muted">({r.basis}{r.units.length ? `: ${r.units.join(", ")}` : ""})</span> {r.text}</li>)}</ul>
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
    <section className="card">
      <div className="card-head"><h2>Bid and portfolio checks</h2><span className="muted">Evidence for the bid manager, never a decision.</span></div>
      <h3>Deviations from the standard product</h3>
      {d.rows.length === 0 ? <p className="ok">{d.checked ? `${d.checked} data-sheet ratings are within the standard products.` : "No data-sheet rating to compare."}</p> : (
        <table className="dense"><thead><tr><th>Product</th><th>Rating</th><th>RFP asks</th><th>Standard</th><th>Severity</th><th>Source</th></tr></thead>
          <tbody>{d.rows.map((r, i) => (
            <tr key={i}><td className="mono">{r.product_id}</td><td>{r.field}</td><td>{r.rfp}</td><td>{r.standard}</td>
              <td><StatusBadge status={r.severity} kind="severity" /></td><td>{r.source}</td></tr>))}
          </tbody></table>)}
      <p className="muted">{d.note}</p>
      <h3>Workload across opportunities</h3>
      <table className="dense"><thead><tr><th>Unit</th><th className="num">This opportunity</th><th>Other opportunities</th><th className="num">Total open</th><th>Capacity</th></tr></thead>
        <tbody>{w.rows.map((r) => (
          <tr key={r.bu}><td>{r.bu}</td><td className="num">{r.open_here}</td>
            <td>{r.open_elsewhere}{r.other_opportunities.length > 0 && <span className="muted"> ({r.other_opportunities.join(", ")})</span>}</td>
            <td className="num">{r.total}</td><td>{r.capacity ?? "—"} {r.over && <StatusBadge status="over" />}</td></tr>))}
        </tbody></table>
      <p className="muted">{w.note}</p>
    </section>
  );
}

// Engineering checks ported from v0.3.0 (task A-06): evidence for the bid manager, never a decision.
function EngineeringChecks({ c, oppId }: { c: Checks; oppId: string }) {
  const req = (id: string) => <a key={id} className="mono" href={`/opportunities/${oppId}/trace#${id}`}>{id}</a>;
  const outside = Object.entries(c.units_outside_scope);
  return (
    <section className="card">
      <div className="card-head"><h2>Engineering checks</h2>
        <span className="muted">Over {c.requirements_checked} frozen requirements. Illustrative rules ported from the earlier code line; to be confirmed with SpinCo engineering.</span></div>
      <h3>Scope: layers this RFP covers</h3>
      <ul className="dec-layers">{c.scope.layers.map((l) => (
        <li key={l.n}><StatusBadge status={l.in_scope ? "pass" : "n/a"} label={l.in_scope ? "in scope" : "not in scope"} />
          {" "}{l.n}. {l.name} <span className="muted">({l.basis})</span>
          {l.terms.length > 0 && <div className="muted">{l.terms.map((t) => <span key={t.term}>“{t.term}” ×{t.count} in {t.req_ids.map(req)}; </span>)}</div>}
        </li>))}</ul>
      {outside.length > 0 && <Alert kind="warn">Suggested although nothing in the RFP points to their layers: {outside.map(([bu, ids]) => `${bu} (${ids.length})`).join(", ")}. Check these matches.</Alert>}
      <h3>Rules</h3>
      <table className="dense dec-rules"><tbody>{c.rules.map((r) => (
        <tr key={r.id}><td className="mono">{r.id}</td><td><StatusBadge status={r.status} /></td>
          <td>{r.note}<div className="muted">{r.rule}</div></td></tr>))}</tbody></table>
      <h3>Offering type against each unit&apos;s default tier</h3>
      {c.tier_flags.length === 0 ? <p className="muted">No flags.</p> : (
        <details><summary>{c.tier_flags.length} item(s) need an engineer&apos;s confirmation</summary>
          <ul className="per-req">{c.tier_flags.map((f, i) => <li key={i}>{req(f.req_id)} {f.bu} · {f.product_id}: {f.note}</li>)}</ul></details>)}
      <h3>Low-voltage solver</h3>
      <p><StatusBadge status={c.solver.status === "NOT_SOLVABLE" ? "n/a" : "pass"} label={c.solver.status.replace(/_/g, " ").toLowerCase()} /></p>
      {c.solver.reasons.length > 0 && <ul>{c.solver.reasons.map((r) => <li key={r} className="muted">{r}</li>)}</ul>}
      {c.solver.working.length > 0 && <table className="dense"><tbody>{c.solver.working.map((w) => (
        <tr key={w.step}><td>{w.step}</td><td className="mono">{w.expression} = {w.result} {w.unit}</td><td className="muted">{w.reference}</td></tr>))}</tbody></table>}
      {c.solver.warnings.map((w) => <p key={w} className="warn">{w}</p>)}
    </section>
  );
}
type Data = { evidence: Evidence; summary: Summary | null; units: Unit[]; participation: Decision | null; go_no_go: Decision | null };

export default function DecisionsPage() {
  const { id } = useParams<{ id: string }>();
  const toast = useToast();
  const [ask, confirmDialog] = useConfirm();
  const { data, error, reload } = useApi<Data>(`/api/opportunities/${id}/decisions`);
  const { data: sent, reload: reloadSent } = useApi<Record<string, string>>(`/api/opportunities/${id}/knowledge`); // A-11
  const [busy, setBusy] = useState<string>(); // what is running: one action at a time
  if (error) return <Alert kind="error" title="Could not load the bid decision.">{error}</Alert>;
  if (!data) return <Skeleton lines={5} />;
  const { evidence: ev, participation: part, go_no_go: go } = data;

  // one action at a time: a double click must not record two decisions or start two dispatches
  const run = <T,>(label: string, request: Promise<T>, done: (r: T) => void = () => {}) => {
    setBusy(label);
    request.then((r) => { done(r); return reload(); }, (e) => toast.error(errorMessage(e))).finally(() => setBusy(undefined));
  };
  const statusChanged = () => window.dispatchEvent(new Event(STATUS_EVENT)); // header stepper and badge
  const recordParticipation = (form: FormData) =>
    run("participation", post(`/api/opportunities/${id}/participation`, { units: form.getAll("units"), rationale: form.get("rationale") }),
      () => toast.success("Participation recorded."));
  const decide = async (outcome: string, form: HTMLFormElement) => {
    const f = new FormData(form);
    const criteria = (data.summary?.criteria ?? []).map((c) => ({ id: c.id, status: f.get(`crit-${c.id}`), note: f.get(`note-${c.id}`) ?? "" }));
    if (outcome === "no_go" && !await ask({ title: "Record no-go?", confirmLabel: "Record no-go", danger: true,
      message: "The opportunity is marked no-go. Nothing is sent to the units; a later go decision can still overrule it." })) return;
    run("decision", post(`/api/opportunities/${id}/go-no-go`, { outcome, rationale: f.get("rationale"), criteria }),
      () => { toast.success(outcome === "go" ? "Decision recorded: go." : "Decision recorded: no-go."); statusChanged(); });
  };
  const dispatch = () => run("dispatch", post<{ created: number }>(`/api/opportunities/${id}/dispatch`), (r) => {
    toast.success(r.created ? `${r.created} new assignment(s) sent to the units.` : "Nothing new to send: every unit already has its work.");
    statusChanged();
  });

  return (
    <div className="decisions">
      <PageHead level={2} title="Bid decision" help="Review the evidence, choose the participating business units, decide go or no-go, then send each unit its work." />
      <section className="card">
        <div className="card-head"><h2>Evidence</h2>
          <span className="muted">{ev.requirements} requirements · {Object.entries(ev.by_category).map(([k, v]) => `${k} ${v}`).join(", ")}</span></div>
        <p>Offering mix: {Object.entries(ev.offering_mix).map(([k, v]) => <StatusBadge key={k} status={k} kind="offering" label={`${offeringLabel(k)} ${v}`} />)}</p>
        <p>Suggested units: {Object.entries(ev.suggested_units).map(([k, v]) => <strong key={k}>{k} ({v}) </strong>)}
          {Object.keys(ev.suggested_units).length === 0 && "none yet: run matching"}</p>
        {ev.unanchored.length > 0 && <details className="dec-unanchored"><summary className="warn">Unanchored: {ev.unanchored.length} requirement(s) without a place in the RFP</summary>
          <p className="muted mono">{ev.unanchored.join(", ")}</p></details>}
        {ev.unmatched.length > 0 && <p className="muted">Not yet matched: {ev.unmatched.length}</p>}
        {ev.not_reviewed > 0 && <p className="muted">Product matches nobody has accepted or changed yet: {ev.not_reviewed} (Traceability, pane 3)</p>}
        {!ev.frozen && <Alert kind="warn">Requirements are not frozen yet: freeze them on the Requirements page before deciding go or no-go.</Alert>}
      </section>

      {ev.frozen && <EngineeringChecks c={ev.checks} oppId={id} />}
      {ev.frozen && <PortfolioChecks ev={ev} />}

      <section className="card">
        <div className="card-head"><h2>1. Which business units take part?</h2>
          {part && <span className="muted">Recorded by <strong>{part.decided_by}</strong>: {part.units.join(", ")}</span>}</div>
        {part && <p>{part.rationale}
          {part.rationale && <> <SendToKnowledge kind="decision" refId={part.id} status={sent?.[`decision:${part.id}`]} onSent={reloadSent} /></>}</p>}
        <form className="form" action={recordParticipation}>
          <fieldset className="dec-units"><legend className="sr-only">Business units</legend>
            {data.units.map((u) => (
              <label key={u.code} className="check">
                <input type="checkbox" name="units" value={u.code}
                  defaultChecked={part ? part.units.includes(u.code) : u.code in ev.suggested_units} /> {u.name}
              </label>
            ))}
          </fieldset>
          <label>Rationale <input name="rationale" /></label>
          <button disabled={!!busy}>Record participation</button>
          {busy === "participation" && <Busy label="Recording…" />}
        </form>
      </section>

      <section className="card">
        <div className="card-head"><h2>2. Go / no-go</h2>
          {go && <span className="muted">Decision <StatusBadge status={go.outcome} kind="opp" label={go.outcome.replace("_", "-")} /> by <strong>{go.decided_by}</strong></span>}</div>
        {go && <p>{go.rationale}
          {go.criteria && go.criteria.length > 0 && <span className="muted"> Criteria judged: {(["met", "not_met", "unknown"] as Judgement[])
            .map((j) => `${go.criteria!.filter((c) => c.status === j).length} ${JUDGEMENT[j]}`).join(", ")}.</span>}
          {go.rationale && <> <SendToKnowledge kind="decision" refId={go.id} status={sent?.[`decision:${go.id}`]} onSent={reloadSent} /></>}</p>}
        {data.summary && <GoNoGoSummary s={data.summary} oppId={id} />}
        <form className="form compact" onSubmit={(e) => e.preventDefault()}>
          {data.summary && <div className="table-scroll"><table className="dec-criteria">
            <thead><tr><th>Criterion</th><th>Layer 0&apos;s assessment</th><th>Your judgement</th><th>Note</th></tr></thead>
            <tbody>{data.summary.criteria.map((c) => (
              <tr key={c.id}>
                <td><strong>{c.name}</strong><div className="muted">{c.question}</div></td>
                <td><StatusBadge status={c.status} kind="compliance" label={JUDGEMENT[c.status]} />
                  <div className="muted">{c.detail}</div></td>
                <td><label><span className="sr-only">Your judgement on {c.name}</span>
                  <select name={`crit-${c.id}`} defaultValue={go?.criteria?.find((x) => x.id === c.id)?.status ?? c.status}>
                    {(Object.keys(JUDGEMENT) as Judgement[]).map((j) => <option key={j} value={j}>{JUDGEMENT[j]}</option>)}</select></label></td>
                <td><label><span className="sr-only">Note on {c.name}</span><input name={`note-${c.id}`} placeholder="optional" /></label></td>
              </tr>))}</tbody>
          </table></div>}
          <label>Rationale <input name="rationale" /></label>
          <div className="row">
            <button type="button" disabled={!ev.frozen || !!busy} onClick={(e) => decide("go", e.currentTarget.form!)}>Go</button>
            <button type="button" disabled={!ev.frozen || !!busy} className="danger secondary" onClick={(e) => decide("no_go", e.currentTarget.form!)}>No-go</button>
            {busy === "decision" && <Busy label="Recording…" />}
            {!ev.frozen && <span className="muted">Freeze the requirements first.</span>}
          </div>
        </form>
      </section>

      {go?.outcome === "go" && <section className="card">
        <div className="card-head"><h2>3. Send the work to the units</h2>
          <span className="muted">Repeat after changing matches or participation: new work is sent, work that no longer fits is withdrawn.</span></div>
        <div className="row">
          <button disabled={!!busy} onClick={dispatch}>Dispatch work packages to units</button>
          {busy === "dispatch" && <Busy label="Dispatching…" />}
        </div>
      </section>}
      {confirmDialog}
    </div>
  );
}
