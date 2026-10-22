// Runnable check for products.ts (J-19): node web/components/catalog/products.check.mjs (Node 22.18+ runs .ts files).
import assert from "node:assert/strict";
import { COLUMNS, DEFAULT_COLUMNS, NO_FILTERS, activeFilters, conflictCount, documentsOf, facets, filterRows, hasUnverifiedImage, imageOf, matchesQuery, paginate, parseColumns, range, sortRows } from "./products.ts";

const row = (o) => ({ key: o.part_number, part_number: "X", family_key: null, family: null, series: null, product_type: "power_module", status: "Active",
  vin_min_v: null, vin_max_v: null, vout_min_v: null, vout_max_v: null, power_w: null, current_a: null, efficiency_pct: null, interfaces: [],
  source: "spreadsheet", has_conflict: false, ...o });
const rows = [
  row({ part_number: "BMR3141011/001", series: "BMR314", family: "Power Modules", power_w: 800, efficiency_pct: 97.5, interfaces: ["PMBus"], vin_min_v: 38, vin_max_v: 60 }),
  row({ part_number: "BMR3161011/021", series: "BMR316", family: "Board-level DC-DC converter modules", family_key: "FPM-DCDC/BMR316", power_w: 1000, source: "both", interfaces: ["PMBus"] }),
  row({ part_number: "BMR3161011/031", series: "BMR316", family: "Board-level DC-DC converter modules", family_key: "FPM-DCDC/BMR316", power_w: 1000, source: "both" }),
  row({ part_number: "BMR4920311/011", series: "BMR492", family: "Board-level DC-DC converter modules", family_key: "FPM-DCDC/BMR492", power_w: 800, source: "both", has_conflict: true }),
  row({ part_number: "PKM4516ADPIHS", series: "PKM", family: "Industrial and railway isolated DC/DC converters", power_w: 150, has_conflict: true }),
  row({ part_number: "ROA1701", series: "BMR316", family: null, product_type: "evaluation_board", status: "Active" }),
  row({ part_number: "MDX", key: "ANORD-LVSB/MDX", family_key: "ANORD-LVSB/MDX", family: "LV switchboard", series: "MDX", product_type: "web_listing", status: "Published", source: "web" }),
];
const doc = (t, keys, applies = "family") => ({ file: t + ".pdf", title: t, doc_type: "brochure", family_keys: keys, part_numbers: [], applies, pages: {}, publisher: "p", note: "n" });
const img = (k, verified) => ({ file: `images/${k}.jpg`, family_key: k, part_numbers: [], source_file: "s.pdf", page: 1, kind: "photo", verified });
const idx = {
  family: new Map([["FPM-DCDC/BMR316", { documents: [doc("a", ["FPM-DCDC/BMR316"]), doc("b", ["FPM-DCDC/BMR316"], "general")], images: [img("u", false), img("v", true)] }],
    ["ANORD-LVSB/MDX", { documents: [doc("m", ["ANORD-LVSB/MDX"])], images: [img("w", false)] }], ["FPM-DCDC/BMR492", { documents: [], images: [] }]]),
  conflicts: new Map([["BMR4920311/011", [{ field: "vin_min_v", spreadsheet: 40, web: 36, web_url: null }, { field: "vin_max_v", spreadsheet: 60, web: 75, web_url: null }]]]),
};
const names = (rs) => rs.map((r) => r.part_number);

// documents, images and conflicts joined from the detail calls
assert.equal(documentsOf(rows[1], idx).length, 2);
assert.equal(documentsOf(rows[0], idx).length, 0, "a row with no family key has no documents");
assert.equal(documentsOf(rows[1], { family: new Map(), conflicts: new Map() }).length, 0, "not loaded yet reads as none, never throws");
assert.equal(imageOf(rows[1], idx).file, "images/v.jpg", "the verified image is shown, not the first one listed");
assert.equal(imageOf(rows[6], idx), null, "an unverified image is a placeholder");
assert.ok(hasUnverifiedImage(rows[6], idx) && !hasUnverifiedImage(rows[0], idx));
assert.equal(conflictCount(rows[3], idx), 2, "two fields in disagreement");
assert.equal(conflictCount(rows[4], idx), 1, "flagged but its detail has not loaded: counts at least 1");
assert.equal(conflictCount(rows[0], idx), 0, "zero state");

// search: words are ANDed, case-insensitive, over part number, series, family, catalog ID, type, status, interface
assert.deepEqual(names(rows.filter((r) => matchesQuery(r, "bmr316"))), ["BMR3161011/021", "BMR3161011/031", "ROA1701"]);
assert.deepEqual(names(rows.filter((r) => matchesQuery(r, "BMR316 /031"))), ["BMR3161011/031"]);
assert.deepEqual(names(rows.filter((r) => matchesQuery(r, "fpm-dcdc/bmr492"))), ["BMR4920311/011"], "the catalog ID of the family");
assert.deepEqual(names(rows.filter((r) => matchesQuery(r, "lv switchboard"))), ["MDX"], "family name");
assert.deepEqual(names(rows.filter((r) => matchesQuery(r, "evaluation board"))), ["ROA1701"], "type label");
assert.deepEqual(names(rows.filter((r) => matchesQuery(r, "pmbus"))), ["BMR3141011/001", "BMR3161011/021"]);
assert.equal(rows.filter((r) => matchesQuery(r, "nothing like this")).length, 0);
assert.equal(rows.filter((r) => matchesQuery(r, "   ")).length, rows.length, "blank search keeps every row");

// filters combine with AND; the has-... filters read the joined data
assert.deepEqual(names(filterRows(rows, { ...NO_FILTERS, source: "both" }, idx)), ["BMR3161011/021", "BMR3161011/031", "BMR4920311/011"]);
assert.deepEqual(names(filterRows(rows, { ...NO_FILTERS, source: "both", conflicts: "yes" }, idx)), ["BMR4920311/011"]);
assert.deepEqual(names(filterRows(rows, { ...NO_FILTERS, family: "Board-level DC-DC converter modules", q: "492" }, idx)), ["BMR4920311/011"]);
assert.deepEqual(names(filterRows(rows, { ...NO_FILTERS, documents: "yes" }, idx)), ["BMR3161011/021", "BMR3161011/031", "MDX"]);
assert.deepEqual(names(filterRows(rows, { ...NO_FILTERS, image: "yes" }, idx)), ["BMR3161011/021", "BMR3161011/031"], "an unverified image does not count as an image");
assert.equal(filterRows(rows, { ...NO_FILTERS, image: "no" }, idx).length, rows.length - 2);
assert.deepEqual(names(filterRows(rows, { ...NO_FILTERS, type: "web_listing", status: "Published" }, idx)), ["MDX"]);
assert.deepEqual(names(filterRows(rows, { ...NO_FILTERS, interface: "PMBus" }, idx)), ["BMR3141011/001", "BMR3161011/021"]);
assert.equal(filterRows(rows, { ...NO_FILTERS, source: "web", conflicts: "yes" }, idx).length, 0, "a combination with no row is an empty list, not an error");
assert.equal(activeFilters({ ...NO_FILTERS, q: "x", source: "web" }), 2);

// facets list only values that exist, with counts
const f = facets(rows);
assert.deepEqual(f.source, [{ value: "both", n: 3 }, { value: "spreadsheet", n: 3 }, { value: "web", n: 1 }]);
assert.deepEqual(f.status.map((x) => x.value), ["Active", "Published"]);
assert.deepEqual(f.interface, [{ value: "PMBus", n: 2 }]);
assert.equal(f.family.find((x) => x.value === null), undefined, "a row without a family adds no empty entry");
assert.equal(facets([]).family.length, 0);

// sorting: numeric, text, stable, unknown last both ways
assert.deepEqual(names(sortRows(rows, "power", "asc", idx)), ["PKM4516ADPIHS", "BMR3141011/001", "BMR4920311/011", "BMR3161011/021", "BMR3161011/031", "ROA1701", "MDX"], "equal 800 W keep their order");
assert.deepEqual(names(sortRows(rows, "power", "desc", idx)), ["BMR3161011/021", "BMR3161011/031", "BMR3141011/001", "BMR4920311/011", "PKM4516ADPIHS", "ROA1701", "MDX"], "ties keep their order; unknown stays last");
assert.deepEqual(names(sortRows(rows, "part", "asc", idx)).slice(0, 3), ["BMR3141011/001", "BMR3161011/021", "BMR3161011/031"]);
assert.deepEqual(names(sortRows(rows, "efficiency", "desc", idx)).slice(0, 1), ["BMR3141011/001"]);
assert.equal(sortRows(rows, "family", "asc", idx).at(-1).part_number, "ROA1701", "no family sorts last");
assert.deepEqual(names(sortRows(rows, "conflicts", "desc", idx)).slice(0, 2), ["BMR4920311/011", "PKM4516ADPIHS"]);
assert.deepEqual(names(sortRows(rows, "documents", "desc", idx)).slice(0, 3), ["BMR3161011/021", "BMR3161011/031", "MDX"]);
assert.deepEqual(names(sortRows(rows, "image", "desc", idx)).slice(0, 3), ["BMR3161011/021", "BMR3161011/031", "MDX"], "verified, then unverified, then none");
const again = sortRows(sortRows(rows, "series", "asc", idx), "series", "desc", idx);
assert.deepEqual(names(again.filter((r) => r.series === "BMR316")), ["BMR3161011/021", "BMR3161011/031", "ROA1701"], "equal series keep the order they came in, also descending");
const before = names(rows).join();
sortRows(rows, "power", "desc", idx); assert.equal(names(rows).join(), before, "the input array is not reordered");

// pages
const p = paginate([...Array(120).keys()], 3, 50);
assert.deepEqual([p.page, p.pages, p.from, p.to, p.total, p.items.length], [3, 3, 101, 120, 120, 20]);
assert.equal(paginate([...Array(120).keys()], 9, 50).page, 3, "a page past the end is the last page");
assert.equal(paginate([...Array(120).keys()], -4, 50).page, 1);
const empty = paginate([], 1, 50);
assert.deepEqual([empty.page, empty.pages, empty.from, empty.to, empty.items.length], [1, 1, 0, 0, 0]);
assert.equal(paginate([1, 2, 3], 1, 25).pages, 1);

// formatting and saved columns
assert.equal(range(38, 60), "38 – 60"); assert.equal(range(12, 12), "12"); assert.equal(range(null, 15), "15"); assert.equal(range(null, null), "—");
assert.deepEqual(parseColumns(null), DEFAULT_COLUMNS);
assert.deepEqual(parseColumns("not json"), DEFAULT_COLUMNS);
assert.deepEqual(parseColumns(JSON.stringify(["part", "power", "status"])), ["part", "status", "power"], "kept in table order");
assert.deepEqual(parseColumns(JSON.stringify(["power", "status"])), DEFAULT_COLUMNS, "without the part number the choice is refused");
assert.deepEqual(parseColumns(JSON.stringify(["part", "nonsense"])), DEFAULT_COLUMNS);
assert.ok(COLUMNS.find((c) => c.id === "part").locked && DEFAULT_COLUMNS.includes("part"));
console.log("products.check.mjs: all checks passed");
