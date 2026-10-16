"use client";
// "Your unit's completion dates" on My work (P-33, C-24): the unit manager gives an estimated completion date for each bid
// the unit takes part in. Shown only to that unit's product manager.  Owner: Atharv.
import { useState } from "react";
import { api, errorMessage, useApi, useMe } from "@/lib/api";
import type { Assignment, Schedule } from "@/lib/types";
import { Alert, Busy, useToast } from "@/components/ui";

function Row({ oppId, bu }: { oppId: string; bu: string }) {
  const toast = useToast();
  const { data, error, reload } = useApi<Schedule>(`/api/opportunities/${oppId}/schedule`);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string>();
  if (error) return <tr><td className="mono">{oppId}</td><td colSpan={2}><Alert kind="error">{error}</Alert></td></tr>;
  const mine = data?.units.find((u) => u.bu === bu);
  if (!data || !mine) return null; // loading, or the unit does not take part in this bid
  const save = (form: FormData) => {
    const date = String(form.get("estimated_completion") ?? "");
    if (!date) { setFormError("Pick a date."); return; }
    setBusy(true); setFormError(undefined);
    api(`/api/opportunities/${oppId}/units/${bu}/completion`, { method: "PUT", body: JSON.stringify({ estimated_completion: date, note: String(form.get("note") ?? "").trim() }) })
      .then(() => { toast.success(`${oppId}: completion date saved.`); return reload(); }, (e) => setFormError(errorMessage(e)))
      .finally(() => setBusy(false));
  };
  return (
    <tr>
      <td className="mono">{oppId}</td>
      <td>{mine.estimated_completion ? mine.estimated_completion.slice(0, 10) : <span className="muted">not given</span>}</td>
      <td>
        <form key={`${mine.estimated_completion}|${mine.note}`} className="inline" action={save}>
          <label><span className="sr-only">Estimated completion date for {oppId}</span>
            <input type="date" name="estimated_completion" required defaultValue={mine.estimated_completion?.slice(0, 10) ?? ""} disabled={busy} /></label>
          <label><span className="sr-only">Note for {oppId} (optional)</span>
            <input name="note" placeholder="Note (optional)" defaultValue={mine.note} disabled={busy} /></label>
          <button className="sm" disabled={busy}>Save</button>
          {busy && <Busy label="Saving…" />}
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
      <div className="card-head"><h2>Your unit&apos;s completion dates</h2>
        <span className="muted">When your unit expects to finish each bid. The bid manager plans the submission from these dates.</span></div>
      <div className="table-scroll"><table className="dense">
        <thead><tr><th>Bid</th><th>Current date</th><th>Your date</th></tr></thead>
        <tbody>{opps.map((o) => <Row key={o} oppId={o} bu={bu} />)}</tbody>
      </table></div>
    </section>
  );
}
