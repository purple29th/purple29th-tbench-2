I am in cerebral organoid lab growing cortical organoids for hypoxia study. After 60 days the core starves and forms necrotic dead zone because oxygen cannot diffuse. We stain with propidium iodide and image with light sheet. Dead core glows bright, but tissue scattering plus light sheet PSF smears the glow everywhere so the dead region looks much bigger and fuzzier than its true size.

I need a program that reports the true physical necrotic core volume in cubic micrometers, not the smeared bright blob. Precision matters for oxygen diffusion model and drug dosing.

Make file `/app/solve.py`. We call `python /app/solve.py <scan_path>` and the last word you print is taken as the volume.

You get one example scan for local dev at `/app/data/scene.oncr`. You may read it while developing, but hidden grading uses different scans you have never seen, with different dimensions, voxel pitch, brightness, scattering strength, tissue absorption. Do not hardcode numbers from example. Your solver must work on any file path given as first arg. Hardcoding sample volume will fail hidden checks.

Format .oncr is a custom binary for organoid necrotic core volumes. Everything is little endian.

* offset 0 magic `ONCR` four ASCII bytes.
* offset 4 version uint32.
* offset 8 dtype code uint32. 2 means int16 voxels, 16 means float32 voxels.
* offset 12 three uint32 values for voxel counts per axis, nx, ny, nz.
* offset 24 three float32 values for micrometers per voxel per axis, sx, sy, sz. These change per file and must be read from header.
* offset 36 uint32 data offset where voxel values start.
* after data offset nx times ny times nz values in announced dtype, x fastest, so linear index for x y z is `x + nx * (y + ny * z)`.

Each volume contains one solid necrotic core where dead cells accumulate PI. The centre is flat and bright where staining saturates, the border is dimmer with partial fill smeared by tissue scattering and light sheet PSF. There is flat ambient autofluorescence background plus camera noise. Some scans have one to three tiny bright specks far away from isolated apoptotic debris that must be ignored. Keep only the main connected dead mass using 26 neighbour connectivity.

Threshold counting cannot be precise. A low cutoff includes huge scattering halo and overcounts by eighty to one hundred thirty percent. A high cutoff misses thin finger like necrotic extensions into the cortical plate that never get bright enough and undercounts by thirty to fifty percent. No fixed cutoff works across files because PI brightness, tissue clarity, scattering width, and background change per organoid batch. The blurry images give the best clue where fluorescence is most concentrated, not how many bright voxels there are. The true core is flat but hidden by scattering noise.

The blur spreads photons but does not create or destroy fluorescence energy. That physics makes precise volume recovery possible despite smear, but using it requires separating the main core from far specks, estimating autofluorescence background without bias from the core itself, estimating the true saturated PI level without being fooled by noise, and deciding how far the faint halo extends without merging debris specks. That is the hard part.

Simple shortcuts are off by large margin. Grading is at three percent tolerance. Only a genuine precise method passes.

Implementation constraints. Parse bytes yourself using only the standard library. Allowed stdlib modules include `struct`, `sys`, `math`, `random`, `tempfile`, `re`. The following are banned and will be rejected by `test_from_scratch`. `numpy`, `scipy`, `skimage`, `cv2`, `PIL`, `Pillow`, `networkx`, `igraph`, `imageio`, `pandas`, `torch`, `tensorflow`, `socket`, `multiprocessing`, `glob`, `pathlib`, `os`, `io`, `posixpath`, `ntpath`, `genericpath`, plus any array, imaging, or graph helper library. Banned calls include `eval`, `exec`, `compile`, `__import__`, `chr`. Banned runtime tricks include `subprocess`, `os.system`, `os.popen`, `os.exec`, `os.fork`, `os.walk`, `os.listdir`, `os.scandir`, `os.open`, `pty`, `importlib`, `runpy`, `ctypes`, filesystem listing, and any obfuscation that hides paths using `chr()`, `bytes.fromhex`, `base64`, `b64decode`, `bytearray`, `bytes([...])` tricks, or string concatenation that builds forbidden paths. Do not attempt to open or list the `/tests` directory, and do not reference `test_outputs`, `heldout`, `reference_volume`, `_gen`, `GEOM_TRUTH`, or `geometric_truth` in your solver source. Your solver must work on random temporary files, not hardcoded paths.

Print the volume in cubic micrometers as the last word on stdout.
