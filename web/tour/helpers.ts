// Small helpers for chapter files: completion conditions and checks that read the DOM or the API.  Owner: Piyush.
import type { TourCtx } from "./types";

/** True when an element with this data-tour id is on the page. */
export const present = (tourId: string) => (ctx: TourCtx) => ctx.el(tourId) !== null;

/** True when the pathname matches (exact, or a prefix when `prefix` is set). "{opp}" allowed. */
export const onRoute = (route: string, prefix = false) => (ctx: TourCtx) => {
  const want = route.replace("{opp}", ctx.oppId);
  return prefix ? ctx.pathname.startsWith(want) : ctx.pathname === want;
};

/** True when the element's visible text contains the words (case-insensitive). */
export const textIn = (tourId: string, words: string) => (ctx: TourCtx) =>
  (ctx.el(tourId)?.textContent ?? "").toLowerCase().includes(words.toLowerCase());

/** The opportunity record, or null when it cannot be read. */
export const opportunity = async (ctx: TourCtx) => {
  try { return (await ctx.api<{ opportunity: { id: string; status: string } }>(`/api/opportunities/${ctx.oppId}`)).opportunity; }
  catch { return null; }
};

/** True when the opportunity status is one of these. */
export const statusIn = (...statuses: string[]) => async (ctx: TourCtx) => {
  const o = await opportunity(ctx);
  return !!o && statuses.includes(o.status);
};

/** Open a <details> that holds the target (so the spotlight can see it). */
export const openDetails = (tourId: string) => (ctx: TourCtx) => {
  const el = ctx.el(tourId);
  const details = el?.closest("details");
  if (details && !details.open) details.open = true;
  el?.scrollIntoView({ block: "center", behavior: "smooth" });
};
