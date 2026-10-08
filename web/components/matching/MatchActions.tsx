"use client";
// Screen-3 actions on one requirement's match: accept, reject, or change its units and products.  Owner: Atharv.
// Used inside the trace page's selectable rows: clicks and keys stay in here so they don't move the row selection.
import { useState } from "react";
import { api, post } from "@/lib/api";
import type { Match, Product, Unit } from "@/lib/types";

type Offering = "CTO" | "SEMI_CUSTOM" | "ETO";
type MatchUnit = { bu: string; product_id: string; offering_type: Offering };
type Props = { oppId: string; reqId: string; match: (Match & { units?: MatchUnit[] }) | null; dispatched: boolean; onDone: () => void };

const OFFERINGS: Offering[] = ["CTO", "SEMI_CUSTOM", "ETO"];

export default function MatchActions({ oppId, reqId, match: m, dispatched, onDone }: Props) {
  const [catalog, setCatalog] = useState<{ units: Unit[]; products: Product[] }>();
  const [draft, setDraft] = useState<MatchUnit[]>();
  const [busy, setBusy] = useState(false);
  const fail = (e: unknown) => { setBusy(false); alert(e); };

  const decide = (action: "accept" | "reject") => {
    setBusy(true);
    post(`/api/matches/${m!.id}/decide`, { action }).then(() => { setBusy(false); onDone(); }, fail);
  };
  const openChange = () => {
    setDraft(m?.units ?? []);
    if (!catalog) api<{ units: Unit[]; products: Product[] }>("/api/catalog").then(
      (c) => setCatalog({ ...c, units: c.units.filter((u) => u.status === "active") }), fail); // pending units can't be offered
  };
  const save = () => {
    setBusy(true);
    post(`/api/opportunities/${oppId}/requirements/${reqId}/match`,
      { units: draft!.map(({ product_id, offering_type }) => ({ product_id, offering_type })) })
      .then(() => { setBusy(false); setDraft(undefined); onDone(); }, fail);
  };
  const product = (id: string) => catalog?.products.find((p) => p.id === id);
  const setRow = (i: number, change: Partial<MatchUnit>) => setDraft(draft!.map((u, j) => (j === i ? { ...u, ...change } : u)));
  const addRow = () => {
    const p = catalog?.products.find((x) => catalog.units.some((u) => u.code === x.bu));
    if (p) setDraft([...draft!, { bu: p.bu, product_id: p.id, offering_type: p.offering_type as Offering }]);
  };
  const others = (m?.units ?? []).slice(1);

  return (
    <div onClick={(e) => e.stopPropagation()} onKeyDown={(e) => e.stopPropagation()}>
      {others.length > 0 && <div className="muted">Also: {others.map((u) => `${u.bu} · ${u.product_id}`).join(", ")}</div>}
      {m && <div className="muted">
        <span className={`badge status-${m.status === "accepted" ? "approved" : m.status}`}>{m.status}</span>
        {m.method === "manual" ? "set by a person" : m.method === "agent" ? "proposed by the matching agent" : "closest catalog entry (no agent answer)"}
      </div>}

      {draft === undefined ? (
        <div className="row-actions">
          {m?.status === "proposed" && <>
            <button disabled={busy} onClick={() => decide("accept")}>Accept</button>
            <button disabled={busy} className="secondary" onClick={() => decide("reject")}>Reject</button>
          </>}
          <button disabled={busy} className="secondary" onClick={openChange}>Change</button>
        </div>
      ) : (
        <div className="form compact">
          {!catalog && <span className="muted">Loading catalog…</span>}
          {catalog && draft.map((u, i) => (
            <div key={i} className="row-actions">
              <label><span className="sr-only">Product</span>
                <select value={u.product_id} onChange={(e) => {
                  const p = product(e.target.value)!;
                  setRow(i, { bu: p.bu, product_id: p.id, offering_type: p.offering_type as Offering });
                }}>
                  {catalog.units.map((unit) => (
                    <optgroup key={unit.code} label={unit.name}>
                      {catalog.products.filter((p) => p.bu === unit.code).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </optgroup>
                  ))}
                </select>
              </label>
              <label><span className="sr-only">Offering type</span>
                <select value={u.offering_type} onChange={(e) => setRow(i, { offering_type: e.target.value as Offering })}>
                  {OFFERINGS.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              </label>
              <button className="secondary" aria-label={`Remove ${u.product_id}`} onClick={() => setDraft(draft.filter((_, j) => j !== i))}>Remove</button>
            </div>
          ))}
          {catalog && draft.length === 0 && <span className="muted">No unit: the bid manager answers it (not a product item).</span>}
          {dispatched && <span className="warn">Already sent to units: dispatch again on the Decisions page to apply this change.
            Added units get the work (if they take part); removed units have theirs withdrawn.</span>}
          <div className="row-actions">
            <button className="secondary" disabled={!catalog} onClick={addRow}>Add unit</button>
            <button disabled={busy || !catalog} onClick={save}>Save</button>
            <button className="secondary" onClick={() => setDraft(undefined)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}
