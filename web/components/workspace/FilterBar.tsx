"use client";
// The filter and sort bar of Requirement Traceability (A-27, C-32), moved out of the page so a detached pane 2 or 3 window can show it too.
// The filters live in the page address of each window and travel between windows as `filters` messages (channel.ts).  Owner: Janvia.
// 19 Oct client review: each dropdown lists only the values this bid has, narrowed by the other filters, with how many
// requirements each would show; a dropdown that cannot narrow anything is left out; the labels say what they filter.
import { TERMS, categoryLabel, complianceLabel } from "@/lib/types";
import { RESPONSES, SORTS, facets, type Facet, type FilterKey } from "@/components/requirements/filters"; // A-27 (Atharv)
import { useWorkspace } from "./TraceWorkspace";

const LABELS: Record<Facet, [string, Record<string, string>]> = {
  category: ["Category", {}],
  offering: [TERMS.offering_type, { CTO: "CTO (configure to order)", SEMI_CUSTOM: "Semi-custom", ETO: "ETO (engineer to order)", NONE: "Bid desk (no product)", unmatched: "Not matched yet" }],
  unit: ["Business unit", { BID: "Bid desk" }],
  response: ["Unit response", RESPONSES],
  compliance: ["Unit compliance (any answer)", { met: complianceLabel("met"), partial: complianceLabel("partial"), deviation: complianceLabel("deviation"), not_met: complianceLabel("not_met"), exception: "Exception (earlier value)" }],
  source: ["RFP source check", { verified: "Quote found on the RFP page", not_verified: "Quote not found on the page" }],
  origin: ["Added by", { extraction: "The RFP reader", correction: "A correction", customer_change: "A customer change document" }],
};

export default function FilterBar() {
  const ws = useWorkspace();
  const d = ws.d;
  if (!d || !ws.data) return null;
  const f = ws.filters;
  const counts = facets(ws.data.rows, f);
  const facet = (k: Facet) => {
    const [label, names] = LABELS[k];
    const options = [...counts[k].entries()].sort(([a], [b]) => a.localeCompare(b));
    // nothing to choose: a single value that every row has (and no choice made) narrows nothing
    if (!f[k] && (options.length === 0 || (options.length === 1 && options[0][1] === d.view.length))) return null;
    if (f[k] && !counts[k].has(f[k]!)) options.push([f[k]!, f[k]!.includes(",") ? d.view.length : 0]); // a saved several-unit link (C-37)
    return (
      <label key={k}>{label} <select value={f[k] ?? ""} onChange={(e) => ws.setFilter(k, e.target.value)} data-tour={`trace-filter-${k}`}>
        <option value="">Any</option>
        {options.map(([v, n]) => <option key={v} value={v}>{names[v] ?? (k === "category" ? categoryLabel(v) : v.split(",").join(", "))} ({n})</option>)}</select></label>);
  };
  return (
    <div className="filters trace-filters" role="search" aria-label="Filter and sort the requirements" data-tour="trace-filters">
      {(["category", "offering", "unit", "response", "compliance", "source", "origin"] as Facet[]).map(facet)}
      <label>Pages <input type="number" min={1} className="narrow" value={f.from ?? ""} onChange={(e) => ws.setFilter("from", e.target.value)} aria-label="From page" />
        – <input type="number" min={1} className="narrow" value={f.to ?? ""} onChange={(e) => ws.setFilter("to", e.target.value)} aria-label="To page" /></label>
      <input type="search" placeholder="Search ID or text" value={f.q ?? ""} onChange={(e) => ws.setFilter("q", e.target.value)} aria-label="Search the requirements" />
      <label>Sort <select value={f.sort ?? ""} onChange={(e) => ws.setFilter("sort" as FilterKey, e.target.value)} data-tour="trace-filter-sort">
        <option value="">RFP order</option>
        {Object.entries(SORTS).filter(([k]) => k !== "rfp").map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
      <span className="muted">{d.view.length} of {ws.data.rows.length}</span>
      {d.filtered && <button type="button" className="secondary sm" onClick={ws.clearFilters}>Clear</button>}
    </div>
  );
}
