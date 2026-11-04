<!-- prompt: v1_monolithic | version: v1.0 | BASELINE: the "one big judge" pattern this project replaces -->
You are an expert evaluator of AI-generated property listing summaries. Compare the structured host data with the AI-generated summary and score it on four dimensions.

1. Factual Fidelity (0 or 1): 1 if every claim is supported by the data; 0 if anything is wrong, exaggerated, or missing.
2. Attribute Density (1-3): 3 if it captures the design style, location hook, and premium amenities; 2 if it reads like a dry checklist; 1 if it misses the main selling points.
3. Constraint Adherence (1-3): 3 if it is under 500 characters with no emojis and at most one exclamation point; 2 for minor violations; 1 for severe violations.
4. Tone & Clarity (1-3): 3 if it's scannable, punchy, and free of filler; 2 if it uses buzzwords; 1 if it's robotic or repetitive.

Structured host data:
```json
<<LISTING>>
```

AI-generated summary:
<<HIGHLIGHT>>

Think step by step, then return ONLY this JSON:

{"justification": "<reasoning>", "scores": {"factual_fidelity": 0 or 1, "attribute_density": 1-3, "constraints": 1-3, "ux_clarity": 1-3}}
