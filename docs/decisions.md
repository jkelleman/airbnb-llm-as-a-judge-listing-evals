# Decision log

Each entry records a rubric or pipeline decision, what prompted it, and the evidence. Add to this as labeling and calibration surface new cases.

| # | Decision | Prompted by | Evidence |
|---|---|---|---|
| 1 | Split one 4-dimension judge into one judge per dimension, all pass/fail | Overlapping dimensions (clichés penalized under both "constraints" and "tone") and 1–3 scales with no anchors | See `rubric_v1_to_v2.md`; v1 vs. v2 agreement in `results/report.md` |
| 2 | Move length, punctuation, emoji, clichés, and internal terms to code | LLMs can't count characters reliably, and listed phrases are exact matches | Layer 1 catches every seeded format failure (tests) |
| 3 | Score faithfulness in code from claim-level verdicts | A holistic judge can "round up" a mostly true summary | `test_one_bad_claim_fails_faithfulness` |
| 4 | Omission is a salience failure, not a faithfulness failure | v1 treated "missing amenities" as a hallucination | Separates "said something false" from "left out something good" |
| 5 | Give the salience judge a fixed standout list | Without a reference, "most compelling features" is the judge's taste | Standouts derived from data in `evals/data.py` |
| 6 | Remove "property" from the internal-term regex | It flagged L14-a, "an apple orchard on the property," where it means land | First Layer 1 run; regression test added |
| 7 | Add an explicit distance-phrase table | "Steps away" vs. "a short walk" had no shared definition | Covered by the faithfulness prompt and perturbation tests |
| 8 | Run pairwise comparisons in both orders and count an inconsistent result as a tie | Position bias in pairwise judging | `test_pairwise_inconsistent_order_becomes_tie` |
| 9 | Use few-shot examples only from listings outside the evaluation set | Examples drawn from the golden set inflate measured agreement | All prompt examples use invented homes not in `data/` |
