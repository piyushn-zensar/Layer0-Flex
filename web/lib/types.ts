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
// C-43: stored values stay; deviation = a deviation from the requested specification (with a proposed change)
export const COMPLIANCE_LABELS: Record<string, string> = { met: "Compliant", partial: "Partially compliant", deviation: "Compliant with changes", not_met: "Non-compliant" };
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
export const ORIGIN_LABELS: Record<string, string> = { extraction: "Read from the RFP", correction: "Correction", customer_change: "Customer change" };
export const originLabel = (o: string | null | undefined) => (o ? ORIGIN_LABELS[o] ?? o.replace(/_/g, " ") : "");

// Extraction snapshots (P-23): E1 is the first read, never changed; E2... are later reads asked for with a reason.
// pages = pages_read + pages_failed + pages_skipped + pages_unreadable; candidates = admitted + exceptions + duplicates (P-24)
export type Coverage = Record<string, number>;
export const COVERAGE_LABELS: Record<string, string> = { pages: "pages", pages_read: "pages read", pages_failed: "pages the reader failed on",
  pages_skipped: "pages skipped (contents, blank)", pages_unreadable: "pages not readable", chunks: "reader calls", chunks_failed: "reader calls failed",
  candidates: "candidates", admitted: "in the register", exceptions: "need a source check", duplicates: "duplicates", groups: "groups", problems: "problems" };
export const coverageLabel = (k: string) => COVERAGE_LABELS[k] ?? k.replace(/_/g, " ");
export const snapshotName = (n: number) => `RFP reading ${n}`;
// What a read produced, in plain words: "207 statements read, grouped into 117 requirements (36 groups)."
export const readSummary = (c: Coverage, requirements?: number) => `${c.candidates ?? 0} statements read`
  + (requirements !== undefined ? `, grouped into ${requirements} requirements` : `, ${c.admitted ?? 0} in the register`)
  + (c.groups ? ` (${c.groups} groups)` : "") + (c.exceptions ? `; ${c.exceptions} need a source check` : "")
  + (c.duplicates ? `; ${c.duplicates} duplicates` : "") + ".";
export interface Snapshot { number: number; document_id: string; created_by: string; created_at: string; reason: string; model: string; pipeline_version: string; coverage: Coverage | null }
export interface SnapshotItem {
  req_id: string; text: string; quote: string; category: string; section: string; page: number | null; line_start: number | null; line_end: number | null;
  status: string; group: string | null; duplicate_of: string | null; spans?: Span[];
}
export interface SnapshotDetail extends Snapshot { items: SnapshotItem[] }
export interface CorrectionResult { baseline: number; added: string[]; modified: string[]; removed: string[]; affected: string[]; returned: number; dispatched: number; note: string }
// Requirement register (C-02/C-05): approved = in the register; exception / dismissed sit outside it.
export const STATUS_LABELS: Record<string, string> = { approved: "In register", rejected: "Excluded: not a requirement", exception: "Needs a source check",
  dismissed: "Dismissed", duplicate: "Duplicate", proposed: "Proposed", split: "Split", merged: "Merged", removed: "Removed",
  uploaded: "Uploaded", ingesting: "Reading", ingested: "Read" }; // the last three: an RFP document
export const statusLabel = (s: string) => STATUS_LABELS[s] ?? s.replace(/_/g, " ");
// Plain words for internal terms (C-44, P-42): screens, messages and the walkthrough use the right-hand word;
// stored values, API paths and data-tour ids keep the internal one. Backend messages repeat these words literally.
export const TERMS = {
  assessment: "Assessment Summary",              // the step, its page and panel (C-36)
  domain_alignment: "Technical requirement match",
  offering_type: "Type of offer",                // CTO / Semi-custom / ETO stay as the values
  exception: "Needs a source check",             // the exception queue and status "exception"
  baseline: "Frozen version",                    // "baseline 2" reads "frozen version 2"
  snapshot: "RFP reading",                       // extraction snapshot E1, E2...
  tier: "usual type of offer",                   // a unit's default tier
  solution: "Proposed solution",                 // a match / product mapping: unit · solution area (C-40)
  solution_area: "Solution area",                // the product family's name; its published models are examples
  solution_pending: "solution to be set by the unit's designer / engineer", // routed, no solution yet (P-44)
  capability_gap: "Capability gap: not offered", // a product requirement no unit offers, held by the bid desk as non-compliant
} as const;
// Bid status (opportunities.STATUSES): the badge shows these, tones still key on the stored value.
export const OPP_STATUS_LABELS: Record<string, string> = { new: "New", reading: "Reading the RFP", review: "In review",
  frozen: "Requirements frozen", go: "Go", no_go: "No-go", dispatched: "Sent to units", consolidating: "Go: response in preparation", submitted: "Submitted" };
export const oppStatusLabel = (s: string) => OPP_STATUS_LABELS[s] ?? s.replace(/_/g, " ");
/** The bid's one status badge where a go/no-go is recorded: never "Sent to units" beside "Go recorded". consolidating (every answer
 * validated after a go) and submitted already say it; before that the recorded decision is the status. */
export const bidStatus = (status: string, decision?: string | null): { status: string; label: string } =>
  decision === "no_go" ? { status: "no_go", label: "No-go recorded" }
    : decision === "go" && !["consolidating", "submitted"].includes(status) ? { status: "go", label: "Go recorded" }
    : { status, label: oppStatusLabel(status) };
// Requirement categories are stored lower case ("technical"); screens show them as labels ("Technical").
export const categoryLabel = (c: string) => (c ? c.charAt(0).toUpperCase() + c.slice(1).replace(/_/g, " ") : c);
/** An approved sub-requirement of a group with its current (corrected) text: matrix rows and My work items (parts). */
export interface Part { req_id: string; text: string }
// One date format on every screen (21 Oct review): "13 Nov 2026", with the time "13 Nov 2026, 19:01". Stored values stay ISO;
// a date alone is a calendar day, a timestamp without a zone is UTC (the API's).
export const formatDate = (t?: string | null, time = false) => {
  if (!t) return "";
  const d = new Date(/^\d{4}-\d{2}-\d{2}$/.test(t) ? `${t}T00:00:00` : /(Z|[+-]\d{2}:?\d{2})$/.test(t) ? t : `${t}Z`);
  return d.toLocaleString("en-GB", { day: "numeric", month: "short", year: "numeric", ...(time ? { hour: "2-digit", minute: "2-digit" } : {}) });
};
// An exception-queue row: the proposed text whose source could not be verified, with the reader's page hint and the reason.
export interface RequirementException extends Requirement { suggested_page: number | null; location_hint: LocationHint | null; reason: string }
export interface Baseline { number: number; count: number; frozen_by: string }
export interface Match {
  id: number; req_id: string; bu: string | null; product_id: string | null; offering_type: OfferingType;
  confidence: number; rationale: string; method: string; status: string;
  // product_id null: routed by the bid manager, the unit's designer / engineer sets the solution (P-44)
  units: { bu: string; product_id: string | null; offering_type: Exclude<OfferingType, "NONE"> }[]; evidence?: unknown[]; decided_by: string | null;
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

// C-40: matching proposes a solution (unit · solution area), not a product or part number; published models are examples only.
export interface Solution { unit: string; area: string | null; examples: string[] }
export const solutionLabel = (s: Solution) => (s.area ? `${s.unit} · ${s.area}` : s.unit);
export const examplesLabel = (s: Solution) => (s.examples.length ? `For example: ${s.examples.join(", ")}` : "");
export interface TraceRow {
  req: Requirement; match: Match | null; product: Product | null; unit: Unit | null;
  solutions: Solution[]; // C-40: one per unit on the match, main unit first (catalog.solution)
  bom: { item: string; qty: string }[]; assignments: Assignment[];
  children: { req_id: string; text: string; source: string; document_id: string }[];
  can_change: boolean; // P-44: the signed-in user may accept, reject or change this match (matching.may_change)
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
// GET /api/bids/{id}/schedule (P-33, C-24): unit estimates, delivery factors (P-47, C-42), planned submission and the bid manager's
// acceptance and compliance approval. Dates are ISO "YYYY-MM-DD".
export type FeasibilityFactor = "people" | "skills" | "capacity" | "materials" | "cost"; // = opportunities.FEASIBILITY_FACTORS
export type FeasibilityStatus = "ok" | "constraint";
export const FEASIBILITY_FACTOR_LABELS: Record<FeasibilityFactor, string> = {
  people: "People", skills: "Skills", capacity: "Manufacturing capacity", materials: "Materials", cost: "Cost" };
export const FEASIBILITY_STATUS_LABELS: Record<FeasibilityStatus, string> = { ok: "No constraint", constraint: "Constraint" };
export const FEASIBILITY_FACTORS = Object.keys(FEASIBILITY_FACTOR_LABELS) as FeasibilityFactor[];
export interface FeasibilityEntry { status: FeasibilityStatus; note: string; entered_by: string }
export interface ScheduleUnit {
  bu: string; estimated_completion: string | null; note: string; entered_by: string | null;
  factors: Partial<Record<FeasibilityFactor, FeasibilityEntry>>; constraints: FeasibilityFactor[];
}
export interface Approval { id: number; kind: "schedule" | "compliance"; snapshot: unknown; note: string; approved_by: string; approved_at: string; current: boolean }
export interface ComplianceCounts { met: number; partial: number; deviation: number; not_met: number; open: number }
export interface Schedule {
  due_date: string | null; consolidation_days: number; units: ScheduleUnit[]; missing: string[];
  missing_factors: Record<string, FeasibilityFactor[]>; constraints: { bu: string; factor: FeasibilityFactor; note: string }[];
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
// GET /api/bids/{id}/assessment-score (P-38, P-43): the Assessment Summary, three measures over technical requirements only
// (C-38, C-39); standards items listed beside, not counted. Counts, never a probability.
export interface AssessmentMeasure { label: string; n: number | null; of: number; req_ids?: string[]; explain: string; confirmed?: number; corrected?: number;
  other_solution?: number; not_compliant_answer?: number } // engineer_reviewed: corrected = other_solution + not_compliant_answer
export type AssessmentGapKind = "no_product_evidence" | "not_in_domain" | "exception" | "needs_owner" | "non_compliant";
export interface AssessmentScore {
  run: number | null; run_at: string | null; catalog_version: number | null; technical: number;
  measures: { technical_match: AssessmentMeasure; engineer_reviewed: AssessmentMeasure; review_progress: AssessmentMeasure };
  standards: { label: string; req_ids: string[] };
  gaps: { kind: AssessmentGapKind; label: string; req_ids: string[] }[];
  note: string;
}
// Product catalog (P-53a contract, team/PLAN.md 12.3): data/knowledge_base/power_modules.json merged with the web catalog.
// Units are in the field name (V, W, A, %, mm); null = unknown, never 0.
export type ProductType = "power_module" | "evaluation_board" | "web_listing";
export interface ProductOutput { n: number; v_min: number | null; v_nom: number | null; v_max: number | null; power_w: number | null; current_a: number | null }
export interface ProductConflict { field: string; spreadsheet: number; web: number; web_url: string | null }
export interface PowerModule {
  part_number: string; component_id: number | null; product_line: string | null; series: string | null; evaluates: string[];
  product_type: ProductType; family_key: string | null; status: string | null;
  application: string[]; interfaces: string[]; attributes: string[];
  isolation: string | null; isolation_v: number | null; regulation: string | null; mounting: string | null; package_type: string | null;
  footprint: string | null; paralleling: string | null; multi_output: boolean | null;
  vin_min_v: number | null; vin_max_v: number | null; vout_min_v: number | null; vout_max_v: number | null; vout_typ_v: number | null;
  power_w: number | null; power_peak_w: number | null; current_a: number | null; current_peak_a: number | null; efficiency_pct: number | null;
  length_mm: number | null; width_mm: number | null; height_mm: number | null; outputs: ProductOutput[];
  imported: Record<string, string>;            // field -> date of the import that last set it
  sheet: { file: string; row: number };        // spreadsheet file and row
  web: { id: string; source_url: string | null; specs: string; retrieved: string } | null;
  conflicts: ProductConflict[]; verified: boolean; in_last_import: boolean;
}
// GET /api/catalog/products?q=&type=&family=&status=&interface=&application=&sort=&dir=&page=&size=
export interface ProductRow {
  key: string;                                 // part number, or the catalog ID of a web-only listing
  part_number: string; family_key: string | null; family: string | null; series: string | null; product_type: ProductType; status: string | null;
  vin_min_v: number | null; vin_max_v: number | null; vout_min_v: number | null; vout_max_v: number | null;
  power_w: number | null; current_a: number | null; efficiency_pct: number | null; interfaces: string[];
  source: "spreadsheet" | "web" | "both"; has_conflict: boolean;
}
export interface ProductPage { total: number; page: number; size: number; items: ProductRow[] }
export interface ProductDocument { file: string; title: string; doc_type: string; family_keys: string[]; part_numbers: string[];
  applies: "part" | "family" | "general"; pages: Record<string, number[]>; publisher: string; note: string }
export interface ProductImage { file: string; family_key: string; part_numbers: string[]; source_file: string; page: number;
  kind: "photo" | "illustration"; verified: boolean }
// GET /api/catalog/product?part=<part number or catalog ID>: a spreadsheet part (PowerModule fields) or a web-only listing
// (key, name, specs, source_url, family_key; numbers absent), with the manifests joined.
export interface ProductDetail extends Partial<PowerModule> {
  key: string; name: string; family: string | null; source: ProductRow["source"];
  variants: ProductRow[];                      // a web series: its spreadsheet parts; a part: its evaluation boards
  documents: ProductDocument[]; images: ProductImage[];
}
// GET/POST /api/bids/{id}/components (P-56): the configurator's last run, one entry per requested component.
// An outcome is the configurator's result on the supplied product data, pending engineering review (never proof).
export type ComponentOutcome = "match" | "near_match" | "insufficient_information" | "no_match" | "system_checks" | "not_applicable" | "not_assessed";
export type RequirementFit = "satisfied" | "not_satisfied" | "cannot_assess";
export interface ComponentRequirement { req_id: string; text: string; document: string | null; page: number | null;
  status: RequirementFit; why: string; fields: string[]; interpreted: string[] }
export interface ComponentInput { req_ids: string[]; source: string; stated: string | string[]; unit: string | null; interpreted: boolean }
export interface ComponentCandidate {
  part_number: string; link: string; family_key: string | null; series: string | null; family: string | null;
  modules_for_load: number | null; modules_total: number | null; input_v: (number | null)[]; output_v: (number | null)[];
  power_w_per_module: number | null; peak_w_per_module: number | null; current_a_per_module: number | null; efficiency_pct: number | null;
  isolation: string | null; isolation_v: number | null; regulation: string | null; digital: string | null;
  package: (string | null)[]; size_mm: (number | null)[]; applications: string | null; review_flags: string[];
  verified: boolean; conflicts: ProductConflict[]; multi_output: boolean;
}
export interface ComponentAssumption { item: string; value: string; basis: string }
export interface ComponentCheck { check: string; status: "open" | "not_supported" | "pass" | "fail" | "review" | "unknown"; detail: string }
export interface ComponentDetail {
  requirements: ComponentRequirement[]; inputs: Record<string, ComponentInput>;
  missing: { scope: "board" | "system"; field: string; needed_for: string }[];
  assumptions: ComponentAssumption[]; checks: ComponentCheck[];
  candidates?: ComponentCandidate[]; near_matches?: ComponentCandidate[]; notes?: string[];
  unit_issues?: { field: string; message: string; req_ids: string[] }[];
  cdu_options?: Record<string, unknown>[]; certifications?: { requested: string; found_in: string | null; status: string }[];
  counts?: Record<"pass" | "fail" | "review" | "unknown", number>;
}
export interface ComponentMatch { id: number; run_id: number; opportunity_id: string; seq: number; name: string;
  kind: "dc_dc" | "system" | "other"; req_ids: string[]; outcome: ComponentOutcome; reason: string; detail: ComponentDetail }
export interface ComponentRun { id: number; opportunity_id: string; catalog_import: string; ungrouped: string[]; unassigned: string[]; run_by: string; run_at: string }
export interface ComponentsResponse { run: ComponentRun | null; components: ComponentMatch[]; outcomes: Record<ComponentOutcome, string>; note: string }
// GET /api/bids/{id}/requirements/{req_id}/components
export interface RequirementComponent { component: ComponentMatch; requirement: ComponentRequirement | null }
