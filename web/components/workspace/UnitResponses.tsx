"use client";
// The "Unit responses" line: one badge per unit with validated / total, or the note that the bid is not sent for assessment yet (J-12).
// Shown in the main toolbar and above pane 3 in its own window.  Owner: Janvia.
import { StatusBadge } from "@/components/ui";
import { useWorkspace } from "./TraceWorkspace";

export default function UnitResponses() {
  const { d, data } = useWorkspace();
  if (!d || !data) return null;
  return (
    <span className="muted" data-tour="trace-unit-responses">Unit responses: {d.assessed ? Object.entries(data.progress).map(([bu, p]) => (
      <StatusBadge key={bu} status={p.validated === p.total ? "validated" : p.submitted > 0 ? "submitted" : "assigned"}
        label={`${bu} ${p.validated}/${p.total} validated`} title={`${p.submitted} of ${p.total} answers submitted`} />)) : "Not sent for assessment yet"}</span>
  );
}
