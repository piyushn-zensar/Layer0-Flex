"use client";
// Pane 3 of Requirement Traceability: the product mapping of every requirement (unit, product, offering type, bill of materials, the
// match actions) and the units' responses, which show only once the bid is sent for assessment (J-12).  Owner: Janvia.
import { complianceLabel } from "@/lib/types";
import { EmptyState, StatusBadge } from "@/components/ui";
import MatchActions from "@/components/matching/MatchActions"; // A-05 (Atharv)
import SendToKnowledge from "@/components/knowledge/SendToKnowledge"; // A-11, P-36
import { useWorkspace } from "./TraceWorkspace";

export default function Pane3Mapping() {
  const ws = useWorkspace();
  const { d, data, selected } = ws;
  if (!d || !data) return null;
  // Walkthrough targets (tour/chapters/trace.ts): "trace-sel-*" ids sit on the selected row only, so each id is unique.
  const sel = (reqId: string, name: string) => (reqId === selected ? name : undefined);
  if (data.rows.length === 0) return <EmptyState title="Nothing to map yet" hint="Product mappings and unit responses appear here once requirements exist." />;
  return (
    <table className="rows" data-tour="trace-table-3">
      <thead><tr><th className="col-id">ID</th><th>Unit · product</th><th>Response</th></tr></thead>
      <tbody>
        {d.view.map(({ req, match: m, unit, product, bom, assignments }) => (
          <tr key={req.req_id} {...ws.rowProps(req.req_id)}>
            <td className="mono trace-id">{req.req_id}</td>
            <td>
              {m?.bu ? (<>
                <div className="trace-unit" data-tour={sel(req.req_id, "trace-sel-unit")}>{unit?.name ?? m.bu}</div>
                <div className="trace-product" data-tour={sel(req.req_id, "trace-sel-product")}>{product?.name ?? m.product_id} <StatusBadge status={m.offering_type} kind="offering" /></div>
                <div className="muted trace-rationale" data-tour={sel(req.req_id, "trace-sel-rationale")}>{m.rationale}</div>
                {bom.length > 0 && <details className="trace-bom" data-tour={sel(req.req_id, "trace-sel-bom")}><summary>Bill of materials ({bom.length} lines)</summary>
                  <ul>{bom.map((b) => <li key={b.item}>{b.item} — {b.qty}</li>)}</ul></details>}
              </>) : <span className="muted" data-tour={sel(req.req_id, "trace-sel-unit")}>{m?.status === "rejected" ? "rejected: choose a unit with Change" // QA-11, once the API sends rejected matches
                : m ? (assignments.some((a) => a.bu !== "BID") ? `Not a product item: answered by the unit managers (${assignments.filter((a) => a.bu !== "BID").map((a) => a.bu).join(", ")})`
                  : "Bid desk (not a product item)") : "not matched yet"}</span>}
              <MatchActions oppId={ws.bidId} reqId={req.req_id} match={m} dispatched={assignments.length > 0} onDone={ws.afterWrite} tour={req.req_id === selected} canChange={ws.bm} />
            </td>
            <td data-tour={sel(req.req_id, "trace-sel-response")}>
              {!d.assessed ? <span className="muted">Responses appear once the bid is sent for assessment</span> : <>
              {assignments.map((a) => (
                <div key={a.id} className="trace-assign"><strong>{a.bu}</strong> <StatusBadge status={a.status} className="trace-status" />
                  {a.compliance && <StatusBadge status={a.compliance} kind="compliance" label={complianceLabel(a.compliance)} className="trace-compliance" />}
                  {a.response && <div className="muted trace-response">{a.response}</div>}
                  {a.status === "validated" && <SendToKnowledge kind="response" refId={a.id} status={ws.sent?.[`response:${a.id}`]} onSent={ws.afterWrite} />}</div>
              ))}
              {assignments.length === 0 && <span className="muted">not dispatched</span>}</>}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
