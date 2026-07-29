# Android Magnetometer Hard Iron Bias Fit

## Summary
I work on Android factory line. Magnetometer has hard iron bias from speaker magnets and screws. During factory test we rotate phone in figure eight and log raw field values. Ideal values would sit on a sphere centered at zero with radius equal to earth field. Real values are shifted by bias plus noise and outliers. Task is to estimate bias vector and radius.

This is similar to thermal subvoxel void tasks where thresholding fails. Here simple averaging fails.

## Why This Task Is Hard
Magnetometer calibration is critical for compass and AR. Factory needs robust estimate despite partial orbit and motor spikes.

Naive methods fail badly:
* averaging (max plus min) divided by 2 per axis fails 40 to 70 percent, error 15 to 35 uT on partial orbits
* using mean of points as bias fails 80 to 120 percent, error 20 to 50 uT
* plain least squares without outlier handling fails outlier case by 4 to 8 uT

Only genuine robust sphere fit passes. Partial coverage as low as 40 percent makes mean not equal center. Outliers up to 5 percent far from sphere break simple least squares. Need iterative robust refinement.

This is precision escalation of clean sphere fit. Clean case is easy but partial and outlier cases are main discriminators, similar to speck heavy in foundry task.

## Approach
Sphere equation is (x minus bx) squared plus (y minus by) squared plus (z minus bz) squared equals R squared. Expand to linear form to solve for bias and intermediate variable c equals bias squared minus R squared. Set up matrix A with columns minus 2x, minus 2y, minus 2z, 1 and vector b equals negative sum squares. Solve using lstsq. Then recover radius from bias squared minus c.

For robustness, after first fit compute residuals as distance to center minus radius, use median absolute deviation to find outliers, remove far points and refit. Iterate a few times. This handles up to 5 percent far outliers.

Method works for N 50 to 10000, noise up to 2.0 uT, partial coverage 40 to 100 percent.

## Files
* mag_calibration.py is main module agent must create, function estimate_hard_iron_bias
* data/sample_orbit.csv is sample for local dev, 500 points, bias 15, negative 20, 8, R 45
* environment/Dockerfile installs python3 plus numpy
* tests/test_outputs.py is evaluation suite

## Completion Criteria
Tests pass when bias error below thresholds that vary by scenario: 0.3 uT clean, 0.9 uT noisy, 1.8 to 2.0 uT partial hard, 1.2 uT strong bias, 1.5 uT outlier case, random stress with adaptive tolerance.

## Anti Cheating
* No hardcoded bias, must estimate from data
* Hidden tests use random bias up to 70 uT, random radius 28 to 62, random N 200 to 1500, random noise up to 1.8, coverage 0.4 to 1.0, outlier ratio up to 0.04
* Sample bias 15, negative 20, 8 differs from hidden
* Only numpy allowed, no scipy, sklearn, torch etc
* Function must be deterministic
