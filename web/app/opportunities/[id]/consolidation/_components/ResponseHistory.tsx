"use client";
// The history of one unit's answer in the matrix detail: every assignment, submission, validation, return and withdrawal with who,
// when and what changed (before → after).  Read-only; loaded from GET /api/assignments/{id}/history (A-21) when it is opened.
// Owner: Janvia (J-13, C-16).
import { useEffect, useState } from "react";
import { api, errorMessage } from "@/lib/api";
import { Busy } from "@/components/ui";
import { CHANGE_LABELS, changeValue, what, when, type HistoryEvent } from "./historyText";

export default function ResponseHistory({ assignmentId, unit, defaultOpen }: { assignmentId: number; unit: string | null; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const [events, setEvents] = useState<HistoryEvent[]>();
  const [error, setError] = useState<string>();
  useEffect(() => { setOpen(defaultOpen); }, [defaultOpen, assignmentId]); // another row, or "History" clicked in the table
  useEffect(() => { setEvents(undefined); setError(undefined); }, [assignmentId]);
  useEffect(() => {
    if (!open || events || error) return;
    let live = true;
    api<HistoryEvent[]>(`/api/assignments/${assignmentId}/history`).then((r) => { if (live) setEvents(r); }, (e) => { if (live) setError(errorMessage(e)); });
    return () => { live = false; };
  }, [open, events, error, assignmentId]);
  return (
    <details className="resp-history" open={open} onToggle={(e) => setOpen(e.currentTarget.open)} data-tour="matrix-history">
      <summary>{open ? "Hide history" : "Show history"}{events ? ` (${events.length})` : ""}</summary>
      {error && <p className="warn" role="alert">{error}</p>}
      {open && !events && !error && <Busy label="Loading the history…" />}
      {events && events.length === 0 && <p className="muted">Nothing is recorded for this answer yet.</p>}
      {events && events.length > 0 && (
        <ol className="resp-history-list" aria-label={`History of the ${unit ?? "unit"} answer, oldest first`}>
          {events.map((ev) => (
            <li key={ev.id}>
              <div><strong>{ev.actor}</strong> {what({ entity: "assignment", action: ev.action })} <span className="muted">· {when(ev.at)}</span></div>
              {ev.note && <div className="detail-text">Note: {ev.note}</div>}
              {Object.keys(CHANGE_LABELS).filter((k) => k in ev.after).map((k) => (
                <div key={k} className="muted">{CHANGE_LABELS[k]}: {changeValue(k, ev.before[k] ?? null)} → {changeValue(k, ev.after[k] ?? null)}</div>))}
            </li>
          ))}
        </ol>
      )}
    </details>
  );
}
