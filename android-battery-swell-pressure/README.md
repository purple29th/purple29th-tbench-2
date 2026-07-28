# codimango/android-battery-swell-pressure

## Description

Agent writes stdlib-only Python at /app/solve.py that reads battery fuel gauge trace BCTR (magic BCTR) dumped from Coulomb counter QA for swelling after fast charge. Each trace has slowly drifting baseline plus noise plus one main charge event where current jumps high with long thin tails from low-pass filtering plus far dust blips from connector noise including one wide low-amplitude blip that has larger sample count than main event but smaller integrated charge, requiring mass-based clustering not count-based. Agent must recover true capacity mAh of main event via charge conservation: robust baseline estimation in presence of linear drift, mass-based 1D grouping to drop dust, halo growth to include smeared tails, integrate residual and convert using interval and gain.

Format: header with total samples, data offset, sample interval, shunt gain, baseline floor, then int16 x10 current payload. Header has garbage padding between 28 and offset to enforce offset parsing (offsets 32,40,64,96 for heldouts).

This is battery capacity mAh task, distinct from subvoxel volume mm3 IR and display mura CDMR 2D count. Battery is 1D contiguous grouping vs mura 2D 8-neighbour flood fill.

## Completion Rates

Hardened version: baseline linear drift 10-20, noise 7-9.5 sigma (0.7-0.95 mA), PSF 4.0-5.2, narrow core 38-50 width, plateau 1200-1480 (120-148 mA), plus wide low dust (width 60-66, amp 0.33-0.42*0.6) requiring mass-based clustering. Oracle 5/5 100% within 3% (errors <0.7%). After removing explicit algorithm recipe (median/MAD/3.5σ/0.5σ/40 iters and exact formula) and adding wide low dust, Avocado expected 1-2/5 (count-based fails 60%+ error, simple sum-all fails 25%+), Opus 2-3/5, GPT 2-3/5. Previously over-specified version with instruction giving full recipe passed 5/5 for all. Now requires genuine engineering judgment: mass vs count, robust baseline vs file baseline field, offset parsing.

## Model Analysis

Dominant failures: counting samples above fixed threshold not recovering smeared tails or including wide low dust causing 60%+ over/under estimation, forgetting int16 x10 scaling to mA, missing data offset padding (hardcode 64 fails on 32/40/96), dust handling by sample count not integrated mass (wide low dust has larger count than main but smaller mass), recursive clustering hitting recursion limit, mis-estimating baseline floor as file baseline field instead of robust median low-half, not handling linear drift, not handling charge conservation (need /10 * interval * gain /3600*1000? actually /3.6) . Hardened anti-cheat includes wide low dust that makes count-based clustering fail.

## Anti-Cheating

Hardcoded values blocked: 5 traces have different capacities 943, 916, 1006, 955, 659 mAh; sample 943 vs heldouts 916,1006,955,659 range 659-1006. Constant fails. Overfit blocked: only scene.bctr at /app/data, hidden files under /tests/data mounted only at verification, copied to neutral temp name scan.bctr and solve.py copied into isolated temp dir. Generator _gen.py never mounted, ground truth in ground_truth.json holds canonical capacities. Reward hacking hardened via AST banned modules including os, pathlib, io, numpy, and calls including eval, chr, getattr, and literal scan blocking /tests, heldout, ground_truth, _gen, reference. Varied data offsets enforce header parsing. Wide low dust (60-66 width) has larger sample count than main (38-50) but smaller integrated mass, so count-based clustering picks wrong cluster.

Author: Tosin Daniel Jimoh - Android battery fuel gauge Coulomb counter capacity mAh, 1D contiguous grouping, charge conservation, mass-based clustering, drift
