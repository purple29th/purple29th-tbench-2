# codimango/aero-composite-delam-subvoxel-area

## Description

Aerospace composite wing skin delamination QA via ultrasonic pulse-echo. Agent writes from-scratch Python script `/app/solve.py` (stdlib only struct sys math collections) that reads custom binary `.udel` magic `UDEL` and reports true delaminated area mm2. Script takes scan path as arg and prints area as final number.

Threshold fails 80-120% over or 30-50% under because fiber weave and beam spread smear echo. No single cutoff works across files because gain and diffusion width change.

Ultrasonic pulse-echo smears but conserves energy:
1. No threshold recovers area - solid plateau core spreads after blur, thin feathered cracks never reach threshold.
2. Correct method is intensity conservation - normalized blur conserves total echo energy, so true voxels = sum(bg-subtracted over delam+halo) / plateau amplitude. Must infer background from border median to avoid delam bias, isolate main delam from far specks via largest-mass 8-connected, estimate plateau via high percentile of main residual to avoid noise edges, integrate halo via growing frontier until shell mean hits noise floor and sum only positive residual pixels without merging specks.
3. Tolerance 6% - conservation lands <1% with room for valid estimator variation, threshold shortcuts >=30% off, naive global with specks >=30% off so still blocked.
4. Header data offset varies 64-128 and version varies 1/2, parser must respect offset.

## Completion Rates

Real validation on commit 4cd8865 (current):

| Model | Trials | Pass rate | Notes |
|---|---|---|---|
| claude-opus-4-8 | 5 | 4/5 | fails heldout_3 by 3.43% near miss |
| meta-avocado-5.14-code | 5 | 4/5 | fails heldout_2 by 3.02% near miss |
| gpt-5.5 | 5 | 2/5 | fails 3 cases by 3-8% |
| oracle (solution/solve.py) | 3 | 3/3 = 100% | passes all within 1% |

Overall non-oracle 10/15 = 66% with conservation method, 0/5 without. Tolerance 6% gives margin for valid estimator variation as reviewer requested. Previous 0/5 table was stale from local sim.

## Model Analysis

Opus and Avocado both implemented intensity conservation correctly and failed only by 0.04 to 0.43 points near 3% line before tolerance loosened to 6%, now passes 4/5 each. GPT fails more often due to halo/plateau calibration. Only genuine conservation method passes, threshold shortcuts fail all.

## Anti-Cheating

* Hardcoded outputs: grading generates heldouts at test time from configs with geometric truth computed inside verifier, not static. Volumes differ from sample 85.33 mm2 vs heldouts 66-99 mm2. Constant cannot pass.
* Secure runner: verifier generates heldouts at runtime in temp dir with random filenames and runs solver via _secure_runner.py with audit hook blocking open on /tests test_outputs heldout _gen GEOM_TRUTH geometric_truth reference_area and blocking banned imports numpy scipy skimage cv2 PIL pandas torch tensorflow subprocess socket multiprocessing glob pathlib os io etc.
* From-scratch guard: test_from_scratch uses AST checks for banned modules and banned calls eval exec compile __import__ chr and bans substrings /tests test_outputs heldout _gen etc and bans chr fromhex b64decode.
* Header enforcement: data offset varies per file, hardcoding 64 fails.

Author: Tosin Daniel Jimoh
