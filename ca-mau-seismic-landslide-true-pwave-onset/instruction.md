I am Linh from Ca Mau at very south of Vietnam Mekong delta, we live on soft mud and landslide kills houses near river bank during monsoon. We have cheap seismometer made from geophone that writes custom binary SEIS magic SEIS with velocity trace smear from sensor response but energy conserved. Need true p wave onset time in nanoseconds for early warning, not smeared cloud. Contains main rupture that is sharp plus tiny aftershock dots far away to ignore.

I need tool that tells true onset in nanoseconds as last token.

Please make file at /app/solve.py. We call python /app/solve.py path and last token ns.

There is one example you can try at /app/data/scene.seis inside container, about one hundred twenty five ns. Hidden evaluation uses totally different traces I made with new num samples sampling interval gain blur and pitch with random temp file names like input_g7h2.seis. So you cannot hardcode.

File layout seis. My own tiny format little endian.

Four bytes ascii SEIS.
Four bytes uint32 version.
Four bytes uint32 dtype code two means int16 sixteen means float32.
Four bytes uint32 num samples n.
Four bytes float32 sampling interval dt ns per sample, this changes per file so you must read it.
Four bytes float32 sx placeholder mm.
Four bytes float32 sy placeholder.
Four bytes uint32 data offset at twenty eight where trace array starts, can be forty eight sixty four eighty ninety six one twenty eight must parse not hardcoded sixty four.
Four bytes float32 multiplier at offset forty that scales final ns sample one point zero hidden at ninety six uses one point two two ignore and you fail by twenty two percent.
At data offset you get n samples in dtype announced, X fastest.

Inside each trace p wave onset is sharp rise but sensor shaper smears via Gaussian point spread so threshold overcounts smeared tails or undercounts thin extensions. True width not recoverable by fixed level. There are also tiny aftershock specks far away that are dust on sensor window, ignore them. Some traces have two distant ruptures both count, sum them, biggest only fails.

Calibration onset equals true width times dt times multiplier. You first recover true width via conservation.

I tried naive brightness levels and they are hopeless. If I am generous and count everything slightly above background my onset nearly doubles. If I am strict and only count very bright samples I lose thin tails and lose third to half. Each file has different background gain and scatter width, no fixed level works.

Energy is preserved despite smear. Total excess stays same, so threshold fails but conservation idea can work if you handle background bias that is pulled by rupture, noise floor that varies per trace, far dust that must be ignored, interior level hidden by blur. You also must avoid counting skirt as background and avoid jumping to distant specks.

If you get background and interior right you land within percent, grading allows three percent.

Coding rules. You must parse bytes yourself only stdlib struct sys math random tempfile re. You cannot use numpy scipy scimage cv2 PIL Pillow networkx etc. Do not try to open or list tests folder. Your solver must work on any random temp path.

Print ns as last printed token.

Author Tosin Daniel Jimoh purple29th at meta.com
