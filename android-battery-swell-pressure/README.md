# codimango/android-battery-swell-pressure

## Description

Agent writes stdlib-only Python at /app/solve.py that reads battery fuel gauge trace BCTR (magic BCTR) dumped from Coulomb counter QA for swelling after fast charge. Each trace has flat baseline plus one main charge event where current jumps high with thin tails from filtering plus far dust blips from connector noise. Agent must recover true capacity mAh of main event.

Format: header with total samples, data offset, sample interval, shunt gain, baseline floor, then int16 x10 current payload.

This is battery capacity mAh task, distinct from subvoxel volume mm3 IR and display mura CDMR count.

## Completion Rates

Calibration: oracle 4/4 100 percent within 3 percent tolerance (errors 0.3 to 0.6 percent), Avocado 3/5 60 percent (1 incomplete, 1 plateau error), Opus 4/5 80 percent (1 timeout), GPT 5/5 100 percent. Distinct from OLED void and mura pool.

## Model Analysis

Dominant failures: counting samples above fixed threshold not recovering smeared tails, forgetting int16 x10 scaling to mA, missing data offset padding, dust handling by count not mass, recursive clustering hitting recursion limit, mis-estimating baseline floor.

## Anti-Cheating

Hardcoded values blocked: 4 hidden traces have different capacities 424,655,580,736 mAh versus sample 472 mAh. Constant fails. Overfit blocked: only scene.bctr at /app/data, hidden files under /tests/data mounted only at verification, copied to neutral temp name scan.bctr and solve.py copied into isolated temp dir. Generator _gen.py never mounted, ground truth in ground_truth.json holds canonical capacities. Reward hacking hardened via AST banned modules including pty and os and calls including breakpoint, and literal scan blocking /tests, heldout, ground_truth, _gen, reference.

Author: Tosin Daniel Jimoh - Android battery fuel gauge Coulomb counter capacity
