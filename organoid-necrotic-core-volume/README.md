# codimango/organoid-necrotic-core-volume

## Description

Agent writes a **from-scratch** Python script (`/app/solve.py`, stdlib only) that reads a custom light-sheet fluorescence volume (`.oncr`, magic `ONCR`) of a cortical organoid necrotic core and reports physical necrotic volume in cubic micrometers. Script takes scan path as first arg and prints volume as final number.

Cerebral organoids form dead cores due to oxygen diffusion limits. Propidium iodide stains dead cells bright, but tissue scattering plus light-sheet PSF smears glow:

1. **No threshold recovers volume** — solid core saturates to plateau after scattering, thin necrotic fingers into cortical plate never reach threshold. Low cut 80-130% over, high cut 30-50% under.
2. **Correct method is fluorescence conservation via most concentrated region** — normalized blur conserves total photon energy, so true voxels = sum(bg-subtracted over core+halo) / plateau. Must isolate main core from far apoptotic debris via largest-mass 26-connected, estimate autofluorescence background without bias, estimate saturated PI plateau via filtered peak, integrate halo until noise floor.
3. **Tighter tolerance 3%** — conservation lands <1.2%, threshold shortcuts >=12% off.

A numpy + threshold template is both forbidden (no numpy/scipy/os/io/pathlib) and wrong.

## Completion Rates

Local oracle validation (11 checks):

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| `oracle` (golden `solution/solve.py`) | 3 | 3/3 = 100% | Validates grader, all 11 checks pass, errors 0.10-1.09% vs 3% tol |
| `claude-threshold-template` | — | 0% expected | Low thr 88-128% over, high thr 31% under, Otsu 18-35% off |
| `naive-global-conservation` | — | fail speck_heavy | Global integral includes debris specks >3% energy |

> Calibration: threshold-and-count fails 80-130% over or 30-50% under; only genuine conservation with robust background, plateau, 26-connected main component isolation (by mass not area), and halo growth to noise floor without merging specks passes within 3 percent. Speck heavy case main discriminator where debris total charge comparable to main but lower per speck, area larger than main, brightness up to 1.5x plateau.

## Model Analysis

Forcing multi-step physics-informed reasoning from raw bytes:
* **Binary parsing:** custom little-endian header magic ONCR, version, dtype 2=int16 16=float32, nx ny nz, sx sy sz um per axis anisotropic, data_offset. X-fastest. From-scratch check rejects numpy/scipy/imaging/graph libs and os/io/pathlib/socket/multiprocessing.
* **Background:** autofluorescence dominates volume, must be estimated via median lower half MAD without bias from bright core.
* **Speck isolation:** far apoptotic debris dropped by keeping largest-mass 26-connected component (mass = sum residual). Area-based selection fails because debris area may exceed core.
* **Plateau:** saturated PI level never observed directly due to scattering+noise; must be estimated from most concentrated region via 3x3x3 local mean filtered peak top-8 mean, not raw max.
* **Halo:** faint scattering halo carries significant energy especially when sig_xy large (2.5-2.7) and noise high, must be included via adaptive growth until shell mean hits 1*sigma floor, without bridging to specks. Skipping halo undercounts by > tolerance.
* **Volume:** voxels = integrated residual / plateau amplitude; um3 = voxels*sx*sy*sz with per-scan anisotropic spacing read from header.

Threshold strategies measured on sample+3 heldouts: low threshold 88-128% over, best fixed absolute 31% worst, best fraction of amplitude 12% worst, half-max/Otsu 18-35% off. Conservation 0.10-1.09% per scan.

## Anti-Cheating Analysis

* **Hardcoded outputs:** grading generates held-out scans at test time from configs with geometric truth computed inside verifier (field = blurred+bg+(rng-0.5)*2*ns), not from static files. Volumes (5207, 3526, 5561 um3 plus randomized extra and speck heavy 5207) differ from sample (3500 um3). Constant cannot pass.
* **Overfitting to visible:** only sample scan present at `/app/data/scene.oncr`. Hidden inputs generated in temp dir with random filenames `input_<hex>.oncr` not byte-identical to committed file.
* **Secure runner:** verifier generates scans at runtime and runs solver via `_secure_runner.py` with `sys.addaudithook` blocking `open()` on paths containing `/tests`, `test_outputs`, `heldout`, `_gen`, `GEOM_TRUTH`, `geometric_truth`, `reference_volume`, blocking `os.listdir/scandir/walk` on `/tests`, blocking `os.system/popen/exec/fork/spawn` and `subprocess/socket` events, plus blocking banned imports `numpy/scipy/skimage/cv2/PIL/pandas/torch/tensorflow/subprocess/socket/multiprocessing/glob/pathlib/os/io/posixpath/ntpath/genericpath`. Does NOT block `/app/data/scene.oncr`, so sample readable but hardcoding its volume fails hidden checks.
* **From-scratch guard:** `test_from_scratch()` AST checks for banned modules including `os/io/pathlib/socket/multiprocessing`, banned calls `eval/exec/compile/__import__/chr`, banned attrs `system/popen/exec/fork/walk/listdir/scandir/rglob/__subclasses__` etc, plus substring checks for `/tests`, `test_outputs`, `heldout`, `_gen`, `GEOM_TRUTH`, `geometric_truth`, `reference_volume`, and bans `chr(`, `fromhex`, `b64decode`, `base64`, `pathlib`, `rglob`, `glob(`, `import os`. Instruction.md banned list synced.
* **New domain:** Cortical organoid necrotic core with PI staining, light-sheet microscopy, tissue scattering, cortical plate finger extensions, hypoxia oxygen diffusion modeling — distinct from foundry thermal, ink blot paper, display capacitive, fingerprint optical, ToF, etc. embedding dedup NOVEL.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
