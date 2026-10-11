// Guided walkthrough: step and chapter definitions. The engine (components/tour) runs them; each page group
// writes its own chapter in tour/chapters/. Plain data plus small functions, no dependencies.  Owner: Piyush.

/** What the walkthrough knows while it runs. Kept in localStorage so a page reload continues where it was. */
export interface TourCtx {
  /** The opportunity the walkthrough works on: the one created in chapter 4, else the seeded demo OPP-0001. */
  oppId: string;
  /** Current "Acting as" person (the actor cookie). */
  actor: string;
  /** Current pathname. */
  pathname: string;
  /** Free values a step stores for later steps (e.g. the ID of a requirement it approved). */
  data: Record<string, unknown>;
  set: (key: string, value: unknown) => void;
  get: <T = unknown>(key: string) => T | undefined;
  /** Client-side navigation (Next router). */
  go: (path: string) => void;
  /** GET /api/... as the current actor; rejects on a non-2xx. */
  api: <T = unknown>(path: string) => Promise<T>;
  /** POST /api/... as the current actor; rejects on a non-2xx. */
  post: <T = unknown>(path: string, body?: unknown) => Promise<T>;
  /** The element a data-tour id points at, if it is on the page right now. */
  el: (tourId: string) => HTMLElement | null;
  /** Set the acting person (cookie) and re-fetch the pages. */
  setActor: (name: string) => void;
}

export type Placement = "auto" | "top" | "bottom" | "left" | "right";

export interface TourStep {
  /** Stable, unique: "<chapter id>-<short name>", e.g. "requirements-approve". */
  id: string;
  title: string;
  /** One or more paragraphs. Light markup: **bold**, `code`, line breaks between paragraphs. */
  body: string | string[];
  /** The route this step lives on. "{opp}" is replaced by ctx.oppId. The engine navigates there when needed. */
  route?: string;
  /** data-tour id of the element to spotlight. None: a centred bubble. */
  target?: string;
  /** Where the bubble sits relative to the target. */
  placement?: Placement;
  /** Explicit "do this now" line, shown highlighted under the body. */
  instruction?: string;
  /** An example the person can apply with one click ("Use example"). */
  example?: { label: string; apply: (ctx: TourCtx) => void | Promise<void> };
  /**
   * explain: Next advances. action: Next is disabled until done() is true (checked every 500 ms and on DOM
   * changes); the person may still press "Continue anyway". wait: like action with no instruction, shows a spinner.
   */
  kind?: "explain" | "action" | "wait";
  /** Completion condition for action / wait steps. */
  done?: (ctx: TourCtx) => boolean | Promise<boolean>;
  /** Skip this step when it does not apply (e.g. the opportunity is already frozen). */
  skipIf?: (ctx: TourCtx) => boolean | Promise<boolean>;
  /** Runs when the step is shown: open a <details>, select a row, scroll a pane. */
  onEnter?: (ctx: TourCtx) => void | Promise<void>;
  /** Shown instead of the spotlight when the target is missing (the step still reads correctly). */
  fallback?: string;
  /** Let the person click inside the spotlight (default: true for action steps, false otherwise). */
  allowInteraction?: boolean;
}

export interface TourChapter {
  /** Stable id, also the step id prefix: "welcome", "portfolio", "navigation", "intake", "requirements", "trace",
   * "decisions", "inbox", "consolidation", "knowledge", "changes", "catalog", "recap". */
  id: string;
  /** Order in the walkthrough (1-based). */
  order: number;
  title: string;
  /** One or two sentences shown in the chapter list. */
  summary: string;
  /** Where the chapter starts ("{opp}" allowed); the engine navigates there when the chapter is opened directly. */
  entryRoute?: string;
  steps: TourStep[];
}

/** Replace {opp} in a route. */
export const resolveRoute = (route: string, ctx: Pick<TourCtx, "oppId">) => route.replace("{opp}", ctx.oppId);

/** The seeded demo opportunity used when the person skips creating one. */
export const DEMO_OPP = "OPP-0001";
