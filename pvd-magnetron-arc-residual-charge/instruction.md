I maintain PVD magnetron sputter tools that coat display glass with ITO. The magnetron runs high power and sometimes the target arcs. When it arcs, a charge pulse flows through the chamber and leaves residual current in the bias cable. If we mis-integrate it, the next layer has wrong thickness and we get color mura.

Write a program and save it as /app/solve.py. It will be called as python /app/solve.py <trace_path> and must print the true residual charge of the main arc event in microcoulombs as its last token. Grading tolerance is 3% relative. We have one sample trace at /app/data/scene.pmar for you to develop with. Hidden evaluation uses different traces you never saw with different dose, drift, gain, RF period, total samples and baseline. Do not hardcode sample numbers. Must work on any file path given as first argument.

File format is .pmar, custom binary, little endian:

- Bytes 0-3 ASCII magic PMAR
- Bytes 4-7 uint32 version = 1
- Bytes 8-11 uint32 N = total int16 samples in file
- Bytes 12-15 uint32 data_offset = byte offset where current samples start
- Bytes 16-19 float32 sample interval in seconds (e.g. 0.0008), varies per file, read it
- Bytes 20-23 float32 gain trim
- Bytes 24-27 uint32 baseline floor hint from firmware, ignore, real baseline drifts with chamber temperature and RF pickup
- Header may have random padding from byte 28 up to data_offset. Use data_offset, do not assume 64. Hidden uses 32 40 48 64 80 96 128.
- At data_offset: N int16 little endian values, each is current in deci-mA: physical mA = value / 10.0

What is inside a trace? A thermal baseline that slowly drifts plus RF sinusoidal interference from the magnetron power supply plus white noise, one dominant arc pulse that is flat-topped ideally but smeared by the electrometer low-pass into a broad peak with long tails, a few isolated fast spikes far away from shutter vibration, and two shallow wide humps: one from target poisoning outgassing and one from anodic afterglow. Each wide hump spans many samples but carries less total charge than the main arc despite its length. The RF sine makes baseline wavy, not flat.

Why counting by threshold fails: low threshold includes diffuse halo plus both wide humps plus RF crests and overcounts by 70-100%. High threshold cuts off the faint tail that still holds real charge and undercounts by 35-60%. Picking the longest connected run by sample count selects a wide hump, not the main arc, because wide humps are longer yet weaker. No fixed absolute or relative level works across chambers because gain, drift slope, RF amplitude/period, and smear width all shift per recipe.

The electrometer blur conserves charge: total integral under smeared curve equals integral of ideal before blur. That property lets you recover true charge despite smear, but you must do it carefully: get unbiased background without letting the main pulse bias you, separate main arc from far spikes and the two wide humps, estimate true interior level without being fooled by noise spikes, and capture faint tail belonging to main until it fades into noise while not bridging to distant artifacts. Skipping tail capture undercounts systematically.

We grade at 3% relative. Simple thresholding is far outside.

Implementation rules: parse binary yourself, stdlib only. Allowed imports: struct, sys, math, random, tempfile, re, collections. Forbidden and will make test_from_scratch fail: numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, shutil, io, os, pty, importlib, runpy, ctypes and other array/imaging/graph libs. Forbidden calls: eval, exec, compile, __import__, chr, ord, breakpoint, bytes, bytearray. Forbidden runtime: subprocess, os.system, os.popen, os.exec, os.fork, os.walk, os.listdir, os.scandir, os.open, pty, importlib, runpy, etc plus tricks hiding paths via chr, bytes.fromhex, base64, b64decode, string concat building forbidden locations. Never open or list /tests, never mention test_outputs, heldout, reference_volume, _gen, GEOM_TRUTH, geometric_truth in solve.py. Work on random temp file path, not hardcoded.

Print charge in microcoulombs as final token. Example: 987.65
