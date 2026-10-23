"use client";
// Technical Requirement Matching on the Assessment Summary (P-57; C-59, C-61): the product configurator's last run over the
// register. Coverage, each requested component with its outcome and reason, the requirement <-> product comparison, gaps,
// assumptions (stated in the RFP or a default) and the engineering reviews still pending. A run is the configurator's
// result on the supplied product data, pending engineering review: never proof that the RFP can be met. Running it is
// the bid manager's.  Owner: Piyush.
import Link from "next/link";
import { Fragment, useState } from "react";
import { BID_MANAGER_ONLY, errorMessage, isBidManager, post, useApi, useMe } from "@/lib/api";
import { TERMS, formatDate, type ComponentMatch, type ComponentOutcome, type ComponentsResponse, type RequirementFit } from "@/lib/types";
import { Alert, Busy, Skeleton, StatusBadge, useToast } from "@/components/ui";

// tones through StatusBadge's existing keys: pass = green, warn = amber, fail = red, frozen = blue, n/a = grey
const OUTCOME_TONE: Record<ComponentOutcome, string> = { match: "pass", near_match: "warn", insufficient_information: "warn",
  no_match: "fail", system_checks: "frozen", not_applicable: "n/a", not_assessed: "n/a" };
export const FIT: Record<RequirementFit, { label: string; tone: string }> = { satisfied: { label: "Satisfied", tone: "pass" },
  not_satisfied: { label: "Not satisfied", tone: "fail" }, cannot_assess: { label: "Cannot assess yet", tone: "warn" } };
const CHECK_TONE: Record<string, string> = { open: "warn", not_supported: "n/a", pass: "pass", fail: "fail", review: "warn", unknown: "n/a" };
const CHECK_LABEL: Record<string, string> = { open: "Open", not_supported: "Not checked by the configurator", pass: "Pass", fail: "Fail",
  review: "To review", unknown: "Unknown" };
const KIND: Record<ComponentMatch["kind"], string> = { dc_dc: "DC/DC module search", system: "Installation checks",
  spec_range: "Published ratings search", other: "No product table" };

export function OutcomeBadge({ c, labels }: { c: Pick<ComponentMatch, "outcome">; labels: Record<string, string> }) {
  return <StatusBadge status={OUTCOME_TONE[c.outcome]} label={labels[c.outcome] ?? c.outcome} />;
}

function ReqLink({ oppId, id }: { oppId: string; id: string }) {
  return <Link className="mono" href={`/opportunities/${oppId}/trace#${id}`}>{id}</Link>;
}

function Details({ oppId, c }: { oppId: string; c: ComponentMatch }) {
  const d = c.detail;
  const cmp = d.comparison;
  return (
    <div>
      {cmp && cmp.rows.length > 0 && cmp.parts.length > 0 && <>
        <h4>Requirement ↔ product{c.outcome === "near_match" ? " (near matches: they fail one constraint)" : ""}</h4>
        <div className="table-scroll"><table className="dense">
          <thead><tr><th>Constraint</th><th>Required</th><th>From</th>
            {cmp.parts.map((p, i) => <th key={p}><Link href={cmp.links[i]} className="mono">{p}</Link></th>)}</tr></thead>
          <tbody>{cmp.rows.map((r) => (
            <tr key={r.constraint}><td>{r.constraint}</td><td><strong>{r.required}</strong></td>
              <td>{r.req_ids.map((id) => <div key={id}><ReqLink oppId={oppId} id={id} /></div>)}</td>
              {r.values.map((v, i) => <td key={i}>{v}</td>)}</tr>))}</tbody>
        </table></div></>}
      {(d.candidates?.length ?? 0) > 3 && <details><summary>All {d.candidates!.length} candidate parts</summary>
        <ul className="per-req">{d.candidates!.map((p) => <li key={p.part_number}><Link className="mono" href={p.link}>{p.part_number}</Link>{" "}
          <span className="muted">{p.family ?? p.series} · {p.power_w_per_module ?? "?"} W × {p.modules_total ?? "?"} · {p.efficiency_pct ?? "?"}%
            {p.conflicts.length > 0 && " · web page disagrees"}</span></li>)}</ul></details>}
      {(d.spec_candidates?.length ?? 0) > 0 && <details><summary>Published variants compared ({d.spec_candidates!.length}; families {d.families?.join(", ")})</summary>
        <ul className="per-req">{d.spec_candidates!.map((s) => <li key={s.spec_id}><Link href={s.link}>{s.family_key}</Link> · {s.variant}{" "}
          <span className="muted">{s.fails} failing, {s.unknowns} not published, of {s.compared} compared{s.verified ? " · confirmed by the unit" : " · unverified"}</span></li>)}</ul>
      </details>}
      {(d.web_listed?.length ?? 0) > 0 && <p className="muted">Listed on the unit&apos;s web pages with no published ratings (not assessed; ask the unit):{" "}
        {d.web_listed!.map((w, i) => <span key={w.key}>{i > 0 && ", "}<Link href={w.link}>{w.name}</Link></span>)}</p>}
      <h4>Requirements ({d.requirements.length})</h4>
      <ul className="per-req">{d.requirements.map((r) => (
        <li key={r.req_id}><ReqLink oppId={oppId} id={r.req_id} /> <StatusBadge status={FIT[r.status].tone} label={FIT[r.status].label} />{" "}
          <span className="muted">{r.why}</span></li>))}</ul>
      {d.missing.length > 0 && <p><strong>Not stated in the RFP:</strong> {d.missing.map((m) => m.needed_for).join("; ")}</p>}
      {(d.evidence?.passages.length ?? 0) > 0 && <><h4>From the supplied product documents</h4>
        <p className="muted">Keyword matches in the published datasheets and brochures tagged to the proposed product families
          ({d.evidence!.families.join(", ")}); supporting evidence to check, never the basis of the outcome.</p>
        <ul className="per-req">{d.evidence!.passages.map((e) => <li key={e.citation}><strong>{e.title}</strong>{" "}
          <span className="muted">({e.citation}; applies to {e.applies_to.join(", ")})</span><div className="muted">{e.text}</div></li>)}</ul></>}
      {d.checks.length > 0 && <><h4>Checks</h4>
        <ul className="per-req">{d.checks.map((k) => <li key={k.check}><StatusBadge status={CHECK_TONE[k.status]} label={CHECK_LABEL[k.status] ?? k.status} />{" "}
          <strong>{k.check}</strong> <span className="muted">{k.detail}</span></li>)}</ul></>}
    </div>
  );
}

export default function ComponentMatching({ oppId }: { oppId: string }) {
  const toast = useToast();
  const bm = isBidManager(useMe());
  const { data, error, reload } = useApi<ComponentsResponse>(`/api/bids/${oppId}/components`);
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState<number>();
  if (error) return <section className="card"><Alert kind="error" title={`Could not load ${TERMS.domain_alignment}.`}>{error}</Alert></section>;
  if (!data) return <section className="card"><Skeleton lines={3} /></section>;

  const runIt = () => {
    setBusy(true);
    post(`/api/bids/${oppId}/components`).then(() => { toast.success("Product configurator run recorded."); return reload(); },
      (e) => toast.error(errorMessage(e))).finally(() => setBusy(false));
  };
  const cs = data.components;
  const fits = { satisfied: 0, not_satisfied: 0, cannot_assess: 0 };
  cs.forEach((c) => c.detail.requirements.forEach((r) => { fits[r.status] += 1; }));
  const searched = cs.filter((c) => c.kind !== "other");
  const gaps = cs.filter((c) => ["no_match", "near_match", "insufficient_information"].includes(c.outcome));
  const sysFails = cs.flatMap((c) => c.kind === "system" ? c.detail.checks.filter((k) => k.status === "fail") : []);
  const assumptions = cs.flatMap((c) => c.detail.assumptions.map((a) => ({ ...a, where: c.name })));
  const pending = cs.flatMap((c) => c.detail.checks.filter((k) => k.status !== "pass").map((k) => ({ ...k, where: c.name })));
  const interpreted = cs.flatMap((c) => c.detail.requirements.filter((r) => r.interpreted.length > 0).map((r) => ({ ...r, where: c.name })));

  return (
    <section className="card" data-tour="asm-components">
      <div className="card-head"><h2>{TERMS.domain_alignment}: products for the requested components</h2>
        {data.run && <span className="muted">Run {data.run.id}, {formatDate(data.run.run_at, true)} · catalog import {data.run.catalog_import}</span>}</div>
      <p className="muted">{data.note}</p>
      <div className="row">
        <button className={data.run ? "secondary sm" : "sm"} disabled={!bm || busy} onClick={runIt} title={bm ? undefined : BID_MANAGER_ONLY}>
          {data.run ? "Run the product configurator again" : "Run the product configurator"}</button>
        {busy && <Busy label="Running…" />}
        {!bm && <span className="muted">{BID_MANAGER_ONLY}</span>}
      </div>
      {!data.run ? <p className="muted">Not run yet. The configurator groups the technical and compliance requirements by the component they ask for,
        searches the Flex Power Modules data for each DC/DC component and checks the installation-wide values.</p> : <>
        <h3>Coverage</h3>
        <p>{cs.length} requested components: {searched.length} checked by the configurator, {cs.length - searched.length} without a product table
          (assessed by the units&apos; engineers). {data.run.ungrouped.length} items name no component.</p>
        <p className="row">{(Object.keys(fits) as RequirementFit[]).map((k) => <StatusBadge key={k} status={FIT[k].tone} label={`${FIT[k].label} ${fits[k]}`} />)}</p>

        <div className="table-scroll"><table className="dense stack-sm">
          <thead><tr><th>Component</th><th>Checked by</th><th>Outcome</th><th>Why</th><th className="num">Items</th><th /></tr></thead>
          <tbody>{cs.map((c) => (<Fragment key={c.id}>
            <tr><td><strong>{c.name}</strong></td><td data-label="Checked by">{KIND[c.kind]}</td>
              <td data-label="Outcome"><OutcomeBadge c={c} labels={data.outcomes} /></td><td data-label="Why" className="muted">{c.reason}</td>
              <td className="num">{c.req_ids.length}</td>
              <td>{(c.kind !== "other" || (c.detail.evidence?.passages.length ?? 0) > 0) && <button className="secondary sm" onClick={() => setOpen(open === c.id ? undefined : c.id)}
                aria-expanded={open === c.id}>{open === c.id ? "Hide" : "Details"}</button>}</td></tr>
            {open === c.id && <tr><td colSpan={6}><Details oppId={oppId} c={c} /></td></tr>}
          </Fragment>))}</tbody>
        </table></div>

        <h3>Gaps</h3>
        {gaps.length === 0 && sysFails.length === 0 ? <p className="muted">No configurator gaps.</p> : <ul className="per-req">
          {gaps.map((c) => <li key={c.id}><strong>{c.name}</strong> <OutcomeBadge c={c} labels={data.outcomes} /> <span className="muted">{c.reason}</span></li>)}
          {sysFails.map((k) => <li key={k.check}><strong>Installation: {k.check}</strong> <span className="muted">{k.detail}</span></li>)}
        </ul>}

        <h3>Assumptions</h3>
        {assumptions.length === 0 ? <p className="muted">None.</p> : <details><summary>{assumptions.length} assumptions
          ({assumptions.filter((a) => a.basis.includes("not in the RFP")).length} configurator defaults not stated in the RFP)</summary>
          <ul className="per-req">{assumptions.map((a, i) => <li key={i}><strong>{a.item}</strong>: {a.value} <span className="muted">· {a.basis} ({a.where})</span></li>)}</ul>
        </details>}

        <h3>Pending engineering reviews</h3>
        <p className="muted">{fits.cannot_assess} requirement results cannot be assessed yet; the units&apos; designers / engineers confirm every outcome.</p>
        <details><summary>{pending.length} checks to close, {interpreted.length} interpreted values to confirm</summary>
          <ul className="per-req">
            {interpreted.map((r) => <li key={`${r.where}-${r.req_id}`}><ReqLink oppId={oppId} id={r.req_id} /> value interpreted from the text: {r.interpreted.join(", ")} <span className="muted">({r.where})</span></li>)}
            {pending.map((k, i) => <li key={i}><StatusBadge status={CHECK_TONE[k.status]} label={CHECK_LABEL[k.status] ?? k.status} /> <strong>{k.check}</strong>{" "}
              <span className="muted">{k.detail} ({k.where})</span></li>)}
          </ul></details>
      </>}
    </section>
  );
}
