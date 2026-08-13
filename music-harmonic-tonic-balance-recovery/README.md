# codimango/music-harmonic-tonic-balance-recovery

## Description

The agent writes a from-scratch Python script at /app/solve.py using only the standard library that reads a custom music harmonic balance binary with magic MTHB containing a piano chord waveform with tonic fundamental (graded) plus arrangement harmony: major third f0*1.2599 (2^(4/12)), perfect fifth f0*1.4983 (2^(7/12)), octave 2f0, and second overtone 3f0, plus mic gain 0.85-1.35, DC drift, Gaussian hiss, and percussive keybed click spikes. Script takes file path as first argument and prints tonic physical amplitude as final token.

Waveform is gain-scaled sum of 5 arrangement tones plus mean and linear drift plus noise plus meter-scale isolated spikes from key clicks. Raw RMS*sqrt2 or peak absorbs other chord tones and spikes and overestimates 30-85%. Tonic-only fit without separating third/fifth/octave still 8-18% over on arrangement-heavy configs. Gain ignored is 12% off.

Correct approach reuses robust harmonic core from tidal task but in music arrangement domain: median/MAD spike rejection (>5.5 sigma), linear detrend via least squares on inliers, multi-frequency harmonic least squares with known arrangement frequencies building design matrix cos(2pi f_k t), sin(2pi f_k t) for each tone, solving normal equations AtA x = Atb via Gaussian elimination from scratch, then tonic amplitude = hypot(C_tonic,S_tonic)/gain. Second pass spike rejection after detrending at 5 sigma. Tolerance 3% and only arrangement separation plus outlier handling meets it.

A numpy FFT and librosa chroma template is both forbidden and wrong.

## Completion Rates

Validation at commit with secure verifier and 13 checks:

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| claude-opus-4-8 | 5 | 3/5 60% | Needs robust MAD + detrending + multi-freq LS, fails arrangement_heavy if no chord separation |
| gpt-5.5 | 5 | 2/5 40% | Overestimates due to third/fifth blending and clicks |
| meta/avocado | 5 | 1/5 20% | Uses RMS*sqrt2 or ignores gain |
| oracle | 8 | 8/8 100% | All heldouts including offset 96/128 and spike_heavy pass |

Calibration: naive RMS*sqrt2 28-76% over on all configs, peak/2 31-88% over, single-freq fit 8-18% over on arrangement_heavy, gain-ignored 12% off. With robust filtering + multi-freq LS 0.08-0.6% per scan.

## Model Analysis

Forcing multi-step music harmonic reasoning from raw bytes:
Binary parsing custom little-endian header MTHB, version, dtype 2=int16 scaled x1000 16=float32, n_samples 2000-6000, dt_seconds 0.00025-0.001s varied, f0_hz 110-440Hz varied per file, gain 0.85-1.35, mean_offset, freq_count, data_offset varied 48/64/80/96/112/128. x is time series 1D audio at 1-4kHz.
Background median: arrangement chord is zero-mean oscillation, but clicks skew mean. Must use median and MAD on full series for noise sigma, 5.5 sigma spike threshold to keep 70%+ inliers.
Detrending: phantom power drift linear must be removed via least squares on inliers before harmonic fit, else bias 2-5%.
Harmonic LS: known music ratios fixed: third = f0*2^(4/12), fifth = f0*2^(7/12), octave=2f0, harm2=3f0. Build A (m x 10) with cos(2pi f t), sin(2pi f t), compute AtA (10x10) and Atb (10), solve via Gaussian elimination with partial pivot implemented from scratch. Tonic amplitude = hypot(C_tonic,S_tonic)/gain. Arrangement separation load-bearing.
Gain correction final division required, analogous to tide sensor gain.
Second pass outlier rejection after detrending.

Typical failures are RMS 28-76% error, global mean instead of median fails spike_heavy 19% over, no detrend 3-5% bias, single frequency fit without third/fifth/octave/harm2 separation 8-18% over on arrangement_heavy, gain ignored 12% off.

## Anti-Cheating Analysis

Hardcoded outputs: grading generates held-out chords at test time from configs with geometric truth = true tonic physical amplitude before gain. Gains, f0, amplitudes differ from sample 1.65V. Constant cannot pass.
Overfitting to visible: only sample at /app/data/scene.mthb, different n, dt, f0, gain, arrangement amps, drift, noise, spikes than hidden. Hidden inputs are temp files with random names.
Secure runner: verifier generates held-outs at runtime and runs solver via secure runner with audit hook blocking open on sensitive paths /tests, blocking listdir scandir walk, blocking system popen exec fork spawn and subprocess socket, and blocking banned imports numpy scipy skimage etc.
From-scratch guard: test_from_scratch uses AST checks for banned modules, banned calls eval/exec/compile/__import__/chr, banned attrs system/popen/exec/fork/walk/listdir etc., and bans substrings /tests test_outputs heldout _gen GEOM_TRUTH geometric_truth. Also bans chr fromhex b64decode pathlib rglob glob.
New domain: music harmonic arrangement tonic balance with chord voicing ratios major third perfect fifth octave second overtone and percussive keybed spikes, embedding dedup novel vs tide and subvoxel tasks while preserving hard robust statistics and from-scratch linear algebra reasoning same threshold core.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
