"use client";
// A business unit's work package: checklist response per requirement, then validation.  Owner: Atharv.
// The unit's product manager / design engineer answers (bid desk: the Bid Manager); only the Bid Manager validates.
// A-07: links to the main RFP and each line's highlighted source; returned items reopen with the note; "Submit all".
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { currentActor, errorMessage, post, useApi } from "@/lib/api";
import type { Assignment, Requirement, Unit } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { Alert, Busy, EmptyState, Skeleton, StatusBadge, useToast } from "@/components/ui";

type Item = Assignment & { requirement: Requirement | null };
type Data = { bu: string; unit: Unit | null; compliance: string[]; items: Item[] };

const BID_MANAGER = "Bid Manager";
const open = (a: Item) => a.status === "assigned" || a.status === "returned";

export default function InboxPage() {
  const { bu } = useParams<{ bu: string }>();
  const { data, error, reload } = useApi<Data>(`/api/inbox/${bu}`);
  const toast = useToast();
  const [busy, setBusy] = useState<number | "all">();      // what is being saved: no double submit
  const [returning, setReturning] = useState<number>();     // the item whose return note is being written
  const [note, setNote] = useState("");
  const [results, setResults] = useState<Record<number, string>>({});  // "Submit all" outcome per row
  if (error) return <div className="content"><PageHead title="My work" /><Alert kind="error">Could not load this work package: {error}</Alert></div>;
  if (!data) return <div className="content"><PageHead title="My work" /><Skeleton lines={4} /></div>;

  const me = currentActor();
  const canAnswer = data.unit ? [data.unit.product_manager, data.unit.design_engineer].includes(me) : me === BID_MANAGER;
  const canValidate = me === BID_MANAGER;
  const opportunities = [...new Set(data.items.map((a) => a.opportunity_id))];
  const openCount = data.items.filter(open).length;
  const toValidate = data.items.filter((a) => a.status === "submitted").length;
  // Walkthrough targets (data-tour): the first open, submitted and returned rows carry stable ids; nothing else changes.
  // While the walkthrough runs it names its opportunity on <html data-tour-opp>, and that opportunity's rows come first.
  const focus = typeof document !== "undefined" ? document.documentElement.getAttribute("data-tour-opp") : null;
  const firstOf = (test: (a: Item) => boolean) => (data.items.find((a) => test(a) && a.opportunity_id === focus) ?? data.items.find(test))?.id;
  const firstOpen = firstOf(open), firstSubmitted = firstOf((a) => a.status === "submitted"), firstReturned = firstOf((a) => a.status === "returned");
  const answer = (a: Item, form: FormData) => post(`/api/assignments/${a.id}/respond`, Object.fromEntries(form));
  const run = (key: number, request: () => Promise<unknown>, done: string) => {
    setBusy(key);
    request().then(() => { setReturning(undefined); setNote(""); toast.success(done); return reload(); }, (e) => toast.error(errorMessage(e)))  // on failure typed text stays
      .finally(() => setBusy(undefined));
  };
  const submitAll = async () => {  // every open row with an answer typed in, one after the other
    setBusy("all");
    const out: Record<number, string> = {};
    for (const a of data.items.filter(open)) {
      const form = document.querySelector<HTMLFormElement>(`form[data-assignment="${a.id}"]`);
      if (!form || !String(new FormData(form).get("response") ?? "").trim()) continue;
      try { await answer(a, new FormData(form)); out[a.id] = "sent"; }
      catch (e) { out[a.id] = `not sent: ${errorMessage(e)}`; }
    }
    setResults(out);
    setBusy(undefined);
    reload();
    const sent = Object.values(out).filter((r) => r === "sent").length, failed = Object.keys(out).length - sent;
    if (Object.keys(out).length === 0) toast.info("Nothing to send: type an answer in at least one row first.");
    else if (failed) toast.error(`${sent} row(s) sent, ${failed} not sent; see the rows.`);
    else toast.success(`${sent} row(s) submitted for validation.`);
  };

  return (
    <div className="content">
      <PageHead title={`My work: ${data.unit?.name ?? "Bid desk (bid manager)"}`}
        help="Each line is a requirement assigned to this unit. Mark it met, partly met, not met or an exception, say what meets it, then submit. The bid manager validates or returns it with a note.">
        {canAnswer && openCount > 0 && <button disabled={busy !== undefined} onClick={submitAll} data-tour="inbox-submit-all">Submit all answered rows</button>}
        {busy === "all" && <Busy label="Sending…" />}
      </PageHead>
      {opportunities.length > 0 && (
        <div className="row inbox-links" data-tour="inbox-links">
          <span>Open the RFP:</span>
          {opportunities.map((o) => <Link key={o} className="button secondary sm" href={`/opportunities/${o}/trace`} data-tour={`inbox-open-rfp-${o}`}>{o}</Link>)}
          {data.unit && <>
            <span className="inbox-sep" aria-hidden="true" />
            <span>Hand-off for this unit&apos;s systems <span className="muted">(JSON: CPQ seed, basis of design, specialist queue)</span>:</span>
            {opportunities.map((o) => <a key={o} className="button secondary sm" href={`/api/opportunities/${o}/handoff/${bu}`} data-tour={`inbox-handoff-${o}`}>{o}</a>)}
            <span className="muted">Starting points for people, not a configuration or a design.</span>
          </>}
        </div>)}
      {!canAnswer && !canValidate && <div data-tour="inbox-readonly"><Alert kind="info">You are acting as {me}: you can read this work package but not answer it. Switch with “Acting as” in the top bar.</Alert></div>}
      {canAnswer && openCount > 0 && <p className="muted" data-tour="inbox-open-count">{openCount} open row(s). “Submit all answered rows” sends every open row where “How it is met” is filled in.</p>}
      {canValidate && toValidate > 0 && <p className="muted" data-tour="inbox-to-validate">{toValidate} submitted answer(s) waiting for validation.</p>}
      {data.items.length === 0 ? <EmptyState title="Nothing assigned" hint="Requirements appear here once the bid manager dispatches an opportunity to this unit." /> : (
      <table className="inbox" data-tour="inbox-table">
        <thead><tr><th>Opportunity</th><th>Requirement</th><th>Response</th><th>Status</th></tr></thead>
        <tbody>
          {data.items.map((a) => {
            const t = (id: string) => (a.id === firstOpen ? id : undefined);        // first open row's targets
            const v = (id: string) => (a.id === firstSubmitted ? id : undefined);   // first submitted row's targets
            return (
            <tr key={a.id} data-tour={t("inbox-row-open") ?? v("inbox-row-submitted") ?? `inbox-row-${a.id}`}>
              <td className="mono"><Link href={`/opportunities/${a.opportunity_id}/trace#${a.req_id}`}>{a.opportunity_id}<br />{a.req_id}</Link></td>
              <td data-tour={t("inbox-req-cell")}>{a.requirement ? <>{a.requirement.text}<div className="quote">“{a.requirement.quote}”</div>
                {a.requirement.provenance === "UNANCHORED" // UX-14: the same badge as the Requirements page, no "not found in source" link
                  ? <StatusBadge status="medium" kind="severity" label="unanchored" title="Quote not located on the page; check the source manually" />
                  : <Link className="muted" href={`/opportunities/${a.opportunity_id}/trace#${a.req_id}`} data-tour={t("inbox-source-link")}>{a.requirement.source}: show highlighted source</Link>}</>
                : <span className="warn">This requirement no longer exists in the opportunity.</span>}</td>
              <td>
                {canAnswer && open(a) ? (
                  <form className="form compact" data-assignment={a.id} aria-busy={busy === a.id} data-tour={t("inbox-form")}
                    onSubmit={(e) => { e.preventDefault(); const f = new FormData(e.currentTarget); run(a.id, () => answer(a, f), `${a.req_id} submitted for validation.`); }}>
                    {a.status === "returned" && <div data-tour={a.id === firstReturned ? "inbox-returned-note" : undefined}><Alert kind="warn" title="Returned">by {a.validated_by}: {a.validation_note}</Alert></div>}
                    <label data-tour={t("inbox-compliance")}><span className="sr-only">Compliance</span>
                      <select name="compliance" defaultValue={a.compliance ?? "met"}>{data.compliance.map((c) => <option key={c}>{c}</option>)}</select></label>
                    <label data-tour={t("inbox-product")}><span className="sr-only">Product or configuration</span>
                      <input name="product_ref" defaultValue={a.product_ref ?? ""} placeholder="Product / configuration" /></label>
                    <label data-tour={t("inbox-response")}><span className="sr-only">How it is met</span>
                      <textarea name="response" rows={2} defaultValue={a.response} placeholder="How it is met" /></label>
                    <div className="inline">
                      <button className="sm" disabled={busy !== undefined} data-tour={t("inbox-submit")}>Submit</button>
                      {busy === a.id && <Busy label="Sending…" />}
                    </div>
                  </form>
                ) : (
                  // UX-04: compliance, product and status are separate blocks, never adjacent text
                  <div data-tour={v("inbox-answer-submitted")}>{a.compliance && <strong>{a.compliance}</strong>}{a.product_ref && <> <span className="mono">{a.product_ref}</span></>}
                    {a.response && <div className="muted">{a.response}</div>}
                    {!a.compliance && <div className="muted">not answered yet</div>}</div>
                )}
                {results[a.id] && <div className={results[a.id] === "sent" ? "ok" : "warn"}>{results[a.id]}</div>}
              </td>
              <td data-tour={v("inbox-validate-cell") ?? t("inbox-status-cell")}>
                <StatusBadge status={a.status} />{a.validated_by && a.status === "validated" && <div className="muted">by {a.validated_by}</div>}
                {canValidate && a.status === "submitted" && (returning === a.id ? (
                  <div className="form compact inbox-return" data-tour={v("inbox-return-form")}>
                    <label><span className="sr-only">Why is it returned?</span>
                      <textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Why is it returned? The unit sees this note." autoFocus data-tour={v("inbox-return-note")} /></label>
                    <div className="inline">
                      <button className="danger sm" disabled={busy !== undefined || !note.trim()} data-tour={v("inbox-return-send")}
                        onClick={() => run(a.id, () => post(`/api/assignments/${a.id}/validate`, { ok: false, note }), `${a.req_id} returned to the unit.`)}>Return with note</button>
                      <button className="secondary sm" disabled={busy !== undefined} onClick={() => { setReturning(undefined); setNote(""); }}>Cancel</button>
                      {busy === a.id && <Busy label="Saving…" />}
                    </div>
                  </div>
                ) : (
                  <div className="inline inbox-validate">
                    <button className="sm" disabled={busy !== undefined} data-tour={v("inbox-validate")} onClick={() => run(a.id, () => post(`/api/assignments/${a.id}/validate`, { ok: true, note: "" }), `${a.req_id} validated.`)}>Validate</button>
                    <button disabled={busy !== undefined} className="secondary sm" data-tour={v("inbox-return")} onClick={() => { setReturning(a.id); setNote(""); }}>Return</button>
                    {busy === a.id && <Busy label="Saving…" />}
                  </div>
                ))}
              </td>
            </tr>);
          })}
        </tbody>
      </table>)}
    </div>
  );
}
