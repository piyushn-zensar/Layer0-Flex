"use client";
// Evidence pack, participation, go/no-go and one-step dispatch.  Owner: Atharv.
import { useParams } from "next/navigation";
import { post, useApi } from "@/lib/api";
import type { Unit } from "@/lib/types";

type Decision = { outcome: string; units: string[]; rationale: string; decided_by: string };
type Evidence = {
  requirements: number; by_category: Record<string, number>; unanchored: string[];
  suggested_units: Record<string, number>; offering_mix: Record<string, number>; unmatched: string[];
};
type Data = { evidence: Evidence; units: Unit[]; participation: Decision | null; go_no_go: Decision | null };

export default function DecisionsPage() {
  const { id } = useParams<{ id: string }>();
  const { data, reload } = useApi<Data>(`/api/opportunities/${id}/decisions`);
  if (!data) return <p>Loading…</p>;
  const { evidence: ev, participation: part, go_no_go: go } = data;

  const recordParticipation = (form: FormData) =>
    post(`/api/opportunities/${id}/participation`, { units: form.getAll("units"), rationale: form.get("rationale") }).then(reload, alert);
  const decide = (outcome: string, form: HTMLFormElement) =>
    post(`/api/opportunities/${id}/go-no-go`, { outcome, rationale: new FormData(form).get("rationale") }).then(reload, alert);
  const dispatch = () => post<{ created: number }>(`/api/opportunities/${id}/dispatch`).then((r) => { alert(`${r.created} assignments created`); reload(); }, alert);

  return (
    <>
      <h1>Participation and go/no-go</h1>
      <section className="card">
        <h2>Evidence</h2>
        <p>{ev.requirements} requirements · {Object.entries(ev.by_category).map(([k, v]) => `${k} ${v}`).join(", ")}</p>
        <p>Offering mix: {Object.entries(ev.offering_mix).map(([k, v]) => <span key={k} className={`tag ${k}`}>{k} {v}</span>)}</p>
        <p>Suggested units: {Object.entries(ev.suggested_units).map(([k, v]) => <strong key={k}>{k} ({v}) </strong>)}
          {Object.keys(ev.suggested_units).length === 0 && "none yet: run matching"}</p>
        {ev.unanchored.length > 0 && <p className="warn">Unanchored: {ev.unanchored.join(", ")}</p>}
        {ev.unmatched.length > 0 && <p className="muted">Not yet matched: {ev.unmatched.length}</p>}
      </section>

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
          <button>Record participation</button>
        </form>
      </section>

      <section className="card">
        <h2>2. Go / no-go</h2>
        {go && <p>Decision <span className="badge">{go.outcome}</span> by <strong>{go.decided_by}</strong>. {go.rationale}</p>}
        <form className="form" onSubmit={(e) => e.preventDefault()}>
          <label>Rationale <input name="rationale" /></label>
          <button type="button" onClick={(e) => decide("go", e.currentTarget.form!)}>Go</button>
          <button type="button" className="secondary" onClick={(e) => decide("no_go", e.currentTarget.form!)}>No-go</button>
        </form>
      </section>

      {go?.outcome === "go" && <button onClick={dispatch}>Dispatch work packages to units</button>}
    </>
  );
}
