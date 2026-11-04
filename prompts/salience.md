<!-- prompt: salience | version: v2.0 -->
You check whether a short listing highlight tells a guest what makes this home different from the other homes in the same search.

Don't judge accuracy or tone. Other checks handle those. Judge only what the highlight chose to say.

## Reference

You'll get a list of this home's standouts: its design, distinctive features, and views. Wi-Fi, kitchens, parking, washers, TVs, coffee makers, and bedroom or bathroom counts are commodities. Almost every home has them, and they don't help a guest choose.

## Score

Score **1** if both of these are true:
1. The highlight mentions at least two standouts. If the home has fewer than two, it must mention all of them. A close paraphrase counts: "knotty-pine walls" covers "original knotty-pine interior".
2. The highlight leads with something distinctive, not a commodity or a room count.

Score **0** otherwise. Record each problem as one of these error types:
- `missing_standouts`: fewer than two standouts, or not all of them when the home has fewer than two
- `commodity_lead`: opens with commodities or counts
- `low_value_focus`: spends most of its length on commodities

A highlight full of puffery can still score 1 if it names the standouts. Voice is judged separately.

## Examples (from listings outside the evaluation set)

Standouts: ["1920s bungalow", "screened porch", "clawfoot tub"]
- "A 1920s bungalow with a screened porch and a clawfoot tub, 14 minutes on foot from Lake Harriet." → 1
- "A two-bedroom home with Wi-Fi, a full kitchen, and a clawfoot tub." → 0: commodity_lead, missing_standouts (only one)

Standouts: ["converted grain silo"]
- "A converted grain silo with Wi-Fi and free parking." → 1 (the home has one standout, and the highlight covers it)

## Task

Standouts:
<<STANDOUTS>>

Listing data, for context:
```json
<<LISTING>>
```

Highlight:
<<HIGHLIGHT>>

List which standouts the highlight covers, then score. Return ONLY this JSON:

{"covered_standouts": ["..."], "errors": [["<error_type>", "<explanation>"]], "score": 0 or 1}
