I work on lunar ISRU sintered regolith for habitat bricks. We use JSC-1A simulant, hydrogen reduction, solar furnace sintering. Residual hydrogen leaves round sealed pores that affect launch weight and thermal performance. I need total weight of those pores under lunar gravity for Starship manifest.

We image pores with helium ion microscope fluorescence where gas glows bright. Scintillator diffusion and lens blur smear glow so direct counting overcounts volume by 80 to 130 percent. Low cutoff includes huge halo and doubles weight, high cutoff clips thin edges and loses third to half. No fixed cutoff works because background and blur vary per lot.

Please make a file at /app/solve.py. We run python /app/solve.py /path/to/scan.lrpw and read last printed token as micro Newtons.

There is one example at /app/data/scene.lrpw for local debugging, about 500 uN. Hidden evaluation uses completely different volumes I make with random names like input_a3f9.lrpw, new dimensions, pitch, thickness, brightness, diffusion, gain. Hardcoding sample fails hidden.

File format custom binary LRPW, little endian:

- Bytes 0 to 3: ASCII LRPW
- Bytes 4 to 7: version uint32
- Bytes 8 to 11: dtype id 2 is int16, 16 is float32
- Bytes 12 to 23: three uint32 nx ny nz counts
- Bytes 24 to 35: three float32 sx sy sz mm per voxel anisotropic and change per lot, must be read
- Bytes 36 to 39: uint32 data offset where payload begins, varies 32, 40, 48, 64, 80, 96, 128, must be respected
- Bytes 40 to 43: float32 gain trim scaling weight, varies 0.85 to 1.35 per file, sample has 1.0 hidden cases like 96 use 1.22 and fail if ignored
- At data offset: nx*ny*nz samples in dtype, x fastest linear = x + nx*(y + ny*z)

Inside each volume there are voids. The voids that count are round sealed pores from trapped hydrogen, near spherical. Some bricks have two separate round pores far apart that both count and must be summed for total volume before weight conversion, so keeping only biggest fails by 40 to 50 percent.

Two artefact types to ignore: elongated sinter necks along heat flow that are long and thin, and tiny bright dust specks far away in corners like (5,5,5) and (75,75,20) from window. If you sum whole volume you pick up dust energy 6 to 12 percent per dot and weight overcounts. If you keep elongated necks you overcount.

Blur spreads energy but does not create or destroy photons, so total glow over pore plus faint skirt divided by true interior brightness gives true voxel count. Using that requires isolating main round pores from far specks and elongated necks, estimating background without bias from pore itself, estimating concentrated interior level despite noise, and deciding how far faint halo extends without bridging to dust. That combination is the difficulty.

Calibration: lab measured bulk density 1.5 mg per mm3. Lunar gravity 1.62 m/s2. So weight micro Newtons = recovered volume *1.5*1.62*gain = volume*2.43*gain. You first recover true pore volume from smeared cloud, then compute weight.

Simple heuristics are far outside 3 percent tolerance, only careful physical reconstruction meets it.

Rules: parse bytes yourself using only stdlib. Allowed helpers struct sys math random tempfile re. Banned libs numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath shutil ctypes importlib runpy. Banned calls eval exec compile __import__ chr ord breakpoint bytes bytearray. Banned tricks subprocess os system popen exec fork walk listdir scandir open pty filesystem listing or hiding forbidden names with chr bytes fromhex base64 b64decode bytearray tricks. Do not open or list /tests. Do not reference test_outputs heldout reference_weight _gen GEOM_TRUTH geometric_truth in solver. Must work on random temp paths.

Print weight in micro Newtons as last token.
