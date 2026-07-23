# codimango/scope-pulse-calculus-duration

## Description

The agent writes a **from-scratch** Python script (`/app/solve.py`, stdlib only) that reads a custom oscilloscope photodiode pulse dump (`.plse`, magic `PLSE`) and reports true original pulse duration in ns. Script takes dump path as first arg and prints duration as final number.

This is the **calculus 1D version** of `android-tof-subvoxel-volume` and `confocal-gold-subvoxel-volume` and `foundry-thermal-subvoxel-void` and `ink-blot-subvoxel-area` – same sweet spot: threshold counting overcounts smeared tails 80-130% or undercounts thin extensions 30-50%, no fixed cutoff works across amplitude, baseline, dt, sigma.

Photodiode square pulse is smeared by front-end shaper amplifier PSF (normalized Gaussian) which conserves total charge. **Correct method is calculus – charge conservation integral:** `true_width_samples = sum(baseline-subtracted over pulse+halo) / plateau_amplitude`, `duration_ns = width*dt`. Agent must infer baseline, isolate main pulse from afterpulses via largest-mass 1D contiguous component, estimate plateau via filtered peak, integrate halo.

Threshold shortcuts are 12-35% off, conservation <2%.

A numpy one-shot is both forbidden and wrong.

## Completion Rates

| Model | Agent | Pass rate |
|-------|-------|-----------|
| Oracle | `oracle` | 1.0 (deterministic; 3 verifier tests) |
| Frontier | `metacode` / `claude-code` | to be measured |

> Calibration target: threshold-and-count fails here; only genuine integral conservation passes.

## Model Analysis

Forces multi-step calculus reasoning from raw bytes:
* **Binary parsing:** custom little-endian header magic PLSE, version, dtype 2=int16 16=float32, n, dt ns per sample, data_offset, baseline_hint (must ignore). X-fastest. From-scratch bans numpy/scipy/imaging/graph libs.
* **Baseline:** baseline drift dominates trace, robust median/MAD needed.
* **Afterpulse isolation:** far afterpulses dropped by largest-mass 1D contiguous component above noise.
* **Plateau:** interior amplitude hidden by shaper+noise; 3-point moving-average peak needed.
* **Halo:** faint shaper tails carry charge, adaptive growth until shell mean hits noise floor.
* **Duration:** width = integrated residual / amplitude; ns = width*dt with per-file dt.

Threshold strategies: low thr 88-128% over, best fixed absolute 31% worst, best fraction of amplitude 12% worst, half-max/Otsu 18-35% off. Conservation 0.19-1.3% per scan.

## Anti-Cheating Analysis

* **Hardcoded outputs:** grading runs on 3 hidden held-out pulses whose durations (130.0, 150.0, 162.0 ns) differ from each other and visible sample (125.0 ns). Constant fails.
* **Overfitting to visible:** only sample in agent container, different duration/spacing/PSF/amplitude/baseline/noise than held-outs. Held-outs under tests/ absent during agent run.
* **Modifying test files:** tests and held-out data copied only at verify time. Ground truth from generator geometric duration, not agent-editable. _gen.py co-located with tests never in agent container.
* **Bypassing intended path:** test_from_scratch rejects numpy/scipy/skimage/cv2/PIL/networkx/igraph/imageio/pandas/torch/tensorflow/socket/multiprocessing/glob and shelling out – forcing genuine byte parsing. Threshold-and-count passes from-scratch but fails every held-out by 80-130%+.
* **New domain:** Oscilloscope photodiode pulse duration is distinct from ToF parcel, gold tumor, thermal void, ink blot – uses particle lab, shaper amplifier, afterpulses, charge conservation, calculus integral, ns duration – embedding dedup NOVEL expected.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
