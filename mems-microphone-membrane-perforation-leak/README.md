# MEMS Microphone Membrane Perforation Leak

## Summary
I work on MEMS microphone factory line. Acoustic membrane has micro perforations that leak air and hurt SNR. X ray shows bright leaks but blurred by X ray PSF, so leak looks larger and fuzzier than true size.

This task requires a from scratch Python script that parses custom binary .mems and reports true leak volume in mm3.

## Why This Is Hard
X ray blur makes threshold counting imprecise. Low cutoff includes huge halo and overcounts by 80 to 130 percent. High cutoff misses thin perforation that never gets bright enough and undercounts by 30 to 50 percent. No fixed cutoff works across files because brightness and blur width change.

Correct method is intensity conservation. Total X ray signal is conserved despite blur. So true leak voxels equals sum of background subtracted intensity divided by plateau intensity.

To make it work you must separate main leaks from far specks and round dust voids using 26 neighbour connectivity plus shape filtering. Elongated perforation leaks along membrane count, round dust voids must be ignored. Estimate background without bias from leaks, estimate true plateau intensity without being fooled by noise, and decide how far faint halo extends without merging specks or round voids. That is the hard part.

## Approach
Similar to other precision void tasks, you need to:
* Parse header respecting data offset, do not hardcode 64
* Keep only main elongated leaks, ignore far dust specks and round voids via shape
* Estimate background from border voxels far from leak
* Estimate plateau from core flat region top percentile mean
* Integrate halo with conservation and recover volume scaling by sx sy sz from header

Method works for varied dimensions, spacings, brightness, blur widths.

## Files
* /app/solve.py is file agent must create, prints volume as last word
* /app/data/scene.mems is sample for local dev
* environment/Dockerfile installs python and pytest
* tests/test_outputs.py is evaluation suite

## Model Analysis / Completion Rate

* Oracle 11/11 100 percent - reference solution passes all heldouts within 1 percent via intensity conservation plus shape discrimination
* Naive threshold counting fails all heldouts by 80 to 130 percent over or 30 to 50 percent under
* Global conservation without speck and round void removal fails speck heavy and shape cases by more than 3 percent because detached round voids and dust specks contribute extra energy
* Shape discrimination is required: elongated perforation leaks that count versus round dust voids that must be ignored. Largest mass may be round void, so largest mass shortcut fails
* Expected difficulty: avocado 0/5 to 2/5, gpt 1/5, opus 2/5 - similar to foundry thermal void which has 0/5 avocado. Harder than simple sphere tasks due to binary parsing with varied data offset plus shape filter
* int16 dtype path exercised via heldout 2 to ensure both dtype branches work

## Anti Cheating
* No numpy, scipy, imaging libraries - from scratch only
* No hardcoded sample volume, must work on any random temp file path
* Do not open or list /tests directory
* From scratch guard bans os, io, pathlib etc
* Secure verifier generates heldouts at runtime in temp dir and runs solver in isolated sandbox with audit hook blocking /tests, test outputs, heldout, _gen etc
* Banned import check via AST in test_from_scratch
