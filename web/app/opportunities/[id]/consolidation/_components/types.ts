// Row shape of GET /api/bids/{id}/compliance-matrix (J-11), shared by the page and its panels.  Owner: Janvia.
import type { Part, Solution } from "@/lib/types";
export type Span = { document_id: string; page: number; line_start: number | null; line_end: number | null; bboxes: number[][] };
// One requirement and one unit's answer (unit is null for a requirement nobody holds). reason, conditions, workaround (shown as Proposed change) and
// next_steps stay null until A-18 stores them; the history count waits for A-21.
export type MatrixRow = {
  req_id: string; requirement: string; quote: string; category: string; state: string; source: string;
  document_id: string; page: number | null; line_start: number | null; line_end: number | null; spans: Span[];
  assignments: number; unit: string | null; unit_name: string; product: string | null;
  solution: Solution | null; // C-40: shown instead of product (the family id); null for the bid desk or no proposed solution
  offering_type: string | null;
  assignment_id: number | null; status: string | null; compliance: string | null; compliance_label: string; response: string;
  responded_by: string | null; validated_by: string | null; validation_note: string;
  reason: string | null; conditions: string | null; workaround: string | null; next_steps: string | null;
  parts?: Part[]; // a group's approved sub-requirements with their current (corrected) text; absent on older data
};
/** A row is one requirement and one unit: the key tells apart the units that hold the same requirement. */
export const rowKey = (r: MatrixRow) => `${r.req_id}:${r.assignment_id ?? "none"}`;
