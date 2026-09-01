# ca mau seismic landslide true pwave onset

## Description

I am Linh from Ca Mau Mekong delta Vietnam landslide early warning. We have seismometer that writes custom binary SEIS magic SEIS with velocity trace smear from sensor response but conserves energy. Need true p wave onset time in nanoseconds not smeared cloud. Contains main rupture plus tiny aftershock dots to ignore far away.

I need tool that tells me true onset ns.

Please make file at /app/solve.py. We call python /app/solve.py path and last token ns.

Example at /app/data/scene.seis about 1520 ns. Hidden random names input_*.seis with new sizes gain blur.

File layout seis little endian four bytes ascii SEIS four bytes uint32 version four bytes uint32 dtype two int16 sixteen float32 four bytes uint32 num samples four bytes float32 sampling interval ns four bytes uint32 data offset forty eight to one twenty eight four bytes float32 multiplier at forty scales final sample one point zero hidden at ninety six one point two two ignore fails twenty two percent.

Inside each trace p wave onset is sharp rise but smear makes it look broad. Tiny aftershock specks far away ignore.

We use connectivity one dimension.

Calibration onset equals integral over baseline removed divided by plateau.

Naive threshold fails.

Energy preserved.

Coding rules only stdlib struct sys math.

Print ns as last token.

Files: /app/solve.py you write last token ns, /app/data/scene.seis sample fifteen twenty ns, Dockerfile python slim pytest, solution/solve.py oracle bespoke reading payload start and multiplier, _gen.py only scene stale avoidance, test_outputs.py secure verifier runtime random names input_a3f9.seis plus payload ninety six one twenty eight and gain variants.

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
