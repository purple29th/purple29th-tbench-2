# codimango/android-sensor-deadtime-flux

## Description

From scratch Python script (`/app/solve.py`, standard library only) that parses a
custom on-device particle/photon counter log (`.flux`) and prints the **total true
number of events** recorded across all time bins. The script takes the log path
as its first argument and prints the total as the final number on stdout, so it
can run on logs it has never seen.

## Why it is hard (the insight)

The detector is **non-paralyzable**: after each recorded count it is blind for a
dead time `tau`, and events arriving during that window are lost (they do not
extend the window). Over a bin of width `dt`, a true rate `n` is therefore
recorded as a measured rate `m = n / (1 + n*tau)`. At high rates the recorded
counts **saturate** and undercount the truth.

The naive reading — sum the recorded counts — undercounts by ~60–66% on these
logs, and by a *rate-dependent* amount that changes per file, so no fixed factor
fixes it. The correct answer requires recognising the saturation and inverting it
**per bin** before summing:

    m = M / dt
    n = m / (1 - m*tau)
    true_count_in_bin = n * dt = M / (1 - (M/dt)*tau)

`dt` and `tau` are in the header and differ per file, so they must be read, not
assumed. This is a measurement-recovery reasoning step (like the intensity
conservation in `android-tof-subvoxel-volume`), not a library call: numpy/scipy
and friends are banned, so parsing and the correction are done by hand.

## Held out cases (measured)

Ground truth is recomputed independently in the verifier (pure standard library,
a different algebraic form of the same inversion), then compared within 2%.
Answers are the verified oracle == reference totals; recovery lands within ~0.4%
of the generator's true event count, while summing the raw counts is ~65% low.

| File | offset | dtype | bins | dt (s) | tau (s) | true total | raw-sum (naive) |
|------|--------|-------|------|--------|---------|------------|-----------------|
| heldout_1 | 64 | uint32 | 400 | 0.02 | 5e-4 | ~16290 | 5680 (-65%) |
| heldout_2 | 96 | uint16 | 300 | 0.005 | 1e-4 | ~15672 | 5350 (-66%) |
| heldout_3 | 96 | uint32 | 500 | 0.05 | 1e-3 | ~25734 | 8782 (-66%) |

## Completion Rates

| Model | Agent | Pass rate |
|-------|-------|-----------|
| Oracle | `oracle` | 1.0 (deterministic; all 5 verifier tests pass) |
| Frontier models | `metacode` / `claude-code` | to be measured by the validation pipeline |

> **Calibration target:** the split comes from whether a trial recognises the
> saturation and derives the per-bin inverse `M / (1 - (M/dt)*tau)` from the
> stated blind-time behaviour, versus summing the raw counts (which is ~65% low)
> or applying a single global factor (which fails because `dt` and `tau` vary per
> file).

## Anti Cheating

- **Hardcoded outputs:** the three held outs have different totals, bin widths,
  dead times, dtypes and offsets, all different from the visible sample. A
  constant cannot satisfy them.
- **Overfitting to visible tests:** the only data in the container is the sample
  log; held outs live under `tests/` and are absent during the agent run.
- **Reward hacking / reading the answer:** the agent script is run on an isolated
  copy of the log under a neutral name from a temp working directory, so it only
  receives the input path and cannot identify the held-out or reach the mounted
  verifier / held-out data. `test_from_scratch()` is an AST import/exec audit
  (robust to spacing and aliasing) that bans array/imaging/graph libraries,
  `subprocess`/`importlib`/`runpy`/`ctypes`/`socket`/`glob`, the dynamic builtins
  `eval`/`exec`/`compile`/`__import__`, importing the verifier, and any token that
  reads `/tests` or scans the filesystem.
- **Test reliability:** grading needs no network — `pytest` is baked into the
  image and the ground-truth recovery is pure standard library. `tests/_gen.py`
  (the deterministic generator) is co-located with the tests and never ships in
  the agent container.

Built in the mold of https://github.com/codimango/mehag-tbench/tree/main/mri-volume-calc
and https://github.com/codimango/purple29th-tbench-2/tree/main/android-tof-subvoxel-volume.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
