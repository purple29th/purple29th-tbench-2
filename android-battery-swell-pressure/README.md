# codimango/android-battery-swell-pressure

## Description

Agent writes stdlib only Python at /app/solve.py that reads battery charge trace BCTR magic BCTR dumped from Android battery fuel gauge Coulomb counter QA for swelling after fast charge. Each trace has flat baseline plus one main charge event where current high plus thin tails plus far dust blips. Filter smears wide, so true shape thick core where current flat high plus thin tails.

This is battery capacity mAh version, not subvoxel volume mm3 and not display mura count. Magic BCTR, format total samples data offset sample interval gain baseline int16 x10 current payload. Physics charge conservation: smear conserves total charge, interior saturated flat hidden by smear and noise. True capacity equals total residual over main plus halo times interval times gain divided by 3.6.

Naive threshold fails: low threshold includes halo, high misses tails.

## Measured difficulty

Conservation 0.6 to 2.1 percent passes at 3 percent tolerance, threshold fails.

## Completion Rates

Calibration target: oracle 3/3 100 percent, Avocado 3/5 60 percent with 1 incomplete and 1 plateau error, Opus 4/5 80 percent with 1 timeout, GPT 5/5 100 percent. Distinct from OLED void IR volume and mura count.

## Model Analysis

Dominant failures: counting bright samples not integrating conserved charge, incomplete timeout, plateau mis estimation, dust handling, forgetting int16 x10 decoding.

## Anti-Cheating

Hardcoded peaks blocked: 4 hidden traces have different capacities 424,655,580,736 mAh vs sample 472. Constant fails. Overfit blocked: only scene.bctr at /app/data, hidden under tests data mounted only at verify, copied to neutral temp name and solve.py copied into isolated temp dir. Generator _gen.py not mounted, ground truth in ground_truth.json true capacities. Reward hacking hardened: bans many modules and tokens via AST and decoded literal inspection, no bold double underscore.

Author: Tosin Daniel Jimoh - Android battery swell pressure capacity mAh, fuel gauge Coulomb counter
