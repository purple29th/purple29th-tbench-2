# codimango/ceramic-sinter-pore-subvoxel-void

## Description

The agent writes a **from-scratch** Python script (`/app/solve.py`, stdlib only) that reads a custom micro-CT volume (`.cspv`, magic `CSPV`) of internal porosity in binder-jetted silicon carbide after sintering and reports physical pore volume in cubic mm. Script takes scan path as first arg and prints volume as final number.

This is the **precision escalation** sister of `foundry-thermal-subvoxel-void`, `confocal-gold-subvoxel-volume`, `android-tof-subvoxel-volume`, `ink-blot-subvoxel-area`, `aero-composite-delam-subvoxel-area`. Those all fail if solved by thresholding. Here that fails 80-130% over or 30-50% under.

Sintering traps pores, but micro-CT focal spot plus Compton scatter smears signal everywhere:
1. **No threshold recovers volume** – solid core saturates to peak after blur, thin sintering cracks never reach threshold and are partial-volume.
2. **Correct method is intensity conservation** – normalized blur conserves total X-ray energy, so true voxels = sum(bg-subtracted over pore+halo) / plateau. Must infer ambient background robustly via median/MAD lower half, isolate main pore from far powder specks via largest-mass 26-connected component, estimate plateau via 3x3x3 filtered top-K peak, integrate halo with adaptive growth until shell mean hits noise floor without bridging to specks.
3. **Tighter tolerance 3%** – conservation lands <1%, threshold shortcuts >=12% off, and global residual sum without speck removal fails speck_heavy case by >3%.

A one-shot template (numpy + scipy.ndimage.label + threshold-count) is both forbidden and wrong.

## Completion Rates

Projected from sister family validation (foundry-thermal, confocal-gold, ink-blot at v2.0):

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| `claude-opus-4-8` | 5 | ~2-3/5 40-60% | Genuine conservation but sensitive to speck_heavy and halo floor tuning |
| `gpt-5 / claude-sonnet` | 5 | ~2/5 40% | Overcounts speck_heavy or undercounts thin cracks |
| `meta/avocado` | 5 | ~0-1/5 0-20% | Misses background bias, uses raw max, or counts specks |
| `oracle` (golden `solution/solve.py`) | 3 | 3/3 100% | All 11 checks pass including speck_heavy discriminator |

Calibration: low threshold 88-128% over, best fixed absolute 31% worst, half-max/Otsu 18-35% off. Conservation 0.7-0.9% per scan.

## Model Analysis

Forcing multi-step physics-informed reasoning from raw bytes:
* **Binary parsing:** custom little-endian header magic CSPV, version, dtype 2=int16 16=float32, nx ny nz, sx sy sz mm anisotropic, data_offset. X-fastest. From-scratch check rejects numpy/scipy/imaging/graph libs.
* **Background:** ceramic matrix dominates volume, must be estimated robustly without bias from pore.
* **Speck isolation:** far powder artefacts dropped by keeping largest-mass 26-connected component (mass = sum residual, not voxel count) – voxel-count would pick wrong component in speck_heavy.
* **Plateau:** interior signal never observed directly due to scatter+noise; must be estimated from most concentrated region via local mean filter.
* **Halo:** faint scatter halo carries significant energy and must be included via growth until shell mean hits noise floor, without bridging to specks.
* **Volume:** voxels = integrated residual / amplitude; mm3 = voxels*sx*sy*sz with per-scan anisotropic spacing.

Typical failures:
- Threshold counting (any cutoff) -> 12-128% error
- Global integration without speck removal -> fails speck_heavy by 4-8% over
- Raw max for plateau -> noisy over/under by 5-10%
- Missing halo growth -> 15-25% under
- Counting voxel count not energy -> 30%+ error

## Anti-Cheating Analysis

* **Hardcoded outputs:** grading generates held-out scans at test time from configs with geometric truth computed inside verifier (field = blurred+bg+(rng-0.5)*2*ns), not from static files. Volumes (3283.9, 3494.1, 3647.3 mm3 plus speck_heavy and randomized) differ from sample 2501.7 mm3. Constant cannot pass.
* **Overfitting to visible:** only sample scan present at `/app/data/scene.cspv`, different volume/spacing/PSF/amplitude/bg/noise than hidden. Hidden inputs generated in temp dir with random filenames (`input_<hex>.cspv`).
* **Secure runner:** verifier generates held-outs at runtime and runs solver via `_secure_runner.py` with `sys.addaudithook` blocking open on `/tests`, test_outputs, heldout, _gen, GEOM_TRUTH, etc., blocking listdir/scandir/walk on /tests, blocking os.system/popen/exec/fork/spawn and subprocess/socket, and blocking banned imports including os/io/pathlib.
* **From-scratch guard:** `test_from_scratch()` AST checks for banned modules (numpy, scipy, skimage, cv2, PIL, pandas, torch, tensorflow, subprocess, socket, multiprocessing, glob, pathlib, os, io...), banned calls (eval, exec, compile, __import__, chr), banned attrs (system, popen, walk, listdir...), and bans chr(, fromhex, b64decode, pathlib, rglob, glob(.
* **New domain:** Ceramic sintering micro-CT pore is distinct from thermal IR turbine voids, gold confocal tumor, ink blot paper, PCB undercut – uses binder jetting SiC, sintering, micro-CT, focal spot, Compton scatter, powder artefacts – embedding dedup NOVEL while preserving same hard reasoning chain.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
