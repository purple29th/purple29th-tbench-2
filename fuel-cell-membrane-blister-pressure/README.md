# Fuel Cell Membrane Blister Pressure

## Summary
I work in energy lab testing fuel cell membranes. Membrane can develop small blisters that lift and block gas flow. When blister pops it releases burst of pressure that we log with pressure sensor. Need true blister pressure in kPa for main event.

## Why This Is Hard
Sensor amplifier low pass smears burst plus thermal baseline drift and pump vibration blips.

* Low cutoff includes halo plus wide low bump and overcounts 60 to 90 percent
* High cutoff misses low tails that still carry pressure and undercounts 30 to 55 percent
* Wide low bump has larger sample count than main but smaller integrated pressure, so count based clustering picks wrong one. Must pick by mass not count.
* No fixed cutoff works because gain and baseline and drift change per membrane and per lot

Blur is pressure conserving. Total pressure under blurred curve equals ideal occupancy times plateau, so true pressure recoverable via integrating background subtracted signal over main plus halo and scaling by interval and gain.

## Approach
* Parse header respecting data offset, do not hardcode 64
* Estimate background robustly via median lower half plus MAD, subtract
* Find 1D connected components above 3.5 sigma, mass based clustering not count, main is largest mass
* Grow halo outward from main until shell mean falls to 0.5 sigma noise floor, do not include far blips
* Integrate residual over main plus halo, convert deci kPa to kPa divided by 10, times interval seconds times gain to get kPa. Actually pressure conversion: true pressure = total_residual /10 * interval * gain

Method works for varied dimensions, gains, drift.

## Files
* /app/solve.py agent must create, prints pressure as last word
* /app/data/scene.fmbp sample for local dev
* environment/Dockerfile installs python and pytest
* tests/test_outputs.py evaluation suite

## Model Analysis / Completion Rate

* Oracle 5/5 100 percent - reference solution passes all heldouts within 3 percent via pressure conservation plus mass based clustering
* Naive threshold counting fails 60-90% over or 30-55% under
* Count based clustering fails wide bump case because wide bump has more samples but less pressure
* Expected difficulty: avocado 0/5 to 2/5, gpt 1/5, opus 2/5 - similar to LRA stiction charge which has 0/5 avocado. Harder than simple volume tasks due to 1D time series drift and mass clustering
* Both int16 and varied data_offset 32,40,64,96,128 exercised to enforce no hardcode 64

## Anti Cheating
* No numpy, scipy, imaging libs - from scratch only
* No hardcoded sample pressure, must work on any random temp file path
* Do not open or list /tests
* From scratch guard bans os, io, pathlib etc
* Secure verifier generates heldouts at runtime in temp dir and runs solver in isolated sandbox with audit hook blocking /tests, heldout, _gen etc
* Banned import check via AST
