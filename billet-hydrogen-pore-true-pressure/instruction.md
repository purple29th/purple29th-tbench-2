I work on continuous cast aluminum billet inspection. Hydrogen from humidity gets into the melt. During solidification it forms round sealed pores that hold pressurized gas. When we extrude, those pores open as surface blisters that fail QA. I need to know internal gas pressure in kilopascals to decide which billets need degas.

We image hydrogen with fluorescence where pores glow bright. Diffusion in the scintillator plus lens smear makes the glow look much bigger than the true pore. Counting bright voxels directly gives double volume.

I need a small tool that tells me total gas pressure in kPa for all round pores together.

Some billets have two separate round pores far apart. Both count. You must sum their volumes first, then convert to pressure via constant divided by volume.

Please make a file at /app/solve.py. We call it like python /app/solve.py /path/to/scan.hprr and we read the last printed token as answer in kPa.

There is one example volume you can try at /app/data/scene.hprr inside the container. That is just for local debugging. Hidden evaluation uses completely different volumes I made with new sizes, spacings, defect thickness, brightness, diffusion, and pitch. They are passed as random temp file names like input_a3f9.hprr. You cannot hardcode numbers from the example. If you hardcode the sample you will fail hidden.

File format. Our scanner writes a custom container with extension hprr. All numbers are little endian. File layout:

- Bytes 0 to 3: ASCII HPPR tag.
- Bytes 4 to 7: uint32 version.
- Bytes 8 to 11: uint32 dtype id. 2 means int16, 16 means float32.
- Bytes 12 to 23: three uint32 nx ny nz voxel counts.
- Bytes 24 to 35: three float32 sx sy sz millimeters per voxel. These are anisotropic and change per billet heat, you must read them from header, not assume constant.
- Bytes 36 to 39: uint32 data offset that tells where payload begins. Our writer uses varied padding, so offset can be 32, 40, 48, 64, 80, 96, 128. You must respect this field.
- Bytes 40 onward up to data offset: zero padding.
- At data offset: nx * ny * nz samples in the dtype declared. X is fastest, so linear index = x + nx * (y + ny * z).

What counts. Inside each cube there is hydrogen in a few places. The pores that count are round sealed pores that are near spherical. Those are the only pores that count.

Two artefact types to ignore:
- Elongated MnS stringers that are long along casting direction, typically 13x3x6 voxels before smear.
- Tiny bright specks from dust on window in corners near (5,5,5) and (75,75,20), far from central pores.

Multi pore handling. Some volumes have 2 separate round pores far apart. Both count. You must sum their volumes first, then convert to pressure via 780 / volume. Keeping only the biggest pore fails by 40 to 50 percent in those cases.

Dust filtering. After background estimation, we keep only components whose total residual above background is at least 35 percent of the strongest component. That drops far specks at (5,5,5). Some billets have 1 to 3 such specks.

Shape rule. Use 26 neighbour connectivity. Build a bright mask where residual above background is more than 8 sigma. Measure bounding box on that bright mask. Keep a pore when its box has longest side at most 35 and longest at most 3 times shortest side. That keeps round pores even after anisotropic PSF smears a 5x5x5 pore to about 20x15x10, and drops stretched stringers where longest is at least 12 and more than 3 times shortest, which become 20x6x6 after smear. This is inverted versus tasks that kept elongated.

Background. We estimate background as median of lower 80 percent of voxel values. Noise sigma from MAD of lower half: sigma = 1.4826 * median(abs(value - median_lower_half)). Base drifts 40 to 95 counts between casts.

Halo growth. Total glow over pore plus faint skirt divided by true interior brightness gives true voxel count. To recover it, we do:

- Core brightness from mean of top 4 raw voxels inside kept pores, with a 3x3x3 smoothed top 4 fallback to avoid a spike.
- Seed region = kept pore voxels.
- Frontier grows outward shell by shell (26 neighbours). At each shell, compute mean residual. Stop when mean drops to about 1.0 sigma noise floor, or after about 40 iterations. While growing, skip any voxels that belong to separate speck clusters, so we do not bridge to dust.
- Sum residual over final region, divide by core brightness to get voxel count. Then volume = count * sx * sy * sz.

Calibration. Lab injected known hydrogen amount. Ideal gas law nRT gives constant 780 kPa * mm3. So pressure kPa = 780 / total pore volume in mm3. You first recover true pore volume from smeared cloud, then compute pressure.

Naive thresholds fail. If you are generous and count everything slightly above background, volume balloons 80 to 130 percent over, so pressure collapses 40 to 55 percent low. If you are strict and only count very bright voxels, you lose thin edges, volume shrinks 30 to 50 percent, pressure spikes 40 to 90 percent high. Each file has different background, gain, and blur.

If you get background and core right you land within 1 percent. Grading allows 3 percent.

Coding rules. You must parse bytes yourself, only stdlib. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any array imaging or graph library. Banned calls include eval exec compile __import__ chr. Banned tricks include subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list tests folder. Do not reference test_outputs heldout reference_charge _gen GEOM_TRUTH geometric_truth in solver. Your solver must work on any random temp path.

Print pressure in kPa as last printed token.
