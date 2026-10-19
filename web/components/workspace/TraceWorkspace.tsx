"use client";
// The state of Requirement Traceability, shared by its three panes (J-18, C-34; before this it sat in trace/page.tsx).
// One provider serves the main window (all attached panes) and a detached pane window (one pane). It holds the trace data, the
// selected requirement, the Linked switches (J-12), enlarge / restore (J-12), the A-27 filters, the layout (order and widths),
// which panes are open in their own windows, and the BroadcastChannel of the bid (see channel.ts). Owner: Janvia.
import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { errorMessage, isBidManager, post, useApi, useMe } from "@/lib/api";
import type { Trace, TraceDoc, TraceRow } from "@/lib/types";
import { useToast } from "@/components/ui";
import { applyFilters, filtersUrl, isFiltered, readFilters, type FilterKey, type Filters } from "@/components/requirements/filters"; // A-27 (Atharv)
import { newer, openChannel, type Channel, type Envelope } from "./channel";
import { DEFAULT_LAYOUT, LAYOUT_KEY, cloneLayout, dropOn, moveBy, parseLayout, serialiseLayout, type Layout } from "./layout";
import { PANES, PANE_NAMES, paneWindowPath, type Pane } from "./types";

// `sent_for_assessment` is a trace-service flag (J-12) that web/lib/types.ts does not declare yet (Piyush's file).
export type TraceView = Trace & { sent_for_assessment?: boolean };
type Derived = {
  docs: TraceDoc[]; mainId?: string; shown?: TraceDoc; docName: (d?: { id: string; filename: string }) => string; assessed: boolean;
  pages: TraceDoc["pages"]; page?: TraceDoc["pages"][number]; view: TraceRow[]; filtered: boolean; categories: string[]; units: string[];
};

export type Workspace = {
  bidId: string; mode: "main" | "pane"; pane?: Pane;
  data?: TraceView; error?: string; reload: () => unknown; afterWrite: () => void; d?: Derived;
  bm: boolean; sent?: Record<string, string>;
  selected?: string; select: (reqId: string, force?: boolean) => void;
  rowProps: (reqId: string) => Record<string, unknown>;
  linked: Record<Pane, boolean>; setLink: (pane: Pane, on: boolean) => void;
  enlarged: Pane | null; setEnlarged: (p: Pane | null) => void;
  filters: Filters; setFilter: (k: FilterKey, v: string) => void; clearFilters: () => void;
  known: string | null; dismissKnown: () => void;
  matching: boolean; matchProducts: () => void;
  pageNo: number; setPageNo: (n: number) => void; setDocId: (id: string) => void;
  // the layout of the main window
  layout: Layout; stacked: () => boolean; attached: Pane[]; setLayout: (l: Layout, persist?: boolean) => void; persistLayout: () => void; resetLayout: () => void;
  move: (pane: Pane, delta: -1 | 1) => void; dragFrom: Pane | null; dragOver: Pane | null; startDrag: (p: Pane) => void; endDrag: () => void; overPane: (p: Pane | null) => void; dropPane: (target: Pane) => void;
  // panes in their own windows
  detached: Pane[]; openPane: (p: Pane) => void; returnPane: (p: Pane) => void; showPane: (p: Pane) => void; returnToMain: () => void; windowGone: boolean;
  notice: string; announce: (msg: string) => void; channelBackend: string;
};

const Ctx = createContext<Workspace | null>(null);
export function useWorkspace(): Workspace {
  const w = useContext(Ctx);
  if (!w) throw new Error("useWorkspace must be used inside <TraceWorkspace>");
  return w;
}

const STACKED = "(max-width: 1100px)";
const HEARTBEAT_MS = 2000, GONE_MS = 7000, POLL_MS = 1000;
const FEATURES = (w: number, h: number, l: number, t: number) => `popup=yes,width=${w},height=${h},left=${l},top=${t}`;

export default function TraceWorkspace({ bidId, mode, pane, children }: { bidId: string; mode: "main" | "pane"; pane?: Pane; children: React.ReactNode }) {
  const toast = useToast();
  const { data, error, reload } = useApi<TraceView>(`/api/bids/${bidId}/trace`);
  const bm = isBidManager(useMe()); // P-31: match changes are the bid manager's; one lookup for every row
  const { data: sent, reload: reloadSent } = useApi<Record<string, string>>(`/api/bids/${bidId}/knowledge`); // A-11

  // --- the workspace state ---
  const [selected, setSelected] = useState<string>();
  const [pageNo, setPageNo] = useState(1);
  const [docId, setDocId] = useState<string>(); // P-11: the document shown in pane 1 (default the main RFP)
  const [linked, setLinked] = useState<Record<Pane, boolean>>({ 1: true, 2: true, 3: true }); // J-12: which panes follow the selection
  const [enlarged, setEnlarged] = useState<Pane | null>(null);
  const [filters, setFilters] = useState<Filters>({}); // A-27 (C-32): filters and sort live in the page address
  const [known, setKnown] = useState<string | null>(null); // P-32 (C-27): the RFP step sends an already-read document here (?known=<file>)
  const [matching, setMatching] = useState(false);
  const [layout, setLayoutState] = useState<Layout>(() => cloneLayout(DEFAULT_LAYOUT));
  const [detached, setDetached] = useState<Pane[]>([]);
  const [dragFrom, setDragFrom] = useState<Pane | null>(null);
  const [dragOver, setDragOver] = useState<Pane | null>(null);
  const [notice, setNotice] = useState("");
  const [windowGone, setWindowGone] = useState(false);
  const [backend, setBackend] = useState("");

  // --- refs: the selection callback and the channel handler stay stable and read the latest values from here ---
  const linkedRef = useRef(linked);
  const selectedRef = useRef<string | undefined>(undefined);
  const filtersRef = useRef<Filters>({});
  const layoutRef = useRef(layout);
  const detachedRef = useRef<Pane[]>([]);
  const chRef = useRef<Channel | null>(null);
  const clock = useRef(0);                                             // Lamport clock: the sequence of selection, link and filters messages
  const last = useRef<Record<string, { seq: number; from: string }>>({}); // what was applied last, per kind (select, link1..3, filters)
  const wins = useRef<Partial<Record<Pane, Window>>>({});               // windows this window opened
  const seenAt = useRef<Partial<Record<Pane, number>>>({});             // last heartbeat of each detached pane window
  const stateSeen = useRef(new Set<string>());                          // hello senders that already got a state reply
  const restore = useRef<{ tops: Record<number, number>; focus?: string } | null>(null);
  const noticeTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const reloadTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const handler = useRef<(m: Envelope) => void>(() => {});

  const announce = useCallback((msg: string) => {
    setNotice(msg);
    clearTimeout(noticeTimer.current);
    noticeTimer.current = setTimeout(() => setNotice(""), 8000);
  }, []);
  const send = useCallback((b: Parameters<Channel["send"]>[0]) => chRef.current?.send(b), []);
  const nextSeq = () => ++clock.current;
  const stacked = useCallback(() => typeof window !== "undefined" && window.matchMedia(STACKED).matches, []);

  // --- moving a pane to a requirement: pane 1 opens its document and page, panes 2 and 3 scroll their row into view ---
  const follow = useCallback((p: Pane, reqId: string) => {
    if (p === 1) {
      const req = data?.rows.find((r) => r.req.req_id === reqId)?.req;
      if (req && data?.docs?.some((d) => d.id === req.document_id)) setDocId(req.document_id); // a new version from an addendum
      if (req?.page) setPageNo(req.page);
    } else {
      document.querySelectorAll(`[data-pane="${p}"] tr[data-req="${reqId}"]`).forEach((tr) => tr.scrollIntoView({ block: "nearest", behavior: "smooth" }));
    }
  }, [data]);

  // the same, for a pane that is still loading its own rows (the register fetches separately): wait for the row, for a few seconds
  const followSoon = useCallback((p: Pane, reqId: string) => {
    let tries = 25;
    const go = () => {
      if (p === 1 || document.querySelector(`[data-pane="${p}"] tr[data-req="${reqId}"]`)) { follow(p, reqId); return; }
      if (--tries > 0) setTimeout(go, 200);
    };
    go();
  }, [follow]);

  // apply a selection in this window; `force`: the first selection on load moves every pane whatever its link
  const applySelect = useCallback((reqId: string, force = false) => {
    setSelected(reqId);
    selectedRef.current = reqId;
    history.replaceState(null, "", `#${reqId}`);
    PANES.filter((p) => force || linkedRef.current[p]).forEach((p) => (force ? followSoon : follow)(p, reqId));
  }, [follow, followSoon]);
  const select = useCallback((reqId: string, force = false) => {
    applySelect(reqId, force);
    if (force) return; // the first selection on load is not news for the other windows
    const seq = nextSeq();
    last.current.select = { seq, from: chRef.current?.id ?? "" };
    send({ t: "select", req: reqId, seq });
  }, [applySelect, send]);

  const applyLink = useCallback((p: Pane, on: boolean) => {
    linkedRef.current = { ...linkedRef.current, [p]: on };
    setLinked(linkedRef.current);
    if (on && selectedRef.current) follow(p, selectedRef.current); // re-linking catches up with the selection at once
  }, [follow]);
  const setLink = useCallback((p: Pane, on: boolean) => {
    applyLink(p, on);
    const seq = nextSeq();
    last.current[`link${p}`] = { seq, from: chRef.current?.id ?? "" };
    send({ t: "link", pane: p, on, seq });
  }, [applyLink, send]);

  const applyFilterState = useCallback((next: Filters) => {
    filtersRef.current = next;
    setFilters(next);
    history.replaceState(null, "", filtersUrl(location.pathname, next, location.hash));
  }, []);
  const broadcastFilters = useCallback((next: Filters) => {
    const seq = nextSeq();
    last.current.filters = { seq, from: chRef.current?.id ?? "" };
    send({ t: "filters", filters: next, seq });
  }, [send]);
  const setFilter = useCallback((k: FilterKey, v: string) => { const next = { ...filtersRef.current, [k]: v || undefined }; applyFilterState(next); broadcastFilters(next); }, [applyFilterState, broadcastFilters]);
  const clearFilters = useCallback(() => { applyFilterState({}); broadcastFilters({}); }, [applyFilterState, broadcastFilters]);

  // --- writes: reload here and tell the other windows to reload ---
  const afterWrite = useCallback(() => { reload(); reloadSent(); send({ t: "changed", source: mode === "pane" ? `pane${pane}` : "main" }); }, [reload, reloadSent, send, mode, pane]);
  const matchProducts = useCallback(() => { // runs the matching agent over the requirements that nobody has decided yet (accepted, manual and rejected stay)
    setMatching(true);
    post<{ matched: number; kept: number }>(`/api/bids/${bidId}/match`)
      .then((r) => { toast.success(`Matching done: ${r.matched} requirement(s) matched, ${r.kept} kept as decided.`); afterWrite(); },
        (e) => toast.error(errorMessage(e)))
      .finally(() => setMatching(false));
  }, [bidId, toast, afterWrite]);

  // --- the layout of the main window ---
  const setLayout = useCallback((l: Layout, persist = true) => {
    layoutRef.current = l; setLayoutState(l);
    if (persist) { try { localStorage.setItem(LAYOUT_KEY, serialiseLayout(l)); } catch { /* private window or blocked storage: the layout lasts this session */ } }
  }, []);
  const persistLayout = useCallback(() => { try { localStorage.setItem(LAYOUT_KEY, serialiseLayout(layoutRef.current)); } catch { /* as above */ } }, []);
  const resetLayout = useCallback(() => {
    try { localStorage.removeItem(LAYOUT_KEY); } catch { /* as above */ }
    setLayout(cloneLayout(DEFAULT_LAYOUT), false);
    announce("Layout reset: panes back in their original order and widths.");
  }, [setLayout, announce]);
  const reorder = useCallback((order: Pane[], focus?: string) => {
    if (order.join() === layoutRef.current.order.join()) return;
    const tops: Record<number, number> = {};
    PANES.forEach((p) => { tops[p] = document.querySelector<HTMLElement>(`[data-pane="${p}"]`)?.scrollTop ?? 0; }); // a moved element would restart at its top
    restore.current = { tops, focus };
    setLayout({ ...layoutRef.current, order });
  }, [setLayout]);
  const move = useCallback((p: Pane, delta: -1 | 1) => {
    const shown = layoutRef.current.order.filter((x) => !detachedRef.current.includes(x));
    const moved = moveBy(shown, p, delta);
    if (moved.join() === shown.join()) return;
    const pos = moved.indexOf(p) + 1;
    const hidden = layoutRef.current.order.filter((x) => detachedRef.current.includes(x));
    reorder([...moved, ...hidden], `[data-pane="${p}"] [data-move="${delta}"]`);
    announce(`Pane ${p}: ${PANE_NAMES[p]} moved to position ${pos} of ${moved.length}.`);
  }, [reorder, announce]);
  const startDrag = useCallback((p: Pane) => setDragFrom(p), []);
  const endDrag = useCallback(() => { setDragFrom(null); setDragOver(null); }, []);
  const dropPane = useCallback((target: Pane) => {
    const from = dragFrom;
    endDrag();
    if (from === null || from === target || stacked()) return;
    const shown = layoutRef.current.order.filter((x) => !detachedRef.current.includes(x));
    const moved = dropOn(shown, from, target);
    const hidden = layoutRef.current.order.filter((x) => detachedRef.current.includes(x));
    reorder([...moved, ...hidden], `[data-pane="${from}"] [data-grip]`);
    announce(`Pane ${from}: ${PANE_NAMES[from]} moved to position ${moved.indexOf(from) + 1} of ${moved.length}.`);
  }, [dragFrom, endDrag, stacked, reorder, announce]);
  useLayoutEffect(() => { // after panes were reordered in the DOM: scroll positions and the focused control come back
    const r = restore.current; if (!r) return; restore.current = null;
    PANES.forEach((p) => { const el = document.querySelector<HTMLElement>(`[data-pane="${p}"]`); if (el) el.scrollTop = r.tops[p] ?? 0; });
    if (r.focus) { // a move button that is now disabled (the pane reached an end) hands focus to its grip
      let el = document.querySelector<HTMLElement>(r.focus);
      if (!el || (el as HTMLButtonElement).disabled) el = document.querySelector<HTMLElement>(r.focus.replace(/\[data-move="-?1"\]/, "[data-grip]"));
      el?.focus();
    }
  }, [layout.order]);

  // --- panes in their own windows (main window) ---
  const markDetached = useCallback((p: Pane) => {
    seenAt.current[p] = Date.now();
    if (!detachedRef.current.includes(p)) { detachedRef.current = [...detachedRef.current, p]; setDetached(detachedRef.current); }
  }, []);
  const returnPane = useCallback((p: Pane) => {
    if (!detachedRef.current.includes(p)) return;
    detachedRef.current = detachedRef.current.filter((x) => x !== p); setDetached(detachedRef.current);
    delete wins.current[p]; delete seenAt.current[p];
    announce(`Pane ${p}: ${PANE_NAMES[p]} is back in this window.`);
    if (selectedRef.current && linkedRef.current[p]) followSoon(p, selectedRef.current); // it was mounted afresh: catch up when its rows are there
  }, [announce, followSoon]);
  const openPane = useCallback((p: Pane) => {
    if (mode !== "main" || detachedRef.current.includes(p)) return;
    const rect = document.querySelector<HTMLElement>(`[data-pane="${p}"]`)?.getBoundingClientRect();
    const w = Math.round(Math.min(Math.max(rect?.width ?? 560, p === 2 ? 760 : 520), 1000)); // the register is wide content
    const h = Math.round(Math.min(Math.max(window.innerHeight - 40, 480), 1000));
    const url = filtersUrl(paneWindowPath(bidId, p), filtersRef.current, selectedRef.current ? `#${selectedRef.current}` : "");
    let win: Window | null = null;
    try { win = window.open(url, `layer0-${bidId}-pane-${p}`, FEATURES(w, h, window.screenX + 60 + detachedRef.current.length * 40, window.screenY + 60)); } catch { win = null; }
    if (!win) { toast.error("Your browser blocked the new window. Allow pop-ups for this site, then try New window again."); announce(`Pane ${p} could not open in a new window: pop-ups are blocked.`); return; }
    wins.current[p] = win;
    setEnlarged((e) => (e === p ? null : e)); // an enlarged pane goes back to normal before it leaves
    markDetached(p);
    announce(`Pane ${p}: ${PANE_NAMES[p]} opened in a new window.`);
  }, [mode, bidId, toast, announce, markDetached]);
  const showPane = useCallback((p: Pane) => { try { wins.current[p]?.focus(); } catch { /* window gone */ } }, []);
  const requestReturn = useCallback((p: Pane) => { // "Return to main window", asked in the main window
    try { wins.current[p]?.close(); } catch { /* not ours to close */ }
    send({ t: "close", pane: p });
    returnPane(p);
  }, [send, returnPane]);
  const returnToMain = useCallback(() => { // "Return to main window", asked in the pane window itself
    send({ t: "bye", pane });
    window.close();
    setTimeout(() => { if (!window.closed) setWindowGone(true); }, 300); // a window the browser will not close: say so
  }, [send, pane]);

  // --- the channel: other windows' messages ---
  handler.current = (m: Envelope) => {
    if ("seq" in m) clock.current = Math.max(clock.current, m.seq);
    const accept = (key: string, seq: number) => { if (!newer(last.current[key], seq, m.from)) return false; last.current[key] = { seq, from: m.from }; return true; };
    switch (m.t) {
      case "select": if (accept("select", m.seq)) applySelect(m.req); break;
      case "link": if (accept(`link${m.pane}`, m.seq)) applyLink(m.pane, m.on); break;
      case "filters": if (accept("filters", m.seq)) applyFilterState(m.filters); break;
      case "changed": // reload what this window shows: every useApi in it re-fetches when the window "regains focus"
        clearTimeout(reloadTimer.current);
        reloadTimer.current = setTimeout(() => window.dispatchEvent(new Event("focus")), 250);
        break;
      case "hello": {
        if (mode === "main" && m.role === "pane" && m.pane) markDetached(m.pane);
        if (mode === "pane" && m.role === "main") send({ t: "ping", role: "pane", pane }); // the main window reloaded: say where we are
        const reply = () => {
          if (stateSeen.current.has(m.from)) return;
          const links: Record<number, { on: boolean; seq: number }> = {};
          PANES.forEach((p) => { const l = last.current[`link${p}`]; if (l) links[p] = { on: linkedRef.current[p], seq: l.seq }; });
          send({ t: "state", to: m.from, select: selectedRef.current ? { req: selectedRef.current, seq: last.current.select?.seq ?? 0 } : null, links, filters: { filters: filtersRef.current, seq: last.current.filters?.seq ?? 0 } });
        };
        if (mode === "main") reply(); else setTimeout(reply, 150); // the main window answers first; a pane window only if nobody did
        break;
      }
      case "state":
        stateSeen.current.add(m.to);
        if (m.to !== chRef.current?.id) break;
        // a state message carries its seqs inside: move the clock past them, or this window's next change could lose to old state
        clock.current = Math.max(clock.current, m.select?.seq ?? 0, m.filters?.seq ?? 0, ...Object.values(m.links).map((l) => l.seq));
        if (m.select && accept("select", m.select.seq)) applySelect(m.select.req, true);
        PANES.forEach((p) => { const l = m.links[p]; if (l && accept(`link${p}`, l.seq)) applyLink(p, l.on); });
        if (m.filters && accept("filters", m.filters.seq)) applyFilterState(m.filters.filters);
        break;
      case "ping": if (mode === "main" && m.role === "pane" && m.pane) markDetached(m.pane); break;
      case "bye": if (mode === "main" && m.pane) returnPane(m.pane); break;
      case "close": if (mode === "pane" && m.pane === pane) { window.close(); setTimeout(() => { if (!window.closed) setWindowGone(true); }, 300); } break;
    }
  };
  useEffect(() => {
    const ch = openChannel(bidId, (m) => handler.current(m));
    chRef.current = ch; setBackend(ch.backend);
    ch.send({ t: "hello", role: mode, pane });
    const bye = () => { if (mode === "pane") ch.send({ t: "bye", pane }); };
    window.addEventListener("pagehide", bye);
    return () => { window.removeEventListener("pagehide", bye); bye(); ch.close(); chRef.current = null; };
  }, [bidId, mode, pane]);

  // a pane window tells the main window it is alive; the main window checks its windows (closed, or silent for too long)
  useEffect(() => {
    if (mode !== "pane") return;
    const t = setInterval(() => chRef.current?.send({ t: "ping", role: "pane", pane }), HEARTBEAT_MS);
    return () => clearInterval(t);
  }, [mode, pane]);
  useEffect(() => {
    if (mode !== "main") return;
    const t = setInterval(() => {
      for (const p of detachedRef.current) {
        const w = wins.current[p];
        const closed = !!w && w.closed;
        const silent = !w && Date.now() - (seenAt.current[p] ?? 0) > GONE_MS; // no handle (the main window reloaded): the heartbeat is all we have
        if (closed || silent) returnPane(p);
      }
    }, POLL_MS);
    return () => clearInterval(t);
  }, [mode, returnPane]);

  // --- first load, layout from the browser, Esc ---
  useEffect(() => {
    setKnown(mode === "main" ? new URLSearchParams(location.search).get("known") : null);
    const f = readFilters(location.search); filtersRef.current = f; setFilters(f);
    if (mode === "main") { const l = (() => { try { return parseLayout(localStorage.getItem(LAYOUT_KEY)); } catch { return cloneLayout(DEFAULT_LAYOUT); } })(); layoutRef.current = l; setLayoutState(l); }
  }, [mode]);
  useEffect(() => { // first load: the requirement in the URL hash, else the first one
    if (!data || selected) return;
    const fromHash = decodeURIComponent(location.hash.slice(1));
    const first = data.rows.find((r) => r.req.req_id === fromHash)
      ?? data.rows.find((r) => r.children.some((k) => k.req_id === fromHash)) // a sub-requirement (Changes links): its group
      ?? data.rows.find((r) => r.req.page);
    if (first) select(first.req.req_id, true);
  }, [data, selected, select]);
  useEffect(() => { // restoring (or switching) the enlarged pane: panes that were hidden could not scroll, so the linked ones catch up now
    if (!selectedRef.current) return;
    const req = selectedRef.current;
    const t = setTimeout(() => PANES.filter((p) => linkedRef.current[p] && (enlarged === null || enlarged === p)).forEach((p) => follow(p, req)), 0);
    return () => clearTimeout(t);
  }, [enlarged]); // on enlarge / restore only, not on every selection (follow and the selection are read from this render and the ref)
  useEffect(() => { // the first Esc restores the three-pane layout and goes no further: a walkthrough that is open stays open
    if (enlarged === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape" || e.defaultPrevented) return;
      e.preventDefault(); e.stopPropagation(); // capture phase: the walkthrough's own Esc handler (bubble phase) never sees this one
      setEnlarged(null);
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [enlarged]);

  const rowProps = useCallback((reqId: string) => ({
    "data-req": reqId, className: reqId === selected ? "selected" : "", onClick: () => select(reqId),
    tabIndex: 0, "aria-current": reqId === selected ? ("true" as const) : undefined,
    // Only when the row itself has focus, so buttons, links and the BOM summary inside it keep their own keys.
    onKeyDown: (e: React.KeyboardEvent) => {
      if (e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); select(reqId); }
    },
  }), [selected, select]);

  // --- what the panes read ---
  const d = useMemo<Derived | undefined>(() => {
    if (!data) return undefined;
    // P-11: the main RFP first, then change documents with requirements anchored in them (older APIs send only doc + pages).
    const docs = data.docs ?? (data.doc ? [{ id: data.doc.id, filename: data.doc.filename, role: data.doc.role, pages: data.pages }] : []);
    const mainId = data.doc?.id ?? docs[0]?.id;
    const shown = docs.find((x) => x.id === docId) ?? docs[0];
    const pages = shown?.pages ?? [];
    const view = applyFilters(data.rows, filters); // A-27: what panes 2 and 3 list
    return {
      docs, mainId, shown, pages, page: pages[pageNo - 1], view, filtered: isFiltered(filters),
      docName: (x) => (!x || x.id === mainId ? "RFP" : x.filename),
      assessed: data.sent_for_assessment ?? data.rows.some((r) => r.assignments.length > 0), // J-12: unit responses show only once sent
      categories: [...new Set(data.rows.map((r) => r.req.category))].sort(),
      units: [...new Set(data.rows.flatMap((r) => [...(r.match?.units ?? []).map((u) => u.bu), ...r.assignments.map((a) => a.bu)]))].sort(),
    };
  }, [data, docId, pageNo, filters]);

  const attached = useMemo(() => layout.order.filter((p) => !detached.includes(p)), [layout.order, detached]);
  const value: Workspace = {
    bidId, mode, pane, data, error, reload, afterWrite, d, bm, sent, selected, select, rowProps, linked, setLink, enlarged, setEnlarged,
    filters, setFilter, clearFilters, known, dismissKnown: () => setKnown(null), matching, matchProducts, pageNo, setPageNo, setDocId,
    layout, stacked, attached, setLayout, persistLayout, resetLayout, move, dragFrom, dragOver, startDrag, endDrag, overPane: setDragOver, dropPane,
    detached, openPane, returnPane: requestReturn, showPane, returnToMain, windowGone, notice, announce, channelBackend: backend,
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
