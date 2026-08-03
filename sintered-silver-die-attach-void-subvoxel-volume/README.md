# codimango/sintered-silver-die-attach-void-subvoxel-volume

## Description

The agent writes a from-scratch Python script (/app/solve.py, stdlib only) that reads a custom nano-focus X-ray CT volume (.ssdv, magic SSDV) of solvent outgassing voids in sintered silver die attach for SiC power modules and reports true sealed void volume in cubic mm. Script takes scan path as first arg and prints volume as final number.

This is the precision escalation of diecast-aluminum-pore-subvoxel-void and ceramic-sinter-pore-subvoxel-void. Those can be approximated by thresholding, here that fails 80 to 130 percent over or 30 to 50 percent under.

Nano-focus X-ray imaging spreads void signal: tube focal spot plus scintillator plus scatter in Ag/Cu creates normalized anisotropic blur conserving total counts:

1. No threshold recovers volume - void core saturates to plateau after blur, thin vent channels never reach threshold.
2. Correct method is energy conservation - normalized blur conserves total energy, so true voxels equals sum(background subtracted over void plus halo) divided by plateau. Must infer background silver level without bias, isolate main void from far organic inclusions via largest-mass 26-connected component, estimate plateau via filtered top-K, integrate halo via adaptive growth until shell mean hits noise floor without bridging specks.
3. Tighter tolerance 3 percent - conservation lands under 1 percent, threshold shortcuts are 12 percent or more off.

A one-shot template (numpy plus threshold count) is both forbidden and wrong.

## Completion Rates

Sync'd from validation at commit c9c0a25 (9 checks, local and server):

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| claude-opus-4-6 | 5 | 2/5 = 40% | 2 fails overcount halo plus speck heavy |
| gpt-5 | 5 | 2/5 = 40% | 2 fails include speck heavy energy |
| meta/avocado-5.14-code | 5 | 1/5 = 20% | 3 incomplete, 1 overcounts halo |
| oracle (golden solution/solve.py) | 3+3 | 3/3 = 100% and 3/3 = 100% | Validates grader, all 9 checks pass |

Overall non-oracle around 35 percent, indicating genuinely hard. Oracle 100 percent confirms solvable.

> Calibration: threshold and count fails 80 to 130 percent over or 30 to 50 percent under; only genuine conservation with robust background, plateau, 26-connected isolation, and halo growth passes within 3 percent. Speck heavy case is main discriminator.

## Model Analysis

Forcing multi-step physics informed reasoning from raw bytes:
* Binary parsing: custom little endian header magic SSDV, version, dtype 2=int16 16=float32, nx ny nz, sx sy sz mm per voxel anisotropic (now sx != sy != sz enforced), data offset. X fastest. From-scratch check rejects numpy scipy imaging graph libs.
* Background: silver matrix dominates volume, must be estimated robustly via median plus MAD without bias.
* Speck isolation: far organic inclusions dropped by keeping largest-mass 26-connected component, mass equals sum residual not voxel count.
* Plateau: interior signal never observed directly due to blur plus noise; must be estimated from most concentrated region via 3x3x3 filtered top-K mean.
* Halo: faint X-ray halo carries signal and must be included via adaptive growth until shell mean hits noise floor, without bridging to specks.
* Volume: voxels equals integrated residual divided by amplitude; mm3 equals voxels times sx times sy times sz with per-scan anisotropic spacing, now exercised with distinct axes.

Threshold strategies: low threshold 80 to 130 percent over, half-max Otsu 18 to 35 percent off. Conservation 0.2 to 0.98 percent per scan.

## Anti-Cheating Analysis

* Hardcoded outputs: grading generates held-out scans at runtime from configs with geometric truth computed inside verifier (field equals blurred plus bg plus deterministic noise), not from static files. Volumes differ from sample 0.0137 mm3, so constant cannot pass.
* Overfitting to visible: only sample scan at /app/data/scene.ssdv, different volume and spacing and blur than hidden scans. Hidden inputs generated in temp dir with random filenames input_<hex>.ssdv and not byte identical to committed file.
* Secure runner: verifier generates held-out scans at runtime in temporary directory with random filenames and runs solver via _secure_runner.py with sys.addaudithook blocking open on paths containing /tests, test_outputs, heldout, _gen, GEOM_TRUTH, geometric_truth, reference_volume, blocking os.listdir scandir walk on /tests, blocking os.system popen exec fork spawn and subprocess socket events, plus blocking banned imports.
* From-scratch guard: test_from_scratch uses AST checks for banned modules, calls, attrs, substring and compact-token checks, bans chr( fromhex b64decode.
* New domain: sintered silver die attach outgassing void is distinct from diecast aluminum pore and ceramic sinter pore - uses SiC power modules, pressure sintering, solvent burnout gas, organic inclusions, junction to case thermal resistance - embedding dedup NOVEL.

## Fix Log

* v0.1: initial, oracle 3/3 PASS, structural 10 PASS
* v0.2: fixed instruction formatting to plain ASCII no backticks no em dashes, removed grey code highlighting
* v0.3: fixed README to 4 sections with completion rates and anti-cheating, made spacing fully anisotropic sx != sy != sz in all configs to enforce sx*sy*sz multiplication.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
