"use client";
// Loads the product list and what the list call does not carry (J-19, C-60, C-63, C-65).  Owner: Janvia.
//   rows:   GET /api/catalog/products, every page (200 rows each), so search, filters, sort and paging run in the browser.
//   media:  GET /api/catalog/product?part=<family key> once per family, for its documents and images (the manifests are joined
//           by the API), and once per part that has conflicts, for the fields in disagreement.
// ponytail: one call per web series (about 76) and per conflicting part (12) because the list rows carry no document, image or
// conflict count. Ask Piyush to add `documents` (count), `image` (file, verified) and `conflicts` (count) to ProductRow
// (contract change), then drop `media` and read them from the rows. Past a few thousand rows, page on the server instead.
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ProductDetail, ProductPage, ProductRow } from "@/lib/types";
import type { MediaIndex } from "./products";

const PAGE = 200;            // the API's largest page
const PARALLEL = 6;          // browsers allow about six connections to one host
const KEEP_MS = 60_000;      // a tab change back to this view within a minute reuses what was loaded

const empty = (): MediaIndex => ({ family: new Map(), conflicts: new Map() });
let saved: { at: number; rows: ProductRow[]; idx: MediaIndex; ready: boolean } | null = null;

async function loadRows(): Promise<ProductRow[]> {
  const first = await api<ProductPage>(`/api/catalog/products?size=${PAGE}&page=1&sort=part_number`);
  const pages = Math.ceil(first.total / PAGE);
  const rest = await Promise.all(Array.from({ length: Math.max(0, pages - 1) }, (_, i) =>
    api<ProductPage>(`/api/catalog/products?size=${PAGE}&page=${i + 2}&sort=part_number`)));
  return [first, ...rest].flatMap((p) => p.items);
}

/** Run `job` over `items` with at most PARALLEL in flight; one failed call is skipped (that product shows no documents), not fatal. */
async function pool<T>(items: T[], job: (item: T) => Promise<void>) {
  let next = 0;
  await Promise.all(Array.from({ length: Math.min(PARALLEL, items.length) }, async () => {
    while (next < items.length) { const item = items[next++]; try { await job(item); } catch { /* leave it unloaded */ } }
  }));
}

export function useProducts() {
  const fresh = saved && Date.now() - saved.at < KEEP_MS ? saved : null;
  const [rows, setRows] = useState<ProductRow[] | undefined>(fresh?.rows);
  const [idx, setIdx] = useState<MediaIndex>(fresh?.idx ?? empty());
  const [ready, setReady] = useState(fresh?.ready ?? false);     // every document / image / conflict call has finished
  const [progress, setProgress] = useState<[number, number]>([0, 0]);
  const [error, setError] = useState<string>();
  const [tries, setTries] = useState(0);

  useEffect(() => {
    let live = true;                                       // this run only: a re-run (dev strict mode, Retry) never feeds an old one
    if (fresh && tries === 0) return () => { live = false; };
    setError(undefined); setReady(false);
    (async () => {
      const all = await loadRows();
      if (!live) return;
      setRows(all);
      const idx2 = empty();
      const families = [...new Set(all.map((r) => r.family_key).filter((k): k is string => !!k))];
      const conflicting = all.filter((r) => r.has_conflict).map((r) => r.key);
      const total = families.length + conflicting.length; let done = 0;
      setProgress([0, total]);
      const tick = () => { done++; if (live && (done % 8 === 0 || done === total)) { setIdx({ family: new Map(idx2.family), conflicts: new Map(idx2.conflicts) }); setProgress([done, total]); } };
      await Promise.all([
        pool(families, async (k) => { const d = await api<ProductDetail>(`/api/catalog/product?part=${encodeURIComponent(k)}`); idx2.family.set(k, { documents: d.documents, images: d.images }); tick(); }),
        pool(conflicting, async (k) => { const d = await api<ProductDetail>(`/api/catalog/product?part=${encodeURIComponent(k)}`); idx2.conflicts.set(k, d.conflicts ?? []); tick(); }),
      ]);
      if (!live) return;
      setIdx({ family: new Map(idx2.family), conflicts: new Map(idx2.conflicts) }); setReady(true); setProgress([total, total]);
      saved = { at: Date.now(), rows: all, idx: idx2, ready: true };
    })().catch((e) => { if (live) setError(e instanceof Error ? e.message : String(e)); });
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tries]);

  return { rows, idx, ready, progress, error, retry: () => { saved = null; setTries((n) => n + 1); } };
}
