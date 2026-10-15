# Spreadsheet Tools Compared with the Built-in Compliance Matrix

Task J-16 (change C-21, priority 3). Prepared 15 October 2026. Scope: a short evaluation note. No integration design, no code, no hands-on vendor trial.
Vendor facts below are **vendor-stated** and come from each vendor's own pages (sources at the end). "Not verified" means the official pages reviewed do not say.

## Recommendation

- **Keep the Layer 0 Compliance Matrix as the system of record.**
- **Do not integrate Row Zero, Quadratic or Gigasheet in this iteration.**
- Today's matrices are hundreds of rows (312 and 167), not millions. They do not present a big-data spreadsheet problem.
- External tools may help later for optional, ad hoc work on approved exports: pivots, charts, joining other data, or very large exported datasets.
- Revisit only when a concrete scale or analysis need appears (see *Review triggers*).

## What Was Asked

Change C-21 ([Documents/changes.md](../Documents/changes.md)): the review meetings mentioned Row Zero, Quadratic and Gigasheet for large compliance matrices.

- Evaluate the three tools against the built-in Compliance Matrix (C-13).
- No product has been selected.
- Avoid building unnecessary custom spreadsheet features if an existing tool solves a real business need.
- This iteration needs only an evaluation note, not an integration.

## Current Matrix Scale

| Item | Rows or limit | Basis |
|---|---|---|
| Syracuse (OPP-0001) | **312** matrix rows (197 held by a unit) | Matrix endpoint on the demo seed, 15 Oct 2026 |
| Logan City (OPP-0002) | **167** matrix rows (not yet dispatched: one row per requirement) | Same |
| Excel worksheet | 1,048,576 rows | Excel's published limit |
| Row Zero | Free: "10s of millions of rows"; Pro and Business: "10M+ rows"; 5 GB per workbook. Enterprise: "1 billion+ rows". Home page: "2 billion+ rows" | Vendor-stated; the pages differ |
| Quadratic | Imports up to 100 MB CSV, 50 MB Excel or Parquet, 10 million cells overall (changelog, 23 Jul 2026). Home page: "multi-GB CSV and Parquet imports" | Vendor-stated; the pages differ |
| Gigasheet | Premium plan: "up to 25 million rows/sheet". Support article: "up to 1B+ rows and up to 5,000 columns" | Vendor-stated; the pages differ |

Syracuse uses about 0.03% of an Excel worksheet. A matrix would have to grow several thousand times before Excel itself ran out of rows, so the scale these tools are built for is far beyond anything Layer 0 holds today. If a review trigger is wanted, "tens of thousands of rows, or slow in-browser filtering" is a prompt to look again, **not** a product limit or a requirement.

## Built-in Layer 0 Compliance Matrix

What the repository provides today (J-11, J-13):

- A JSON endpoint, one row per requirement and unit answer.
- Search; filters for unit, compliance, state and category; an "Open only" filter; a "Needs an answer" summary grouped by reason.
- A row detail panel: requirement, RFP quote, unit, product, response, compliance (Fully, Partially, Non-compliant), and Reason, Conditions, Workaround and Next Steps.
- Evidence: a rendered image of the source PDF page with highlight boxes over the quoted wording, and links to Traceability.
- History: per-answer response history and a bid-level Activity log (append-only audit).
- Exports: CSV, and a deterministic Excel workbook (written by code, never by a model) with a customer sheet of validated answers and an internal Tracking sheet.
- Sign-in is required for every route. Answering is limited to the unit's people and validation to the bid manager (in the unit work and decision screens, not in the matrix view itself).

Current limitations:

- The matrix is read-only. Answers change through the unit and validation workflow.
- No spreadsheet formulas (exported cells are plain text), no pivots, no charts, no column sorting, no saved analytical views, no joins with external datasets.
- Filtering happens in the browser; the first 100 rows are drawn and the rest are added with "Show more".

## Row Zero

Vendor-stated (pricing, home, import and security pages):

- **Files and scale:** CSV, TSV, TXT, Parquet, JSONL, XLSX and GZ, up to 5 GB per file on Free, Pro and Business; scale figures above.
- **Analysis:** Excel-compatible formulas, native Python, dynamic pivot tables and charts, and an AI chat described as "fully auditable and editable".
- **Collaboration and history:** multi-user editing and sharing; version history from Pro.
- **Data connections:** two-way connections to Snowflake, Databricks, Redshift and others; refresh and write-back to a warehouse from Business.
- **Enterprise:** SSO and SCIM, workspaces, restricted data export, custom connectors, dedicated data plane; the security page adds region lock and customer-managed storage. Which plan includes each control is not clear.
- **Security claims:** SOC 2 Type II, HIPAA and GDPR; SSO through SAML 2.0 and OpenID Connect.
- **Pricing listed:** Free $0; Pro $12 and Business $20 per user per month; Enterprise custom. The pricing page also states that Row Zero has been acquired by Databricks.

## Quadratic

Vendor-stated (home, pricing, docs, self-hosting and changelog pages):

- **What it is:** a spreadsheet with code in cells. **Verified:** Python, SQL, JavaScript and formulas.
- **AI:** plain-English requests that write formulas, code and charts; agent integration over MCP. AI credits per plan (Pro $20, Business $40 a month; Personal "limited").
- **Data and files:** connections to Postgres, MySQL, Snowflake, BigQuery, MS SQL and others. Imports CSV, Excel, Parquet and PDF (AI extraction); exports Excel (paid plans), CSV, PDF and Parquet.
- **Collaboration and history:** sharing and a shared workspace on Pro; real-time co-editing is not described. Version history exists (changelog, July 2026).
- **Enterprise:** SSO and a self-hosting option. Docs: self-hosting is free for individuals, priced per user for business, needs a licence key, and officially supports AWS and Docker.
- **Security claims:** "SOC 2 and HIPAA certified" (SOC 2 type not stated).
- **Pricing listed (billed annually):** Free; Pro $18 and Business $36 per user per month; Enterprise custom.
- **Licence:** Quadratic's own blog carries a note that it is "closed-source" as of March 2026, and its public repository could not be opened. **Exact licence terms: not verified.**
- **Suitability:** technical analysis; good use assumes people who can read code.

## Gigasheet

Vendor-stated (pricing, security, support and product pages). Its home page now centres on healthcare price data, so general details come from support articles.

- **Files and scale:** CSV, TSV, Excel (XLSX, XLS and variants), Parquet, JSON, SQLite and more; scale figures above.
- **Analysis:** Groups work like pivot tables; Pivot Mode allows up to 1,000 row values and 100 column values. Filters and Functions (formulas) are documented. **Charts: not verified.**
- **AI:** a Sheet Assistant that groups, aggregates and filters and explains its steps.
- **Collaboration:** private sharing by email with Viewer or Editor roles, and public view links. Version history and data connections: not verified.
- **Security claims:** SOC 2 Type 2 "under continuous monitoring"; AES-256 at rest, TLS in transit; US servers; custom SSO on Enterprise. **The security page says it is "not yet fully GDPR compliant".**
- **Pricing listed (Premium):** 25 GB, $95 a month or $295 a year; 50 GB, $165 or $1,650; 75 GB, $250 or $2,500. Other plans and free-tier limits: not publicly listed on the pages reviewed.

## Comparison

| Aspect | Layer 0 matrix | Row Zero | Quadratic | Gigasheet |
|---|---|---|---|---|
| Primary purpose | Answer, validate and evidence one bid | Big-data spreadsheet | Spreadsheet with code and AI | Browser tool for very large tables |
| Relevant scale | 312 and 167 rows | 10M+ to 1B+ rows | 10M cells per import | 25M to 1B+ rows |
| CSV and Excel | Exports both | Imports XLSX and CSV; CSV export (Pro) | Imports and exports both | Imports both; CSV export documented |
| Formulas | None (plain-text cells) | Excel-compatible; Python | Formulas, Python, SQL, JavaScript | "Functions" documented |
| Pivoting and grouping | Filters only | Pivot tables | Not verified | Groups and Pivot Mode |
| Charts | None | Yes | Listed | Not verified |
| AI assistance | None in the matrix | AI chat | AI chat; credits per plan | Sheet Assistant |
| Warehouse or database | None | Yes (two-way) | Yes (many databases) | Not verified |
| Collaboration | Shared screen, read-only | Multi-user editing | Sharing; co-editing not described | Viewer and Editor sharing |
| Version history | Per-answer history (below) | Pro and up | Yes | Not verified |
| Source PDF preview | **Yes** | Not stated | PDF import only | Not stated |
| Highlighted evidence | **Yes** | Not stated | Not stated | Not stated |
| Requirement-to-response trace | **Yes** | Not stated | Not stated | Not stated |
| Unit assignment workflow | **Yes** | Not stated | Not stated | Not stated |
| Compliance reasoning fields | **Yes** (Reason, Conditions, Workaround, Next Steps) | Not stated | Not stated | Not stated |
| Response history | **Yes** | Not stated | Not stated | Not stated |
| Bid-level activity log | **Yes** | Not stated | Not stated | Not stated |
| Role-aware access | Unit and bid-manager roles | Generic (SSO, workspaces, Enterprise) | Generic (SSO, Enterprise) | Viewer and Editor roles |
| Security and controls | Runs in the bid team's deployment; sign-in required; append-only audit | SOC 2 Type II, HIPAA, GDPR; export restriction, region lock (vendor-stated) | SOC 2, HIPAA (vendor-stated); SSO, self-hosting on Enterprise | SOC 2 Type 2 (vendor-stated); not fully GDPR compliant |
| Adoption effort | None | Accounts, security review, training | Same, plus code literacy | Accounts, security review, training |
| Best fit for Layer 0 | System of record | Optional analysis of approved exports | Optional technical analysis | Optional analysis of very large exports |

"Not stated" means the vendor's reviewed pages do not mention it; it is not a statement that the capability is absent.

## Where External Tools May Help

Ad hoc exploration, pivoting and grouping (for example answers by unit or category), supplemental charts, joining other data such as a price book, very large datasets if one ever appears, and offline analysis for stakeholders. All of it should work from **controlled exports** of approved data; none replaces the system of record.

## Where the Built-in Matrix Is Stronger

- RFP-grounded evidence: the source page and highlighted wording, one click from any row.
- A bid-specific workflow: unit assignment, answering and bid-manager validation, with compliance reasoning recorded.
- Per-answer history and a bid-level Activity log from one audit record; role-aware actions.
- Deterministic exports, and one source of truth, so matrix, exports and history cannot drift apart.

## Risks and Trade-offs

- **Duplicate sources of truth,** manual synchronisation and export-and-import drift once people edit a copy.
- **Confidentiality and residency:** uploading customer RFP content needs approval first, and vendor claims (SOC 2, GDPR, residency) need the reports and terms, not web pages.
- **Lost evidence links and workflow context:** a copy has no source preview, highlights, assignment state or history.
- **Vendor dependency, licensing and cost:** for example Row Zero's acquisition and Quadratic's move to closed source (both vendor-stated); per-user plans.
- **Training:** more tools for bid and unit staff, and code literacy for Quadratic.

## Recommendation and Review Triggers

Recommended now:

- No vendor integration in this iteration.
- Keep the built-in matrix as the system of record.
- Keep offering CSV and Excel exports.
- Use external tools only for optional analysis of approved exports.
- Do not upload confidential RFP content to an external service without security approval.

Revisit if:

- Matrices grow well beyond the current hundreds of rows (a prompt to look again, for example tens of thousands of rows, not a product limit).
- Users consistently ask for pivots, charts or joins.
- In-browser filtering becomes slow.
- Stakeholders need shared spreadsheet editing.
- A governed enterprise analytics platform is chosen.

## Demo Note

- Demonstrate the built-in Compliance Matrix: the source page with highlighted wording, the answer history, the Activity log, and the Excel export.
- Mention that the exports can feed approved downstream analysis.
- Do not give a live demonstration of a third-party vendor.

## Sources and Open Questions

Date accessed for every source: **15 October 2026.** Third-party reviews were not used for any claim above.

Row Zero
- Pricing, https://www.rowzero.com/pricing
- Row Zero (home), https://www.rowzero.com
- Data Import, https://rowzero.com/docs/data-import
- Security, https://rowzero.com/security

Quadratic
- Pricing, https://www.quadratichq.com/pricing
- Quadratic: The AI Spreadsheet (home), https://www.quadratichq.com
- Quadratic Docs, https://docs.quadratichq.com
- Self-hosting: Getting started, https://docs.quadratichq.com/self-hosting/getting-started
- Changelog, https://www.quadratichq.com/changelog
- Blog, "Comparing the 5 Best Open Source Spreadsheets" (Quadratic's own note on closed source), https://www.quadratichq.com/blog/comparing-the-5-best-open-source-spreadsheets

Other
- Excel's 1,048,576-row limit is Microsoft's published figure; it was not re-checked in this review.

Gigasheet
- Pricing, https://www.gigasheet.com/pricing
- Gigasheet Premium, https://www.gigasheet.com/pricing/premium
- Gigasheet (home), https://www.gigasheet.com
- Security, https://www.gigasheet.com/security
- Supported File Types And Encoding, https://support.gigasheet.com/support/solutions/articles/69000625931-supported-file-types-and-encoding
- Pivot Tables On Data Too Big For Excel (Pivot Mode), https://support.gigasheet.com/support/solutions/articles/69000822766-pivot-mode
- Sharing Sheets and Folders, https://support.gigasheet.com/support/solutions/articles/69000833373-sharing-sheets-and-folders
- Gigasheet basics, https://support.gigasheet.com/support/solutions/articles/69000634103-gigasheet-basics
- AI Spreadsheet Assistant, https://www.gigasheet.com/popular-tools/ai-spreadsheet

**Verified from vendor pages:** the scale figures, file formats, features, plan prices and security claims listed above, each as a vendor statement. The vendors' own pages differ on scale (all three), on Quadratic's import limits and licence, and on Gigasheet's row limit.

**Not verified:**
- Quadratic: exact licence terms; real-time co-editing; plan limits on version history.
- Gigasheet: charts, version history, data connections, free-tier limits, and plans other than Premium.
- Row Zero: which plan includes each Enterprise control (export restriction, region lock, row-level security).

**Needs a hands-on trial or an enterprise security review:**
- How each tool opens a Layer 0 Excel export (two sheets, long text cells).
- How export restrictions and sharing controls behave.
- SOC 2 report scope and dates, data processing terms, retention, and data residency.
- The effect of vendor ownership and licence changes on terms.
