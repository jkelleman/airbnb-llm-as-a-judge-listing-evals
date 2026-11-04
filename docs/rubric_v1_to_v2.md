# From v1 to v2: why the first rubric would mislead you

v1 (`prompts/v1_monolithic.md`) is the rubric most teams write first: one judge, four dimensions, 1–3 scales, "think step by step." It looks rigorous. Here is what goes wrong when you run it, and what v2 does instead.

| Problem in v1 | What it causes | v2 fix |
|---|---|---|
| Fidelity fails on "wrong, exaggerated, **or missing**" | Leaving something out is scored as a hallucination, so the fidelity metric means two things at once | Faithfulness covers only claims made. Omission belongs to salience |
| Clichés are penalized under both Constraints and Tone | Correlated scores. One defect costs two points, and error analysis can't tell which dimension moved | Each rule lives in exactly one place (see the enforcement table in `content_principles.md`) |
| The judge checks "under 500 characters" | LLMs count characters badly, so a deterministic rule gets a probabilistic answer | Length, punctuation, emoji, and listed clichés run in code (Layer 1) |
| Scales of 1–3 with adjectives such as "punchy" and "scannable" as anchors | Unanchored middle scores invite raters and judges to split between 2 and 3 on the same text, which caps agreement before the judge even runs | Binary pass/fail per dimension, with typed errors and worked examples |
| A holistic fidelity score | The judge can pass a summary that is "mostly true" | Claim-by-claim verdicts. Code fails the summary if any claim is unsupported or contradicted |
| "Most compelling features" with no reference | The judge's own taste becomes the metric | The salience judge gets a fixed standout list for each home |
| Few-shot examples absent, or taken from the test set | No anchor, or inflated agreement | Examples come only from invented homes outside the evaluation set |
| Claims that isolating constraints "neutralizes length bias" | Verbosity bias still operates on the other dimensions, unmeasured | The report measures it: the judge's pass rate on long vs. short known failures |
| Calibrate on a sample, with no metric named | "Looks aligned" | Inter-rater α first (the ceiling), then κ with confidence intervals, fail recall, perturbation catch rates, and false alarms on controls |
| One model, one pass | Hides run-to-run variance and position bias | Repeated samples (test-retest) and pairwise judging in both orders |

## What v2 keeps from v1

The instinct to separate dimensions was right. So were reasoning before scoring and a strict JSON output. v2 pushes those ideas further: **one judge per dimension, rules in exactly one place, and anything countable done in code.**

## How to compare them

```bash
python -m evals judge --version v1
python -m evals judge --version v2
python -m evals report
```

Section 3 of the report puts v1 and v2 side by side against the same labels. v1's scales are mapped to pass/fail for the comparison: salience passes only at density 3, and voice only at clarity 3. Treating only the top score as a pass is the closest match to v2's bar. The cut is one line in `evals/judges.py` if you want to test another.
