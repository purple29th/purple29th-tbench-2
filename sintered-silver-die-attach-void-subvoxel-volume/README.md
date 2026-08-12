# codimango/sintered-silver-die-attach-void-subvoxel-volume

## Description

The agent writes a from-scratch Python script (/app/solve.py, stdlib only) that reads a custom nano-focus X-ray CT volume (.ssdv, magic SSDV) of solvent outgassing voids in sintered silver die attach for SiC power modules and reports true sealed void volume in cubic mm. Script takes scan path as first arg and prints volume as final number.

Nano-focus X-ray imaging spreads void signal: Phoenix tube focal spot plus scintillator plus scatter in dense Ag/Cu creates normalized anisotropic blur conserving total counts, so threshold counting fails 80 to 130 percent over or 30 to 50 percent under:

1. No threshold recovers volume - void core saturates to plateau after blur, thin vent channels where gas tried to escape to die edge never reach threshold.
2. Correct method is energy conservation - normalized blur conserves total energy, so true voxels equals sum(background subtracted over void plus halo) divided by plateau. Must infer background silver level without bias, isolate main void from far organic inclusions via largest-mass 26-connected component, estimate plateau via filtered top-K, integrate halo via adaptive growth until shell mean hits noise floor without bridging specks.
3. Tighter tolerance 3 percent - conservation lands under 1 percent, threshold shortcuts are 12 percent or more off.

A one-shot template (numpy plus threshold count) is both forbidden and wrong.

## Completion Rates

Sync'd from validation at commit eaa07eb1 and re-validated after fix at 795e423412 (11 checks, local and server):

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| claude-opus-4-8 | 5 | 5/5 = 100% | Robust conservation with halo growth and speck filter |
| gpt-5.5 | 5 | 5/5 = 100% | Direct residual-energy pipeline, plateau via filtered top-K |
| meta/avocado-5.14-code | 5 | 3/5 = 60% | 1 incomplete no solve.py, 1 numerical miss overcounts specks / undercounts int16 |
| oracle (golden solution/solve.py) | 5 | 5/5 = 100% | Validates grader, all 11 checks pass (8 secure + 1 extra + 2 existence) |

Overall non-oracle 13/15 ~86.7 percent. At generation time with opus-4-6/gpt-5 baseline was ~35 percent, indicating genuinely hard at the time. After frontier upgrade to opus-4-8/gpt-5.5 frontier now aces the physics pipeline, so discrimination rests on avocado robustness to speck isolation, int16 parsing, halo floor tuning, and mass vs count.

> Calibration: threshold and count fails 80 to 130 percent over or 30 to 50 percent under; only genuine conservation with robust background, plateau, 26-connected isolation, and halo growth passes within 3 percent. Speck heavy case is main discriminator. Global integration without speck removal fails speck_heavy by 4-8 percent over, pixel-count trap fails count-based by 130 percent over while mass-based passes within 1 percent, raw max for plateau trap 26 percent error vs filtered top-K 1.8 percent, missing halo 2-4 percent under on wide scatter configs.

## Model Analysis

Forcing multi-step physics informed reasoning from raw bytes:
* Binary parsing: custom little endian header magic SSDV, version, dtype 2=int16 16=float32, nx ny nz, sx sy sz mm per voxel anisotropic (now sx != sy != sz enforced), data offset. X fastest. From-scratch check rejects numpy scipy imaging graph libs.
* Background: silver matrix dominates volume, must be estimated robustly via median plus MAD without bias from void. Must use lower half to avoid bubble bias.
* Speck isolation: far organic inclusions and unsintered paste clumps dropped by keeping largest-mass 26-connected component, mass equals sum residual not voxel count. Speck energy tuned greater than 3 percent to force filter. Pixel-count trap uses large faint speck with many voxels 4765 vs main 4423 but low mass due to 0.2 amplitude scale, so mass-based picks main while count-based picks speck with 130 percent over.
* Plateau: interior signal never observed directly due to blur plus noise; must be estimated from most concentrated region via 3x3x3 filtered top-K mean to avoid noise spike. Plateau trap has conserved hot spike plus 400 at void core with energy redistributed to 26 neighbors preserving total counts, so raw max 1600 vs filtered 1195, diff 33 percent, giving raw-max volume error 26 percent vs filtered 1.8 percent.
* Halo: faint X-ray halo now real after fix. Wider sig_xy 3.0 to 3.2 and lower amp 700 to 900 with noise 15 gives 1 shell with 2 to 3 percent energy, up to 4 percent on halo_heavy, exercised in 4 configs. Previously halo growth was dead code with 0 shells on every config. Now missing halo causes 2 to 4 percent under, sufficient to fail 3 percent tolerance on wide configs.
* Volume: voxels equals integrated residual divided by amplitude; mm3 equals voxels times sx times sy times sz with per-scan anisotropic spacing, now exercised with distinct axes.

Threshold strategies: low threshold 80 to 130 percent over, half-max Otsu 18 to 35 percent off. Conservation 0.2 to 1.3 percent per scan on hidden configs after fix.

## Anti-Cheating Analysis

* Hardcoded outputs: grading generates held-out scans at runtime from configs with geometric truth computed inside verifier (field equals blurred plus bg plus deterministic noise plus optional conserved hot spike), not from static files. Volumes differ from sample 0.0137 mm3, so constant cannot pass.
* Overfitting to visible: only sample scan at /app/data/scene.ssdv, different volume and spacing and blur than hidden scans. Hidden inputs generated in temp dir with random filenames input_<hex>.ssdv and not byte identical to committed file.
* Secure runner: verifier generates held-out scans at runtime in temporary directory with random filenames and runs solver via _secure_runner.py with sys.addaudithook blocking open on paths containing /tests, test_outputs, heldout, _gen, GEOM_TRUTH, geometric_truth, reference_volume, blocking os.listdir scandir walk on /tests, blocking os.system popen exec fork spawn and subprocess socket events, plus blocking banned imports.
* From-scratch guard: test_from_scratch uses AST checks for banned modules, calls, attrs, substring and compact-token checks, bans chr fromhex b64decode. Fixed false positives per review: removed walk listdir scandir rglob from BANNED_ATTRS which collided with user helper Grid.walk(), and removed /tests from string-literal ban which flagged docstring containing phrase from instruction. Security still enforced by audit hook and module bans.
* Calibration author checks: global conservation shortcut and pixel-count shortcut validations moved to author_side_checks.py not counted in grading. They verify naive methods fail by 15 percent and 130 percent respectively.
* Domain novelty: sintered silver die attach uses SiC power modules, DBC copper, Henkel ABLESTIK pressure sintering, solvent burnout outgassing, thin vent legs to die edge, organic residue inclusions, junction to case thermal resistance rise in power cycling - embedding distinct from generic pore tasks while preserving hard reasoning.

## Fix Log

* v0.1: initial, oracle 3/3 PASS, structural 10 PASS
* v0.2: fixed instruction formatting to plain ASCII no backticks no em dashes, removed grey code highlighting
* v0.3: fixed README to 4 sections with completion rates and anti-cheating, made spacing fully anisotropic sx != sy != sz in all configs to enforce sx*sy*sz multiplication.
* v0.4: updated completion rates to current wave eaa07eb1 - opus-4-8 5/5, gpt-5.5 5/5, avocado 3/5 (86.7% non-oracle), clarified frontier now aces and discrimination rests on avocado; removed sibling task references per policy.
* v0.5: review fixes - promoted radius-12 speck config to ALL_TEST_CONFIGS as pixel_count_trap with faint 0.2 scale so mass-based passes and count-based fails 130 percent, made halo real by widening sig_xy to 3.0-3.2 and lowering amp to 700-900 with noise 15 giving 1 shell 2-3 percent, added plateau_trap with conserved hot spike plus 400 giving raw max 33 percent over filtered and volume error 26 percent vs 1.8 percent, added halo_heavy, narrowed BANNED_ATTRS removing walk listdir scandir rglob to avoid false positive on Grid.walk(), removed /tests from string literal ban, moved calibration tests to author_side_checks.py, refreshed README to 11 checks and corrected halo and raw-max numbers.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
