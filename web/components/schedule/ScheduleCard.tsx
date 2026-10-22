"use client";
// The bid manager's two approvals (P-33, C-24), in two parts (P-44, C-41). part "schedule", on the Assessment Summary: delivery
// feasibility from the teams (P-47, C-42): the RFP due date and consolidation days, each unit's estimate and five delivery
// factors, the latest date and planned submission, and the bid manager's acceptance of the teams' estimates.
// part "compliance", on the Bid decision once a unit answer is validated: the high-level compliance position and Approve
// compliance position. decided (the go/no-go is recorded): the accepted estimates and the settings show as recorded, the bid manager
// opens them again with "Change…"; a person who cannot act sees the recorded state, no greyed form (21 Oct review).  Owner: Atharv.
import { useState } from "react";
import { api, errorMessage, isBidManager, post, useApi, useMe } from "@/lib/api";
import { COMPLIANCE_LABELS, FEASIBILITY_FACTOR_LABELS, FEASIBILITY_FACTORS, type Approval, formatDate, type FeasibilityFactor, type Schedule,
  type ScheduleUnit } from "@/lib/types";
import { Alert, Busy, Skeleton, useConfirm, useToast } from "@/components/ui";

const day = (iso?: string | null) => (iso ? iso.slice(0, 10) : ""); // a date input's value
const show = (iso?: string | null) => formatDate(day(iso));          // shown
const NOT_READY = "Every participating unit must give its estimate and the five delivery factors first";

// accept: the schedule kind reads "accepted" (the teams' estimates, P-47); the compliance kind "approved"
function ApprovalLine({ a, accept }: { a: Approval | null; accept: boolean }) {
  if (!a) return <span className="muted">{accept ? "Not accepted yet." : "Not approved yet."}</span>;
  if (!a.current) return <span className="warn">Reopened: {accept ? "an estimate or a delivery factor" : "answers"} changed since {show(a.approved_at)}</span>;
  return <span>{accept ? "Accepted" : "Approved"} by <strong>{a.approved_by}</strong> on {show(a.approved_at)}{a.note && <span className="muted"> ({a.note})</span>}</span>;
}

function FactorCell({ u, f }: { u: ScheduleUnit; f: FeasibilityFactor }) {
  const e = u.factors[f];
  if (!e) return <span className="muted">Not stated</span>;
  if (e.status === "ok") return <span className="muted">No constraint</span>;
  return <><span className="tag sev-medium" title={e.note}>Constraint</span><div className="muted">{e.note}</div></>;
}

export default function ScheduleCard({ oppId, part, decided = false }: { oppId: string; part: "schedule" | "compliance"; decided?: boolean }) {
  const toast = useToast();
  const bm = isBidManager(useMe());
  const { data, error, reload } = useApi<Schedule>(`/api/bids/${oppId}/schedule`);
  const [ask, confirmDialog] = useConfirm();
  const [busy, setBusy] = useState<string>(); // one action at a time
  const [formError, setFormError] = useState<string>();
  const [changing, setChanging] = useState(false); // the bid manager reopened the recorded settings and acceptance
  if (error) return <section className="card"><Alert kind="error" title="Could not load the schedule.">{error}</Alert></section>;
  if (!data) return <section className="card"><Skeleton lines={3} /></section>;

  const run = (label: string, request: () => Promise<unknown>, done: string) => {
    setBusy(label); setFormError(undefined);
    request().then(() => { toast.success(done); setChanging(false); return reload(); }, (e) => { setFormError(errorMessage(e)); toast.error(errorMessage(e)); })
      .finally(() => setBusy(undefined));
  };
  const save = (form: FormData) => {
    const days = Number(form.get("consolidation_days"));
    if (!Number.isInteger(days) || days < 0) { setFormError("Consolidation days must be a whole number, 0 or more."); return; }
    run("save", () => api(`/api/bids/${oppId}/schedule`, { method: "PUT", body: JSON.stringify({
      due_date: String(form.get("due_date") ?? "") || null, consolidation_days: days }) }), "Schedule settings saved.");
  };
  const approve = async (kind: "schedule" | "compliance") => {
    const schedule = kind === "schedule";
    const again = !!data.approvals[kind];
    if (!(await ask({ title: schedule ? "Accept the teams' estimates?" : "Approve the compliance position?",
      message: schedule ? `You accept the units' estimates and the constraints they report: planned submission ${show(data.planned_submission) || "as shown"}. Each unit's estimate stays with its unit manager.`
        : "You approve the high-level compliance position from the units' validated answers. Each unit validates its own answers.",
      confirmLabel: schedule ? (again ? "Accept again" : "Accept") : (again ? "Approve again" : "Approve") }))) return;
    run(kind, () => post(`/api/bids/${oppId}/approvals`, { kind, note: "" }), schedule ? "Teams' estimates accepted." : "Compliance position approved.");
  };

  const complianceUnits = Object.keys(data.compliance).sort();
  const key = `${data.due_date}|${data.consolidation_days}`; // reset the inputs when the saved values change
  // the schedule part once the go/no-go is recorded and the estimates are accepted: recorded, not a live form
  const settled = part === "schedule" && decided && !!data.approvals.schedule?.current && !changing;
  const approval = (kind: "schedule" | "compliance", tour: string) => {
    const a = data.approvals[kind];
    const blocked = kind === "schedule" && !data.ready;
    return (
      <div className="row" data-tour={tour}>
        {bm && !settled && <button className={a?.current ? "secondary sm" : "sm"} disabled={!!busy || blocked} onClick={() => approve(kind)}>
          {kind === "schedule" ? "Accept the teams' estimates" : "Approve compliance position"}</button>}
        {busy === kind && <Busy label={kind === "schedule" ? "Accepting…" : "Approving…"} />}
        <ApprovalLine a={a} accept={kind === "schedule"} />
        {bm && blocked && <span className="muted">{NOT_READY}</span>}
        {!bm && !a?.current && <span className="muted">{kind === "schedule" ? "Only the bid manager accepts the estimates." : "Only the bid manager approves."}</span>}
        {bm && settled && <button type="button" className="secondary sm" onClick={() => setChanging(true)}>Change…</button>}
        {bm && changing && <button type="button" className="secondary sm" onClick={() => setChanging(false)}>Cancel</button>}
      </div>);
  };

  if (part === "compliance") {
    const validated = Object.values(data.compliance).some((c) => Object.entries(c).some(([k, n]) => k !== "open" && n > 0));
    if (!validated) return null;
    return (
      <section className="card" data-tour="dec-compliance">
        {confirmDialog}
        <div className="card-head"><h2>Compliance position</h2></div>
        <p className="muted">Counted per unit answer: a requirement several units answer counts once for each, and the bid desk row holds the
          capability gaps (stated as not offered). The bid manager approves the high-level position here; each unit validates its own answers.</p>
        <div className="table-scroll"><table className="dense stack-sm">
          <thead><tr><th>Unit</th><th className="num">{COMPLIANCE_LABELS.met}</th><th className="num">{COMPLIANCE_LABELS.partial}</th>
            <th className="num">{COMPLIANCE_LABELS.deviation}</th>
            <th className="num">{COMPLIANCE_LABELS.not_met}</th><th className="num">Open</th></tr></thead>
          <tbody>{complianceUnits.map((bu) => { const c = data.compliance[bu]; return (
            <tr key={bu}><td><strong>{bu === "BID" ? "Bid desk and capability gaps" : bu}</strong></td><td className="num" data-label={COMPLIANCE_LABELS.met}>{c.met}</td>
              <td className="num" data-label={COMPLIANCE_LABELS.partial}>{c.partial}</td><td className="num" data-label={COMPLIANCE_LABELS.deviation}>{c.deviation}</td>
              <td className="num" data-label={COMPLIANCE_LABELS.not_met}>{c.not_met}</td><td className="num" data-label="Open">{c.open}</td></tr>); })}</tbody>
        </table></div>
        <Alert kind="error">{formError}</Alert>
        {approval("compliance", "dec-approve-compliance")}
      </section>
    );
  }

  return (
    <section className="card" data-tour="asm-schedule">
      {confirmDialog}
      <div className="card-head"><h2>Delivery feasibility from the teams</h2></div>
      <p className="muted">Each unit manager gives the unit&apos;s estimate and reports people, skills, manufacturing capacity, materials and cost.
        Technical feasibility is the designers&apos; / engineers&apos; answers. The bid manager accepts the teams&apos; estimates and does not set the units&apos; dates.</p>

      {!bm || settled ? <p>RFP due date: <strong>{show(data.due_date) || "not set"}</strong> · Consolidation days: <strong>{data.consolidation_days}</strong></p> : (
      <form key={key} className="form" action={save}>
        <div className="row">
          <label>RFP due date (from the RFP) <input type="date" name="due_date" defaultValue={day(data.due_date)} disabled={!bm || !!busy} /></label>
          <label>Consolidation days <input type="number" name="consolidation_days" className="narrow" min={0} step={1} defaultValue={data.consolidation_days} disabled={!bm || !!busy} /></label>
          {bm && <button className="secondary sm" disabled={!!busy}>Save</button>}
          {busy === "save" && <Busy label="Saving…" />}
        </div>
      </form>)}
      <Alert kind="error">{formError}</Alert>

      <h3>Estimates and delivery factors per unit</h3>
      {data.units.length === 0 ? <p className="muted">No unit takes part yet: record participation first.</p> : (
        <div className="table-scroll"><table className="dense feasibility">
          <thead><tr><th>Unit</th><th>Estimate</th>{FEASIBILITY_FACTORS.map((f) => <th key={f}>{FEASIBILITY_FACTOR_LABELS[f]}</th>)}<th>Entered by</th></tr></thead>
          <tbody>{data.units.map((u) => (
            <tr key={u.bu}><td data-label="Unit">{u.bu}</td>
              <td data-label="Estimate">{u.estimated_completion ? <>{show(u.estimated_completion)}{u.note && <div className="muted">{u.note}</div>}</>
                : <span className="tag">Waiting for the unit manager</span>}</td>
              {FEASIBILITY_FACTORS.map((f) => <td key={f} data-label={FEASIBILITY_FACTOR_LABELS[f]}><FactorCell u={u} f={f} /></td>)}
              <td data-label="Entered by">{u.entered_by || "—"}</td></tr>))}</tbody>
        </table></div>)}

      {data.units.length > 0 && (data.constraints.length === 0 ? <p className="muted">No team reports a constraint.</p> : <>
        <p>Constraints reported: <strong>{data.constraints.length}</strong></p>
        <ul>{data.constraints.map((c) => <li key={`${c.bu}-${c.factor}`}>{c.bu} · {FEASIBILITY_FACTOR_LABELS[c.factor]}: {c.note}</li>)}</ul></>)}

      <p data-tour="asm-planned">{data.planned_submission
        ? <>Latest estimate {show(data.latest_unit_date)}; planned submission <strong>{show(data.planned_submission)}</strong> (+ {data.consolidation_days} days to consolidate)</>
        : <>Planned submission: when every unit has given its estimate (waiting: {data.missing.join(", ") || "none"})</>}</p>
      {data.after_due && <Alert kind="warn" title="After the due date">The planned submission {show(data.planned_submission)} is later than the RFP due date {show(data.due_date)}.</Alert>}

      {approval("schedule", "asm-approve-schedule")}
    </section>
  );
}
