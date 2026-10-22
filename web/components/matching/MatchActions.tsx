"use client";
// Screen-3 actions on one requirement's match: accept, reject, or change its units and solution areas (C-40).  Owner: Atharv.
// Used inside the trace page's selectable rows: clicks on the buttons and the change form stay in here so they don't
// move the row selection; a click on the status line still selects the row (QA-11). Who may act comes from the API (canChange,
// matching.may_change, C-41): a technical match is its unit's designer / engineer's, any other item the bid manager's.
import { useState } from "react";
import { api, errorMessage, post } from "@/lib/api";
import { TERMS, type Match, type Product, type Unit } from "@/lib/types";
import { Busy, StatusBadge, offeringLabel, useToast } from "@/components/ui";

type Offering = "CTO" | "SEMI_CUSTOM" | "ETO";
type MatchUnit = { bu: string; product_id: string | null; offering_type: Offering };
type Props = { oppId: string; reqId: string; match: (Match & { units?: MatchUnit[] }) | null; dispatched: boolean; onDone: () => void;
  /** Walkthrough targets (data-tour="match-*"): the trace page sets it on the selected row only, so each id is unique. */
  tour?: boolean;
  /** P-44: the signed-in user may accept, reject or change this match (the row's can_change from the API, which checks too). */
  canChange?: boolean };

const OFFERINGS: Offering[] = ["CTO", "SEMI_CUSTOM", "ETO"];
// QA-04: how the match came about (matching.service stores the method; "rule" is a non-product category routed to the bid desk)
const METHOD: Record<string, string> = {
  manual: "set by a person", routed: "routed by the bid manager: the unit's designer / engineer confirms the solution", agent: "proposed by the matching agent",
  rule: "routed by rule", retrieval_only: "closest catalog entry (no agent answer)",
};
const stop = (e: React.SyntheticEvent) => e.stopPropagation();
const NO_SOLUTION = "Choose a solution for each unit (Change).";

export default function MatchActions({ oppId, reqId, match: m, dispatched, onDone, tour, canChange = true }: Props) {
  const toast = useToast();
  const t = (name: string) => (tour ? name : undefined);
  const [catalog, setCatalog] = useState<{ units: Unit[]; products: Product[] }>();
  const [draft, setDraft] = useState<MatchUnit[]>();
  const [busy, setBusy] = useState(false);
  const hasSolution = !(m?.units ?? []).some((u) => !u.product_id); // routed by the bid manager: the engineer sets it with Change
  const fail = (e: unknown) => { setBusy(false); toast.error(errorMessage(e)); };

  const decide = (action: "accept" | "reject") => {
    setBusy(true);
    post(`/api/matches/${m!.id}/decide`, { action }).then(() => {
      setBusy(false); onDone();
      toast.success(action === "accept" ? `${reqId}: match accepted.` : `${reqId}: match rejected; it goes back to the bid manager to route.`);
    }, fail);
  };
  const openChange = () => {
    setDraft(m?.units ?? []);
    if (!catalog) api<{ units: Unit[]; products: Product[] }>("/api/catalog").then(
      (c) => setCatalog({ ...c, units: c.units.filter((u) => u.status === "active") }),
      (e) => { setDraft(undefined); fail(e); }); // pending units can't be offered; a failed load closes the form (19 Oct review)
  };
  const save = () => {
    setBusy(true);
    post(`/api/bids/${oppId}/requirements/${reqId}/match`,
      { units: draft!.map(({ product_id, offering_type }) => ({ product_id, offering_type })) })
      .then(() => { setBusy(false); setDraft(undefined); onDone(); toast.success(`${reqId}: match saved.`); }, fail);
  };
  const product = (id: string) => catalog?.products.find((p) => p.id === id);
  const setRow = (i: number, change: Partial<MatchUnit>) => setDraft(draft!.map((u, j) => (j === i ? { ...u, ...change } : u)));
  const addRow = () => {
    const p = catalog?.products.find((x) => catalog.units.some((u) => u.code === x.bu));
    if (p) setDraft([...draft!, { bu: p.bu, product_id: p.id, offering_type: p.offering_type as Offering }]);
  };

  return (
    <div className="match-actions" data-tour={t("match-actions")}>
      {/* a non-product item routed by rule needs no acceptance: no status badge, no Accept / Reject; a match with no unit (a capability
          gap, or a product item that needs an owner) has no solution to accept, so no badge either: pane 3 says what it is */}
      {m && <div className="muted match-meta" data-tour={t("match-meta")}>{m.method !== "rule" && (m.bu || m.status === "rejected") && <StatusBadge status={m.status} />} {METHOD[m.method] ?? m.method}</div>}

      {draft === undefined ? (canChange && ( // only the person who may act sees the buttons (matching.may_change)
        <div className="row-actions" onClick={stop} onKeyDown={stop} data-tour={t("match-buttons")}>
          {m?.status === "proposed" && m.method !== "rule" && <>
            <button disabled={busy || !hasSolution} title={hasSolution ? undefined : NO_SOLUTION} onClick={() => decide("accept")} data-tour={t("match-accept")}>Accept</button>
            <button disabled={busy} className="secondary" onClick={() => decide("reject")} data-tour={t("match-reject")}>Reject</button>
          </>}
          <button disabled={busy} className="secondary" onClick={openChange} data-tour={t("match-change")}>Change</button>
          {busy && <Busy label="Saving…" />}
        </div>)
      ) : (
        <div className="form compact" onClick={stop} onKeyDown={stop} data-tour={t("match-form")}>
          {!catalog && <Busy label="Loading catalog…" />}
          {catalog && draft.map((u, i) => (
            <div key={i} className="row-actions">
              <label><span className="sr-only">{TERMS.solution_area}</span>
                <select value={u.product_id ?? ""} onChange={(e) => {
                  const p = product(e.target.value)!;
                  setRow(i, { bu: p.bu, product_id: p.id, offering_type: p.offering_type as Offering });
                }}>
                  <option value="" disabled>Choose a solution</option>
                  {catalog.units.map((unit) => (
                    <optgroup key={unit.code} label={unit.name}>
                      {catalog.products.filter((p) => p.bu === unit.code).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </optgroup>
                  ))}
                </select>
              </label>
              <label><span className="sr-only">{TERMS.offering_type}</span>
                <select value={u.offering_type} onChange={(e) => setRow(i, { offering_type: e.target.value as Offering })}>
                  {OFFERINGS.map((o) => <option key={o} value={o}>{offeringLabel(o)}</option>)}
                </select>
              </label>
              <button className="secondary" aria-label={`Remove ${(u.product_id && product(u.product_id)?.name) || u.bu}`} onClick={() => setDraft(draft.filter((_, j) => j !== i))}>Remove</button>
            </div>
          ))}
          {catalog && draft.length === 0 && <span className="muted">No unit: a non-product item goes to the bid desk (commercial and submission items); a product item is listed as Needs an owner until the bid manager routes it to a unit or records a capability gap.</span>}
          {dispatched && <span className="warn" data-tour={t("match-dispatched-warning")}>Already sent to units: the bid manager sends for assessment again on the Assessment Summary to apply this change.
            Added units get the work (if they take part); removed units have theirs withdrawn.</span>}
          <div className="row-actions">
            <button className="secondary" disabled={!catalog || busy} onClick={addRow} data-tour={t("match-add-unit")}>Add unit</button>
            <button disabled={busy || !catalog || draft.some((u) => !u.product_id)} title={draft.some((u) => !u.product_id) ? NO_SOLUTION : undefined}
              onClick={save} data-tour={t("match-save")}>Save</button>
            <button className="secondary" disabled={busy} onClick={() => setDraft(undefined)} data-tour={t("match-cancel")}>Cancel</button>
            {busy && <Busy label="Saving…" />}
          </div>
        </div>
      )}
    </div>
  );
}
