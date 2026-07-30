# Laser Weld Keyhole Channel Porosity

## Summary
I work on laser weld factory line. Weldment after high power laser sometimes forms keyhole collapse that leaves a long narrow channel along weld direction that can leak fluid. X ray shows bright channels but blurred by X ray PSF, so channel looks larger and fuzzier than true size.

This task requires a from scratch Python script that parses custom binary .weld and reports true channel porosity volume in mm3.

## Why This Is Hard
X ray blur makes threshold counting imprecise. Low cutoff includes huge halo and overcounts by 80 to 130 percent. High cutoff misses thin channel that never gets bright enough and undercounts by 30 to 50 percent. No fixed cutoff works across files because brightness and blur width change.

Correct method is intensity conservation. Total X ray signal is conserved despite blur. So true channel voxels equals sum of background subtracted intensity divided by plateau intensity.

To make it work you must separate main channels from far specks and round gas pores using 26 neighbour connectivity plus shape filtering. Long narrow keyhole channels along weld count, round gas pores must be ignored. Estimate background without bias from channels, estimate true plateau intensity without being fooled by noise, and decide how far faint halo extends without merging specks or round pores. That is the hard part.

## Approach
Similar to other precision porosity tasks, you need to:
* Parse header respecting data offset, do not hardcode 64
* Keep only main long narrow channels, ignore far specks and round gas pores via shape
* Estimate background from border voxels far from channel
* Estimate plateau from core flat region top percentile mean
* Integrate halo with conservation and recover volume scaling by sx sy sz from header

Method works for varied dimensions, spacings, brightness, blur widths.

## Files
* /app/solve.py is file agent must create, prints volume as last word
* /app/data/scene.weld is sample for local dev
* environment/Dockerfile installs python and pytest
* tests/test_outputs.py is evaluation suite

## Model Analysis / Completion Rate

* Oracle 11/11 100 percent - reference solution passes all heldouts within 1 percent via intensity conservation plus shape discrimination
* Naive threshold counting fails all heldouts by 80 to 130 percent over or 30 to 50 percent under
* Global conservation without speck and round pore removal fails speck heavy and shape cases by more than 3 percent because detached round pores and specks contribute extra energy
* Shape discrimination is required: long narrow keyhole channels that count versus round gas pores that must be ignored. Largest mass may be round pore, so largest mass shortcut fails
* Expected difficulty: avocado 0/5 to 2/5, gpt 1/5, opus 2/5 - similar to foundry thermal void which has 0/5 avocado. Harder than simple sphere tasks due to binary parsing with varied data offset plus shape filter
* int16 dtype path exercised via heldout 2 to ensure both dtype branches work

## Anti Cheating
* No numpy, scipy, imaging libraries - from scratch only
* No hardcoded sample volume, must work on any random temp file path
* Do not open or list /tests directory
* From scratch guard bans os, io, pathlib etc
* Secure verifier generates heldouts at runtime in temp dir and runs solver in isolated sandbox with audit hook blocking /tests, test outputs, heldout, _gen etc
* Banned import check via AST in test_from_scratch
