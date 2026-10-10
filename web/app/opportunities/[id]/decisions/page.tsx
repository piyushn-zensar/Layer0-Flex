"use client";
// Evidence pack, participation, go/no-go and one-step dispatch.  Owner: Atharv.
import { useParams } from "next/navigation";
import { useState } from "react";
import { post, useApi } from "@/lib/api";
import type { Unit } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";

type Judgement = "met" | "not_met" | "unknown";
type Decision = { outcome: string; units: string[]; rationale: string; decided_by: string; criteria?: { id: string; status: Judgement; note: string }[] };
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
      <p className="warn"><strong>{s.advice}</strong></p>
      <h3>How the requirements are satisfied</h3>
      <table>
        <thead><tr><th>Category</th><th>Fully</th><th>Partly</th><th>Not</th><th>Bid desk</th></tr></thead>
        <tbody>{Object.entries(s.by_category).map(([cat, n]) => (
          <tr key={cat}><td>{cat}</td><td>{n.fully}</td><td>{n.partly}</td><td>{n.not}</td><td>{n.bid_desk}</td></tr>))}</tbody>
      </table>
      <details><summary>Per requirement ({s.rows.length}): from the unit&apos;s answer where there is one, otherwise estimated from the match</summary>
        <ul>{s.rows.map((r) => <li key={r.req_id}><a className="mono" href={`/opportunities/${oppId}/trace#${r.req_id}`}>{r.req_id}</a>{" "}
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

const STATUS_CLASS: Record<string, string> = { pass: "status-approved", warn: "status-proposed", fail: "status-rejected", "n/a": "" };

// Bid and portfolio checks ported from v1.1 onto real data (task A-10): evidence, never a decision.
function PortfolioChecks({ ev }: { ev: Evidence }) {
  const d = ev.deviations, w = ev.workload;
  return (
    <section className="card">
      <h2>Bid and portfolio checks</h2>
      <h3>Deviations from the standard product</h3>
      {d.rows.length === 0 ? <p className="ok">{d.checked ? `${d.checked} data-sheet ratings are within the standard products.` : "No data-sheet rating to compare."}</p> : (
        <table><thead><tr><th>Product</th><th>Rating</th><th>RFP asks</th><th>Standard</th><th>Severity</th><th>Source</th></tr></thead>
          <tbody>{d.rows.map((r, i) => (
            <tr key={i}><td className="mono">{r.product_id}</td><td>{r.field}</td><td>{r.rfp}</td><td>{r.standard}</td>
              <td><span className={`badge ${r.severity === "high" ? "status-rejected" : "status-proposed"}`}>{r.severity}</span></td><td>{r.source}</td></tr>))}
          </tbody></table>)}
      <p className="muted">{d.note}</p>
      <h3>Workload across opportunities</h3>
      <table><thead><tr><th>Unit</th><th>This opportunity</th><th>Other opportunities</th><th>Total open</th><th>Capacity</th></tr></thead>
        <tbody>{w.rows.map((r) => (
          <tr key={r.bu}><td>{r.bu}</td><td>{r.open_here}</td>
            <td>{r.open_elsewhere}{r.other_opportunities.length > 0 && <span className="muted"> ({r.other_opportunities.join(", ")})</span>}</td>
            <td>{r.total}</td><td>{r.capacity ?? "—"} {r.over && <span className="badge status-rejected">over</span>}</td></tr>))}
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
      <h2>Engineering checks</h2>
      <p className="muted">Over {c.requirements_checked} frozen requirements. Illustrative rules ported from the earlier code line; to be confirmed with SpinCo engineering.</p>
      <h3>Scope: layers this RFP covers</h3>
      <ul>{c.scope.layers.map((l) => (
        <li key={l.n}><span className={`badge ${l.in_scope ? "status-approved" : ""}`}>{l.in_scope ? "in scope" : "not in scope"}</span>
          {" "}{l.n}. {l.name} <span className="muted">({l.basis})</span>
          {l.terms.length > 0 && <div className="muted">{l.terms.map((t) => <span key={t.term}>“{t.term}” ×{t.count} in {t.req_ids.map(req)}; </span>)}</div>}
        </li>))}</ul>
      {outside.length > 0 && <p className="warn">Suggested although nothing in the RFP points to their layers: {outside.map(([bu, ids]) => `${bu} (${ids.length})`).join(", ")}. Check these matches.</p>}
      <h3>Rules</h3>
      <table><tbody>{c.rules.map((r) => (
        <tr key={r.id}><td className="mono">{r.id}</td><td><span className={`badge ${STATUS_CLASS[r.status]}`}>{r.status}</span></td>
          <td>{r.note}<div className="muted">{r.rule}</div></td></tr>))}</tbody></table>
      <h3>Offering type against each unit&apos;s default tier</h3>
      {c.tier_flags.length === 0 ? <p className="muted">No flags.</p> : (
        <details><summary>{c.tier_flags.length} item(s) need an engineer&apos;s confirmation</summary>
          <ul>{c.tier_flags.map((f, i) => <li key={i}>{req(f.req_id)} {f.bu} · {f.product_id}: {f.note}</li>)}</ul></details>)}
      <h3>Low-voltage solver</h3>
      <p><span className={`badge ${c.solver.status === "NOT_SOLVABLE" ? "" : "status-approved"}`}>{c.solver.status}</span></p>
      {c.solver.reasons.length > 0 && <ul>{c.solver.reasons.map((r) => <li key={r} className="muted">{r}</li>)}</ul>}
      {c.solver.working.length > 0 && <table><tbody>{c.solver.working.map((w) => (
        <tr key={w.step}><td>{w.step}</td><td className="mono">{w.expression} = {w.result} {w.unit}</td><td className="muted">{w.reference}</td></tr>))}</tbody></table>}
      {c.solver.warnings.map((w) => <p key={w} className="warn">{w}</p>)}
    </section>
  );
}
type Data = { evidence: Evidence; summary: Summary | null; units: Unit[]; participation: Decision | null; go_no_go: Decision | null };

export default function DecisionsPage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, reload } = useApi<Data>(`/api/opportunities/${id}/decisions`);
  const [busy, setBusy] = useState(false);
  if (error) return <p className="warn">Could not load the bid decision: {error}</p>;
  if (!data) return <p>Loading…</p>;
  const { evidence: ev, participation: part, go_no_go: go } = data;

  // one action at a time: a double click must not record two decisions or start two dispatches
  const run = <T,>(request: Promise<T>, done: (r: T) => void = () => {}) => {
    setBusy(true);
    request.then((r) => { done(r); return reload(); }, alert).finally(() => setBusy(false));
  };
  const recordParticipation = (form: FormData) =>
    run(post(`/api/opportunities/${id}/participation`, { units: form.getAll("units"), rationale: form.get("rationale") }));
  const decide = (outcome: string, form: HTMLFormElement) => {
    const f = new FormData(form);
    const criteria = (data.summary?.criteria ?? []).map((c) => ({ id: c.id, status: f.get(`crit-${c.id}`), note: f.get(`note-${c.id}`) ?? "" }));
    run(post(`/api/opportunities/${id}/go-no-go`, { outcome, rationale: f.get("rationale"), criteria }));
  };
  const dispatch = () => run(post<{ created: number }>(`/api/opportunities/${id}/dispatch`), (r) =>
    alert(r.created ? `${r.created} new assignments sent to the units.` : "Nothing new to send: every unit already has its work."));

  return (
    <>
      <PageHead level={2} title="Bid decision" help="Review the evidence, choose the participating business units, decide go or no-go, then send each unit its work." />
      <section className="card">
        <h2>Evidence</h2>
        <p>{ev.requirements} requirements · {Object.entries(ev.by_category).map(([k, v]) => `${k} ${v}`).join(", ")}</p>
        <p>Offering mix: {Object.entries(ev.offering_mix).map(([k, v]) => <span key={k} className={`tag ${k}`}>{k} {v}</span>)}</p>
        <p>Suggested units: {Object.entries(ev.suggested_units).map(([k, v]) => <strong key={k}>{k} ({v}) </strong>)}
          {Object.keys(ev.suggested_units).length === 0 && "none yet: run matching"}</p>
        {ev.unanchored.length > 0 && <p className="warn">Unanchored: {ev.unanchored.join(", ")}</p>}
        {ev.unmatched.length > 0 && <p className="muted">Not yet matched: {ev.unmatched.length}</p>}
        {ev.not_reviewed > 0 && <p className="muted">Product matches nobody has accepted or changed yet: {ev.not_reviewed} (Traceability, pane 3)</p>}
        {!ev.frozen && <p className="warn">Requirements are not frozen yet: freeze them on the Requirements page before deciding go or no-go.</p>}
      </section>

      {ev.frozen && <EngineeringChecks c={ev.checks} oppId={id} />}
      {ev.frozen && <PortfolioChecks ev={ev} />}

      <section className="card">
        <h2>1. Which business units take part?</h2>
        {part && <p>Recorded by <strong>{part.decided_by}</strong>: {part.units.join(", ")}. {part.rationale}</p>}
        <form className="form" action={recordParticipation}>
          {data.units.map((u) => (
            <label key={u.code} className="check">
              <input type="checkbox" name="units" value={u.code}
                defaultChecked={part ? part.units.includes(u.code) : u.code in ev.suggested_units} /> {u.name}
            </label>
          ))}
          <label>Rationale <input name="rationale" /></label>
          <button disabled={busy}>Record participation</button>
        </form>
      </section>

      <section className="card">
        <h2>2. Go / no-go</h2>
        {go && <p>Decision <span className="badge">{go.outcome}</span> by <strong>{go.decided_by}</strong>. {go.rationale}
          {go.criteria && go.criteria.length > 0 && <span className="muted"> Criteria judged: {(["met", "not_met", "unknown"] as Judgement[])
            .map((j) => `${go.criteria!.filter((c) => c.status === j).length} ${JUDGEMENT[j]}`).join(", ")}.</span>}</p>}
        {data.summary && <GoNoGoSummary s={data.summary} oppId={id} />}
        <form className="form compact" onSubmit={(e) => e.preventDefault()}>
          {data.summary && <table>
            <thead><tr><th>Criterion</th><th>Layer 0&apos;s assessment</th><th>Your judgement</th><th>Note</th></tr></thead>
            <tbody>{data.summary.criteria.map((c) => (
              <tr key={c.id}>
                <td><strong>{c.name}</strong><div className="muted">{c.question}</div></td>
                <td><span className={`badge ${c.status === "met" ? "status-approved" : c.status === "not_met" ? "status-proposed" : ""}`}>{JUDGEMENT[c.status]}</span>
                  <div className="muted">{c.detail}</div></td>
                <td><label><span className="sr-only">Your judgement on {c.name}</span>
                  <select name={`crit-${c.id}`} defaultValue={go?.criteria?.find((x) => x.id === c.id)?.status ?? c.status}>
                    {(Object.keys(JUDGEMENT) as Judgement[]).map((j) => <option key={j} value={j}>{JUDGEMENT[j]}</option>)}</select></label></td>
                <td><label><span className="sr-only">Note on {c.name}</span><input name={`note-${c.id}`} placeholder="optional" /></label></td>
              </tr>))}</tbody>
          </table>}
          <label>Rationale <input name="rationale" /></label>
          <button type="button" disabled={!ev.frozen || busy} onClick={(e) => decide("go", e.currentTarget.form!)}>Go</button>
          <button type="button" disabled={!ev.frozen || busy} className="secondary" onClick={(e) => decide("no_go", e.currentTarget.form!)}>No-go</button>
        </form>
      </section>

      {go?.outcome === "go" && <p><button disabled={busy} onClick={dispatch}>Dispatch work packages to units</button>{" "}
        <span className="muted">Repeat after changing matches or participation: new work is sent, work that no longer fits is withdrawn.</span></p>}
    </>
  );
}
