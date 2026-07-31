# EUV Plasma Chamber Wall Charge Decay

## Summary
EUV plasma chamber wall charge decay for defect control. After plasma clean charge stays trapped on wall and leaks as current. Need to estimate true decay charge despite RF low pass smear.

## Difficulty
Hard part is separating main wall discharge mass from baseline drift, halo, far shutter blips, broad vibration bump. Requires robust baseline, mass based selection, tail growth, variable offset.

## Anti Cheating
No numpy, from scratch only. No hardcoded charge. Audit hook sandbox blocks /tests etc. Whitelist guard.

## Model Analysis
Oracle 100 percent via conservation plus mass clustering. Naive threshold fails 60 to 88 high or 28 to 52 low.
