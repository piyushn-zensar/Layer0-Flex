"use client";
// A business unit's work package: checklist response per requirement, then validation.  Owner: Atharv.
// The unit's designer / engineer answers its technical items and the unit manager the others (bid desk: the bid manager);
// the unit manager validates the technical answers, the bid manager the others (workflow.json, A-17, 19 Oct 2026), and
// the bid manager may return any answer with a question.
// A-07: links to the main RFP and each line's highlighted source; returned items reopen with the note; "Submit all".
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { api, errorMessage, isBidManager, isReader, post, useApi, useMe } from "@/lib/api";
import { TERMS, complianceLabel, examplesLabel, formatDate, solutionLabel, type Assignment, type Part, type Requirement, type Solution, type Unit } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import KnowledgeReview from "@/components/knowledge/KnowledgeReview";
import UnitCompletion from "@/components/schedule/UnitCompletion";
import { Alert, Busy, EmptyState, Skeleton, StatusBadge, useToast } from "@/components/ui";

// C-12 response fields (A-18): every assignment row carries them; null until a unit fills them in
type Fields = { reason: string | null; conditions: string | null; workaround: string | null; next_steps: string | null };
// may: what the signed-in user may do with the row, from workflow.json with role and unit from the token (A-17, C-25)
type Item = Assignment & Fields & { requirement: Requirement | null; open_questions: number; may: { answer: boolean; validate: boolean; return: boolean };
  solution: Solution | null; // C-40: the dispatched solution, worded at solution level (product_ref keeps the family id)
  parts?: Part[] }; // a group's approved sub-requirements with their current (corrected) text; absent on older data
const FIELDS: { name: keyof Fields; label: string; hint?: string }[] = [
  { name: "conditions", label: "Conditions" }, { name: "workaround", label: "Proposed change", hint: "required for compliant with changes" },
  { name: "next_steps", label: "Next steps" }];
type Data = { bu: string; unit: Unit | null; compliance: string[]; items: Item[] };
type Portfolio = { opp: { id: string }; progress: Record<string, { total: number; submitted: number; validated: number }> }[];

const BID_DESK = "Bid desk (commercial and submission items)";

// A-21 (C-16): an assignment's history, loaded when it is opened. before / after hold only what the event changed.
type HistoryEvent = { id: number; at: string; actor: string; action: string; note: string; before: Record<string, string | null>; after: Record<string, string | null> };
const ACTIONS: Record<string, string> = { assigned: "assigned it", reopened: "reopened it", responded: "submitted an answer",
  validated: "validated it", returned: "returned it", withdrawn: "withdrew it", capability_gap: "recorded a capability gap" };
const CHANGE_LABELS: Record<string, string> = { compliance: "Compliance", product_ref: TERMS.solution, response: "How it is met", reason: "Reason",
  conditions: "Conditions", workaround: "Proposed change", next_steps: "Next steps" };

// A-22 (C-17): questions and comments on a requirement; an open question blocks completion until it is closed.
type Note = { id: number; author: string; text: string; kind: string; status: string; closed_by: string | null };

function Questions({ oppId, reqId, assignmentId, open, me, bm, onChanged }:
  { oppId: string; reqId: string; assignmentId: number; open: number; me: string; bm: boolean; onChanged: () => void }) {
  const toast = useToast();
  const [notes, setNotes] = useState<Note[]>();
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);
  const readOnly = isReader(useMe()); // the administrator reads only
  const load = () => api<Note[]>(`/api/bids/${oppId}/comments?req_id=${encodeURIComponent(reqId)}`).then(setNotes, (e) => setError(errorMessage(e)));
  const act = (request: Promise<unknown>, done: string) => {
    setBusy(true);
    request.then(() => { toast.success(done); onChanged(); return load(); }, (e) => toast.error(errorMessage(e))).finally(() => setBusy(false));
  };
  return (
    <details className="inbox-questions" onToggle={(e) => { if (e.currentTarget.open && !notes) load(); }}>
      <summary>Questions and comments{open > 0 && <> · <span className="warn">{open} open question(s)</span></>}</summary>
      {error && <div className="warn">{error}</div>}
      {!notes && !error && <Busy label="Loading…" />}
      {notes?.length === 0 && <p className="muted">None yet.</p>}
      {notes && notes.length > 0 && <ol>{notes.map((c) => (
        <li key={c.id}><strong>{c.author}</strong>{" "}
          <span className="muted">({c.kind}{c.status === "closed" ? `, closed by ${c.closed_by}` : c.kind === "question" ? ", open" : ""})</span>: {c.text}
          {c.status === "open" && c.kind === "question" && (c.author === me || bm) &&
            <> <button className="secondary sm" disabled={busy} onClick={() => act(post(`/api/comments/${c.id}/close`), "Question closed.")}>Close</button></>}
        </li>))}</ol>}
      <form className="form compact" onSubmit={(e) => {
        e.preventDefault();
        const form = e.currentTarget, f = new FormData(form);
        act(post(`/api/bids/${oppId}/comments`, { req_id: reqId, assignment_id: assignmentId, kind: f.get("kind"), text: f.get("text") })
          .then(() => form.reset()), f.get("kind") === "question" ? "Question sent." : "Comment added.");
      }}>
        <label><span className="sr-only">Question or comment</span>
          <select name="kind" defaultValue="question"><option value="question">Question (open until closed)</option><option value="comment">Comment</option></select></label>
        <label><span className="sr-only">Text</span><textarea name="text" rows={2} required placeholder="Ask a question or add a comment" /></label>
        <button className="secondary sm" disabled={busy || readOnly} title={readOnly ? "The administrator reads only." : undefined}>Send</button>
      </form>
    </details>
  );
}

function History({ id }: { id: number }) {
  const [events, setEvents] = useState<HistoryEvent[]>();
  const [error, setError] = useState<string>();
  const load = (open: boolean) => { if (open && !events) api<HistoryEvent[]>(`/api/assignments/${id}/history`).then(setEvents, (e) => setError(errorMessage(e))); };
  const show = (k: string, v: string | null) => (v == null || v === "" ? "—" : k === "compliance" ? answerLabel(v) : v);
  return (
    <details className="inbox-history" onToggle={(e) => load(e.currentTarget.open)}>
      <summary>History</summary>
      {error && <div className="warn">{error}</div>}
      {!events && !error && <Busy label="Loading…" />}
      {events && <ol>{events.map((ev) => (
        <li key={ev.id}><span className="muted">{formatDate(ev.at, true)}</span> <strong>{ev.actor}</strong> {ACTIONS[ev.action] ?? ev.action}
          {ev.note && <>: {ev.note}</>}
          {Object.keys(ev.after).filter((k) => k in CHANGE_LABELS).map((k) => (
            <div key={k} className="muted">{CHANGE_LABELS[k]}: {show(k, ev.before[k])} → {show(k, ev.after[k])}</div>))}
        </li>))}</ol>}
    </details>
  );
}
const open = (a: Item) => a.status === "assigned" || a.status === "returned";
// Stored values stay; screens show Compliant / Partially compliant / Compliant with changes / Non-compliant (16.2, C-43). "exception" is retired.
const answerLabel = (c: string) => (c === "exception" ? "Exception (earlier value)" : complianceLabel(c));

export default function InboxPage() {
  const { bu } = useParams<{ bu: string }>();
  const { data, error, reload } = useApi<Data>(`/api/inbox/${bu}`);
  const { data: portfolio } = useApi<Portfolio>("/api/portfolio");
  const signedIn = useMe();
  const me = signedIn?.name ?? "", bm = isBidManager(signedIn);
  // unit switcher: answers waiting for validation, only on the units the signed-in person validates (the bid manager: any)
  const validates = (u: string) => bm || (signedIn?.role === "product_manager" && signedIn.bu === u);
  // work-package tabs: a unit role sees its own unit only; the bid manager and the administrator see every unit (21 Oct review)
  const showsUnit = (u: string) => !!signedIn && (bm || isReader(signedIn) || signedIn.bu === u);
  const toast = useToast();
  const [busy, setBusy] = useState<number | "all">();      // what is being saved: no double submit
  const [returning, setReturning] = useState<number>();     // the item whose return note is being written
  const [note, setNote] = useState("");
  const [results, setResults] = useState<Record<number, string>>({});  // "Submit all" outcome per row
  if (error) return <div className="content"><PageHead title="My work" /><Alert kind="error">Could not load this work package: {error}</Alert></div>;
  if (!data) return <div className="content"><PageHead title="My work" /><Skeleton lines={4} /></div>;

  const canAnswer = data.items.some((a) => a.may.answer);
  const canValidate = data.items.some((a) => a.may.validate || a.may.return);
  const opportunities = [...new Set(data.items.map((a) => a.opportunity_id))];
  const openCount = data.items.filter((a) => a.may.answer).length;
  const toValidate = data.items.filter((a) => a.may.validate).length;
  // Walkthrough targets (data-tour): the first open, submitted and returned rows carry stable ids; nothing else changes.
  // While the walkthrough runs it names its opportunity on <html data-tour-opp>, and that opportunity's rows come first.
  const focus = typeof document !== "undefined" ? document.documentElement.getAttribute("data-tour-opp") : null;
  const firstOf = (test: (a: Item) => boolean) => (data.items.find((a) => test(a) && a.opportunity_id === focus) ?? data.items.find(test))?.id;
  // Every unit with work, and per bid how many of its answers wait for validation (progress.submitted includes validated ones).
  const waiting: Record<string, Record<string, number>> = { BID: {} };
  for (const o of portfolio ?? []) for (const [u, p] of Object.entries(o.progress)) {
    waiting[u] = waiting[u] ?? {};
    if (p.submitted > p.validated) waiting[u][o.opp.id] = p.submitted - p.validated;
  }
  const waitingLabel = (u: string) => { const w = Object.entries(waiting[u]); const n = w.reduce((s, [, k]) => s + k, 0);
    return validates(u) && n > 0 ? `${n} to validate (${w.map(([o]) => o).join(", ")})` : ""; };
  const allDone = data.items.length > 0 && data.items.every((a) => a.status === "validated");
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
    for (const a of data.items.filter((x) => x.may.answer)) {
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
      <PageHead title={`My work: ${data.unit?.name ?? BID_DESK}`}
        help="Each line is a requirement assigned to this unit. Mark it compliant, partially compliant, compliant with changes (a deviation from the requested specification) or non-compliant; say how it is met; give a reason unless it is compliant, and the proposed change for compliant with changes; add conditions or next steps where they apply, then submit. The unit manager validates the technical answers and the bid manager the others; the bid manager may return any answer with a question.">
        {canAnswer && openCount > 0 && <button disabled={busy !== undefined} onClick={submitAll} data-tour="inbox-submit-all">Submit all answered rows</button>}
        {busy === "all" && <Busy label="Sending…" />}
      </PageHead>
      <UnitCompletion bu={bu} />
      <KnowledgeReview />
      <nav className="row inbox-links" aria-label="Work packages" data-tour="inbox-units">
        <span>Work package:</span>
        {Object.keys(waiting).filter(showsUnit).sort((a, b) => (a === "BID" ? -1 : b === "BID" ? 1 : a.localeCompare(b))).map((u) => (
          <Link key={u} href={`/inbox/${u}`} className={`chip${u === bu ? " on" : ""}`} aria-current={u === bu ? "page" : undefined}>
            {u === "BID" ? BID_DESK : u}{waitingLabel(u) && <span>{waitingLabel(u)}</span>}
          </Link>))}
      </nav>
      {opportunities.length > 0 && (
        <div className="row inbox-links" data-tour="inbox-links">
          <span>Open the RFP:</span>
          {opportunities.map((o) => <Link key={o} className="button secondary sm" href={`/opportunities/${o}/trace`} data-tour={`inbox-open-rfp-${o}`}>{o}</Link>)}
          {data.unit && <>
            <span className="inbox-sep" aria-hidden="true" />
            <span>Download hand-off file:</span>
            {opportunities.map((o) => <a key={o} className="button secondary sm" href={`/api/bids/${o}/handoff/${bu}`} data-tour={`inbox-handoff-${o}`}>{o}</a>)}
            <span className="muted">Starting points for people, not a configuration or a design.</span>
          </>}
        </div>)}
      {allDone ? <div data-tour="inbox-readonly"><Alert kind="info">All {data.items.length} answers are submitted and validated: nothing to do.</Alert></div>
        : !canAnswer && !canValidate && <div data-tour="inbox-readonly"><Alert kind="info">You are signed in as {me}: you can read this work package but not act on it. A unit&apos;s technical items are answered by its designers / engineers and validated by its unit manager; its other items are answered by the unit manager and validated by the bid manager.</Alert></div>}
      {canAnswer && openCount > 0 && <p className="muted" data-tour="inbox-open-count">{openCount} open row(s). “Submit all answered rows” sends every open row where “How it is met” is filled in.</p>}
      {canValidate && toValidate > 0 && <p className="muted" data-tour="inbox-to-validate">{toValidate} submitted answer(s) waiting for validation.</p>}
      {data.items.length === 0 ? <EmptyState title="Nothing assigned" hint="Requirements appear here once the bid manager dispatches a bid to this unit." /> : (
      <table className="inbox stack-sm" data-tour="inbox-table">
        <thead><tr><th>Bid</th><th>Requirement</th><th>Response</th><th>Status</th></tr></thead>
        <tbody>
          {data.items.map((a) => {
            const t = (id: string) => (a.id === firstOpen ? id : undefined);        // first open row's targets
            const v = (id: string) => (a.id === firstSubmitted ? id : undefined);   // first submitted row's targets
            return (
            <tr key={a.id} data-tour={t("inbox-row-open") ?? v("inbox-row-submitted") ?? `inbox-row-${a.id}`}>
              <td className="mono"><Link href={`/opportunities/${a.opportunity_id}/trace#${a.req_id}`}>{a.opportunity_id}<br />{a.req_id}</Link></td>
              <td data-tour={t("inbox-req-cell")}>{a.requirement ? <>{a.requirement.text}
                {(a.parts?.length ?? 0) > 0 && <ul className="parts">{a.parts!.map((p) => <li key={p.req_id}><span className="mono">{p.req_id}</span> {p.text}</li>)}</ul>}
                <div className="quote">“{a.requirement.quote}”</div>
                {a.requirement.provenance === "UNANCHORED" // UX-14: the same badge as the Requirements page, no "not found in source" link
                  ? <StatusBadge status="medium" kind="severity" label="Source not verified" title="Quote not located on the page; check the source manually" />
                  : <Link className="muted" href={`/opportunities/${a.opportunity_id}/trace#${a.req_id}`} data-tour={t("inbox-source-link")}>{a.requirement.source}: show highlighted source</Link>}</>
                : <span className="warn">This requirement no longer exists in the bid.</span>}
                <Questions oppId={a.opportunity_id} reqId={a.req_id} assignmentId={a.id} open={a.open_questions} me={me} bm={bm} onChanged={reload} /></td>
              <td data-label="Response">
                {a.may.answer ? (
                  <form className="form compact" data-assignment={a.id} aria-busy={busy === a.id} data-tour={t("inbox-form")}
                    onSubmit={(e) => { e.preventDefault(); const f = new FormData(e.currentTarget); run(a.id, () => answer(a, f), `${a.req_id} submitted for validation.`); }}>
                    {a.status === "returned" && <div data-tour={a.id === firstReturned ? "inbox-returned-note" : undefined}><Alert kind="warn" title="Returned">by {a.validated_by}: {a.validation_note}</Alert></div>}
                    <label data-tour={t("inbox-compliance")}><span className="sr-only">Compliance</span>
                      <select name="compliance" defaultValue={a.compliance ?? "met"}>{data.compliance.map((c) => <option key={c} value={c}>{answerLabel(c)}</option>)}</select></label>
                    {/* C-40: shown, not edited; no product_ref is posted, so the dispatched one is kept */}
                    {a.solution && <div className="muted" data-tour={t("inbox-product")}>{TERMS.solution}: {solutionLabel(a.solution)}{a.solution.examples.length > 0 && <> · {examplesLabel(a.solution)}</>}</div>}
                    <label data-tour={t("inbox-response")}><span className="sr-only">How it is met</span>
                      <textarea name="response" rows={2} defaultValue={a.response} placeholder="How it is met" /></label>
                    <label data-tour={t("inbox-reason")}><span className="sr-only">Reason</span>
                      <textarea name="reason" rows={2} defaultValue={a.reason ?? ""} placeholder="Reason: what is not met or what changes, and why (required unless compliant)" /></label>
                    {FIELDS.map((f) => <label key={f.name}><span className="sr-only">{f.label}</span>
                      <input name={f.name} defaultValue={a[f.name] ?? ""} placeholder={`${f.label} (${f.hint ?? "optional"})`} /></label>)}
                    <div className="inline">
                      <button className="sm" disabled={busy !== undefined} data-tour={t("inbox-submit")}>Submit</button>
                      {busy === a.id && <Busy label="Sending…" />}
                    </div>
                  </form>
                ) : (
                  // UX-04: compliance, solution and status are separate blocks, never adjacent text
                  <div data-tour={v("inbox-answer-submitted")}>{a.compliance && <strong>{answerLabel(a.compliance)}</strong>}{a.solution && <div className="muted">{TERMS.solution}: {solutionLabel(a.solution)}</div>}
                    {a.response && <div className="muted">{a.response}</div>}
                    {a.reason && <div className="muted"><strong>Reason:</strong> {a.reason}</div>}
                    {FIELDS.map((f) => a[f.name] && <div key={f.name} className="muted"><strong>{f.label}:</strong> {a[f.name]}</div>)}
                    {!a.compliance && <div className="muted">not answered yet</div>}</div>
                )}
                {results[a.id] && <div className={results[a.id] === "sent" ? "ok" : "warn"}>{results[a.id]}</div>}
              </td>
              <td data-label="Status" data-tour={v("inbox-validate-cell") ?? t("inbox-status-cell")}>
                <StatusBadge status={a.status} />{a.validated_by && a.status === "validated" && <div className="muted">by {a.validated_by}</div>}
                <History id={a.id} />
                {(a.may.validate || a.may.return) && (returning === a.id ? (
                  <div className="form compact inbox-return" data-tour={v("inbox-return-form")}>
                    <label><span className="sr-only">Why is it returned?</span>
                      <textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} placeholder={a.may.validate ? "Why is it returned? The unit sees this note." : "Your question: the unit sees it and answers again."} autoFocus data-tour={v("inbox-return-note")} /></label>
                    <div className="inline">
                      <button className="danger sm" disabled={busy !== undefined || !note.trim()} data-tour={v("inbox-return-send")}
                        onClick={() => run(a.id, () => post(`/api/assignments/${a.id}/validate`, { ok: false, note }), `${a.req_id} returned to the unit.`)}>Return with note</button>
                      <button className="secondary sm" disabled={busy !== undefined} onClick={() => { setReturning(undefined); setNote(""); }}>Cancel</button>
                      {busy === a.id && <Busy label="Saving…" />}
                    </div>
                  </div>
                ) : (
                  <div className="inline inbox-validate">
                    {a.may.validate && <button className="sm" disabled={busy !== undefined} data-tour={v("inbox-validate")} onClick={() => run(a.id, () => post(`/api/assignments/${a.id}/validate`, { ok: true, note: "" }), `${a.req_id} validated.`)}>Validate</button>}
                    <button disabled={busy !== undefined} className="secondary sm" data-tour={v("inbox-return")} onClick={() => { setReturning(a.id); setNote(""); }}>{a.may.validate ? "Return" : "Return with a question"}</button>
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
