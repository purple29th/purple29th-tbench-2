# Android Magnetometer Hard Iron Bias Fit

## Summary
Android factory line magnetometer calibration. Each phone has internal magnets from speakers and screws adding a constant offset (hard iron) and metal chassis causing soft iron scale distortion up to 15 percent per axis where sphere becomes ellipsoid. During factory test the phone is rotated in a figure eight while logging raw magnetic readings. Without offset all readings would be roughly same distance from zero. With offset the cloud is shifted, with soft iron stretched. Task is to estimate the shift and earth field magnitude from messy production data.

## Why This Task Is Hard
Factory data is not ideal lab data. Coverage is often partial as low as 30 percent because operators stop early. The rig dwells longer at ends of figure eight so density is non uniform — about 60 to 70 percent of points are clustered in two tight lobes at the ends where the rig pauses, with extra motor magnetic interference up to 0.7 uT when dwelling, so a density weighted centroid is biased. Metal chassis causes soft iron scale sx sy sz in 0.85 to 1.15, turning sphere into ellipsoid, so textbook one-pass sphere fit fails (error 0.8+ uT) while ellipsoid-aware method succeeds. There are far outliers from motor spikes up to 7 percent, and occasional NaN or Inf when a channel saturates. Noise up to 2.0 uT stdev. Bias random up to 80 uT, radius 25 to 65.

A correct tool must be robust to all these effects at once: partial coverage, non-uniform dwell density with motor interference, soft iron ellipsoid stretch, outliers, NaN/Inf, and large N up to 10000. Geometric reasoning with density downsampling plus ellipsoid fitting is needed rather than single average or simple sphere least squares. Textbook one-pass sphere without density handling or ellipsoid handling fails on soft iron and dwell tests, while robust solution with voxel downsampling plus ellipsoid axis fit plus MAD trim passes.

## What The Tool Does
Input is Nx3 array of raw readings in uT. Output is dict with bx by bz radius as floats, JSON serializable. Bias is constant offset present in every sample, radius is magnitude of earth field in that location. Factory model is raw equals S times earth vector of fixed length but varying direction plus bias plus noise plus occasional corrupted rows, where S is diagonal soft iron scale. So after subtracting true bias and correcting scale, distances cluster around radius.

## Files
* mag_calibration.py is main module agent must create, function estimate_hard_iron_bias
* data/sample_orbit.csv is sample for local dev, 500 points, bias 15, negative 20, 8, R 45, no soft iron, available as data/sample_orbit.csv for local dev
* environment/Dockerfile installs python3 plus numpy
* tests/test_outputs.py is evaluation suite with soft iron and dwell tests

## Completion Criteria
Tests check estimation error against hidden ground truth under many conditions including clean, noisy, partial coverage, strong bias, outliers, partial plus outlier combo, random stress, NaN handling, determinism, JSON serializability, large N performance up to 10000, non-uniform dwell density with motor interference, soft iron ellipsoid distortion, and combined hardest case (soft iron plus dwell plus partial plus outliers plus NaN). Tolerances are tighter for easy cases (0.3) and moderately tight for hard cases (1.0 to 1.8) to ensure textbook one-pass sphere without ellipsoid or density handling fails while robust ellipsoid plus downsampling passes. Additional checks verify naive centroid and min-max averages fail on partial and dwell cases.

## Anti Cheating
* No hardcoded bias, must estimate from data
* Hidden tests use random bias up to 80 uT, random radius 28 to 62, random N 200 to 10000, random noise up to 2.0, coverage 0.3 to 1.0, outlier ratio up to 0.07, soft iron scale 0.85 to 1.15 on some tests, dwell ratio 0.0 to 0.65 with motor interference up to 0.7, plus NaN or Inf injection
* Sample bias 15, negative 20, 8 differs from hidden
* Only numpy and standard library allowed, no scipy, sklearn, torch etc
* Only dangerous builtins banned: eval, exec, compile, __import__, breakpoint — getattr, hasattr, locals etc are allowed per spec to avoid false FAIL
* Function must be deterministic and JSON serializable
* Subprocess isolation used, agent runs in temp dir with PYTHONPATH=td so cannot read /tests
* Canary token present
