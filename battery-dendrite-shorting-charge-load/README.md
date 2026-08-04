# battery-dendrite-shorting-charge-load

## Summary
Battery failure analysis via X-ray fluorescence separator imaging. Lithium dendrites grow across separator and trap metallic lithium, creating shorting risk. Custom binary `.ldch` (magic `LDCH`) holds 3D fluorescence volume where dendrite signal is smeared by diffusion plus lens PSF. Task: recover total trapped charge in milliCoulombs (mC).

This is a precision measurement task where threshold counting fails 80-130% over or 30-50% under. Only intensity conservation with shape discrimination passes within 3% tolerance.

## Why Creative (Not Volume/Area)
Output is charge load in mC, not geometric volume in mm³ or area in mm². Calibration 2.8 mC per mm³ converts recovered volume to charge, but grading checks charge directly. This evaluates same physics (energy conservation) in a different domain (battery safety) with additional shape discrimination (elongated dendrites vs round plating artefacts).

## Approach
Similar to precision void tasks but with Li dendrite specifics:
* Parse header respecting data_offset (do not hardcode 64 for future proofing, though current gen uses 64)
* Keep main elongated dendrite structures, ignore round plating artefacts via aspect ratio filter (longest >=8 voxels and >1.6x shortest)
* Estimate background from border voxels far from dendrite via median
* Estimate plateau from core flat region via top percentile mean
* Integrate halo with conservation until shell mean hits noise floor, without merging plating specks
* Charge = voxel_count * sx*sy*sz * 2.8 mC/mm³

Method works for varied dimensions, spacings, brightness, blur widths, and densities.

## Files
* `/app/solve.py` - agent must create, prints charge mC as last word
* `/app/data/scene.ldch` - sample for local dev
* `environment/Dockerfile` - installs python and pytest
* `tests/test_outputs.py` - evaluation suite with secure runtime generation

## Completion Criteria
Tests pass when charge error <3% on heldouts including speck-heavy and plating-artefact cases. Threshold counting fails all heldouts. Global conservation without speck/plating removal fails speck-heavy by >3% because detached dust/plating contributes extra energy. Largest-mass shortcut without shape filter fails plating-heavy where round artefacts outweigh thin dendrite tips.

## Expected Difficulty
* Oracle 100% - reference solution via conservation + shape filter + halo growth
* Naive threshold 0% - 80-130% over / 30-50% under
* Global conservation without filtering 0% on speck_heavy/plating cases
* Expected similar to foundry-thermal and pcb-undercut: gpt 1-2/5, opus 2/5, avocado 0-1/5

## Anti-Cheating
* No numpy/scipy/imaging libs - from scratch only
* No hardcoded sample charge, must work on random temp file paths
* Do not open/list /tests
* From-scratch guard bans os, io, pathlib etc
* Secure verifier generates heldouts at runtime in temp dir with random filenames and runs solver in isolated sandbox with audit hook blocking /tests, test_outputs, heldout, _gen etc
* Banned import check via AST
