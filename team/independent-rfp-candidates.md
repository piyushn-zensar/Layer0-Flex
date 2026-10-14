# Independent validation RFP candidates (C-11, J-14)

Internal. Purpose: pick one public RFP from an issuer other than Syracuse Regional Airport Authority, to validate the extraction pipeline and the unit matching on an outside document (change C-11). Owner: Janvia (J-14). Feeds P-26 and A-23.
Researched and retrieved on 14 Oct 2026. Page counts and text layers were measured with PyMuPDF on the downloaded files (a page counts as "usable text" at more than 200 characters). The PDFs are not in the repo; they sit in the session scratchpad only. Everything marked "not verified" was not checked.

Search found about 14 candidates; three are written up. Rejected ones are listed at the end.

## 1. Logan City, Utah: 15 kV Switchgear for Substation 6

| Item | Value |
|---|---|
| Issuer | Logan City (Light & Power Department), Utah. A municipal power utility |
| Title / number | Request for Bids, "15kV Switchgear for Substation 6". No solicitation number found in the document |
| Issue date | Specification dated 8 Sep 2017; bids due 29 Sep 2017 (11:00) |
| Landing page | Not verified. The city purchasing pages (loganutah.org) returned HTTP 403 to my tools, and the search found no bid listing page |
| Direct PDF | https://cms9files.revize.com/loganut/departments/purchasing/Substation%206%20Switchgear%20Building.pdf (downloaded 14 Oct 2026, HTTP 200, no login) |
| Pages | 46 |
| Pages with text layer | 44 of 46. Low text: p. 42 (attachments divider) and p. 43 (placeholder "Attachment 6.1", one image) |
| Specification | Part 2 Technical Requirements pp. 14 to 26 (2.1 to 2.10 including relays and switches). General requirements pp. 5 to 13; proposal data sheets pp. 27 to 31; insurance and bonds pp. 32 to 33; contract pp. 34 to 41; attachments pp. 42 to 46 |
| Drawings | pp. 44 to 46: one-line diagram and building layout, vector drawings with some extractable text (not checked for usefulness). No scanned pages found |

Scope: a walk-in outdoor switchgear building with 15 kV metal-clad switchgear (IEEE C37.20.2, stored-energy vacuum-type breakers as described), feeder breakers rated 1200 A, short-circuit rating 18 kA rms (p. 23), 48 V DC control. Includes roof-top bushings for the owner's overhead bus, HVAC, lighting, relay and instrument panels, AC/DC panels, battery charger and RTU space, prewiring for IED communication, SCADA and relay wiring coordination (p. 13), and a protective relay (SEL-351S shown on the drawing). Quantity of units: not verified (the one-line shows about 5 numbered units).

Why public: a city's own bid document posted on the city's public purchasing site (revize-hosted city site) with no login for the PDF. I saw no terms of use on the PDF. Public-body bid under Utah procurement practice (not verified beyond that).

Flex units it would exercise: CROWN (metal-clad switchgear 15 kV, the e-house / enclosure, power control assembly), EP2 (relay and control panels, battery charger and AC/DC panels, which are fitted in the building), ANORD (secondary: LV auxiliary panels, power management). The bid desk (BID) for the commercial and insurance front matter.

Risks:
- Issued 2017, before the preferred 2019 cut-off. The bid is closed, so no live deadline and no live addenda.
- Landing page not verified; the PDF link works today but the page that lists it was not found.
- Addenda: none seen; whether any were issued is not verified.
- Layout: single column, numbered clauses (1.1, A., 1.), few tables. About 13 pages of general requirements, then a technical part, then forms and a 9-page contract. Similar in kind to Syracuse (commercial front matter, then specification), different issuer wording.
- Proposal data sheets (pp. 27 to 31) are fill-in forms with blanks, which can look like requirements to the reader.

## 2. City of Tacoma (Tacoma Power): 15 kV Padmount Switchgear

| Item | Value |
|---|---|
| Issuer | City of Tacoma, Tacoma Power / Transmission & Distribution (public utility) |
| Title / number | Request for Bids, "15kV Padmount Switchgear", Specification No. PT24-0117F |
| Issue date | Not stated on the document. Submittal deadline Tuesday 25 Jun 2024, 11:00 Pacific. Template revised 23 Jul 2023 |
| Landing page | Portal: https://www.tacomapurchasing.org (redirects to https://tacoma.gov/government/departments/finance/procurement-and-payables-division/purchasing/, HTTP 200). The page for PT24-0117F itself was not found (bid closed), so only the portal is verified |
| Direct PDF | https://cityoftacoma.org/UserFiles/Servers/Server_6/File/cms/Purchasing/FormalBids/PT24-0117F.pdf (downloaded 14 Oct 2026, HTTP 200, no login) |
| Pages | 55 |
| Pages with text layer | 52 of 55. Low text: pp. 10, 34, 52 (appendix divider pages; p. 52 has an image) |
| Specification | Section 2 Technical Specifications pp. 20 to 33 (ratings p. 21, approved models and configurations p. 22, structure, barriers, finish, operators, fuse and venting). Special provisions pp. 11 to 19; bid instructions pp. 2 to 9; price and data forms pp. 35 to 41; sample contract pp. 42 to 50; vault configuration drawings and PPI index pp. 51 to 55 |
| Drawings | pp. 22 and 53 to 55 contain images and diagrams (configuration tables, vault diagrams, danger label). Text layer present on those pages but the diagrams themselves are images |

Scope: a supply contract (framework, estimated 3-year quantities in the price sheets) for pad-mounted, 14.4 kV nominal / 17 kV maximum, 95 kV BIL switchgear: 600 A live-front switched ways and 200 A dead-front or live-front fused ways, fault-closing 22,400 A (switched) and 14,000 A (fused). Standard configurations, vault covers, labels and price-adjustment index. Quantities per item are in the price sheet (pp. 36 to 38); not extracted here.

Why public: a formal bid with a public bid opening (opened Tuesdays 11:15, in person and virtual), documents posted on the City's purchasing site. The PDF needs no login. The document says vendors may register for a Bid Holders List to receive addenda and Q&A.

Flex units it would exercise: weak fit. Pad-mounted utility load-break switchgear is not a Crown, Anord or EP2 product line as listed in the knowledge base (CROWN is 4.16 to 38 kV metal-clad; ANORD lists RMUs and packaged substations, which are the nearest). It would mostly test the matcher on "no good match", plus BID for commercial terms.

Risks:
- Addenda: the signature page has acknowledgement lines for addenda #1 to #5, so addenda probably existed; they are not in this PDF and were not found. Addenda may need the Bid Holders List registration (not verified).
- Short technical part with many tables (ratings, configurations, price sheets with blank columns). Sample contract (9 pages) includes federal-grant boilerplate text.
- The specific bid page and any award are not verified.

## 3. LUCELEC (St. Lucia Electricity Services): Troumassee 10 MWac Solar PV, 13.3 MW / 26.6 MWh BESS and 66/11 kV Substation

| Item | Value |
|---|---|
| Issuer | St. Lucia Electricity Services Limited (LUCELEC), the island's electric utility. Listed company, not a government agency; whether it counts as a "public body" under criterion 1 is a judgement for the team |
| Title / number | Request for Proposals, Instruction to Tenderers. No solicitation number found |
| Issue date | 10 Nov 2025 (date in the document URL path and the search summary of the LUCELEC page; not stated inside the PDF text I read) |
| Landing page | https://www.lucelec.com/content/rfp-troumassee-10mwac-solar-pv-133mw266mwh-bess-and-substation-project. Not verified: it returned HTTP 522 to curl on 14 Oct 2026. The search result described a download package (instructions, scope and technical specifications, drawings, forms) |
| Direct PDF | https://www.lucelec.com/sites/default/files/documents/rfp/20251110/Final_Instruction%20to%20Tenderers%2020251110.pdf (downloaded 14 Oct 2026, HTTP 200, no login) |
| Pages | 81 |
| Pages with text layer | 77 of 81. Low text: pp. 1, 2, 80, 81 (cover, blank, last pages) |
| Specification | Section 7 Scope of Work pp. 32 to 69, with the substation and 11 kV switchgear in 7.7 (pp. 36 to 37, 54 to 63), BESS and PCS pp. 41 to 52. Instructions and commercial pp. 6 to 31; forms and schedules pp. 74 to 79; technical schedules p. 80 (not populated in this file) |
| Drawings | Few: p. 32, 33 and 36 (map, grid schematic). Single line diagrams and the engineering design are in the separate download package, not in this PDF |

Scope: an EPC tender for a 10 MWac solar farm, a 13.3 MW / 26.6 MWh battery system and a 66/11 kV substation. Substation items named in the text: two 66/11 kV 15/22.5 MVA transformers, 66 kV outdoor open-type switchgear (two bays plus a tie-in bay), 11 kV indoor metal-clad switchgear for 4 feeders, 2 BESS connections and 2 solar connections, RMUs, a control building housing the 11 kV switchgear, EMS, control panels, UPS and auxiliary power, and a full protection and control system.

Why public: posted on the utility's own website with no login for this PDF. No terms of use seen. It is a state-linked utility tender but not a government body.

Flex units it would exercise: the widest spread. CROWN (11 kV metal-clad switchgear, control building / e-house), EP2 (protection and control, auxiliary AC/DC), ANORD (RMUs, LV auxiliary distribution, EMS and SCADA integration), possibly CLOUD or FPM only for the BESS side (not checked against the catalog), and the bid desk.

Risks:
- Scope is mainly solar and BESS EPC; electrical power equipment is a part, and the demo reads equipment requirements. Fewer product-level ratings than a switchgear specification.
- Outside the preferred regions (Caribbean; English, IEC-style units).
- The real technical specification, drawings and schedules are in other files in the package (zip, Excel). This PDF is only the instructions and scope. The landing page could not be opened.
- Table-heavy (evaluation tables, deliverable tables, price schedules); long prose paragraphs.
- Bid is open or recently closed; addenda may exist (not verified).

## Comparison

| | Logan Sub 6 | Tacoma PT24-0117F | LUCELEC Troumassee |
|---|---|---|---|
| Issuer type | City utility (US) | City utility (US) | Island utility (St. Lucia) |
| Date | 2017 | 2024 | Nov 2025 |
| Pages / text pages | 46 / 44 | 55 / 52 | 81 / 77 |
| Spec location | pp. 14 to 26 | pp. 20 to 33 | pp. 32 to 69 |
| Equipment | 15 kV metal-clad in e-house, relays | 15 kV padmount switches (framework) | 11 kV switchgear, 66 kV, control building, BESS |
| Flex units | CROWN, EP2, ANORD | Weak (ANORD RMU only) | CROWN, EP2, ANORD, others |
| Style vs Syracuse | Closest (commercial front, then spec, then drawings) | Different (bid forms, short spec) | Different (EPC tender) |
| Landing page verified | No | Portal only | No (HTTP 522) |
| Main risk | 2017, landing page not found | Poor Flex fit, addenda | Scope is mostly solar and BESS |

## Recommendation

Use **Logan City, Substation 6 15 kV Switchgear (candidate 1)**. It is the only one that is a metal-clad medium-voltage switchgear and building specification with relays and control equipment, so it exercises CROWN and EP2 and the bid desk in the same way Syracuse does, from a different issuer and a different format. It has a clean text layer (44 of 46 pages), is a manageable 46 pages, and its specification, data sheets, contract and drawings are all in the one PDF. The cost: it dates from 2017 (preferred is 2019 or later), and I could not find or open a landing page. If the client insists on 2019 or later, use LUCELEC (candidate 3) as the fallback, accepting a wider scope and a landing page that was down.

## Not used

- Radford University RFP R25-012 (2025, electrical early equipment package): the direct PDF URL returned an error page (HTTP 404 body) on 14 Oct 2026. Dropped.
- Wits University Parktown 11 kV switchgear (South Africa): the URL returned an error page. Dropped.
- Providence RI, Davey Lopes generator and main switchgear (RFP 48364, 2025, 173 pages): downloaded; the technical specification is a generator, plumbing and site package, with no switchgear specification section found. Dropped.
- University of Texas Health San Antonio RFB 745-15-9894 (15 kV metal-clad and power control room): 17 pages, 2015, specification only. Too short and old.
- City of Charlotte airport ITB AVIA-25-15 and University of Missouri CRMC project manual: both blocked from my machine (access denied / untrusted certificate). Not verified.
- Braintree Electric Light Department IFB 0520261: one page, specifications only on request. Dropped.
- University / master specifications (Houston, Texas State, Texas A&M), Chelan PUD and Burlington Electric specifications, UFGS: specifications or templates, not RFPs. Not used.
