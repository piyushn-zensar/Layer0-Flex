// Layout of the three panes in the main window (J-18, C-34): their order and their widths, kept per browser in localStorage.
// Pure functions, so they run without a browser: node web/components/workspace/layout.check.mjs (Node 22.18+ runs .ts files).
// Not stored: the selected requirement, the Linked switches and which panes are detached; those belong to the session.  Owner: Janvia.
import type { Pane } from "./types";

export const LAYOUT_KEY = "layer0.workspace.v1";
export const MIN_PX = 240;      // the narrowest a pane may be dragged to
export const GUTTER_PX = 10;    // the splitter between two panes

export type Layout = { order: Pane[]; widths: Record<Pane, number> };
/** Widths are relative weights (CSS fr), by pane, so a pane keeps its width when it is moved. */
export const DEFAULT_LAYOUT: Layout = { order: [1, 2, 3], widths: { 1: 1, 2: 1, 3: 1.3 } };

export const cloneLayout = (l: Layout): Layout => ({ order: [...l.order], widths: { ...l.widths } });
export const isDefaultLayout = (l: Layout) =>
  l.order.join() === DEFAULT_LAYOUT.order.join() && ([1, 2, 3] as Pane[]).every((p) => l.widths[p] === DEFAULT_LAYOUT.widths[p]);

const round3 = (n: number) => Math.round(n * 1000) / 1000;
const okWeight = (n: unknown): n is number => typeof n === "number" && Number.isFinite(n) && n >= 0.2 && n <= 10;

/** A saved layout, or the default when it is missing, from another version, or does not hold together. Never throws. */
export function parseLayout(raw: unknown): Layout {
  try {
    const v = typeof raw === "string" ? JSON.parse(raw) : raw;
    if (!v || typeof v !== "object" || (v as { v?: unknown }).v !== 1) return cloneLayout(DEFAULT_LAYOUT);
    const { order, widths } = v as { order?: unknown; widths?: Record<string, unknown> };
    const isPermutation = Array.isArray(order) && order.length === 3 && [1, 2, 3].every((p) => (order as unknown[]).includes(p));
    if (!isPermutation || !widths || !okWeight(widths[1]) || !okWeight(widths[2]) || !okWeight(widths[3])) return cloneLayout(DEFAULT_LAYOUT);
    return { order: [...(order as Pane[])], widths: { 1: round3(widths[1] as number), 2: round3(widths[2] as number), 3: round3(widths[3] as number) } };
  } catch { return cloneLayout(DEFAULT_LAYOUT); }
}
export const serialiseLayout = (l: Layout) => JSON.stringify({ v: 1, order: l.order, widths: l.widths });

/** The order after moving a pane one place left (-1) or right (+1); unchanged at the ends. */
export function moveBy(order: Pane[], pane: Pane, delta: -1 | 1): Pane[] {
  const i = order.indexOf(pane), j = i + delta;
  if (i < 0 || j < 0 || j >= order.length) return order;
  const next = [...order];
  [next[i], next[j]] = [next[j], next[i]];
  return next;
}

/** The order after dropping a dragged pane on another: it takes the other pane's place and the rest shift. */
export function dropOn(order: Pane[], dragged: Pane, target: Pane): Pane[] {
  if (dragged === target || !order.includes(dragged) || !order.includes(target)) return order;
  const at = order.indexOf(target);
  const rest = order.filter((p) => p !== dragged);
  rest.splice(at, 0, dragged);
  return rest;
}

/** New widths after dragging the splitter between `left` and `right` by `dx` pixels; their two weights keep their sum, neither pane goes under `minPx`. */
export function resizePair(widths: Record<Pane, number>, left: Pane, right: Pane, leftPx: number, rightPx: number, dx: number, minPx = MIN_PX): Record<Pane, number> {
  const total = leftPx + rightPx;
  if (!(total >= 2 * minPx)) return widths;
  const l = Math.min(Math.max(leftPx + dx, minPx), total - minPx);
  const share = widths[left] + widths[right];
  const wl = round3((share * l) / total);
  return { ...widths, [left]: wl, [right]: round3(share - wl) };
}

/** The grid columns for the panes shown, in order, with a splitter track between neighbours. */
export function columns(shown: Pane[], widths: Record<Pane, number>): string {
  return shown.map((p) => `minmax(${MIN_PX}px, ${widths[p]}fr)`).join(` ${GUTTER_PX}px `);
}
