"use client";
// The panes of the main window (J-18, C-34): in the order and widths of the saved layout, with a splitter between neighbours, and a notice
// for each pane that is open in its own window. A pane in another window leaves this grid and returns when that window closes.
// On a narrow screen (up to 1100 px) the panes stack: dragging, resizing and the splitters are off (CSS hides them).  Owner: Janvia.
import { Fragment, useLayoutEffect, useRef, useState } from "react";
import { EmptyState } from "@/components/ui";
import Pane1Rfp from "./Pane1Rfp";
import Pane2Register from "./Pane2Register";
import Pane3Mapping from "./Pane3Mapping";
import PaneFrame from "./PaneFrame";
import { useWorkspace } from "./TraceWorkspace";
import { MIN_PX, columns, resizePair } from "./layout";
import { PANE_NAMES, type Pane } from "./types";

export const PaneBody = ({ pane }: { pane: Pane }) => (pane === 1 ? <Pane1Rfp /> : pane === 2 ? <Pane2Register /> : <Pane3Mapping />);

const px = (p: Pane) => document.querySelector<HTMLElement>(`[data-pane="${p}"]`)?.getBoundingClientRect().width ?? 0;

/** The bar between two neighbouring panes: drag it (mouse or touch) or use the arrow keys, Home and End. */
function Splitter({ left, right, hidden }: { left: Pane; right: Pane; hidden: boolean }) {
  const ws = useWorkspace();
  const [active, setActive] = useState(false);
  const [share, setShare] = useState({ l: 0, r: 0, pair: 0, total: 0 });
  const start = useRef<{ x: number; l: number; r: number; w: Record<Pane, number> } | null>(null);
  useLayoutEffect(() => { // widths in pixels, for the values a screen reader and the label read out
    if (hidden) return;
    const l = px(left), r = px(right), total = ws.attached.reduce((s, p) => s + px(p), 0);
    setShare((s) => (Math.abs(s.l - l) < 1 && Math.abs(s.r - r) < 1 && Math.abs(s.total - total) < 1 ? s : { l, r, pair: l + r, total }));
  }, [ws.layout, ws.attached, hidden, left, right, active]);
  const pct = (n: number) => (share.total ? Math.round((n / share.total) * 100) : 0);
  const minPct = share.pair ? Math.round((MIN_PX / share.pair) * 100) : 0;
  const label = `${pct(share.l)}% | ${pct(share.r)}%`;
  const apply = (dx: number, fromStart?: { l: number; r: number; w: Record<Pane, number> }, persist = true) =>
    ws.setLayout({ ...ws.layout, widths: resizePair(fromStart?.w ?? ws.layout.widths, left, right, fromStart?.l ?? px(left), fromStart?.r ?? px(right), dx) }, persist);
  return (
    <div className={`ws-split${active ? " active" : ""}`} data-tour={`trace-split-${left}`} role="separator" aria-orientation="vertical" tabIndex={hidden ? -1 : 0} hidden={hidden}
      aria-label={`Resize: pane ${left}: ${PANE_NAMES[left]} and pane ${right}: ${PANE_NAMES[right]}`}
      aria-valuemin={minPct} aria-valuemax={100 - minPct} aria-valuenow={share.pair ? Math.round((share.l / share.pair) * 100) : 50}
      aria-valuetext={`Pane ${left} is ${pct(share.l)} percent wide, pane ${right} is ${pct(share.r)} percent wide`}
      title="Drag to resize. Arrow keys resize, Shift makes bigger steps, Home and End go to the limits." data-label={label}
      onPointerDown={(e) => {
        if (e.pointerType === "mouse" && e.button !== 0) return;
        e.currentTarget.setPointerCapture(e.pointerId); e.preventDefault();
        start.current = { x: e.clientX, l: px(left), r: px(right), w: ws.layout.widths }; setActive(true);
      }}
      onPointerMove={(e) => { const s = start.current; if (s) apply(e.clientX - s.x, s, false); }}
      onPointerUp={() => { if (start.current) { start.current = null; setActive(false); ws.persistLayout(); } }}
      onPointerCancel={() => { if (start.current) { start.current = null; setActive(false); ws.persistLayout(); } }}
      onKeyDown={(e) => {
        const step = e.shiftKey ? 96 : 24;
        const dx = e.key === "ArrowLeft" ? -step : e.key === "ArrowRight" ? step : e.key === "Home" ? -1e6 : e.key === "End" ? 1e6 : 0;
        if (!dx) return;
        e.preventDefault(); apply(dx);
      }} />
  );
}

export default function Workspace() {
  const ws = useWorkspace();
  const zoom = ws.enlarged !== null;
  return (<>
    <div className="sr-only" role="status" aria-live="polite" data-tour="trace-notice">{ws.notice}</div>
    {ws.detached.length > 0 && (
      <div className="ws-detached" data-tour="trace-detached">
        {ws.detached.map((p) => (
          <div key={p} className="ws-detached-row" role="group" aria-label={`Pane ${p} is in another window`}>
            <span><strong>Pane {p}: {PANE_NAMES[p]}</strong> is open in another window.</span>
            <button type="button" className="secondary sm" onClick={() => ws.showPane(p)} aria-label={`Show the window of pane ${p}: ${PANE_NAMES[p]}`}>Show window</button>
            <button type="button" className="secondary sm" onClick={() => ws.returnPane(p)} aria-label={`Return pane ${p}: ${PANE_NAMES[p]} to the main window`}>Return to main window</button>
          </div>))}
      </div>)}
    {ws.attached.length === 0
      ? <EmptyState title="All three panes are open in other windows" hint="Use Return to main window above to bring a pane back here." />
      : (
      <div className={`three ws${zoom ? " zoom" : ""}`} style={{ "--ws-cols": columns(ws.attached, ws.layout.widths) } as React.CSSProperties} data-tour="trace-panes">
        {ws.attached.map((p, i) => (
          <Fragment key={p}>
            {i > 0 && <Splitter left={ws.attached[i - 1]} right={p} hidden={zoom} />}
            <PaneFrame pane={p}><PaneBody pane={p} /></PaneFrame>
          </Fragment>))}
      </div>)}
  </>);
}
