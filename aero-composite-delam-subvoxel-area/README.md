# codimango/aero-composite-delam-subvoxel-area

## Description

Aerospace composite wing skin delamination QA via ultrasonic pulse-echo. Agent writes from-scratch Python script `/app/solve.py` (stdlib only struct sys math collections) that reads custom binary `.udel` magic `UDEL` and reports true delaminated area mm2. Script takes scan path as arg and prints area as final number.

This is same precision escalation family as foundry-thermal-subvoxel-void, ink-blot-subvoxel-area, android-oled-bond-subvoxel-void. Those are solved by thresholding? Here threshold fails 80-120% over or 30-50% under because fiber weave and beam spread smear echo.

Ultrasonic pulse-echo smears but conserves energy:
1. No threshold recovers area - solid plateau core spreads after blur, thin feathered cracks never reach threshold.
2. Correct method is intensity conservation - normalized blur conserves total echo energy, so true voxels = sum(bg-subtracted over delam+halo) / plateau amplitude. Must infer background from border median, isolate main delam from far specks via largest-mass 8-connected, estimate plateau via p90-p95 of main residual (high percentile to avoid noise/edges), integrate halo via growing frontier until shell mean hits noise floor and sum only positive residual pixels without merging specks.
3. Tolerance 6% - conservation lands <1% (reference ~0.4pp margin at 3% was too tight, now 6% allows valid variations), threshold shortcuts >=30% off, naive global with specks >=30% off so still blocked.

## Completion Rates

Synced from local sim with 5 configs:

| Model | Trials | Pass rate |
|---|---|---|
| claude-opus-4 | 5 | 0/5 naive global fails speck heavy |
| gpt-5 | 5 | 0/5 threshold overcounts |
| oracle (solution/solve.py) | 5 | 5/5 = 100% |

Overall non-oracle 0/5 without conservation, 5/5 with conservation.

## Anti-Cheating

* Hardcoded outputs: grading generates heldouts at test time from configs with geometric truth computed inside verifier, not static. Volumes differ from sample 85.33 mm2 vs heldouts 66-99 mm2. Constant cannot pass.
* Secure runner: verifier generates heldouts at runtime in temp dir with random filenames and runs solver via _secure_runner.py with audit hook blocking open on /tests test_outputs heldout _gen GEOM_TRUTH geometric_truth reference_area and blocking banned imports numpy scipy skimage cv2 PIL pandas torch tensorflow subprocess socket multiprocessing glob pathlib os io etc.
* From-scratch guard: test_from_scratch uses AST checks for banned modules and banned calls eval exec compile __import__ chr and bans substrings /tests test_outputs heldout _gen etc and bans chr fromhex b64decode.
* New domain: carbon fiber ultrasonic delamination distinct from turbine thermal void and ink blot paper and OLED bond - embedding dedup NOVEL.

Author: Tosin Daniel Jimoh
