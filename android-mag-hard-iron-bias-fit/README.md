# Android Magnetometer Hard Iron Bias Fit

## Summary
Android factory line magnetometer calibration. Each phone has internal magnets from speakers and screws adding a constant offset. During factory test the phone is rotated in a figure eight while logging raw magnetic readings. Without offset all readings would be roughly same distance from zero. With offset the cloud is shifted. Task is to estimate the shift and the earth field magnitude from messy production data.

## Why This Task Is Hard
Factory data is not ideal lab data. Coverage is often partial as low as 30 percent because operators stop early. The rig dwells longer at ends of figure eight so density is non uniform, so a density weighted centroid is biased. There are far outliers from motor spikes up to 7 percent, and occasional NaN or Inf when a channel saturates. Noise up to 2.0 uT stdev. Bias random up to 80 uT, radius 25 to 65.

A correct tool must be robust to all these effects at once. Geometric reasoning is needed rather than a single average.

## What The Tool Does
Input is Nx3 array of raw readings in uT. Output is dict with bx by bz radius as floats, JSON serializable. Bias is constant offset present in every sample, radius is magnitude of earth field in that location.

The factory model is raw equals earth vector of fixed length but varying direction plus bias plus noise, plus occasional corrupted rows. So after subtracting true bias, distances to origin should cluster around radius.

## Files
* mag_calibration.py is main module agent must create, function estimate_hard_iron_bias
* data/sample_orbit.csv is sample for local dev, 500 points, bias 15, negative 20, 8, R 45
* environment/Dockerfile installs python3 plus numpy
* tests/test_outputs.py is evaluation suite

## Completion Criteria
Tests check estimation error against hidden ground truth under many conditions including clean, noisy, partial coverage, strong bias, outliers, partial plus outlier combo, random stress, NaN handling, determinism, JSON serializability, large N performance. Tolerances are tighter for easy cases and looser for harder cases with high noise and low coverage.

## Anti Cheating
* No hardcoded bias, must estimate from data
* Hidden tests use random bias up to 80 uT, random radius 28 to 62, random N 200 to 2000, random noise up to 2.0, coverage 0.3 to 1.0, outlier ratio up to 0.07, plus NaN or Inf injection
* Sample bias 15, negative 20, 8 differs from hidden
* Only numpy allowed, no scipy, sklearn, torch etc
* Function must be deterministic
* Subprocess isolation used for oracle, agent cannot read test files
* Canary token present
