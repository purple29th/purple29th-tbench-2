You are in a ceramics additive lab inspecting sintered silicon carbide parts made by binder jetting plus sintering. After firing, internal pores remain that hurt strength. Micro-CT sees them but the X-ray focal spot is not a point and Compton scatter spreads signal everywhere, so each pore glows as a large fuzzy cloud much bigger than its true solid void.

Create a program that reports the true physical size of the main internal pore in cubic millimetres, not the smeared X-ray cloud. Precision matters for fracture prediction.

Your program must be saved as `/app/solve.py`. It will be invoked as `python /app/solve.py <scan_path>` and the last word it prints will be taken as the volume.

You are provided one example scan for local testing at `/app/data/scene.cspv`. You may read this file while developing, but hidden grading uses different scans you have never seen, with different dimensions, spacings, brightness, ceramic density, and voxel pitch, passed as random temporary files. Do not hardcode numbers or paths from the example; your solver must work on any file path given as the first argument. Hardcoding the sample volume will fail the hidden volume checks.

Format .cspv is a custom binary for ceramic sinter pore volumes. Everything is little-endian:

* Offset 0: magic `CSPV` four ASCII bytes.
* Offset 4: version uint32.
* Offset 8: dtype code uint32. 2 means int16 voxels, 16 means float32 voxels.
* Offset 12: three uint32 values for voxel counts per axis, nx, ny, nz.
* Offset 24: three float32 values for millimetres per voxel per axis, sx, sy, sz. These change per file and must be read from the header.
* Offset 36: uint32 data offset where voxel values start.
* After data offset: nx * ny * nz values in the announced dtype, x fastest, so linear index for x,y,z is `x + nx * (y + ny * z)`.

Each volume contains one solid pore where signal is negative contrast (dark void) stored as inverted bright signal after inversion for easier processing: the pore interior is flat and hot where inverted void signal saturates, the border is dimmer with partial fill smeared by X-ray blur. There is a flat ambient background plus sensor noise. Some scans have one or two tiny bright specks far away from powder artefacts that must be ignored. Keep only the main connected pore mass using 26-neighbour connectivity.

Threshold counting cannot be precise. A low cutoff includes a huge halo and overcounts by eighty to one hundred thirty percent. A high cutoff misses thin sintering cracks that never get bright enough and undercounts by thirty to fifty percent. No fixed cutoff works across files because brightness and diffusion width change. The blurry images give the best clue where signal is most concentrated, not how many bright voxels there are. The true core is flat but hidden by blur noise.

The blur spreads energy but does not create or destroy signal. That physics makes precise volume recovery possible despite smear, but using it requires separating the main pore from far specks, estimating background without bias from the pore itself, estimating the true concentrated level without being fooled by noise, and deciding how far the faint halo extends without merging specks. That is the hard part.

Simple shortcuts are off by a large margin. Grading is at three percent tolerance; only a genuine precise method passes.

Implementation constraints: parse bytes yourself using only the standard library. Allowed stdlib modules include `struct`, `sys`, `math`, `random`, `tempfile`, `re`. The following are banned and will be rejected by `test_from_scratch`: `numpy`, `scipy`, `skimage`, `cv2`, `PIL`, `Pillow`, `networkx`, `igraph`, `imageio`, `pandas`, `torch`, `tensorflow`, `socket`, `multiprocessing`, `glob`, `pathlib`, `os`, `io`, `posixpath`, `ntpath`, `genericpath`, plus any array, imaging, or graph helper library. Banned calls include `eval`, `exec`, `compile`, `__import__`, `chr`. Banned runtime tricks include `subprocess`, `os.system`, `os.popen`, `os.exec`, `os.fork`, `os.walk`, `os.listdir`, `os.scandir`, `os.open`, `pty`, `importlib`, `runpy`, `ctypes`, filesystem listing, and any obfuscation that hides paths using `chr()`, `bytes.fromhex`, `base64`, `b64decode`, `bytearray`, `bytes([...])` tricks, or string concatenation that builds forbidden paths. Do not attempt to open or list the `/tests` directory, and do not reference `test_outputs`, `heldout`, `reference_volume`, `_gen`, `GEOM_TRUTH`, or `geometric_truth` in your solver source. Your solver must work on random temporary files, not hardcoded paths.

Print the volume in mm3 as the last word on stdout.
