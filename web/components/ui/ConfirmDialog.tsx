"use client";
// Confirmation dialog that replaces window.confirm.  Owner: Janvia.
// Either render <ConfirmDialog open ... /> yourself, or use the hook, which keeps the state for you:
//   const [ask, confirmDialog] = useConfirm();
//   onClick={async () => { if (await ask({ title: "Discard the change set?", message: "The baseline stays as it is.", danger: true })) run(); }}
//   ... return <>{confirmDialog}...</>;
// Focus moves to the confirm button on open, Tab cycles inside the dialog, Esc or the backdrop cancels.
import { useCallback, useEffect, useRef, useState } from "react";

export type ConfirmProps = {
  open: boolean; title: string; message?: React.ReactNode;
  confirmLabel?: string; cancelLabel?: string; danger?: boolean; busy?: boolean;
  onConfirm: () => void; onCancel: () => void;
};

export default function ConfirmDialog({ open, title, message, confirmLabel = "Confirm", cancelLabel = "Cancel", danger, busy, onConfirm, onCancel }: ConfirmProps) {
  const box = useRef<HTMLDivElement>(null);
  const first = useRef<HTMLButtonElement>(null);
  useEffect(() => { if (open) first.current?.focus(); }, [open]);
  if (!open) return null;

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") { e.preventDefault(); onCancel(); return; }
    if (e.key !== "Tab" || !box.current) return;
    const items = box.current.querySelectorAll<HTMLElement>("button:not(:disabled), [href], input, select, textarea");
    if (items.length === 0) return;
    const firstEl = items[0], lastEl = items[items.length - 1];
    if (e.shiftKey && document.activeElement === firstEl) { e.preventDefault(); lastEl.focus(); }
    else if (!e.shiftKey && document.activeElement === lastEl) { e.preventDefault(); firstEl.focus(); }
  };

  return (
    <div className="dialog-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onCancel(); }}>
      <div ref={box} className="dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-title" onKeyDown={onKeyDown}>
        <h2 id="confirm-title">{title}</h2>
        {message && (typeof message === "string" ? <p>{message}</p> : message)}
        <div className="dialog-actions">
          <button type="button" className="secondary" disabled={busy} onClick={onCancel}>{cancelLabel}</button>
          <button ref={first} type="button" className={danger ? "danger" : ""} disabled={busy} onClick={onConfirm}>{confirmLabel}</button>
        </div>
      </div>
    </div>
  );
}

type AskOptions = Omit<ConfirmProps, "open" | "onConfirm" | "onCancel" | "busy">;

/** Promise-style confirm: `const [ask, dialog] = useConfirm()`; render `dialog` once, then `await ask({...})` gives true or false. */
export function useConfirm(): [(opts: AskOptions) => Promise<boolean>, React.ReactNode] {
  const [state, setState] = useState<{ opts: AskOptions; resolve: (ok: boolean) => void }>();
  const ask = useCallback((opts: AskOptions) => new Promise<boolean>((resolve) => setState({ opts, resolve })), []);
  const close = (ok: boolean) => { state?.resolve(ok); setState(undefined); };
  const dialog = state ? <ConfirmDialog open {...state.opts} onConfirm={() => close(true)} onCancel={() => close(false)} /> : null;
  return [ask, dialog];
}
