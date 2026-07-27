# codimango/confocal-gold-subvoxel-volume

## Description

The agent writes a **from-scratch** Python script (`/app/solve.py`, standard library only) that reads a custom confocal fluorescence volume (`.gvol`, magic `GVOL`) of a tumor labeled with gold nanoclusters and reports its physical volume in cubic millimetres. The script takes the scan path as first argument and prints volume as final number on stdout.

This is the **precision escalation** of `mri-volume-calc` and `android-depth-object-volume`. Those tasks are solved by thresholding to a bright mask and counting largest connected component voxels. **Here that approach is wrong by 20–130%.**

Gold labeling makes the tumor a concentrated bright mass, but the confocal microscope Airy disk point-spread function smears that concentrated light everywhere. Three consequences:

1. **No threshold recovers volume.** Solid core saturates to a peak amplitude after blur, but thin infiltrating strands have partial-volume intensity never reaching any usable threshold. Counting thresholded voxels either misses thin strands (cut too high) or balloons halo (cut too low). No static rule works across scans.

2. **Correct method is intensity conservation via most concentrated area.** A normalized blur conserves total fluorescence, so true voxel count is `sum(intensity - background over object+halo) / plateau_amplitude`. The agent must infer background, isolate main tumor from far gold dust specks, estimate interior plateau where gold is most concentrated (most concentrated area), and integrate over halo.

3. **Tighter tolerance.** Grading at **3%** vs 5% in family. Conservation method lands <1%; threshold shortcuts are >=12% off.

A one-shot template (numpy + scipy.ndimage.label + threshold-count) is both forbidden and wrong, making task resistant to recall.

## Completion Rates

Sync'd from validation at commit 79c0488 (15 trials + 3 oracle):

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| `claude-opus-4-8` | 5 | 4/5 = 80% | Conservation solutions |
| `gpt-5.5` | 5 | 4/5 = 80% | Conservation solutions |
| `meta/avocado-5.14-code` | 5 | 1/5 = 20% | 1 PASSED, 4 incomplete / wrong |
| `oracle` (golden `solution/solve.py`) | 3 | 3/3 = 100% | Validates grader |

Overall: 9/15 = 60% non-oracle passes, indicating real insight needed.

> **Calibration target:** models reaching for family threshold-and-count solution or numpy one-shot fail here; only genuine intensity-conservation derivation passes. Dominant expected failure is *counting thresholded voxels instead of integrating conserved intensity*.

## Model Analysis

The task forces multi-step physics-informed reasoning from raw bytes:

* **Binary parsing:** custom little-endian header with magic GVOL, version, dtype code 2=int16 16=float32, nx ny nz, sx sy sz mm per axis anisotropic, data_offset. X-fastest indexing. From-scratch check rejects numpy/scipy/imaging/graph libs plus pathlib, glob, etc.
* **Background inference:** background dominates volume, must be estimated robustly without bias from tumor itself. Flat constant bg plus symmetric uniform noise, robust median/MAD needed to reject tumor outliers.
* **Speck isolation:** far gold dust artefacts must be dropped by keeping largest-mass 26-connected component, not largest voxel count.
* **Plateau amplitude:** interior value never observed directly due to blur+noise; must be estimated from most concentrated region via filtered peak, not naive max.
* **Halo integration:** faint Airy halo still carries gold signal and must be included via adaptive growth until shell mean hits noise floor, without bridging to specks.
* **Volume calc:** voxels = integrated residual / amplitude; mm3 = voxels * sx * sy * sz with per-scan anisotropic spacing.

Threshold strategies measured on sample+3 heldouts: threshold@200 + largest CC = 88-128% over, best fixed absolute threshold = 31% worst-case, best fixed fraction of amplitude (true bg and amp given) = 12% worst-case, half-max and Otsu = 18-35% off. Conservation = 0.19-0.99% per scan.

## Anti-Cheating Analysis

* **Hardcoded outputs:** grading generates held-out scans at test time from configs with geometric truth computed inside verifier, not from static files. Volumes (3977.5, 3983.36, 4428.0 mm3 plus randomized extras) differ from sample (3206.3 mm3). Constant fails. No hardcoded GEOM_TRUTH dict with filenames parseable by solver; truth is derived from field generation.
* **Overfitting to visible:** only sample scan in agent container at `/app/data/scene.gvol`, different volume/spacing/PSF/amplitude/bg/noise than hidden generated scans. Hidden inputs are generated in temp dir with random filenames and passed to solver, not byte-identical to any committed file. `tests/data/heldout_*.gvol` no longer used by verifier.
* **Secure runner:** verifier runs solver via `_secure_runner.py` with `sys.addaudithook` blocking any `open()` of paths containing `/tests`, `test_outputs`, `heldout`, `reference`, `_gen`, `/app/data`, `scene.gvol`, `GEOM_TRUTH`, `geometric_truth`, `reference_volume`, plus blocking `os.listdir/scandir/walk` on sensitive dirs and blocking `os.system/popen/exec/fork/spawn` and `subprocess/socket` events. Audit also blocks banned imports `numpy/scipy/skimage/cv2/PIL/pandas/torch/tensorflow/subprocess/socket/multiprocessing/glob/pathlib`. This defeats the previously reported reward hack that read `/tests/test_outputs.py` for hardcoded truths and iterated `/tests/data` via `pathlib.Path`.
* **From-scratch guard:** `test_from_scratch()` uses AST checks for banned modules including `pathlib`, banned calls `eval/exec/compile/__import__/chr/getattr/setattr`, banned attrs `system/popen/exec/fork/walk/listdir/scandir/rglob/__subclasses__` etc, plus case-insensitive substring and compact-token checks for `/tests`, `test_outputs`, `heldout`, `reference`, `_gen`, `scene.gvol`, `/app/data`, `GEOM_TRUTH`, `geometric_truth`, `reference_volume`, and explicit bans on `chr()`, `fromhex`, `b64decode`, `base64`, `pathlib`, `rglob`, `glob(` to prevent obfuscation.
* **Bypassing intended path:** numpy one-shot and threshold-and-count both pass from-scratch but fail every hidden generated case by 80-130%+.

Author: Tosin Daniel Jimoh <purple29th@meta.com>

## Fix Log
* 2026-07-23: Fixed TBR FAIL test_deps_not_in_image by removing numpy/scipy from Dockerfile (stdlib-only verifier), reference uses geometric truth 3977.5/3983.36/4428.0 mm3
* 2026-07-27: Fixed Needs Revision reward hack per raheel@meta.com. Rewrote `tests/test_outputs.py` to secure verifier pattern: generate heldouts in temp dir with random filenames, compute geometric truth at runtime, run solver in isolated sandbox with audit hook blocking /tests, /app/data, heldout, reference, _gen, scene.gvol, GEOM_TRUTH, pathlib, glob, chr obfuscation. Added explicit banned list to `instruction.md` and hardened `test_from_scratch()`. Verified oracle passes 7/7 and exploit `Path("/tests/data").iterdir()` + `open("/tests/test_outputs.py")` now blocked at AST and runtime.
