# RAG evaluation report (P-39)

Run on 16 Oct 2026 with `scripts/eval_rag.py` against the draft set `data/golden/rag_eval.json` (not yet independently reviewed, so these results do not count yet).

| Ranking | Passed | Failed |
|---|---|---|
| Keyword only (offline, as on the demo laptop) | 10 of 13 | R-02, R-04, R-05 |
| Keyword and semantic (embedding service) | 11 of 13 | R-02, R-05 |

Reading:

- Semantic ranking fixes R-04 (a paraphrase of 'arc flash').
- R-02 and R-05 fail in both modes: the expected passages say '+/-400' and 'busbar', and other rack-power passages rank above them. They are the first cases to look at.
- U-01 first failed with semantic ranking (an unrelated question always found something, because cosine is never 0); a minimum semantic score (0.35, a placeholder) now applies.
- Model prompts always use the keyword ranking, so their frozen answers replay offline.

Detail of the run with the embedding service:

Evaluation set: data/golden/rag_eval.json, status **draft**, reviewed by: nobody yet.
Result: **11 of 13** checks passed. Ranking: keyword and semantic.

| Case | Measure | Result | Detail |
|---|---|---|---|
| R-01 | retrieval relevance | pass | 'SST input voltage 13.8 kV': top 5: KS-0003 v1, p. 9, lines 7-48, KS-0001 v1, p. 27, lines 34-45, KS-0002 v1, p. 30, lines 31-33, KS-0003 v1, p. 12, lines 19-22, KS-0001 v1, p. 33, lines 88-124 |
| R-02 | retrieval relevance | FAIL | 'sidecar power rack at +/-400 VDC': top 5: KS-0001 v1, p. 11, lines 2-13, KS-0001 v1, p. 9, lines 18-23, KS-0002 v1, p. 46, lines 11-18, KS-0001 v1, p. 15, lines 14-14, KS-0001 v1, p. 18, lines 22-28 |
| R-03 | retrieval relevance | pass | 'grounding of an LVDC distribution system': top 5: KS-0002 v1, p. 66, lines 13-18, KS-0002 v1, p. 66, lines 1-12, KS-0002 v1, p. 26, lines 1-10, KS-0002 v1, p. 67, lines 15-24, KS-0002 v1, p. 67, lines 1-14 |
| R-04 | retrieval relevance | pass | 'arc flash hazard in DC distribution': top 5: KS-0002 v1, p. 102, lines 1-10, KS-0002 v1, p. 98, lines 1-11, KS-0002 v1, p. 100, lines 22-30, KS-0002 v1, p. 140, lines 11-20, KS-0002 v1, p. 89, lines 20-28 |
| R-05 | retrieval relevance | FAIL | 'busbar between the power rack and the IT rack': top 5: KS-0001 v1, p. 10, lines 14-18, KS-0002 v1, p. 17, lines 1-5, KS-0002 v1, p. 15, lines 13-21, KS-0001 v1, p. 23, lines 26-38, KS-0001 v1, p. 19, lines 2-6 |
| R-06 | retrieval relevance | pass | 'solid state transformer converting medium voltage to 800 VDC': top 6: KS-0003 v1, p. 1, lines 1-7, KS-0003 v1, p. 7, lines 11-21, KS-0003 v1, p. 2, lines 1-1, KS-0003 v1, p. 5, lines 1-1, KS-0004 v1, p. 5, lines 10-17, KS-0003 v1, p. 8, lines 33-38 |
| C-01 | citation support | pass | 31 cited passages: 29 found in order on their cited page, 2 with every word on the page in another order (table cells) |
| N-01 | numerical values | pass | 'input voltage 13.8 kV': values ['13.8', '34.5', '57-63', '5', '10', '>0.99', '>0.98', '>0.95'] |
| N-02 | numerical values | pass | 'input voltage 34.5 kV': values ['13.8', '34.5', '57-63', '5', '10', '>0.99', '>0.98', '>0.95'] |
| U-01 | unknowns | pass | 'chocolate croissant pastry recipe': 0 hit(s) |
| I-01 | isolation between bids | pass | bid A sees its evidence: True; bid B sees it: False |
| E-01 | extraction coverage | pass | recall 0.982 (min 0.95), precision 0.547, 818 proposed |
| U-02 | unknowns | pass | 10 technical record(s), all marked 'no reviewed product evidence': True |

Not measured: interpretation accuracy: needs reviewed interpretations of requirements, and model-written conclusions are not produced yet (assessment records hold evidence, conclusion None)
