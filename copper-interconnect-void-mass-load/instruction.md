I work on copper damascene interconnects that fail from electromigration. Under high current density the electron wind pushes copper atoms and leaves elongated voids along the line that cause opens. We inspect lines with X-ray CT fluorescence where the copper-depleted void region glows in dark field inversion bright, but diffusion plus lens smear makes the glow look much bigger than true void.

I need a small tool that tells me total void mass in milligrams for all elongated electromigration voids that are the real open defect. Some volumes have two or three separate elongated voids far apart that all count, you must sum them.

Please make a file at /app/solve.py. We call it like python /app/solve.py path to scan and we read final printed token as answer.

There is one example volume you can try at /app/data/scene.cuvd inside container. That is just for you to debug. Hidden evaluation uses completely different volumes I made with new sizes spacings defect thickness brightness diffusion and pitch passed as random temp file names. So you cannot hardcode numbers from example. If you hardcode example you will fail hidden.

File layout cuvd. My own tiny format, everything little endian.

Four bytes ascii CUVD.
Four bytes uint32 version.
Four bytes uint32 dtype code. Two means int16 voxels, sixteen means float32 voxels.
Twelve bytes are three uint32 nx ny nz counts per axis.
Twelve bytes are three float32 sx sy sz millimeters per voxel, this changes per file so you must read it.
Four bytes uint32 data offset where voxel array starts.
At data offset you get nx times ny times nz samples in dtype announced, X fastest, linear index is x plus nx times y plus ny times z.

Inside each cube there is voiding in a few places. The real defect is long copper depletion voids elongated along current that are the only ones that count. There are also compact barrier pits that are almost spherical and benign, you must not count them. In lab we keep a void when its bounding box longest side is at least eight and more than one point six times its shortest side. Pits are cubic. Some scans also have one to three very tiny bright dots far away that are dust on window, ignore them.

We use twenty six neighbour connectivity in three dimensions.

Calibration: lab shows density of copper is eight point nine six milligrams per cubic millimeter. So mass in mg equals volume mm3 times eight point nine six, but this void is copper missing, so mass of missing copper is volume times eight point nine six. So you first recover true void volume in cubic millimeters from smeared cloud, then multiply by eight point nine six to get mass of missing copper.

I tried naive brightness levels and they are hopeless. If I am generous and count everything slightly above background my mass nearly doubles. If I am strict and only count very bright voxels I lose thin tails and I lose third to half. Each file has different background gain and scatter width, so no fixed level works.

Energy is preserved despite smear. Total excess stays same, so bright counting fails but a conservation idea can work if you handle background bias that is pulled by the defect, the noise floor that varies per build, the far dust that must be ignored, and the interior level hidden by blur. You also must avoid counting skirt as background and avoid jumping to distant specks, and you must sum all separate elongated pieces not just the biggest.

If you get background and interior right you land within a percent, grading allows three percent.

Coding rules. You must parse bytes yourself, only stdlib. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any array imaging or graph library. Banned calls include eval exec compile __import__ chr. Banned tricks include subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list tests folder. Do not reference test_outputs heldout reference_mass _gen GEOM_TRUTH geometric_truth in solver. Your solver must work on any random temp path.

Print mass in mg as last printed token.
