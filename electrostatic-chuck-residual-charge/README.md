# Electrostatic Chuck Residual Charge

## Summary
I work on semiconductor fab handling electrostatic chucks that hold wafers. After dechuck there is residual charge that stays. We log current trace with a main discharge event plus drift and robot vibration blips. Need true residual charge in microcoulombs for main event.

## Why This Is Hard
Driver low pass smears the spike plus thermal baseline drift and hand micro movement blips.

* Low cutoff includes halo and wide low amplitude shake and overcounts 60 to 90 percent
* High cutoff misses low amplitude tails that still hold significant charge and undercounts 30 to 55 percent
* Wide low amplitude shake has larger sample count than main but smaller integrated charge, so count based clustering picks wrong one. Must pick by mass not count.
* No fixed cutoff works because gain and baseline and temperature drift change per batch

Blur is charge conserving. Total charge under blurred curve equals ideal occupancy times plateau, so true charge recoverable via integrating background subtracted signal over main plus halo and scaling by interval and gain.

## Approach
* Parse header respecting data offset, do not hardcode 64
* Estimate background robustly via median lower half + MAD, subtract
* Find 1D connected components above 3.5 sigma, mass based clustering not count, main is largest mass
* Grow halo outward from main until shell mean falls to 0.5 sigma noise floor, do not include far dust blips
* Integrate residual over main plus halo, convert deci mA to mA divided by 10, times interval seconds times 1000 times gain to get microcoulombs

Method works for varied dimensions, gains, drift.

## Files
* /app/solve.py agent must create, prints charge as last word
* /app/data/scene.esca sample for local dev
* environment/Dockerfile installs python and pytest
* tests/test_outputs.py evaluation suite

## Model Analysis / Completion Rate

* Oracle 5/5 100 percent - reference solution passes all heldouts within 3 percent via charge conservation plus mass based clustering
* Naive threshold counting fails 60-90% over or 30-55% under
* Count based clustering fails wide shake case because wide shake has more samples but less charge
* Expected difficulty: avocado 0/5 to 2/5, gpt 1/5, opus 2/5 - harder than simple threshold tasks due to 1D time series drift and mass clustering
* Format is int16 deci-mA payload, data_offset varied 32,40,64,96,128 to enforce no hardcode 64

## Anti Cheating
* No numpy, scipy, imaging libs - from scratch only, whitelist: struct, sys, math, random, tempfile, re, collections
* No hardcoded sample charge, must work on any random temp file path
* Do not open or list /tests and do not mention test outputs, heldout, reference volume, _gen, geometric truth
* From-scratch guard uses AST whitelist and detects concatenated forbidden paths including "/te"+"sts" patterns
* Verifier runs solver in isolated temp dir with sys.addaudithook blocking open/listdir/stat of /tests, heldout, _gen, ground_truth, reference volume etc even when paths are built dynamically via bytes or concatenation
* Banned dynamic primitives: eval, exec, chr, bytes, bytearray, fromhex, b64decode etc and reflection calls
