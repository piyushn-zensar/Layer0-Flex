// Words for the history of a unit answer (A-21) and for the bid's activity log (P-27), shared by the matrix's History panel and
// the Activity page (J-13, C-16).  Owner: Janvia.  Both read the append-only audit log; nothing here changes anything.
import { TERMS, complianceLabel, formatDate } from "@/lib/types";
import type { ActivityEvent } from "@/lib/types";

/** Audit timestamps carry no zone and are UTC; read them as UTC (the same rule as the Requirements and Changes pages). */
export const when = (t: string) => formatDate(t, true);

const pretty = (s: string) => { const t = s.replace(/_/g, " "); return t.charAt(0).toUpperCase() + t.slice(1); };

/** GET /api/assignments/{id}/history: one entry per event; before / after hold only what the event changed. */
export type HistoryEvent = { id: number; at: string; actor: string; action: string; note: string; before: Record<string, string | null>; after: Record<string, string | null> };

// What the person did, per audit entity and action ("<entity>.<action>"); anything not listed reads as the action itself.
const WHAT: Record<string, string> = {
  "assignment.assigned": "assigned the work", "assignment.reopened": "reopened the work", "assignment.responded": "submitted an answer",
  "assignment.validated": "validated the answer", "assignment.returned": "returned the answer", "assignment.withdrawn": "withdrew the work",
  "assignment.capability_gap": "recorded a capability gap",
  "match.proposed": "proposed a solution", "match.manual": "set the proposed solution", "match.accept": "accepted the match", "match.reject": "rejected the match",
  "match.routed": "routed the requirement to a unit",
  "requirement.proposed": "proposed the requirement", "requirement.approve": "approved the requirement", "requirement.reject": "rejected the requirement",
  "requirement.edit": "edited the requirement", "requirement.split": "split the requirement", "requirement.merged": "merged requirements",
  "requirement.merged_into": "merged it into another", "requirement.grouped": "grouped requirements", "requirement.ungrouped": "ungrouped the group",
  "requirement.revised": "revised the requirement", "requirement.removed": "removed the requirement", "requirement.duplicate_of": "marked it a duplicate",
  "requirement.resolved": "linked a requirement to its source", "requirement.dismissed": "dismissed a requirement that needed a source check", "requirement.discarded": "discarded the draft",
  "opportunity.created": "created the bid", "opportunity.status": "moved the bid to a new status",
  "participation.decided": "decided which units take part", "go_no_go.decided": "recorded the go / no-go decision",
  "baseline.frozen": "froze a version of the requirements", "baseline.follow_up_failed": "could not finish the follow-up of a frozen version",
  "change.read": "read a change document", "change.confirmed": "confirmed a change", "change.overridden": "overrode a change", "change.confirmed_all": "confirmed every change",
  "change.applied": "applied a change set", "change.discarded": "discarded a change set", "change.follow_up_failed": "could not finish the follow-up of a change set",
  "document.uploaded": "uploaded a document", "extraction_snapshot.read": "read the RFP",
  "comment.asked": "asked a question", "comment.commented": "added a comment", "comment.closed": "closed a question",
  "knowledge.sent": "nominated a reviewed example",
  "knowledge.nominated": "nominated a reviewed example",
};
export const what = (e: Pick<ActivityEvent, "entity" | "action">) => WHAT[`${e.entity}.${e.action}`] ?? pretty(e.action).toLowerCase();

const ENTITIES: Record<string, string> = {
  assignment: "Unit answer", match: TERMS.solution, requirement: "Requirement", opportunity: "Bid", participation: "Participation", go_no_go: "Go / no-go",
  baseline: "Frozen version", change: "Change set", document: "Document", extraction_snapshot: "RFP reading", comment: "Question or comment", knowledge: "Knowledge base",
};
export const entityLabel = (entity: string) => ENTITIES[entity] ?? pretty(entity);

/** What changed in an answer, as the History panel labels it. */
export const CHANGE_LABELS: Record<string, string> = { status: "State", compliance: "Compliance", product_ref: TERMS.solution, response: "How it is met", reason: "Reason",
  conditions: "Conditions", workaround: "Proposed change", next_steps: "Next steps" };
/** A value in a before / after line ("exception" is the retired compliance value). */
export const changeValue = (key: string, v: string | null) => (v == null || v === "" ? "—" : key === "compliance" ? (v === "exception" ? "Exception (earlier value)" : complianceLabel(v)) : key === "status" ? pretty(v) : v);

const text = (v: unknown): string => (v == null ? "" : typeof v === "string" ? v : typeof v === "number" || typeof v === "boolean" ? String(v) : JSON.stringify(v));
const clip = (s: string, n = 220) => (s.length > n ? `${s.slice(0, n).trimEnd()}…` : s);

/** One line on what an event recorded, from the keys the module stored with it (null when it stored nothing worth a line). */
export function detail(e: Pick<ActivityEvent, "entity" | "action" | "data">): string | null {
  const d = e.data;
  const parts: string[] = [];
  const add = (label: string, v: unknown) => { const t = text(v).trim(); if (t) parts.push(label ? `${label}: ${clip(t)}` : clip(t)); };
  switch (`${e.entity}.${e.action}`) {
    case "assignment.responded": add("Compliance", d.compliance ? complianceLabel(String(d.compliance)) : ""); add(TERMS.solution, d.product_ref); add("Answer", d.response); break;
    case "assignment.assigned": add("Owner", d.owner); break;
    case "assignment.withdrawn": add("Was", d.was); add("Because", d.reason); break;
    case "assignment.returned": add("Note", d.note); break;
    case "assignment.validated": add("Note", d.note); break;
    case "opportunity.status": add("", `${text(d.before)} → ${text(d.after)}`); break;
    case "opportunity.created": add("Title", d.title); break;
    case "baseline.frozen": add("Requirements", d.count); break;
    case "match.proposed": case "match.manual": case "match.routed":
      if (Array.isArray(d.units)) add("", (d.units as { bu?: string; product_id?: string }[]).map((u) => [u.bu, u.product_id].filter(Boolean).join(" · ")).filter(Boolean).join("; "));
      add("Method", d.method); break;
    case "participation.decided": case "go_no_go.decided": add("Units", Array.isArray(d.units) ? (d.units as string[]).join(", ") : d.units); add("Reason", d.rationale); break;
    case "document.uploaded": add("File", d.filename); add("Type", d.role); break;
    default: add("", d.note); add("Reason", d.reason); add("", d.text);
  }
  return parts.length ? parts.join(" · ") : null;
}
