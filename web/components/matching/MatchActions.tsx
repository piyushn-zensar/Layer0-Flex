"use client";
// Screen-3 actions on one requirement's match: accept, reject, or change its units and products.  Owner: Atharv.
// Used inside the trace page's selectable rows: clicks on the buttons and the change form stay in here so they don't
// move the row selection; a click on the status line still selects the row (QA-11).
import { useState } from "react";
import { api, errorMessage, post } from "@/lib/api";
import type { Match, Product, Unit } from "@/lib/types";
import { Busy, StatusBadge, offeringLabel, useToast } from "@/components/ui";

type Offering = "CTO" | "SEMI_CUSTOM" | "ETO";
type MatchUnit = { bu: string; product_id: string; offering_type: Offering };
type Props = { oppId: string; reqId: string; match: (Match & { units?: MatchUnit[] }) | null; dispatched: boolean; onDone: () => void;
  /** Walkthrough targets (data-tour="match-*"): the trace page sets it on the selected row only, so each id is unique. */
  tour?: boolean };

const OFFERINGS: Offering[] = ["CTO", "SEMI_CUSTOM", "ETO"];
// QA-04: how the match came about (matching.service stores the method; "rule" is a non-product category routed to the bid desk)
const METHOD: Record<string, string> = {
  manual: "set by a person", agent: "proposed by the matching agent",
  rule: "routed to the bid desk by rule (not a product category)", retrieval_only: "closest catalog entry (no agent answer)",
};
const stop = (e: React.SyntheticEvent) => e.stopPropagation();

export default function MatchActions({ oppId, reqId, match: m, dispatched, onDone, tour }: Props) {
  const toast = useToast();
  const t = (name: string) => (tour ? name : undefined);
  const [catalog, setCatalog] = useState<{ units: Unit[]; products: Product[] }>();
  const [draft, setDraft] = useState<MatchUnit[]>();
  const [busy, setBusy] = useState(false);
  const fail = (e: unknown) => { setBusy(false); toast.error(errorMessage(e)); };

  const decide = (action: "accept" | "reject") => {
    setBusy(true);
    post(`/api/matches/${m!.id}/decide`, { action }).then(() => {
      setBusy(false); onDone();
      toast.success(action === "accept" ? `${reqId}: match accepted.` : `${reqId}: match rejected. Use Change to pick a unit.`);
    }, fail);
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
      .then(() => { setBusy(false); setDraft(undefined); onDone(); toast.success(`${reqId}: match saved.`); }, fail);
  };
  const product = (id: string) => catalog?.products.find((p) => p.id === id);
  const setRow = (i: number, change: Partial<MatchUnit>) => setDraft(draft!.map((u, j) => (j === i ? { ...u, ...change } : u)));
  const addRow = () => {
    const p = catalog?.products.find((x) => catalog.units.some((u) => u.code === x.bu));
    if (p) setDraft([...draft!, { bu: p.bu, product_id: p.id, offering_type: p.offering_type as Offering }]);
  };
  const others = (m?.units ?? []).slice(1);

  return (
    <div className="match-actions" data-tour={t("match-actions")}>
      {others.length > 0 && <div className="muted" data-tour={t("match-others")}>Also: {others.map((u) => `${u.bu} · ${u.product_id}`).join(", ")}</div>}
      {m && <div className="muted match-meta" data-tour={t("match-meta")}><StatusBadge status={m.status} /> {METHOD[m.method] ?? m.method}</div>}

      {draft === undefined ? (
        <div className="row-actions" onClick={stop} onKeyDown={stop} data-tour={t("match-buttons")}>
          {m?.status === "proposed" && <>
            <button disabled={busy} onClick={() => decide("accept")} data-tour={t("match-accept")}>Accept</button>
            <button disabled={busy} className="secondary" onClick={() => decide("reject")} data-tour={t("match-reject")}>Reject</button>
          </>}
          <button disabled={busy} className="secondary" onClick={openChange} data-tour={t("match-change")}>Change</button>
          {busy && <Busy label="Saving…" />}
        </div>
      ) : (
        <div className="form compact" onClick={stop} onKeyDown={stop} data-tour={t("match-form")}>
          {!catalog && <Busy label="Loading catalog…" />}
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
                  {OFFERINGS.map((o) => <option key={o} value={o}>{offeringLabel(o)}</option>)}
                </select>
              </label>
              <button className="secondary" aria-label={`Remove ${u.product_id}`} onClick={() => setDraft(draft.filter((_, j) => j !== i))}>Remove</button>
            </div>
          ))}
          {catalog && draft.length === 0 && <span className="muted">No unit: the bid manager answers it (not a product item).</span>}
          {dispatched && <span className="warn" data-tour={t("match-dispatched-warning")}>Already sent to units: dispatch again on the Decisions page to apply this change.
            Added units get the work (if they take part); removed units have theirs withdrawn.</span>}
          <div className="row-actions">
            <button className="secondary" disabled={!catalog || busy} onClick={addRow} data-tour={t("match-add-unit")}>Add unit</button>
            <button disabled={busy || !catalog} onClick={save} data-tour={t("match-save")}>Save</button>
            <button className="secondary" disabled={busy} onClick={() => setDraft(undefined)} data-tour={t("match-cancel")}>Cancel</button>
            {busy && <Busy label="Saving…" />}
          </div>
        </div>
      )}
    </div>
  );
}
