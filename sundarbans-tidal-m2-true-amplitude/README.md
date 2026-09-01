# sundarbans tidal m2 true amplitude

## Description

I am Rahim from Sundarbans Bangladesh India border fisher in mangrove. Tide gauge writes THLD magic THLD with sea level time series contaminated by multi constituent tides M2 S2 O1 K1 sensor gain drift skew noise ship wake spikes. M2 lunar semidiurnal period twelve point four two zero six hours is grading quantity. Raw RMS overestimates thirty to eighty percent due to blending.

I need tool that tells true M2 amplitude meters.

Please make file at /app/solve.py last token meters.

Example at /app/data/scene.thld about one point two meters. Hidden random names input_*.thld with data offset forty eight to one twenty eight gain zero point eight five to one point three five.

File layout thld little endian four bytes ascii THLD version dtype num samples sampling interval hours data offset multiplier at forty.

Inside need robust background median MAD detrend linear least squares reject far outliers perform multi frequency linear least squares M2 S2 O1 K1 via normal equations Gaussian elimination isolate M2 amplitude correct by gain.

Naive RMS fails.

Coding rules only stdlib.

Print meters as last token.

Files: /app/solve.py you write last token meters, /app/data/scene.thld about one point two meters, Dockerfile python slim pytest, solution/solve.py oracle bespoke reading payload start and multiplier and least squares, _gen.py, test_outputs.py secure verifier runtime random names input_a3f9.thld plus payload ninety six one twenty eight and gain variants.

Completion Oracle three of three, Avocado zero to one of five.

Model Analysis low threshold fails etc.

Anti Cheating varied.

Tags tidal M2 amplitude Sundarbans THLD halo recovery

Author Tosin Daniel Jimoh purple29th at meta.com


## Files

* /app/solve.py you write last token
* /app/data/scene sample
* Dockerfile
* solution/solve.py oracle
* tests/_gen.py generates
* test_outputs.py secure verifier random names

## Completion Rates

Oracle three of three deterministic
Avocado zero to one of five
Opus four of five GPT three of five

## Model Analysis

No background overcounts, fixed cutoff over and under, no speck keeps far dust, no shape keeps round, no halo under, hardcoded offset fails 96/128, hardcoded gain fails 22 percent.

## Anti-Cheating

Varied dims spacing amp bg sig noise seed random temp names so constant fails. Secure runner blocks tests.

## Tags

Tags sundarbans tidal m2 true amplitude human story

Author Tosin Daniel Jimoh purple29th at meta.com
