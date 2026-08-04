I work in battery failure analysis checking separator shorts. Lithium dendrites grow across the separator and trap metallic lithium that glows bright when we image with X-ray fluorescence. The problem is fluorescence diffusion plus the detector lens point spread smears the glow everywhere so the bright blob looks much larger and fuzzier than the true metallic lithium that creates shorting risk.

I need a program that reports total trapped lithium charge in milliCoulombs for safety grading. Precision matters because we classify cells for field risk.

Please save your program as /app/solve.py. We will run it as python /app/solve.py with the scan path as first argument and we take the last word it prints as the charge.

You have one example scan for local testing at /app/data/scene.ldch. You can read it while developing but hidden grading uses different scans you never saw with different dimensions spacings brightness dendrite thickness and voxel pitch passed as random temp files. Do not hardcode numbers or paths from the example. Your solver must work on any file path given as first argument. Hardcoding sample charge will fail hidden checks.

What is ldch. Our own binary for lithium dendrite charge volumes. Everything little endian.

Offset 0 magic LDCH four ascii bytes.
Offset 4 version uint32.
Offset 8 dtype code uint32. 2 means int16 voxels 16 means float32 voxels.
Offset 12 three uint32 nx ny nz voxel counts per axis.
Offset 24 three float32 sx sy sz mm per voxel per axis. These change per file and must be read from header.
Offset 36 uint32 data offset where voxel values start.
After data offset nx times ny times nz values in announced dtype x fastest so index for x y z is x plus nx times y plus ny times z.

Each volume contains lithium dendrites that are elongated and branching along separator and they are the only structures that count for shorting charge plus some round lithium plating artefacts that are near spherical and must be ignored. You can tell them apart by shape elongated if longest dimension at least 1.6 times shortest and at least 8 voxels long plating artefacts are round cubic. Also there are one to three tiny bright specks far away from dust that must be ignored. Keep only main elongated dendrite structures using 26 neighbour connectivity plus shape filtering.

Calibration lab shows each cubic mm of dendrite holds 2.8 mC of trapped charge. So charge in mC equals dendrite volume mm3 times 2.8. Dendrite volume itself must be recovered despite blur.

Threshold counting cannot be precise. Low cutoff includes huge halo and overcounts by eighty to one hundred thirty percent. High cutoff misses thin dendrite tips that never get bright enough and undercounts by thirty to fifty percent. No fixed cutoff works across files because brightness and blur width change.

Blur spreads energy but does not create or destroy signal. That physics makes precise recovery possible. True voxels equals sum of background subtracted intensity over dendrite plus halo divided by plateau intensity. Must infer ambient background from border estimate plateau from most concentrated region and grow halo until shell mean hits noise floor without merging plating artefacts.

Simple shortcuts fail by large margin. Grading at three percent tolerance only genuine precise method passes.

Implementation constraints parse bytes yourself using only standard library. Allowed stdlib modules include struct sys math random tempfile re. The following are banned and will be rejected by test from scratch. numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath plus any array imaging or graph helper library. Banned calls include eval exec compile __import__ chr. Banned runtime tricks include subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing and any obfuscation that hides paths using chr bytes fromhex base64 b64decode bytearray bytes tricks or string concatenation that builds forbidden paths. Do not attempt to open or list the tests directory and do not reference test_outputs heldout reference_charge _gen GEOM_TRUTH or geometric_truth in your solver source. Your solver must work on random temporary files not hardcoded paths.

Print charge in mC as last word.
