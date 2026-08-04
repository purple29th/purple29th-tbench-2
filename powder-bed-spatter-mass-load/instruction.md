I work on laser powder bed fusion builds checking spatter defects. During printing the laser ejects hot spatter that gets trapped as elongated inclusions along gas flow that cause cracks. We inspect builds with X-ray CT fluorescence where spatter glows bright, but diffusion plus lens smear makes the glow look much bigger than true spatter.

I need a small tool that tells me total spatter mass in milligrams for the main elongated spatter.

Please make a file at /app/solve.py. We call it like python /app/solve.py path to scan and we read final printed token as answer.

There is one example volume you can try at /app/data/scene.spat inside container. That is just for you to debug. Hidden evaluation uses completely different volumes I made with new sizes spacings defect thickness brightness diffusion and pitch passed as random temp file names. So you cannot hardcode numbers from example. If you hardcode example you will fail hidden.

File layout spat. My own tiny format, everything little endian.

Four bytes ascii SPAT.
Four bytes uint32 version.
Four bytes uint32 dtype code. Two means int16 voxels, sixteen means float32 voxels.
Twelve bytes are three uint32 nx ny nz counts per axis.
Twelve bytes are three float32 sx sy sz millimeters per voxel, this changes per file so you must read it.
Four bytes uint32 data offset where voxel array starts.
At data offset you get nx times ny times nz samples in dtype announced, X fastest, linear index is x plus nx times y plus ny times z.

Inside each cube there is spatter in a few places. The real defect is long spatter along gas flow that are the only ones that count. There are also compact gas pores that are almost spherical and benign, you must not count them. In lab we keep a spatter when its bounding box longest side is at least eight and more than one point six times its shortest side. Pores are cubic. Some scans also have one to three very tiny bright dots far away that are dust on window, ignore them.

We use twenty six neighbour connectivity in three dimensions.

Calibration: lab shows density of solidified spatter is three point eight milligrams per cubic millimeter. So mass in mg equals volume mm3 times three point eight. So you first recover true spatter volume in cubic millimeters from smeared cloud, then multiply by three point eight to get mass.

I tried naive brightness levels and they are hopeless. If I am generous and count everything slightly above background my mass nearly doubles. If I am strict and only count very bright voxels I lose thin tails and I lose third to half. Each file has different background gain and scatter width, so no fixed level works.

What does work is energy preservation. Scatter does not create signal, it only moves it. So adding up background removed glow over spatter plus faint skirt and dividing by true interior brightness gives true voxel count. To make that work you need clean background from seventy percent lower median and noise from median absolute deviation of lower half, you need to seed bright voxels above four sigma and grow twenty six connected blobs, keep stretched spatter via stretch test and drop compact pores, you need robust interior level by smoothing each candidate with three by three by three neighbourhood mean then averaging top four inside main defect, and you need to grow outward shell by shell until average shell glow falls to about noise floor, skipping artefact voxels.

If you do those steps you land within a percent, grading allows three percent.

Coding rules. You must parse bytes yourself, only stdlib. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any array imaging or graph library. Banned calls include eval exec compile __import__ chr. Banned tricks include subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list tests folder. Do not reference test_outputs heldout reference_charge _gen GEOM_TRUTH geometric_truth in solver. Your solver must work on any random temp path.

Print mass in mg as last printed token.
