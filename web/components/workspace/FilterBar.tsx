"use client";
// The filter and sort bar of Requirement Traceability (A-27, C-32), moved out of the page so a detached pane 2 or 3 window can show it too.
// The filters live in the page address of each window and travel between windows as `filters` messages (channel.ts).  Owner: Janvia.
import { complianceLabel } from "@/lib/types";
import { RESPONSES, SORTS, type FilterKey } from "@/components/requirements/filters"; // A-27 (Atharv)
import { useWorkspace } from "./TraceWorkspace";

export default function FilterBar() {
  const ws = useWorkspace();
  const d = ws.d;
  if (!d || !ws.data) return null;
  const f = ws.filters;
  const choose = (k: FilterKey, label: string, options: [string, string][]) => (
    <label>{label} <select value={f[k] ?? ""} onChange={(e) => ws.setFilter(k, e.target.value)} data-tour={`trace-filter-${k}`}>
      <option value="">{k === "sort" ? "RFP order" : "All"}</option>
      {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>);
  return (
    <div className="filters trace-filters" role="search" aria-label="Filter and sort the requirements" data-tour="trace-filters">
      {choose("category", "Category", d.categories.map((c) => [c, c]))}
      {choose("offering", "Offering", [["CTO", "CTO"], ["SEMI_CUSTOM", "Semi-custom"], ["ETO", "ETO"], ["NONE", "Bid desk"], ["unmatched", "Not matched"]])}
      {choose("unit", "Unit", d.units.map((u) => [u, u === "BID" ? "Bid desk" : u]))}
      {choose("response", "Response", Object.entries(RESPONSES))}
      {choose("compliance", "Compliance", [["met", complianceLabel("met")], ["partial", complianceLabel("partial")], ["not_met", complianceLabel("not_met")]])}
      {choose("source", "Source", [["verified", "Verified"], ["not_verified", "Not verified"]])}
      {choose("origin", "Origin", [["extraction", "Extraction"], ["correction", "Correction"], ["customer_change", "Customer change"]])}
      <label>Pages <input type="number" min={1} className="narrow" value={f.from ?? ""} onChange={(e) => ws.setFilter("from", e.target.value)} aria-label="From page" />
        – <input type="number" min={1} className="narrow" value={f.to ?? ""} onChange={(e) => ws.setFilter("to", e.target.value)} aria-label="To page" /></label>
      <input type="search" placeholder="Search ID or text" value={f.q ?? ""} onChange={(e) => ws.setFilter("q", e.target.value)} aria-label="Search the requirements" />
      {choose("sort", "Sort", Object.entries(SORTS).filter(([k]) => k !== "rfp"))}
      <span className="muted">{d.view.length} of {ws.data.rows.length}</span>
      {d.filtered && <button type="button" className="secondary sm" onClick={ws.clearFilters}>Clear</button>}
    </div>
  );
}
