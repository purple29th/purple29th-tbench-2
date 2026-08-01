# codimango/android-periscope-prism-glue-void-subvoxel-volume

## Description

Agent writes from-scratch Python at /app/solve.py using only stdlib that reads a custom micro-CT volume with magic APCV of glue voids in Android flagship periscope telephoto prism bonding and reports physical void volume in mm3. Script takes scan path as first arg and prints volume as final number.

Periscope uses right-angle glass prism glued to lens barrel with UV adhesive; entrapped air forms sealed voids causing OIS drift and flare. 160kV micro-focus X-ray plus scintillator spread plus glass scatter smears signal while preserving total energy. Solid core saturates to peak after blur and thin glue fingers along prism edge never reach fixed level due to partial volume. Threshold counting therefore fails. Correct method is intensity conservation where true voxels = sum(bg-subtracted over void+halo) / plateau. Requires inferring background robustly, isolating main void from far dust specks via largest-mass 26-connected, estimating plateau via filtered peak, integrating halo with adaptive growth until shell mean hits noise floor without bridging to specks. Tolerance 3% and only careful reconstruction meets it.

One-shot numpy template with threshold count is both forbidden and wrong.

## Completion Rates

Validation at commit with secure verifier and 5 checks:
Internal oracle: scene truth vs solver error <1% on all heldouts including speck_heavy discriminator.
Calibration: low threshold 88-130% over, best fixed absolute 30% worst, half-max/Otsu 18-36% off. Conservation 0.5-1.1% per scan.

Expected difficulty hard, genuine conservation required.

## Model Analysis

Binary parsing custom little-endian header magic APCV, version, dtype 2=int16 16=float32, nx ny nz, sx sy sz mm anisotropic, data_offset. X fastest. From-scratch check rejects array imaging graph libs.
Background glass matrix dominates volume, must be estimated robustly without bias from void.
Speck isolation far dust artefacts dropped by keeping largest-mass 26-connected component. Mass is sum residual, not voxel count.
Plateau interior signal never observed directly due to scatter plus noise, must be estimated from most concentrated region via local mean filter.
Halo faint scatter halo carries significant energy and must be included via growth until shell mean hits noise floor, without bridging to specks.
Volume voxels = integrated residual / amplitude, mm3 = voxels*sx*sy*sz with per-scan anisotropic spacing.

Typical failures: threshold counting 12-130% error, global integration without speck removal fails speck_heavy by 20%+ over, raw max for plateau noisy 5-10% error, missing halo growth 15-25% under.

## Anti-Cheating Analysis

Hardcoded outputs: grading generates held-out scans at test time from configs with geometric truth computed inside verifier, not from static files. Volumes differ from sample. Constant cannot pass.
Overfitting to visible: only sample scan present at /app/data/scene.apcv, different volume/spacing/PSF/amplitude/background/noise than hidden generated scans. Hidden inputs generated in temp dir with random filenames.
Secure runner: verifier generates held-outs at runtime and runs solver via secure runner with audit hook blocking open on sensitive paths, blocking listdir scandir walk, blocking system popen exec fork spawn and subprocess socket, and blocking banned imports.
From-scratch guard: test_from_scratch uses AST checks for banned modules, banned calls, banned attrs, bans chr fromhex b64decode pathlib rglob glob.

New domain: Android periscope prism glue bond void uses flagship telephoto periscope, right-angle glass prism, UV-cure adhesive, OIS drift, flare, distinct from OLED bond despite same physics core.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
