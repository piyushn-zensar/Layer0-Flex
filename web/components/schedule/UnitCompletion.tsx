"use client";
// "Your unit's delivery estimates" on My work (P-33, P-47; C-24, C-42): the unit manager gives an estimated completion date
// for each bid the unit takes part in and states the five delivery factors (no constraint, or a constraint with a note).
// Shown only to that unit's product manager.  Owner: Atharv.
import { useState } from "react";
import { api, errorMessage, useApi, useMe } from "@/lib/api";
import { FEASIBILITY_FACTOR_LABELS, FEASIBILITY_FACTORS, FEASIBILITY_STATUS_LABELS, formatDate, type Assignment, type Schedule } from "@/lib/types";
import { Alert, Busy, useToast } from "@/components/ui";

function Row({ oppId, bu }: { oppId: string; bu: string }) {
  const toast = useToast();
  const { data, error, reload } = useApi<Schedule>(`/api/bids/${oppId}/schedule`);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string>();
  if (error) return <tr><td className="mono">{oppId}</td><td colSpan={3}><Alert kind="error">{error}</Alert></td></tr>;
  const mine = data?.units.find((u) => u.bu === bu);
  if (!data || !mine) return null; // loading, or the unit does not take part in this bid
  const stated = FEASIBILITY_FACTORS.filter((f) => mine.factors[f]).length;
  const save = (form: FormData) => {
    const date = String(form.get("estimated_completion") ?? "");
    if (!date) { setFormError("Pick a date."); return; }
    const factors = [];
    for (const f of FEASIBILITY_FACTORS) {
      const status = String(form.get(`f-${f}`) ?? "");
      const note = String(form.get(`n-${f}`) ?? "").trim();
      if (!status) continue; // not stated: left as it was
      if (status === "constraint" && !note) { setFormError(`Say what limits delivery for ${FEASIBILITY_FACTOR_LABELS[f]}.`); return; }
      factors.push({ factor: f, status, note });
    }
    setBusy(true); setFormError(undefined);
    api(`/api/bids/${oppId}/units/${bu}/completion`, { method: "PUT", body: JSON.stringify({
      estimated_completion: date, note: String(form.get("note") ?? "").trim(), factors }) })
      .then(() => { toast.success(`${oppId}: delivery estimate saved.`); return reload(); }, (e) => setFormError(errorMessage(e)))
      .finally(() => setBusy(false));
  };
  return (
    <tr>
      <td className="mono"><strong>{oppId}</strong></td>
      <td data-label="Current estimate">{mine.estimated_completion ? formatDate(mine.estimated_completion.slice(0, 10)) : <span className="muted">not given</span>}</td>
      <td data-label="Constraints">{stated === 0 ? <span className="muted">factors not stated</span>
        : mine.constraints.length === 0 ? <span className="muted">none</span>
        : mine.constraints.map((f) => <span key={f} className="tag sev-medium" title={mine.factors[f]?.note}>{FEASIBILITY_FACTOR_LABELS[f]}</span>)}</td>
      <td data-label="Your estimate">
        <form key={`${mine.estimated_completion}|${mine.note}|${JSON.stringify(mine.factors)}`} action={save}>
          <div className="inline">
            <label><span className="sr-only">Estimated completion date for {oppId}</span>
              <input type="date" name="estimated_completion" required defaultValue={mine.estimated_completion?.slice(0, 10) ?? ""} disabled={busy} /></label>
            <label><span className="sr-only">Note for {oppId} (optional)</span>
              <input name="note" placeholder="Note (optional)" defaultValue={mine.note} disabled={busy} /></label>
            <button className="sm" disabled={busy}>Save</button>
            {busy && <Busy label="Saving…" />}
          </div>
          <details>
            <summary>Delivery factors ({stated} of {FEASIBILITY_FACTORS.length} stated)</summary>
            {FEASIBILITY_FACTORS.map((f) => (
              <div key={f} className="inline">
                <label>{FEASIBILITY_FACTOR_LABELS[f]}{" "}
                  <select name={`f-${f}`} defaultValue={mine.factors[f]?.status ?? ""} disabled={busy}>
                    <option value="">Not stated</option>
                    <option value="ok">{FEASIBILITY_STATUS_LABELS.ok}</option>
                    <option value="constraint">{FEASIBILITY_STATUS_LABELS.constraint}</option>
                  </select></label>
                <label><span className="sr-only">What limits delivery: {FEASIBILITY_FACTOR_LABELS[f]}</span>
                  <input name={`n-${f}`} placeholder="What limits delivery (required for a constraint)" defaultValue={mine.factors[f]?.note ?? ""} disabled={busy} /></label>
              </div>))}
          </details>
        </form>
        {formError && <div className="warn">{formError}</div>}
      </td>
    </tr>
  );
}

export default function UnitCompletion({ bu }: { bu: string }) {
  const me = useMe();
  const { data } = useApi<{ items: Assignment[] }>(`/api/inbox/${bu}`);
  if (me?.role !== "product_manager" || me.bu !== bu || !data) return null;
  const opps = [...new Set(data.items.map((a) => a.opportunity_id))];
  if (opps.length === 0) return null;
  return (
    <section className="card" data-tour="inbox-completion">
      <div className="card-head"><h2>Your unit&apos;s delivery estimates</h2>
        <span className="muted">When your unit expects to finish each bid and what could limit delivery: people, skills, manufacturing
          capacity, materials and cost. The bid manager accepts these estimates; no resource plan is needed.</span></div>
      <div className="table-scroll"><table className="dense stack-sm">
        <thead><tr><th>Bid</th><th>Current estimate</th><th>Constraints</th><th>Your estimate</th></tr></thead>
        <tbody>{opps.map((o) => <Row key={o} oppId={o} bu={bu} />)}</tbody>
      </table></div>
    </section>
  );
}
