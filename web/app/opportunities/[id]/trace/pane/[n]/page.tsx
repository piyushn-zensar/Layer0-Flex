"use client";
// One pane of Requirement Traceability on its own address (J-18, C-34): /opportunities/{id}/trace/pane/{1|2|3}. This is what "Open in new window"
// opens. The window has no top bar, bid header or walkthrough (components/shell/Shell.tsx); it loads its own data, follows the selection when
// its pane is Linked, and hears the other windows of the bid over the channel (components/workspace/channel.ts).  Owner: Janvia.
import { notFound, useParams } from "next/navigation";
import { useEffect } from "react";
import { Alert, Skeleton } from "@/components/ui";
import FilterBar from "@/components/workspace/FilterBar";
import PaneFrame from "@/components/workspace/PaneFrame";
import TraceWorkspace, { useWorkspace } from "@/components/workspace/TraceWorkspace";
import UnitResponses from "@/components/workspace/UnitResponses";
import { PaneBody } from "@/components/workspace/Workspace";
import { PANE_NAMES, isPane, type Pane } from "@/components/workspace/types";

export default function PaneWindowPage() {
  const { id, n } = useParams<{ id: string; n: string }>();
  const pane = Number(n);
  if (!isPane(pane)) notFound();
  return <TraceWorkspace bidId={id} mode="pane" pane={pane}><PaneWindow pane={pane} /></TraceWorkspace>;
}

function PaneWindow({ pane }: { pane: Pane }) {
  const ws = useWorkspace();
  useEffect(() => { document.title = `Pane ${pane}: ${PANE_NAMES[pane]} (${ws.bidId})`; }, [pane, ws.bidId]);
  if (ws.error) return <div className="pane-window-body"><Alert kind="error" title="Could not load this pane.">{ws.error}</Alert></div>;
  if (!ws.data || !ws.d) return <div className="pane-window-body"><Skeleton lines={4} /></div>;
  return (
    <div className="pane-window-body">
      <div className="sr-only" role="status" aria-live="polite">{ws.notice}</div>
      {ws.windowGone && <Alert kind="info">This pane is back in the main window. You can close this window.</Alert>}
      {pane !== 1 && <FilterBar />}
      {pane === 3 && <div className="toolbar"><UnitResponses /></div>}
      <PaneFrame pane={pane}><PaneBody pane={pane} /></PaneFrame>
    </div>
  );
}
