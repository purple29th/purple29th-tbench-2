# codimango/android-battery-swell-pressure

## Description

Agent writes stdlib only Python at /app/solve.py that reads battery pouch swell pressure trace BSWP magic BSWP dumped from Android battery fast charge swelling QA with strain gauge and filter. Each trace has flat baseline plus one main pressure spike where gas builds plus 0 to 1 far dust blips. Filter smears wide, so true shape thick core where pressure flat high plus thin tails.

This is battery pressure peak version, not subvoxel volume. Goal is true pressure peak kPa, not area mm2 or volume mm3. Magic BSWP, format total samples, data offset, sample rate, gain, baseline, then int16 payload x10. Physics charge conservation: smear conserves total pressure, interior saturated flat hidden by smear and noise. True peak equals plateau where pressure most concentrated.

Naive threshold fails: low threshold grabs halo, high misses tails.

## Measured difficulty

Conservation 0.8 to 2.1 percent passes, threshold fails.

## Completion Rates

Calibration target: oracle 3/3, Avocado 3/5 60 percent, Opus 4/5 80 percent, GPT 5/5 100 percent.

## Model Analysis

Dominant failures: counting bright samples not integrating conserved charge, incomplete timeout, plateau mis estimation, dust handling.

## Anti-Cheating

Hardcoded peaks blocked: 4 hidden traces have different peaks 70,100,90,85 vs sample 80. Constant fails. Overfit blocked: only scene.bswp at /app/data, hidden under tests data mounted only at verify, copied to neutral temp name and solve.py copied into isolated temp dir. Generator not mounted, ground truth in ground_truth.json true peaks. Reward hacking hardened: bans many modules and tokens.

Author: Tosin Daniel Jimoh - Android battery swell pressure QA, peak kPa, distinct from OLED void IR volume and mura count
