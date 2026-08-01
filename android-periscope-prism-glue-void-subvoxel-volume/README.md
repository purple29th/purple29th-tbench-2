# Android Periscope Prism Glue Void - Subvoxel Volume

## Overview

This task checks an Android flagship periscope telephoto camera module for adhesive air pockets. At the Seoul line, a large glass prism is UV-glued to the plastic barrel; trapped air after cure leads to OIS drift and flare in final image QA. The line uses 160 kV micro-focus cone-beam CT to screen modules.

Relevant physics: finite focal spot plus scintillator bleed plus scatter inside thick prism acts as a normalized anisotropic low-pass. Total integrated excess over background stays constant, but energy is spread into a wide halo, so the bubble appears much larger than reality.

Input is custom binary `.apcv` (magic `APCV`) with anisotropic voxel pitch `sx sy sz` in mm, dimensions `nx ny nz`, dtype int16 (2) or float32 (16), x-fastest, contrast inverted so voids appear bright. Task delivers volume in cubic mm as last token of stdout. Only the principal sealed pocket counts; far dust specks on prism facet must be ignored. A simple bright-voxel count over-estimates by ~2x (halo) or under-estimates by ~0.5x (thin glue tails along chamfer) and no universal cutoff works because tube brightness, glass absorption, smear width and noise floor drift per lot.

The intended solver exploits conservation: `true_voxels = sum(background_subtracted over void+halo) / plateau`. Achieving 3% relative error demands careful handling of background bias, noise level, dust exclusion via largest integrated residual under 26-connectivity, plateau estimation from most concentrated region, and inclusive halo growth until shell mean drops to noise without bridging to distant specks.

Templated numpy + label + threshold counting is both forbidden by from-scratch guard and wrong physically.

## Validation

Secure verifier generates held-out volumes at test time with random temporary filenames, varied grid, pitch, amplitude, background, PSF, noise. Sample at `/app/data/scene.apcv` only ~560 mm3, heldouts 795/820/931 mm3 plus speck_heavy and randomized, all anisotropic.

Oracle: stdlib-only conservation with median lower-half baseline, MAD noise, largest-mass 26-connected isolation, 3x3x3 mean-filter plateau top-8, halo growth to noise floor. Measured <1.1% per scan.

Negative controls:
- Low cutoff includes halo → 88-130% over
- Best fixed absolute → 30% worst
- Half-max/Otsu → 18-36% off
- Global sum without speck removal → speck_heavy fails by 20%+ over
- Missing halo growth → 15-25% under

Tolerance 3% sits in empty band between ~1% (any sound conservation) and >=12% (any counting shortcut).

## Anti-Cheating Hardening

- No generator `_gen.py` mounted in grading bundle; geometric truth recomputed inside verifier
- `solve.py` executed in isolated `TemporaryDirectory` with neutral scan name, `PYTHONPATH=td`, audit hook blocks open on `/tests`, `test_outputs`, `heldout`, `_gen`, `GEOM_TRUTH`, `geometric_truth`, `reference_volume`, blocks `listdir/scandir/walk`, blocks `system/popen/exec/fork/spawn` and `subprocess/socket`, blocks banned imports
- `test_from_scratch` AST bans `numpy/scipy/skimage/cv2/PIL/pandas/torch/tensorflow/subprocess/socket/multiprocessing/glob/pathlib/os/io/posixpath/ntpath/genericpath` and calls `eval/exec/compile/__import__/chr`, bans `chr(`, `fromhex`, `b64decode`, `base64`, `pathlib`, `rglob`, `glob(`
- Hardcoded volume blocked: sample 560.7 mm3 differs from hidden; hidden files random names in temp dir

New domain uses Android periscope telephoto, right-angle glass prism, UV glue, OIS drift, flare — embedding dedup distinct from ceramic sinter SiC despite same conservation physics; ceramic uses spark plasma sintering, SiC armor, Compton scatter, powder artefacts. This task is periscope prism glue void.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
