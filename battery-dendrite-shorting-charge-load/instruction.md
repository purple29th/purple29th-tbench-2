You work in battery failure analysis. Lithium dendrites grow across the separator and trap metallic lithium. We image the separator with X-ray fluorescence - trapped lithium glows bright, but fluorescence diffusion plus the detector lens PSF smears the glow everywhere, so the bright region looks much larger and fuzzier than the true metallic lithium that creates shorting risk.

Build a tool that reports total trapped lithium charge in milliCoulombs (mC) for shorting risk grading. Precision matters for safety classification.

Your program must be saved as `/app/solve.py`. It will be invoked as `python /app/solve.py <scan_path>` and the last word it prints will be taken as the charge load.

You are provided one example scan for local testing at `/app/data/scene.ldch`. You may read this file while developing, but hidden grading uses different scans you have never seen, with different dimensions, spacings, brightness, dendrite thickness, and voxel pitch, passed as random temporary files. Do not hardcode numbers or paths from the example; your solver must work on any file path given as first argument. Hardcoding sample charge will fail hidden checks.

Format .ldch is custom binary for lithium dendrite charge volumes. Everything is little-endian:

* Offset 0: magic `LDCH` four ASCII bytes.
* Offset 4: version uint32.
* Offset 8: dtype code uint32. 2 means int16 voxels, 16 means float32 voxels.
* Offset 12: three uint32 values for voxel counts per axis nx ny nz.
* Offset 24: three float32 values for mm per voxel per axis sx sy sz. These change per file and must be read.
* Offset 36: uint32 data offset where voxels start.
* After offset: nx*ny*nz values in announced dtype, x fastest, index = x + nx*(y+ny*z).

Each volume contains lithium dendrites that are elongated and branching along the separator (they are the only structures that count for shorting charge), plus some round lithium plating artefacts that are near-spherical and must be ignored for charge. You can distinguish them by shape: dendrites are elongated (longest dimension at least 1.6x shortest and at least 8 voxels long), plating artefacts are round/cubic. Also there are 1-3 tiny bright specks far away from dust that must be ignored. Keep only main elongated dendrite structures using 26-neighbour connectivity plus shape filtering.

Calibration: lab measurement shows each cubic mm of dendrite holds 2.8 mC of trapped charge. So charge_mC = dendrite_volume_mm3 * 2.8. Dendrite volume itself must be recovered despite blur.

Threshold counting cannot be precise. Low cutoff includes huge halo and overcounts 80-130%. High cutoff misses thin dendrite tips that never get bright and undercounts 30-50%. No fixed cutoff works across files because brightness and blur width change.

The blur spreads energy but does not create or destroy signal. That physics allows precise recovery: true voxels = sum(background-subtracted intensity over dendrite+halo) / plateau_intensity. Must infer ambient background from border, isolate main dendrite from far specks and round plating via largest-mass plus shape filter, estimate plateau from most concentrated region, integrate halo until shell mean hits noise floor without merging plating artefacts.

Simple shortcuts fail large margin. Grading at 3% tolerance; only genuine precise method passes.

Implementation constraints: parse bytes yourself using only stdlib. Allowed: struct, sys, math, random, tempfile, re. Banned and will be rejected by test_from_scratch: numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, os, io, posixpath, ntpath, genericpath, plus any array/imaging/graph helper. Banned calls: eval, exec, compile, __import__, chr. Banned runtime tricks: subprocess, os.system, os.popen, os.exec, os.fork, os.walk, os.listdir, os.scandir, os.open, pty, importlib, runpy, ctypes, filesystem listing, obfuscation via chr() bytes.fromhex base64 b64decode bytearray bytes([...]) tricks, or building forbidden paths. Do not open/listing /tests, do not reference test_outputs, heldout, reference_charge, _gen, GEOM_TRUTH, geometric_truth in solver source. Solver must work on random temp files, not hardcoded paths.

Print charge in mC as last word.
