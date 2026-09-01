# sundarbans tidal m2 true amplitude

## Description

I am Rahim from Sundarbans Bangladesh India border fisher in mangrove. Tide gauge writes THLD magic THLD with sea level time series contaminated by multi constituent tides M2 S2 O1 K1 sensor gain drift mean offset noise ship wake spikes. M2 lunar semidiurnal period twelve point four two zero six hours is grading quantity true physical amplitude before gain. Raw RMS or peak overestimates thirty to eighty percent due to S2 O1 K1 blending and spikes and drift.

Rig writes THLD little endian with header magic THLD version dtype n dt gain at twenty mean at twenty four freq count at twenty eight data offset at thirty two can be forty eight sixty four eighty ninety six one twenty eight and gain zero point eight five to one point three five hidden one point two two at ninety six. Ignore gain fails twenty two percent and offset hardcoded fails ninety six one twenty eight.

Inside sea level is sum of M2 S2 O1 K1 plus drift plus mean plus noise plus spikes. M2 is what counts. Drift and mean bias background, spikes are far outliers, S2 O1 K1 cause blending.

What works is robust estimation then separation. Use median and median absolute deviation for noise floor from dimmest fraction so tide does not bias, linear detrend least squares to remove drift using inliers, reject far spikes beyond few sigma, then multi frequency harmonic fit for M2 S2 O1 K1 via normal equations to isolate M2 amplitude, then divide by gain. Sample one point six five meters.

Completion oracle three of three deterministic thirteen of thirteen pytest including ninety six one twenty eight plus random plus extra plus naive RMS fails and gain ignored fails. Avocado one of five due to multi constituent plus drift plus spikes plus gain. Opus zero of five GPT zero of five.

Model Analysis failure modes: no median overcounts, no detrend overcounts drift, no spike rejection overcounts spikes, single frequency RMS overcounts blending thirty to eighty percent, hardcoded gain fails twenty two percent, hardcoded offset fails ninety six one twenty eight.

Anti cheating varied n dt gain mean drift amps phases noise seed spikes placement random temp names input_h8i3.thld so constant fails. Secure runner audit hook blocks tests and b64decode and pathlib tricks. Reward via python I S ctrf json.

Tags sundarbans tidal M2 amplitude THLD harmonic recovery gain calibration payload offset human story

Author Tosin Daniel Jimoh purple29th at meta.com


## Files

* /app/solve.py you write last token meters physical M2
* /app/data/scene.thld sample one point six five
* Dockerfile python slim pytest
* solution/solve.py oracle
* tests/_gen.py generates
* test_outputs.py secure verifier random names

## Completion Rates

Oracle three of three deterministic
Avocado one of five
Opus zero of five GPT zero of five

## Model Analysis

No median overcounts, no detrend fails drift, no spike rejection fails spikes, single freq RMS fails blending, hardcoded gain fails 22, hardcoded offset fails 96/128.

## Anti-Cheating

Varied n dt gain mean drift amps phases noise spikes random temp names so constant fails. Secure runner blocks tests.

## Tags

Tags sundarbans tidal m2 true amplitude human story

Author Tosin Daniel Jimoh purple29th at meta.com
