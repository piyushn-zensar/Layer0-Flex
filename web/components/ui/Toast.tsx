"use client";
// Toasts: short confirmations and errors that replace window.alert.  Owner: Janvia.
// <ToastProvider> is mounted once in app/layout.tsx; pages call useToast():
//   const toast = useToast();
//   post(url).then(() => toast.success("Baseline frozen."), (e) => toast.error(errorMessage(e)));
// success/info go after 5 s, errors after 8 s; a click or the close button dismisses one early. Four at most.
import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";

export type ToastKind = "success" | "error" | "info";
type Toast = { id: number; kind: ToastKind; text: string };
type Api = {
  show: (kind: ToastKind, text: string) => void;
  success: (text: string) => void; error: (text: string) => void; info: (text: string) => void;
};

const TTL: Record<ToastKind, number> = { success: 5000, info: 5000, error: 8000 };
const noop = () => {};
const Ctx = createContext<Api>({ show: noop, success: noop, error: noop, info: noop });

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const next = useRef(1);
  const dismiss = useCallback((id: number) => setToasts((t) => t.filter((x) => x.id !== id)), []);
  const show = useCallback((kind: ToastKind, text: string) => {
    const id = next.current++;
    setToasts((t) => [...t.slice(-3), { id, kind, text }]);
    setTimeout(() => dismiss(id), TTL[kind]);
  }, [dismiss]);
  const api = useMemo<Api>(() => ({
    show, success: (t) => show("success", t), error: (t) => show("error", t), info: (t) => show("info", t),
  }), [show]);

  return (
    <Ctx.Provider value={api}>
      {children}
      {/* one polite live region for successes, an assertive one for errors, so screen readers announce both */}
      <div className="toasts">
        <div className="sr-only" aria-live="polite">{toasts.filter((t) => t.kind !== "error").map((t) => t.text).join(". ")}</div>
        <div className="sr-only" aria-live="assertive">{toasts.filter((t) => t.kind === "error").map((t) => t.text).join(". ")}</div>
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.kind}`} onClick={() => dismiss(t.id)}>
            <span className="toast-text">{t.text}</span>
            <button type="button" className="alert-close" aria-label="Dismiss" onClick={(e) => { e.stopPropagation(); dismiss(t.id); }}>×</button>
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}

/** Toast API; a no-op outside the provider (tests, server rendering). */
export function useToast(): Api {
  return useContext(Ctx);
}
