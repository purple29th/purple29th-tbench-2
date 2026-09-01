I am Linh from Ca Mau Mekong delta Vietnam, landslide early warning. We have seismometer that writes custom binary SEIS magic SEIS. It has velocity trace smear from sensor response but conserves energy. Need true p wave onset time in nanoseconds not smeared cloud. Contains main rupture plus tiny aftershock dots to ignore.

I need tool that tells me true onset ns.

Please make file at /app/solve.py. We call python /app/solve.py path and last token ns.

Example at /app/data/scene.seis about 1520 ns. Hidden random names input_*.seis with new sizes gain blur.

File layout seis little endian four bytes ascii SEIS four bytes uint32 version four bytes uint32 dtype two int16 sixteen float32 four bytes uint32 num samples four bytes float32 sampling interval ns four bytes uint32 data offset forty eight to one twenty eight four bytes float32 multiplier at forty scales final.

Inside each trace p wave onset is sharp rise but smear makes it look broad. Tiny aftershock specks far away ignore.

We use connectivity one dimension.

Calibration onset equals integral over baseline removed divided by plateau.

Naive threshold fails.

Energy preserved.

Coding rules only stdlib struct sys math.

Print ns as last token.

Author Tosin Daniel Jimoh
