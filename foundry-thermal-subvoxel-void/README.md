# codimango/foundry-thermal-subvoxel-void

## Description

The agent writes a **from-scratch** Python script (`/app/solve.py`, stdlib only) that reads a custom thermal IR volume (`.tiv`, magic `TIVR`) of internal porosity voids in a laser powder bed fusion turbine blade and reports physical void volume in cubic mm. Script takes scan path as first arg and prints volume as final number.

This is the **precision escalation** of `android-tof-subvoxel-volume` and `confocal-gold-subvoxel-volume`. Those are solved by thresholding? Here that fails 80-130% over or 30-50% under.

Laser flash makes trapped pores hot, but thermal diffusion plus mid-wave IR lens PSF smears hot glow everywhere:
1. **No threshold recovers volume** – solid core saturates to peak after diffusion, thin cracks never reach threshold.
2. **Correct method is intensity conservation via most concentrated area** – normalized blur conserves total thermal energy, so true voxels = sum(bg-subtracted over void+halo) / plateau_temperature. Must infer ambient background, isolate main void from far spatter specks via largest-mass 26-connected, estimate plateau via filtered peak, integrate halo.
3. **Tighter tolerance 3%** – conservation lands <1%, threshold shortcuts >=12% off.

A one-shot template (numpy + scipy.ndimage.label + threshold-count) is both forbidden and wrong.

## Completion Rates

Sync'd from validation at commit bc94c39 (18 attempts, secure verifier 9 checks):

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| `claude-opus-4-8` | 5 | 5/5 = 100% | All genuine energy-conservation passes |
| `gpt-5.5` | 5 | 4/5 = 80% | 4 passes, 1 fail |
| `meta/avocado-5.14-code` | 5 | 4/5 = 80% | 4 passes, 1 fail (previously 2/5 with infra, now 4/5 after scaffold fix) |
| `oracle` (golden `solution/solve.py`) | 3 | 3/3 = 100% | Validates grader |

Overall non-oracle: 13/15 = 86.7% passes, indicating method is discoverable but requires precise calibration. Earlier v1.0 had gpt-5.5 2/5 (40%) inflated by rate-limit incompletes; v1.3 after sandbox fix shows higher genuine pass rate.

> Calibration target: threshold-and-count fails here 88-128% over or 30-50% under; only genuine intensity-conservation passes <1% error. Honest solutions need robust background, plateau, 26-connected main-component isolation, and halo integration to stay within 3%.

## Model Analysis

Forcing multi-step physics-informed reasoning from raw bytes:
* **Binary parsing:** custom little-endian header magic TIVR, version, dtype 2=int16 16=float32, nx ny nz, sx sy sz mm per axis anisotropic, data_offset. X-fastest. From-scratch check rejects numpy/scipy/imaging/graph libs.
* **Background:** ambient dominates volume, must be estimated robustly without bias.
* **Speck isolation:** far spatter artefacts dropped by keeping largest-mass 26-connected component.
* **Plateau:** interior temperature never observed directly due to diffusion+noise; must be estimated from most concentrated region.
* **Halo:** faint thermal halo carries signal and must be included via adaptive growth until shell mean hits noise floor, without bridging to specks.
* **Volume:** voxels = integrated residual / amplitude; mm3 = voxels*sx*sy*sz with per-scan anisotropic spacing.

Threshold strategies measured on sample+3 heldouts: low threshold 88-128% over, best fixed absolute 31% worst, best fraction of amplitude 12% worst, half-max/Otsu 18-35% off. Conservation 0.21-0.98% per scan.

## Anti-Cheating Analysis

* **Hardcoded outputs:** grading now generates held-out scans at test time from configs with geometric truth computed inside verifier (field = blurred+bg+(rng-0.5)*2*ns), not from static files. Volumes (3350.6, 3423.2, 3729.9 mm3 plus randomized extra) differ from sample (2460.0 mm3). Constant cannot pass. No hardcoded GEOM_TRUTH dict parseable by solver; truth derived from build_field.
* **Overfitting to visible:** only sample scan present in agent container at `/app/data/scene.tiv`, different volume/spacing/PSF/amplitude/bg/noise than hidden generated scans. Hidden inputs are generated in temp dir with random filenames (`input_<hex>.tiv`) and are not byte-identical to any committed file. `tests/data/heldout_*.tiv` no longer used by verifier.
* **Secure runner:** verifier runs solver via `_secure_runner.py` with `sys.addaudithook` blocking `open()` on paths containing `/tests`, `test_outputs`, `heldout`, `reference`, `_gen`, `/app/data`, `scene.tiv`, `GEOM_TRUTH`, `geometric_truth`, `reference_volume`, blocking `os.listdir/scandir/walk` on sensitive dirs, blocking `os.system/popen/exec/fork/spawn` and `subprocess/socket` events, and blocking banned imports `numpy/scipy/skimage/cv2/PIL/pandas/torch/tensorflow/subprocess/socket/multiprocessing/glob/pathlib/os/io/posixpath/ntpath/genericpath`. Defeats reward hack that could read `test_outputs.py` or iterate `/tests/data` via `pathlib`. Previously v1.1 patched builtins.open etc but retained fallback `_resolve_script_path` that made tests pass without `/app/solve.py`, causing TBR Eval GT to report Gold patch resolves task 0.
* **From-scratch guard:** `test_from_scratch()` uses AST checks for banned modules including `os/io/pathlib/socket/multiprocessing`, banned calls `eval/exec/compile/__import__/chr`, banned attrs `system/popen/exec/fork/walk/listdir/scandir/rglob/__subclasses__` etc, plus substring and compact-token checks for `/tests`, `test_outputs`, `heldout`, `GEOM_TRUTH`, `scene.tiv`, `/app/data`, and bans `chr(`, `fromhex`, `b64decode`, `base64`, `pathlib`, `rglob`, `glob(` and `import os`. Instruction.md banned list now fully synced to include socket, multiprocessing, glob, pathlib, os, io, chr, bytes, bytearray, posixpath, ntpath, genericpath per reviewer request.
* **New domain:** Foundry thermal IR void detection is distinct from previous ToF parcel and gold tumor – uses flash heating, turbine blades, laser powder bed fusion, spatter artefacts, thermal diffusion – embedding dedup NOVEL.

## Fix Log
* v1.0 -> v1.1 R05/BAD_LEAKAGE: added filesystem sandbox in run_agent, deny /tests and /app/data, patch open etc; R07/BAD_GRADING_WEAK: added negative tests, expanded BANNED_MODULES to include pathlib/os/io/posixpath/ntpath/genericpath, expanded BANNED_CALLS to chr, expanded BANNED_TOKENS to pathlib/os./chr(/bytes etc, added dynamic-concat detection; README synced completion rates; instruction.md synced banned list to include socket, multiprocessing, glob, pathlib, os, io.
* v1.2 -> v1.3: clarified conservation vs thresholding per reviewer, removed getattr etc from BANNED_CALLS to match instruction, dropped ast.Str deprecation.
* v1.3 -> v1.4: fixed TBR Eval GT FAIL Gold patch resolves task 0 grading_error. Root cause was `_resolve_script_path` fallback that made test_script_exists and test_heldout pass even without `/app/solve.py`, so fail-to-pass was 0. Rewrote verifier to secure pattern used in ink-blot/confocal/pulse: generate heldouts at runtime in temp dir with random filenames, compute geometric truth at runtime, run via secure runner with audit hook blocking /tests, /app/data, heldout, GEOM_TRUTH, and blocking banned imports including os/io/pathlib. Now without solution 7 fail 2 pass, with solution 9 pass, fail-to-pass >0. Also synced README completion rates to validation at bc94c39: opus 5/5 100%, gpt 4/5 80%, avocado 4/5 80%.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
