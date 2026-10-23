# Layer 0: Product Selection from the Supplied Data (Iteration 5)

Status: **Expected (written direction)** for what was asked; **Proposed (inferred design)** for how the build answers it. Each change is marked **Built** (in the code on 23 Oct 2026 and checked), **Built, partly** (built with a stated limit) or **Later** (registered, not started). Product ratings shown by the system are read from supplied or published documents and are **unverified** until the owning unit confirms them. Unit answers in the demonstration are **illustrative** placeholders, not Flex positions. Written 23 Oct 2026.

## 1. Purpose, Who This Is For, and Sources

**Purpose.** This document registers the changes asked in the written direction of 22 Oct 2026: connect the RFP requirements to real product selection, using the supplied Flex Power Modules spreadsheet and the supplied configurator script, while keeping the catalog built from the official web pages. For each change it says what was asked, what the system does now and how it was checked. The numbering continues from [changes-iteration4.md](changes-iteration4.md) (C-35 to C-51), so this register starts at C-52.

**Who this is for.** The Zensar point of contact, who reviews the direction and presents the demonstration, and the Flex team who may see it.

**Sources.**
- The written direction from the Zensar point of contact received on 22 Oct 2026, and the follow-up decisions of 23 Oct 2026 recorded in section 7.
- The supplied files: the Flex Power Modules export (721 parts, exported 14 Oct 2026), the configurator script `rfp_configurator.py`, and 16 datasheets and brochures (Anord Mardix, Crown, JetCool, Flex), kept unchanged in `data/axiom_products/`.
- Official product pages and one datasheet fetched from anordmardix.com, jetcool.com and flex.com on 23 Oct 2026 (`data/axiom_products/web/`, each with its address, retrieval date and fingerprint).
- The synthetic RFP RC-1 "Grid to Chip", its synthetic Addendum No. 1 (section 5), and the public Syracuse switchgear RFP.

## 2. Summary

Product matching now has three layers, each saying what it is based on:

| Layer | What it gives | Based on | Covers |
|---|---|---|---|
| Proposed solution (earlier iterations) | A business unit and a product family per requirement, with a rationale | Model judgement over the catalog text, confirmed or corrected by the unit's designer / engineer | Every product requirement |
| Part-level search (new) | Part numbers, module count, pass or fail per stated value | The supplied configurator over the Power Modules spreadsheet (numeric filters) | Board-level DC/DC power modules only |
| Published-ratings search (new) | A product family or variant whose published ratings meet, miss or do not state each value | Rating tables read from the supplied brochures and the official pages | Busway, low-voltage switchgear and switchboards, power distribution units and remote power panels, coolant distribution units, MV switchgear (one-pager) |

Every result says which requirements it satisfies, fails or cannot assess yet, and why. Nothing is relaxed to produce a recommendation: a near match names the value it fails and is never shown as a match. A configurator result is never treated as proof that the RFP can be met; the go/no-go does not read it.

## 3. Change Register

| ID | Asked | Status |
|---|---|---|
| C-52 | Merge the spreadsheet into the catalog by exact part number; enrich, add, keep web data; variants and evaluation boards apart | Built |
| C-53 | Normalise and validate the spreadsheet (Series columns, numbers and units, empty = unknown) | Built |
| C-54 | Sources, import dates, conflicts with the web pages; no empty overwrite; repeat imports | Built |
| C-55 | RFP requirements into the configurator's input, with requirement text, reference and units | Built |
| C-56 | Group requirements by component; one search per component; system checks apart | Built, partly (grouping varies, section 6) |
| C-57 | Real product recommendations with specifications, catalog links, quantities, assumptions | Built |
| C-58 | Explain outcomes: satisfied, failed, cannot assess; match, near match, insufficient information, no match | Built |
| C-59 | Assessment Summary and Technical Requirement Matching screens | Built |
| C-60 | All-products table on the Product Catalog page | Built (table); product details page in progress |
| C-61 | Assumptions and engineering limits visible | Built |
| C-62 | Validate the whole flow on a power and a cloud RFP, with a match and a no-match or missing-information case | Built (section 5) |
| C-63 | Link datasheets and brochures to the right part or family | Built |
| C-64 | Index the supporting documents into retrieval with page references | Built |
| C-65 | Verified product images with sources; placeholder when uncertain | Built |
| C-66 | Catalog presentation | In progress |

## 4. Changes in Detail

### C-52 to C-54. The spreadsheet in the catalog
- **Now.** The 721 parts are one catalog entry each, keyed by part number. The two "Series" columns are split: the first (the same on every row, "Power Modules") is the product line; the second is the series code, or the ordering code of an evaluation board. The 27 evaluation and test boards are typed as boards and are never recommended as modules. No spreadsheet part number appears on the web pages, so a part whose series is a web catalog model (170 parts, for example BMR316) is linked to it as a variant; the other 551 are new catalog entries. Numbers keep the unit in the header (V, W, A, %, mm); an empty cell is unknown, never zero.
- **Sources and conflicts.** Each value records the date of the import that last set it. Where the web page states a range for the series, a part outside it is flagged for review with both values kept: 12 parts today (the BMR492 input range, PKM-D power, one BMR350 efficiency). A repeat import with the same file changes nothing, and an empty cell never overwrites an earlier value.
- **Checked.** Tests on a repeat import, an emptied cell, boards versus modules and a conflict.

### C-55 to C-58, C-61. The configurator in the system
- **The script.** The supplied script runs on the merged catalog with one structural change (it reads the catalog instead of the spreadsheet file). Its own self-test passes, and on the same question it returns the same parts as on the spreadsheet. Seven caveats found in the script are fixed in the system's copy, each confirmed first and listed in the file's header:

| Caveat in the supplied script | Now |
|---|---|
| "1,500 W" was read as 1 W | Thousands separators are read correctly |
| "UL 50" counted as UL 508A; a bare "IEC" counted as a certification found | A standard matches only itself or a more specific part of it |
| A distribution voltage without AC or DC ("800 V") failed | It is a point to review |
| In-rack coolant distribution units were sized from the whole IT load (751 units for 120 MW) | Sized per rack from the rack density |
| A fixed-ratio (unregulated) module passed a 12 V ±5% output over a 40 to 60 V input, although its output follows the input (10 to 15 V) | Its output across the stated input range must sit inside the required output; each such candidate shows that range |
| A blank part status could stop the search | A blank status counts as not active |
| Typical efficiency was compared as a guaranteed minimum | A note says it is the typical value |

- **From requirements to the script's input.** A model reads the values each component's requirements state and returns each number exactly as written, with the requirement it comes from. Code converts the units; a number not found in its requirement's text is dropped with the reason (this caught a model answer that had turned "15 kW" into 15,000 kW). Values the model had to interpret (for example "four blocks plus one catcher" read as N+1) are marked for confirmation. Inputs the script needs and the RFP does not state are listed.
- **Explanations.** Each component has an outcome and a reason; each requirement reads Satisfied, Not satisfied or Cannot assess yet, with the reason. Candidates carry their specifications, a link to the catalog, the number of modules, and flags (unverified values, conflicts with the web page). Assumptions are marked "stated in the RFP" or "configurator default, not in the RFP" (redundancy, design margin, maximum modules in parallel, module count). Open engineering checks are listed (fixed-ratio output, parallel operation, thermal derating, peak power conditions, certification applicability, unverified values), and the multiple-output limit is named as not checked by the configurator.

### C-56 and the published-ratings search
- **Grouping.** The technical and compliance requirements are grouped by the component they ask for. Each DC/DC component is searched part by part; the installation-wide values are checked once and shown apart. The installation checks use limits from the Axiom brochure and are shown as not applicable when an RFP states no IT load, rack density or cooling (the Syracuse switchgear RFP).
- **Rating tables.** For the components the spreadsheet does not cover, rating tables were read from the supplied brochures and the official pages: 138 items with 483 values for 21 product families. A value is kept only when the words it is quoted from are on the cited page and the number is in that quote; units are converted by code; 28 values were left out, each with the reason. A spot check of 15 random values found 11 right and 4 with the wrong rating name or family, so every value stays **unverified** until the owning unit confirms or rejects it (a unit manager or designer / engineer of that unit only).
- **Comparison.** Each stated value is compared only with the families proposed for its own requirements, by a rule per rating: at least (current, short-circuit rating, cooling capacity), within the published range (voltage, frequency, temperatures), at most (size, weight, approach temperature), or read from the text (IP rating, form of separation, standards). A short-circuit rating published for fewer seconds than asked does not count. A match needs at least two values compared; one rating does not select a product.

### C-59. Screens
- The measure and the new card read **Technical Requirement Matching**. On the Assessment Summary the card shows coverage, each component with its outcome and reason, the requirement-to-product comparison (the required value beside the first products' values), gaps, assumptions and pending engineering reviews, with the note "configurator result on the supplied product data, pending engineering review; not proof that the RFP can be met". Requirement Traceability shows the same result under each requirement.

### C-60, C-63 to C-66. Catalog, documents, retrieval, images
- The Product Catalog page lists every product (spreadsheet parts and web listings) in one table with search, filters, sorting and pages. The 16 supplied documents are tied to the families and pages they describe; the extracted images keep their source page and show a placeholder when the product is uncertain. The documents are product evidence in retrieval, published by the owning unit's manager; each component cites up to three passages from documents tagged to its proposed families, as supporting evidence that never decides an outcome.

## 5. The Demonstration (C-62)

**RC-1 "Grid to Chip" (cloud and 800 V), with Synthetic Addendum No. 1.** No supplied RFP asks for a board-level DC/DC conversion, the only product type the spreadsheet covers. As decided on 23 Oct 2026, a clearly labelled synthetic addendum to the synthetic RC-1 adds three Lot 4 requirements (L4.13 to L4.15): each compute tray converts the 54 VDC rack bus (40 to 60 VDC) to 12 VDC, at least 1,500 W, PMBus telemetry, typical efficiency of at least 97%, and at most 60 × 40 × 15 mm. It enters through the normal change-document flow. The configurator's results on RC-1 (illustrative):

| Component | Outcome | Why |
|---|---|---|
| 54 VDC to 12 VDC compute tray converters | **Match** | 26 parts meet every stated value; the best are BMR352 and BMR351 quarter-brick converters (for example BMR3522200/031: 40 to 60 V in, 8 to 13.2 V out, 2,000 W, PMBus, 97.9%, 58.4 × 36.8 × 14.5 mm) |
| 800 VDC to 54 VDC rack power shelves | **No match** | No board-level module takes an 800 V input; an upstream conversion stage is needed. BMR720 and BMR515 are listed on the unit's web pages without published ratings and are named for the unit to confirm; the input constraint is not relaxed |
| 800 VDC distribution system | **Near match** | The closest published busway variant fails the rated current asked (6,000 A against a published 800 to 1,250 A); shown for review, not as a match |
| Power blocks, cooling plant and CDUs, compute and storage | **Insufficient information** | The published ratings do not state some of the values asked (for example the coolant supply temperature) |
| System parameters | Installation checks | Module count and CDU sizing to review; rack density, distribution voltage, redundancy and coolant temperature pass against the brochure limits (unverified) |

**Hand check.** The matching parts were checked against the original spreadsheet rows, outside the system: the first six meet every stated value, and an independent count over the spreadsheet finds the same 26 parts as the configurator.

**Syracuse switchgear RFP (power).** 11 components; the installation checks are not applicable (no data-centre values), and the published-ratings search of the MV switchgear components gives **insufficient information**, because the only supplied Crown document is a one-page overview (the voltage class is met; frequency, impulse withstand and short-time ratings are not published).

## 6. Known Limits

- **Coverage.** Part-level selection exists only for board-level DC/DC modules. Busway, switchgear, CDUs and PDUs are compared with brochure ranges per family or variant, not with orderable configurations; most RFP values for them are not published and read "Cannot assess yet" until the unit confirms them.
- **Unverified ratings.** The rating tables are read by a model; about one value in four in a spot check had the wrong rating name or family. They need the units' review before any customer use.
- **Grouping varies.** The grouping of requirements into components is a model's proposal. When the register changes (for example after the addendum) the components can be drawn differently; on RC-1 the MV switchgear joined the power-block component after the addendum.
- **BMR720.** The 800 VDC module has no series page or datasheet on flex.com (checked 23 Oct 2026); only its hub-page line is published ("800 and ±400 VDC systems, peak power up to 15 kW").
- **Rack density on RC-1.** The RFP writes it as "rack TDP"; the configurator's reading can miss it, and it is then listed as a missing input rather than guessed.

## 7. Decisions Recorded (23 Oct 2026)

- The RC-1 rack shelf stays a **no match**; the input constraint is never relaxed; no BMR720 datasheet is expected.
- More product data is taken from the official pages, the supplied PDFs are turned into rating tables (unverified, for unit review), and the supplied script's caveats are fixed.
- The published-ratings search is built on those tables.
- A synthetic, clearly labelled addendum to RC-1 provides the demonstration's board-level DC/DC case.

## 8. Open Questions (Needs confirmation)

1. The meaning of the spreadsheet's two "Series" columns (read as product line and series or ordering code) and the linking of parts to the web catalog by series.
2. Whether the units can supply structured rating exports for busway, switchgear and CDUs like the Power Modules export; the brochure tables are a stand-in.
3. Who reviews the extracted rating tables in each unit, and whether a confirmed rating may be shown to a customer.
4. The Axiom limits the installation checks use (module capacity, rack density, voltages, coolant temperature) are from the brochure and not confirmed by Axiom.

## 9. What Does Not Change

- The proposed solution per requirement (unit and solution area) and the units' reviewed answers remain the basis of the compliance position and the go/no-go.
- The bid manager runs the configurator; it proposes, people decide. Earlier runs are kept.
- Numeric matching stays the basis of the part-level and published-ratings searches; document passages are supporting evidence only.
