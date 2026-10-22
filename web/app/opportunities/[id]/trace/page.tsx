"use client";
// Requirement Traceability (A-26, C-30): three panes: (1) RFP page with highlights, (2) the requirement register with its
// corrections, exceptions, line picker and history (components/requirements/Register), (3) proposed solutions + responses.
// J-18 (C-34): the state and the panes live in components/workspace. This page is the main window: the panes can be dragged into a new
// order, resized, and opened each in a window of its own (/trace/pane/{n}); the layout is remembered per browser.
// Selecting a requirement selects it everywhere; every pane that is Linked also follows it, an Unlinked pane keeps its place (J-12).
// A pane can be enlarged (the others stay mounted, hidden). Unit responses show only once the bid is sent for assessment (J-12 / C-15).  Owner: Janvia.
import { useParams } from "next/navigation";
import { useApi } from "@/lib/api";
import PageHead from "@/components/shell/PageHead";
import { Alert, Busy, Skeleton } from "@/components/ui";
import FilterBar from "@/components/workspace/FilterBar";
import TraceWorkspace, { useWorkspace } from "@/components/workspace/TraceWorkspace";
import UnitResponses from "@/components/workspace/UnitResponses";
import Workspace from "@/components/workspace/Workspace";
import { isDefaultLayout } from "@/components/workspace/layout";

export default function TracePage() {
  const { id } = useParams<{ id: string }>();
  return <TraceWorkspace bidId={id} mode="main"><TraceMain /></TraceWorkspace>;
}

function TraceMain() {
  const ws = useWorkspace();
  const { data: decided } = useApi<{ go_no_go: unknown }>(`/api/bids/${ws.bidId}/decisions`); // as the bid header: is a go/no-go recorded?
  if (ws.error) return <Alert kind="error" title="Could not load the traceability view.">{ws.error}</Alert>; // UX-10
  if (!ws.data || !ws.d) return <Skeleton lines={4} />;
  return (
    <>
      <PageHead level={2} title="Requirement Traceability"
        help="Original RFP, the requirement register and the proposed solutions side by side. Select a requirement in any linked pane to follow it across the panes; correct the register in pane 2 (enlarge it to work there). Drag a pane by its grip, or use the arrows, to change the order; drag the bars between panes to resize them; open a pane in a window of its own for another screen.">
        {ws.matching && <Busy label="Proposing solutions…" />}
        {/* the bid manager's, until the go/no-go is recorded: then the solutions are the units' answers (C-44 wording) */}
        {ws.bm && decided && !decided.go_no_go && <button className="secondary" disabled={ws.matching} onClick={ws.matchProducts} data-tour="trace-match-button"
          title="Propose a solution (unit and solution area) for every requirement nobody has decided yet">Propose solutions</button>}
      </PageHead>
      {ws.known && <Alert kind="info" onClose={ws.dismissKnown}>{ws.known} was read before in this bid, so it was not read again: these are its stored, frozen requirements.</Alert>}
      <div className="toolbar">
        <UnitResponses />
        <button type="button" className="secondary sm" onClick={ws.resetLayout} disabled={isDefaultLayout(ws.layout)} data-tour="trace-reset-layout"
          title="Back to the original order and widths of the panes">Reset layout</button>
      </div>
      <FilterBar />
      <div className="trace-legend" aria-label="Type of offer legend" data-tour="trace-legend">
        <span className="tag CTO"><strong>CTO</strong> Configure-to-order: catalog product with options (CPQ)</span>
        <span className="tag SEMI_CUSTOM"><strong>Semi-custom</strong> Configured product plus workshop work for this customer</span>
        <span className="tag ETO"><strong>ETO</strong> Engineered-to-order: designed for this requirement</span>
      </div>
      <Workspace />
    </>
  );
}
