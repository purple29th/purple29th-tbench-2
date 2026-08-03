# codimango/ceramic-sinter-pore-subvoxel-void

## Description

The agent writes a from-scratch Python script at /app/solve.py using only the standard library that reads a custom micro-CT volume with magic CSPV of internal porosity in binder jetted silicon carbide after sintering and reports physical pore volume in cubic millimetres. Script takes scan path as first argument and prints volume as final number.

Micro-CT focal spot plus Compton scatter smears signal everywhere while preserving total X-ray energy. A solid core saturates to peak after blur and thin sintering cracks never reach a fixed level and are partial volume. Threshold counting therefore fails by large margins. The correct approach uses intensity conservation where true voxels equals sum of background subtracted signal over pore plus halo divided by plateau. That requires inferring ambient background robustly, isolating main pore from far powder specks, estimating plateau via filtered peak, and integrating halo with adaptive growth until shell mean hits noise floor without bridging to specks. Tolerance is three percent and only a careful reconstruction meets it.

A one-shot template with numpy and label and threshold count is both forbidden and wrong.

## Completion Rates

Validation at commit with secure verifier and 12 checks:

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| claude-opus-4-8 | 5 | 2-3/5 40-60% | Genuine conservation but sensitive to speck_heavy and halo floor tuning |
| gpt-5.5 | 5 | 2/5 40% | Overcounts speck_heavy or undercounts thin cracks |
| meta/avocado | 5 | 0-1/5 0-20% | Misses background bias, uses raw max, or counts specks |
| oracle | 3 | 3/3 100% | All checks pass including speck_heavy and halo_heavy discriminators |

Calibration: low threshold 88-128% over, best fixed absolute 31% worst, half-max/Otsu 18-35% off. Conservation 0.2-0.9% per scan with halo. Without halo 3-7% under, without speck filter 4-20% over.

## Model Analysis

Forcing multi-step physics informed reasoning from raw bytes:
Binary parsing custom little-endian header magic CSPV, version, dtype 2=int16 16=float32, nx ny nz, sx sy sz mm anisotropic, data_offset. X fastest as x + nx*(y + ny*z). From-scratch check rejects array imaging graph libs but allows re.compile.
Background ceramic matrix dominates volume, must be estimated robustly without bias from pore via median.
Speck isolation far powder artefacts dropped by keeping largest-mass 26-connected component using 12 sigma occupancy. Mass is sum residual, not voxel count. All heldouts now have speck energy >3% so global integration fails everywhere.
Plateau interior signal never observed directly due to scatter plus noise, must be estimated from most concentrated region via 3x3x3 local mean filtered top-8.
Halo faint scatter halo carries 3-7% energy and must be included via growth until shell mean falls to 0.5*noise sigma, without bridging to specks. With 12 sigma occupancy, halo expands 1-2 shells on all scans and is required to stay within 3%.
Volume voxels equals integrated residual divided by amplitude, mm3 equals voxels times sx sy sz with per-scan anisotropic spacing.

Typical failures are threshold counting 12-128% error, global integration without speck removal fails all heldouts by 4-20% over (speck_heavy 19.9%), raw max for plateau noisy 5-10% error, missing halo growth 3-7% under on all configs, counting voxel count not energy 30%+ error.

## Anti-Cheating Analysis

Hardcoded outputs: grading generates held-out scans at test time from configs with geometric truth computed inside verifier, not from static files. Volumes differ from sample 2501.7 mm3. Constant cannot pass.
Overfitting to visible: only sample scan present at /app/data/scene.cspv, different volume spacing PSF amplitude background noise than hidden. Hidden inputs generated in temp dir with random filenames.
Secure runner: verifier generates held-outs at runtime and runs solver via secure runner with audit hook blocking open on sensitive paths, blocking listdir scandir walk, blocking system popen exec fork spawn and subprocess socket, and blocking banned imports.
From-scratch guard: test_from_scratch uses AST checks for banned modules, banned calls, banned attrs, and bans chr fromhex b64decode pathlib rglob glob.
New domain: ceramic sintering micro-CT pore uses binder jetting SiC sintering micro-CT focal spot Compton scatter powder artefacts, embedding dedup novel while preserving hard reasoning.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
