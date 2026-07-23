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

| Model | Agent | Pass rate |
|-------|-------|-----------|
| Oracle | `oracle` | 1.0 (deterministic; 3 verifier tests) |
| Frontier | `metacode` / `claude-code` | to be measured |

> Calibration target: threshold-and-count fails here; only genuine intensity-conservation passes. Dominant failure is counting thresholded voxels instead of integrating conserved intensity.

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

* **Hardcoded outputs:** grading runs script on 3 hidden held-out scans whose volumes (3350.6, 3423.2, 3729.9 mm3) differ from each other and visible sample (2460.0 mm3). Constant cannot pass.
* **Overfitting to visible tests:** only data in agent container is sample scan, which has different volume, spacing, PSF width, amplitude, background than graded scans. Held-outs live under tests/ absent during agent run.
* **Modifying test files:** tests and held-out data copied only at verify time. Ground truth recomputed from generator geometric volume, not from agent-editable value. _gen.py co-located with tests and never present in agent container.
* **Bypassing intended path:** test_from_scratch rejects numpy/scipy/skimage/cv2/PIL/networkx/igraph/imageio/pandas/torch/tensorflow/socket/multiprocessing/glob and shelling out – forcing genuine byte parsing. From-scratch is necessary but not sufficient: threshold-and-count passes from-scratch but fails every held-out by 80-130%+.
* **New domain:** Foundry thermal IR void detection is distinct from previous ToF parcel and gold tumor – uses flash heating, turbine blades, laser powder bed fusion, spatter artefacts, thermal diffusion – embedding dedup NOVEL.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
