"use client";
// Activity: the bid's whole audit log, newest first, read-only, filterable by type, requirement, unit and person (J-13 / C-16).
// Rows come from GET /api/opportunities/{id}/activity (P-27); the filters are query parameters, so a link from the compliance matrix
// (?req_id=…) opens it already filtered. The first 200 events load, "Show older events" pages back with `before`.  Owner: Janvia.
import Link from "next/link";
import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api, errorMessage } from "@/lib/api";
import type { Activity, ActivityEvent } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { Alert, Busy, EmptyState, Skeleton } from "@/components/ui";
import { detail, entityLabel, what, when } from "../_components/historyText";

const KEYS = ["entity", "req_id", "bu", "person"] as const;
type Key = (typeof KEYS)[number];
const PAGE = 200;
const HELP = "Everything recorded for this bid, newest first: who did what, and when. Read-only; nothing here can be changed.";

export default function ActivityPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const path = usePathname();
  const params = useSearchParams();
  const filters = useMemo(() => Object.fromEntries(KEYS.map((k) => [k, params.get(k) ?? ""])) as Record<Key, string>, [params]);
  const query = useMemo(() => KEYS.filter((k) => filters[k]).map((k) => `${k}=${encodeURIComponent(filters[k])}`).join("&"), [filters]);

  const [loaded, setLoaded] = useState<{ query: string; data?: Activity; error?: string }>();
  const [options, setOptions] = useState<Activity["filters"]>(); // the bid's own lists; they do not change with the filters
  const [older, setOlder] = useState<ActivityEvent[]>([]);
  const [cursor, setCursor] = useState<number | null>(null);
  const [moreBusy, setMoreBusy] = useState(false);
  const [moreError, setMoreError] = useState<string>();
  const [tick, setTick] = useState(0);
  const [reqText, setReqText] = useState(filters.req_id);
  useEffect(() => { setReqText(filters.req_id); }, [filters.req_id]);

  useEffect(() => {
    let live = true;
    setOlder([]); setMoreError(undefined);
    api<Activity>(`/api/opportunities/${id}/activity?${query ? `${query}&` : ""}limit=${PAGE}`).then((d) => {
      if (!live) return;
      setLoaded({ query, data: d }); setCursor(d.next_before); setOptions((o) => o ?? d.filters);
    }, (e) => { if (live) setLoaded({ query, error: errorMessage(e) }); });
    return () => { live = false; };
  }, [id, query, tick]);

  const set = useCallback((patch: Partial<Record<Key, string>>) => {
    const next = new URLSearchParams(params.toString());
    for (const [k, v] of Object.entries(patch)) { if (v) next.set(k, v); else next.delete(k); }
    const qs = next.toString();
    router.replace(qs ? `${path}?${qs}` : path, { scroll: false });
  }, [params, path, router]);

  const showOlder = () => {
    if (cursor == null) return;
    setMoreBusy(true); setMoreError(undefined);
    api<Activity>(`/api/opportunities/${id}/activity?${query ? `${query}&` : ""}limit=${PAGE}&before=${cursor}`)
      .then((d) => { setOlder((o) => [...o, ...d.events]); setCursor(d.next_before); }, (e) => setMoreError(errorMessage(e)))
      .finally(() => setMoreBusy(false));
  };

  const current = loaded?.query === query ? loaded : undefined; // a filter change shows the previous list until the new one arrives
  const shown = loaded?.data;
  const events = useMemo(() => {
    const seen = new Set<number>();
    return [...(shown?.events ?? []), ...older].filter((e) => !seen.has(e.id) && !!seen.add(e.id));
  }, [shown, older]);
  const filtering = KEYS.some((k) => filters[k]);
  const back = <Link className="button secondary" href={`/opportunities/${id}/consolidation`}>Compliance matrix</Link>;
  const head = <PageHead level={2} title="Activity" help={HELP}>{back}</PageHead>;

  if (loaded?.error && !shown) return <>{head}<Alert kind="error" title="Could not load the activity log.">{loaded.error}</Alert></>;
  if (!shown) return <>{head}<Skeleton lines={4} /></>;

  return (
    <>
      {head}
      <form className="matrix-filters" role="search" aria-label="Filter the activity log" data-tour="act-filters"
        onSubmit={(e) => { e.preventDefault(); set({ req_id: reqText.trim() }); }}>
        <label>Type
          <select value={filters.entity} onChange={(e) => set({ entity: e.target.value })}>
            <option value="">All types</option>
            {(options?.entities ?? []).map((x) => <option key={x} value={x}>{entityLabel(x)}</option>)}
          </select>
        </label>
        <label className="act-req">Requirement
          <input type="search" value={reqText} placeholder="e.g. REQ-0001-0885" onChange={(e) => setReqText(e.target.value)}
            onBlur={() => { if (reqText.trim() !== filters.req_id) set({ req_id: reqText.trim() }); }} />
        </label>
        <label>Unit
          <select value={filters.bu} onChange={(e) => set({ bu: e.target.value })}>
            <option value="">All units</option>
            {(options?.units ?? []).map((u) => <option key={u} value={u}>{u}</option>)}
          </select>
        </label>
        <label>Person
          <select value={filters.person} onChange={(e) => set({ person: e.target.value })}>
            <option value="">Everyone</option>
            {(options?.people ?? []).map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </label>
        <div className="mf-actions">
          <button type="button" className="secondary sm" disabled={!filtering} onClick={() => set({ entity: "", req_id: "", bu: "", person: "" })}>Clear filters</button>
          <button type="button" className="secondary sm" onClick={() => setTick((t) => t + 1)}>Refresh</button>
        </div>
      </form>
      {current?.error && <Alert kind="error" title="Could not refresh the activity log.">{current.error}</Alert>}
      <p className="muted matrix-count" role="status" aria-live="polite" data-tour="act-count">
        {!current ? "Updating…" : <>{filtering ? `${shown.total} matching events` : `${shown.total} events`}
          {events.length < shown.total && `, showing the newest ${events.length}`}</>}
      </p>

      {events.length === 0 ? (
        <EmptyState title={filtering ? "No events match these filters" : "Nothing has been recorded for this bid yet"}
          hint={filtering ? "Clear a filter to see more." : "Every action on the bid is recorded here as it happens."} />
      ) : (
        <div className="table-scroll">
          <table className="act-table" data-tour="act-table">
            <caption className="sr-only">Activity log of {id}, newest first</caption>
            <thead><tr><th>When</th><th>Who</th><th>What</th><th>Subject</th><th>Details</th></tr></thead>
            <tbody>
              {events.map((e) => {
                const line = detail(e);
                const isReq = e.entity_id.startsWith("REQ-");
                const unit = typeof e.data.bu === "string" ? e.data.bu : "";
                return (
                  <tr key={e.id}>
                    <td className="act-when">{when(e.at)}</td>
                    <td>{e.actor}</td>
                    <td>{what(e)}</td>
                    <td><span className="tag">{entityLabel(e.entity)}</span>{" "}
                      {isReq ? <Link className="mono" href={`/opportunities/${id}/trace#${e.entity_id}`} title="Open in Traceability">{e.entity_id}</Link> : <span className="mono">{e.entity_id}</span>}
                      {unit && <span className="muted"> · {unit}</span>}</td>
                    <td className="act-detail">{line ?? <span className="muted">—</span>}
                      {Object.keys(e.data).length > 0 && (
                        <details className="act-raw"><summary>All data</summary><pre>{JSON.stringify(e.data, null, 1)}</pre></details>)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {cursor != null && events.length > 0 && (
        <p className="matrix-more">
          <button type="button" className="secondary" disabled={moreBusy} onClick={showOlder}>Show older events</button>
          {moreBusy && <> <Busy label="Loading…" /></>}
          {moreError && <span className="warn" role="alert"> {moreError}</span>}
        </p>
      )}
    </>
  );
}
