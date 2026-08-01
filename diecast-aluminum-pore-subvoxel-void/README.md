# codimango/diecast-aluminum-pore-subvoxel-void

## Description

The agent writes a from-scratch Python script at /app/solve.py using only the standard library that reads a custom industrial CT volume with magic ADPV of internal hydrogen gas porosity in high-pressure die-cast aluminum EV inverter housings and reports physical pore volume in cubic millimetres. Script takes scan path as first argument and prints volume as final number.

225 kV cone-beam tube focal spot plus flat-panel scintillator spread and scatter inside thick Al wall smears signal while preserving total photon count energy. A sealed bubble core saturates to peak after blur and thin shrinkage dendrite channels never reach a fixed level due to partial volume. Threshold counting therefore fails by large margins. The correct approach uses intensity conservation where true voxels equals sum of background subtracted signal over pore plus halo divided by plateau. That requires inferring ambient aluminum background robustly, isolating main pore from far microporosity specks, estimating plateau via filtered peak, and integrating halo with adaptive growth until shell mean hits noise floor without bridging to specks. Tolerance is three percent and only a careful reconstruction meets it.

A one-shot template with numpy and label and threshold count is both forbidden and wrong.

## Completion Rates

Validation left for ensyte per author request. Local avocado testing skipped intentionally. Oracle reference implemented with stdlib-only conservation matching geometric truth within <1% on sample and heldouts.

Calibration from sibling physics model (same generator family, different domain):
- Threshold low 88-128% over, best fixed absolute 31% worst, half-max/Otsu 18-35% off.
- Conservation 0.7-0.9% per scan.
- Speck heavy case discriminates global integration.

Expected difficulty: hard, genuine conservation required.

## Model Analysis

Forcing multi-step physics informed reasoning from raw bytes:
Binary parsing custom little-endian header magic ADPV, version, dtype 2=int16 16=float32, nx ny nz, sx sy sz mm anisotropic, data_offset. X fastest. From-scratch check rejects array imaging graph libs.
Background aluminum matrix dominates volume, must be estimated robustly without bias from pore.
Speck isolation far microporosity artefacts dropped by keeping largest-mass 26-connected component. Mass is sum residual, not voxel count.
Plateau interior signal never observed directly due to scatter plus noise, must be estimated from most concentrated region via local mean filter.
Halo faint scatter halo carries significant energy and must be included via growth until shell mean hits noise floor, without bridging to specks.
Volume voxels equals integrated residual divided by amplitude, mm3 equals voxels times sx sy sz with per-scan anisotropic spacing.

Typical failures are threshold counting 12-128% error, global integration without speck removal fails speck_heavy by 4-8% over, raw max for plateau noisy 5-10% error, missing halo growth 15-25% under, counting voxel count not energy 30%+ error.

## Anti-Cheating Analysis

Hardcoded outputs: grading generates held-out scans at test time from configs with geometric truth computed inside verifier, not from static files. Volumes differ from sample 2610.9 mm3. Constant cannot pass.
Overfitting to visible: only sample scan present at /app/data/scene.adpv, different volume spacing PSF amplitude background noise than hidden. Hidden inputs generated in temp dir with random filenames.
Secure runner: verifier generates held-outs at runtime and runs solver via secure runner with audit hook blocking open on sensitive paths, blocking listdir scandir walk, blocking system popen exec fork spawn and subprocess socket, and blocking banned imports.
From-scratch guard: test_from_scratch uses AST checks for banned modules, banned calls, banned attrs, and bans chr fromhex b64decode pathlib rglob glob.
New domain: aluminum high-pressure die-cast hydrogen gas porosity uses HPDC AlSi10Mg hydrogen precipitation gas entrapment industrial CT cone-beam scintillator spread, embedding dedup novel while preserving hard reasoning.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
