"use client";
// Walkthrough engine: a state machine over the chapters and steps in web/tour.  Owner: tour engine.
//
// How it runs
//   - Progress lives in localStorage "layer0.tour": {session, status, chapter, step, ctx: {oppId, data}}. It is
//     written on every change, so a browser refresh or a hot reload (HMR) continues at the same step. The session id
//     comes from GET /tour-session (a new id per dev-server start): a different id resets progress and offers the
//     welcome dialog again; the same id with status skipped/done keeps quiet; status running resumes on any page.
//   - Entering a step: skipIf is evaluated in the direction of travel (Next or Previous) and skipped steps are
//     passed over. If the step has a route and the page is elsewhere, the engine router.push()es it, then polls for
//     the step's data-tour target for up to 10 s; onEnter runs once the target is on the page (at once for a step
//     without a target). A missing target never throws: the bubble is centred and shows step.fallback.
//   - action / wait steps: done(ctx) is checked every 500 ms and after DOM changes (MutationObserver); Next is
//     enabled only when it is true. "Continue anyway" always works. Previous re-enters the step, so done() is
//     re-checked; explain steps are safe to revisit (no API call is made by the engine itself).
//   - ctx.oppId defaults to DEMO_OPP. A chapter may set it with `ctx.oppId = id` (the property has a setter) or
//     ctx.set("oppId", id); both persist. ctx.setActor(name) writes the actor cookie, saves progress and reloads
//     the page: every page re-fetches as that person and the walkthrough resumes at the same step.
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api, currentActor, post, setActor as setActorCookie } from "@/lib/api";
import { CHAPTERS, DEMO_OPP, STEPS, resolveRoute, type TourChapter, type TourCtx, type TourStep } from "@/tour";

export type TourStatus = "loading" | "offered" | "running" | "skipped" | "done";
export type TargetState = "none" | "searching" | "found" | "missing";
type Stored = { session: string; status: TourStatus; chapter: string; step: string; ctx: { oppId: string; data: Record<string, unknown> } };

export const STORAGE_KEY = "layer0.tour";
const TARGET_WAIT_MS = 10_000;
const DONE_POLL_MS = 500;

type Step = TourStep & { chapter: string };

export interface TourApi {
  status: TourStatus;
  /** Index into STEPS. */
  index: number;
  step: Step | null;
  chapter: TourChapter | null;
  /** 1-based position inside the chapter, and the chapter's step count. */
  stepInChapter: number;
  chapterSteps: number;
  total: number;
  ctx: TourCtx;
  target: TargetState;
  /** done() result for the current action / wait step (true for explain steps). */
  done: boolean;
  /** "Use example" in progress. */
  busy: boolean;
  /** Last error from an example or an onEnter, shown in the bubble. */
  error: string | null;
  dialogOpen: boolean;
  openDialog: () => void;
  closeDialog: () => void;
  start: () => void;
  resume: () => void;
  restart: () => void;
  next: () => void;
  prev: () => void;
  /** "Skip walkthrough": closes it and clears progress for this session. */
  skip: () => void;
  /** "Exit": closes it but keeps the position, so Resume continues here. */
  exit: () => void;
  goToChapter: (id: string) => void;
  finish: () => void;
  applyExample: () => void;
  /** Chapters finished (every step before the current one), for the ticks in the chapter list. */
  chapterDone: (id: string) => boolean;
  /** Whether a stored position exists to resume (running or exited part-way). */
  canResume: boolean;
}

const noop = () => {};
const emptyCtx: TourCtx = {
  oppId: DEMO_OPP, actor: "Bid Manager", pathname: "/", data: {}, set: noop, get: () => undefined, go: noop,
  api: () => Promise.reject(new Error("walkthrough not mounted")), post: () => Promise.reject(new Error("walkthrough not mounted")),
  el: () => null, setActor: noop,
};
const Ctx = createContext<TourApi>({
  status: "loading", index: 0, step: null, chapter: null, stepInChapter: 0, chapterSteps: 0, total: STEPS.length, ctx: emptyCtx,
  target: "none", done: true, busy: false, error: null, dialogOpen: false, openDialog: noop, closeDialog: noop, start: noop, resume: noop,
  restart: noop, next: noop, prev: noop, skip: noop, exit: noop, goToChapter: noop, finish: noop, applyExample: noop,
  chapterDone: () => false, canResume: false,
});

/** First STEPS index of a chapter (-1 when the chapter has no steps). */
const firstIndex = (chapterId: string) => STEPS.findIndex((s) => s.chapter === chapterId);
const lastIndex = (chapterId: string) => { let i = -1; STEPS.forEach((s, n) => { if (s.chapter === chapterId) i = n; }); return i; };
const findEl = (id: string): HTMLElement | null => {
  if (typeof document === "undefined") return null;
  try { return document.querySelector<HTMLElement>(`[data-tour="${id.replace(/"/g, "")}"]`); } catch { return null; }
};
const readStored = (): Stored | null => {
  try { const raw = localStorage.getItem(STORAGE_KEY); return raw ? (JSON.parse(raw) as Stored) : null; } catch { return null; }
};
const writeStored = (s: Stored) => { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); } catch { /* private window, quota */ } };
const text = (e: unknown) => (e instanceof Error ? e.message : String(e)).replace(/^Error:\s*/, "");

/** The route a step lives on: its own, else the chapter's entryRoute when the step opens the chapter. */
function routeOf(step: Step, index: number): string | undefined {
  if (step.route) return step.route;
  const chapter = CHAPTERS.find((c) => c.id === step.chapter);
  return chapter && firstIndex(chapter.id) === index ? chapter.entryRoute : undefined;
}

export function TourProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "/";
  const router = useRouter();
  const [status, setStatus] = useState<TourStatus>("loading");
  const [session, setSession] = useState<string>("");
  const [index, setIndex] = useState(0);
  const [data, setData] = useState<Record<string, unknown>>({});
  const [actor, setActorState] = useState("Bid Manager");
  const [target, setTarget] = useState<TargetState>("none");
  const [done, setDone] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const hydrated = useRef(false);
  const navigatedFor = useRef("");
  const dataRef = useRef(data);
  dataRef.current = data;
  const oppId = typeof data.oppId === "string" && data.oppId ? data.oppId : DEMO_OPP;

  // ----- the context handed to steps -----
  const ctx = useMemo<TourCtx>(() => {
    const set = (key: string, value: unknown) => setData((d) => ({ ...d, [key]: value }));
    const c: TourCtx = {
      oppId, actor, pathname, data, set,
      get: <T,>(key: string) => dataRef.current[key] as T | undefined,
      go: (path) => router.push(path),
      api: (path) => api(path),
      post: (path, body) => post(path, body),
      el: findEl,
      setActor: (name) => {
        setActorCookie(name);
        const stored = readStored();
        if (stored) writeStored({ ...stored, ctx: { oppId: oppId, data: dataRef.current } }); // progress first, then the reload
        location.reload();
      },
    };
    // `ctx.oppId = "OPP-0003"` persists like ctx.set("oppId", ...): chapter files may use either.
    Object.defineProperty(c, "oppId", { get: () => (typeof dataRef.current.oppId === "string" && dataRef.current.oppId ? dataRef.current.oppId : DEMO_OPP),
      set: (v: string) => set("oppId", v), enumerable: true });
    return c;
  }, [oppId, actor, pathname, data, router]);
  const ctxRef = useRef(ctx);
  ctxRef.current = ctx;

  const step: Step | null = status === "running" ? STEPS[index] ?? null : null;
  const chapter = step ? CHAPTERS.find((c) => c.id === step.chapter) ?? null : null;
  const stepInChapter = step && chapter ? index - firstIndex(chapter.id) + 1 : 0;

  // ----- session + stored progress (once per page load) -----
  useEffect(() => {
    setActorState(currentActor());
    let cancelled = false;
    (async () => {
      let id = "";
      try { id = (await (await fetch("/tour-session", { cache: "no-store" })).json()).id as string; } catch { id = "no-session"; }
      if (cancelled) return;
      const stored = readStored();
      if (!stored || stored.session !== id) { // a new server run: reset and offer the walkthrough
        setSession(id); setIndex(0); setData({}); setStatus("offered");
      } else {
        setSession(id);
        setData(stored.ctx?.data ?? {});
        let i = STEPS.findIndex((s) => s.id === stored.step);
        if (i < 0) i = Math.max(0, firstIndex(stored.chapter)); // a step id that no longer exists: the chapter start
        setIndex(i);
        setStatus(stored.status === "running" || stored.status === "skipped" || stored.status === "done" ? stored.status : "offered");
      }
      hydrated.current = true;
    })();
    return () => { cancelled = true; };
  }, []);

  // ----- tell the pages which opportunity the walkthrough works on (<html data-tour-opp>): the inbox uses it to put
  // that opportunity's rows under its first-row targets -----
  useEffect(() => {
    const root = document.documentElement;
    if (status === "running") root.setAttribute("data-tour-opp", oppId); else root.removeAttribute("data-tour-opp");
    return () => root.removeAttribute("data-tour-opp");
  }, [status, oppId]);

  // ----- persist on every change -----
  useEffect(() => {
    if (!hydrated.current || status === "loading") return;
    const s = STEPS[index];
    writeStored({ session, status, chapter: s?.chapter ?? "welcome", step: s?.id ?? "", ctx: { oppId, data } });
  }, [session, status, index, data, oppId]);

  // ----- enter a step: route, target, onEnter -----
  useEffect(() => {
    if (!step) { setTarget("none"); return; }
    const route = routeOf(step, index);
    const want = route ? resolveRoute(route, { oppId }) : null;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    if (want && pathname !== want) {
      const key = `${index}:${want}`;
      if (navigatedFor.current !== key) { navigatedFor.current = key; router.push(want); }
      setTarget("searching");
      // the route may 404 (an opportunity that no longer exists): stop waiting after a while and show the fallback
      timer = setTimeout(() => { if (!cancelled) setTarget("missing"); }, TARGET_WAIT_MS);
      return () => { cancelled = true; clearTimeout(timer); };
    }
    // onEnter runs as soon as the page is the right one, and again (about once a second) while the target is still
    // missing, then once more when it appears. Many onEnter functions are what makes the target appear (choose a
    // filter chip, open a <details>, select a row), so they cannot wait for it; they are written to be idempotent.
    let entering = false;
    const enter = () => {
      if (!step.onEnter || entering) return;
      entering = true;
      Promise.resolve().then(() => step.onEnter!(ctxRef.current)).catch((e) => { if (!cancelled) setError(text(e)); }).finally(() => { entering = false; });
    };
    if (!step.target) { setTarget("none"); enter(); return () => { cancelled = true; }; }
    setTarget("searching");
    const started = Date.now();
    let ticks = 0;
    enter();
    const tick = () => {
      if (cancelled) return;
      const el = findEl(step.target!);
      if (el) {
        setTarget("found");
        try { el.scrollIntoView({ block: "center", inline: "nearest", behavior: "smooth" }); } catch { /* ignore */ }
        enter();
        return;
      }
      // After the wait the fallback text is shown, but the search goes on at a slower pace: an element that appears
      // later (a table that loads after a refresh, a details the person opens) is spotlighted as soon as it is there.
      const late = Date.now() - started > TARGET_WAIT_MS;
      if (late) setTarget("missing");
      if (++ticks % (late ? 4 : 5) === 0) enter();
      timer = setTimeout(tick, late ? 500 : 200);
    };
    tick();
    return () => { cancelled = true; clearTimeout(timer); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step?.id, index, pathname, oppId, status]);

  // ----- done() polling for action / wait steps -----
  useEffect(() => {
    setError(null);
    if (!step || (step.kind !== "action" && step.kind !== "wait") || !step.done) { setDone(true); return; }
    setDone(false);
    let cancelled = false, checking = false, finished = false;
    let debounce: ReturnType<typeof setTimeout> | undefined;
    const check = async () => {
      if (checking || finished || cancelled) return;
      checking = true;
      try { const ok = await step.done!(ctxRef.current); if (!cancelled && ok) { finished = true; setDone(true); stop(); } }
      catch { /* a failing check just means "not yet" */ }
      finally { checking = false; }
    };
    const interval = setInterval(check, DONE_POLL_MS);
    const mo = new MutationObserver(() => { clearTimeout(debounce); debounce = setTimeout(check, 150); });
    try { mo.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true }); } catch { /* ignore */ }
    const stop = () => { clearInterval(interval); mo.disconnect(); clearTimeout(debounce); };
    check();
    return () => { cancelled = true; stop(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step?.id, status]);

  // ----- moving between steps -----
  const enterFrom = useCallback(async (from: number, dir: 1 | -1) => {
    let i = from + dir;
    while (i >= 0 && i < STEPS.length) {
      const s = STEPS[i];
      let skip = false;
      if (s.skipIf) { try { skip = !!(await s.skipIf(ctxRef.current)); } catch { skip = false; } }
      if (!skip) break;
      i += dir;
    }
    if (i >= STEPS.length) { setStatus("done"); setIndex(STEPS.length - 1); return; }
    setIndex(Math.max(0, i));
    setStatus("running");
  }, []);

  const start = useCallback(() => { setDialogOpen(false); setData({}); navigatedFor.current = ""; void enterFrom(-1, 1); }, [enterFrom]);
  const resume = useCallback(() => { setDialogOpen(false); setStatus("running"); }, []);
  const restart = useCallback(() => { setDialogOpen(false); setData({}); navigatedFor.current = ""; void enterFrom(-1, 1); }, [enterFrom]);
  const next = useCallback(() => { void enterFrom(index, 1); }, [enterFrom, index]);
  const prev = useCallback(() => { if (index > 0) void enterFrom(index, -1); }, [enterFrom, index]);
  const skip = useCallback(() => { setDialogOpen(false); setStatus("skipped"); setIndex(0); setData({}); }, []);
  const exit = useCallback(() => { setDialogOpen(false); setStatus("skipped"); }, []);
  const finish = useCallback(() => { setDialogOpen(false); setStatus("done"); }, []);
  const goToChapter = useCallback((id: string) => {
    const i = firstIndex(id);
    if (i < 0) return;
    setDialogOpen(false);
    void enterFrom(i - 1, 1);
  }, [enterFrom]);
  const applyExample = useCallback(() => {
    const s = STEPS[index];
    if (!s?.example) return;
    setBusy(true); setError(null);
    Promise.resolve().then(() => s.example!.apply(ctxRef.current)).catch((e) => setError(text(e))).finally(() => setBusy(false));
  }, [index]);
  const chapterDone = useCallback((id: string) => status === "done" || (status !== "loading" && lastIndex(id) >= 0 && lastIndex(id) < index && index > 0), [status, index]);
  const canResume = status === "running" || (status === "skipped" && index > 0);

  const value = useMemo<TourApi>(() => ({
    status, index, step, chapter, stepInChapter, chapterSteps: chapter?.steps.length ?? 0, total: STEPS.length, ctx, target, done, busy, error,
    dialogOpen, openDialog: () => setDialogOpen(true), closeDialog: () => setDialogOpen(false),
    start, resume, restart, next, prev, skip, exit, goToChapter, finish, applyExample, chapterDone, canResume,
  }), [status, index, step, chapter, stepInChapter, ctx, target, done, busy, error, dialogOpen, start, resume, restart, next, prev, skip, exit,
    goToChapter, finish, applyExample, chapterDone, canResume]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useTour(): TourApi {
  return useContext(Ctx);
}
