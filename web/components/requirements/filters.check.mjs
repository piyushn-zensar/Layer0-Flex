// Runnable check for filters.ts (A-27): node web/components/requirements/filters.check.mjs (Node 22.18+ runs .ts files).
import assert from "node:assert/strict";
import { applyFilters, filtersUrl, isFiltered, readFilters } from "./filters.ts";

const row = (id, category, page, { offering = "ETO", bu = "CROWN", status, compliance, provenance = "EXTRACTED", origin, at } = {}) => ({
  req: { req_id: id, text: `text ${id}`, quote: "", category, page, provenance, origin, created_at: at },
  match: offering === "unmatched" ? null : { bu, offering_type: offering, units: bu ? [{ bu, product_id: "P", offering_type: offering }] : [] },
  assignments: status ? [{ bu, status, compliance }] : [], children: [],
});
const rows = [
  row("R1", "technical", 55, { status: "validated", compliance: "met", at: "2026-10-01T00:00:00Z" }),
  row("R2", "technical", 56, { offering: "CTO", bu: "EP2", status: "submitted", compliance: "partial", at: "2026-10-03T00:00:00Z" }),
  row("R3", "submission", 5, { offering: "NONE", bu: null, origin: "correction", at: "2026-10-02T00:00:00Z" }),
  row("R4", "schedule", 70, { offering: "unmatched", provenance: "UNANCHORED" }),
];
const ids = (f) => applyFilters(rows, f).map((r) => r.req.req_id);

assert.deepEqual(ids({}), ["R1", "R2", "R3", "R4"]);
assert.deepEqual(ids({ category: "technical" }), ["R1", "R2"]);
assert.deepEqual(ids({ offering: "NONE" }), ["R3"]);
assert.deepEqual(ids({ offering: "unmatched" }), ["R4"]);
assert.deepEqual(ids({ unit: "EP2" }), ["R2"]);
assert.deepEqual(ids({ response: "not_sent" }), ["R3", "R4"]);
assert.deepEqual(ids({ compliance: "partial" }), ["R2"]);
assert.deepEqual(ids({ source: "not_verified" }), ["R4"]);
assert.deepEqual(ids({ origin: "correction" }), ["R3"]);
assert.deepEqual(ids({ from: "55", to: "60" }), ["R1", "R2"]);
assert.deepEqual(ids({ q: "text r3" }), ["R3"]);
assert.deepEqual(ids({ sort: "compliance" }), ["R2", "R1", "R3", "R4"]); // weakest answer first, unanswered last, ties in RFP order
assert.deepEqual(ids({ sort: "changed" }), ["R2", "R3", "R1", "R4"]); // newest version first
assert.deepEqual(ids({ sort: "unit" }), ["R1", "R2", "R3", "R4"]);
assert.deepEqual(readFilters("?category=technical&offering=ETO&nope=1"), { category: "technical", offering: "ETO" });
assert.equal(filtersUrl("/opportunities/OPP-0001/trace", { category: "technical", q: "" }, "#REQ-1"), "/opportunities/OPP-0001/trace?category=technical#REQ-1");
assert.equal(isFiltered({ sort: "rfp" }), false);
assert.equal(isFiltered({ sort: "id" }) && isFiltered({ unit: "CROWN" }), true);
console.log("filters.ts: ok");
