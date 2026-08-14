I work on the PCB factory line inspecting copper traces. After etching, some traces have overetch that creates a small gap under solder mask. This gap hurts reliability. We use X ray to see it but the X ray blur spreads the gap signal everywhere, so the gap looks larger and fuzzier than its true size.

I need you to build a small tool for me. Please create a file at /app/solve.py. It will be invoked as python at /app/solve.py plus a scan path and the last word it prints will be taken as the gap volume.

You are provided one example scan for local testing at /app/data/scene.pcb. You may read this file while developing, but hidden grading uses different scans you have never seen, with different dimensions, spacings, brightness, copper thickness, and voxel pitch, passed as random temporary files. Do not hardcode numbers or paths from the example. Your solver must work on any file path given as the first argument. Hardcoding the sample volume will fail the hidden volume checks.

Format pcb is a custom binary for X ray overetch gap volumes. Everything is little endian:

* Offset 0: magic PCBG four ASCII bytes.
* Offset 4: version uint32.
* Offset 8: dtype code uint32. 2 means int16 voxels, 16 means float32 voxels.
* Offset 12: three uint32 values for voxel counts per axis, nx, ny, nz.
* Offset 24: three float32 values for millimetres per voxel per axis, sx, sy, sz. These change per file and must be read from the header.
* Offset 36: uint32 data offset where voxel values start.
* After data offset: nx times ny times nz values in the announced dtype, x fastest, so linear index for x y z is x plus nx times (y plus ny times z).

Each volume contains copper trace with overetch gaps that are elongated along trace direction and are the only gaps that count, plus some round solder voids that are artefacts and must be ignored. You can tell them apart by shape, elongated versus round. The centre of each gap is flat and bright where X ray sees open gap, the border is dimmer with partial fill smeared by X ray blur. There is a flat ambient background plus sensor noise. Some scans also have one or two tiny bright specks far away from dust artefacts that must be ignored. Keep only the main elongated overetch gaps using 26 neighbour connectivity plus shape filtering.

Threshold counting cannot be precise. A low cutoff includes a huge halo and overcounts by eighty to one hundred thirty percent. A high cutoff misses thin overetch that never gets bright enough and undercounts by thirty to fifty percent. No fixed cutoff works across files because brightness and blur width change. The blurry images give the best clue where signal is most concentrated, not how many bright voxels there are. The true core is flat but hidden by blur noise.

The blur spreads energy but does not create or destroy signal. That physics makes precise volume recovery possible despite smear, but using it requires separating the main gap from far specks, estimating background without bias from the gap itself, estimating the true concentrated intensity without being fooled by noise, and deciding how far the faint halo extends without merging specks. That is the hard part.

Simple shortcuts are off by a large margin. Grading is at three percent tolerance, only a genuine precise method passes.

Implementation constraints: parse bytes yourself using only the standard library. Allowed stdlib modules include struct, sys, math, random, tempfile, re. The following are banned and will be rejected by test from scratch: numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, os, io, posixpath, ntpath, genericpath, plus any array, imaging, or graph helper library. Banned calls include eval, exec, compile, __import__, chr. Banned runtime tricks include subprocess, os system, os popen, os exec, os fork, os walk, os listdir, os scandir, os open, pty, importlib, runpy, ctypes, filesystem listing, and any obfuscation that hides paths using chr, bytes fromhex, base64, b64decode, bytearray, bytes tricks, or string concatenation that builds forbidden paths. Do not attempt to open or list the /tests directory, and do not reference test outputs, heldout, reference volume, _gen, GEOM TRUTH, or geometric truth in your solver source. Your solver must work on random temporary files, not hardcoded paths.

Print the volume in mm3 as the last word on stdout.
