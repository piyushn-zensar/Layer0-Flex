# Investigations: Word and Excel, past Flex responses (P-28)

Task P-28 (iteration 2, priority 3): C-18 asks whether Word and Excel documents can enter the same layout model; C-19 asks how past Flex RFP responses could support extraction. Owner: Piyush. Written 14 Oct 2026.

## 1. Word and Excel into the layout model (C-18): spike built

**Result.** Short enough to build, so it is built as a spike: a `.docx` or `.xlsx` file uploaded as any document type is read, anchored, highlighted and traced like a PDF. Other types (CAD, legacy `.doc` / `.xls`) are still recorded but not read.

**How it works** (`app/modules/ingestion/office.py`, about 100 lines, no new dependency):

- The stored file keeps its own bytes and SHA-256 (rule R6). On ingestion it is rendered once into a plain, deterministic PDF next to it, and the normal parser reads that PDF. Pages, line numbers, the frozen layout cache, anchoring, highlights and page images therefore work unchanged.
- **Word:** read from the document XML with the standard library. Paragraphs become lines; a manual line break starts a new line; each table row becomes one line with its cells joined by " | ". Each heading 1 (or title) starts a new page, so a page is a section.
- **Excel:** read with openpyxl (already used for the compliance matrix export), formulas as their last computed value. Each sheet starts a new page with the line "Sheet: <name>", then one line per non-empty row, cells joined by " | ".
- Long lines wrap; each wrapped piece is its own line, and the anchoring follows a quote across lines as for a PDF.
- Checked by `tests/test_p28_office.py`: an Excel data sheet and a two-section Word document are ingested (1 and 2 pages), their lines read as expected, a page image renders, and a quote from the data sheet ("Rated maximum voltage: 15 kV rms") enters the register as p. 1, line 3. A CAD file stays "unsupported".

**Limits found** (none blocks the spike; the first two matter most):

| Limit | Effect | Fix and rough effort |
|---|---|---|
| Sources cite the rendered page and line, not the original's terms | A requirement from Excel reads "p. 1, line 3", where a buyer expects "Sheet Data sheet, row 2"; Word has no fixed pages at all | Keep a source map (page and line to sheet and row, or section and paragraph) in the layout model and print it in the source; about 1 day |
| Word list numbering is not in the text | Automatic numbers such as "2.1.3" or "a." are lost (Word computes them from `numbering.xml`) | Compute them from the numbering definitions; about half a day |
| The viewer shows the rendered page | Plain text, not the original's look (fonts, colours, images) | Accept for the PoC; a faithful view needs an office-to-PDF converter such as LibreOffice on the server |
| Word headers, footers, footnotes, comments, text boxes and images are left out | Usually page furniture; footnotes can hold real obligations | Add footnotes and text boxes if real RFPs need them |
| Excel: merged cells, hidden rows and sheets are read as stored; a file saved by a tool that does not cache formula values shows empty cells | Rare in RFP data sheets; possible in large compliance matrices | Check on real files |
| Legacy `.doc` / `.xls` and macro files are not read | Recorded as unsupported, as before | LibreOffice conversion if needed |
| A new document needs the model service once | As for any new PDF: its reader answers are frozen on the first read | None (by design, rule R2) |

**Recommendation.** Keep the spike. Before relying on it, read two or three real Word or Excel RFP documents from the units and score the result. If Excel compliance matrices are the main use, build the sheet-and-row source map first; this also serves C-21 (spreadsheet tools for large compliance matrices).

## 2. Past Flex responses to support extraction (C-19): note

**Today.** `data/knowledge_base/past_responses.json` holds 8 *illustrative* past answers (one requirement and one answer each, per unit). They are used in three places: the fixed part of the matcher's prompt, the long-term search index (products, catalog models and past responses), and the related passages beside the response outline. Approved answers from finished bids can be added through the knowledge-base review queue.

**Where real past responses would help, in order of value:**

1. **Matching and routing (largest gain, lowest risk).** A past RFP line with the unit that answered it and how is direct evidence for the matcher. Added to the long-term index, the nearest past lines appear as evidence beside each match, and the routing of similar requirements can be checked against what the business actually did. This uses the existing retrieval; no prompt change is needed.
2. **Credibility and drafting.** Beside a requirement: "answered before in bid X by unit Y: compliant, with this wording". The response outline and the units' answers can start from validated past wording instead of a blank field.
3. **Extraction (the reader).** Past compliance matrices show how Flex itemises an RFP (granularity, what counts as one obligation). They can calibrate the reader, by examples in its prompt or by checks after it. This is the riskiest use: a prompt change regenerates all frozen answers and must be measured against the golden list first, so it comes last.

**What is needed from the business (Needs confirmation):**

- 5 to 10 past RFPs **with the response actually submitted** (the compliance matrix or the deviation list, in PDF, Word or Excel), across at least Crown Technical Systems, EP² and Anord Mardix; for each: issuer, date, the unit(s) that answered and, if it can be shared, the outcome.
- Permission to use them in the PoC, and whether customer names must be removed.
- One contact per unit to confirm which past answers are still valid (products and ratings change).

**How it would plug in** (no new mechanism):

1. Read each past RFP like a new one (the Word and Excel spike above covers the usual formats); freeze its layout and reader answers.
2. Link each line of the submitted compliance matrix to the requirement it answers (same anchoring), giving requirement, unit, compliance and wording.
3. Add those pairs to the long-term index as past responses (rule R7: data, not code). The matcher and the outline see them as evidence, and the knowledge-base queue keeps a person in the loop.
4. Measure: hold one past bid out, run the pipeline on it, and compare the matcher's units and the drafted answers with what was submitted.

**Not recommended now:** putting past answers into the reader's prompt before the measurement in step 4 exists, or using past responses without the unit confirming they are still valid.
