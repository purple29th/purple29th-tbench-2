I work on hot rolled steel plate inspection for manganese sulfide stringers. During rolling MnS inclusions stretch into long stringers along rolling direction that cause lamellar tearing when we weld. We inspect plates with fluorescent magnetic particle where MnS glows bright, but diffusion plus lens smear makes the glow look much bigger than true sulfide.

I need a small tool that tells me total stringer length in millimeters for the main elongated stringers.

Please make a file at /app/solve.py. We call it like python /app/solve.py path to scan and we read final printed token as answer.

There is one example volume you can try at /app/data/scene.strg inside container. That is just for you to debug. Hidden evaluation uses completely different volumes I made with new sizes spacings defect thickness brightness diffusion and pitch passed as random temp file names. So you cannot hardcode numbers from example. If you hardcode example you will fail hidden.

File layout strg. My own tiny format, everything little endian.

Four bytes ascii STRG.
Four bytes uint32 version.
Four bytes uint32 dtype code. Two means int16 voxels, sixteen means float32 voxels.
Twelve bytes are three uint32 nx ny nz counts per axis.
Twelve bytes are three float32 sx sy sz millimeters per voxel, this changes per file so you must read it.
Four bytes uint32 data offset where voxel array starts.
At data offset you get nx times ny times nz samples in dtype announced, X fastest, linear index is x plus nx times y plus ny times z.

Inside each cube there is sulfide in a few places. The real defect is long stringers along rolling direction that are the only ones that count. There are also compact MnS dots that are almost spherical and benign, you must not count them. In lab we keep a stringer when its bounding box longest side is at least eight and more than one point six times its shortest side. Dots are cubic. Some scans also have one to three very tiny bright dots far away that are dust on window, ignore them.

We use twenty six neighbour connectivity in three dimensions.

Calibration: lab shows cross section of a stringer is zero point one eight square millimeters. So length in mm equals volume mm3 divided by zero point one eight. So you first recover true sulfide volume in cubic millimeters from smeared cloud, then divide by zero point one eight to get length.

I tried naive brightness levels and they are hopeless. If I am generous and count everything slightly above background my length nearly doubles. If I am strict and only count very bright voxels I lose thin tips and I lose third to half. Each file has different background gain and scatter width, so no fixed level works.

Energy is preserved despite smear. The glow is moved into a skirt but total stays same, so counting bright voxels fails but a conservation idea can work if you handle the background bias that is pulled by the defect, the detector noise floor that drifts per coil, the far dust that looks bright but is not part of main stringer, and the interior level that is hidden by blur and partial occupancy. You also need to avoid counting the faint skirt as background and avoid jumping to a distant speck.

If you get background and interior right you land within a percent, grading allows three percent.

Coding rules. You must parse bytes yourself, only stdlib. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any array imaging or graph library. Banned calls include eval exec compile __import__ chr. Banned tricks include subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list tests folder. Do not reference test_outputs heldout reference_charge _gen GEOM_TRUTH geometric_truth in solver. Your solver must work on any random temp path.

Print length in mm as last printed token.
