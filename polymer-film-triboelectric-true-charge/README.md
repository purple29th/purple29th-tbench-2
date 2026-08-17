# polymer-film-triboelectric-true-charge

## Summary
Polymer film QC via Kelvin probe surface potential mapping. Triboelectric charging during roll-to-roll creates elongated charged patches along draw direction that attract dust. Custom binary `.trch` (magic `TRCH`) holds 2D charge map where signal is smeared by probe diffusion + lens PSF. Task: recover total patch charge in nanoCoulombs (nC).

This is a precision measurement where threshold counting fails 70-120% over or 30-50% under. Only intensity conservation with shape discrimination passes within 3%.

## Why Non-Volume Charge Task
Output is surface charge in nC, not mm³ volume or mm² area alone. Calibration 1.5 nC per mm² converts recovered area to charge, but grading checks charge. Domain is polymer ESD surface charge recovered from a 2D areal scan.

## Approach
* Parse header respecting data_offset
* Keep main elongated tribo patch, ignore round static dots via aspect ratio (longest>=10 and >1.6x shortest)
* Estimate background via median, noise via MAD lower half
* Estimate plateau from most concentrated region via 3x3 filtered top-8 mean
* Integrate halo via growth until shell mean hits noise floor, excluding round artefacts
* Charge = pixel_count * sx*sy * 1.5 nC/mm²

## Files
* `/app/solve.py` prints charge nC
* `/app/data/scene.trch` sample
* `environment/Dockerfile` python+pytest
* `tests/test_outputs.py` secure verifier generating heldouts at runtime

## Completion Criteria
Charge error <3% on heldouts including speck-heavy and round-artefact cases. Threshold fails all. Global conservation without filtering fails speck-heavy >3%. Largest-mass shortcut without shape filter fails when round artefact outweighs thin patch.

## Expected Difficulty
* Oracle 100%
* Naive threshold 0%
* Global without filter 0% on speck_heavy
* Frontier baseline: gpt 1-2/5, opus 2/5, avocado 0-1/5

## Anti-Cheating
* Stdlib only, no numpy/scipy/imaging
* No hardcoded sample charge
* Secure verifier with audit hook blocking /tests, test_outputs, heldout, _gen etc
* AST banned import check
