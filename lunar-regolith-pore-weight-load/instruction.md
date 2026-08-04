I work on lunar ISRU sintered regolith for habitat bricks. We take JSC-1A simulant, reduce with hydrogen, then sinter in solar furnace. Residual hydrogen leaves round sealed pores with trapped gas that affect launch weight and thermal conductivity. I need to know total weight of those pores under lunar gravity to manifest for Starship.

We image pores with helium ion microscope fluorescence where gas glows bright. Scintillator diffusion plus lens blur smears glow so counting bright voxels directly overcounts volume by 80 to 130 percent.

I need a small tool that tells me total weight in micro Newtons under lunar gravity for all round pores together.

Some bricks have two separate round pores far apart. Both count. You must sum their volumes first, then convert to weight.

Please make a file at /app/solve.py. We run python /app/solve.py /path/to/scan.lrpw and read last printed token as micro Newtons.

There is one example at /app/data/scene.lrpw for local debugging. Hidden evaluation uses completely different volumes I made with new sizes, spacings, thickness, brightness, diffusion, pitch. They are passed as random temp file names like input_a3f9.lrpw. You cannot hardcode example numbers. Hardcoding sample fails hidden.

File format. Custom container extension lrpw, little endian. Layout:

- Bytes 0 to 3: ASCII LRPW tag.
- Bytes 4 to 7: uint32 version.
- Bytes 8 to 11: uint32 dtype id. 2 means int16, 16 means float32.
- Bytes 12 to 23: three uint32 nx ny nz voxel counts.
- Bytes 24 to 35: three float32 sx sy sz mm per voxel anisotropic and change per brick lot, you must read from header.
- Bytes 36 to 39: uint32 data offset telling where payload begins. Our writer uses varied padding, so offset can be 32, 40, 48, 64, 80, 96, 128. You must respect this field.
- Bytes 40 to 43: float32 gain trim that scales weight and varies 0.85 to 1.35 per file. Sample has 1.0 so effect hidden, hidden cases like offset 96 use 1.22 and fail if ignored.
- Bytes 40 onward to data offset: zero padding.
- At data offset: nx*ny*nz samples in dtype declared. X fastest, linear = x + nx*(y + ny*z).

What counts. Inside each brick there are voids. The voids that count are round sealed pores that are near spherical from trapped hydrogen. Those are the only pores that count.

Two artefact types to ignore:
- Elongated sinter necks along heat flow direction, long and thin.
- Tiny bright specks from dust on window in corners near (5,5,5) and (75,75,20), far from central pores.

Multi pore handling. Some volumes have 2 separate round pores far apart. Both count. Sum their volumes first then convert to weight. Keeping only biggest fails by 40 to 50 percent in those cases.

Dust filtering. After background estimation, keep only components whose total residual above background is at least 22 percent of strongest component. That drops far specks at (5,5,5). Some bricks have 1 to 2 such specks. This gate also keeps split parts of a large pore that may appear as separate blobs due to noise.

Shape rule. Use 26 neighbour connectivity. Build bright mask where residual above background exceeds 8 sigma. Measure bounding box on that bright mask. Keep a pore when its box has longest side at most 35 and longest at most 3 times shortest side. That keeps round pores even after anisotropic PSF smears a 5x5x5 pore to about 20x15x10, and drops elongated necks where longest at least 12 and more than 3 times shortest.

Background. Estimate background as median of lower 80 percent of voxel values. Noise sigma from MAD of lower half: sigma = 1.4826 * median(abs(value - median_lower_half)). Base drifts 40 to 95 counts between lots.

Halo growth. Total glow over pore plus faint skirt divided by true interior brightness gives true voxel count. To recover:

- Core brightness from mean of top 4 raw voxels inside kept pores, with 3x3x3 smoothed top 4 fallback.
- Seed region = kept pore voxels.
- Frontier grows outward shell by shell (26 neighbours). At each shell compute mean residual. Stop when mean drops to about 1.0 sigma noise floor, or after about 40 iterations. While growing skip voxels belonging to separate speck clusters to avoid bridging to dust.
- Sum residual over final region, divide by core brightness to get voxel count. Volume = count * sx * sy * sz.

Calibration. Lab measured regolith bulk density 1.5 mg per mm3. Lunar gravity 1.62 m/s2. So weight micro Newtons = volume mm3 * 1.5 * 1.62 * gain = volume * 2.43 * gain. You first recover true pore volume from smeared cloud, then compute weight.

Naive thresholds fail. Low threshold includes whole aureole and overcounts 80 to 130 percent, so weight high. High threshold clips thin edges, undercounts 30 to 50 percent, weight low. Each file has different background, gain, blur.

If you get background and core right you land within 1 percent. Grading allows 3 percent.

Coding rules. You must parse bytes yourself, only stdlib. Allowed libs struct sys math random tempfile re. Forbidden libs numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any imaging array graph lib. Forbidden calls eval exec compile __import__ chr ord breakpoint bytes bytearray. Forbidden tricks subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list tests folder. Do not reference test_outputs heldout reference_weight _gen GEOM_TRUTH geometric_truth in solver. Solver must work on any random temp path.

Print weight in micro Newtons as last printed token.
