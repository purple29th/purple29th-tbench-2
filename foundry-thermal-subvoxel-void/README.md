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

Sync'd from validation at commit 721013b (15 attempts, secure verifier 11 checks, per sthallam v2.0 review):

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| `claude-opus-4-8` | 5 + 5 | 2/5 = 40% and 3/5 = 60% (combined 5/10 = 50%) | Genuine conservation but sensitive to speck heavy case, 2 fails overcount halo and 1 undercount |
| `gpt-5.5` | 5 + 5 | 2/5 = 40% and 2/5 = 40% (combined 4/10 = 40%) | 2 fails overcount speck heavy 3707 vs 3350, 1 fail randomized extra just over tolerance |
| `meta/avocado-5.14-code` | 5 + 5 | 0/5 = 0% and 1/5 = 20% (combined 1/10 = 10%) | 0/5 incomplete missing file, 1/5 fail reasoning overcount speck heavy up to 3901 vs 3350 |
| `oracle` (golden `solution/solve.py`) | 3 + 3 | 3/3 = 100% and 3/3 = 100% | Validates grader, all 11 checks pass |

Overall non-oracle: 6/15 = 40% passes at v2.0 head, indicating task is genuinely hard, not inflated by earlier 5/5 runs at bc94c39 which had no speck heavy stress. Earlier v1.0 had gpt 1/5 rate limit incompletes, v1.3 bc94c39 had 5/5 opus and 4/5 gpt without speck heavy failure, v2.0 721013b adds speck heavy case that drops rates to 2/5 claude, 2/5 codex, 0/5 avocado per review.

> Calibration: threshold-and-count fails 88-128% over or 30-50% under; only genuine intensity conservation with robust background, plateau, 26-connected main component isolation, and halo growth to noise floor without merging specks passes within 3 percent. Speck heavy case is main discriminator.

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
* **Secure runner:** verifier now generates held-out scans at runtime in a temporary directory with random filenames and runs solver via `_secure_runner.py` with `sys.addaudithook` blocking `open()` on paths containing `/tests`, `test_outputs`, `heldout`, `_gen`, `GEOM_TRUTH`, `geometric_truth`, `reference_volume`, blocking `os.listdir/scandir/walk` on `/tests`, and blocking `os.system/popen/exec/fork/spawn` and `subprocess/socket` events, plus blocking banned imports `numpy/scipy/skimage/cv2/PIL/pandas/torch/tensorflow/subprocess/socket/multiprocessing/glob/pathlib/os/io/posixpath/ntpath/genericpath`. It does NOT block `/app/data` or `scene.tiv`, so reading the provided sample is allowed and hardcoding sample volume fails the volume check, not the guard. This fixes the previous spec/test trap. The previous `reference` broad substring ban that flagged harmless comments like `reference level` has been narrowed to exact `reference_volume` to avoid false negatives.
* **From-scratch guard:** `test_from_scratch()` uses AST checks for banned modules including `os/io/pathlib/socket/multiprocessing`, banned calls `eval/exec/compile/__import__/chr`, banned attrs `system/popen/exec/fork/walk/listdir/scandir/rglob/__subclasses__` etc, plus substring and compact-token checks for `/tests`, `test_outputs`, `heldout`, `_gen`, `GEOM_TRUTH`, `geometric_truth`, `reference_volume` only (not broad `reference`), and bans `chr(`, `fromhex`, `b64decode`, `base64`, `pathlib`, `rglob`, `glob(` and `import os`. Instruction.md banned list is fully synced to include socket, multiprocessing, glob, pathlib, os, io, chr, bytes, fromhex, base64, b64decode, bytearray, posixpath, ntpath, genericpath per reviewer feedback. Harmless comments containing `reference` without `reference_volume` now pass.
* **New domain:** Foundry thermal IR void detection is distinct from previous ToF parcel and gold tumor – uses flash heating, turbine blades, laser powder bed fusion, spatter artefacts, thermal diffusion – embedding dedup NOVEL.

## Fix Log
* v1.0 -> v1.1 R05/BAD_LEAKAGE: added filesystem sandbox, deny /tests and /app/data, patch open etc; R07/BAD_GRADING_WEAK: added negative tests, expanded BANNED_MODULES, BANNED_CALLS, BANNED_TOKENS; README synced rates; instruction.md synced banned list.
* v1.2 -> v1.3: clarified conservation vs thresholding, removed getattr etc from BANNED_CALLS, dropped ast.Str deprecation.
* v1.3 -> v1.4: fixed TBR Eval GT FAIL Gold patch resolves 0. Root cause was _resolve_script_path fallback making tests pass without /app/solve.py. Rewrote verifier to secure runtime generation with random filenames and audit hook. Synced README rates to bc94c39: opus 5/5 100%, gpt 4/5 80%, avocado 4/5 80%.
* v1.4 -> v1.5: fixed Quality Review BAD_GRADING_WRONG + BAD_AMBIGUOUS at 4c1cb5f. Over-broad bans of substring `reference` in BANNED_SUBSTRINGS_SRC and BLOCKED_SUBSTRS flagged harmless comment `reference level` as cheating, though prompt only bans `reference_volume`. Narrowed both lists from broad `reference` to exact `reference_volume` only, plus `/tests`, `test_outputs`, `heldout`, `_gen`, `GEOM_TRUTH`, `geometric_truth`. Also removed `/app/data` and `scene.tiv` from blocked lists to fix spec/test trap where instruction tells agent example is at /app/data/scene.tiv but guard blocked it. Updated README anti-cheating to reflect current harness not blocking sample path and narrowed reference ban.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
