# codimango/android-fingerprint-oil-smear

## Description

Agent writes stdlib-only Python at /app/solve.py that reads fingerprint oil smear map fpos magic FPOS from Android under-display optical fingerprint QA. Each map has one main oil smear plus bleed lines plus far dust. Smear conserves light, so true shape is bright core where brightness is flat high plus thin tails. Ground truth in ground_truth.json is canonical true count from generator: rounded sum of occupancy map (core plus partial border plus bleed lines), not from the reference estimator. Agent must estimate count via mass-based 8-neighbour clustering to drop dust, estimate baseline and plateau, and integrate halo to recover true count.

Distinct from OLED void volume mm3 IR and display mura CDMR capacitive count and battery BCTR capacity mAh.

## Completion Rates

Target: oracle 4/4 within tol=max(2,3%), Avocado 3/5 60 percent, Opus 4/5 80 percent, GPT 5/5 100 percent. Oracle errors 0 to 2 counts vs true 190,281,422,698.

## Model Analysis

Dominant failures: counting bright pixels with fixed threshold not integrating conserved light, incomplete due to recursive flood fill, plateau amplitude mis-estimation, dust handling by count not mass, forgetting int16 little endian decoding.

## Anti-Cheating

Hardcoded counts blocked: 4 hidden maps have different counts 190,281,422,600 vs sample 251. Constant fails. Overfit blocked: only scene.fpos at /app/data, hidden under tests/data mounted only at verify, copied to neutral temp name scan.fpos and solve.py copied into isolated temp dir. Generator _gen.py not mounted, ground truth in ground_truth.json is canonical occupancy count from _gen.py true_count, not from solve.py reference. Reward hacking hardened: bans many modules (including pty, os) and calls (including breakpoint) via AST and decoded literal inspection.

Author: Tosin Daniel Jimoh - Android fingerprint oil smear QA
