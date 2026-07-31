# Cryo Pump Regen Gas Burst Residual Charge

## Summary
Cryo pump regeneration gas burst measurement for contamination control. During regen the cold head warms and trapped gas bursts out as ion current. Need to estimate true burst charge despite low pass smear and drift.

## Difficulty
Hard part is separating main gas burst mass from baseline drift, low pass halo, far valve blips, and broad vibration bump without fixed cutoff. Requires robust baseline, mass based event selection, tail growth, and variable offset handling.

## Anti Cheating
No numpy, from scratch only with struct sys math random tempfile re collections. No hardcoded charge. Audit hook sandbox blocks /tests, heldout, _gen etc even with dynamic path construction. From scratch guard whitelist.

## Model Analysis
Oracle 100 percent via charge conservation plus mass clustering. Naive threshold fails 65 to 95 percent high or 25 to 50 low. Count based clustering fails wide vibration bump case.
# trigger revalidation Thu Jul 30 06:08:34 PM PDT 2026
