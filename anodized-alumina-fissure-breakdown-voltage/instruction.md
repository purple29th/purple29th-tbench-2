I work on anodized aluminum oxide for high voltage capacitor foils. We grow thick alumina by anodization in acid bath. Sometimes field assisted dissolution creates elongated fissures along electric field direction. Those fissures are weak spots where dielectric breakdown starts and voltage rating drops. I need to estimate total breakdown voltage drop from those fissures to bin foils.

We image fissures with X-ray fluorescence where alumina gaps glow bright. Diffusion in scintillator and lens point spread smears the glow so counting bright voxels directly overcounts volume by 80 to 130 percent.

I need a small tool that tells me total breakdown voltage drop in volts for all elongated fissures together.

Some foils have two separate elongated fissures far apart. Both count. You must sum their volumes first, then convert to voltage.

Please make a file at /app/solve.py. We run python /app/solve.py /path/to/scan.aafv and read last printed token as volts.

There is one example at /app/data/scene.aafv for local debugging. Hidden evaluation uses completely different volumes I made with new sizes, spacings, thickness, brightness, diffusion, pitch. They are passed as random temp file names like input_a3f9.aafv. You cannot hardcode example numbers. Hardcoding sample fails hidden.

File format. Custom container extension aafv, little endian. Layout:

- Bytes 0 to 3: ASCII AAFV tag.
- Bytes 4 to 7: uint32 version.
- Bytes 8 to 11: uint32 dtype id. 2 means int16, 16 means float32.
- Bytes 12 to 23: three uint32 nx ny nz voxel counts.
- Bytes 24 to 35: three float32 sx sy sz mm per voxel anisotropic and change per foil lot, you must read from header.
- Bytes 36 to 39: uint32 data offset telling where payload begins. Our writer uses varied padding, so offset can be 32, 40, 48, 64, 80, 96, 128. You must respect this field.
- Bytes 40 to 43: float32 gain trim that scales voltage and varies 0.85 to 1.35 per file. Sample has 1.0 so effect hidden, hidden cases like offset 96 use 1.22 and fail if ignored.
- Bytes 40 onward to data offset: zero padding.
- At data offset: nx*ny*nz samples in dtype declared. X fastest, linear = x + nx*(y + ny*z).

What counts. Inside each cube there are gaps. The gaps that count are elongated fissures along field direction. They are long and thin, not round.

Two artefact types to ignore:
- Round etch pits from acid attack, near spherical, about 3 to 4 voxels radius.
- Tiny bright specks from dust on window in corners near (5,5,5) and (75,75,20), far from central fissures.

Multi fissure handling. Some volumes have 2 separate elongated fissures far apart. Both count. Sum their volumes first then convert to voltage via 0.85 * gain. Keeping only biggest fails by 40 to 50 percent in those cases.

Dust filtering. After background estimation, keep only components whose total residual above background is at least 22 percent of strongest component. That drops far specks at (5,5,5). Some foils have 1 to 2 such specks. This gate also keeps split parts of a large fissure that may appear as separate blobs due to noise.

Shape rule. Use 26 neighbour connectivity. Build bright mask where residual above background exceeds 5 sigma. Measure bounding box on that bright mask. Keep a fissure when its box has longest side at least 12 and longest more than 1.5 times shortest side and at most 35. That keeps elongated fissures and drops round pits where longest at most 1.6 times shortest. This keeps field oriented fissures even after blur.

Background. Estimate background as median of lower 80 percent of voxel values. Noise sigma from MAD of lower half: sigma = 1.4826 * median(abs(value - median_lower_half)). Base drifts 40 to 95 counts between lots.

Halo growth. Total glow over fissure plus faint skirt divided by true interior brightness gives true voxel count. To recover:

- Core brightness from mean of top 4 raw voxels inside kept fissures, with 3x3x3 smoothed top 4 fallback to avoid spike.
- Seed region = kept fissure voxels.
- Frontier grows outward shell by shell (26 neighbours). At each shell compute mean residual. Stop when mean drops to about 1.0 sigma noise floor, or after about 40 iterations. While growing skip voxels belonging to separate speck clusters to avoid bridging to dust.
- Sum residual over final region, divide by core brightness to get voxel count. Volume = count * sx * sy * sz.

Calibration. Lab measured that each cubic mm of fissure gap lowers breakdown by 0.85 volts times gain trim. So voltage drop V = volume mm3 * 0.85 * gain. You first recover true fissure volume from smeared cloud, then compute voltage.

Naive thresholds fail. Low threshold includes whole aureole and overcounts volume 80 to 130 percent over, so voltage over 80 to 130 percent high. High threshold clips thin tails, undercounts 30 to 50 percent, voltage under 30 to 50 percent low. Each file has different background, gain, blur.

If you get background and core right you land within 1 percent. Grading allows 3 percent.

Coding rules. You must parse bytes yourself, only stdlib. Allowed libs struct sys math random tempfile re. Forbidden libs numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any imaging array graph lib. Forbidden calls eval exec compile __import__ chr ord breakpoint bytes bytearray. Forbidden tricks subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list tests folder. Do not reference test_outputs heldout reference_voltage _gen GEOM_TRUTH geometric_truth in solver. Solver must work on any random temp path.

Print breakdown voltage drop in volts as last printed token.
