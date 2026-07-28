# codimango/android-fingerprint-oil-smear

## Description

Agent writes stdlib only Python at /app/solve.py that reads fingerprint oil smear map fpos magic FPOS from Android under display optical fingerprint QA. Each map has one main oil smear plus bleed lines plus far dust. Smear conserves light, need mass based 8 neighbour clustering to drop dust, estimate baseline plateau and integrate halo to get true count of affected pixels.

Distinct from OLED void volume mm3 IR and display mura CDMR capacitive count and battery BCTR capacity mAh.

## Completion Rates

Target: oracle 3/3, Avocado 3/5 60 percent, Opus 4/5 80 percent, GPT 5/5 100 percent.

## Model Analysis

Failures: counting bright pixels not integrating conserved light, incomplete, plateau error, dust.

## Anti-Cheating

Hardcoded counts blocked: 4 hidden maps have different counts 190,281,422,600 vs sample 251. Constant fails. Overfit blocked: only scene.fpos at /app/data, hidden under tests data mounted only at verify, neutral temp copy and isolated TD. Generator not mounted, ground truth in ground_truth.json. Reward hacking hardened.

Author: Tosin Daniel Jimoh - Android fingerprint oil smear QA
