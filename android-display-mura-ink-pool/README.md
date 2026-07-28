# codimango/android-display-mura-ink-pool

## Description

Agent writes stdlib-only Python at /app/solve.py that reads capacitive touch map CDMR (magic CDMR) from display lamination ghost touch QA. Each map has one main ink pool where capacitance high plus thin bleed lines plus far dust blobs. Smear conserves charge, need mass-based 8-neighbour clustering to drop dust, estimate baseline/plateau and integrate halo to get true count of affected touch cells.

True count is fractional occupancy integral: interior 1.0, border 0-0.55, bleed lines 0.35-0.70, sum rounded. Equivalent to conserved charge / saturated plateau. Grading tolerance is max(2, 3% of expected). Sample scene.cdmr has true count 249 (tolerance ~7).

This task is UI ghost touch counting, not subvoxel volume mm3 and not luminance area mm2. It uses CDMR capacitive grid with baseline field and int16 payload, goal count integer, not area. Different from OLED void IR volume and battery swell pressure.

Dust handling is enforced: hidden maps include heavy dust cases where total dust charge is 40-80 cells equivalent (up to 50% extra if summed globally) and bright dust up to 1.5x plateau, plus off-center/edge pools (center at 14,48 and 20,55) to defeat center assumption. Naive global sum of positive excess fails 4/8 heldouts.

## Completion Rates

Calibration target: oracle 3/3, Avocado 2/5 originally, Opus 5/5, GPT 5/5 but now hardened to be harder. Heavy dust cases cause Avocado to drop. All within 1-4/5 not too easy.

## Model Analysis

Dominant failures: counting bright cells not integrating conserved charge, global sum without dust isolation, incomplete timeout, plateau mis-estimation using global max instead of interior median, dust handling using count not mass, assuming centered pool.

## Anti-Cheating

Hardcoded counts blocked: 8 hidden maps have different counts 192,283,347,508,278,346,219,425 vs sample 248-249. Constant fails. Overfit blocked: only scene.cdmr exists in agent container, hidden under tests/data mounted only at verify, copied to neutral temp name and solve.py copied into isolated temp dir. Generator not mounted, ground truth in ground_truth.json true counts (geometric integral, not heuristic). Reward hacking hardened: bans many modules and tokens with decoded literal inspection and dunder audit via AST, no bold double underscore substrings. Heavy dust forces mass-based component selection: naive all-grid charge ratio fails by >5x tolerance on heldout_5-8.

Author: Tosin Daniel Jimoh - Android display ghost touch QA
