"use client";
// The compliance badge; for Partially compliant and Non-compliant it also explains itself (mouse hover or keyboard focus).
// The text is the unit's real reason, or "Reason not provided" (A-18 stores it; nothing is made up).  Owner: Janvia.
import { useId, useState } from "react";
import { complianceLabel } from "@/lib/types";
import { StatusBadge } from "@/components/ui";
import type { MatrixRow } from "./types";

export const NO_REASON = "Reason not provided";

export default function ComplianceBadge({ row }: { row: Pick<MatrixRow, "compliance" | "reason"> }) {
  const id = useId();
  const [pos, setPos] = useState<{ x: number; y: number }>();
  if (!row.compliance) return null;
  const badge = <StatusBadge status={row.compliance} kind="compliance" label={complianceLabel(row.compliance)} />;
  if (row.compliance !== "partial" && row.compliance !== "not_met") return badge;
  // position: fixed, so the table's own scrolling never clips the text; always in the page, so aria-describedby always resolves
  const show = (el: HTMLElement) => { const b = el.getBoundingClientRect(); setPos({ x: Math.max(8, Math.min(b.left, window.innerWidth - 320)), y: b.bottom + 6 }); };
  return (
    <span className="reason-tip" tabIndex={0} aria-describedby={id}
      onMouseEnter={(e) => show(e.currentTarget)} onMouseLeave={() => setPos(undefined)}
      onFocus={(e) => show(e.currentTarget)} onBlur={() => setPos(undefined)}
      onKeyDown={(e) => { if (e.key === "Escape" && pos) { e.stopPropagation(); setPos(undefined); } }}>
      {badge}
      <span id={id} role="tooltip" className={`reason-pop${pos ? " on" : ""}`} style={pos ? { left: pos.x, top: pos.y } : undefined}>{row.reason ?? NO_REASON}</span>
    </span>
  );
}
