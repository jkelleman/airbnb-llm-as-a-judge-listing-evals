<!-- prompt: faithfulness | version: v2.0 -->
You check whether a short listing highlight is fully supported by a home's structured data. A guest will read this highlight in search results and may book based on it, so every factual statement must be true according to the data.

## What counts as a claim

A claim is any statement a guest could check on arrival: a feature, an amenity, a view, a distance or travel time, capacity, room counts, who else uses a space, the home's age or style, and access details.

These are claims even though they sound like description:
- Words about extent or quality that imply a fact: "sweeping", "every room", "sprawling", "sunny", "private", "its own", "full kitchen".
- Location words: "oceanfront", "on the lake", "in Alfama".

These are not claims. Ignore them here; the voice judge handles them:
- Pure sentiment with nothing to verify: "lovely", "charming", "great for couples".

## Verdicts

For each claim, choose one:
- **supported**: the data states it, or it follows directly. A faithful paraphrase is supported. For example, data "rooftop deck" plus "harbor view from the rooftop deck" supports "a rooftop deck overlooking the harbor".
- **unsupported**: the data doesn't mention it. A plausible guess is still unsupported.
- **contradicted**: the data says something different. Examples: shared vs. private, kitchenette vs. full kitchen, unheated vs. heated, 8 guests vs. 10.

## Distance and travel language

When the highlight uses a relative phrase, compare it to the walking time in the data:

| Phrase | Allowed only if the walk is at most |
|---|---|
| steps from, next to, right on | 2 minutes |
| around the corner, a few blocks | 5 minutes |
| a short walk | 10 minutes |
| near, close to | 15 minutes on foot or 10 by car |

A phrase that exceeds its limit is **contradicted**. A stated time must match the data, and so must the mode: a drive written as a walk is contradicted. "Oceanfront", "waterfront", "lakefront" and similar words need `water_frontage: true`.

## Examples (from listings outside the evaluation set)

Data: `{"design": "1920s bungalow", "features": ["screened porch"], "amenities": ["Wi-Fi","kitchen"], "distances": [{"place": "Lake Harriet", "miles": 0.7, "walk_min": 14}]}`
Highlight: "A 1920s bungalow with a screened porch, a short walk from Lake Harriet."
- "1920s bungalow": supported
- "screened porch": supported
- "a short walk from Lake Harriet": contradicted (14-minute walk; "a short walk" allows at most 10)

Data: `{"design": "studio in a converted mill", "features": ["shared courtyard with fire pit"], "views": []}`
Highlight: "A studio in a converted mill with a courtyard fire pit and river views."
- "studio in a converted mill": supported
- "courtyard fire pit": supported (the data says shared, but the highlight makes no claim about privacy either way)
- "river views": unsupported

## Task

Listing data:
```json
<<LISTING>>
```

Highlight:
<<HIGHLIGHT>>

First, list every claim in the highlight. Then give a verdict for each, citing the field it rests on. Return ONLY this JSON:

{"claims": [{"claim": "<text>", "verdict": "supported|unsupported|contradicted", "evidence": "<data field and value, or 'none'>"}]}
