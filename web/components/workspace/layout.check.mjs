// Runnable check for layout.ts (J-18): node web/components/workspace/layout.check.mjs (Node 22.18+ runs .ts files).
import assert from "node:assert/strict";
import { DEFAULT_LAYOUT, columns, dropOn, isDefaultLayout, moveBy, parseLayout, resizePair, serialiseLayout } from "./layout.ts";
import { isPaneWindowPath, paneWindowPath } from "./types.ts";

// defaults and saved layouts
assert.deepEqual(parseLayout(undefined), DEFAULT_LAYOUT);
assert.deepEqual(parseLayout(null), DEFAULT_LAYOUT);
assert.deepEqual(parseLayout("not json"), DEFAULT_LAYOUT);
assert.deepEqual(parseLayout(serialiseLayout(DEFAULT_LAYOUT)), DEFAULT_LAYOUT);
const mine = { order: [3, 1, 2], widths: { 1: 1.2, 2: 0.8, 3: 2 } };
assert.deepEqual(parseLayout(serialiseLayout(mine)), mine);
assert.ok(isDefaultLayout(DEFAULT_LAYOUT) && !isDefaultLayout(mine));
// a saved layout that does not hold together is dropped, never partly used
for (const bad of [
  { v: 2, order: [1, 2, 3], widths: { 1: 1, 2: 1, 3: 1 } },          // another version
  { v: 1, order: [1, 2, 2], widths: { 1: 1, 2: 1, 3: 1 } },          // not a permutation
  { v: 1, order: [1, 2], widths: { 1: 1, 2: 1, 3: 1 } },             // too short
  { v: 1, order: [1, 2, 3], widths: { 1: 1, 2: "x", 3: 1 } },        // not a number
  { v: 1, order: [1, 2, 3], widths: { 1: 0, 2: 1, 3: 1 } },          // a pane squeezed to nothing
  { v: 1, order: [1, 2, 3], widths: { 1: 1, 2: 1, 3: 99 } },         // absurd
  { v: 1, order: [1, 2, 3] },                                         // no widths
]) assert.deepEqual(parseLayout(JSON.stringify(bad)), DEFAULT_LAYOUT, JSON.stringify(bad));

// reorder by buttons
assert.deepEqual(moveBy([1, 2, 3], 2, -1), [2, 1, 3]);
assert.deepEqual(moveBy([1, 2, 3], 2, 1), [1, 3, 2]);
assert.deepEqual(moveBy([1, 2, 3], 1, -1), [1, 2, 3], "first pane cannot go left");
assert.deepEqual(moveBy([1, 2, 3], 3, 1), [1, 2, 3], "last pane cannot go right");
// reorder by drag and drop
assert.deepEqual(dropOn([1, 2, 3], 3, 1), [3, 1, 2]);
assert.deepEqual(dropOn([1, 2, 3], 1, 3), [2, 3, 1]);
assert.deepEqual(dropOn([1, 2, 3], 2, 2), [1, 2, 3], "dropping on itself changes nothing");
assert.deepEqual(dropOn([1, 2, 3], 1, 2), [2, 1, 3]);
assert.deepEqual(dropOn([2, 1], 1, 2), [1, 2], "two panes shown (one detached)");

// resize: the pair keeps its total weight, a pane never goes under the minimum, the third pane is untouched
const w = { 1: 1, 2: 1, 3: 1.3 };
const r = resizePair(w, 1, 2, 400, 400, 100);
assert.equal(+(r[1] + r[2]).toFixed(3), 2);
assert.ok(r[1] > w[1] && r[2] < w[2] && r[3] === 1.3);
assert.equal(r[1], 1.25, "500 of 800 px = 62.5% of weight 2");
const squeezed = resizePair(w, 1, 2, 400, 400, 10_000);
assert.equal(squeezed[2], +(2 * 240 / 800).toFixed(3), "the right pane stops at 240 px");
assert.equal(resizePair(w, 1, 2, 400, 400, -10_000)[1], +(2 * 240 / 800).toFixed(3), "the left pane stops at 240 px");
assert.deepEqual(resizePair(w, 1, 2, 200, 200, 50), w, "too narrow for two minimum panes: unchanged");

// the grid tracks: a gutter between neighbours only
assert.equal(columns([1, 2, 3], w), "minmax(240px, 1fr) 10px minmax(240px, 1fr) 10px minmax(240px, 1.3fr)");
assert.equal(columns([3], w), "minmax(240px, 1.3fr)");
assert.equal(columns([2, 1], w), "minmax(240px, 1fr) 10px minmax(240px, 1fr)");

// the address of a detached pane
assert.equal(paneWindowPath("OPP-0001", 2), "/opportunities/OPP-0001/trace/pane/2");
assert.ok(isPaneWindowPath("/opportunities/OPP-0001/trace/pane/3") && isPaneWindowPath("/opportunities/OPP-0002/trace/pane/1/"));
assert.ok(!isPaneWindowPath("/opportunities/OPP-0001/trace") && !isPaneWindowPath("/opportunities/OPP-0001/trace/pane/4") && !isPaneWindowPath(undefined));
console.log("layout.check.mjs: all checks passed");
