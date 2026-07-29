# Android Magnetometer Hard-Iron Bias Fit

## Summary
Factory calibration task for Android magnetometer: estimate hard-iron bias vector from figure-8 orbit data using sphere fitting.

The device's magnetometer is affected by static magnetic fields from internal components (speaker magnets, screws). This creates a constant offset per axis. During factory test, the phone is rotated through a 3D orbit; ideal readings lie on a sphere centered at origin with radius equal to Earth's field (35-60 uT). Real readings are offset by bias.

This task requires implementing a numerically stable linear least-squares sphere fit to recover bias `[bx, by, bz]` and radius `R`.

## Why This Task
Magnetometer calibration is critical for compass accuracy, AR orientation, and navigation. Hard-iron estimation via orbit data is a standard factory procedure on Android production lines. The algorithm must be robust to sensor noise (up to 1.5 uT) and partial angular coverage.

## Approach

**Sphere fitting method:**

Given points `(x_i, y_i, z_i)`:

```
(x - bx)^2 + (y - by)^2 + (z - bz)^2 = R^2
x^2 + y^2 + z^2 -2*bx*x -2*by*y -2*bz*z + (b^2 - R^2) = 0
```

Set up `A * u = b` where `A = [-2x, -2y, -2z, 1]` (N x 4), `b = -(x^2+y^2+z^2)`, `u = [bx, by, bz, c]`, `c = b^2 - R^2`. Solve via `lstsq`, then `R = sqrt(bx^2+by^2+bz^2 - c)`.

This linear method is efficient, works for N=50..5000, and tolerates noise.

## Files

- `mag_calibration.py` - main module agent must create (function `estimate_hard_iron_bias`)
- `data/sample_orbit.csv` - sample data for local dev (500 points, bias [15,-20,8], R=45)
- `environment/Dockerfile` - installs python3 + numpy
- `tests/test_outputs.py` - evaluation suite

## Completion Criteria
Tests pass when bias error < thresholds varying by scenario (0.3 uT clean, 0.8 uT noisy, 1.5 uT partial).

