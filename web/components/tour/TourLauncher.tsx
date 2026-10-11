"use client";
// Walkthrough launcher: the welcome dialog and the top-bar "Walkthrough" button.  Owner: tour engine.
// The dialog opens by itself when the provider's status is "offered" (first visit in this server session) and from
// the button at any time: then it offers Resume (when progress exists), Restart and the chapter list.
import { useEffect, useRef } from "react";
import { CHAPTERS, STEPS } from "@/tour";
import { useTour } from "./TourProvider";

const ABOUT = [
  "Layer 0 takes one bid opportunity from the moment an RFP arrives to the final response: it reads the RFP into requirement line items with exact page and line sources.",
  "Each line item is matched to a business unit's product; participation and the go/no-go decision are recorded with their rationale.",
  "Every participating unit gets one work package, answers it as a checklist, and the bid manager validates and consolidates the answers.",
  "Agents propose, people decide: every proposal is reviewed by a named person and every action is written to an append-only audit trail.",
];

export function WalkthroughButton() {
  const t = useTour();
  return (
    // "raised" lifts the button above the overlay's backdrop while the walkthrough runs, so it stays reachable.
    <button type="button" className={`button secondary tour-launch ${t.status === "running" ? "raised" : ""}`} data-tour="shell-help" onClick={t.openDialog}
      title="Guided walkthrough of every screen" aria-haspopup="dialog">
      Walkthrough
    </button>
  );
}

export default function TourLauncher() {
  const t = useTour();
  const open = t.status === "offered" || t.dialogOpen;
  const box = useRef<HTMLDivElement>(null);
  const primary = useRef<HTMLButtonElement>(null);
  useEffect(() => { if (open) primary.current?.focus(); }, [open]);
  if (!open) return null;

  const firstVisit = t.status === "offered";
  const close = () => { if (firstVisit) t.skip(); else t.closeDialog(); };
  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") { e.preventDefault(); close(); return; }
    if (e.key !== "Tab" || !box.current) return;
    const items = box.current.querySelectorAll<HTMLElement>("button:not(:disabled), [href]");
    if (items.length === 0) return;
    const first = items[0], last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  };
  const current = t.step?.chapter;

  return (
    <div className="tour-launch-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) close(); }}>
      <div ref={box} className="tour-launch-dialog" role="dialog" aria-modal="true" aria-labelledby="tour-launch-title" onKeyDown={onKeyDown}>
        <div className="tour-launch-head">
          <h2 id="tour-launch-title">{firstVisit ? "Welcome to Layer 0" : "Guided walkthrough"}</h2>
          <button type="button" className="tour-x" onClick={close} aria-label="Close">×</button>
        </div>
        <ul className="tour-launch-about">{ABOUT.map((l, i) => <li key={i}>{l}</li>)}</ul>
        <p className="tour-launch-time">
          The walkthrough explains every screen, component and action, and lets you run a bid end to end on a sample RFP.
          It takes about <strong>25 to 30 minutes</strong>; you can leave at any time (Esc) and continue later from the <strong>Walkthrough</strong> button in the top bar.
          {t.status === "done" && " You completed it in this session; start again or jump to a chapter."}
        </p>
        <ol className="tour-launch-chapters" aria-label="Chapters">
          {CHAPTERS.map((c) => (
            <li key={c.id} className={c.id === current && t.status !== "done" ? "current" : t.chapterDone(c.id) ? "done" : ""}>
              <button type="button" className="link" disabled={c.steps.length === 0} onClick={() => t.goToChapter(c.id)}
                title={c.steps.length ? `Open chapter ${c.order}` : "No steps yet"}>
                <span className="tour-menu-no" aria-hidden>{t.chapterDone(c.id) ? "✓" : c.order}</span>
                <span className="tour-menu-text">
                  <span className="tour-menu-title">{c.title} <span className="muted">({c.steps.length} {c.steps.length === 1 ? "step" : "steps"})</span></span>
                  {c.summary && <span className="tour-menu-sum">{c.summary}</span>}
                </span>
              </button>
            </li>
          ))}
        </ol>
        <div className="tour-launch-actions">
          {firstVisit ? (
            <>
              <button type="button" className="secondary" onClick={t.skip}>Not now</button>
              <button ref={primary} type="button" onClick={t.start} disabled={STEPS.length === 0}>Start walkthrough</button>
            </>
          ) : (
            <>
              <button type="button" className="secondary" onClick={t.closeDialog}>Close</button>
              <button type="button" className="secondary" onClick={t.restart} disabled={STEPS.length === 0}>Restart</button>
              {t.canResume && <button ref={primary} type="button" onClick={t.resume}>Resume</button>}
              {!t.canResume && <button ref={primary} type="button" onClick={t.start} disabled={STEPS.length === 0}>Start walkthrough</button>}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
