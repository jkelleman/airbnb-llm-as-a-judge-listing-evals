<p align="center"><img src="assets/banner.png" alt="Listing highlights guests can trust: an LLM-as-a-judge stack for AI-written stay highlights on a booking platform. A fictional listing card shows a highlight flagged by the faithfulness judge for calling an 8-minute walk 'steps from' the cafes." width="100%"></p>

# Listing Highlight Evals: LLM-as-a-Judge for AI-Written Stay Highlights

**[Live demo](https://jkelleman.github.io/listing-highlight-evals/)**: run the Layer 1 checks on all 30 homes, or write your own highlight.


<p align="center">
  <a href="https://github.com/jkelleman/listing-highlight-evals/actions/workflows/tests.yml"><img alt="Tests" src="https://github.com/jkelleman/listing-highlight-evals/actions/workflows/tests.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-222222?logo=python&logoColor=white">
  <img alt="Dependencies: none" src="https://img.shields.io/badge/dependencies-none-222222">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-222222"></a>
  <br>
  <img alt="LLM-as-a-judge" src="https://img.shields.io/badge/LLM--as--a--judge-3%20virtual%20judges-FF385C">
  <img alt="Planted defects" src="https://img.shields.io/badge/stress%20tests-207%20planted%20defects-FF385C">
  <img alt="Human-calibrated" src="https://img.shields.io/badge/calibration-blind%20human%20labels-FF385C">
  <a href="CASE_STUDY.md"><img alt="Status: labeling in progress" src="https://img.shields.io/badge/status-labeling%20in%20progress-FFB400"></a>
</p>

**"Steps from the beach" is an 18-minute walk. "Private pool" is shared. Who catches that before a guest books?**

This repo is a content designer's answer: an LLM-as-a-judge stack for AI-written stay highlights on a booking platform. It turns style principles into enforceable rules, grades every claim with three single-purpose virtual judges, plants 207 known defects to see what slips through, and checks the judges against blind human labels.

The repo shows the full loop for making an LLM-as-judge trustworthy. Content principles become evaluable rules, rules go to the right layer (code, judge, or human), the judges are calibrated against blind human labels, and the judges themselves are stress-tested with injected defects.

> **Independent portfolio project.** Not affiliated with or endorsed by Airbnb. All 30 homes are invented; cities and landmarks are real places used for realism, and no data comes from Airbnb or any other booking platform.

**Start with [CASE_STUDY.md](CASE_STUDY.md)** for the story, the decisions, and where the project stands.

> **Status: in progress.** The stack is built and tested; blind human labeling is underway, and results will be published from real labeled runs.

## The stack

```mermaid
flowchart LR
    H[Highlight + home data] --> L1[Layer 1: code checks<br/>length · punctuation · emoji<br/>clichés · internal terms · frontage]
    L1 --> F[Faithfulness judge<br/>claim by claim]
    L1 --> S[Salience judge<br/>vs. standout list]
    L1 --> V[Voice judge<br/>content principles]
    F & S & V --> R[Pass / fail per dimension<br/>+ typed errors]
    R -. calibrated against .-> HL[Layer 3: blind human labels<br/>inter-rater α]
    P[Perturbation suite<br/>known defects] -. stress-tests .-> F & S & V
```

| Layer | What it decides | Why it decides it |
|---|---|---|
| 1. Code | Anything countable or exactly matchable | Free, exact, and never miscounts characters |
| 2. Virtual judges | Faithfulness, salience, voice — one judge each, binary, with typed errors | Each needs reading comprehension, and one dimension per judge keeps errors traceable |
| 3. Humans | Ground truth, rubric disputes, the final call on what "good" means | Judges are only as good as the labels they're calibrated to |

## What gets measured

- **Judge vs. human agreement** per dimension: % agreement, Cohen's κ with bootstrap 95% CI, and fail recall and precision. Fail is the positive class because missed failures are what reach guests.
- **Human vs. human agreement** (Krippendorff's α): the ceiling no judge can beat.
- **v1 vs. v2**: a typical monolithic rubric against the split stack, on the same labels.
- **Perturbation catch rates**: eight injected defect types, plus unchanged controls to measure false alarms.
- **Length bias, test-retest consistency, and pairwise position consistency.**
- **`results/disagreements.md`**: every item where the system and the labels disagree, with the judge's stated reasons. This is the file to read before changing any prompt.

## Quickstart

```bash
pip install -e ".[anthropic]"         # or .[openai]; no other dependencies
python data/build_seed.py             # (re)build the dataset
python -m pytest                      # offline; no API key needed

python -m evals all                   # offline smoke run with the mock judge (numbers are noise)

export JUDGE_PROVIDER=anthropic JUDGE_MODEL=<model id>
python -m evals label --rater yourname    # label blind first
python -m evals all --samples 3           # real run
```

To score model-written highlights instead of the hand-written seed set, set `GEN_PROVIDER` and `GEN_MODEL` to a **different model family** from the judge and run `python -m evals generate`. The judge command warns you if the families match.

## Repo map

```
data/        listings, candidate highlights, human labels (data/labels/<rater>.csv)
prompts/     one file per judge, versioned in a header comment; v1_monolithic is the baseline
evals/       checks.py (Layer 1) · judges.py · perturb.py · metrics.py · report.py · CLI
docs/        content principles · labeling guide · v1→v2 rationale · decision log
results/     report.md, metrics.json, disagreements.md (cache/ is gitignored)
tests/       20 offline tests, including scoring logic driven by scripted judge replies
```

## Further reading

- [Eval-driven development: lessons from evaluating GenAI at scale](https://airbnb.tech/ai-ml/eval-driven-development-lessons-from-evaluating-genai-at-scale/) — the three-layer framing and calibration targets this project follows
