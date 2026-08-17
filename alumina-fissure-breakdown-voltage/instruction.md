I work on anodized aluminum oxide for high voltage capacitor foils. We grow thick alumina by anodization in acid bath. Field assisted dissolution sometimes creates elongated fissures along electric field direction. Those fissures are weak spots where dielectric breakdown starts and voltage rating drops. I need to bin foils by total breakdown voltage drop from those fissures.

We image fissures with X-ray fluorescence where gaps glow bright. Scintillator diffusion and lens point spread smear glow so direct bright counting overcounts volume by 80 to 130 percent. A low cutoff includes huge halo and doubles voltage, a high cutoff clips thin tails that are dim from partial fill and loses third to half. No fixed cutoff works because background and blur vary per foil lot.

Please make a file at /app/solve.py. We run python /app/solve.py /path/to/scan.aafv and take last printed token as volts.

There is one example at /app/data/scene.aafv for local debugging, about 8 V. Hidden evaluation uses completely different volumes I make with random names like input_a3f9.aafv, new dimensions, pitch, thickness, brightness, diffusion, gain. Hardcoding sample fails hidden.

File format is custom binary AAFV, little endian:

- Bytes 0 to 3: ASCII AAFV
- Bytes 4 to 7: version uint32
- Bytes 8 to 11: dtype id 2 is int16, 16 is float32
- Bytes 12 to 23: three uint32 nx ny nz counts
- Bytes 24 to 35: three float32 sx sy sz mm per voxel anisotropic and change per lot, must be read
- Bytes 36 to 39: uint32 data offset where payload begins, varies 32, 40, 48, 64, 80, 96, 128, must be respected
- Bytes 40 to 43: float32 gain trim scaling voltage, varies 0.85 to 1.35 per file, sample has 1.0 hidden cases like 96 use 1.22 and fail if ignored
- At data offset: nx*ny*nz samples in dtype, x fastest linear = x + nx*(y + ny*z)

Inside each volume there are gaps. The gaps that count are elongated fissures along field direction, long and thin. Some foils have two separate elongated fissures far apart that both count and must be summed for total volume before voltage conversion, so keeping only biggest fails by 40 to 50 percent.

Two artefact types to ignore: round etch pits from acid attack that are compact near spherical, and tiny bright dust specks far away in corners like (5,5,5) and (75,75,20) from window contamination. If you sum whole volume you pick up dust energy 6 to 12 percent per speck and voltage overcounts. If you keep round pits you overcount.

Blur spreads energy but does not create or destroy photons, so total glow over fissure plus its faint skirt divided by true interior brightness gives true voxel count. Using that requires isolating main elongated fissures from far specks and round pits, estimating background without bias from fissure itself, estimating concentrated interior level despite noise, and deciding how far faint halo extends without bridging to dust. That is the hard part.

Calibration from lab: each cubic mm of fissure lowers breakdown by 0.85 volts times gain trim. So voltage = recovered volume *0.85*gain. You first recover true fissure volume from smeared cloud, then compute voltage.

Simple heuristics are far outside 3 percent tolerance, only careful physical reconstruction meets it.

Rules: parse bytes yourself using only stdlib. Allowed helpers struct sys math random tempfile re. Banned libs numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath shutil ctypes importlib runpy. Banned calls eval exec compile __import__ chr ord breakpoint bytes bytearray. Banned tricks subprocess os system popen exec fork walk listdir scandir open pty filesystem listing or hiding forbidden names with chr bytes fromhex base64 b64decode bytearray tricks. Do not open or list /tests. Do not reference test_outputs heldout reference_voltage _gen GEOM_TRUTH geometric_truth in solver. Must work on random temp paths.

Print breakdown voltage drop in volts as last token.
