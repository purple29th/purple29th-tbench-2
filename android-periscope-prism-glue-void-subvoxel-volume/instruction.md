At the flagship Android camera line in Seoul, we assemble periscope telephoto units. The 5x periscope folds light with a big glass prism that is bonded to the plastic lens barrel using UV glue. If the dispenser leaves air, after UV cure you get sealed pockets inside the adhesive layer. Those pockets shift under OIS actuation and create moving flare spots that fail final image QA. We need an automated measurement of the pocket.

We screen every module on a 160-kilovolt micro-focus cone-beam CT. The scanner is not perfect. The focal spot has finite size, the scintillator bleeds, and the thick prism causes internal scatter. Effect is a smooth shift-invariant smear: total integrated signal over the whole volume stays same, but it is spread far beyond the real bubble. Visual inspection therefore overestimates size by factor two or more.

Write a solver:

Place Python code at /app/solve.py. It will be executed as `python /app/solve.py /app/data/scene.apcv` during development and as `python /app/solve.py <temporary_random_path>` during hidden grading. The program must output the physical volume of the principal glue bubble in cubic millimetres; the evaluation harness extracts the last whitespace-separated token and parses it as float. No hardcoding of the development file volume is allowed — hidden files have different dimensions, spacing, brightness, scatter kernel, baseline and noise, and are delivered via random temporary paths. A constant that matches only the sample will fail.

Container .apcv (Android Periscope Camera Void) — little-endian:

- 0x00: 4 bytes ASCII "APCV"
- 0x04: uint32 version
- 0x08: uint32 dtype id (2 = int16 little-endian, 16 = float32 little-endian)
- 0x0C: 3× uint32 nx, ny, nz (extent in voxels)
- 0x18: 3× float32 sx, sy, sz = millimetres per voxel along each axis, anisotropic, read from file, varies
- 0x24: uint32 offset = where voxel payload starts (header may have padding)
- At offset: nx*ny*nz samples in declared dtype, x index moves fastest: linear = x + nx*(y + ny*z). During export the contrast was inverted so air pockets appear bright.

Inside a volume: one large sealed adhesive bubble is the grading target, sometimes plus one or two isolated sub-millimetre bright specks far from it caused by dust on prism facet or lens surface. Specks must be excluded — keep only the biggest structure by integrated excess, using 26-neighbour 3D connectivity. The bubble has a uniform interior that is saturated bright, but edges are partial-volume dimmed and then further blurred by the CT point-spread. The rest of the crop is uniform glass/plastic background plus read noise.

Fixed thresholds do not work for this inspection: a low threshold picks up the surrounding glow that belongs to the bubble after blur and you over-estimate heavily; a very high threshold discards the slender glue tails that run along the prism chamfer, which never reach full brightness due to thin fill, and you under-estimate. Batch variation in tube brightness, prism absorption and blur width means no universal cutoff exists across modules. What is preserved is total excess signal, not number of bright voxels.

Exploiting that invariant is necessary for 3% relative accuracy, but implementation is non-trivial: estimate the background level of the surrounding material without being pulled by the bubble itself, estimate how much random variation the detector has, separate the dominant bubble from far dust, determine the interior plateau value that would be observed without blur and without being fooled by spikes, then gradually include surrounding faint region belonging to the bubble until its mean excess drops to noise level, stopping before you accidentally jump to a far speck. Missing the halo loses charge and under-reports, including dust over-reports.

We check your result with 3% relative tolerance. Simple intensity cutoffs are far outside.

From-scratch rule: `solve.py` is scanned with AST. Allowed imports only `struct sys math random tempfile re`. Any use of `numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath` or any array/image/graph helper will cause `test_from_scratch` to fail. Also banned are `eval exec compile __import__ chr`, plus runtime tricks `subprocess os.system os.popen os.exec os.fork os.walk os.listdir os.scandir os.open pty importlib runpy ctypes`, directory listing, and obfuscated path construction via `chr() bytes.fromhex base64 b64decode bytearray bytes([...])` etc. Do not attempt to open `/tests`, do not reference strings `test_outputs heldout reference_volume _gen GEOM_TRUTH geometric_truth` in your solver. Must work on any temporary file path.

Print volume mm3 as last token, e.g. 12.345
