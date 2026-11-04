# Content principles for listing highlights

A **listing highlight** is one or two sentences, written by a model, that appear under a home in search results. A guest skims dozens of them in a minute. The highlight has one job: help the guest decide whether to open this home.

This page holds the principles, the rules they turn into, and which layer of the eval stack enforces each rule. The point of writing it this way is that **every principle a writer would apply by taste is turned into something a person, a regex, or a judge can apply the same way twice.**

## The principles

**1. True before interesting.** A guest who books on a false promise has a worse trip than one who never clicked. Every fact must come from the home's data. Words about extent ("sweeping", "every room", "sprawling") and about privacy ("private", "its own") are facts, not flavor.

**2. Distinct before complete.** Nearly every home has Wi-Fi and a kitchen, so saying so wastes the guest's attention. Lead with what only this home has: its design, its standout features, its view.

**3. Distance is a promise.** "Steps from the beach" is the claim guests remember and complain about. Say the time when you can, and use relative phrases only within these limits:

| Phrase | Walk of at most |
|---|---|
| steps from, next to, right on | 2 min |
| around the corner, a few blocks | 5 min |
| a short walk | 10 min |
| near, close to | 15 min on foot, or 10 by car |

Waterfront words (oceanfront, lakefront, beachfront) require the data to say the home sits on the water.

**4. Name things; don't sell feelings.** "A clawfoot tub" tells the guest something. "Pure relaxation awaits" doesn't. If a phrase would fit every listing on the platform, cut it.

**5. Plain words, guest words.** Say pool, not "aquatic amenity," and home, not "domicile." Never use company words such as "listing," "unit," or "inventory."

**6. Honest negatives are a feature.** "It's a third-floor walk-up" and "There's no Wi-Fi" stop the wrong guest from booking. They belong in the highlight when the data flags them, and the judges must not penalize them.

**7. Calm and complete.** Use one or two full sentences that end with a period. No exclamation points, emoji, hedging, fragments, or keyword strings.

## From principle to enforcement

| Principle | Rule | Enforced by | Why there |
|---|---|---|---|
| True before interesting | Every claim is supported by the data | Faithfulness judge (claim by claim) | Needs reading comprehension; scored in code so one bad claim always fails |
| Distance is a promise | Relative phrases within the limits above | Faithfulness judge (table in prompt) | Needs matching a phrase to the right place in the data |
| Distance is a promise | No waterfront words without `water_frontage` | Layer 1 regex | Exact; costs nothing |
| Distinct before complete | At least two standouts, not led by a commodity | Salience judge, given a fixed standout list | The reference list keeps the judge from using its own taste |
| Name things | No stock clichés (list in `evals/config.py`) | Layer 1 regex | Known phrases are cheap to catch exactly |
| Name things | No puffery of any wording | Voice judge | Novel puffery ("prepare to fall in love") can't be listed in advance |
| Plain words | No internal terms | Layer 1 regex (+ voice judge for context-dependent words) | "Property" can mean land, so a context-dependent word goes to the judge |
| Calm and complete | ≤ 200 chars, ≤ 2 sentences, ends with a period, no `!` `?` or emoji | Layer 1 | Counting is code's job; LLMs miscount characters |
| Calm and complete | No fragments, hedging, or keyword dumps | Voice judge | Needs grammar judgment |
| Honest negatives | Never penalized | Voice judge examples, labeling guide | Stated explicitly because judges default to "negative = bad" |

## What's deliberately not a rule

- **Sentence rhythm and "punchiness."** These are hard to define tightly enough for two raters to apply the same way, and if raters can't, a judge can't either. Taste issues go to the pairwise judge, which ranks candidates instead of grading them.
- **A minimum number of features.** Two standouts is the bar. A highlight that lists five isn't better; it's harder to scan.
