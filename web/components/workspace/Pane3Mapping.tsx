"use client";
// Pane 3 of Requirement Traceability: the proposed solution of every requirement (unit · solution area, example models, offering
// type, example bill of materials, the match actions) and the units' responses, which show only once the bid is sent for assessment (J-12).  Owner: Janvia.
import { TERMS, complianceLabel, examplesLabel, solutionLabel } from "@/lib/types";
import { EmptyState, StatusBadge } from "@/components/ui";
import MatchActions from "@/components/matching/MatchActions"; // A-05 (Atharv)
import SendToKnowledge from "@/components/knowledge/SendToKnowledge"; // A-11, P-36
import { useWorkspace } from "./TraceWorkspace";
import RequirementProducts, { useComponentsByReq } from "@/components/assessment/RequirementProducts"; // P-57 (Piyush)

const PRODUCT = ["technical", "compliance"]; // matching.PRODUCT_CATEGORIES: the items a unit's designer / engineer answers
const NEEDS_OWNER = "Needs an owner: no participating unit offers it yet";

export default function Pane3Mapping() {
  const ws = useWorkspace();
  const config = useComponentsByReq(ws.bidId); // the product configurator's last run (C-59)
  const { d, data, selected } = ws;
  if (!d || !data) return null;
  // Walkthrough targets (tour/chapters/trace.ts): "trace-sel-*" ids sit on the selected row only, so each id is unique.
  const sel = (reqId: string, name: string) => (reqId === selected ? name : undefined);
  if (data.rows.length === 0) return <EmptyState title="Nothing to map yet" hint="Proposed solutions and unit responses appear here once requirements exist." />;
  return (
    <table className="rows" data-tour="trace-table-3">
      <thead><tr><th className="col-id">ID</th><th>{TERMS.solution}</th><th>Response</th></tr></thead>
      <tbody>
        {d.view.map(({ req, match: m, solutions, bom, assignments, can_change }) => {
          // a non-product item routed to units is answered by their managers, never given a solution (C-41)
          const managers = assignments.some((a) => a.bu !== "BID") ? assignments.filter((a) => a.bu !== "BID").map((a) => a.bu)
            : PRODUCT.includes(req.category) ? [] : (m?.units ?? []).map((u) => u.bu);
          // a product item with no unit: a capability gap once the bid desk holds it (stated as not offered), else it needs an owner
          const noUnit = PRODUCT.includes(req.category) ? (assignments.some((a) => a.bu === "BID") ? TERMS.capability_gap : NEEDS_OWNER) : "Bid desk (not a product item)";
          return (
          <tr key={req.req_id} {...ws.rowProps(req.req_id)}>
            <td className="mono trace-id">{req.req_id}</td>
            <td>
              {m?.bu && PRODUCT.includes(req.category) ? (<>
                {solutions.map((s, i) => ( // C-40: one proposed solution per unit, main unit first; models are examples only
                  <div key={i} data-tour={i === 0 ? sel(req.req_id, "trace-sel-unit") : undefined}>
                    <div className="trace-unit"><span className="muted">{TERMS.solution}:</span> {solutionLabel(s)}{!s.area && <span className="muted"> · {TERMS.solution_pending}</span>}</div>
                    {s.examples.length > 0 && <div className="muted trace-product">{examplesLabel(s)}</div>}
                  </div>
                ))}
                <div className="trace-product" data-tour={sel(req.req_id, "trace-sel-product")}><StatusBadge status={m.offering_type} kind="offering" /></div>
                <div className="muted trace-rationale" data-tour={sel(req.req_id, "trace-sel-rationale")}>{m.rationale}</div>
                {bom.length > 0 && <details className="trace-bom" data-tour={sel(req.req_id, "trace-sel-bom")}><summary>Example bill of materials ({bom.length} {bom.length === 1 ? "line" : "lines"})</summary>
                  <ul>{bom.map((b) => <li key={b.item}>{b.item} — {b.qty}</li>)}</ul></details>}
              </>) : <span className="muted" data-tour={sel(req.req_id, "trace-sel-unit")}>{m?.status === "rejected" ? "Rejected: choose a unit with Change" // QA-11, once the API sends rejected matches
                : m ? (managers.length > 0 ? `Not a product item: answered by the unit managers (${managers.join(", ")})`
                  : noUnit) : "Not matched yet"}</span>}
              <MatchActions oppId={ws.bidId} reqId={req.req_id} match={m} dispatched={assignments.length > 0} onDone={ws.afterWrite} tour={req.req_id === selected} canChange={can_change} />
              <RequirementProducts reqId={req.req_id} entries={config.by.get(req.req_id)} outcomes={config.outcomes} />
            </td>
            <td data-tour={sel(req.req_id, "trace-sel-response")}>
              {!d.assessed ? <span className="muted">Responses appear once the bid is sent for assessment</span> : <>
              {assignments.map((a) => (
                <div key={a.id} className="trace-assign"><strong>{a.bu}</strong> <StatusBadge status={a.status} className="trace-status" />
                  {a.compliance && <StatusBadge status={a.compliance} kind="compliance" label={complianceLabel(a.compliance)} className="trace-compliance" />}
                  {a.response && <div className="muted trace-response">{a.response}</div>}
                  {a.status === "validated" && <SendToKnowledge kind="response" refId={a.id} status={ws.sent?.[`response:${a.id}`]} onSent={ws.afterWrite} />}</div>
              ))}
              {assignments.length === 0 && <span className="muted">Not sent to units</span>}</>}
            </td>
          </tr>);
        })}
      </tbody>
    </table>
  );
}
