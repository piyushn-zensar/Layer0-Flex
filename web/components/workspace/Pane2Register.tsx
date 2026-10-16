"use client";
// Pane 2 of Requirement Traceability: the requirement register (A-26, Atharv's Register component, unchanged). This wrapper only
// connects it to the workspace: the shared selection, the filtered order, the reload and the "Nominate" control.  Owner: Janvia.
import Register from "@/components/requirements/Register"; // A-26 (Atharv)
import SendToKnowledge from "@/components/knowledge/SendToKnowledge"; // A-11, P-36
import { useWorkspace } from "./TraceWorkspace";

export default function Pane2Register() {
  const ws = useWorkspace();
  return (
    <Register bidId={ws.bidId} onChanged={ws.afterWrite} rowProps={ws.rowProps} order={ws.d?.filtered ? ws.d.view.map((r) => r.req.req_id) : undefined}
      extra={(reqId) => reqId === ws.selected && <span data-tour="trace-send-knowledge">
        <SendToKnowledge kind="requirement" refId={reqId} status={ws.sent?.[`requirement:${reqId}`]} onSent={ws.afterWrite} /></span>} />
  );
}
