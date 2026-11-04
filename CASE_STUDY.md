# Teaching a judge what "good" means: calibrating virtual judges for AI listing highlights

*Content design × LLM evaluation · independent project*

> **Status: in progress.** The evaluation stack, content principles, labeling guide, and perturbation suite are built and tested. Blind human labeling is underway. Results will be added from real labeled runs only; this page doesn't report any number a run hasn't produced.

## The problem

Travel marketplaces now put model-written highlights under each home in search results, one or two sentences a guest skims while comparing dozens of places. When a highlight is wrong, a guest books on a false promise: "steps from the beach" for a 20-minute walk, "private pool" for a shared one. When it's generic ("a stunning hidden gem"), it wastes the one line the guest gives it.

Nobody can read every highlight, so quality depends on automated judges. A judge that hasn't been calibrated is worse than none. It produces confident numbers that don't track what guests experience.

**My question:** how do you turn a content designer's standards into judges that agree with careful human reviewers, and how do you prove it?

## What I built

A three-layer evaluation stack over 30 invented homes and 60 candidate highlights, written to cover the failures that matter. (Repo: this one.)

1. **Content principles → rules → enforcement.** I wrote seven principles for highlights, then mapped each one to a rule and to the cheapest layer that can enforce it reliably ([content_principles.md](docs/content_principles.md)). Counting goes to code, judgment goes to a judge, and definitions go to humans.
2. **One judge per dimension.** Faithfulness, salience, and voice each get a binary judge with typed errors and worked examples drawn from homes outside the test set.
3. **Blind human labels.** These include inter-rater agreement measured before any judge is trusted.
4. **A perturbation suite** that injects known defects into known-good highlights. That gives ground truth by construction, not opinion.

## Key decisions

**I started from a typical rubric and took it apart.** The first version (`v1`) was one judge scoring four overlapping dimensions on 1–3 scales. Clichés were penalized twice, "missing amenities" counted as hallucination, and the model was asked to count characters. [rubric_v1_to_v2.md](docs/rubric_v1_to_v2.md) walks through each failure.

**Distance became a defined vocabulary.** "Steps from" and "a short walk" are the promises guests remember. I gave them hard limits (2 and 10 minutes on foot) and put the table in both the guidelines and the judge prompt. Now raters and the judge are applying the same definition.

**Faithfulness is scored claim by claim, in code.** The judge lists each claim with a verdict and its evidence. Code fails the highlight if any claim is unsupported. A holistic judge can't "round up" a summary that's mostly true.

**Salience gets a reference, not a vibe.** "Surfaces the most compelling features" becomes "names at least two items from this home's standout list and doesn't lead with Wi-Fi."

**Honest negatives are protected.** "It's a third-floor walk-up" is good guest-facing writing. Judges tend to read negatives as flaws, so the rule is stated in the prompt, the examples, and the labeling guide.

**The first code run taught me something.** The internal-terms check flagged "an apple orchard on the property," where *property* means land. Context-dependent words moved from regex to the voice judge, and a regression test locks the change in ([decision log](docs/decisions.md)).

## Where it stands

**Done**
- 30 invented homes and 60 candidate highlights, each written to probe a specific failure: distance compression, shared spaces called private, unheated pools called heated, commodity checklists, puffery, and honest negatives that should pass.
- Seven content principles, each mapped to a rule and an enforcement layer.
- Layer 1 checks, three single-purpose judges, a pairwise judge that runs in both orders, and the v1 baseline kept for comparison.
- A perturbation suite: 207 cases across eight defect types, plus unchanged controls to measure false alarms.
- Metrics code for agreement, κ with bootstrap intervals, fail recall, Krippendorff's α, length bias, and test-retest consistency, with 20 offline tests.
- A blind labeling tool that shuffles items per rater and hides the author's notes.

**Next**
1. Finish blind labeling, ideally with a second rater, and report inter-rater α as the ceiling.
2. Run v1 and v2 judges against those labels and report agreement, κ, and fail recall for each dimension.
3. Report perturbation catch rates and false alarms on controls.
4. Read every disagreement, revise one rule, rerun, and report the before-and-after.

**What I'm watching for.** I expect the borderline distance cases to split raters before they split the judge. L05-b, "a short walk" for an 18-minute walk, is the test of whether the distance table matches how people read. I also expect the voice judge to flag honest negatives unless the examples protect them, which is why the rule appears in the prompt, the examples, and the labeling guide.

## What I'd do in production

- Sample live highlights daily, run Layer 1 and the judges, and route flagged items to a weekly review. Every new failure pattern becomes a new rule, example, or perturbation.
- Recalibrate whenever the generator model or prompt changes, and gate releases on fail recall for faithfulness, not on average scores.
- Derive the standout list from guest behavior (what people filter on and click) instead of structured fields.
- Grow the golden set with real generator outputs and adversarial cases, keeping the few-shot examples strictly separate from it.

## Limitations

60 items give wide confidence intervals; the report shows them rather than hiding them. The seed highlights are hand-written to cover failure modes, so they're harder than a typical model's output distribution. `python -m evals generate` adds real model outputs to close that gap.
