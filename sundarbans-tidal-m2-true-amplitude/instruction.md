I am Rahim from Sundarbans mangrove forest on border of Bangladesh and India, I am fisher and my boat depends on tide. My grandfather taught me tide tables but sea level rise changed them. We have tide gauge that writes THLD magic THLD with sea level time series contaminated by multi constituent tides M2 S2 O1 K1 sensor gain drift skew noise ship wake spikes from tourist boats. M2 lunar semidiurnal period twelve point four two zero six hours is grading quantity. Raw RMS or peak overestimates thirty to eighty percent due to S2 K1 O1 blending and spikes. I need true M2 amplitude meters for navigation.

I need tool that tells true M2 amplitude meters as last token.

Please make file at /app/solve.py. We call python /app/solve.py path last token meters.

Example at /app/data/scene.thld about one point two meters. Hidden uses totally different series with new num samples sampling interval gain drift with random temp names like input_h8i3.thld.

File layout thld little endian.

Four bytes ascii THLD.
Four bytes uint32 version.
Four bytes uint32 dtype two int16 sixteen float32.
Four bytes uint32 num samples.
Four bytes float32 sampling interval hours per sample.
Four bytes uint32 data offset where samples start can be forty eight sixty four eighty ninety six one twenty eight.
Four bytes float32 multiplier at offset forty scales final meters sample one point zero hidden at ninety six one point two two ignore fails twenty two percent.
At offset you get num samples in dtype.

Inside need robust background median lower half median absolute deviation to estimate noise, detrend via linear least squares to remove drift, reject far outliers beyond three sigma ship wake spikes, perform multi frequency linear least squares M2 S2 O1 K1 via normal equations four by four and Gaussian elimination to isolate M2 amplitude, correct by gain.

Naive RMS fails.

Coding rules only stdlib struct sys math random.

Print meters as last token.

Files: /app/solve.py you write, /app/data/scene.thld sample, Dockerfile, solution/solve.py oracle bespoke reading payload start and multiplier and least squares with Gaussian elimination, _gen.py generates thld with drift and spikes, test_outputs.py secure verifier runtime random names input_a3f9.thld plus payload ninety six one twenty eight and gain variants thirteen configs, graded three percent.

Author Tosin Daniel Jimoh purple29th at meta.com
