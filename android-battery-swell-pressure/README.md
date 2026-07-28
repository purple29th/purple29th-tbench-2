# codimango/android-battery-swell-pressure

## Description

Agent writes stdlib-only Python at /app/solve.py that reads battery fuel gauge trace BCTR (magic BCTR) dumped from Coulomb counter QA for swelling after fast charge. Each trace has flat baseline plus one main charge event where current jumps high with thin tails from filtering plus far dust blips from connector noise. Agent must recover true capacity mAh of main event via charge conservation: integrate residual after baseline subtraction over main cluster + smeared halo, divide by plateau, convert using interval and gain.

Format: header with total samples, data offset, sample interval, shunt gain, baseline floor, then int16 x10 current payload. Header has garbage padding between 28 and offset to enforce offset parsing (offsets 32,40,64,96 for heldouts).

This is battery capacity mAh task, distinct from subvoxel volume mm3 IR and display mura CDMR 2D count. Battery is 1D contiguous grouping vs mura 2D 8-neighbour flood fill.

## Completion Rates

After making easier (lower noise 2.5-3.2 sigma, higher plateau 1200-1400, wider core 65-80, smaller PSF 1.7-2.1, explicit charge-conservation hint and sample expected 1321.67 mAh): oracle 4/4 100 percent within 3 percent (errors <0.5%), Avocado expected 3/5 60 percent, Opus 4-5/5, GPT 4-5/5. Previously with no hint it was 0/5 unsolvable. Now solvable but still requires mass-based clustering and halo integration, not fixed threshold.

## Model Analysis

Dominant failures: counting samples above fixed threshold not recovering smeared tails (threshold fails), forgetting int16 x10 scaling to mA, missing data offset padding (hardcode 64 fails on 32/40/96), dust handling by count not mass, recursive clustering hitting recursion limit, mis-estimating baseline floor as file baseline field instead of median, not handling charge conservation (charge = residual/10 * interval * gain /3.6), not handling negative ids (if filtered).

## Anti-Cheating

Hardcoded values blocked: 4 hidden traces have different capacities 1232,1426,1297,1560 mAh versus sample 1321.67 mAh. Constant fails. Overfit blocked: only scene.bctr at /app/data, hidden files under /tests/data mounted only at verification, copied to neutral temp name scan.bctr and solve.py copied into isolated temp dir. Generator _gen.py never mounted, ground truth in ground_truth.json holds canonical capacities. Reward hacking hardened via AST banned modules including os, pathlib, io, numpy, and calls including eval, chr, getattr, and literal scan blocking /tests, heldout, ground_truth, _gen, reference. Varied data offsets enforce header parsing.

Author: Tosin Daniel Jimoh - Android battery fuel gauge Coulomb counter capacity mAh, 1D contiguous grouping, charge conservation
