# codimango/sintered-silver-die-attach-void-subvoxel-volume

## Description

The agent writes a from-scratch Python script (/app/solve.py, stdlib only) that reads a custom nano-focus X-ray CT volume (.ssdv, magic SSDV) of solvent outgassing voids in sintered silver die attach for SiC power modules and reports true sealed void volume in cubic mm. Script takes scan path as first arg and prints volume as final number.

Nano-focus X-ray imaging spreads void signal: Phoenix tube focal spot plus scintillator plus scatter in dense Ag/Cu creates normalized anisotropic blur conserving total counts, so threshold counting fails 80 to 130 percent over or 30 to 50 percent under:

1. No threshold recovers volume - void core saturates to plateau after blur, thin vent channels where gas tried to escape to die edge never reach threshold.
2. Correct method is energy conservation - normalized blur conserves total energy, so true voxels equals sum(background subtracted over void plus halo) divided by plateau. Must infer background silver level without bias, isolate main void from far organic inclusions via largest-mass 26-connected component, estimate plateau via filtered top-K, integrate halo via adaptive growth until shell mean hits noise floor without bridging specks.
3. Tighter tolerance 3 percent - conservation lands under 1 percent, threshold shortcuts are 12 percent or more off.

A one-shot template (numpy plus threshold count) is both forbidden and wrong.

## Completion Rates

Sync'd from validation at commit eaa07eb1 (9 checks, local and server):

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| claude-opus-4-8 | 5 | 5/5 = 100% | Robust conservation with halo growth and speck filter |
| gpt-5.5 | 5 | 5/5 = 100% | Direct residual-energy pipeline, plateau via filtered top-K |
| meta/avocado-5.14-code | 5 | 3/5 = 60% | 1 incomplete no solve.py, 1 numerical miss overcounts specks / undercounts int16 |
| oracle (golden solution/solve.py) | 3 | 3/3 = 100% | Validates grader, all 9 checks pass |

Overall non-oracle 13/15 ~86.7 percent. At generation time with opus-4-6/gpt-5 baseline was ~35 percent, indicating genuinely hard at the time. After frontier upgrade to opus-4-8/gpt-5.5 frontier now aces the physics pipeline, so discrimination rests on avocado robustness to speck isolation, int16 parsing, and halo floor tuning.

> Calibration: threshold and count fails 80 to 130 percent over or 30 to 50 percent under; only genuine conservation with robust background, plateau, 26-connected isolation, and halo growth passes within 3 percent. Speck heavy case is main discriminator. Global integration without speck removal fails speck_heavy by 4-8 percent over, raw max for plateau 5-10 percent error, missing halo 15-25 percent under.

## Model Analysis

Forcing multi-step physics informed reasoning from raw bytes:
* Binary parsing: custom little endian header magic SSDV, version, dtype 2=int16 16=float32, nx ny nz, sx sy sz mm per voxel anisotropic (now sx != sy != sz enforced), data offset. X fastest. From-scratch check rejects numpy scipy imaging graph libs.
* Background: silver matrix dominates volume, must be estimated robustly via median plus MAD without bias from void. Must use lower half to avoid bubble bias.
* Speck isolation: far organic inclusions and unsintered paste clumps dropped by keeping largest-mass 26-connected component, mass equals sum residual not voxel count. Speck energy tuned >3 percent to force filter.
* Plateau: interior signal never observed directly due to blur plus noise; must be estimated from most concentrated region via 3x3x3 filtered top-K mean to avoid noise spike.
* Halo: faint X-ray halo carries 3-7 percent energy and must be included via adaptive growth until shell mean hits noise floor, without bridging to far specks. Required on wide scatter configs.
* Volume: voxels equals integrated residual divided by amplitude; mm3 equals voxels times sx times sy times sz with per-scan anisotropic spacing, now exercised with distinct axes.

Threshold strategies: low threshold 80 to 130 percent over, half-max Otsu 18 to 35 percent off. Conservation 0.2 to 0.98 percent per scan on hidden configs.

## Anti-Cheating Analysis

* Hardcoded outputs: grading generates held-out scans at runtime from configs with geometric truth computed inside verifier (field equals blurred plus bg plus deterministic noise), not from static files. Volumes differ from sample 0.0137 mm3, so constant cannot pass.
* Overfitting to visible: only sample scan at /app/data/scene.ssdv, different volume and spacing and blur than hidden scans. Hidden inputs generated in temp dir with random filenames input_<hex>.ssdv and not byte identical to committed file.
* Secure runner: verifier generates held-out scans at runtime in temporary directory with random filenames and runs solver via _secure_runner.py with sys.addaudithook blocking open on paths containing /tests, test_outputs, heldout, _gen, GEOM_TRUTH, geometric_truth, reference_volume, blocking os.listdir scandir walk on /tests, blocking os.system popen exec fork spawn and subprocess socket events, plus blocking banned imports.
* From-scratch guard: test_from_scratch uses AST checks for banned modules, calls, attrs, substring and compact-token checks, bans chr( fromhex b64decode.
* Domain novelty: sintered silver die attach uses SiC power modules, DBC copper, Henkel ABLESTIK pressure sintering, solvent burnout outgassing, thin vent legs to die edge, organic residue inclusions, junction to case thermal resistance rise in power cycling - embedding distinct from generic pore tasks while preserving hard reasoning.

## Fix Log

* v0.1: initial, oracle 3/3 PASS, structural 10 PASS
* v0.2: fixed instruction formatting to plain ASCII no backticks no em dashes, removed grey code highlighting
* v0.3: fixed README to 4 sections with completion rates and anti-cheating, made spacing fully anisotropic sx != sy != sz in all configs to enforce sx*sy*sz multiplication.
* v0.4: updated completion rates to current wave eaa07eb1 - opus-4-8 5/5, gpt-5.5 5/5, avocado 3/5 (86.7% non-oracle), clarified frontier now aces and discrimination rests on avocado; removed sibling task references per policy.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
