"use client";
// Business units, products and knowledge-base search.  Owner: Atharv.
import { useState } from "react";
import { useApi } from "@/lib/api";
import type { Product, Unit } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";
import { Alert, EmptyState, Skeleton, StatusBadge } from "@/components/ui";

type Hit = { kind: string; id: string; bu: string; score: number; text: string };
type Data = { units: Unit[]; products: Product[]; results: Hit[] };

export default function CatalogPage() {
  const [q, setQ] = useState("");
  const { data, error } = useApi<Data>(`/api/catalog?q=${encodeURIComponent(q)}`);
  return (
    <div className="content">
      <PageHead title="Product catalog" help="Business units, their products and past responses used for matching. Illustrative seed data, to be confirmed with each unit." />
      <form className="inline catalog-search" role="search" action={(f) => setQ(String(f.get("q") ?? "").trim())} data-tour="catalog-search">
        <label><span className="sr-only">Search the knowledge base</span>
          <input type="search" name="q" defaultValue={q} placeholder="Search products and past responses" data-tour="catalog-search-input" /></label>
        <button data-tour="catalog-search-button">Search</button>
        {q && <button type="button" className="secondary" onClick={() => setQ("")}>Clear</button>}
      </form>
      <Alert kind="error">{error}</Alert>
      {!data && !error && <Skeleton lines={4} />}
      {data && q && (
        <section className="card" data-tour="catalog-results">
          <div className="card-head"><h2>Results for “{q}”</h2><span className="muted">{data.results.length} match(es), best first</span></div>
          {data.results.length === 0 ? <p className="muted">Nothing matches. Try another wording; the index holds product descriptions and past responses.</p> : (
            <table className="dense" data-tour="catalog-results-table">
              <thead><tr><th className="num">Score</th><th>Kind</th><th>Unit</th><th>ID</th><th>Text</th></tr></thead>
              <tbody>{data.results.map((r) => (
                <tr key={r.id}><td className="num">{r.score}</td><td>{r.kind}</td><td>{r.bu}</td><td className="mono">{r.id}</td><td>{r.text.slice(0, 160)}</td></tr>))}</tbody>
            </table>)}
        </section>
      )}
      {data?.units.length === 0 && <EmptyState title="No business units" hint="The catalog seed has not been loaded." />}
      {data?.units.map((u) => {
        const products = data.products.filter((p) => p.bu === u.code);
        return (
          <section key={u.code} className="card" data-tour={`catalog-unit-${u.code}`}>
            <div className="card-head" data-tour={`catalog-unit-head-${u.code}`}>
              <h2>{u.name} <span className="mono muted">{u.code}</span></h2>
              <span className="muted">{u.pillar}</span>
              <StatusBadge status={u.status} />
            </div>
            <p>{u.focus}</p>
            <p className="muted" data-tour={`catalog-unit-people-${u.code}`}>Product manager {u.product_manager} · Design engineer {u.design_engineer}</p>
            {products.length === 0 ? <p className="muted">No products listed.</p> : (
              <ul className="catalog-products" data-tour={`catalog-products-${u.code}`}>{products.map((p) =>
                <li key={p.id}><span className="mono">{p.id}</span> {p.name} <StatusBadge status={p.offering_type} kind="offering" /></li>)}</ul>)}
          </section>
        );
      })}
    </div>
  );
}
