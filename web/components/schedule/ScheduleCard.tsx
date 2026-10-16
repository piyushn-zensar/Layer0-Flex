"use client";
// "Schedule and approvals" on the Assessment step (P-33, C-24): the RFP due date and consolidation days, each unit's
// estimated completion date, the planned submission, the high-level compliance position, and the bid manager's two
// approvals (overall schedule, high-level compliance).  Owner: Atharv.
import { useState } from "react";
import { api, errorMessage, isBidManager, post, useApi, useMe } from "@/lib/api";
import { COMPLIANCE_LABELS, type Approval, type Schedule } from "@/lib/types";
import { Alert, Busy, Skeleton, useConfirm, useToast } from "@/components/ui";

const day = (iso?: string | null) => (iso ? iso.slice(0, 10) : "");
const NOT_READY = "Every participating unit must give its date first";

function ApprovalLine({ a }: { a: Approval | null }) {
  if (!a) return <span className="muted">Not approved yet.</span>;
  if (!a.current) return <span className="warn">Reopened: dates or answers changed since {day(a.approved_at)}</span>;
  return <span>Approved by <strong>{a.approved_by}</strong> on {day(a.approved_at)}{a.note && <span className="muted"> ({a.note})</span>}</span>;
}

export default function ScheduleCard({ oppId }: { oppId: string }) {
  const toast = useToast();
  const bm = isBidManager(useMe());
  const { data, error, reload } = useApi<Schedule>(`/api/opportunities/${oppId}/schedule`);
  const [ask, confirmDialog] = useConfirm();
  const [busy, setBusy] = useState<string>(); // one action at a time
  const [formError, setFormError] = useState<string>();
  if (error) return <section className="card"><Alert kind="error" title="Could not load the schedule.">{error}</Alert></section>;
  if (!data) return <section className="card"><Skeleton lines={3} /></section>;

  const run = (label: string, request: () => Promise<unknown>, done: string) => {
    setBusy(label); setFormError(undefined);
    request().then(() => { toast.success(done); return reload(); }, (e) => { setFormError(errorMessage(e)); toast.error(errorMessage(e)); })
      .finally(() => setBusy(undefined));
  };
  const save = (form: FormData) => {
    const days = Number(form.get("consolidation_days"));
    if (!Number.isInteger(days) || days < 0) { setFormError("Consolidation days must be a whole number, 0 or more."); return; }
    run("save", () => api(`/api/opportunities/${oppId}/schedule`, { method: "PUT", body: JSON.stringify({
      due_date: String(form.get("due_date") ?? "") || null, consolidation_days: days }) }), "Schedule settings saved.");
  };
  const approve = async (kind: "schedule" | "compliance") => {
    const schedule = kind === "schedule";
    const again = !!data.approvals[kind];
    if (!(await ask({ title: schedule ? "Approve the schedule?" : "Approve the compliance position?",
      message: schedule ? `You approve the overall schedule: planned submission ${day(data.planned_submission) || "as shown"}. Each unit's date stays with its manager.`
        : "You approve the high-level compliance position shown here. Each unit validates its own answers.",
      confirmLabel: again ? "Approve again" : "Approve" }))) return;
    run(kind, () => post(`/api/opportunities/${oppId}/approvals`, { kind, note: "" }), schedule ? "Schedule approved." : "Compliance position approved.");
  };

  const complianceUnits = Object.keys(data.compliance).sort();
  const key = `${data.due_date}|${data.consolidation_days}`; // reset the inputs when the saved values change

  return (
    <section className="card" data-tour="asm-schedule">
      {confirmDialog}
      <div className="card-head"><h2>Schedule and approvals</h2></div>
      <p className="muted">The bid manager approves only the overall schedule and the high-level compliance position; units validate their own answers.</p>

      <form key={key} className="form" action={save}>
        <div className="row">
          <label>RFP due date <input type="date" name="due_date" defaultValue={day(data.due_date)} disabled={!bm || !!busy} /></label>
          <label>Consolidation days <input type="number" name="consolidation_days" className="narrow" min={0} step={1} defaultValue={data.consolidation_days} disabled={!bm || !!busy} /></label>
          {bm && <button className="secondary sm" disabled={!!busy}>Save</button>}
          {busy === "save" && <Busy label="Saving…" />}
          {!bm && <span className="muted">Only the bid manager changes these.</span>}
        </div>
      </form>
      <Alert kind="error">{formError}</Alert>

      <h3>Estimated completion per unit</h3>
      {data.units.length === 0 ? <p className="muted">No unit takes part yet: record participation first.</p> : (
        <div className="table-scroll"><table className="dense">
          <thead><tr><th>Unit</th><th>Estimated completion</th><th>Note</th><th>Entered by</th></tr></thead>
          <tbody>{data.units.map((u) => (
            <tr key={u.bu}><td>{u.bu}</td>
              <td>{u.estimated_completion ? day(u.estimated_completion) : <span className="tag">Waiting for the unit manager</span>}</td>
              <td>{u.note || "—"}</td><td>{u.entered_by || "—"}</td></tr>))}</tbody>
        </table></div>)}

      <p data-tour="asm-planned">{data.planned_submission
        ? <>Planned submission: <strong>{day(data.planned_submission)}</strong> (last unit {day(data.latest_unit_date)} + {data.consolidation_days} days)</>
        : <>Planned submission: when every unit has given its date (waiting: {data.missing.join(", ") || "none"})</>}</p>
      {data.after_due && <Alert kind="warn" title="After the due date">The planned submission {day(data.planned_submission)} is later than the RFP due date {day(data.due_date)}.</Alert>}

      <h3>High-level compliance</h3>
      {complianceUnits.length === 0 ? <p className="muted">No answers yet.</p> : (
        <div className="table-scroll"><table className="dense">
          <thead><tr><th>Unit</th><th className="num">{COMPLIANCE_LABELS.met}</th><th className="num">{COMPLIANCE_LABELS.partial}</th>
            <th className="num">{COMPLIANCE_LABELS.not_met}</th><th className="num">Open</th></tr></thead>
          <tbody>{complianceUnits.map((bu) => { const c = data.compliance[bu]; return (
            <tr key={bu}><td>{bu}</td><td className="num">{c.met}</td><td className="num">{c.partial}</td><td className="num">{c.not_met}</td><td className="num">{c.open}</td></tr>); })}</tbody>
        </table></div>)}

      <h3>Approvals</h3>
      <div className="stack">
        {(["schedule", "compliance"] as const).map((kind) => {
          const a = data.approvals[kind];
          const blocked = kind === "schedule" && !data.ready;
          return (
            <div key={kind} className="row" data-tour={`asm-approve-${kind}`}>
              {bm && <button className={a?.current ? "secondary sm" : "sm"} disabled={!!busy || blocked} onClick={() => approve(kind)}>
                {kind === "schedule" ? "Approve schedule" : "Approve compliance position"}</button>}
              {busy === kind && <Busy label="Approving…" />}
              <ApprovalLine a={a} />
              {bm && blocked && <span className="muted">{NOT_READY}</span>}
            </div>);
        })}
      </div>
      {!bm && <p className="muted">Only the bid manager approves.</p>}
    </section>
  );
}
