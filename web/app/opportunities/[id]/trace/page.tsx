"use client";
// Requirement Traceability (A-26, C-30): three panes: (1) RFP page with highlights, (2) the requirement register with its
// corrections, exceptions, line picker and history (components/requirements/Register, moved from the Requirements page),
// (3) product mapping + responses.
// Selecting a requirement selects it everywhere; every pane that is Linked also follows it (pane 1 opens its page, panes 2 and 3
// scroll to its rows), an Unlinked pane keeps its place. A pane can be enlarged (the other two stay mounted, hidden). Unit
// responses show only once the bid has been sent for assessment (J-12 / C-15).  Owner: Janvia.
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { errorMessage, isBidManager, post, useApi, useMe } from "@/lib/api";
import { complianceLabel, docTypeLabel } from "@/lib/types";
import type { Trace } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { Alert, Busy, EmptyState, Skeleton, StatusBadge, useToast } from "@/components/ui";
import MatchActions from "@/components/matching/MatchActions"; // A-05 (Atharv)
import Register from "@/components/requirements/Register"; // A-26 (Atharv)
import { RESPONSES, SORTS, applyFilters, filtersUrl, isFiltered, readFilters, type FilterKey, type Filters } from "@/components/requirements/filters"; // A-27
import SendToKnowledge from "@/components/knowledge/SendToKnowledge"; // A-11 (Atharv)

type Pane = 1 | 2 | 3;
const PANES: Pane[] = [1, 2, 3];
// `sent_for_assessment` is a trace-service flag (J-12) that web/lib/types.ts does not declare yet (Piyush's file).
type TraceView = Trace & { sent_for_assessment?: boolean };

export default function TracePage() {
  const { id } = useParams<{ id: string }>();
  const toast = useToast();
  const { data, error, reload } = useApi<TraceView>(`/api/bids/${id}/trace`);
  const bm = isBidManager(useMe()); // P-31: match changes are the bid manager's; one lookup for every row
  const { data: sent, reload: reloadSent } = useApi<Record<string, string>>(`/api/bids/${id}/knowledge`); // A-11
  const [selected, setSelected] = useState<string>();
  const [pageNo, setPageNo] = useState(1);
  const [docId, setDocId] = useState<string>(); // P-11: the document shown in pane 1 (default the main RFP)
  const [matching, setMatching] = useState(false);
  const [linked, setLinked] = useState<Record<Pane, boolean>>({ 1: true, 2: true, 3: true }); // J-12: which panes follow the selection
  const [enlarged, setEnlarged] = useState<Pane | null>(null);
  // P-32 (C-27): the RFP step sends an already-read document here (?known=<file>): its stored requirements, not a new read
  const [known, setKnown] = useState<string | null>(null);
  // A-27 (C-32): filters and sort live in the page address, so a link (e.g. from a summary count) opens that view
  const [filters, setFilters] = useState<Filters>({});
  useEffect(() => { setKnown(new URLSearchParams(location.search).get("known")); setFilters(readFilters(location.search)); }, []);
  const setFilter = (k: FilterKey, v: string) => {
    const next = { ...filters, [k]: v || undefined };
    setFilters(next);
    history.replaceState(null, "", filtersUrl(location.pathname, next, location.hash));
  };
  const clearFilters = () => { setFilters({}); history.replaceState(null, "", filtersUrl(location.pathname, {}, location.hash)); };
  const linkedRef = useRef(linked); // select() is a stable callback, so it reads the current links from a ref
  const selectedRef = useRef<string | undefined>(undefined);

  // Runs the matching agent over the requirements that nobody has decided yet (accepted, manual and rejected stay).
  const matchProducts = () => {
    setMatching(true);
    post<{ matched: number; kept: number }>(`/api/bids/${id}/match`)
      .then((r) => { toast.success(`Matching done: ${r.matched} requirement(s) matched, ${r.kept} kept as decided.`); return reload(); },
        (e) => toast.error(errorMessage(e)))
      .finally(() => setMatching(false));
  };

  // Moves one pane to a requirement: pane 1 opens its document and page, panes 2 and 3 scroll its row into view.
  const follow = useCallback((pane: Pane, reqId: string) => {
    if (pane === 1) {
      const req = data?.rows.find((r) => r.req.req_id === reqId)?.req;
      if (req && data?.docs?.some((d) => d.id === req.document_id)) setDocId(req.document_id); // a new version from an addendum
      if (req?.page) setPageNo(req.page);
    } else {
      document.querySelectorAll(`[data-pane="${pane}"] tr[data-req="${reqId}"]`).forEach((tr) => tr.scrollIntoView({ block: "nearest", behavior: "smooth" }));
    }
  }, [data]);

  // `force`: the first selection on load (a deep link or the first row) moves every pane whatever its link.
  const select = useCallback((reqId: string, force = false) => {
    setSelected(reqId);
    selectedRef.current = reqId;
    history.replaceState(null, "", `#${reqId}`);
    PANES.filter((p) => force || linkedRef.current[p]).forEach((p) => follow(p, reqId));
  }, [follow]);

  const setLink = (pane: Pane, on: boolean) => {
    linkedRef.current = { ...linkedRef.current, [pane]: on };
    setLinked(linkedRef.current);
    if (on && selectedRef.current) follow(pane, selectedRef.current); // re-linking catches up with the selection at once
  };

  // Restoring (or switching) the enlarged pane: the panes that were hidden could not scroll, so the linked ones catch up now.
  useEffect(() => {
    if (!selectedRef.current) return;
    const req = selectedRef.current;
    const t = setTimeout(() => PANES.filter((p) => linkedRef.current[p] && (enlarged === null || enlarged === p)).forEach((p) => follow(p, req)), 0);
    return () => clearTimeout(t);
  }, [enlarged]); // on enlarge / restore only, not on every selection (follow and the selection are read from this render and the ref)

  useEffect(() => { // the first Esc restores the three-pane layout and goes no further: a walkthrough that is open stays open
    if (enlarged === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape" || e.defaultPrevented) return;
      e.preventDefault(); e.stopPropagation(); // capture phase: the walkthrough's own Esc handler (bubble phase) never sees this one
      setEnlarged(null);
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [enlarged]);

  useEffect(() => { // first load: the requirement in the URL hash, else the first one
    if (!data || selected) return;
    const fromHash = decodeURIComponent(location.hash.slice(1));
    const first = data.rows.find((r) => r.req.req_id === fromHash)
      ?? data.rows.find((r) => r.children.some((k) => k.req_id === fromHash)) // a sub-requirement (Changes links): its group
      ?? data.rows.find((r) => r.req.page);
    if (first) select(first.req.req_id, true);
  }, [data, selected, select]);

  if (error) return <Alert kind="error" title="Could not load the traceability view.">{error}</Alert>; // UX-10
  if (!data) return <Skeleton lines={4} />;
  // P-11: the main RFP first, then change documents with requirements anchored in them (older APIs send only doc + pages).
  const docs = data.docs ?? (data.doc ? [{ id: data.doc.id, filename: data.doc.filename, role: data.doc.role, pages: data.pages }] : []);
  const mainId = data.doc?.id ?? docs[0]?.id;
  const shown = docs.find((d) => d.id === docId) ?? docs[0];
  const docName = (d?: { id: string; filename: string }) => (!d || d.id === mainId ? "RFP" : d.filename);
  const assessed = data.sent_for_assessment ?? data.rows.some((r) => r.assignments.length > 0); // J-12: unit responses show only once sent
  const pages = shown?.pages ?? [];
  const page = pages[pageNo - 1];
  const view = applyFilters(data.rows, filters); // A-27: what panes 2 and 3 list
  const filtered = isFiltered(filters);
  const categories = [...new Set(data.rows.map((r) => r.req.category))].sort();
  const units = [...new Set(data.rows.flatMap((r) => [...(r.match?.units ?? []).map((u) => u.bu), ...r.assignments.map((a) => a.bu)]))].sort();
  const choose = (k: FilterKey, label: string, options: [string, string][]) => (
    <label>{label} <select value={filters[k] ?? ""} onChange={(e) => setFilter(k, e.target.value)} data-tour={`trace-filter-${k}`}>
      <option value="">{k === "sort" ? "RFP order" : "All"}</option>
      {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>);
  // Walkthrough targets (tour/chapters/trace.ts): "trace-sel-*" ids sit on the selected row only, so each id is unique;
  // the first group and the first unanchored requirement get one id each.
  const sel = (reqId: string, name: string) => (reqId === selected ? name : undefined);
  const rowProps = (reqId: string) => ({
    "data-req": reqId, className: reqId === selected ? "selected" : "", onClick: () => select(reqId),
    tabIndex: 0, "aria-current": reqId === selected ? ("true" as const) : undefined,
    // Only when the row itself has focus, so buttons, links and the BOM summary inside it keep their own keys.
    onKeyDown: (e: React.KeyboardEvent) => {
      if (e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); select(reqId); }
    },
  });

  // J-12: the heading row of a pane, with its Linked / Unlinked switch and its Enlarge / Restore button. The visible words are short;
  // each button's accessible name says the action and the pane (the three panes would otherwise all have an "Enlarge"), and the
  // Linked / Unlinked name ends with the current state, so the visible word is in the name. No aria-pressed: the name already
  // carries the state, and a changing name plus a pressed state would announce it twice.
  const paneHead = (pane: Pane, name: string) => (
    <div className="pane-head">
      <h2>{pane} · {name}</h2>
      <div className="pane-tools">
        <button type="button" className={`chip${linked[pane] ? " on" : ""}`} onClick={() => setLink(pane, !linked[pane])} data-tour={`trace-link-${pane}`}
          aria-label={linked[pane] ? `Unlink pane ${pane}: ${name} (currently linked)` : `Link pane ${pane}: ${name} (currently unlinked)`}
          title="A linked pane follows the selected requirement; an unlinked pane keeps its place until you link it again.">
          {linked[pane] ? "Linked" : "Unlinked"}</button>
        <button type="button" className="secondary sm" onClick={() => setEnlarged(enlarged === pane ? null : pane)} data-tour={`trace-enlarge-${pane}`}
          aria-label={`${enlarged === pane ? "Restore" : "Enlarge"} pane ${pane}: ${name}`}
          title={enlarged === pane ? "Back to the three panes (Esc)" : "Show only this pane"}>{enlarged === pane ? "Restore" : "Enlarge"}</button>
      </div>
    </div>
  );
  const paneProps = (pane: Pane) => ({ "data-pane": pane, hidden: enlarged !== null && enlarged !== pane });

  return (
    <>
      <PageHead level={2} title="Requirement Traceability"
        help="Original RFP, the requirement register and product mapping side by side. Select a requirement in any linked pane to follow it across the panes; correct the register in pane 2 (enlarge it to work there).">
        {matching && <Busy label="Matching…" />}
        <button className="secondary" disabled={matching} onClick={matchProducts} data-tour="trace-match-button">Match products</button>
      </PageHead>
      {known && <Alert kind="info" onClose={() => setKnown(null)}>{known} was read before in this bid, so it was not read again: these are its stored, frozen requirements.</Alert>}
      <div className="toolbar">
        <span className="muted" data-tour="trace-unit-responses">Unit responses: {assessed ? Object.entries(data.progress).map(([bu, p]) => (
          <StatusBadge key={bu} status={p.validated === p.total ? "validated" : p.submitted > 0 ? "submitted" : "assigned"}
            label={`${bu} ${p.validated}/${p.total} validated`} title={`${p.submitted} of ${p.total} answers submitted`} />)) : "Not sent for assessment yet"}</span>
      </div>
      <div className="filters trace-filters" role="search" aria-label="Filter and sort the requirements" data-tour="trace-filters">
        {choose("category", "Category", categories.map((c) => [c, c]))}
        {choose("offering", "Offering", [["CTO", "CTO"], ["SEMI_CUSTOM", "Semi-custom"], ["ETO", "ETO"], ["NONE", "Bid desk"], ["unmatched", "Not matched"]])}
        {choose("unit", "Unit", units.map((u) => [u, u === "BID" ? "Bid desk" : u]))}
        {choose("response", "Response", Object.entries(RESPONSES))}
        {choose("compliance", "Compliance", [["met", complianceLabel("met")], ["partial", complianceLabel("partial")], ["not_met", complianceLabel("not_met")]])}
        {choose("source", "Source", [["verified", "Verified"], ["not_verified", "Not verified"]])}
        {choose("origin", "Origin", [["extraction", "Extraction"], ["correction", "Correction"], ["customer_change", "Customer change"]])}
        <label>Pages <input type="number" min={1} className="narrow" value={filters.from ?? ""} onChange={(e) => setFilter("from", e.target.value)} aria-label="From page" />
          – <input type="number" min={1} className="narrow" value={filters.to ?? ""} onChange={(e) => setFilter("to", e.target.value)} aria-label="To page" /></label>
        <input type="search" placeholder="Search ID or text" value={filters.q ?? ""} onChange={(e) => setFilter("q", e.target.value)} aria-label="Search the requirements" />
        {choose("sort", "Sort", Object.entries(SORTS).filter(([k]) => k !== "rfp"))}
        <span className="muted">{view.length} of {data.rows.length}</span>
        {filtered && <button type="button" className="secondary sm" onClick={clearFilters}>Clear</button>}
      </div>
      <div className="trace-legend" aria-label="Offering type legend" data-tour="trace-legend">
        <span className="tag CTO"><strong>CTO</strong> Configure-to-order: catalog product with options (CPQ)</span>
        <span className="tag SEMI_CUSTOM"><strong>Semi-custom</strong> Configured product plus workshop work for this customer</span>
        <span className="tag ETO"><strong>ETO</strong> Engineered-to-order: designed for this requirement</span>
      </div>
      <div className={`three${enlarged ? " zoom" : ""}`} data-tour="trace-panes">
        <section className="pane" data-tour="trace-pane-1" {...paneProps(1)}>
          {paneHead(1, "Original RFP")}
          {shown && page ? (<>
            <div className="trace-docs" data-tour="trace-docs">
              <span>Showing <strong>{docName(shown)}</strong>{shown.id !== mainId && <> <span className="tag">{docTypeLabel(shown.role)}</span></>}</span>
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

        <section className="pane" data-tour="trace-pane-2" {...paneProps(2)}>
          {paneHead(2, "Requirement register")}
          <Register bidId={id} onChanged={reload} rowProps={rowProps} order={filtered ? view.map((r) => r.req.req_id) : undefined}
            extra={(reqId) => reqId === selected && <span data-tour="trace-send-knowledge">
              <SendToKnowledge kind="requirement" refId={reqId} status={sent?.[`requirement:${reqId}`]} onSent={reloadSent} /></span>} />
        </section>

        <section className="pane" data-tour="trace-pane-3" {...paneProps(3)}>
          {paneHead(3, "Product mapping and responses")}
          {data.rows.length === 0 ? <EmptyState title="Nothing to map yet" hint="Product mappings and unit responses appear here once requirements exist." /> : (
          <table className="rows" data-tour="trace-table-3">
            <thead><tr><th className="col-id">ID</th><th>Unit · product</th><th>Response</th></tr></thead>
            <tbody>
              {view.map(({ req, match: m, unit, product, bom, assignments }) => (
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
                    <MatchActions oppId={id} reqId={req.req_id} match={m} dispatched={assignments.length > 0} onDone={reload} tour={req.req_id === selected} canChange={bm} />
                  </td>
                  <td data-tour={sel(req.req_id, "trace-sel-response")}>
                    {!assessed ? <span className="muted">Responses appear once the bid is sent for assessment</span> : <>
                    {assignments.map((a) => (
                      <div key={a.id} className="trace-assign"><strong>{a.bu}</strong> <StatusBadge status={a.status} className="trace-status" />
                        {a.compliance && <StatusBadge status={a.compliance} kind="compliance" label={complianceLabel(a.compliance)} className="trace-compliance" />}
                        {a.response && <div className="muted trace-response">{a.response}</div>}
                        {a.status === "validated" && <SendToKnowledge kind="response" refId={a.id} status={sent?.[`response:${a.id}`]} onSent={reloadSent} />}</div>
                    ))}
                    {assignments.length === 0 && <span className="muted">not dispatched</span>}</>}
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
