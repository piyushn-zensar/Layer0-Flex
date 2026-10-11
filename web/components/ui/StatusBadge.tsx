// One status badge for every status string in the app, coloured by the five tones in globals.css.  Owner: Janvia.
//   <StatusBadge status="validated" />                      -> green "validated"
//   <StatusBadge status="submitted" kind="opp" />           -> green (a submitted final response is done; a submitted unit answer is blue)
//   <StatusBadge status="SEMI_CUSTOM" label="Semi-custom" /> -> amber, with its own text
// Unknown strings get the neutral tone. The text shown is the status with underscores as spaces unless `label` is given.

export type Tone = "ok" | "info" | "pending" | "bad" | "neutral";
export type BadgeKind = "status" | "opp" | "severity" | "offering" | "compliance";

const TONES: Record<string, Tone> = {
  // requirements, matches, change sets, knowledge items
  proposed: "pending", approved: "ok", accepted: "ok", rejected: "neutral", merged: "neutral", split: "neutral", duplicate: "neutral",
  review: "pending", applied: "ok", discarded: "neutral", queued: "pending", confirmed: "ok",
  // assignments
  assigned: "pending", submitted: "info", validated: "ok", returned: "bad", withdrawn: "neutral", blocked: "bad",
  // opportunities (see OPP), documents and business units
  new: "neutral", reading: "pending", frozen: "info", go: "info", no_go: "bad", dispatched: "info", consolidating: "info",
  uploaded: "pending", ingesting: "pending", ingested: "ok", failed: "bad", active: "ok",
  // severities, rule outcomes, consolidation states
  high: "bad", medium: "pending", low: "neutral", pass: "ok", warn: "pending", fail: "bad", "n/a": "neutral",
  answered: "ok", pending: "pending", over: "bad",
  // offering types
  CTO: "ok", SEMI_CUSTOM: "pending", ETO: "bad", NONE: "neutral",
  // compliance
  met: "ok", partial: "pending", partially_met: "pending", not_met: "bad", exception: "info", unknown: "neutral",
  // change kinds
  added: "ok", modified: "pending", removed: "bad", unchanged: "neutral", not_a_requirement: "neutral",
};
const OPP: Partial<Record<string, Tone>> = { submitted: "ok" }; // the final response went out
const OFFERING: Record<string, string> = { SEMI_CUSTOM: "Semi-custom" }; // shown as the trace legend names it; the value stays SEMI_CUSTOM

/** The offering type as shown on screen (CTO, Semi-custom, ETO). */
export const offeringLabel = (status: string | null | undefined) => OFFERING[String(status ?? "NONE")] ?? String(status ?? "NONE");

export function toneOf(status: string | null | undefined, kind: BadgeKind = "status"): Tone {
  const s = String(status ?? "").trim().replace(/[\s-]+/g, "_");
  return (kind === "opp" && OPP[s]) || TONES[s] || TONES[s.toLowerCase()] || "neutral";
}

export default function StatusBadge({ status, kind = "status", label, className = "", title }:
  { status: string | null | undefined; kind?: BadgeKind; label?: string; className?: string; title?: string }) {
  const text = label ?? (kind === "offering" ? offeringLabel(status) : String(status ?? "unknown").replace(/_/g, " "));
  return <span className={`badge t-${toneOf(status, kind)} ${className}`.trim()} title={title}>{text}</span>;
}
