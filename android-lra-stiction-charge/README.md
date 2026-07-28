# codimango/android-lra-stiction-charge v0.1

## Description

Agent writes stdlib-only Python at /app/solve.py that reads LRA haptics trace LRAE (magic LRAE) dumped from coil back-EMF QA for stiction after drop. Each trace has slowly drifting baseline (10-22 mA thermal), Gaussian noise (0.7-1.1 mA), one main snap event where current jumps high with long thin tails from driver low-pass, plus far hand micro-shake blips plus one wide low-amplitude shake that is broad but shallow – larger sample count than main but smaller integrated charge.

This is the 1D analog of `android-battery-swell-pressure` and `foundry-thermal-subvoxel-void` family but for haptics:
- Battery: BCTR capacity mAh, Coulomb counter, charge conservation, mass-based 1D clustering vs wide low dust
- This: LRAE charge uC (microcoulombs), back-EMF current, same conservation, mass-based 1D clustering
- Distinct via magic LRAE vs BCTR, unit uC (1000 * mA * sec) vs mAh (/3.6), story haptics vs battery, coil gain vs shunt gain, interval 0.0008 sec vs 0.5 sec, drift 10-22 vs 10-20, noise 7-11 vs 7-9.5
- Ink-blot and fingerprint are 2D area mm2 / pixel count, OLED/Foundry are 3D volume mm3.

Format: header with total samples, data_offset, interval f32, gain f32, baseline floor u32, garbage padding (offsets 32,40,64,96,128), then int16 deci-mA payload (value/10 = mA, x10 scaling like battery).

This is 1D contiguous grouping (mass = sum residual) not 2D 8-neighbour (ink) or 3D 26-neighbour (OLED/foundry).

## Completion Rates

Oracle 5/5 100% within 3% (errors <0.8%). Expected after hardening:
- avocado 1-2/5: count-based fails 60%+ due to wide low shake having larger count than main, simple low/high threshold fails 60-90% over / 30-55% under, missing offset fails 3/4, forgetting /10 scaling fails.
- opus 2-3/5
- gpt 2-3/5
Overall ~40% like battery and foundry.

Previously battery over-specified version gave 5/5 all models; hardened version with wide low dust requiring mass-based not count-based drops to 1-2/5 avocado.

## Model Failure Modes

- Counting samples above fixed threshold not recovering smeared tails or including wide low shake causing 60-90% over/under
- Picking cluster by sample count not integrated mass: wide low shake (62-74 width) has larger count than main (36-52) but smaller mass, mass-based picks correct
- Forgetting deci-mA /10 scaling to mA, forgetting *1000 to uC (1 mA*sec = 1000 uC)
- Hardcoding data_offset 64 fails on 32/40/96/128
- Estimating baseline from header baseline floor field instead of robust median low-half, not handling linear drift 10-22
- Recursive flood fill hitting recursion limit (2048-3072 samples)
- Not handling halo growth: shell mean <0.5 sigma stop

## Anti-Cheating

- 5 traces: scene ~4967 uC, heldouts 3316-6506 uC range (4781,6506,5275,3316) – all different, constant fails
- Only scene.lrae at /app/data, hidden under /tests/data mounted only at verification, neutral temp copy scan.lrae
- Ground truth in ground_truth.json holds canonical uC capacities from generator occupancy integral, not from reference estimator
- Reward hacking: AST banned modules os, pathlib, io, numpy etc and calls eval, chr, getattr, plus literal scan blocking /tests, heldout, ground_truth, _gen
- Varied offsets enforce header parsing
- Wide low dust ensures count-based clustering fails

Author: Tosin Daniel Jimoh – Android haptics LRA stiction charge uC, 1D contiguous mass-based clustering, charge conservation, distinct from battery mAh and OLED mm3.
