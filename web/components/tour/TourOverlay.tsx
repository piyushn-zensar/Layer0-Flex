"use client";
// Walkthrough overlay: dimmed backdrop with a spotlight around the step's target, and the step bubble.  Owner: tour engine.
//
// The backdrop is four fixed rectangles around the spotlight (top, bottom, left, right), so the hole itself has no
// element over it: clicks there reach the page when the step allows interaction (action steps by default). When
// it does not, a fifth transparent rectangle covers the hole and blocks clicks. The target rectangle is re-measured
// every animation frame (cheap: one getBoundingClientRect) and on ResizeObserver callbacks, so scrolling, resizing
// and late layout shifts keep the spotlight on the element. Z-order: backdrop 30 (above cards and sticky table
// heads, below the app's own dialogs at 40, so a confirmation dialog a step asks for stays usable), bubble 45
// (above those dialogs, below toasts at 50).
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CHAPTERS } from "@/tour";
import { useTour } from "./TourProvider";

type Rect = { top: number; left: number; width: number; height: number };
const PAD = 6;          // spotlight padding around the target
const GAP = 12;         // bubble distance from the spotlight
const EDGE = 8;         // bubble distance from the viewport edge
const MOBILE_MAX = 700; // docked bubble under this width

/** Inline markup: **bold** and `code`. */
function inline(s: string): React.ReactNode[] {
  return s.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={i}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("`") && part.endsWith("`")) return <code key={i}>{part.slice(1, -1)}</code>;
    return <span key={i}>{part}</span>;
  });
}

/** Paragraphs from a string (blank-line separated) or an array. */
export function Body({ body }: { body: string | string[] }) {
  const paras = (Array.isArray(body) ? body : body.split(/\n\s*\n/)).map((p) => p.trim()).filter(Boolean);
  return <>{paras.map((p, i) => <p key={i}>{inline(p)}</p>)}</>;
}

const same = (a: Rect | null, b: Rect | null) => (!a && !b) || (!!a && !!b && a.top === b.top && a.left === b.left && a.width === b.width && a.height === b.height);

export default function TourOverlay() {
  const t = useTour();
  if (t.status !== "running" || !t.step) return null;
  return <Overlay key={t.step.id} />;
}

function Overlay() {
  const t = useTour();
  const step = t.step!;
  const bubble = useRef<HTMLDivElement>(null);
  const [rect, setRect] = useState<Rect | null>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });
  const [vp, setVp] = useState({ w: 1024, h: 768 });
  const [menu, setMenu] = useState(false);
  const allow = step.allowInteraction ?? step.kind === "action";
  const waiting = (step.kind === "action" || step.kind === "wait") && !t.done;

  // ---- measure the target every frame; the element may be replaced by a re-render, so query it by id each time ----
  useEffect(() => {
    let raf = 0;
    let last: Rect | null = null;
    let ro: ResizeObserver | undefined;
    let observed: Element | null = null;
    const measure = () => {
      const el = step.target && t.target !== "missing" ? t.ctx.el(step.target) : null;
      let r: Rect | null = null;
      if (el) {
        const b = el.getBoundingClientRect();
        if (b.width > 0 || b.height > 0) r = { top: Math.round(b.top), left: Math.round(b.left), width: Math.round(b.width), height: Math.round(b.height) };
        if (observed !== el && ro) { if (observed) ro.unobserve(observed); ro.observe(el); observed = el; }
      }
      if (!same(r, last)) { last = r; setRect(r); }
      const w = window.innerWidth, h = window.innerHeight;
      setVp((v) => (v.w === w && v.h === h ? v : { w, h }));
      if (bubble.current) {
        const bw = bubble.current.offsetWidth, bh = bubble.current.offsetHeight;
        setSize((s) => (s.w === bw && s.h === bh ? s : { w: bw, h: bh }));
      }
      raf = requestAnimationFrame(measure);
    };
    try { ro = new ResizeObserver(measure); } catch { ro = undefined; }
    raf = requestAnimationFrame(measure);
    return () => { cancelAnimationFrame(raf); ro?.disconnect(); };
  }, [step.target, t.target, t.ctx]);

  // ---- focus the bubble when the step changes (the Overlay is keyed by step id) ----
  useEffect(() => { bubble.current?.focus({ preventScroll: true }); }, []);

  // ---- keyboard: Esc exits, arrows move (not while typing in a form field) ----
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement | null)?.tagName ?? "";
      const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(tag) || (e.target as HTMLElement | null)?.isContentEditable;
      if (e.key === "Escape") { if (menu) { setMenu(false); return; } if (!typing) { e.preventDefault(); t.exit(); } return; }
      if (typing) return;
      if (e.key === "ArrowRight" && !waiting) { e.preventDefault(); t.next(); }
      if (e.key === "ArrowLeft") { e.preventDefault(); t.prev(); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [t, waiting, menu]);

  // ---- bubble position ----
  const docked = vp.w < MOBILE_MAX;
  const style = useMemo<React.CSSProperties>(() => {
    if (docked) return {};
    if (!rect || size.w === 0) return { top: "50%", left: "50%", transform: "translate(-50%, -50%)" };
    const hole = { top: rect.top - PAD, left: rect.left - PAD, width: rect.width + 2 * PAD, height: rect.height + 2 * PAD };
    const bw = size.w, bh = size.h;
    const clampX = (x: number) => Math.min(Math.max(x, EDGE), Math.max(EDGE, vp.w - bw - EDGE));
    const clampY = (y: number) => Math.min(Math.max(y, EDGE), Math.max(EDGE, vp.h - bh - EDGE));
    const centreX = hole.left + hole.width / 2 - bw / 2, centreY = hole.top + hole.height / 2 - bh / 2;
    const fits = { bottom: hole.top + hole.height + GAP + bh <= vp.h - EDGE, top: hole.top - GAP - bh >= EDGE,
      right: hole.left + hole.width + GAP + bw <= vp.w - EDGE, left: hole.left - GAP - bw >= EDGE };
    let place: "auto" | "top" | "bottom" | "left" | "right" | "none" = step.placement ?? "auto";
    if (place === "auto" || !fits[place as keyof typeof fits]) place = (["bottom", "top", "right", "left"] as const).find((p) => fits[p]) ?? "none";
    switch (place) {
      case "bottom": return { top: hole.top + hole.height + GAP, left: clampX(centreX) };
      case "top": return { top: hole.top - GAP - bh, left: clampX(centreX) };
      case "right": return { top: clampY(centreY), left: hole.left + hole.width + GAP };
      case "left": return { top: clampY(centreY), left: hole.left - GAP - bw };
      default: // nothing fits beside the spotlight (a huge target): bottom-right corner, over the dim
        return { top: clampY(vp.h - bh - EDGE), left: clampX(vp.w - bw - EDGE) };
    }
  }, [rect, size, vp, docked, step.placement]);

  const hole = rect ? { top: rect.top - PAD, left: rect.left - PAD, width: rect.width + 2 * PAD, height: rect.height + 2 * PAD } : null;
  const finished = (step.kind === "action" || step.kind === "wait") && t.done;
  const showFallback = step.target && !finished && (t.target === "missing" || (t.target !== "searching" && !rect));
  const stop = useCallback((e: React.SyntheticEvent) => e.stopPropagation(), []);
  // Action steps let the person use the whole page (the spotlight only points): an action often continues outside
  // the target (a form that opens in the row, a bulk bar, a confirmation dialog). Explain steps keep the page blocked.
  const dim = `tour-dim ${allow ? "tour-dim-pass" : ""}`;

  return (
    <div className="tour-root" data-tour-open>
      {/* backdrop: four rectangles around the spotlight, or one full-screen sheet for a centred step */}
      {hole ? (
        <>
          <div className={dim} style={{ top: 0, left: 0, right: 0, height: Math.max(0, hole.top) }} />
          <div className={dim} style={{ top: hole.top + hole.height, left: 0, right: 0, bottom: 0 }} />
          <div className={dim} style={{ top: hole.top, left: 0, width: Math.max(0, hole.left), height: hole.height }} />
          <div className={dim} style={{ top: hole.top, left: hole.left + hole.width, right: 0, height: hole.height }} />
          {!allow && <div className="tour-dim tour-dim-hole" style={{ top: hole.top, left: hole.left, width: hole.width, height: hole.height }} title="Explained in the walkthrough; use Next to continue" />}
          <div className="tour-ring" style={{ top: hole.top, left: hole.left, width: hole.width, height: hole.height }} aria-hidden />
        </>
      ) : <div className={`${dim} tour-dim-all`} />}

      <div ref={bubble} className={`tour-bubble ${docked ? "docked" : ""} ${step.kind === "wait" ? "wait" : ""}`} style={style} role="dialog"
        aria-modal="false" aria-labelledby="tour-title" tabIndex={-1} onMouseDown={stop} onClick={stop}
        data-step={step.id} data-target={step.target ? t.target : "none"} data-done={t.done ? "true" : "false"}>
        <div className="tour-head">
          <div className="tour-crumb">
            <span className="tour-chapter">{t.chapter?.order}. {t.chapter?.title}</span>
            <span className="tour-pos">Step {t.stepInChapter} of {t.chapterSteps} (chapter) · {t.index + 1} of {t.total} overall</span>
          </div>
          <button type="button" className="tour-x" onClick={t.exit} aria-label="Exit walkthrough (Esc)">×</button>
        </div>
        <div className="sr-only" aria-live="polite">{`${t.chapter?.title}: ${step.title}. Step ${t.stepInChapter} of ${t.chapterSteps}.`}</div>
        <h2 id="tour-title" className="tour-title">{step.title}</h2>
        <div className="tour-body"><Body body={step.body} /></div>
        {t.target === "searching" && step.target && <p className="tour-note">Finding this on the page…</p>}
        {showFallback && <p className="tour-note tour-fallback">{step.fallback ?? "This element is not on the page right now; the explanation above still applies."}</p>}
        {finished && step.kind === "action" && <p className="tour-note tour-done">Done. Press Next to continue.</p>}
        {step.instruction && step.kind !== "wait" && <p className="tour-instruction"><strong>Do this now:</strong> {inline(step.instruction)}</p>}
        {step.kind === "wait" && !t.done && <p className="tour-instruction tour-waiting"><span className="tour-spinner" aria-hidden /> Working… this step continues by itself when the page is ready.</p>}
        {t.error && <p className="tour-error" role="alert">{t.error}</p>}
        <div className="tour-actions">
          <div className="tour-actions-left">
            {step.example && <button type="button" className="secondary sm" disabled={t.busy} onClick={t.applyExample}>{t.busy ? "Applying…" : `Use example: ${step.example.label}`}</button>}
          </div>
          <div className="tour-actions-right">
            <button type="button" className="secondary sm" onClick={t.prev} disabled={t.index === 0}>Previous</button>
            {waiting ? (
              <>
                <button type="button" className="sm" disabled aria-disabled="true"><span className="tour-spinner" aria-hidden /> Waiting…</button>
                <button type="button" className="link sm tour-continue" onClick={t.next}>Continue anyway</button>
              </>
            ) : (
              <button type="button" className="sm" onClick={t.index + 1 >= t.total ? t.finish : t.next}>{t.index + 1 >= t.total ? "Finish" : "Next"}</button>
            )}
          </div>
        </div>
        <div className="tour-foot">
          <button type="button" className="link" aria-expanded={menu} onClick={() => setMenu((m) => !m)}>Chapters</button>
          <span aria-hidden>·</span>
          <button type="button" className="link" onClick={t.skip}>Skip walkthrough</button>
          <span aria-hidden>·</span>
          <button type="button" className="link" onClick={t.exit}>Exit</button>
          <span className="tour-keys" aria-hidden>Esc exits · ← → move</span>
        </div>
        {menu && (
          <ol className="tour-menu" aria-label="Chapters">
            {CHAPTERS.map((c) => (
              <li key={c.id} className={c.id === step.chapter ? "current" : t.chapterDone(c.id) ? "done" : ""}>
                <button type="button" className="link" disabled={c.steps.length === 0} onClick={() => { setMenu(false); t.goToChapter(c.id); }}>
                  <span className="tour-menu-no" aria-hidden>{t.chapterDone(c.id) ? "✓" : c.order}</span>
                  <span className="tour-menu-text"><span className="tour-menu-title">{c.title}</span>{c.summary && <span className="tour-menu-sum">{c.summary}</span>}
                    {c.steps.length === 0 && <span className="tour-menu-sum">(no steps yet)</span>}</span>
                </button>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}
