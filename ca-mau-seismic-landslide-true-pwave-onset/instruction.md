I am Linh from Ca Mau at very south of Vietnam Mekong delta, we live on soft mud and landslide kills houses near river bank during monsoon. We have cheap seismometer made from geophone that writes custom binary SEIS magic SEIS with velocity trace smear from sensor response but energy conserved. Need true p wave onset time in nanoseconds for early warning, not smeared cloud. Contains main rupture that is sharp plus tiny aftershock dots far away to ignore.

I need tool that tells true onset in nanoseconds as last token.

Please make file at /app/solve.py. We call python /app/solve.py path and last token ns.

Example at /app/data/scene.seis about one hundred twenty five ns. Hidden evaluation uses totally different traces I made with new num samples sampling interval gain blur with random temp file names like input_g7h2.seis payload offset forty eight to one twenty eight and gain.

File layout seis little endian with embed fix.

Four bytes ascii SEIS at zero.
Four bytes uint32 version at four.
Four bytes uint32 dtype code two means int16 sixteen means float32 at eight.
Four bytes uint32 num samples n at twelve.
Four bytes float32 sampling interval dt ns per sample at sixteen changes per file must read.
Four bytes float32 sx placeholder at twenty.
Four bytes float32 sy placeholder at twenty four.
Four bytes uint32 data offset at byte twenty eight where samples start can be forty eight sixty four eighty ninety six one twenty eight must parse not hardcoded sixty four.
Four bytes float32 multiplier gain at offset forty byte forty scales final ns sample one point zero hidden at ninety six is one point two two ignore fails twenty two percent.
At data offset you get n samples in dtype announced.

Scene file at /app/data/scene.seis uses offset sixty four gain one point zero but hidden uses ninety six one twenty eight plus forty eight eighty.

Inside each trace p wave onset is sharp rise but sensor shaper smears via Gaussian point spread so threshold overcounts smeared tails or undercounts thin extensions. Correct recovery is charge conservation calculus integral, true width samples equals sum baseline subtracted over pulse plus halo divided by plateau amplitude, onset equals width times sampling interval times multiplier plus baseline offset. Tiny aftershock specks far away ignore via mass filter.

Dockerfile python slim copies scene.seis not plse.

Inside each trace p wave onset is sharp rise but sensor shaper smears via Gaussian point spread so threshold overcounts smeared tails or undercounts thin extensions. Correct recovery is charge conservation calculus integral, true width samples equals sum baseline subtracted over pulse plus halo divided by plateau amplitude, onset equals width times sampling interval times multiplier plus baseline offset. Tiny aftershock specks far away ignore via mass filter.

Naive threshold fails thirty to fifty percent.

Energy preserved.

Coding rules parse bytes yourself only stdlib struct sys math random tempfile re. No numpy scipy.

Print ns as last token.

Files: /app/solve.py you write, /app/data/scene.seis sample, Dockerfile python slim pytest, solution/solve.py oracle bespoke reading payload start and multiplier and calculus integral plus halo growth, _gen.py only scene stale avoidance, test_outputs.py secure verifier runtime random names input_a3f9.seis plus payload ninety six one twenty eight and gain variants thirteen configs now, graded three percent.

Author Tosin Daniel Jimoh purple29th at meta.com
