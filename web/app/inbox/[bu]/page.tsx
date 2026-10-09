"use client";
// A business unit's work package: checklist response per requirement, then validation.  Owner: Atharv.
// The unit's product manager / design engineer answers (bid desk: the Bid Manager); only the Bid Manager validates.
// A-07: links to the main RFP and each line's highlighted source; returned items reopen with the note; "Submit all".
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { currentActor, post, useApi } from "@/lib/api";
import type { Assignment, Requirement, Unit } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";

type Item = Assignment & { requirement: Requirement | null };
type Data = { bu: string; unit: Unit | null; compliance: string[]; items: Item[] };

const BID_MANAGER = "Bid Manager";
const open = (a: Item) => a.status === "assigned" || a.status === "returned";

export default function InboxPage() {
  const { bu } = useParams<{ bu: string }>();
  const { data, error, reload } = useApi<Data>(`/api/inbox/${bu}`);
  const [busy, setBusy] = useState<number | "all">();      // what is being saved: no double submit
  const [returning, setReturning] = useState<number>();     // the item whose return note is being written
  const [note, setNote] = useState("");
  const [results, setResults] = useState<Record<number, string>>({});  // "Submit all" outcome per row
  if (error) return <p className="content warn">Could not load this work package: {error}</p>;
  if (!data) return <p className="content">Loading…</p>;

  const me = currentActor();
  const canAnswer = data.unit ? [data.unit.product_manager, data.unit.design_engineer].includes(me) : me === BID_MANAGER;
  const canValidate = me === BID_MANAGER;
  const opportunities = [...new Set(data.items.map((a) => a.opportunity_id))];
  const answer = (a: Item, form: FormData) => post(`/api/assignments/${a.id}/respond`, Object.fromEntries(form));
  const run = (key: number, request: () => Promise<unknown>) => {
    setBusy(key);
    request().then(() => { setReturning(undefined); setNote(""); return reload(); }, alert)  // on failure typed text stays
      .finally(() => setBusy(undefined));
  };
  const submitAll = async () => {  // every open row with an answer typed in, one after the other
    setBusy("all");
    const out: Record<number, string> = {};
    for (const a of data.items.filter(open)) {
      const form = document.querySelector<HTMLFormElement>(`form[data-assignment="${a.id}"]`);
      if (!form || !String(new FormData(form).get("response") ?? "").trim()) continue;
      try { await answer(a, new FormData(form)); out[a.id] = "sent"; }
      catch (e) { out[a.id] = `not sent: ${String(e).replace(/^Error: \d+: /, "")}`; }
    }
    setResults(out);
    setBusy(undefined);
    reload();
    if (Object.keys(out).length === 0) alert("Nothing to send: type an answer in at least one row first.");
  };

  return (
    <div className="content">
      <PageHead title={`My work: ${data.unit?.name ?? "Bid desk (bid manager)"}`} />
      <p className="page-help">Each line is a requirement assigned to this unit. Mark it met, partly met, not met or an exception,
        say what meets it, then submit. The bid manager validates or returns it with a note.</p>
      {opportunities.length > 0 && <p>Open the RFP: {opportunities.map((o) =>
        <Link key={o} className="button secondary" href={`/opportunities/${o}/trace`}>{o}</Link>)}</p>}
      {data.unit && opportunities.length > 0 && <p>Hand-off for this unit&apos;s systems (JSON: CPQ seed, basis of design, specialist queue): {opportunities.map((o) =>
        <a key={o} className="button secondary" href={`/api/opportunities/${o}/handoff/${bu}`}>{o}</a>)}
        {" "}<span className="muted">Starting points for people, not a configuration or a design.</span></p>}
      {!canAnswer && !canValidate && <p className="muted">You are acting as {me}: you can read this work package but not answer it.</p>}
      {canAnswer && data.items.some(open) && <p><button disabled={busy !== undefined} onClick={submitAll}>Submit all answered rows</button>{" "}
        <span className="muted">Sends every open row where “How it is met” is filled in.</span></p>}
      <table>
        <thead><tr><th>Opportunity</th><th>Requirement</th><th>Response</th><th>Status</th></tr></thead>
        <tbody>
          {data.items.map((a) => (
            <tr key={a.id}>
              <td className="mono"><Link href={`/opportunities/${a.opportunity_id}/trace#${a.req_id}`}>{a.opportunity_id}<br />{a.req_id}</Link></td>
              <td>{a.requirement ? <>{a.requirement.text}<div className="quote">“{a.requirement.quote}”</div>
                <Link className="muted" href={`/opportunities/${a.opportunity_id}/trace#${a.req_id}`}>{a.requirement.source}: show highlighted source</Link></>
                : <span className="warn">This requirement no longer exists in the opportunity.</span>}</td>
              <td>
                {canAnswer && open(a) ? (
                  <form className="form compact" data-assignment={a.id} onSubmit={(e) => { e.preventDefault(); const f = new FormData(e.currentTarget); run(a.id, () => answer(a, f)); }}>
                    {a.status === "returned" && <div className="warn">Returned by {a.validated_by}: {a.validation_note}</div>}
                    <label><span className="sr-only">Compliance</span>
                      <select name="compliance" defaultValue={a.compliance ?? "met"}>{data.compliance.map((c) => <option key={c}>{c}</option>)}</select></label>
                    <label><span className="sr-only">Product or configuration</span>
                      <input name="product_ref" defaultValue={a.product_ref ?? ""} placeholder="Product / configuration" /></label>
                    <label><span className="sr-only">How it is met</span>
                      <textarea name="response" rows={2} defaultValue={a.response} placeholder="How it is met" /></label>
                    <button disabled={busy !== undefined}>Submit</button>
                  </form>
                ) : (
                  <div>{a.compliance && <strong>{a.compliance}</strong>} {a.product_ref}
                    {a.response && <div className="muted">{a.response}</div>}
                    {!a.compliance && <span className="muted">not answered yet</span>}</div>
                )}
                {results[a.id] && <div className={results[a.id] === "sent" ? "ok" : "warn"}>{results[a.id]}</div>}
              </td>
              <td><span className="badge">{a.status}</span>{a.validated_by && a.status === "validated" && <div className="muted">by {a.validated_by}</div>}
                {canValidate && a.status === "submitted" && (returning === a.id ? (
                  <div className="form compact">
                    <label><span className="sr-only">Why is it returned?</span>
                      <textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Why is it returned? The unit sees this note." /></label>
                    <div className="inline">
                      <button disabled={busy !== undefined || !note.trim()} onClick={() => run(a.id, () => post(`/api/assignments/${a.id}/validate`, { ok: false, note }))}>Return with note</button>
                      <button className="secondary" onClick={() => { setReturning(undefined); setNote(""); }}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div className="inline">
                    <button disabled={busy !== undefined} onClick={() => run(a.id, () => post(`/api/assignments/${a.id}/validate`, { ok: true, note: "" }))}>Validate</button>
                    <button disabled={busy !== undefined} className="secondary" onClick={() => { setReturning(a.id); setNote(""); }}>Return</button>
                  </div>
                ))}
              </td>
            </tr>
          ))}
          {data.items.length === 0 && <tr><td colSpan={4} className="muted">Nothing assigned.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
