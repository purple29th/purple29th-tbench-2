I am Rahim from Sundarbans mangrove forest on border of Bangladesh and India, I am fisher and my boat depends on tide. My grandfather taught me tide tables but sea level rise changed them. We have tide gauge that writes THLD magic THLD with sea level time series contaminated by multi constituent tides M2 S2 O1 K1 sensor gain drift mean offset noise ship wake spikes from tourist boats. M2 lunar semidiurnal period twelve point four two zero six hours is grading quantity. Raw RMS or peak overestimates thirty to eighty percent due to S2 K1 O1 blending and spikes. I need true M2 amplitude meters for navigation.

I need tool that tells true M2 amplitude meters as last token.

Please make file at /app/solve.py. We call python /app/solve.py path last token meters.

There is one example you can try at /app/data/scene.thld inside container, about one point six five meters physical amplitude before gain. Hidden evaluation uses totally different series I made with new num samples sampling interval gain mean offset drift spikes with random temp file names like input_h8i3.thld. So you cannot hardcode.

File layout thld little endian.

Four bytes ascii THLD at zero.
Four bytes uint32 version at four.
Four bytes uint32 dtype code two means int16 scaled by thousand sixteen means float32 at eight.
Four bytes uint32 num samples n at twelve.
Four bytes float32 sampling interval dt seconds per sample at sixteen changes per file must read.
Four bytes float32 sensor gain at twenty that scales observed values observed equals true times gain, hidden at ninety six uses one point two two ignore fails twenty two percent.
Four bytes float32 mean offset at twenty four.
Four bytes uint32 freq count at twenty eight.
Four bytes uint32 data offset at thirty two where samples start can be forty eight sixty four eighty ninety six one twenty eight must parse not hardcoded sixty four.
At data offset you get n samples in dtype announced.

Inside sea level is sum of M2 S2 O1 K1 tides plus linear drift plus mean plus noise plus occasional ship wake spikes positive or negative Far outlier. M2 is biggest but S2 O1 K1 blend confuses RMS. Drift tricks mean estimate, spikes trick variance.

What works is robust stats then harmonic separation. Estimate background via median and median absolute deviation, detrend via linear least squares to remove drift, reject far outliers beyond few sigma that are ship spikes, then perform multi frequency fit for M2 S2 O1 K1 to isolate M2 amplitude, then correct by dividing by gain.

If you get background and detrending and spike rejection right you land within percent, grading allows three percent.

Coding rules. You must parse bytes yourself only stdlib struct sys math random. You cannot use numpy scipy etc. Do not try to open or list tests folder. Your solver must work on any random temp path.

Print meters as last printed token, physical M2 amplitude before gain.

Author Tosin Daniel Jimoh purple29th at meta.com
