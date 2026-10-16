"use client";
// A business unit's work package: checklist response per requirement, then validation.  Owner: Atharv.
// The unit's product manager / design engineer answers (bid desk: the Bid Manager); the unit's product manager validates
// (workflow.json, A-17) and the Bid Manager may return any answer with a question.
// A-07: links to the main RFP and each line's highlighted source; returned items reopen with the note; "Submit all".
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { api, errorMessage, post, useApi, useMe } from "@/lib/api";
import { complianceLabel, type Assignment, type Requirement, type Unit } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import KnowledgeReview from "@/components/knowledge/KnowledgeReview";
import UnitCompletion from "@/components/schedule/UnitCompletion";
import { Alert, Busy, EmptyState, Skeleton, StatusBadge, useToast } from "@/components/ui";

// C-12 response fields (A-18): every assignment row carries them; null until a unit fills them in
type Fields = { reason: string | null; conditions: string | null; workaround: string | null; next_steps: string | null };
type Item = Assignment & Fields & { requirement: Requirement | null; open_questions: number };
const FIELDS: { name: keyof Fields; label: string }[] = [
  { name: "conditions", label: "Conditions" }, { name: "workaround", label: "Workaround" }, { name: "next_steps", label: "Next steps" }];
type Data = { bu: string; unit: Unit | null; compliance: string[]; items: Item[] };
type Portfolio = { progress: Record<string, { total: number; submitted: number; validated: number }> }[];

const BID_MANAGER = "Bid Manager";
const BID_DESK = "Bid desk (commercial and submission items)";

// A-21 (C-16): an assignment's history, loaded when it is opened. before / after hold only what the event changed.
type HistoryEvent = { id: number; at: string; actor: string; action: string; note: string; before: Record<string, string | null>; after: Record<string, string | null> };
const ACTIONS: Record<string, string> = { assigned: "assigned it", reopened: "reopened it", responded: "submitted an answer",
  validated: "validated it", returned: "returned it", withdrawn: "withdrew it", capability_gap: "recorded a capability gap" };
const CHANGE_LABELS: Record<string, string> = { compliance: "Compliance", product_ref: "Product", response: "How it is met", reason: "Reason",
  conditions: "Conditions", workaround: "Workaround", next_steps: "Next steps" };

// A-22 (C-17): questions and comments on a requirement; an open question blocks completion until it is closed.
type Note = { id: number; author: string; text: string; kind: string; status: string; closed_by: string | null };

function Questions({ oppId, reqId, assignmentId, open, me, bm, onChanged }:
  { oppId: string; reqId: string; assignmentId: number; open: number; me: string; bm: boolean; onChanged: () => void }) {
  const toast = useToast();
  const [notes, setNotes] = useState<Note[]>();
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);
  const load = () => api<Note[]>(`/api/opportunities/${oppId}/comments?req_id=${encodeURIComponent(reqId)}`).then(setNotes, (e) => setError(errorMessage(e)));
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
        act(post(`/api/opportunities/${oppId}/comments`, { req_id: reqId, assignment_id: assignmentId, kind: f.get("kind"), text: f.get("text") })
          .then(() => form.reset()), f.get("kind") === "question" ? "Question sent." : "Comment added.");
      }}>
        <label><span className="sr-only">Question or comment</span>
          <select name="kind" defaultValue="question"><option value="question">Question (open until closed)</option><option value="comment">Comment</option></select></label>
        <label><span className="sr-only">Text</span><textarea name="text" rows={2} required placeholder="Ask a question or add a comment" /></label>
        <button className="secondary sm" disabled={busy}>Send</button>
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
        <li key={ev.id}><span className="muted">{new Date(ev.at).toLocaleString()}</span> <strong>{ev.actor}</strong> {ACTIONS[ev.action] ?? ev.action}
          {ev.note && <>: {ev.note}</>}
          {Object.keys(ev.after).filter((k) => k in CHANGE_LABELS).map((k) => (
            <div key={k} className="muted">{CHANGE_LABELS[k]}: {show(k, ev.before[k])} → {show(k, ev.after[k])}</div>))}
        </li>))}</ol>}
    </details>
  );
}
const open = (a: Item) => a.status === "assigned" || a.status === "returned";
// Stored values stay; screens show Fully / Partially / Non-compliant (technical-architecture 16.2). "exception" is retired.
const answerLabel = (c: string) => (c === "exception" ? "Exception (earlier value)" : complianceLabel(c));

export default function InboxPage() {
  const { bu } = useParams<{ bu: string }>();
  const { data, error, reload } = useApi<Data>(`/api/inbox/${bu}`);
  const { data: portfolio } = useApi<Portfolio>("/api/portfolio");
  const me = useMe()?.name ?? "";  // unit switcher: which units have work, and waiting answers
  const toast = useToast();
  const [busy, setBusy] = useState<number | "all">();      // what is being saved: no double submit
  const [returning, setReturning] = useState<number>();     // the item whose return note is being written
  const [note, setNote] = useState("");
  const [results, setResults] = useState<Record<number, string>>({});  // "Submit all" outcome per row
  if (error) return <div className="content"><PageHead title="My work" /><Alert kind="error">Could not load this work package: {error}</Alert></div>;
  if (!data) return <div className="content"><PageHead title="My work" /><Skeleton lines={4} /></div>;

  const canAnswer = data.unit ? [data.unit.product_manager, data.unit.design_engineer].includes(me) : me === BID_MANAGER;
  // A-17: the unit's product manager validates (the bid manager for the bid desk); the bid manager may return any answer
  const canValidate = data.unit ? me === data.unit.product_manager : me === BID_MANAGER;
  const canReturn = canValidate || me === BID_MANAGER;
  const opportunities = [...new Set(data.items.map((a) => a.opportunity_id))];
  const openCount = data.items.filter(open).length;
  const toValidate = data.items.filter((a) => a.status === "submitted").length;
  // Walkthrough targets (data-tour): the first open, submitted and returned rows carry stable ids; nothing else changes.
  // While the walkthrough runs it names its opportunity on <html data-tour-opp>, and that opportunity's rows come first.
  const focus = typeof document !== "undefined" ? document.documentElement.getAttribute("data-tour-opp") : null;
  const firstOf = (test: (a: Item) => boolean) => (data.items.find((a) => test(a) && a.opportunity_id === focus) ?? data.items.find(test))?.id;
  // Every unit with work, and how many of its answers wait for validation (progress.submitted includes validated ones).
  const waiting: Record<string, number> = { BID: 0 };
  for (const o of portfolio ?? []) for (const [u, p] of Object.entries(o.progress)) waiting[u] = (waiting[u] ?? 0) + p.submitted - p.validated;
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
      <PageHead title={`My work: ${data.unit?.name ?? BID_DESK}`}
        help="Each line is a requirement assigned to this unit. Mark it fully, partially or non-compliant, say how it is met (for partially or non-compliant: what is not met and why), add conditions, a workaround or next steps where they apply, then submit. The bid manager validates or returns it with a note.">
        {canAnswer && openCount > 0 && <button disabled={busy !== undefined} onClick={submitAll} data-tour="inbox-submit-all">Submit all answered rows</button>}
        {busy === "all" && <Busy label="Sending…" />}
      </PageHead>
      <UnitCompletion bu={bu} />
      <KnowledgeReview />
      <nav className="row inbox-links" aria-label="Work packages" data-tour="inbox-units">
        <span>Work package:</span>
        {Object.keys(waiting).sort((a, b) => (a === "BID" ? -1 : b === "BID" ? 1 : a.localeCompare(b))).map((u) => (
          <Link key={u} href={`/inbox/${u}`} className={`chip${u === bu ? " on" : ""}`} aria-current={u === bu ? "page" : undefined}>
            {u === "BID" ? BID_DESK : u}{canValidate && waiting[u] > 0 && <span>{waiting[u]} to validate</span>}
          </Link>))}
      </nav>
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
      {!canAnswer && !canValidate && <div data-tour="inbox-readonly"><Alert kind="info">You are signed in as {me}: you can read this work package but not answer it. Sign in as one of this unit's people to answer.</Alert></div>}
      {canAnswer && openCount > 0 && <p className="muted" data-tour="inbox-open-count">{openCount} open row(s). “Submit all answered rows” sends every open row where “How it is met” is filled in.</p>}
      {canValidate && toValidate > 0 && <p className="muted" data-tour="inbox-to-validate">{toValidate} submitted answer(s) waiting for validation.</p>}
      {data.items.length === 0 ? <EmptyState title="Nothing assigned" hint="Requirements appear here once the bid manager dispatches a bid to this unit." /> : (
      <table className="inbox" data-tour="inbox-table">
        <thead><tr><th>Bid</th><th>Requirement</th><th>Response</th><th>Status</th></tr></thead>
        <tbody>
          {data.items.map((a) => {
            const t = (id: string) => (a.id === firstOpen ? id : undefined);        // first open row's targets
            const v = (id: string) => (a.id === firstSubmitted ? id : undefined);   // first submitted row's targets
            return (
            <tr key={a.id} data-tour={t("inbox-row-open") ?? v("inbox-row-submitted") ?? `inbox-row-${a.id}`}>
              <td className="mono"><Link href={`/opportunities/${a.opportunity_id}/trace#${a.req_id}`}>{a.opportunity_id}<br />{a.req_id}</Link></td>
              <td data-tour={t("inbox-req-cell")}>{a.requirement ? <>{a.requirement.text}<div className="quote">“{a.requirement.quote}”</div>
                {a.requirement.provenance === "UNANCHORED" // UX-14: the same badge as the Requirements page, no "not found in source" link
                  ? <StatusBadge status="medium" kind="severity" label="Source not verified" title="Quote not located on the page; check the source manually" />
                  : <Link className="muted" href={`/opportunities/${a.opportunity_id}/trace#${a.req_id}`} data-tour={t("inbox-source-link")}>{a.requirement.source}: show highlighted source</Link>}</>
                : <span className="warn">This requirement no longer exists in the bid.</span>}
                <Questions oppId={a.opportunity_id} reqId={a.req_id} assignmentId={a.id} open={a.open_questions} me={me} bm={canValidate} onChanged={reload} /></td>
              <td>
                {canAnswer && open(a) ? (
                  <form className="form compact" data-assignment={a.id} aria-busy={busy === a.id} data-tour={t("inbox-form")}
                    onSubmit={(e) => { e.preventDefault(); const f = new FormData(e.currentTarget); run(a.id, () => answer(a, f), `${a.req_id} submitted for validation.`); }}>
                    {a.status === "returned" && <div data-tour={a.id === firstReturned ? "inbox-returned-note" : undefined}><Alert kind="warn" title="Returned">by {a.validated_by}: {a.validation_note}</Alert></div>}
                    <label data-tour={t("inbox-compliance")}><span className="sr-only">Compliance</span>
                      <select name="compliance" defaultValue={a.compliance ?? "met"}>{data.compliance.map((c) => <option key={c} value={c}>{answerLabel(c)}</option>)}</select></label>
                    <label data-tour={t("inbox-product")}><span className="sr-only">Product or configuration</span>
                      <input name="product_ref" defaultValue={a.product_ref ?? ""} placeholder="Product / configuration" /></label>
                    <label data-tour={t("inbox-response")}><span className="sr-only">How it is met</span>
                      <textarea name="response" rows={2} defaultValue={a.response} placeholder="How it is met" /></label>
                    <label data-tour={t("inbox-reason")}><span className="sr-only">Reason</span>
                      <textarea name="reason" rows={2} defaultValue={a.reason ?? ""} placeholder="Reason: what is not met and why (required for partially or non-compliant)" /></label>
                    {FIELDS.map((f) => <label key={f.name}><span className="sr-only">{f.label}</span>
                      <input name={f.name} defaultValue={a[f.name] ?? ""} placeholder={`${f.label} (optional)`} /></label>)}
                    <div className="inline">
                      <button className="sm" disabled={busy !== undefined} data-tour={t("inbox-submit")}>Submit</button>
                      {busy === a.id && <Busy label="Sending…" />}
                    </div>
                  </form>
                ) : (
                  // UX-04: compliance, product and status are separate blocks, never adjacent text
                  <div data-tour={v("inbox-answer-submitted")}>{a.compliance && <strong>{answerLabel(a.compliance)}</strong>}{a.product_ref && <> <span className="mono">{a.product_ref}</span></>}
                    {a.response && <div className="muted">{a.response}</div>}
                    {a.reason && <div><strong>Reason:</strong> {a.reason}</div>}
                    {FIELDS.map((f) => a[f.name] && <div key={f.name} className="muted"><strong>{f.label}:</strong> {a[f.name]}</div>)}
                    {!a.compliance && <div className="muted">not answered yet</div>}</div>
                )}
                {results[a.id] && <div className={results[a.id] === "sent" ? "ok" : "warn"}>{results[a.id]}</div>}
              </td>
              <td data-tour={v("inbox-validate-cell") ?? t("inbox-status-cell")}>
                <StatusBadge status={a.status} />{a.validated_by && a.status === "validated" && <div className="muted">by {a.validated_by}</div>}
                <History id={a.id} />
                {canReturn && a.status === "submitted" && (returning === a.id ? (
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
                    {canValidate && <button className="sm" disabled={busy !== undefined} data-tour={v("inbox-validate")} onClick={() => run(a.id, () => post(`/api/assignments/${a.id}/validate`, { ok: true, note: "" }), `${a.req_id} validated.`)}>Validate</button>}
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
