"use client";
// Business units, products and knowledge-base search.  Owner: Atharv.
import { useState } from "react";
import { useApi } from "@/lib/api";
import type { Product, Unit } from "@/lib/types";
import PageHead from "@/components/shell/PageHead";

type Hit = { kind: string; id: string; bu: string; score: number; text: string };
type Data = { units: Unit[]; products: Product[]; results: Hit[] };

export default function CatalogPage() {
  const [q, setQ] = useState("");
  const { data } = useApi<Data>(`/api/catalog?q=${encodeURIComponent(q)}`);
  return (
    <div className="content">
      <PageHead title="Product catalog" help="Business units, their products and past responses used for matching. Illustrative seed data, to be confirmed with each unit." />
      <form className="inline" action={(f) => setQ(String(f.get("q") ?? ""))}>
        <label><span className="sr-only">Search the knowledge base</span>
          <input name="q" defaultValue={q} placeholder="Search the knowledge base" /></label><button>Search</button>
      </form>
      {data && data.results.length > 0 && (
        <table>
          <thead><tr><th>Score</th><th>Kind</th><th>Unit</th><th>ID</th><th>Text</th></tr></thead>
          <tbody>{data.results.map((r) => <tr key={r.id}><td>{r.score}</td><td>{r.kind}</td><td>{r.bu}</td><td className="mono">{r.id}</td><td>{r.text.slice(0, 160)}</td></tr>)}</tbody>
        </table>
      )}
      {data?.units.map((u) => (
        <section key={u.code} className="card">
          <h2>{u.name} <span className="badge">{u.status}</span></h2>
          <p>{u.focus}</p>
          <p className="muted">{u.product_manager} · {u.design_engineer}</p>
          <ul>{data.products.filter((p) => p.bu === u.code).map((p) =>
            <li key={p.id}><span className="mono">{p.id}</span> {p.name} <span className={`tag ${p.offering_type}`}>{p.offering_type}</span></li>)}</ul>
        </section>
      ))}
    </div>
  );
}
