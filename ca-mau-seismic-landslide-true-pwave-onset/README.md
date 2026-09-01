ca-mau-seismic-landslide-true-pwave-onset

Description

I am Linh from Ca Mau Mekong delta Vietnam, landslide early warning. We have seismometer that writes custom binary SEIS magic SEIS. It has velocity trace smear from sensor response but conserves energy. Need true p wave onset time in nanoseconds not smeared cloud. Contains main rupture plus tiny aftershock dots to ignore.

I need tool that tells me true onset ns.

Please make file at /app/solve.py. We call python /app/solve.py path and last token ns.

Example at /app/data/scene.seis about 1520 ns. Hidden random names input_*.seis with new sizes gain blur.

File layout seis little endian four bytes ascii SEIS four bytes uint32 version four bytes uint32 dtype two int16 sixteen float32 four bytes uint32 num samples four bytes float32 sampling interval ns four bytes uint32 data offset forty ei

Files

* /app/solve.py you write last token ca-mau-seismic-landslide-true-pwave-onset
* /app/data/sample inside container
* Dockerfile
* solution/solve.py oracle
* tests generate volumes

Completion Rates

Oracle three of three deterministic
Avocado zero to one of five due to lifecycle plus generation plus gain
Opus four of five GPT three of five

Model Analysis

No generation tracking shows stale image, no budget accrual loses fractional carry, no window reserve violates floor, no shape filter keeps round pores, no halo misses skirt, hardcoded offset fails ninety six one twenty eight, hardcoded gain fails twenty two percent.

Anti Cheating

Varied dims spacing random names secure runner blocks tests.

Tags ca mau seismic landslide true pwave onset human story

Author Tosin Daniel Jimoh purple29th at meta.com
