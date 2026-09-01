I am Rahim from Sundarbans Bangladesh India border, fisher in mangrove. Tide gauge writes THLD magic THLD with sea level time series contaminated by multi constituent tides M2 S2 O1 K1 sensor gain drift skew noise ship wake spikes. M2 lunar semidiurnal period twelve point four two zero six hours is grading quantity. Raw RMS overestimates thirty to eighty percent due to blending.

I need tool that tells true M2 amplitude meters.

Please make file at /app/solve.py last token meters.

Example at /app/data/scene.thld about one point two meters. Hidden random names input_*.thld with data offset forty eight to one twenty eight gain zero point eight five to one point three five.

File layout thld little endian four bytes ascii THLD version dtype num samples sampling interval hours data offset multiplier at forty.

Inside need robust background median MAD detrend linear least squares reject far outliers perform multi frequency linear least squares M2 S2 O1 K1 via normal equations Gaussian elimination isolate M2 amplitude correct by gain.

Naive RMS fails.

Coding rules only stdlib.

Print meters as last token.

Author Tosin Daniel Jimoh
