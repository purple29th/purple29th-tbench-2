# codimango/android-display-mura-ink-pool

## Description

Agent writes stdlib only Python at /app/solve.py that reads capacitive touch map cdmr magic CDMR from display lamination ghost touch QA. Each map has one main ink pool where capacitance high plus thin bleed lines plus far dust. Smear conserves charge, need mass based 8 neighbour clustering to drop dust, estimate baseline plateau and integrate halo to get true count of affected touch cells.

This task is UI ghost touch counting, not subvoxel volume mm3 and not luminance area mm2. It uses CDMR capacitive grid with baseline field and int16 payload, goal count integer, not area. Different from OLED void IR volume and battery swell pressure capacity mAh.

## Completion Rates

Calibration target: oracle 3/3, Avocado 2/4 50 percent, Opus 3/5 60 percent, GPT 4/5 80 percent. All within 1 to 4/5 not too easy.

## Model Analysis

Dominant failures: counting bright cells not integrating conserved charge, incomplete timeout, plateau mis estimation, dust handling using count not mass.

## Anti-Cheating

Hardcoded counts blocked: 4 hidden maps have different counts 192,283,347,508 vs sample 248. Constant fails. Overfit blocked: only scene.cdmr exists in agent container, hidden under tests data mounted only at verify, copied to neutral temp name and solve.py copied into isolated temp dir. Generator not mounted, ground truth in ground_truth.json true counts. Reward hacking hardened: bans many modules and tokens with decoded literal inspection and dunder audit via AST, no bold double underscore substrings.

Author: Tosin Daniel Jimoh - Android display ghost touch QA
