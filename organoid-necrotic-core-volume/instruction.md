hey i am in cerebral organoid lab growing cortical organoids for hypoxia study. after 60 days the core starves and forms necrotic dead zone because oxygen cant diffuse. we stain with propidium iodide and image with light-sheet. dead core glows bright, but tissue scattering plus light-sheet PSF smears the glow everywhere so the dead region looks much bigger and fuzzier than its true size.

i need a program that reports the true physical necrotic core volume in cubic micrometers, not the smeared bright blob. precision matters for oxygen diffusion model and drug dosing.

make file `/app/solve.py`. we call `python /app/solve.py <scan_path>` and the last word you print is taken as the volume.

you get one example scan for local dev at `/app/data/scene.oncr`. you may read it while developing, but hidden grading uses different scans you have never seen, with different dimensions, voxel pitch, brightness, scattering strength, tissue absorption. do not hardcode numbers from example; your solver must work on any file path given as first arg. hardcoding sample volume will fail hidden checks.

format .oncr is a custom binary for organoid necrotic core volumes. everything little-endian:

* offset 0: magic `ONCR` four ASCII bytes.
* offset 4: version uint32.
* offset 8: dtype code uint32. 2 means int16 voxels, 16 means float32 voxels.
* offset 12: three uint32 values for voxel counts per axis, nx, ny, nz.
* offset 24: three float32 values for micrometers per voxel per axis, sx, sy, sz. these change per file and must be read from header.
* offset 36: uint32 data offset where voxel values start.
* after data offset: nx * ny * nz values in announced dtype, x fastest, so linear index for x,y,z is `x + nx * (y + ny * z)`.

each volume contains one solid necrotic core where dead cells accumulate PI. the centre is flat and bright where staining saturates, the border is dimmer with partial fill smeared by tissue scattering and light-sheet PSF. there is flat ambient autofluorescence background plus camera noise. some scans have one to three tiny bright specks far away from isolated apoptotic debris that must be ignored. keep only the main connected dead mass using 26-neighbour connectivity.

threshold counting cannot be precise. a low cutoff includes huge scattering halo and overcounts by eighty to one hundred thirty percent. a high cutoff misses thin finger-like necrotic extensions into the cortical plate that never get bright enough and undercounts by thirty to fifty percent. no fixed cutoff works across files because PI brightness, tissue clarity, scattering width, and background change per organoid batch. the blurry images give the best clue where fluorescence is most concentrated, not how many bright voxels there are. the true core is flat but hidden by scattering noise.

the blur spreads photons but does not create or destroy fluorescence energy. that physics makes precise volume recovery possible despite smear, but using it requires separating the main core from far specks, estimating autofluorescence background without bias from the core itself, estimating the true saturated PI level without being fooled by noise, and deciding how far the faint halo extends without merging debris specks. that is the hard part.

simple shortcuts are off by large margin. grading is at three percent tolerance; only a genuine precise method passes.

implementation constraints: parse bytes yourself using only the standard library. allowed stdlib modules include `struct`, `sys`, `math`, `random`, `tempfile`, `re`. the following are banned and will be rejected by `test_from_scratch`: `numpy`, `scipy`, `skimage`, `cv2`, `PIL`, `Pillow`, `networkx`, `igraph`, `imageio`, `pandas`, `torch`, `tensorflow`, `socket`, `multiprocessing`, `glob`, `pathlib`, `os`, `io`, `posixpath`, `ntpath`, `genericpath`, plus any array, imaging, or graph helper library. banned calls include `eval`, `exec`, `compile`, `__import__`, `chr`. banned runtime tricks include `subprocess`, `os.system`, `os.popen`, `os.exec`, `os.fork`, `os.walk`, `os.listdir`, `os.scandir`, `os.open`, `pty`, `importlib`, `runpy`, `ctypes`, filesystem listing, and any obfuscation that hides paths using `chr()`, `bytes.fromhex`, `base64`, `b64decode`, `bytearray`, `bytes([...])` tricks, or string concatenation that builds forbidden paths. do not attempt to open or list the `/tests` directory, and do not reference `test_outputs`, `heldout`, `reference_volume`, `_gen`, `GEOM_TRUTH`, or `geometric_truth` in your solver source. your solver must work on random temporary files, not hardcoded paths.

print the volume in cubic micrometers as the last word on stdout.
