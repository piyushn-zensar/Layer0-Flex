"use client";
// Traceability pane 3 (P-57, C-59): where the product configurator put this requirement — the requested component, its outcome,
// the requirement's status with the reason (for a group row: each sub-requirement's), and for a DC/DC component the first
// candidate parts (links to the catalog). The configurator's result on the supplied product data, pending engineering review.
// Owner: Piyush.
import Link from "next/link";
import { useMemo } from "react";
import { useApi } from "@/lib/api";
import { TERMS, type ComponentMatch, type ComponentRequirement, type ComponentsResponse } from "@/lib/types";
import { StatusBadge } from "@/components/ui";
import { FIT, OutcomeBadge } from "./ComponentMatching";

type Entry = { component: ComponentMatch; requirement: ComponentRequirement };

/** One request for the whole pane: requirement ID (and group ID, for its sub-requirements) -> its configurator entries. */
export function useComponentsByReq(oppId: string) {
  const { data } = useApi<ComponentsResponse>(`/api/bids/${oppId}/components`);
  return useMemo(() => {
    const by = new Map<string, Entry[]>();
    const add = (id: string, e: Entry) => by.set(id, [...(by.get(id) ?? []), e]);
    for (const c of data?.components ?? []) for (const r of c.detail.requirements) {
      add(r.req_id, { component: c, requirement: r });
      if (r.parent) add(r.parent, { component: c, requirement: r });
    }
    return { by, outcomes: data?.outcomes ?? {} };
  }, [data]);
}

export default function RequirementProducts({ reqId, entries, outcomes }: { reqId: string; entries?: Entry[]; outcomes: Record<string, string> }) {
  if (!entries?.length) return null;
  const byComponent = new Map<number, Entry[]>();
  entries.forEach((e) => byComponent.set(e.component.id, [...(byComponent.get(e.component.id) ?? []), e]));
  return (
    <div className="trace-config">
      {[...byComponent.values()].map((es) => {
        const c = es[0].component;
        const parts = (c.detail.candidates?.length ? c.detail.candidates : c.detail.near_matches ?? []).slice(0, 3);
        return (
          <div key={c.id}>
            <span className="muted">{TERMS.domain_alignment}: {c.name}</span> <OutcomeBadge c={c} labels={outcomes} />
            {es.filter(({ requirement: r }) => r.req_id === reqId || r.fields.length > 0).map(({ requirement: r }) => (
              <div key={r.req_id}>{r.req_id !== reqId && <span className="mono">{r.req_id} </span>}
                <StatusBadge status={FIT[r.status].tone} label={FIT[r.status].label} /> <span className="muted">{r.why}</span></div>))}
            {(() => { // a group row: its other sub-requirements gave the configurator nothing to check
              const rest = es.filter(({ requirement: r }) => r.req_id !== reqId && r.fields.length === 0).length;
              return rest > 0 && <div className="muted">{rest} other sub-requirement{rest === 1 ? "" : "s"}: not configurator inputs (engineering review)</div>;
            })()}
            {parts.length > 0 && es.some((e) => e.requirement.fields.length > 0) && <div className="muted">
              {c.outcome === "near_match" ? "Near matches" : "Candidates"}:{" "}
              {parts.map((p, i) => <span key={p.part_number}>{i > 0 && ", "}<Link className="mono" href={p.link}>{p.part_number}</Link></span>)}</div>}
          </div>);
      })}
    </div>
  );
}
