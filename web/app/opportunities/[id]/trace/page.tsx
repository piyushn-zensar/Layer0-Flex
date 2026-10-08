"use client";
// Traceability: three linked panes: (1) RFP page with highlights, (2) requirement line items, (3) product mapping + responses.
// Selecting a requirement in any pane selects it in all three and opens its source page.  Owner: Janvia.
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { post, useApi } from "@/lib/api";
import type { Trace } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import MatchActions from "@/components/matching/MatchActions"; // A-05 (Atharv)

// Assignment status -> safe CSS class suffix (displayed text stays as-is).
const statusClass = (s: string | null | undefined) =>
  `status-${String(s ?? "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "unknown"}`;

export default function TracePage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, reload } = useApi<Trace>(`/api/opportunities/${id}/trace`);
  const [selected, setSelected] = useState<string>();
  const [pageNo, setPageNo] = useState(1);

  const select = useCallback((reqId: string) => {
    setSelected(reqId);
    const req = data?.rows.find((r) => r.req.req_id === reqId)?.req;
    if (req?.page) setPageNo(req.page);
    history.replaceState(null, "", `#${reqId}`);
    document.querySelectorAll(`tr[data-req="${reqId}"]`).forEach((tr) => tr.scrollIntoView({ block: "nearest", behavior: "smooth" }));
  }, [data]);

  useEffect(() => { // first load: the requirement in the URL hash, else the first one
    if (!data || selected) return;
    const fromHash = decodeURIComponent(location.hash.slice(1));
    const first = data.rows.find((r) => r.req.req_id === fromHash) ?? data.rows.find((r) => r.req.page);
    if (first) select(first.req.req_id);
  }, [data, selected, select]);

  if (error) return <p className="warn">Unable to load this view. Please refresh the page or try again shortly.</p>;
  if (!data) return <p>Loading…</p>;
  const page = data.pages[pageNo - 1];
  const rowProps = (reqId: string) => ({
    "data-req": reqId, className: reqId === selected ? "selected" : "", onClick: () => select(reqId),
    tabIndex: 0, "aria-selected": reqId === selected,
    onKeyDown: (e: React.KeyboardEvent) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(reqId); } },
  });

  return (
    <>
      <PageHead level={2} title="Traceability"
        help="Original RFP, requirement breakdown and product mapping side by side. Select a requirement in any pane to follow it across all three.">
        <button className="secondary" onClick={() => post(`/api/opportunities/${id}/match`).then(reload, alert)}>Match products</button>
      </PageHead>
      <div className="toolbar">
        <span className="muted">Unit responses: {Object.entries(data.progress).map(([bu, p]) => <span key={bu} className="tag">{bu} {p.validated}/{p.total} validated</span>)}
          {Object.keys(data.progress).length === 0 && "not sent to units yet"}</span>
      </div>
      <div className="trace-legend" aria-label="Offering type legend">
        <span className="tag CTO"><strong>CTO</strong> Configure-to-order: catalog product with options (CPQ)</span>
        <span className="tag SEMI_CUSTOM"><strong>Semi-custom</strong> Configured product plus workshop work for this customer</span>
        <span className="tag ETO"><strong>ETO</strong> Engineered-to-order: designed for this requirement</span>
      </div>
      <div className="three">
        <section className="pane">
          <h2>1 · Original RFP</h2>
          {data.doc && page ? (<>
            <div className="pager">
              <button aria-label="Previous page" onClick={() => setPageNo(Math.max(1, pageNo - 1))}>◀</button>
              <span>Page <input type="number" aria-label="Page number" min={1} max={data.pages.length} value={pageNo}
                onChange={(e) => setPageNo(Math.min(data.pages.length, Math.max(1, Number(e.target.value))))} /> / {data.pages.length}</span>
              <button aria-label="Next page" onClick={() => setPageNo(Math.min(data.pages.length, pageNo + 1))}>▶</button>
              {page.unreviewed && <span className="warn">No text layer: page not read (needs OCR)</span>}
            </div>
            <div className="page">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`/api/documents/${data.doc.id}/pages/${pageNo}.png`} alt={`RFP page ${pageNo}`} />
              {data.rows.filter((r) => r.req.page === pageNo).flatMap((r) => r.req.bboxes.map(([x0, y0, x1, y1], i) => (
                <div key={`${r.req.req_id}-${i}`} title={r.req.req_id} onClick={() => select(r.req.req_id)}
                  className={`hl${r.req.req_id === selected ? " sel" : ""}`}
                  style={{ left: `${(x0 / page.width) * 100}%`, top: `${(y0 / page.height) * 100}%`,
                    width: `${((x1 - x0) / page.width) * 100}%`, height: `${((y1 - y0) / page.height) * 100}%` }} />
              )))}
            </div>
          </>) : <p className="muted trace-empty">No RFP page available.</p>}
        </section>

        <section className="pane">
          <h2>2 · Requirement breakdown</h2>
          {data.rows.length === 0 ? <p className="muted trace-empty">No requirements extracted.</p> : (
          <table className="rows">
            <thead><tr><th className="col-id">ID</th><th className="col-src">Source</th><th>Requirement</th></tr></thead>
            <tbody>
              {data.rows.map(({ req }) => (
                <tr key={req.req_id} {...rowProps(req.req_id)}>
                  <td><div className="mono trace-id">{req.req_id}</div><div className="tag">{req.category}</div></td>
                  <td className="trace-source">{req.source}{req.provenance === "UNANCHORED" && <div className="warn">unanchored</div>}</td>
                  <td><div className="trace-text">{req.text}</div><div className="quote trace-quote">“{req.quote}”</div></td>
                </tr>
              ))}
            </tbody>
          </table>)}
        </section>

        <section className="pane">
          <h2>3 · Product mapping and responses</h2>
          {data.rows.length === 0 ? <p className="muted trace-empty">No product mappings or responses available.</p> : (
          <table className="rows">
            <thead><tr><th className="col-id">ID</th><th>Unit · product</th><th>Response</th></tr></thead>
            <tbody>
              {data.rows.map(({ req, match: m, unit, product, bom, assignments }) => (
                <tr key={req.req_id} {...rowProps(req.req_id)}>
                  <td className="mono trace-id">{req.req_id}</td>
                  <td>
                    {m?.bu ? (<>
                      <div className="trace-unit">{unit?.name ?? m.bu}</div>
                      <div className="trace-product">{product?.name ?? m.product_id} <span className={`tag ${m.offering_type}`}>{m.offering_type}</span></div>
                      <div className="muted trace-rationale">{m.rationale}</div>
                      {bom.length > 0 && <details className="trace-bom"><summary>Bill of materials ({bom.length} lines)</summary>
                        <ul>{bom.map((b) => <li key={b.item}>{b.item} — {b.qty}</li>)}</ul></details>}
                    </>) : <span className="muted">{m ? "Bid manager (not a product item)" : "not matched yet"}</span>}
                    <MatchActions oppId={id} reqId={req.req_id} match={m} dispatched={assignments.length > 0} onDone={reload} />
                  </td>
                  <td>
                    {assignments.map((a) => (
                      <div key={a.id} className="trace-assign"><strong>{a.bu}</strong> <span className={`badge trace-status ${statusClass(a.status)}`}>{a.status}</span> <span className="trace-compliance">{a.compliance}</span>
                        {a.response && <div className="muted trace-response">{a.response}</div>}</div>
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
