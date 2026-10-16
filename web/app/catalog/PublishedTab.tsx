"use client";
// Published catalog view (P-34): what the official Flex product pages say (name, key features, link). Not compliance evidence.
import { useState } from "react";
import { errorMessage, post, useApi, useMe } from "@/lib/api";
import type { PublishedCatalog, PublishedProduct, PublishedRun, PublishedVersion } from "@/lib/types";
import { Alert, Busy, EmptyState, Skeleton, StatusBadge, useToast } from "@/components/ui";

const NO_UNIT = "No unit";
const when = (iso?: string | null) => (iso ? iso.slice(0, 16).replace("T", " ") : "");
const day = (iso?: string | null) => (iso ? iso.slice(0, 10) : "");
// StatusBadge has no "ok" tone word, so map to statuses that carry the tone: green, amber, red
const RUN_TONE: Record<string, string> = { ok: "confirmed", partial: "partial", failed: "failed", running: "pending", skipped: "neutral" };

function History({ pkey }: { pkey: string }) {
  const { data, error } = useApi<PublishedVersion[]>(`/api/catalog/published/versions?key=${encodeURIComponent(pkey)}`);
  if (error) return <Alert kind="error">{error}</Alert>;
  if (!data) return <Skeleton lines={2} />;
  return (
    <ul>{data.map((v) => (
      <li key={v.version}><strong>v{v.version}</strong> {v.name} <span className="muted">({day(v.valid_from)} to {v.valid_to ? day(v.valid_to) : "now"})</span>
        {v.features.length > 0 && <div className="muted">{v.features.join("; ")}</div>}</li>))}</ul>
  );
}

function Name({ p }: { p: PublishedProduct }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <strong>{p.name}</strong> {!p.active && <span className="tag">Inactive</span>}
      {p.earlier_names.length > 0 && <div className="muted">Renamed from {p.earlier_names.join(", ")}</div>}
      <details onToggle={(e) => setOpen(e.currentTarget.open)}>
        <summary className="muted">History</summary>
        {open && <History pkey={p.key} />}
      </details>
    </>
  );
}

function LastRun({ run, version, reload }: { run?: PublishedRun; version: number | null; reload: () => void }) {
  const toast = useToast();
  const me = useMe();
  const [busy, setBusy] = useState(false);
  const [fail, setFail] = useState<string>();
  const allowed = me?.role === "bid_manager" || me?.role === "admin";
  async function refresh() {
    setBusy(true); setFail(undefined);
    try {
      const r = await post<PublishedRun>("/api/catalog/refresh");
      toast.success(`Refreshed: ${r.added} added, ${r.changed} changed, ${r.removed} removed.`);
      reload();
    } catch (e) { setFail(errorMessage(e)); } finally { setBusy(false); }
  }
  return (
    <section className="card" data-tour="published-refresh">
      <div className="row">
        {run ? (
          <span>Last refresh {when(run.finished_at ?? run.started_at)} <StatusBadge status={RUN_TONE[run.status] ?? run.status} label={run.status} />
            {" "}{run.added} added / {run.changed} changed / {run.removed} removed · catalog version {version ?? "-"}</span>
        ) : <span className="muted">No refresh has run yet.</span>}
        <button disabled={busy || !allowed} title={allowed ? undefined : "Only the bid manager or an administrator can refresh."} onClick={refresh}>Refresh now</button>
        {busy && <Busy label="Reading the Flex pages, this can take about 30 seconds…" />}
      </div>
      {run?.error && <p className="warn">{run.error}</p>}
      <Alert kind="error">{fail}</Alert>
      {run && run.sources.length > 0 && (
        <details>
          <summary className="muted">{run.sources.length} page(s) read</summary>
          <table className="dense">
            <thead><tr><th>Page</th><th>Status</th><th className="num">Products</th><th>Error</th></tr></thead>
            <tbody>{run.sources.map((s) => (
              <tr key={s.url}><td><a href={s.url} target="_blank" rel="noopener noreferrer">{s.url}</a></td>
                <td><StatusBadge status={RUN_TONE[s.status] ?? s.status} label={s.status} /></td>
                <td className="num">{s.products}</td><td>{s.error}</td></tr>))}</tbody>
          </table>
        </details>)}
    </section>
  );
}

function Rows({ p, head, unit }: { p: PublishedProduct; head: boolean; unit: string }) {
  return (
    <>
      {head && <tr><th colSpan={6} scope="colgroup">{unit}</th></tr>}
      <tr>
        <td><Name p={p} /></td>
        <td>{p.category}</td>
        <td>{p.features.length === 0 ? <span className="muted">-</span> : <ul>{p.features.slice(0, 4).map((f, i) => <li key={i}>{f}</li>)}
          {p.features.length > 4 && <li className="muted">+{p.features.length - 4} more</li>}</ul>}</td>
        <td>{p.link ? <a href={p.link} target="_blank" rel="noopener noreferrer">Open</a> : <span className="muted">-</span>}</td>
        <td>{day(p.first_seen)}</td><td>{day(p.last_seen)}</td>
      </tr>
    </>
  );
}

export default function PublishedTab() {
  const { data, error, reload } = useApi<PublishedCatalog>("/api/catalog/published");
  const [unit, setUnit] = useState("");
  const [inactive, setInactive] = useState(false);
  const [q, setQ] = useState("");
  if (error) return <Alert kind="error">{error}</Alert>;
  if (!data) return <Skeleton lines={4} />;

  const unitOf = (p: PublishedProduct) => p.bu ?? NO_UNIT;
  const units = [...new Set(data.products.map(unitOf))].sort();
  const needle = q.trim().toLowerCase();
  const shown = data.products
    .filter((p) => (inactive || p.active) && (!unit || unitOf(p) === unit)
      && (!needle || [p.name, ...p.features].some((t) => t.toLowerCase().includes(needle))))
    .sort((a, b) => unitOf(a).localeCompare(unitOf(b)) || a.name.localeCompare(b.name));

  return (
    <>
      <p className="muted">Read from the official Flex product pages on server start and every 24 hours. It shows what is published (name, key features, link); it is not compliance evidence, and it does not change the matching.</p>
      <LastRun run={data.runs[0]} version={data.catalog_version} reload={reload} />
      {data.products.length === 0 ? <EmptyState title="No published catalog yet." hint="It is read on server start; use Refresh now." /> : (
        <>
          <div className="filters" data-tour="published-filters">
            <label><span className="sr-only">Unit</span>
              <select value={unit} onChange={(e) => setUnit(e.target.value)}>
                <option value="">All units</option>
                {units.map((u) => <option key={u} value={u}>{u}</option>)}</select></label>
            <label className="inline"><input type="checkbox" checked={inactive} onChange={(e) => setInactive(e.target.checked)} /> Include inactive</label>
            <label className="grow"><span className="sr-only">Search</span>
              <input type="search" placeholder="Search names and key features" value={q} onChange={(e) => setQ(e.target.value)} /></label>
            <span className="muted">{shown.length} of {data.products.length}</span>
          </div>
          {shown.length === 0 ? <EmptyState title="No product matches" hint="Try other filters." /> : (
            <table className="dense" data-tour="published-table">
              <thead><tr><th>Name</th><th>Category</th><th>Key features</th><th>Link</th><th>First seen</th><th>Last seen</th></tr></thead>
              <tbody>{shown.map((p, i) => <Rows key={p.key} p={p} head={i === 0 || unitOf(shown[i - 1]) !== unitOf(p)} unit={unitOf(p)} />)}</tbody>
            </table>)}
        </>)}
    </>
  );
}
