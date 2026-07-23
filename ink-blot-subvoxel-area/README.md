# codimango/ink-blot-subvoxel-area

## Description

The agent writes a **from-scratch** Python script (`/app/solve.py`, stdlib only) that reads a custom capillary ink blot scan (`.inkb`, magic `INKB`) on porous paper and reports true inked area in square mm. Script takes scan path as first arg and prints area as final number.

This is the **area** version of `android-tof-subvoxel-volume` and `confocal-gold-subvoxel-volume` and `foundry-thermal-subvoxel-void` – same sweet spot but 2D calculus: threshold counting overcounts halo 80-130% or undercounts thin feathered wicking 30-50%, no fixed cutoff works across different paper porosity, ink darkness, pixel pitch.

Ink drop wicks via capillary diffusion plus lens PSF smears darkness everywhere, so true inked area is not recoverable by counting dark pixels. **Correct method is intensity conservation via most concentrated area (calculus integration):** `area_pixels = sum(bg-subtracted over blot+halo) / plateau_darkness`, `mm2 = pixels*sx*sy`. Agent must infer paper background, isolate main blot from far dust specks via largest-mass 8-connected component, estimate plateau darkness via filtered peak, integrate halo.

Threshold shortcuts are 12-35% off, conservation <1%.

A numpy one-shot is both forbidden and wrong.

## Completion Rates

| Model | Agent | Pass rate |
|-------|-------|-----------|
| Oracle | `oracle` | 1.0 (deterministic; 3 verifier tests) |
| Frontier | `metacode` / `claude-code` | to be measured |

> Calibration target: threshold-and-count fails here; only genuine intensity-conservation passes.

## Model Analysis

Forces multi-step reasoning from raw bytes:
* **Binary parsing:** custom little-endian header magic INKB, version, dtype 2=int16 16=float32, nx ny, sx sy mm per pixel anisotropic, data_offset. X-fastest. From-scratch bans numpy/scipy/imaging/graph libs.
* **Background:** paper background dominates image, robust median/MAD needed.
* **Speck isolation:** far dust specks dropped by largest-mass 8-connected component.
* **Plateau:** interior darkness hidden by diffusion+noise; filtered peak needed.
* **Halo:** faint capillary halo carries ink signal, adaptive growth until shell mean hits noise floor.
* **Area calc:** pixels = integrated residual / amplitude; mm2 = pixels*sx*sy with per-scan anisotropic pixel size.

Threshold strategies: low thr 88-128% over, best fixed absolute 31% worst, best fraction of amplitude 12% worst, half-max/Otsu 18-35% off. Conservation 0.19-0.99%.

## Anti-Cheating Analysis

* **Hardcoded outputs:** grading runs on 3 hidden held-out scans whose areas (12.36, 6.21, 10.10 mm2) differ from each other and visible sample (6.04 mm2). Constant fails.
* **Overfitting to visible:** only sample in agent container, different area/spacing/PSF/amplitude/background than held-outs. Held-outs under tests/ absent during agent run.
* **Modifying test files:** tests and held-out data copied only at verify time. Ground truth from generator geometric area, not agent-editable. _gen.py co-located with tests never in agent container.
* **Bypassing intended path:** test_from_scratch rejects numpy/scipy/skimage/cv2/PIL/networkx/igraph/imageio/pandas/torch/tensorflow/socket/multiprocessing/glob and shelling out – forcing genuine byte parsing. Threshold-and-count passes from-scratch but fails every held-out by 80-130%+.
* **New domain:** Ink blot capillary wicking on porous paper is distinct from ToF parcel, gold tumor, thermal void – uses paper lab, filter paper, ink darkness, dust specks, capillary diffusion – embedding dedup NOVEL expected.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
