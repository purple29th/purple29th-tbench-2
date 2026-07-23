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

| Model | Agent | Pass rate |
|-------|-------|-----------|
| Oracle | `oracle` | 1.0 (deterministic; all 5 verifier tests pass) |
| Frontier models | `metacode` / `claude-code` | to be measured by validation pipeline |

> **Calibration target:** models reaching for family threshold-and-count solution or numpy one-shot fail here; only genuine intensity-conservation derivation passes. Dominant expected failure is *counting thresholded voxels instead of integrating conserved intensity* — reasoning gap not setup issue: oracle and independent conservation impl both pass under 1.1%, so correct base-Python solution exists.

## Model Analysis

The task forces multi-step physics-informed reasoning from raw bytes:

* **Binary parsing:** custom little-endian header with magic GVOL, version, dtype code 2=int16 16=float32, nx ny nz, sx sy sz mm per axis anisotropic, data_offset. X-fastest indexing. From-scratch check rejects numpy/scipy/imaging/graph libs.
* **Background inference:** background dominates volume, must be estimated robustly without bias from tumor itself.
* **Speck isolation:** far gold dust artefacts must be dropped by keeping largest-mass 26-connected component, not largest voxel count.
* **Plateau amplitude:** interior value never observed directly due to blur+noise; must be estimated from most concentrated region via filtered peak, not naive max.
* **Halo integration:** faint Airy halo still carries gold signal and must be included via adaptive growth until shell mean hits noise floor, without bridging to specks.
* **Volume calc:** voxels = integrated residual / amplitude; mm3 = voxels * sx * sy * sz with per-scan anisotropic spacing.

Threshold strategies measured on sample+3 heldouts: threshold@200 + largest CC = 88-128% over, best fixed absolute threshold = 31% worst-case, best fixed fraction of amplitude (true bg and amp given) = 12% worst-case, half-max and Otsu = 18-35% off. Conservation = 0.19-0.99% per scan.

## Anti-Cheating Analysis

* **Hardcoded outputs:** grading runs script on three hidden held-out scans whose volumes (3977.5, 3983.4, 4428.0 mm^3) differ from each other and visible sample (3206.3 mm^3). Constant or sample-memorized value cannot pass.
* **Overfitting to visible tests:** only data in agent container is sample scan, which has different volume and different voxel spacing, PSF width, amplitude, background than graded scans. Held-outs live under `tests/` and absent during agent run.
* **Modifying test files:** tests and held-out data copied only at verify time. Reward computed by verifier from ground truth it recalculates independently with numpy+scipy by intensity conservation, not from anything agent can edit. `tests/_gen.py` co-located with tests and never present in agent container.
* **Bypassing intended path:** `test_from_scratch()` rejects numpy, scipy, scikit-image, OpenCV, PIL/Pillow, networkx, igraph, etc and shelling out — forcing genuine byte parsing and hand-written solution. From-scratch is necessary but not sufficient: prior family's threshold-and-count passes `test_from_scratch()` but fails every held-out by 88-128%. Per-scan varied spacing forces reading header; point-spread blur plus partial-volume defeats every fixed threshold >=12% off; 3% tolerance rejects naive shortcuts while admitting any sound conservation implementation.

Author: Tosin Daniel Jimoh <purple29th@meta.com>


## Fix Log (2026-07-23)
- Fixed TBR FAIL test_deps_not_in_image by removing numpy/scipy from Dockerfile (stdlib-only verifier)
- Fixed Quality Review: reference now uses geometric truth 3977.5/3983.36/4428.0 mm3
- Commit 01cc0dbf verified on GitHub API
