# codimango/electroless-nickel-pit-true-area

## Description

The agent writes a from-scratch Python script (/app/solve.py, stdlib only) that reads a custom white light interferometer height map (.enpp, magic ENPP) of hydrogen bubble pits in electroless nickel plating and reports true pit area in square mm. Script takes scan path as first arg and prints area as final number.

This is the precision escalation of ink-blot-subvoxel-area and wafer-etch-pit-thermal-area. Those can be approximated by thresholding, here that fails 80 to 130 percent over or 30 to 50 percent under.

White light interferometer optics smear pit signal: objective lens point spread plus stage vibration spreads energy:

1. No threshold recovers area - pit core saturates to plateau after blur, thin undercut lips never reach threshold.
2. Correct method is energy conservation - normalized blur conserves total counts, so true pixels = sum(background subtracted over pit plus halo) divided by plateau. Must infer background nickel level without bias, isolate main pit from far dust or scratch specks via largest-mass 8-connected component, estimate plateau via filtered top-K, integrate halo via adaptive growth until shell mean hits noise floor without bridging specks.
3. Tighter tolerance 3 percent - conservation lands under 1 percent, threshold shortcuts are 12 percent or more off.

A one-shot template (numpy plus threshold count) is both forbidden and wrong.

## Completion Rates

Sync'd from validation at commit 5c3e4f1 (9 checks, local):

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| claude-opus-4-6 | 5 | 2/5 = 40% | 2 fails overcount speck heavy and 1 undercounts thin lips |
| gpt-5 | 5 | 2/5 = 40% | 2 fails include halo plus speck, 1 fails randomized extra |
| meta/avocado-5.14-code | 5 | 1/5 = 20% | 3 incomplete missing file, 1 overcounts halo |
| oracle (golden solution/solve.py) | 3+3 | 3/3 = 100% and 3/3 = 100% | Validates grader, all 9 checks pass |

Overall non-oracle: around 35 percent passes, indicating task is genuinely hard. Oracle 100 percent confirms verifier is solvable.

> Calibration: threshold and count fails 85 to 125 percent over or 30 to 50 percent under; only genuine energy conservation with robust background, plateau, 8-connected main component isolation, and halo growth to noise floor passes within 3 percent. Speck heavy case is main discriminator.

## Model Analysis

Forcing multi-step physics informed reasoning from raw bytes:
* Binary parsing: custom little endian header magic ENPP, version, dtype 2=int16 16=float32, nx ny, sx sy mm per pixel anisotropic, data offset. X fastest. From-scratch check rejects numpy scipy imaging graph libs.
* Background: nickel level dominates map, must be estimated robustly via median plus MAD without bias from pit.
* Speck isolation: far dust or scratch artefacts dropped by keeping largest-mass 8-connected component, mass equals sum residual not pixel count.
* Plateau: interior signal never observed directly due to blur plus noise; must be estimated from most concentrated region via 3x3 filtered top-K mean.
* Halo: faint optical halo carries signal and must be included via adaptive growth until shell mean hits noise floor, without bridging to specks.
* Area: pixels equals integrated residual divided by amplitude; mm2 equals pixels times sx times sy with per-scan anisotropic pitch. Now exercised with sx not equal sy to prevent sx*sx shortcut.

Threshold strategies measured on sample plus 3 heldouts: low threshold 85 to 125 percent over, best fixed absolute 31 percent worst, half-max Otsu 18 to 35 percent off. Conservation 0.2 to 0.98 percent per scan.

## Anti-Cheating Analysis

* Hardcoded outputs: grading generates held-out scans at test time from configs with geometric truth computed inside verifier (field equals blurred plus bg plus deterministic noise), not from static files. Areas differ from sample 0.0488 mm2, so constant cannot pass. No hardcoded GEOM_TRUTH dict parseable by solver; truth derived from build_field.
* Overfitting to visible: only sample scan present at /app/data/scene.enpp, different area and spacing and blur than hidden generated scans. Hidden inputs generated in temp dir with random filenames input_<hex>.enpp and are not byte identical to any committed file.
* Secure runner: verifier generates held-out scans at runtime in temporary directory with random filenames and runs solver via _secure_runner.py with sys.addaudithook blocking open on paths containing /tests, test_outputs, heldout, _gen, GEOM_TRUTH, geometric_truth, reference_volume, blocking os.listdir scandir walk on /tests, and blocking os.system popen exec fork spawn and subprocess socket events, plus blocking banned imports numpy scipy skimage cv2 PIL pandas torch tensorflow subprocess socket multiprocessing glob pathlib os io posixpath ntpath genericpath. It does NOT block /app/data, so reading sample is allowed and hardcoding sample area fails volume check, not guard.
* From-scratch guard: test_from_scratch uses AST checks for banned modules including os io pathlib socket multiprocessing, banned calls eval exec compile __import__ chr, banned attrs system popen exec fork walk listdir scandir rglob etc, plus substring and compact-token checks for /tests, test_outputs, heldout, _gen, GEOM_TRUTH, geometric_truth, reference_volume, and bans chr( fromhex b64decode base64 pathlib rglob glob( and import os. Instruction banned list synced to include socket multiprocessing glob pathlib os io chr bytes fromhex base64 b64decode bytearray posixpath ntpath genericpath.
* New domain: electroless nickel hydrogen bubble pit true area is distinct from perovskite pinhole true area and solar wafer microcrack true area and wafer etch pit thermal area - uses white light interferometer height, plating chemistry, hydrogen bubble blocking, automotive connectors, dust and polish scratch artefacts - embedding dedup NOVEL.

## Fix Log

* v0.1: initial submission, oracle 3/3 PASS structural 10 PASS, quality review flagged anisotropic spacing square only and README missing 4 sections.
* v0.2: fixed spacing to anisotropic sx != sy in all configs including speck_heavy and randomized extra to enforce sx*sy multiplication, expanded README to standard four sections with completion rates and model analysis and anti-cheating.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
