# codimango/confocal-gold-subvoxel-volume

## Description

The agent writes a **from-scratch** Python script (`/app/solve.py`, stdlib only) that reads a custom confocal fluorescence volume (`.gvol`, magic `GVOL`) of a resected tissue sample labeled with gold nanocluster tumor marker and reports true physical tumor volume in cubic millimetres. Script takes scan path as first argument and prints volume as final number on stdout.

Clinical oncology scenario for intraoperative dosing: gold nanoclusters make tumor cells fluoresce brightly under confocal, but the microscope's Airy disk and tissue scattering spread that fluorescence far beyond the true margin. The raw stack shows a large fuzzy glowing cloud, but the true tumor that would be measured under ideal deconvolved optics is smaller with thin infiltrating strands that never appear fully bright. Low threshold counting includes huge diffuse glow overcounting 88 to 128 percent, high threshold misses infiltrating strands undercounting 30 to 50 percent, and no fixed cutoff is stable across samples because gold amount, autofluorescence background, voxel pitch, and PSF width change per scan.

Precise recovery requires full physics reasoning from raw bytes, not bright voxel counting. A naive numpy plus scipy.ndimage.label threshold one-shot is both forbidden by the from-scratch guard and wrong by more than 12 percent at 3 percent tolerance. The correct physics-informed reconstruction must robustly estimate background without tumor bias, isolate main gold mass from far dust artefacts, estimate interior concentrated brightness despite blur and noise, and grow to include faint diffusion halo without merging specks. Honest reconstruction lands under 1 percent error.

> Calibration: threshold shortcuts are 12-35 percent off, genuine reconstruction <1 percent at 3 percent tolerance.

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

Forces multi-step clinical image reasoning from raw bytes without array libraries:

* **GVOL parsing:** little-endian binary with magic GVOL, version, dtype 2=int16 16=float32, dimensions nx ny nz, anisotropic voxel pitch sx sy sz mm, data offset. X fastest index `x + nx*(y+ny*z)`. From-scratch guard rejects numpy, scipy, skimage, cv2, PIL, networkx, etc plus pathlib and glob.
* **Autofluorescence background:** tissue autofluorescence dominates voxel count, appears as flat constant plus symmetric uniform noise. Robust median and MAD over lower half needed to avoid tumor bias.
* **Gold dust filtering:** isolated bright specks far from main lesion are manufacturing artefacts. Must keep gold mass with greatest total residual, using 26-neighbour flood fill, not largest voxel count.
* **Concentrated brightness:** core saturated value is never directly observable after Airy blur plus noise. Requires 3D mean filtering over main mass and top few peak average, not simple maximum.
* **Diffuse glow inclusion:** faint Airy disk halo still belongs to tumor and carries significant total signal. Adaptive shell growth outward until ring average falls to noise floor, stopping before bridging to distant specks.
* **Anisotropic volume:** final mm3 uses per-scan pitch read from header. Thin infiltrating strands are partial volume and cannot be recovered by any fixed threshold; only total energy aware reconstruction stays within 3 percent.

Measured on 4 generated configs: low threshold plus largest CC 88 to 128 percent over, best fixed absolute 31 percent worst, best fraction of true amplitude 12 percent worst, half max and Otsu 18 to 35 percent off. Physics-informed method 0.19 to 0.99 percent per scan.

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
