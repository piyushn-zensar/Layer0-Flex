// Runnable check for channel.ts (J-18): node web/components/workspace/channel.check.mjs (Node 22.18+ runs .ts files).
// Node has BroadcastChannel; the localStorage fallback is exercised through a small fake store shared by two "windows".
import assert from "node:assert/strict";
import { channelName, newer, openChannel } from "./channel.ts";

const wait = (ms = 60) => new Promise((r) => setTimeout(r, ms));

// ordering protection: higher sequence wins, a tie goes to the larger window id in every window
assert.ok(newer(undefined, 1, "a"));
assert.ok(newer({ seq: 1, from: "a" }, 2, "a"));
assert.ok(!newer({ seq: 2, from: "a" }, 1, "z"));
assert.ok(newer({ seq: 2, from: "a" }, 2, "b") && !newer({ seq: 2, from: "b" }, 2, "a"));
assert.ok(!newer({ seq: 2, from: "a" }, 2, "a"), "the same message twice is not applied twice");
assert.equal(channelName("OPP-0001"), "layer0-trace-OPP-0001");

// BroadcastChannel: others receive, the sender does not, other bids are separate
{
  const got = { a: [], b: [], other: [] };
  const a = openChannel("OPP-1", (m) => got.a.push(m), { id: "A" });
  const b = openChannel("OPP-1", (m) => got.b.push(m), { id: "B" });
  const other = openChannel("OPP-2", (m) => got.other.push(m), { id: "C" });
  assert.equal(a.backend, "broadcast");
  a.send({ t: "select", req: "REQ-1", seq: 1 });
  b.send({ t: "link", pane: 2, on: false, seq: 2 });
  a.send({ t: "hello", role: "pane", pane: 3 });
  await wait();
  assert.deepEqual(got.b.map((m) => m.t), ["select", "hello"]);
  assert.deepEqual(got.a.map((m) => m.t), ["link"], "a window does not hear itself");
  assert.deepEqual(got.other, [], "another bid's windows hear nothing");
  assert.equal(got.b[0].from, "A");
  assert.equal(got.b[0].req, "REQ-1");
  assert.ok(got.b[0].v === 1 && typeof got.b[0].n === "number");
  a.close(); b.close(); other.close();
}

// the fallback: localStorage "storage" events, which fire in the OTHER windows only
{
  const listeners = new Set();
  const store = (owner) => ({
    setItem: (k, v) => { for (const l of listeners) if (l.owner !== owner) l.fn(k, v); },   // the event reaches the other windows
    removeItem: (k) => { for (const l of listeners) if (l.owner !== owner) l.fn(k, null); },
  });
  const onStorage = (owner) => (fn) => { const l = { owner, fn }; listeners.add(l); return () => listeners.delete(l); };
  const got = { a: [], b: [] };
  const a = openChannel("OPP-1", (m) => got.a.push(m), { id: "A", prefer: "storage", storage: store("A"), onStorage: onStorage("A") });
  const b = openChannel("OPP-1", (m) => got.b.push(m), { id: "B", prefer: "storage", storage: store("B"), onStorage: onStorage("B") });
  assert.equal(a.backend, "storage");
  a.send({ t: "select", req: "REQ-9", seq: 4 });
  a.send({ t: "select", req: "REQ-9", seq: 4 });
  b.send({ t: "filters", filters: { category: "technical" }, seq: 5 });
  assert.deepEqual(got.b.map((m) => m.t), ["select", "select"], "removal events are not messages; each send is delivered");
  assert.deepEqual(got.a.map((m) => m.t), ["filters"]);
  assert.deepEqual(got.a[0].filters, { category: "technical" });
  a.close();
  b.send({ t: "ping", role: "pane", pane: 2 });
  assert.equal(got.a.length, 1, "a closed channel hears nothing");
  b.close();
}

// no transport at all: sending is a harmless no-op
{
  const c = openChannel("OPP-1", () => {}, { id: "X", BroadcastChannel: undefined, storage: undefined, onStorage: undefined });
  assert.equal(c.backend, "none");
  c.send({ t: "bye", pane: 1 }); c.close();
}

// garbage from elsewhere is ignored
{
  const heard = [];
  const a = openChannel("OPP-3", (m) => heard.push(m), { id: "A" });
  const raw = new BroadcastChannel(channelName("OPP-3"));
  raw.postMessage("hello"); raw.postMessage({ v: 2, from: "x", t: "select" }); raw.postMessage({ v: 1, t: "select" }); raw.postMessage(null);
  raw.postMessage({ v: 1, from: "A", t: "select", req: "mine" });   // from this very window id
  raw.postMessage({ v: 1, from: "Z", t: "select", req: "ok", seq: 1, n: 1 });
  await wait();
  assert.deepEqual(heard.map((m) => m.req), ["ok"]);
  a.close(); raw.close();
}
console.log("channel.check.mjs: all checks passed");
