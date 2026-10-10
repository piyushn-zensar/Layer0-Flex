# Layer 0 Walkthrough

*Walkthrough as of 11 Oct 2026. It describes the demonstration build of that date, with demonstration data.*

*Note: the screenshots are being retaken. Where a screenshot shows older numbers (for example 13 requirements), the text gives the current figures.*

## 1. Overview

Layer 0 helps manage a bid opportunity from the customer's request for proposal (RFP) to a consolidated response. It reads the RFP into numbered requirements with exact sources, proposes a business unit and product for each, records participation and go/no-go decisions, and collects and consolidates each unit's response. Every response stays traceable to its requirement and to the RFP page it came from.

This walkthrough follows one example bid through the screens in the order of the work. Layer 0 is a proof of concept: the screens show demonstration data.

## 2. Demonstration Scenario

The example is **OPP-0001, Switchgear procurement (RFP 2023-20)** for **Syracuse Regional Airport Authority** (public sector). The RFP is a 101-page PDF. It is read into 814 line items. 21 of them repeat an earlier line item and are marked as duplicates, and related line items are grouped into 162 requirements with sub-requirements. The result is **348 requirements**, all approved and frozen as Baseline 1. The opportunity has the status "dispatched".

Three parties respond in the example. The screens show them by code:
- **CROWN** is Crown Technical Systems.
- **EP2** is Electrical Power Products (EP²).
- **BID** is the bid desk, which holds the bid manager's own requirements.

## 3. End-to-End Workflow

The screens follow this order of work. The Screen column gives the step in the bar under the opportunity title, or the page in the top bar. Completed steps are ticked.

| Step | What happens | Screen | Status |
|---|---|---|---|
| 1 | **Opportunity creation:** a title, customer and customer type are entered. | New opportunity | Current |
| 2 | **RFP document upload:** the RFP PDF is added to the opportunity. | RFP | Current |
| 3 | **Requirement extraction:** requirements are extracted from the document. | RFP | Current |
| 4 | **Requirement review:** each requirement is checked against its source, and a baseline is recorded. | Requirements | Current |
| 5 | **Source traceability:** a requirement can be followed to its place on the RFP page. | Traceability | Current |
| 6 | **Product and business-unit matching:** each requirement is proposed to a unit and product. | Traceability | Current |
| 7 | **Participation and go/no-go:** the bid manager records which units take part and whether to bid. | Bid decision | Current |
| 8 | **Work-package dispatch:** each participating unit receives its requirements (its work package). | Bid decision | Current |
| 9 | **Unit response collection:** units answer, and the bid manager validates the answers. | My work | Current |
| 10 | **Consolidation:** responses are brought together, and open items are shown. | Final response | Current |
| 11 | **Change handling:** later changes to the RFP, such as an addendum, are compared with the baseline and applied. | Changes | Current |

## 4. Opportunities

**Purpose.** The starting page. It lists the opportunities and where each one stands.

![Opportunities](images/01-opportunities.png)

*Figure 1. The Opportunities page.*

- The top bar offers **Opportunities**, **My work**, **Product catalog** and **Knowledge base**, a **New opportunity** button and the **Acting as** role selector.
- Each row shows the opportunity ID, title, customer, status and number of requirements (348 in the example).
- **Unit responses (validated / total)** shows, for each unit and the bid desk, how many responses are validated out of those assigned: Crown Technical Systems 1 of 96, Electrical Power Products 0 of 7 and the bid desk 0 of 245 (shown on screen as CROWN 1/96, EP2 0/7 and BID 0/245). A bar beside each count shows validated work (green) and work awaiting validation (blue). Each unit code opens that unit's work package under **My work**.
- **Open** enters the opportunity at its Traceability step.

## 5. New Opportunity

**Purpose.** Starts a new bid.

![New opportunity](images/02-new-opportunity.png)

*Figure 2. The New opportunity form.*

The form asks for a **title**, the **customer** and the **customer type**. The page notes that one opportunity is created per RFP, and that the RFP is uploaded on the next page.

## 6. RFP

**Purpose.** Holds the RFP and the other documents of the opportunity.

![RFP documents](images/03-rfp-documents.png)

*Figure 3. The RFP step, showing the RFP with status "ingested".*

- The customer and its sector are shown above the file list, with the sequence: upload the RFP, then have it broken into requirements.
- Each document shows its **file name**, **role** ("main" for the RFP), **page count** (101), **status** ("ingested") and a document fingerprint.
- A further PDF can be added by choosing a file and a role and selecting **Upload and read**. **Refresh status** updates the status column.
- Once requirement review has started, the page states that the RFP is not read again, and that missed items can be added on the Requirements page.

## 7. Requirements Review

**Purpose.** Lets the requirements be checked against the RFP before the work starts.

![Requirements](images/04-requirements.png)

*Figure 4. The Requirements step, listing the requirements with source and exact quotation.*

- A note states that Baseline 1 was frozen by the Bid Manager with 348 items. Later changes are handled as a difference from this baseline.
- Filters show the requirements by review state (To review, Unanchored, Approved, Rejected, Duplicates, Ungrouped / split / merged, All), each with a count, and a search box finds an ID or text.
- Each requirement has an **ID** (for example REQ-0001-0001), a **category** (technical, compliance, commercial, schedule, submission, legal or staffing), a **source** (page and lines of the RFP) and a **status**. All 348 requirements in the example are "approved".
- The requirement is stated in plain language, with the **exact quotation** from the RFP beneath it.
- A group (162 in the example) can be expanded to show its sub-requirements, each with its own source. A duplicate points to the line item it repeats.
- 32 requirements are "unanchored": their wording could not be located at an exact place in the RFP, so they are listed under their own filter for checking.

## 8. Requirement Traceability and Product Matching

This capability is presented through the Traceability step, which brings together the source document, extracted requirements, and proposed products and responses in three panels.

**Purpose.** Shows a requirement, its source and its proposed product and response in one view.

![Traceability](images/05-traceability.png)

*Figure 5. The Traceability step with REQ-0001-0001 selected in all three panels.*

| Panel | Content |
|---|---|
| **1. Original RFP** | The RFP page, with requirement text highlighted. Page controls move through the document. After a change document has been applied, the panel can also show its pages, and a requirement revised by it opens at its place in that document. |
| **2. Requirement breakdown** | ID, category, source, requirement and quotation. |
| **3. Product mapping and responses** | The proposed business unit and product, offering type, matching rationale, an expandable Bill of materials (for example, 5 lines), the proposal status with **Accept**, **Reject** and **Change** buttons, and the unit's response and status. |

**How it works**
- Selecting a requirement in any panel selects it in all three panels. The RFP opens on the page of the requirement, with its text highlighted more strongly than the others.
- Each panel scrolls on its own.
- The line above the panels shows each unit's validated responses (for example, 1 of 96 for Crown Technical Systems).
- **Match products** proposes a business unit and product for each requirement.
- A proposed match can be accepted, rejected or changed.
- A requirement that is not a product item is shown as belonging to the **Bid manager**.

**Traceability.** From one requirement the reader can see its exact RFP wording and location, the product proposed for it and the response it received. The same ID and source then appear in the unit's work package under My work and in the Final response.

**Offering types.** A legend under the page introduction explains the three types:

| Type | Meaning |
|---|---|
| CTO | Configure-to-order: catalog product with options (CPQ) |
| Semi-custom | Configured product plus workshop work for this customer |
| ETO | Engineered-to-order: designed for this requirement |

## 9. Bid Decision: Participation and Go/No-Go

**Purpose.** Records the decisions of the bid manager and releases the work.

![Bid decision](images/06-bid-decision.png)

*Figure 6. The Bid decision step.*

1. **Evidence.** The number of requirements by category (348 in total), the offering mix (ETO 96, CTO 5, Semi-custom 2, NONE 245, where NONE means requirements that are not product items) and the suggested units, each with a count (Crown Technical Systems 96, Electrical Power Products 7). The page states that the requirements must be frozen on the Requirements page before go or no-go is decided.
2. **Which business units take part?** The bid manager selects the participating units from the list, may enter a rationale, and selects **Record participation**. The screen shows who recorded the choice.
3. **Go / no-go.** The bid manager selects **Go** or **No-go**, with a rationale field. The screen shows the decision and who made it.

**Dispatch work packages to units** then sends each participating unit its requirements. The page notes that dispatch is repeated after changing matches or participation: new work is sent, and work that no longer fits is withdrawn.

## 10. Work Packages and Responses

**Purpose.** Gives each unit, and the bid desk, its own list of requirements to answer.

The demonstration allows selection of different participant roles using the **Acting as** selector. The list contains the Bid Manager and, for each business unit, a Product Manager and a Design Engineer. **My work** opens the work package of the selected role's unit.

![Acting as](images/07-acting-as.png)

*Figure 7. The Acting as selector.*

![My work](images/08-my-work.png)

*Figure 8. My work: the work package of the Bid desk (bid manager).*

- The example shows the work package of the **Bid desk (bid manager)**.
- Each line shows the requirement, its exact quotation and its source.
- The response has a compliance choice (the page explains: met, partly met, not met or an exception), a **Product / configuration** field and a **How it is met** field. **Submit** sends the response.
- The status of each line is shown as assigned, submitted or validated. Validated lines show the response and who validated it. The bid manager validates the responses.

## 11. Final Response

**Purpose.** Brings all responses together and shows what remains open.

![Final response](images/09-final-response.png)

*Figure 9. The Final response step.*

- The page explains that every requirement must be answered by its business unit and validated before the response is complete.
- A progress line shows the requirements answered out of the total (1 / 348 in the example) and how many still need an answer (347).
- Each requirement shows its ID and source, the responding unit, its answer, the product reference and the response status. The ID links to the requirement in Traceability.
- Each requirement has an overall state. In the example, requirements with a validated response are "answered", and those whose responses are assigned or submitted are "pending".
- **Download compliance matrix (Excel)** exports a workbook with two sheets: **Compliance matrix**, for the customer, with one row per requirement in RFP order (sub-requirements listed under their group, each with its RFP reference), the compliance in customer terms and only validated answers; and **Tracking**, for internal use, with one row per unit answer. **CSV** exports the tracking table as a CSV file. A requirement taken from a change document gives that document's name with its page and lines.
- **Response outline (draft)** opens a first draft of the response, one chapter per group of requirement categories plus an executive summary. It is written only from validated answers, every paragraph cites its requirements, and what is still open is listed. It can be downloaded as Markdown for the bid manager to edit.

## 12. Change Handling

**Purpose.** Handles addenda, question-and-answer documents and change requests that arrive after the baseline is frozen.

The numbered steps do not include this stage. It appears as a separate link, **Changes**, beside them in the bar under the opportunity title. The page shows the current baseline and its number of requirements.

1. **Read.** A change document (PDF) is uploaded with **Read the change document**. It is read in the same way as the RFP, and each statement is compared with the frozen baseline. Each is proposed as **added**, **modified**, **removed**, **unchanged** or **not a requirement**, with the baseline requirement it affects, the new wording, a rationale and its source (page and lines in the change document).
2. **Confirm.** A person checks each proposal against the change document's page and confirms or changes it. **Confirm all proposals** confirms the remaining ones.
3. **Apply.** The bid manager selects **Apply to requirements**. Nothing is edited in place: a modified requirement gets a new version anchored in the change document, a removed one gets a "removed" version, and an added one gets a new ID. Together they form the next baseline (Baseline 2), and the earlier wording stays readable in each requirement's history.
4. **Follow-up.** Answers to modified requirements are returned to their units with the new wording, work on removed requirements is withdrawn, and added requirements are matched and dispatched. Only the requirements that changed are matched again; all other matches and answers stay as they are.

A change set can also be discarded instead of applied. One change set is reviewed at a time. The demonstration includes an illustrative addendum, invented for the demonstration and marked as such on its first lines.

## 13. Summary

Layer 0 provides a structured workflow for turning an RFP into actionable requirements, assigning work to the appropriate business units, tracking responses and consolidating the results, while keeping every response traceable to the original source material.

This proof of concept demonstrates the workflow from document upload through consolidation, and the handling of later changes to the RFP against the frozen baseline.

## 14. Key Benefits

- Maintains end-to-end traceability from source requirements to responses.
- Supports structured review and approval of extracted requirements.
- Gives visibility of the work assigned to participating business units.
- Helps coordinate responses across multiple business units.
- Provides consolidated visibility into response progress and coverage.
- Supports compliance tracking throughout the bid process.
- Handles RFP changes against a frozen baseline, so only the requirements that changed are revisited.

## Appendix A: Product Catalog

**Purpose.** The reference list of business units and products, with their past responses, used for matching.

![Product catalog](images/10-product-catalog.png)

*Figure 10. The Product catalog of business units and products.*

- Each business unit is listed with its status, a short description, its product manager and design engineer roles, and its products, each with a code, a name and an offering type. A search box looks up the catalog.
- The catalog content is illustrative sample data and **needs confirmation** with each business unit.

## Appendix B: Knowledge Base

**Purpose.** Collects what the next bids should learn from.

- Requirements, validated answers and decision rationales can be sent to the knowledge base with **Send to knowledge base** from Traceability, the response outline and the bid decision.
- A curator approves or rejects each item sent (a rejection needs a note). Approved items are found by matching, by the response outline and by the catalog search.
