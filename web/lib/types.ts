// Shapes returned by the FastAPI backend. Mirror of each module's controller.  Owner: Piyush.
// Add a field here when a controller starts returning it.

export type OfferingType = "CTO" | "SEMI_CUSTOM" | "ETO" | "NONE";
// The status vocabularies (kept as `string` on the shapes below so a new backend value never breaks a page);
// <StatusBadge> colours every one of them. OpportunityStatus is the workflow order of the stepper.
export type OpportunityStatus = "new" | "reading" | "review" | "frozen" | "go" | "no_go" | "dispatched" | "consolidating" | "submitted";
export type RequirementStatus = "proposed" | "approved" | "rejected" | "merged" | "split" | "duplicate";
export type MatchStatus = "proposed" | "accepted" | "rejected";
export type AssignmentStatus = "assigned" | "submitted" | "validated" | "returned" | "withdrawn";
export type Severity = "high" | "medium" | "low";
export interface Person { name: string; bu: string | null } // /api/people: who "Acting as" can be

export interface Opportunity { id: string; title: string; customer: string; customer_type: string; status: string; created_by: string }
export interface Doc { id: string; sha256: string; filename: string; role: string; status: string; page_count: number }
export interface Requirement {
  req_id: string; version: number; text: string; quote: string; category: string; section: string;
  page: number | null; line_start: number | null; line_end: number | null; bboxes: number[][];
  provenance: "EXTRACTED" | "UNANCHORED"; status: string; baseline: number | null; source: string;
  derived_from: string[]; created_by: string; kind: "item" | "group"; parent_id: string | null;
  document_id: string; // the RFP, or the change document a new version comes from (P-11)
}
export interface Baseline { number: number; count: number; frozen_by: string }
export interface Match {
  id: number; req_id: string; bu: string | null; product_id: string | null; offering_type: OfferingType;
  confidence: number; rationale: string; method: string; status: string;
  units: { bu: string; product_id: string; offering_type: Exclude<OfferingType, "NONE"> }[]; evidence?: unknown[]; decided_by: string | null;
}
export interface Assignment {
  id: number; opportunity_id: string; req_id: string; bu: string; owner: string; status: string;
  compliance: string | null; product_ref: string | null; response: string; responded_by: string | null;
  validated_by: string | null; validation_note: string;
}
export interface Unit { code: string; name: string; pillar: string; status: string; focus: string; product_manager: string; design_engineer: string }
export interface Product { id: string; bu: string; name: string; offering_type: OfferingType; description: string; bom: { item: string; qty: string }[] }
export interface Progress { [bu: string]: { total: number; submitted: number; validated: number } }
export interface Page { page: number; width: number; height: number; unreviewed: boolean }

export interface TraceRow {
  req: Requirement; match: Match | null; product: Product | null; unit: Unit | null;
  bom: { item: string; qty: string }[]; assignments: Assignment[];
  children: { req_id: string; text: string; source: string; document_id: string }[];
}
// A document shown in Traceability pane 1: the main RFP first, then change documents with requirements anchored in them (P-11).
export interface TraceDoc { id: string; filename: string; role: string; pages: Page[] }
export interface Trace { opp: Opportunity; doc: Doc | null; rows: TraceRow[]; pages: Page[]; progress: Progress; docs?: TraceDoc[] }
export interface RequirementHistory {
  req_id: string; quote: string; source: string; derived_from: string[];
  versions: { n: number; at: string; by: string; label: string; text: string; category: string; reason?: string }[];
  events: { at: string; by: string; action: string; details: Record<string, unknown> }[];
}

// Changes (P-11): an addendum, Q&A or change request compared with the frozen baseline.
export type ChangeKind = "added" | "modified" | "removed" | "unchanged" | "not_a_requirement";
export interface ChangeItem {
  id: number; n: number; page: number | null; line_start: number | null; line_end: number | null; bboxes: number[][]; source: string;
  quote: string; text: string; category: string; action: "add" | "modify" | "delete" | "clarify" | "info"; // what the document says it does
  proposed_kind: ChangeKind; proposed_target: string | null; rationale: string; confidence: number;
  kind: ChangeKind | null; target: string | null; status: "proposed" | "confirmed"; decided_by: string | null;
  target_text: string | null; target_source: string | null; candidates: { req_id: string; text: string; source: string }[];
}
export interface ChangeSet {
  id: number; opportunity_id: string; document_id: string; filename: string; status: "review" | "applied" | "discarded";
  created_by: string; created_at: string; applied_by: string | null; applied_at: string | null; baseline_from: number; baseline_to: number | null;
  counts: Record<ChangeKind, number>; confirmed: number; total: number; share: number; drastic: boolean;
  pages: { page: number; width: number; height: number }[];
  result: { baseline: number; added: string[]; modified: string[]; removed: string[]; returned: number; dispatched: number; note: string } | null;
  items: ChangeItem[];
}
export interface Changes { baseline: { number: number; count: number } | null; drastic_threshold: number; sets: ChangeSet[] }
