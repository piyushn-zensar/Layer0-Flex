// Shapes returned by the FastAPI backend. Mirror of each module's controller.  Owner: Piyush.
// Add a field here when a controller starts returning it.

export type OfferingType = "CTO" | "SEMI_CUSTOM" | "ETO" | "NONE";
// The status vocabularies (kept as `string` on the shapes below so a new backend value never breaks a page);
// <StatusBadge> colours every one of them. OpportunityStatus is the workflow order of the stepper.
export type OpportunityStatus = "new" | "reading" | "review" | "frozen" | "go" | "no_go" | "dispatched" | "consolidating" | "submitted";
export type RequirementStatus = "proposed" | "approved" | "rejected" | "merged" | "split" | "duplicate" | "exception" | "dismissed" | "removed";
export type MatchStatus = "proposed" | "accepted" | "rejected";
export type AssignmentStatus = "assigned" | "submitted" | "validated" | "returned" | "withdrawn";
export type Severity = "high" | "medium" | "low";
export interface Person { name: string; bu: string | null } // /api/people: the people with sign-in accounts

// Visible labels for stored values (technical-architecture §16.2). The API keeps the stored values; screens show these.
export const DOC_TYPES: Record<string, string> = { main: "Main RFP", addendum: "Addendum", qa: "Clarification / Q&A", change: "Change request", other: "Other" };
export const docTypeLabel = (role: string) => DOC_TYPES[role] ?? role;
// Roles (C-25, P-30): stored values stay, the unit roles read Unit manager and Unit designer / engineer.
export const ROLE_LABELS: Record<string, string> = { bid_manager: "Bid manager", product_manager: "Unit manager",
  design_engineer: "Unit designer / engineer", admin: "Administrator" };
export const roleLabel = (role: string) => ROLE_LABELS[role] ?? role;
export const COMPLIANCE_LABELS: Record<string, string> = { met: "Fully compliant", partial: "Partially compliant", not_met: "Non-compliant" };
export const complianceLabel = (c: string | null | undefined) => (c ? COMPLIANCE_LABELS[c] ?? c.replace(/_/g, " ") : "");
export const sourceLabel = (provenance: string) => (provenance === "EXTRACTED" ? "Source verified" : "Source not verified");

export interface Opportunity { id: string; title: string; customer: string; customer_type: string; status: string; created_by: string }
export interface Doc { id: string; sha256: string; filename: string; role: string; status: string; page_count: number }
export interface Requirement {
  req_id: string; version: number; text: string; quote: string; category: string; section: string;
  page: number | null; line_start: number | null; line_end: number | null; bboxes: number[][];
  provenance: "EXTRACTED" | "UNANCHORED"; status: string; baseline: number | null; source: string;
  derived_from: string[]; created_by: string; kind: "item" | "group"; parent_id: string | null;
  document_id: string; // the RFP, or the change document a new version comes from (P-11)
  origin?: Origin | null; // where this version came from (P-23); null = data from before origin was recorded
  spans?: Span[]; // every source span (P-24): a quote across a page break, or a lead-in and its item; [] = older data
}
export interface Span { document_id: string; page: number; line_start: number; line_end: number; bboxes: number[][] }
/** An exception's likely place (P-24): the reader's page when it holds most of the quote's words. Where to look, never a source. */
export interface LocationHint { page: number; line_start: number | null; line_end: number | null; share: number }
export type Origin = "extraction" | "correction" | "customer_change";
export const ORIGIN_LABELS: Record<string, string> = { extraction: "Extraction", correction: "Correction", customer_change: "Customer change" };
export const originLabel = (o: string | null | undefined) => (o ? ORIGIN_LABELS[o] ?? o.replace(/_/g, " ") : "");

// Extraction snapshots (P-23): E1 is the first read, never changed; E2... are later reads asked for with a reason.
// pages = pages_read + pages_failed + pages_skipped + pages_unreadable; candidates = admitted + exceptions + duplicates (P-24)
export type Coverage = Record<string, number>;
export const COVERAGE_LABELS: Record<string, string> = { pages: "pages", pages_read: "pages read", pages_failed: "pages the reader failed on",
  pages_skipped: "pages skipped (contents, blank)", pages_unreadable: "pages not readable", chunks: "reader calls", chunks_failed: "reader calls failed",
  candidates: "candidates", admitted: "in the register", exceptions: "exceptions", duplicates: "duplicates", groups: "groups", problems: "problems" };
export const coverageLabel = (k: string) => COVERAGE_LABELS[k] ?? k.replace(/_/g, " ");
export const snapshotName = (n: number) => `E${n}`;
export interface Snapshot { number: number; document_id: string; created_by: string; created_at: string; reason: string; model: string; pipeline_version: string; coverage: Coverage | null }
export interface SnapshotItem {
  req_id: string; text: string; quote: string; category: string; section: string; page: number | null; line_start: number | null; line_end: number | null;
  status: string; group: string | null; duplicate_of: string | null; spans?: Span[];
}
export interface SnapshotDetail extends Snapshot { items: SnapshotItem[] }
export interface CorrectionResult { baseline: number; added: string[]; modified: string[]; removed: string[]; affected: string[]; returned: number; dispatched: number; note: string }
// Requirement register (C-02/C-05): approved = in the register; exception / dismissed sit outside it.
export const STATUS_LABELS: Record<string, string> = { approved: "In register", rejected: "Excluded: not a requirement", exception: "Source not verified",
  dismissed: "Dismissed", duplicate: "Duplicate", proposed: "Proposed", split: "Split", merged: "Merged", removed: "Removed" };
export const statusLabel = (s: string) => STATUS_LABELS[s] ?? s.replace(/_/g, " ");
// An exception-queue row: the proposed text whose source could not be verified, with the reader's page hint and the reason.
export interface RequirementException extends Requirement { suggested_page: number | null; location_hint: LocationHint | null; reason: string }
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
export interface Unit { code: string; name: string; pillar: string; status: string; focus: string; product_manager: string; design_engineer: string; source_url?: string }
export interface Product { id: string; bu: string; name: string; offering_type: OfferingType; description: string; bom: { item: string; qty: string }[]; source_url?: string }
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
  versions: { n: number; at: string; by: string; label: string; origin?: Origin | null; text: string; category: string; reason?: string }[];
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
// GET /api/bids/{id}/activity (P-27): the bid's audit log, newest first; query entity, req_id, bu, person,
// before (= next_before of the previous page), limit. Read-only.
export interface ActivityEvent { id: number; at: string; actor: string; action: string; entity: string; entity_id: string; data: Record<string, unknown> }
export interface Activity { events: ActivityEvent[]; total: number; next_before: number | null; filters: { entities: string[]; people: string[]; units: string[] } }
// GET/POST /api/knowledge/sources (P-35): reference documents registered for retrieval, reviewed before they count as evidence.
export type SourceStatus = "draft" | "published" | "rejected" | "retired";
export interface KnowledgeSource {
  ks_id: string; collection: string; title: string; publisher: string; revision: string; scope: string; permissions: string; url: string;
  file_name: string; sha256: string; document_id: string; instance_id: string; id_source: "embedded" | "fingerprint"; version: number;
  status: SourceStatus; opportunity_id: string | null; pages: number; passages: number; annotated: number;
  registered_by: string; registered_at: string; reviewed_by: string | null; reviewed_at: string | null; review_note: string;
}
export interface SourceList {
  sources: KnowledgeSource[]; collections: Record<string, string>; reviewers: Record<string, string[]>; statuses: SourceStatus[];
}
export interface PassageAnnotation {
  topics: string[]; content_type: string; attributes: { name: string; value: string; unit: string; conditions: string }[];
  applicability: string; ambiguities: string[];
}
export interface SourcePassage {
  id: number; page: number; line_start: number; line_end: number; heading: string; table: string | null; text: string; annotations: PassageAnnotation | null;
}
export interface SourceDetail { source: KnowledgeSource; passages: SourcePassage[] }
// GET/POST /api/knowledge (P-36): reviewed examples. A person nominates one; the person who may review it approves or rejects.
export type KbExampleType = "requirement" | "preference" | "background" | "partial_compliance" | "insufficient_evidence" | "other";
export type KbStatus = "queued" | "approved" | "rejected" | "retired";
export interface KbItem {
  kb_id: string; kind: "requirement" | "response" | "decision" | "correction"; example_type: KbExampleType; source_ref: string;
  opportunity_id: string; bu: string; requirement: string; response: string; source: string; conditions: string; limits: string; note: string;
  illustrative: boolean; status: KbStatus; version: number; supersedes: string | null; sent_by: string; sent_at: string;
  reviewed_by: string | null; reviewed_at: string | null; review_note: string; may_review: boolean;
}
export interface KbList { items: KbItem[]; curator: string; example_types: KbExampleType[]; learned: number; index: string }
export const KB_EXAMPLE_TYPES: Record<KbExampleType, string> = {
  requirement: "Requirement", preference: "Preference", background: "Background information", partial_compliance: "Partial compliance",
  insufficient_evidence: "Insufficient evidence", other: "Other",
};
// GET /api/bids/{id}/schedule (P-33, C-24): unit completion dates, planned submission and the two bid-manager approvals. Dates are ISO "YYYY-MM-DD".
export interface ScheduleUnit { bu: string; estimated_completion: string | null; note: string; entered_by: string | null }
export interface Approval { id: number; kind: "schedule" | "compliance"; snapshot: unknown; note: string; approved_by: string; approved_at: string; current: boolean }
export interface ComplianceCounts { met: number; partial: number; not_met: number; open: number }
export interface Schedule {
  due_date: string | null; consolidation_days: number; units: ScheduleUnit[]; missing: string[];
  latest_unit_date: string | null; planned_submission: string | null; after_due: boolean; ready: boolean;
  compliance: Record<string, ComplianceCounts>;
  approvals: { schedule: Approval | null; compliance: Approval | null };
}
// GET /api/catalog/published (P-34): the catalog read from the official Flex product pages. Not compliance evidence; matching does not use it.
export interface PublishedProduct {
  key: string; bu: string | null; category: string; source_url: string; active: boolean; first_seen: string; last_seen: string;
  name: string; features: string[]; link: string; version: number; earlier_names: string[];
}
export interface PublishedRunSource { url: string; status: "ok" | "failed" | "skipped"; sha256: string; products: number; error: string }
export interface PublishedRun {
  id: number | string; started_at: string; finished_at: string | null; status: "running" | "ok" | "partial" | "failed"; trigger: string;
  sources: PublishedRunSource[]; added: number; changed: number; removed: number; error: string;
}
export interface PublishedCatalog { products: PublishedProduct[]; runs: PublishedRun[]; catalog_version: number | null }
// GET /api/catalog/published/versions?key=...
export interface PublishedVersion { version: number; name: string; features: string[]; link: string; refresh_id: number | string; valid_from: string; valid_to: string | null }
// GET /api/bids/{id}/assessment-score (P-38, C-23): executive-summary measures for the bid manager. "n" is null until an assessment run exists.
// A preliminary assessment, never a probability.
export interface AssessmentMeasure { label: string; n: number | null; of: number; req_ids?: string[]; explain: string; formula?: string }
export type AssessmentGapKind = "no_product_evidence" | "not_in_domain" | "exception" | "needs_owner" | "non_compliant";
export interface AssessmentScore {
  run: number | null; run_at: string | null; catalog_version: number | null; technical: number;
  measures: { domain_alignment: AssessmentMeasure; product_evidence: AssessmentMeasure; review_progress: AssessmentMeasure; preliminary_feasibility: AssessmentMeasure };
  gaps: { kind: AssessmentGapKind; label: string; req_ids: string[] }[];
  note: string;
}
