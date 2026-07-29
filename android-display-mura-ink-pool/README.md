# codimango/android-display-mura-ink-pool

## Description

Agent writes stdlib-only Python at /app/solve.py that reads capacitive touch map CDMR (magic CDMR) from display lamination ghost touch QA. Each map has one main ink pool where capacitance high plus thin bleed lines plus far dust blobs. Smear conserves charge, need mass-based 8-neighbour clustering to drop dust, estimate baseline plateau and integrate halo to get true count of affected touch cells. Header data offset varies 64-128 and must be respected.

True count is fractional occupancy integral: interior 1.0, border partial, bleed lines partial, sum rounded. Equivalent to conserved charge divided by saturated plateau. Grading tolerance is max(2, 3% of expected). Sample scene.cdmr has true count 249 (tolerance ~7).

Dust handling is enforced: hidden maps include heavy dust where total dust charge is 40-80 cells equivalent and bright dust up to 1.5x plateau, plus dust with larger area than main pool to defeat area selection, plus off-center edge pools and large PSF cases where halo holds significant charge so skipping halo growth fails. Naive global sum fails, area-selection fails, no-halo shortcut fails.

## Completion Rates

Calibration target: oracle 3/3, Avocado 2/5 originally, Opus 5/5, GPT 5/5 but now hardened to be harder. Heavy dust cases cause Avocado to drop. All within 1-4/5 not too easy.

## Model Analysis

Dominant failures: counting bright cells not integrating conserved charge, global sum without dust isolation, incomplete timeout, plateau mis-estimation using global max instead of interior median, dust handling using count not mass, assuming centered pool.

## Anti-Cheating

Hardcoded counts blocked: 8 hidden maps have different counts 192,283,347,508,278,346,219,425 vs sample 248-249. Constant fails. Overfit blocked: only scene.cdmr exists in agent container, hidden under tests/data mounted only at verify, copied to neutral temp name and solve.py copied into isolated temp dir. Generator not mounted, ground truth in ground_truth.json true counts (geometric integral, not heuristic). Reward hacking hardened: bans many modules and tokens with decoded literal inspection and dunder audit via AST, no bold double underscore substrings. Heavy dust forces mass-based component selection: naive all-grid charge ratio fails by >5x tolerance on heldout_5-8.

Author: Tosin Daniel Jimoh - Android display ghost touch QA
