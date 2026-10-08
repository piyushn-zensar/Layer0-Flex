// Shapes returned by the FastAPI backend. Mirror of each module's controller.  Owner: Piyush.
// Add a field here when a controller starts returning it.

export type OfferingType = "CTO" | "SEMI_CUSTOM" | "ETO" | "NONE";

export interface Opportunity { id: string; title: string; customer: string; customer_type: string; status: string; created_by: string }
export interface Doc { id: string; filename: string; role: string; status: string; page_count: number }
export interface Requirement {
  req_id: string; version: number; text: string; quote: string; category: string; section: string;
  page: number | null; line_start: number | null; line_end: number | null; bboxes: number[][];
  provenance: "EXTRACTED" | "UNANCHORED"; status: string; baseline: number | null; source: string;
}
export interface Baseline { number: number; count: number; frozen_by: string }
export interface Match {
  id: number; req_id: string; bu: string | null; product_id: string | null; offering_type: OfferingType;
  confidence: number; rationale: string; method: string; status: string;
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
}
export interface Trace { opp: Opportunity; doc: Doc | null; rows: TraceRow[]; pages: Page[]; progress: Progress }
