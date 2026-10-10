"use client";
// Response outline (J-07): the drafting agent's first draft per chapter (P-10), with the validated answers each
// paragraph rests on, what is still open, and related passages from both retrieval indexes.  Owner: Janvia.
import Link from "next/link";
import { useParams } from "next/navigation";
import { useApi } from "@/lib/api";
import PageHead from "@/components/shell/PageHead";
import SendToKnowledge from "@/components/knowledge/SendToKnowledge"; // A-11 (Atharv)

type Draft = { drafted: boolean; paragraphs: { text: string; sources: string[] }[]; gaps: string[]; dropped: number; note: string };
type Answer = { assignment_id: number; req_id: string; source: string; unit: string; compliance: string; product: string; requirement: string; response: string };
type Chapter = {
  id: string; title: string; total: number; answered: number; draft: Draft; material: Answer[]; exceptions: Answer[];
  open: { req_id: string; source: string; text: string; state: string }[];
  references: { rfp: { page: number; line_start: number; line_end: number; text: string }[]; past: { id: string; bu: string; text: string }[];
    mode: { rfp: string; knowledge: string } };
};
type Outline = { total: number; answered: number; validated_answers: number; summary: Draft; chapters: Chapter[]; note: string };

const OPEN_SHOWN = 8; // open requirements listed per chapter before the link to Final response

export default function OutlinePage() {
  const { id } = useParams<{ id: string }>();
  const { data: o, error } = useApi<Outline>(`/api/opportunities/${id}/response-outline`);
  const { data: sent, reload: reloadSent } = useApi<Record<string, string>>(`/api/opportunities/${id}/knowledge`); // A-11
  if (error) return <p className="warn">{error}</p>;
  if (!o) return <p>Drafting the outline…</p>;
  const ref = (reqId: string) => <Link key={reqId} className="mono" href={`/opportunities/${id}/trace#${reqId}`} title="Open in Traceability">{reqId}</Link>;

  const DraftView = ({ d }: { d: Draft }) => d.drafted ? (
    <>
      {d.paragraphs.map((p, i) => (
        <p key={i} className="outline-para">{p.text} <span className="muted">[{p.sources.map((s, j) => <span key={s}>{j > 0 && ", "}{ref(s)}</span>)}]</span></p>
      ))}
      {d.gaps.length > 0 && <div className="outline-gaps"><strong>To add or confirm</strong><ul>{d.gaps.map((g) => <li key={g}>{g}</li>)}</ul></div>}
      {d.note && <p className="muted">{d.note}</p>}
    </>
  ) : <p className="muted">Not drafted: {d.note}</p>;

  return (
    <>
      <PageHead level={2} title="Response outline"
        help="A first draft for the bid manager to edit, written by the drafting agent only from validated answers. Every paragraph cites its requirements; nothing is drafted for open ones." />
      <p><strong>{o.answered} / {o.total}</strong> requirements answered and validated ({o.validated_answers} validated answers).{" "}
        <a className="button" href={`/api/opportunities/${id}/response-outline.md`}>Download outline (Markdown)</a>{" "}
        <Link className="button secondary" href={`/opportunities/${id}/consolidation`}>Back to Final response</Link></p>
      <p className="muted"><span className="badge status-proposed">Draft</span> {o.note}</p>

      <section className="card">
        <h3>Executive summary</h3>
        <DraftView d={o.summary} />
      </section>

      {o.chapters.map((c, n) => (
        <section key={c.id} className="card">
          <h3>{n + 1}. {c.title} <span className="muted">{c.answered} of {c.total} answered</span></h3>
          <DraftView d={c.draft} />
          {c.exceptions.length > 0 && (
            <p className="warn">Not full compliance: {c.exceptions.map((a, i) => <span key={a.req_id + a.unit}>{i > 0 && "; "}{ref(a.req_id)} {a.unit}: {a.compliance}</span>)}</p>)}
          {c.material.length > 0 && (
            <details><summary>Validated answers ({c.material.length})</summary>
              <table><thead><tr><th>Requirement</th><th>Unit</th><th>Compliance</th><th>Answer</th><th>Knowledge base</th></tr></thead>
                <tbody>{c.material.map((a) => (
                  <tr key={a.req_id + a.unit}><td>{ref(a.req_id)}<div className="muted">{a.source}</div></td><td>{a.unit}{a.product && <div className="muted">{a.product}</div>}</td>
                    <td>{a.compliance}</td><td>{a.response}</td>
                    <td><SendToKnowledge kind="response" refId={a.assignment_id} status={sent?.[`response:${a.assignment_id}`]} onSent={reloadSent} /></td></tr>))}
                </tbody></table>
            </details>)}
          {c.open.length > 0 && (
            <details><summary>Still open ({c.open.length})</summary>
              <ul>{c.open.slice(0, OPEN_SHOWN).map((r) => <li key={r.req_id}>{ref(r.req_id)} <span className="muted">{r.source}</span> {r.text}</li>)}</ul>
              {c.open.length > OPEN_SHOWN && <p className="muted">and {c.open.length - OPEN_SHOWN} more: see <Link href={`/opportunities/${id}/consolidation`}>Final response</Link>.</p>}
            </details>)}
          {(c.references.rfp.length > 0 || c.references.past.length > 0) && (
            <details><summary>Related passages</summary>
              {c.references.rfp.length > 0 && <><p className="muted">In this RFP ({c.references.mode.rfp} search)</p>
                <ul>{c.references.rfp.map((p) => <li key={`${p.page}-${p.line_start}`}><span className="mono">p. {p.page}, lines {p.line_start}-{p.line_end}</span> {p.text}</li>)}</ul></>}
              {c.references.past.length > 0 && <><p className="muted">Past responses ({c.references.mode.knowledge} search; illustrative)</p>
                <ul>{c.references.past.map((p) => <li key={p.id}><span className="mono">{p.id}</span> {p.text}</li>)}</ul></>}
            </details>)}
        </section>
      ))}
    </>
  );
}
