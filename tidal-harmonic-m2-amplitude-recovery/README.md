# codimango/tidal-harmonic-m2-amplitude-recovery

## Description

The agent writes a from-scratch Python script at /app/solve.py using only the standard library that reads a custom coastal tide gauge binary with magic THLD containing sea-level time series contaminated by multi-constituent tides, sensor gain, drift, and ship-wake spikes, and reports physical M2 lunar semidiurnal amplitude in meters. Script takes file path as first argument and prints amplitude as final token.

Sea level is gain-scaled sum of M2 (12.4206h, graded), S2 (12h), O1 (25.82h), K1 (23.93h) plus mean offset and linear drift from subsidence plus Gaussian noise plus meter-scale isolated spikes from ship wakes. Raw RMS or peak-to-peak absorbs other constituents and spikes and overestimates 30-80%. Gain ignored gives 8-35% error.

Correct approach uses robust median/MAD outlier rejection (>5.5 sigma), linear detrending via least squares on inliers, and multi-frequency harmonic least squares. Build design matrix with cos(w_k t) and sin(w_k t) columns for known omegas, solve normal equations A^T A x = A^T y via Gaussian elimination from scratch, then M2 amplitude = sqrt(C_M2^2+S_M2^2)/gain. Tolerance 3% and only separation of constituents plus outlier handling meets it.

A numpy FFT and simple threshold RMS template is both forbidden and wrong.

## Completion Rates

Validation at commit with secure verifier and 13 checks:

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| claude-opus-4-8 | 5 | 3/5 60% | Needs robust MAD + detrending + multi-freq LS, fails spike_heavy if no outlier rejection |
| gpt-5.5 | 5 | 2/5 40% | Overestimates due to S2/O1 blending and spikes |
| meta/avocado | 5 | 1/5 20% | Uses RMS*sqrt2 or ignores gain |
| oracle | 8 | 8/8 100% | All heldouts including offset 96/128 and spike_heavy pass |

Calibration: naive RMS*sqrt2 28-73% over on all configs, peak/2 31-85% over, gain-ignored 12% off on heldout_1. With robust filtering + multi-freq LS 0.08-0.5% per scan.

## Model Analysis

Forcing multi-step signal processing from raw bytes:
Binary parsing custom little-endian header THLD, version, dtype 2=int16 scaled x1000 16=float32, n_samples, dt_seconds, gain 0.85-1.35, mean_offset, freq_count, data_offset varied 48/64/80/96/112/128. x is time series 1D.
Background median: tide occupies zero-mean oscillation, but spikes skew mean. Must use median and MAD on lower half for noise sigma, 5.5 sigma spike threshold to keep 70%+ inliers.
Detrending: subsidence drift 0.86 m/day linear must be removed via least squares on inliers before harmonic fit, else bias 2-4%.
Harmonic LS: known frequencies fixed physics M2=0.0001405189 rad/s, S2=0.000145444, O1=0.0000675977, K1=0.0000729211. Build A (m x 8) with cos/sin, compute AtA (8x8) and Atb (8), solve via Gaussian elimination with partial pivot implemented from scratch. Amplitude = hypot(C,S)/gain.
Outlier handling second pass after detrending at 5 sigma removes residual wakes.
Gain correction final division required.

Typical failures are RMS 28-73% error, global mean instead of median fails spike_heavy 19% over, no detrend 3-5% bias, single frequency fit without S2/O1/K1 separation 8-15% over on multi_constituent_heavy, gain ignored 12% off.

## Anti-Cheating Analysis

Hardcoded outputs: grading generates held-out gauges at test time from configs with geometric truth = true M2 physical amplitude before gain. Gains differ, amplitudes differ from sample 1.65m. Constant cannot pass.
Overfitting to visible: only sample at /app/data/scene.thld, different n, dt, gain, constituents, drift, noise, spikes than hidden. Hidden inputs are temp files with random names.
Secure runner: verifier generates held-outs at runtime and runs solver via secure runner with audit hook blocking open on sensitive paths /tests, blocking listdir scandir walk, blocking system popen exec fork spawn and subprocess socket, and blocking banned imports numpy scipy skimage etc.
From-scratch guard: test_from_scratch uses AST checks for banned modules, banned calls eval/exec/compile/__import__/chr, banned attrs system/popen/exec/fork/walk/listdir etc., and bans substrings /tests test_outputs heldout _gen GEOM_TRUTH geometric_truth. Also bans chr fromhex b64decode pathlib rglob glob.
New domain: ocean tide gravimetry M2 harmonic analysis with ship-wake spikes and multi-constituent blending, embedding dedup novel vs subvoxel-void true-volume tasks while preserving hard robust statistics and from-scratch linear algebra reasoning.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
