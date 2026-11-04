# Labeling guide

The human labels are the ground truth that every judge is calibrated against, so they need to be consistent before anything is automated. **If two raters disagree on an item, that's a rubric problem to fix first, not noise to average away.**

## Setup

```bash
python -m evals label --rater yourname
```

The tool shows each highlight with the home's structured data and its standouts, in an order shuffled per rater. It never shows the author's notes, and you can quit with `q` and resume later. Labels save to `data/labels/yourname.csv`.

Label every item on all three dimensions as **1 (pass)** or **0 (fail)**. Use the notes field for anything you hesitated on. Those notes are the raw material for rubric revisions.

## Faithfulness: is every claim true according to the data?

Pass only if you could defend every factual statement from the data shown.

- Fail on any unsupported or contradicted claim, even a minor one. The bar is binary.
- Extent and privacy words are claims. Examples: "every window" when the data says one, "private" when the data says shared, "heated" when the data says unheated.
- Apply the distance table in `content_principles.md`. An 18-minute walk is not "a short walk."
- Pure sentiment ("lovely") is not a claim. Ignore it here.

**Hard case — L05-b:** "a short walk from the Old Port" for an 18-minute walk. The rule says fail. If that feels too strict, write a note rather than overriding the rule. Disagreement here is a signal about whether the table is right.

## Salience: does it say what makes this home different?

Pass if it names at least two of the listed standouts (or all of them, if there are fewer than two) and doesn't open with a commodity or a room count.

- Judge only what it chose to say, not whether it's true or well written.
- A paraphrase counts: "knotty-pine walls" covers "original knotty-pine interior."

## Voice: does it read the way we want it to?

Pass if it has none of these: salesy phrasing, jargon, internal terms, fragments, keyword strings, or hedging.

- **Honest negatives pass.** "It's four flights up with no lift" is good writing.
- Format errors such as length, emoji, and `!` are checked by code, but label them anyway. A highlight with an emoji fails voice.

## Two quality checks on the labels themselves

1. **Inter-rater agreement.** At least two people should label the full set. The report computes Krippendorff's α per dimension. Below about 0.67 on a dimension, revise the guide and relabel before calibrating any judge on it.
2. **Intra-rater agreement.** If you're the only rater for now, relabel a random 20 items a week later under a second name (`--rater yourname-retest`). This doesn't replace a second rater, but it shows how stable your own judgment is, and it's honest about the limitation.

## Resolving disagreements

Discuss each split item, decide, and record the reason in `docs/decisions.md`. One person makes the final call on what "good" means. Disagreements left unresolved are dropped from the consensus labels, not guessed.
