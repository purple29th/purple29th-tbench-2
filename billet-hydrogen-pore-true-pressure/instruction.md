I work on continuous cast aluminum billet inspection. Hydrogen from humidity gets into the melt. During solidification it forms round sealed pores that hold pressurized gas. When we extrude, those pores open as surface blisters that fail QA. I need to know internal gas pressure in kilopascals to decide which billets need degas.

We image hydrogen with fluorescence where pores glow bright. Diffusion in the scintillator plus lens smear makes the glow look much bigger than the true pore. Counting bright voxels directly gives double volume.

I need a small tool that tells me total gas pressure in kPa for all round pores together.

Some billets have two separate round pores far apart. Both count. You must sum their volumes first, then convert to pressure via constant divided by volume.

Please make a file at /app/solve.py. We call it like python /app/solve.py /path/to/scan.hprr and we read the last printed token as answer in kPa.

There is one example volume you can try at /app/data/scene.hprr inside the container. That is just for local debugging. Hidden evaluation uses completely different volumes I made with new sizes, spacings, defect thickness, brightness, diffusion, and pitch. They are passed as random temp file names like input_a3f9.hprr. You cannot hardcode numbers from the example. If you hardcode the sample you will fail hidden.

File format — little endian, extension hprr:

| Bytes | Type    | Field |
|-------|---------|-------|
| 0-3   | ASCII   | `HPPR` magic |
| 4-7   | uint32  | version |
| 8-11  | uint32  | dtype id (2=int16, 16=float32) |
| 12-15 | uint32  | nx |
| 16-19 | uint32  | ny |
| 20-23 | uint32  | nz |
| 24-27 | float32 | sx mm/voxel |
| 28-31 | float32 | sy |
| 32-35 | float32 | sz |
| 36-39 | uint32  | data_offset |

`data_offset` can be 40, 48, 64, 80, 96, 128 — respect the header value. Bytes between header and payload are zero padding. At `data_offset` you have `nx*ny*nz` samples in the announced dtype, x fastest: index = x + nx*(y + ny*z). `sx`, `sy`, `sz`, `data_offset`, and dtype vary per billet heat and must be read.

What counts. Inside each cube there is hydrogen in a few places. The pores that count are near-spherical sealed pores that appear compact after accounting for smear. In practice a counted pore has a bounding-box longest span at most 35 voxels and at most 3× its shortest span (e.g., radii like 6,5,4 or 6,5,5 are counted; strongly elongated shapes are not). Those are the only pores that count; pores may appear anywhere in the volume including near the rim, and all compact pores count regardless of position.

Two artefact types to ignore:
- Elongated MnS stringers that are long along casting direction, typically axis-aligned boxes with longest side at least three times the shortest side, and strongly anisotropic ellipsoids whose bounding-box longest span exceeds 3× the shortest (or radii differ by more than ~2×).
- Tiny bright specks from dust on window, identified by small size: radius at most 3 voxels and volume under 150 voxels (much smaller than true pores which are several hundred voxels), or more generally any compact blob whose integrated mass is less than 0.35× the mass of the largest compact pore in that volume. Dust may appear near corners but is distinguished by size/mass, not solely by position.

Multi pore handling. Some volumes have 2 or 3 separate round pores far apart. All compact pores above the 0.35× mass threshold count. You must sum their volumes first, then convert to pressure via 780 / volume. Keeping only the biggest pore fails by 40 to 50 percent in those cases.

Why simple thresholds fail. If you are generous and count everything slightly above background, volume balloons 80–130% over, so pressure collapses 40–55% low. If you are strict and only count very bright voxels, you lose edges, volume shrinks 30–50%, pressure spikes 40–90% high. Each file has different background, gain, and blur.

Recovering true pore volume from the smeared glow is the core challenge — the signal is conserved but spread by the optics. Pressure is then 780 divided by total pore volume in mm³. If you recover volume accurately you land within 1 percent. Grading allows 3 percent.

Coding rules. You must parse bytes yourself, only stdlib. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any array imaging or graph library. Banned calls include eval exec compile __import__ chr. Banned tricks include subprocess os system popen exec fork walk listdir scandir pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list tests folder (the solver naturally needs to open the input file given as argv). Do not reference /tests test_outputs heldout tests/_gen GEOM_TRUTH geometric_truth reference_length in solver. Your solver must work on any random temp path.

Print pressure in kPa as last printed token.
