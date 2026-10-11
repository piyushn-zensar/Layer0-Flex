"use client";
// Traceability: three linked panes: (1) RFP page with highlights, (2) requirement line items, (3) product mapping + responses.
// Selecting a requirement in any pane selects it in all three and opens its source page.  Owner: Janvia.
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { errorMessage, post, useApi } from "@/lib/api";
import type { Trace } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { Alert, Busy, EmptyState, Skeleton, StatusBadge, useToast } from "@/components/ui";
import MatchActions from "@/components/matching/MatchActions"; // A-05 (Atharv)
import SendToKnowledge from "@/components/knowledge/SendToKnowledge"; // A-11 (Atharv)

// P-11: what a document other than the main RFP is (its upload role).
const ROLE: Record<string, string> = { change: "Change document", addendum: "Addendum", qa: "Q&A" };

export default function TracePage() {
  const { id } = useParams<{ id: string }>();
  const toast = useToast();
  const { data, error, reload } = useApi<Trace>(`/api/opportunities/${id}/trace`);
  const { data: sent, reload: reloadSent } = useApi<Record<string, string>>(`/api/opportunities/${id}/knowledge`); // A-11
  const [selected, setSelected] = useState<string>();
  const [pageNo, setPageNo] = useState(1);
  const [docId, setDocId] = useState<string>(); // P-11: the document shown in pane 1 (default the main RFP)
  const [matching, setMatching] = useState(false);

  // Runs the matching agent over the requirements that nobody has decided yet (accepted, manual and rejected stay).
  const matchProducts = () => {
    setMatching(true);
    post<{ matched: number; kept: number }>(`/api/opportunities/${id}/match`)
      .then((r) => { toast.success(`Matching done: ${r.matched} requirement(s) matched, ${r.kept} kept as decided.`); return reload(); },
        (e) => toast.error(errorMessage(e)))
      .finally(() => setMatching(false));
  };

  const select = useCallback((reqId: string) => {
    setSelected(reqId);
    const req = data?.rows.find((r) => r.req.req_id === reqId)?.req;
    if (req && data?.docs?.some((d) => d.id === req.document_id)) setDocId(req.document_id); // a new version from an addendum
    if (req?.page) setPageNo(req.page);
    history.replaceState(null, "", `#${reqId}`);
    document.querySelectorAll(`tr[data-req="${reqId}"]`).forEach((tr) => tr.scrollIntoView({ block: "nearest", behavior: "smooth" }));
  }, [data]);

  useEffect(() => { // first load: the requirement in the URL hash, else the first one
    if (!data || selected) return;
    const fromHash = decodeURIComponent(location.hash.slice(1));
    const first = data.rows.find((r) => r.req.req_id === fromHash)
      ?? data.rows.find((r) => r.children.some((k) => k.req_id === fromHash)) // a sub-requirement (Changes links): its group
      ?? data.rows.find((r) => r.req.page);
    if (first) select(first.req.req_id);
  }, [data, selected, select]);

  if (error) return <Alert kind="error" title="Could not load the traceability view.">{error}</Alert>; // UX-10
  if (!data) return <Skeleton lines={4} />;
  // P-11: the main RFP first, then change documents with requirements anchored in them (older APIs send only doc + pages).
  const docs = data.docs ?? (data.doc ? [{ id: data.doc.id, filename: data.doc.filename, role: data.doc.role, pages: data.pages }] : []);
  const mainId = data.doc?.id ?? docs[0]?.id;
  const shown = docs.find((d) => d.id === docId) ?? docs[0];
  const docName = (d?: { id: string; filename: string }) => (!d || d.id === mainId ? "RFP" : d.filename);
  const docOf = (of?: string) => (of && mainId && of !== mainId ? docs.find((d) => d.id === of)?.filename ?? "Change document" : null);
  const pages = shown?.pages ?? [];
  const page = pages[pageNo - 1];
  // Walkthrough targets (tour/chapters/trace.ts): "trace-sel-*" ids sit on the selected row only, so each id is unique;
  // the first group and the first unanchored requirement get one id each.
  const sel = (reqId: string, name: string) => (reqId === selected ? name : undefined);
  const firstGroup = data.rows.find((r) => r.children.length > 0)?.req.req_id;
  const firstUnanchored = data.rows.find((r) => r.req.provenance === "UNANCHORED")?.req.req_id;
  const rowProps = (reqId: string) => ({
    "data-req": reqId, className: reqId === selected ? "selected" : "", onClick: () => select(reqId),
    tabIndex: 0, "aria-current": reqId === selected ? ("true" as const) : undefined,
    // Only when the row itself has focus, so buttons, links and the BOM summary inside it keep their own keys.
    onKeyDown: (e: React.KeyboardEvent) => {
      if (e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); select(reqId); }
    },
  });

  return (
    <>
      <PageHead level={2} title="Traceability"
        help="Original RFP, requirement breakdown and product mapping side by side. Select a requirement in any pane to follow it across all three.">
        {matching && <Busy label="Matching…" />}
        <button className="secondary" disabled={matching} onClick={matchProducts} data-tour="trace-match-button">Match products</button>
      </PageHead>
      <div className="toolbar">
        <span className="muted" data-tour="trace-unit-responses">Unit responses: {Object.entries(data.progress).map(([bu, p]) => (
          <StatusBadge key={bu} status={p.validated === p.total ? "validated" : p.submitted > 0 ? "submitted" : "assigned"}
            label={`${bu} ${p.validated}/${p.total} validated`} title={`${p.submitted} of ${p.total} answers submitted`} />))}
          {Object.keys(data.progress).length === 0 && "not sent to units yet"}</span>
      </div>
      <div className="trace-legend" aria-label="Offering type legend" data-tour="trace-legend">
        <span className="tag CTO"><strong>CTO</strong> Configure-to-order: catalog product with options (CPQ)</span>
        <span className="tag SEMI_CUSTOM"><strong>Semi-custom</strong> Configured product plus workshop work for this customer</span>
        <span className="tag ETO"><strong>ETO</strong> Engineered-to-order: designed for this requirement</span>
      </div>
      <div className="three" data-tour="trace-panes">
        <section className="pane" data-tour="trace-pane-1">
          <h2>1 · Original RFP</h2>
          {shown && page ? (<>
            <div className="trace-docs" data-tour="trace-docs">
              <span>Showing <strong>{docName(shown)}</strong>{shown.id !== mainId && <> <span className="tag">{ROLE[shown.role] ?? "Document"}</span></>}</span>
              {docs.length > 1 && <span className="trace-doc-switch" role="group" aria-label="Document shown" data-tour="trace-doc-switch">{docs.map((d) => (
                <button key={d.id} type="button" className={`chip${d.id === shown.id ? " on" : ""}`} aria-pressed={d.id === shown.id} title={d.filename}
                  onClick={() => { setDocId(d.id); setPageNo(1); }}>{docName(d)}</button>))}</span>}
            </div>
            <div className="pager" data-tour="trace-pager">
              <button aria-label="Previous page" onClick={() => setPageNo(Math.max(1, pageNo - 1))}>◀</button>
              <span>Page <input type="number" aria-label="Page number" min={1} max={pages.length} value={pageNo}
                onChange={(e) => setPageNo(Math.min(pages.length, Math.max(1, Number(e.target.value))))} /> / {pages.length}</span>
              <button aria-label="Next page" onClick={() => setPageNo(Math.min(pages.length, pageNo + 1))}>▶</button>
              {page.unreviewed && <span className="warn" data-tour="trace-unreviewed-warning">No text layer: page not read (needs OCR)</span>}
            </div>
            <div className="page" data-tour="trace-page-image">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`/api/documents/${shown.id}/pages/${pageNo}.png`} alt={`${docName(shown)} page ${pageNo}`} />
              {data.rows.filter((r) => r.req.page === pageNo && r.req.document_id === shown.id).flatMap((r) => r.req.bboxes.map(([x0, y0, x1, y1], i) => (
                <div key={`${r.req.req_id}-${i}`} title={r.req.req_id} onClick={() => select(r.req.req_id)}
                  data-tour={i === 0 ? sel(r.req.req_id, "trace-highlight-selected") : undefined}
                  role="button" tabIndex={i === 0 ? 0 : -1} aria-label={`Select ${r.req.req_id}`}
                  onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(r.req.req_id); } }}
                  className={`hl${r.req.req_id === selected ? " sel" : ""}`}
                  style={{ left: `${(x0 / page.width) * 100}%`, top: `${(y0 / page.height) * 100}%`,
                    width: `${((x1 - x0) / page.width) * 100}%`, height: `${((y1 - y0) / page.height) * 100}%` }} />
              )))}
            </div>
          </>) : <p className="muted trace-empty">No RFP page available.</p>}
        </section>

        <section className="pane" data-tour="trace-pane-2">
          <h2>2 · Requirement breakdown</h2>
          {data.rows.length === 0 ? <EmptyState title="No requirements yet" hint="Nothing has been extracted from the RFP for this opportunity." /> : (
          <table className="rows" data-tour="trace-table-2">
            <thead><tr><th className="col-id">ID</th><th className="col-src">Source</th><th>Requirement</th></tr></thead>
            <tbody>
              {data.rows.map(({ req, children }) => (
                <tr key={req.req_id} {...rowProps(req.req_id)}>
                  <td data-tour={sel(req.req_id, "trace-sel-id")}><div className="mono trace-id">{req.req_id}</div><div className="tag">{req.category}</div></td>
                  <td className="trace-source" data-tour={sel(req.req_id, "trace-sel-source")}>{docOf(req.document_id) && <div><span className="tag">{docOf(req.document_id)}</span></div>}
                    {/* UX-14: the same badge as the Requirements page */}
                    {req.provenance === "UNANCHORED" ? <span data-tour={req.req_id === firstUnanchored ? "trace-unanchored" : undefined}>
                      <StatusBadge status="medium" kind="severity" label="unanchored" title="Quote not located on the page; check the source manually" /></span> : req.source}</td>
                  <td data-tour={sel(req.req_id, "trace-sel-text")}><div className="trace-text">{req.text}</div>
                    {children.length > 0 ? (
                      <ul className="trace-children" data-tour={req.req_id === firstGroup ? "trace-group" : undefined}>{children.map((k) => <li key={k.req_id}>{k.text} <span className="muted">({docOf(k.document_id) ? `${docOf(k.document_id)}, ` : ""}{k.source})</span></li>)}</ul>
                    ) : <div className="quote trace-quote">“{req.quote}”</div>}
                    {req.req_id === selected && <span data-tour="trace-send-knowledge"><SendToKnowledge kind="requirement" refId={req.req_id} status={sent?.[`requirement:${req.req_id}`]} onSent={reloadSent} /></span>}</td>
                </tr>
              ))}
            </tbody>
          </table>)}
        </section>

        <section className="pane" data-tour="trace-pane-3">
          <h2>3 · Product mapping and responses</h2>
          {data.rows.length === 0 ? <EmptyState title="Nothing to map yet" hint="Product mappings and unit responses appear here once requirements exist." /> : (
          <table className="rows" data-tour="trace-table-3">
            <thead><tr><th className="col-id">ID</th><th>Unit · product</th><th>Response</th></tr></thead>
            <tbody>
              {data.rows.map(({ req, match: m, unit, product, bom, assignments }) => (
                <tr key={req.req_id} {...rowProps(req.req_id)}>
                  <td className="mono trace-id">{req.req_id}</td>
                  <td>
                    {m?.bu ? (<>
                      <div className="trace-unit" data-tour={sel(req.req_id, "trace-sel-unit")}>{unit?.name ?? m.bu}</div>
                      <div className="trace-product" data-tour={sel(req.req_id, "trace-sel-product")}>{product?.name ?? m.product_id} <StatusBadge status={m.offering_type} kind="offering" /></div>
                      <div className="muted trace-rationale" data-tour={sel(req.req_id, "trace-sel-rationale")}>{m.rationale}</div>
                      {bom.length > 0 && <details className="trace-bom" data-tour={sel(req.req_id, "trace-sel-bom")}><summary>Bill of materials ({bom.length} lines)</summary>
                        <ul>{bom.map((b) => <li key={b.item}>{b.item} — {b.qty}</li>)}</ul></details>}
                    </>) : <span className="muted" data-tour={sel(req.req_id, "trace-sel-unit")}>{m?.status === "rejected" ? "rejected: choose a unit with Change" // QA-11, once the API sends rejected matches
                      : m ? "Bid manager (not a product item)" : "not matched yet"}</span>}
                    <MatchActions oppId={id} reqId={req.req_id} match={m} dispatched={assignments.length > 0} onDone={reload} tour={req.req_id === selected} />
                  </td>
                  <td data-tour={sel(req.req_id, "trace-sel-response")}>
                    {assignments.map((a) => (
                      <div key={a.id} className="trace-assign"><strong>{a.bu}</strong> <StatusBadge status={a.status} className="trace-status" />
                        {a.compliance && <StatusBadge status={a.compliance} kind="compliance" className="trace-compliance" />}
                        {a.response && <div className="muted trace-response">{a.response}</div>}
                        {a.status === "validated" && <SendToKnowledge kind="response" refId={a.id} status={sent?.[`response:${a.id}`]} onSent={reloadSent} />}</div>
                    ))}
                    {assignments.length === 0 && <span className="muted">not dispatched</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>)}
        </section>
      </div>
    </>
  );
}
