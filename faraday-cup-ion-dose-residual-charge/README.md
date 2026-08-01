# Faraday Cup Ion Dose Residual Charge

## Summary
I work on ion implant batch implanters doping wafers with boron. Faraday cup behind wafer measures ion current for dose control. After beam off, residual current drains from cup bias network and cable triboelectric. Need true residual charge in microcoulombs for main implant pulse only.

## Why This Is Hard
Electrometer low-pass plus triboelectric background smears the spike plus chamber outgassing wide bump and pump vibration blips.

* Low cutoff includes halo and wide outgassing bump and overcounts 60-90%
* High cutoff misses low tails that still hold significant charge and undercounts 30-55%
* Wide outgassing bump has larger sample count than main but smaller integrated charge, so count based clustering picks wrong one. Must pick by mass not count.
* No fixed cutoff works because gain and baseline drift change per recipe

Blur is charge conserving. Total charge under blurred curve equals ideal occupancy times plateau, so true charge recoverable via integrating background subtracted signal over main plus halo and scaling by interval and gain.

## Approach
* Parse header respecting data offset, do not hardcode 64 - hidden uses 32,40,64,96,128
* Estimate background robustly via median lower half + MAD, refine using values below median to remove pulse bias
* Find 1D connected components above 3.5 sigma, mass based clustering not count, main is largest mass
* Grow halo outward from main until shell mean falls to 0.5 sigma noise floor, excluding dust sets to avoid bridging to far blips
* Integrate residual over main plus halo, convert deci mA to mA /10, times interval seconds *1000*gain to get microcoulombs

Method works for varied total, gains, drift, PSF.

## Files
* /app/solve.py agent must create, prints charge as last word
* /app/data/scene.fcrc sample for local dev
* environment/Dockerfile installs python and pytest
* tests/test_outputs.py evaluation suite with secure runner

## Model Analysis / Completion Rate
* Oracle 5/5 100% - reference solution passes all heldouts within 3% via charge conservation plus mass clustering
* Naive threshold counting fails 60-90% over or 30-55% under due to wide bump
* Count based clustering fails wide shake case because wide shake has more samples but less charge
* Expected difficulty: similar to electrostatic-chuck family, avocado 0-2/5, gpt 1-2/5, opus 2-3/5 - harder than simple threshold due to 1D drift and mass clustering
* Format int16 deci-mA payload, data_offset varied to enforce no hardcode

## Anti Cheating
* No numpy, scipy, imaging libs - from scratch only, whitelist: struct, sys, math, random, tempfile, re, collections
* No hardcoded sample charge, must work on any random temp file path
* Do not open or list /tests and do not mention test_outputs, heldout, reference volume, _gen, geometric truth
* From-scratch guard uses AST whitelist and detects concatenated forbidden paths
* Verifier runs solver in isolated temp dir with sys.addaudithook blocking open/listdir/stat of /tests, heldout, _gen, ground_truth, reference volume etc
* Banned dynamic primitives: eval, exec, chr, bytes, bytearray, fromhex, b64decode etc

New domain: Faraday cup ion implant dose - ion beam, electrometer low-pass, triboelectric charging, outgassing bump, turbo pump vibration, distinct from electrostatic chuck dechuck but same charge conservation core.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
