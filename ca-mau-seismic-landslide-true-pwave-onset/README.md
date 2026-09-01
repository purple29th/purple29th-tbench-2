# ca mau seismic landslide true pwave onset

## Description

I am Linh from Ca Mau Mekong delta Vietnam landslide early warning. We have seismometer that writes custom binary SEIS magic SEIS with velocity trace smear from sensor response but conserves energy. Need true p wave onset time in nanoseconds not smeared cloud. Contains main rupture plus tiny aftershock dots to ignore far away.

I need tool that tells me true onset ns.

Please make file at /app/solve.py. We call python /app/solve.py path and last token ns.

Example at /app/data/scene.seis about one hundred twenty five ns. Hidden random names input_*.seis with new num samples dt gain blur data offset forty eight sixty four eighty ninety six one twenty eight.

File layout seis little endian.
Four bytes ascii SEIS.
Four bytes uint32 version one.
Four bytes uint32 dtype two means int16 sixteen means float32.
Four bytes uint32 num samples n.
Four bytes float32 sampling interval dt ns per sample changes per file must read.
Four bytes uint32 data offset at byte twenty eight where samples start can be forty eight sixty four eighty ninety six one twenty eight must parse.
Four bytes float32 multiplier at offset forty scales final ns sample one point zero hidden at ninety six is one point two two ignore fails twenty two percent.
At data offset you get n samples in dtype announced.

Inside each trace p wave onset is sharp rise but sensor shaper smears via Gaussian PSF so threshold overcounts smeared tails or undercounts thin extensions. Correct recovery is charge conservation integral true width samples equals sum baseline subtracted over pulse plus halo divided by plateau amplitude onset equals width times dt times multiplier plus baseline offset. Tiny aftershock specks far away ignore via mass filter keep mass greater than zero point three five times biggest.

Naive threshold fails thirty to fifty percent.

Energy preserved blur conserves sum.

Coding rules parse bytes yourself only stdlib struct sys math random tempfile re no numpy scipy skimage cv2 PIL etc. No tests access.

Print ns as last token.

Files: /app/solve.py you write last token ns, /app/data/scene.seis sample about one hundred twenty five ns about fifty samples, Dockerfile python slim pytest, solution/solve.py oracle bespoke reading payload start at twenty eight and multiplier at forty and robust background dimmest thirty percent plus MAD sigma plus component mass filter plus plateau top eight average plus halo growth sixty steps, _gen.py only scene stale avoidance, test_outputs.py secure verifier runtime random names input_a3f9.seis plus payload ninety six one twenty eight forty eight eighty and gain variants thirteen configs.

Completion Oracle three of three, Avocado zero to one of five due to onset pick plus multiplier plus halo.

Model Analysis low threshold grabs smear and overcounts thirty to fifty percent, high clips loses half, no baseline inflates, ignoring multiplier fails.

Anti Cheating varied width height pitch brightness base blur multiplier seed far placement random temp names so constant fails. Secure runner audit hook blocks tests.

Tags seismic p wave onset landslide Ca Mau SEIS halo recovery gain calibration payload offset human story

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

Tags ca mau seismic landslide true pwave onset human story

Author Tosin Daniel Jimoh purple29th at meta.com
