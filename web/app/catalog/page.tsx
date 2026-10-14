"use client";
// Business units, product families with their published models, and knowledge-base search.  Owner: Atharv.
import { useState } from "react";
import { useApi } from "@/lib/api";
import type { Product, Unit } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { Alert, EmptyState, Skeleton, StatusBadge } from "@/components/ui";

type Hit = { kind: string; id: string; bu: string; score: number; text: string; family?: string };
type Item = { id: string; family: string; bu: string; model: string; name: string; specs: string; source_url: string };
type Data = { units: Unit[]; products: Product[]; items: Item[]; results: Hit[] };

const Source = ({ url }: { url?: string }) =>
  url ? <a className="catalog-source" href={url} target="_blank" rel="noopener noreferrer">source</a> : null;

export default function CatalogPage() {
  const [q, setQ] = useState("");
  const { data, error } = useApi<Data>(`/api/catalog?q=${encodeURIComponent(q)}`);
  return (
    <div className="content">
      <PageHead title="Product catalog" help="Business units, their product families and models, and the past responses used for matching." />
      <p className="muted catalog-provenance">Families and models from public Flex web pages (retrieved 12 Oct 2026); to be confirmed with each unit.</p>
      <form className="inline catalog-search" role="search" action={(f) => setQ(String(f.get("q") ?? "").trim())} data-tour="catalog-search">
        <label><span className="sr-only">Search the knowledge base</span>
          <input type="search" name="q" defaultValue={q} placeholder="Search products, models and past responses" data-tour="catalog-search-input" /></label>
        <button data-tour="catalog-search-button">Search</button>
        {q && <button type="button" className="secondary" onClick={() => setQ("")}>Clear</button>}
      </form>
      <Alert kind="error">{error}</Alert>
      {!data && !error && <Skeleton lines={4} />}
      {data && q && (
        <section className="card" data-tour="catalog-results">
          <div className="card-head"><h2>Results for “{q}”</h2><span className="muted">{data.results.length} match(es), best first</span></div>
          {data.results.length === 0 ? <p className="muted">Nothing matches. Try another wording; the index holds product families, their models and past responses.</p> : (
            <table className="dense" data-tour="catalog-results-table">
              <thead><tr><th className="num">Score</th><th>Kind</th><th>Unit</th><th>ID</th><th>Text</th></tr></thead>
              <tbody>{data.results.map((r) => (
                <tr key={r.id}><td className="num">{r.score}</td>
                  <td>{r.kind === "catalog_item" ? <>model of <span className="mono">{r.family}</span></> : r.kind}</td>
                  <td>{r.bu}</td><td className="mono">{r.id}</td><td>{r.text.slice(0, 160)}</td></tr>))}</tbody>
            </table>)}
        </section>
      )}
      {data?.units.length === 0 && <EmptyState title="No business units" hint="No business units are loaded yet." />}
      {data?.units.map((u) => {
        const products = data.products.filter((p) => p.bu === u.code);
        return (
          <section key={u.code} className="card" data-tour={`catalog-unit-${u.code}`}>
            <div className="card-head" data-tour={`catalog-unit-head-${u.code}`}>
              <h2>{u.name} <span className="mono muted">{u.code}</span></h2>
              <span className="muted">{u.pillar}</span>
              <StatusBadge status={u.status} />
            </div>
            <p>{u.focus} <Source url={u.source_url} /></p>
            <p className="muted" data-tour={`catalog-unit-people-${u.code}`}>Product manager {u.product_manager} · Design engineer {u.design_engineer}</p>
            {products.length === 0 ? <p className="muted">No products listed.</p> : (
              <ul className="catalog-products" data-tour={`catalog-products-${u.code}`}>{products.map((p) => {
                const models = data.items.filter((i) => i.family === p.id);
                return (
                  <li key={p.id}><span className="mono">{p.id}</span> {p.name} <StatusBadge status={p.offering_type} kind="offering" /> <Source url={p.source_url} />
                    {models.length > 0 && (
                      <details className="catalog-models">
                        <summary>{models.length} model{models.length > 1 ? "s" : ""} / series</summary>
                        <ul>{models.map((m) => (
                          <li key={m.id}><strong>{m.model}</strong> {m.name !== m.model && <>{m.name}. </>}<span className="muted">{m.specs}</span> <Source url={m.source_url} /></li>))}</ul>
                      </details>)}
                  </li>);
              })}</ul>)}
          </section>
        );
      })}
    </div>
  );
}
