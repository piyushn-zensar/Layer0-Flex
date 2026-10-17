"use client";
// One pane with its heading row (J-12, J-18): the title, Linked / Unlinked, Enlarge / Restore, and the J-18 controls: a grip to drag the
// pane to a new place, Move left / right buttons, Open in new window; in a detached window, Return to main window.
// Every control has a name that says which pane it acts on (the three panes would otherwise all have an "Enlarge").  Owner: Janvia.
import { useWorkspace } from "./TraceWorkspace";
import { PANE_NAMES, type Pane } from "./types";

const GripIcon = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true" focusable="false">
    {[3, 7, 11].flatMap((y) => [4, 10].map((x) => <circle key={`${x}-${y}`} cx={x} cy={y} r="1.3" fill="currentColor" />))}
  </svg>
);

export default function PaneFrame({ pane, children }: { pane: Pane; children: React.ReactNode }) {
  const ws = useWorkspace();
  const name = PANE_NAMES[pane];
  const main = ws.mode === "main";
  const linked = ws.linked[pane];
  const at = ws.attached.indexOf(pane), count = ws.attached.length;
  const hidden = main && ws.enlarged !== null && ws.enlarged !== pane;
  const droppable = main && ws.dragFrom !== null && ws.dragFrom !== pane;
  return (
    <section className={`pane${ws.dragOver === pane && droppable ? " drop-target" : ""}${ws.dragFrom === pane ? " dragging" : ""}`}
      data-tour={`trace-pane-${pane}`} data-pane={pane} hidden={hidden}
      onDragOver={droppable ? (e) => { e.preventDefault(); e.dataTransfer.dropEffect = "move"; if (ws.dragOver !== pane) ws.overPane(pane); } : undefined}
      onDragLeave={droppable ? (e) => { if (!e.currentTarget.contains(e.relatedTarget as Node | null)) ws.overPane(null); } : undefined}
      onDrop={droppable ? (e) => { e.preventDefault(); ws.dropPane(pane); } : undefined}>
      <div className="pane-head">
        {main && (
          <div className="pane-arrange" role="group" aria-label={`Arrange pane ${pane}: ${name}`} data-tour={`trace-arrange-${pane}`}>
            <button type="button" className="pane-grip" draggable data-grip
              aria-label={`Drag pane ${pane}: ${name} to a new place. With the keyboard, press the left or right arrow key.`}
              title="Drag to reorder. Left and right arrow keys also move it."
              onDragStart={(e) => { e.dataTransfer.setData("application/x-layer0-pane", String(pane)); e.dataTransfer.effectAllowed = "move"; ws.startDrag(pane); }}
              onDragEnd={ws.endDrag}
              onKeyDown={(e) => { if (e.key === "ArrowLeft" || e.key === "ArrowRight") { e.preventDefault(); ws.move(pane, e.key === "ArrowLeft" ? -1 : 1); } }}>
              <GripIcon />
            </button>
            <button type="button" className="pane-move" data-move="-1" disabled={at <= 0} onClick={() => ws.move(pane, -1)}
              aria-label={`Move pane ${pane}: ${name} left (now position ${at + 1} of ${count})`} title="Move left"><span aria-hidden="true">◀</span></button>
            <button type="button" className="pane-move" data-move="1" disabled={at < 0 || at >= count - 1} onClick={() => ws.move(pane, 1)}
              aria-label={`Move pane ${pane}: ${name} right (now position ${at + 1} of ${count})`} title="Move right"><span aria-hidden="true">▶</span></button>
          </div>
        )}
        <h2>{pane} · {name}</h2>
        <div className="pane-tools">
          <button type="button" className={`chip${linked ? " on" : ""}`} onClick={() => ws.setLink(pane, !linked)} data-tour={`trace-link-${pane}`}
            aria-label={linked ? `Unlink pane ${pane}: ${name} (currently linked)` : `Link pane ${pane}: ${name} (currently unlinked)`}
            title="A linked pane follows the selected requirement; an unlinked pane keeps its place until you link it again.">
            {linked ? "Linked" : "Unlinked"}</button>
          {main && (
            <button type="button" className="secondary sm" onClick={() => ws.setEnlarged(ws.enlarged === pane ? null : pane)} data-tour={`trace-enlarge-${pane}`}
              aria-label={`${ws.enlarged === pane ? "Restore" : "Enlarge"} pane ${pane}: ${name}`}
              title={ws.enlarged === pane ? "Back to the three panes (Esc)" : "Show only this pane"}>{ws.enlarged === pane ? "Restore" : "Enlarge"}</button>)}
          {main && (
            <button type="button" className="secondary sm pane-detach" onClick={() => ws.openPane(pane)} data-tour={`trace-detach-${pane}`}
              aria-label={`Open pane ${pane}: ${name} in a new window`} title="Open this pane in its own window, for example on another screen">New window</button>)}
          {!main && (
            <button type="button" className="secondary sm" onClick={ws.returnToMain} data-tour="trace-return-pane"
              aria-label={`Return pane ${pane}: ${name} to the main window`} title="Close this window; the pane goes back to the main window">Return to main window</button>)}
        </div>
      </div>
      {children}
    </section>
  );
}
