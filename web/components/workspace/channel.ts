// Messages between the windows of one bid (J-18, C-34): the main Traceability window and any pane opened in its own window.
// One channel per bid, "layer0-trace-{bid}", over the browser's BroadcastChannel (same origin, same browser profile, so the sign-in
// cookie is shared and nobody signs in twice). Where BroadcastChannel is missing, the same envelope travels through localStorage
// "storage" events instead. A window ignores its own messages. Selection, Linked and filters carry a sequence number and are
// applied only if newer (see `newer`), so two windows acting at once end up agreeing.
// Runnable check: node web/components/workspace/channel.check.mjs (Node 22.18+ runs .ts files).  Owner: Janvia.
import type { Pane } from "./types";
import type { Filters } from "@/components/requirements/filters";

export type Role = "main" | "pane";
export type Body =
  | { t: "select"; req: string; seq: number }                       // a requirement was selected
  | { t: "link"; pane: Pane; on: boolean; seq: number }             // a pane was linked or unlinked
  | { t: "filters"; filters: Filters; seq: number }                 // the filters and sort changed
  | { t: "changed"; source: string }                                // something was written: reload your data
  | { t: "hello"; role: Role; pane?: Pane }                         // a window opened (or the main window reloaded)
  | { t: "state"; to: string; select: { req: string; seq: number } | null; links: Partial<Record<Pane, { on: boolean; seq: number }>>; filters: { filters: Filters; seq: number } | null } // the reply to hello
  | { t: "ping"; role: Role; pane?: Pane }                          // heartbeat of a detached pane window
  | { t: "bye"; pane?: Pane }                                       // a pane window is closing
  | { t: "close"; pane: Pane };                                     // the main window asks a pane window to close
export type Envelope = Body & { v: 1; from: string; n: number };

export const channelName = (bid: string) => `layer0-trace-${bid}`;

/** Is (seq, from) newer than what was applied last? Higher sequence wins; the window id breaks a tie the same way in every window. */
export function newer(last: { seq: number; from: string } | undefined, seq: number, from: string): boolean {
  if (!last) return true;
  return seq > last.seq || (seq === last.seq && from > last.from);
}

export const newWindowId = () => `${Math.random().toString(36).slice(2, 8)}${Date.now().toString(36).slice(-4)}`;

export type Channel = { id: string; backend: "broadcast" | "storage" | "none"; send: (body: Body) => void; close: () => void };
export type Deps = {
  BroadcastChannel?: typeof BroadcastChannel;
  storage?: Pick<Storage, "setItem" | "removeItem">;
  onStorage?: (fn: (key: string | null, value: string | null) => void) => () => void;
  id?: string;
  prefer?: "broadcast" | "storage";   // tests force the fallback
};

function defaults(): Deps {
  const g = globalThis as unknown as { BroadcastChannel?: typeof BroadcastChannel; localStorage?: Storage; addEventListener?: Window["addEventListener"]; removeEventListener?: Window["removeEventListener"] };
  let storage: Storage | undefined;
  try { storage = g.localStorage; } catch { storage = undefined; }   // blocked storage throws
  return {
    BroadcastChannel: g.BroadcastChannel, storage,
    onStorage: (fn) => {
      const h = (e: Event) => { const s = e as StorageEvent; fn(s.key, s.newValue); };
      g.addEventListener?.("storage", h);
      return () => g.removeEventListener?.("storage", h);
    },
  };
}

/** Open the channel of one bid. `onMessage` gets other windows' messages only. */
export function openChannel(bid: string, onMessage: (m: Envelope) => void, deps: Deps = {}): Channel {
  const d = { ...defaults(), ...deps };
  const id = d.id ?? newWindowId();
  const name = channelName(bid);
  let n = 0;
  const accept = (raw: unknown) => {
    const m = raw as Envelope | null;
    if (m && typeof m === "object" && m.v === 1 && typeof m.from === "string" && m.from !== id) onMessage(m);
  };
  if (d.BroadcastChannel && d.prefer !== "storage") {
    const bc = new d.BroadcastChannel(name);
    bc.onmessage = (e) => accept(e.data);
    return { id, backend: "broadcast", send: (b) => bc.postMessage({ ...b, v: 1, from: id, n: ++n }), close: () => bc.close() };
  }
  if (d.storage && d.onStorage) {
    const storage = d.storage;
    const off = d.onStorage((key, value) => { if (key === name && value) { try { accept(JSON.parse(value)); } catch { /* not ours */ } } });
    return {
      id, backend: "storage", close: off,
      // a storage event fires in the OTHER windows when the value changes: the nonce makes every message a change, the removal keeps the store empty
      send: (b) => { try { storage.setItem(name, JSON.stringify({ ...b, v: 1, from: id, n: ++n, r: Math.random() })); storage.removeItem(name); } catch { /* storage full or blocked */ } },
    };
  }
  return { id, backend: "none", send: () => {}, close: () => {} };
}
