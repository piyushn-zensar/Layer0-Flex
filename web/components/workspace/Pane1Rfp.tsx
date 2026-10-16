"use client";
// Pane 1 of Requirement Traceability: the RFP page as an image, with a highlight over every requirement anchored on it.  Owner: Janvia.
import { docTypeLabel } from "@/lib/types";
import { useWorkspace } from "./TraceWorkspace";

export default function Pane1Rfp() {
  const ws = useWorkspace();
  const { d, data, selected, pageNo } = ws;
  if (!d || !data) return null;
  const { shown, page, pages, docs, mainId, docName } = d;
  // Walkthrough targets (tour/chapters/trace.ts): "trace-sel-*" ids sit on the selected row only, so each id is unique.
  const sel = (reqId: string, name: string) => (reqId === selected ? name : undefined);
  if (!shown || !page) return <p className="muted trace-empty">No RFP page available.</p>;
  return (<>
    <div className="trace-docs" data-tour="trace-docs">
      <span>Showing <strong>{docName(shown)}</strong>{shown.id !== mainId && <> <span className="tag">{docTypeLabel(shown.role)}</span></>}</span>
      {docs.length > 1 && <span className="trace-doc-switch" role="group" aria-label="Document shown" data-tour="trace-doc-switch">{docs.map((x) => (
        <button key={x.id} type="button" className={`chip${x.id === shown.id ? " on" : ""}`} aria-pressed={x.id === shown.id} title={x.filename}
          onClick={() => { ws.setDocId(x.id); ws.setPageNo(1); }}>{docName(x)}</button>))}</span>}
    </div>
    <div className="pager" data-tour="trace-pager">
      <button aria-label="Previous page" onClick={() => ws.setPageNo(Math.max(1, pageNo - 1))}>◀</button>
      <span>Page <input type="number" aria-label="Page number" min={1} max={pages.length} value={pageNo}
        onChange={(e) => ws.setPageNo(Math.min(pages.length, Math.max(1, Number(e.target.value))))} /> / {pages.length}</span>
      <button aria-label="Next page" onClick={() => ws.setPageNo(Math.min(pages.length, pageNo + 1))}>▶</button>
      {page.unreviewed && <span className="warn" data-tour="trace-unreviewed-warning">No text layer: page not read (needs OCR)</span>}
    </div>
    <div className="page" data-tour="trace-page-image">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={`/api/documents/${shown.id}/pages/${pageNo}.png`} alt={`${docName(shown)} page ${pageNo}`} />
      {data.rows.filter((r) => r.req.page === pageNo && r.req.document_id === shown.id).flatMap((r) => r.req.bboxes.map(([x0, y0, x1, y1], i) => (
        <div key={`${r.req.req_id}-${i}`} title={r.req.req_id} onClick={() => ws.select(r.req.req_id)}
          data-tour={i === 0 ? sel(r.req.req_id, "trace-highlight-selected") : undefined}
          role="button" tabIndex={i === 0 ? 0 : -1} aria-label={`Select ${r.req.req_id}`}
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); ws.select(r.req.req_id); } }}
          className={`hl${r.req.req_id === selected ? " sel" : ""}`}
          style={{ left: `${(x0 / page.width) * 100}%`, top: `${(y0 / page.height) * 100}%`,
            width: `${((x1 - x0) / page.width) * 100}%`, height: `${((y1 - y0) / page.height) * 100}%` }} />
      )))}
    </div>
  </>);
}
