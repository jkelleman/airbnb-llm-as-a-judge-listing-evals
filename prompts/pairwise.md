<!-- prompt: pairwise | version: v2.0 -->
Two highlights were written for the same home. Pick the one that would better help a guest decide whether this home fits their trip.

Weigh these in order:
1. **Accuracy.** A highlight with any claim the data doesn't support loses to one without, whatever else is true.
2. **What it surfaces.** It should name the home's distinctive features rather than commodities.
3. **How it reads.** It should be specific, plain, and calm. Neither salesy nor robotic.

Length isn't a merit. If both are about equally good, answer "tie". The order the highlights appear in doesn't matter.

Listing data:
```json
<<LISTING>>
```

Highlight A:
<<A>>

Highlight B:
<<B>>

Compare them against each criterion in order, then decide. Return ONLY this JSON:

{"reasoning": "<two or three sentences>", "winner": "A" | "B" | "tie"}
