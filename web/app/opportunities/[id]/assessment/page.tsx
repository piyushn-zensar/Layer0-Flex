"use client";
// Assessment step (A-16, technical-architecture 16.5): bid summary, open questions, participation, routing, Send for
// assessment (dispatch: the register is frozen when the RFP is read, P-32) and progress per unit. Go/no-go follows on
// the Bid decision step.  Owner: Atharv.
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { errorMessage, isBidManager, post, useApi, useMe } from "@/lib/api";
import type { Unit } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { STATUS_EVENT } from "@/components/shell/OppSteps"; // the header listens for it after sending
import { Alert, Busy, Skeleton, StatusBadge, offeringLabel, useToast } from "@/components/ui";
import SendToKnowledge from "@/components/knowledge/SendToKnowledge";
import ScheduleCard from "@/components/schedule/ScheduleCard";
import AssessmentPanel from "@/components/assessment/AssessmentPanel";

type Route = "unit" | "bid_desk" | "capability_gap" | "needs_owner";
type Data = {
  published: boolean; baseline: number | null; no_go: boolean; sent: boolean; units: Unit[];
  summary: { requirements: number; by_category: Record<string, number>; by_offering: Record<string, number>;
    suggested_units: Record<string, number>; sections: { section: string; count: number }[] };
  open_questions: {
    exceptions: { req_id: string; text: string; reason: string }[];
    needs_owner: { req_id: string; text: string; category: string; suggested: string[] }[];
    rule_warnings: { id: string; status: string; note: string }[];
    questions: { id: number; req_id: string; author: string; text: string }[];
  };
  participation: { id: number; units: string[]; rationale: string; decided_by: string } | null;
  routing: { req_id: string; text: string; category: string; section: string; route: Route;
    units: { bu: string; product_id: string | null; specialists: string[] }[] }[];
  progress: Record<string, { total: number; submitted: number; validated: number }>;
};
const BID_DESK = "Bid desk (commercial and submission items)";
const ROUTE: Record<Route, string> = { unit: "Business unit", bid_desk: BID_DESK, capability_gap: "Capability gap (non-compliant)", needs_owner: "Needs an owner" };

export default function AssessmentPage() {
  const { id } = useParams<{ id: string }>();
  const toast = useToast();
  const bm = isBidManager(useMe()); // participation, routing and sending are the bid manager's (16.6)
  const { data, error, reload } = useApi<Data>(`/api/bids/${id}/assessment`);
  const { data: sent, reload: reloadSent } = useApi<Record<string, string>>(`/api/bids/${id}/knowledge`); // A-11
  const [busy, setBusy] = useState<string>(); // one action at a time: no double participation or dispatch
  if (error) return <Alert kind="error" title="Could not load the assessment.">{error}</Alert>;
  if (!data) return <Skeleton lines={5} />;
  const { summary: s, open_questions: q, participation: part } = data;
  const open = q.exceptions.length + q.needs_owner.length + q.rule_warnings.length + q.questions.length;
  const count = (route: Route) => data.routing.filter((r) => r.route === route).length;

  const run = <T,>(label: string, request: Promise<T>, done: (r: T) => void) => {
    setBusy(label);
    request.then((r) => { done(r); return reload(); }, (e) => toast.error(errorMessage(e))).finally(() => setBusy(undefined));
  };
  const statusChanged = () => window.dispatchEvent(new Event(STATUS_EVENT));
  const recordParticipation = (form: FormData) =>
    run("participation", post(`/api/bids/${id}/participation`, { units: form.getAll("units"), rationale: form.get("rationale") }),
      () => toast.success("Participation recorded."));
  const recordGap = (reqId: string, form: FormData) =>
    run("gap", post(`/api/bids/${id}/requirements/${reqId}/capability-gap`, { reason: form.get("reason") }),
      () => toast.success(`${reqId}: capability gap recorded (non-compliant, with the reason).`));
  const send = () => run("send", post<{ created: number; needs_owner: number }>(`/api/bids/${id}/dispatch`), (r) => {
    toast.success((r.created ? `${r.created} new assignment(s) sent to the units.` : "Nothing new to send: every unit already has its work.")
      + (r.needs_owner ? ` ${r.needs_owner} product requirement(s) need an owner and were not sent.` : ""));
    statusChanged();
  });

  return (
    <div className="decisions">
      <PageHead level={2} title="Assessment"
        help="Review the bid summary and the open questions, choose the participating business units, check the routing, then send the register for assessment. Each unit's specialists answer in My work; the go/no-go follows on the Bid decision step." />

      <section className="card" data-tour="asm-summary">
        <div className="card-head"><h2>Bid summary</h2>
          <span className="muted">{s.requirements} requirement(s) in the register · {data.published ? `frozen as baseline ${data.baseline}` : "not frozen yet: read the RFP first"}</span></div>
        {/* A-24 (C-20): each count opens Traceability filtered to it (?category= / ?offering=) */}
        <p>By category: {Object.entries(s.by_category).map(([k, v]) => <Link key={k} className="chip" href={`/opportunities/${id}/trace?category=${encodeURIComponent(k)}`}>{k} {v}</Link>)}</p>
        <p>By offering type: {Object.entries(s.by_offering).map(([k, v]) => (
          <Link key={k} href={`/opportunities/${id}/trace?offering=${encodeURIComponent(k)}`}><StatusBadge status={k} kind="offering" label={`${offeringLabel(k)} ${v}`} /></Link>))}</p>
        {s.sections.length > 0 && <p>Major sections: {s.sections.map((x) => `${x.section} (${x.count})`).join(" · ")}</p>}
        <p>Suggested units: {Object.entries(s.suggested_units).map(([k, v]) => <strong key={k}>{k} ({v}) </strong>)}
          {Object.keys(s.suggested_units).length === 0 && "none yet: run matching in Traceability"}</p>
      </section>

      <AssessmentPanel oppId={id} />

      <section className="card" data-tour="asm-open-questions">
        <div className="card-head"><h2>Open questions</h2><span className="muted">{open === 0 ? "None." : `${open} to look at`}</span></div>
        {q.exceptions.length > 0 && <><h3>Source not verified ({q.exceptions.length})</h3>
          <ul className="per-req">{q.exceptions.map((e) => <li key={e.req_id}><span className="mono">{e.req_id}</span> {e.text} <span className="muted">{e.reason}</span></li>)}</ul>
          <p className="muted">Link them to their lines or dismiss them on the <Link href={`/opportunities/${id}/trace`}>Requirement Traceability</Link> step.</p></>}
        {q.needs_owner.length > 0 && <div data-tour="asm-needs-owner"><h3>Needs an owner ({q.needs_owner.length})</h3>
          <p className="muted">Product requirements no participating unit holds are not sent. Assign a unit in Traceability (pane 3), let the matched unit take part, or record a capability gap: why no unit can offer it.</p>
          <ul className="per-req">{q.needs_owner.map((o) => <li key={o.req_id}>
            <Link className="mono" href={`/opportunities/${id}/trace#${o.req_id}`}>{o.req_id}</Link> {o.text}
            {o.suggested.length > 0 && <span className="muted"> (matched to {o.suggested.join(", ")}, not taking part)</span>}
            {bm && <form className="inline" action={(f) => recordGap(o.req_id, f)}>
              <label><span className="sr-only">Why no unit can offer {o.req_id}</span><input name="reason" required placeholder="Capability gap: why no unit can offer it" /></label>
              <button className="secondary sm" disabled={!!busy}>Record capability gap</button></form>}
          </li>)}</ul></div>}
        {q.rule_warnings.length > 0 && <><h3>Engineering rule warnings ({q.rule_warnings.length})</h3>
          <ul className="per-req">{q.rule_warnings.map((r) => <li key={r.id}><span className="mono">{r.id}</span> <StatusBadge status={r.status} /> {r.note}</li>)}</ul></>}
        {q.questions.length > 0 && <><h3>Questions not yet closed ({q.questions.length})</h3>
          <ul className="per-req">{q.questions.map((c) => <li key={c.id}><Link className="mono" href={`/opportunities/${id}/trace#${c.req_id}`}>{c.req_id}</Link> <strong>{c.author}</strong>: {c.text}</li>)}</ul></>}
      </section>

      <section className="card" data-tour="asm-participation">
        <div className="card-head"><h2>1. Which business units take part?</h2>
          {part && <span className="muted">Recorded by <strong>{part.decided_by}</strong>: {part.units.join(", ")}</span>}</div>
        {part && <p>{part.rationale}
          {part.rationale && <> <SendToKnowledge kind="decision" refId={part.id} status={sent?.[`decision:${part.id}`]} onSent={reloadSent} /></>}</p>}
        <form className="form" action={recordParticipation}>
          <fieldset className="dec-units"><legend className="sr-only">Business units</legend>
            {data.units.map((u) => (
              <label key={u.code} className="check">
                <input type="checkbox" name="units" value={u.code} defaultChecked={part ? part.units.includes(u.code) : u.code in s.suggested_units} /> {u.name}
              </label>))}
          </fieldset>
          <label>Rationale <input name="rationale" /></label>
          <button disabled={!!busy || !bm}>Record participation</button>
          {busy === "participation" && <Busy label="Recording…" />}
          {!bm && <span className="muted">Only the bid manager records participation.</span>}
        </form>
      </section>

      <section className="card" data-tour="asm-routing">
        <div className="card-head"><h2>Routing</h2>
          <span className="muted">{count("unit")} to units · {count("bid_desk")} to the bid desk · {count("capability_gap")} capability gap(s) · {count("needs_owner")} need an owner{part ? "" : " (preview with the suggested units)"}</span></div>
        <details><summary>Requirement → unit → specialists ({data.routing.length})</summary>
          <div className="table-scroll"><table className="dense">
            <thead><tr><th>Requirement</th><th>Category</th><th>Route</th><th>Unit and product</th><th>Specialists</th></tr></thead>
            <tbody>{data.routing.map((r) => (
              <tr key={r.req_id}><td><Link className="mono" href={`/opportunities/${id}/trace#${r.req_id}`}>{r.req_id}</Link> {r.text}</td>
                <td>{r.category}</td><td className={r.route === "needs_owner" ? "warn" : undefined}>{ROUTE[r.route]}</td>
                <td>{r.units.map((u) => <div key={u.bu}>{u.bu === "BID" ? "Bid desk" : u.bu}{u.product_id && <span className="mono muted"> {u.product_id}</span>}</div>)}</td>
                <td>{r.units.map((u) => <div key={u.bu}>{u.specialists.join(", ") || "—"}</div>)}</td></tr>))}</tbody>
          </table></div></details>
      </section>

      <section className="card" data-tour="asm-send">
        <div className="card-head"><h2>2. Send for assessment</h2>
          <span className="muted">Sends each participating unit its work. Repeat after changing matches or participation: new work is sent, work that no longer fits is withdrawn.</span></div>
        <div className="row">
          <button disabled={!!busy || !part || data.no_go || !bm || !data.published} onClick={send} data-tour="asm-send-button">Send for assessment</button>
          {!data.published && <span className="muted">The register is frozen automatically when the RFP has been read (RFP step).</span>}
          {busy === "send" && <Busy label="Sending…" />}
          {!part && <span className="muted">Record which business units take part first.</span>}
          {data.no_go && <span className="muted">The bid is marked no-go: nothing is sent until a go decision resumes it.</span>}
          {part && !data.no_go && !bm && <span className="muted">Only the bid manager sends the bid for assessment.</span>}
        </div>
        {data.sent && <><h3>Progress per unit</h3>
          <table className="dense" data-tour="asm-progress"><thead><tr><th>Unit</th><th className="num">Items</th><th className="num">Answered</th><th className="num">Validated</th></tr></thead>
            <tbody>{Object.entries(data.progress).map(([bu, p]) => (
              <tr key={bu}><td><Link href={`/inbox/${bu}`}>{bu === "BID" ? BID_DESK : bu}</Link></td>
                <td className="num">{p.total}</td><td className="num">{p.submitted}</td><td className="num">{p.validated}</td></tr>))}</tbody></table>
          <p className="muted">When the units have answered, the bid manager decides on the <Link href={`/opportunities/${id}/decisions`}>Bid decision</Link> step.</p></>}
      </section>

      <ScheduleCard oppId={id} />
    </div>
  );
}
