I am Rahim from Sundarbans mangrove forest on border of Bangladesh and India. I am fisher and my boat depends on tide. My grandfather taught me tide tables but sea level rise changed them. We have tide gauge that writes THLD file with sea level time series. It is messy: M2 S2 O1 K1 tides all mixed, sensor gain that drifts the amplitude, mean offset, linear drift from subsidence, noise, and ship wake spikes from tourist boats that are far outliers. M2 lunar semidiurnal is what I need for navigation, period twelve point four two zero six hours. Other constituents are S2 twelve hours, O1 twenty five point eight one nine three four hours, K1 twenty three point nine three four four seven hours. These blend and cause naive RMS or peak to overestimate thirty to eighty percent, and spikes make it worse.

I need a small tool that tells true physical M2 amplitude in meters before gain, as last token.

Please make file at /app/solve.py. We call python /app/solve.py path and last token is meters.

There is one example you can try at /app/data/scene.thld inside container, about one point six five meters physical amplitude. Hidden evaluation uses totally different series I made with new num samples sampling interval gain mean offset drift spikes with random temp file names like input_h8i3.thld. So you cannot hardcode.

File layout thld little endian.

Four bytes ascii THLD at zero.
Four bytes uint32 version at four.
Four bytes uint32 dtype code two means int16 scaled by thousand sixteen means float32 at eight.
Four bytes uint32 num samples n at twelve.
Four bytes float32 sampling interval dt seconds per sample at sixteen, changes per file must read.
Four bytes float32 sensor gain at twenty that scales observed values observed equals true times gain, hidden uses one point two two at ninety six and zero point eight five to one point three five range, ignore fails twenty two percent.
Four bytes float32 mean offset at twenty four.
Four bytes uint32 freq count at twenty eight.
Four bytes uint32 data offset at thirty two where samples start can be forty eight sixty four eighty ninety six one twenty eight must parse not hardcoded sixty four.
At data offset you get n samples in dtype announced.

Inside sea level is sum of tides plus drift plus mean plus noise plus spikes. You need to isolate M2 from the mixture while handling drift and spikes.

I tried simple methods and they fail. RMS includes all constituents and overestimates, peak picks spikes, mean biases.

You need to handle background and drift that vary per file, and spikes that are far from regular tide, and blending of S2 O1 K1 with M2. If you can separate them you land within grading tolerance three percent.

Coding rules. You must parse bytes yourself only stdlib struct sys math random. You cannot use numpy scipy etc. Do not try to open or list tests folder. Your solver must work on any random temp path.

Print physical M2 amplitude meters as last printed token.

Author Tosin Daniel Jimoh purple29th at meta.com
