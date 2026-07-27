# codimango/ink-blot-subvoxel-area

## Description

The agent writes a **from-scratch** Python script (`/app/solve.py`, stdlib only) that reads a custom capillary ink blot scan (`.inkb`, magic `INKB`) on porous paper and reports true inked area in square mm. Script takes scan path as first arg and prints area as final number.

This is the **area** version of `android-tof-subvoxel-volume` and `confocal-gold-subvoxel-volume` and `foundry-thermal-subvoxel-void` – same sweet spot but 2D calculus: threshold counting overcounts halo 80-130% or undercounts thin feathered wicking 30-50%, no fixed cutoff works across different paper porosity, ink darkness, pixel pitch.

Ink drop wicks via capillary diffusion plus lens PSF smears darkness everywhere, so true inked area is not recoverable by counting dark pixels. **Correct method is intensity conservation via most concentrated area (calculus integration):** `area_pixels = sum(bg-subtracted over blot+halo) / plateau_darkness`, `mm2 = pixels*sx*sy`. Agent must infer paper background, isolate main blot from far dust specks via largest-mass 8-connected component, estimate plateau darkness via filtered peak, integrate halo.

Threshold shortcuts are 12-35% off, conservation <1%.

A numpy one-shot is both forbidden and wrong.

## Completion Rates

Sync'd from validation at commit 72e84de (15 trials + oracle):

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| `claude-opus-4-8` | 5 | 2/5 = 40% | Conservation solutions, 3 failures incomplete/threshold |
| `gpt-5.5` | 5 | 4/5 = 80% | 4 passes, 1 fail |
| `meta/avocado-5.14-code` | 5 | 1/5 = 20% | 1 pass, 4 fails |
| `oracle` (golden `solution/solve.py`) | 3 | 3/3 = 100% | Validates grader |

Overall non-oracle: 7/15 = 46.7% passes, showing real difficulty vs pulse task.

> Calibration target: threshold-and-count fails 80-130% over or 30-50% under; only genuine intensity-conservation passes <1% error. Grading at 3% tolerance.

## Model Analysis

Forces multi-step calculus reasoning from raw bytes:
* **Binary parsing:** custom little-endian header magic INKB, version, dtype 2=int16 16=float32, nx ny, sx sy mm per pixel anisotropic, data_offset. X-fastest. From-scratch bans numpy/scipy/imaging/graph libs plus pathlib/glob etc.
* **Background:** flat paper background `bg` plus symmetric uniform noise `(rng-0.5)*2*noise` (no drift). Robust median/MAD over full image needed to reject blot/dust outliers.
* **Speck isolation:** far dust specks dropped by largest-mass 8-connected component above noise, not largest voxel count.
* **Plateau:** interior darkness hidden by diffusion+noise; 3x3 mean-filtered peak over blot needed, not naive max.
* **Halo:** faint capillary diffusion halo carries conserved ink signal, adaptive growth until shell mean hits noise floor, without bridging to specks.
* **Area calc:** pixels = integrated residual / amplitude; mm2 = pixels*sx*sy with per-scan anisotropic pixel size.

Threshold strategies measured on 5 generated configs: low thr 88-128% over, best fixed absolute 31% worst, best fixed fraction of amplitude 12% worst, half-max/Otsu 18-35% off. Conservation 0.19-0.99% per scan.

## Anti-Cheating Analysis

* **Hardcoded outputs:** grading generates 5 held-out scans at test time from configs with geometric truth computed inside verifier (`field = blurred+bg+(rng-0.5)*2*ns`), not from static files. Areas differ from sample (6.04 mm2) and from each other (e.g. heldouts ~12.36, 6.21, 10.10 mm2 plus extra large_blot and random_feather). Constant or sample-memorized value fails. No hardcoded GEOM_TRUTH dict parseable by solver.
* **Overfitting to visible:** only sample scan present in agent container at `/app/data/scene.inkb`, with different area/spacing/PSF/amplitude/bg/noise than hidden generated scans. Hidden inputs are generated in temp dir with random filenames (`input_<hex>.inkb`) and are not byte-identical to any committed file.
* **Secure runner:** verifier runs solver via `_secure_runner.py` with `sys.addaudithook` blocking `open()` on paths containing `/tests`, `test_outputs`, `heldout`, `reference`, `_gen`, `/app/data`, `scene.inkb`, `GEOM_TRUTH`, blocking `os.listdir/scandir/walk` on sensitive dirs, blocking `os.system/popen/exec/fork/spawn` and `subprocess/socket` events, and blocking banned imports `numpy/scipy/skimage/cv2/PIL/pandas/torch/tensorflow/subprocess/socket/multiprocessing/glob/pathlib`. Defeats reward hack that previously could read `test_outputs.py` for truths or iterate `/tests/data` via `pathlib`.
* **From-scratch guard:** `test_from_scratch()` uses AST checks for banned modules including `pathlib`, banned calls `eval/exec/compile/__import__/chr/getattr/setattr`, banned attrs `system/popen/exec/fork/walk/listdir/scandir/rglob/__subclasses__` etc, plus case-insensitive substring and compact-token checks for `/tests`, `test_outputs`, `heldout`, `reference`, `_gen`, `scene.inkb`, `/app/data`, `GEOM_TRUTH`, `geometric_truth`, and bans `chr(`, `fromhex`, `b64decode`, `base64`, `pathlib`, `rglob`, `glob(`.
* **New domain:** Ink blot capillary wicking on porous paper (filter paper, ink darkness, dust specks, capillary diffusion, mm2 area) is distinct from ToF parcel volume, gold tumor mm3, thermal void, and pulse ns duration. 2D 8-connected version vs 3D 26-connected family shows transfer but requires adaptation.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
