You are in a surgical oncology lab assessing resected tissue labeled with gold nanocluster tumor markers. Under confocal microscopy the marked tumor fluoresces, but tissue scattering plus the Airy disk spreads fluorescence far beyond the lesion, so the volume looks much larger than its true extent.

Build a program that reports the true physical tumor volume in cubic millimetres, not the smeared glow. Accuracy matters for intraoperative dosing decisions.

Save your program as `/app/solve.py`. It will be run as `python /app/solve.py <scan_path>` and the final word it prints will be interpreted as the volume.

A single example scan for local development is available at `/app/data/scene.gvol`. You may read it, but hidden evaluation uses different scans with random temporary filenames that vary in grid size, voxel pitch, gold load, background, and blur. Do not hardcode values or paths from the example; the solver must interpret the header of any file given on the command line.

Format `.gvol` is a custom binary volume. All integers and floats are little-endian:

* Offset 0: magic `GVOL` four ASCII bytes.
* Offset 4: version uint32.
* Offset 8: dtype code uint32. Code 2 is int16 voxels, code 16 is float32 voxels.
* Offset 12: three uint32 values for voxel counts per axis, historically nx, ny, nz.
* Offset 24: three float32 values for millimetres per voxel per axis, sx, sy, sz. These change per file and must be read.
* Offset 36: uint32 data offset where voxel data starts.
* After offset: nx * ny * nz values in the announced dtype, x fastest, linear index `x + nx*(y + ny*z)`.

Inside each volume is one solid tumor region where gold concentration is high. The centre is flat and bright where concentration saturates, the rim is dimmer with partial volume and is further smeared by optics. The tissue has flat autofluorescent background plus sensor noise. Some scans contain one or two tiny bright clumps far from the main lesion caused by gold dust; ignore them and keep only the primary connected tumor using 26-neighbour connectivity.

Naive bright voxel counting is unreliable. A permissive brightness cutoff inflates the estimate because it includes the diffuse tails, while a strict cutoff excludes thin infiltrating strands that never become fully bright. No fixed cutoff is stable across samples.

Optics spreads photons but total collected fluorescence is preserved, which makes subvoxel recovery possible despite the blur. Exploiting that property requires isolating the main lesion from remote artefacts, estimating ambient background without bias from the lesion, estimating the concentrated interior level despite noise, and deciding how far the faint periphery extends without bridging to distant specks. That combination is the difficulty.

Simple heuristics are far outside tolerance. Grading requires three percent relative error; only a careful physical reconstruction meets it.

Implementation rules: parse bytes yourself with the standard library. Allowed modules include `struct`, `sys`, `math`, `random`, `tempfile`, `re`. The following are prohibited and checked in `test_from_scratch`: `numpy`, `scipy`, `skimage`, `cv2`, `PIL`, `Pillow`, `networkx`, `igraph`, `imageio`, `pandas`, `torch`, `tensorflow`, `socket`, `multiprocessing`, `glob`, `pathlib`, `importlib`, `runpy`, `ctypes`. Banned calls include `eval`, `exec`, `compile`, `__import__`, `chr`, `getattr`, `setattr`. Also forbidden are runtime tricks such as `subprocess`, `os.system`, `os.popen`, `os.symlink`, `os.link`, `os.path.realpath`, `os.path.readlink` monkeypatching, filesystem listing via `walk`, `listdir`, `scandir`, `rglob`, `glob()`, and path hiding via `chr()`, `bytes.fromhex`, `base64`, `b64decode`, `bytearray`, or string concatenation that builds forbidden paths including split literals like "/te"+"sts". Do not open or list `/tests`, `/tests/data`, `/app/data`, and do not reference `test_outputs`, `heldout`, `reference`, `_gen`, `scene.gvol`, `/app/data`, `GEOM_TRUTH`, `geometric_truth`, `reference_volume`, `symlink` in solver source. The solver must operate on random temporary files with random names, not hardcoded locations. The verifier secures runtime with an audit hook that saves original realpath/abspath before solver import, blocks symlink/link creation, chmod 000 /tests and /app/data during solver run, and evaluates static string concatenations to catch obfuscated paths.

Print the volume in mm3 as the last token on stdout.
