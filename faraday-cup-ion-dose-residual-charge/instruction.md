I run dose QA on high-current boron implanters in the Dresden fab. We implant 300mm wafers for power devices. Behind the wafer there is a graphite Faraday cup with a bias network that measures ion current. The electrometer has a long integration time and cable triboelectric leakage, so after beam off you see a slowly decaying current tail. Dose error if we integrate the wrong part causes Vt shift, and we scrap lots.

You must write a standalone program saved as /app/solve.py. It is invoked as python /app/solve.py <trace_path> and must print the true residual charge of the main implant pulse in microcoulombs as its last whitespace token. Tolerance is 3% relative. Hidden grading uses traces you never saw with different dose, drift rate, electrometer gain, sample count, interval, baseline temperature, and turbo pump vibration patterns. Do not hardcode numbers from the example. Work on any path given as first argument.

Sample for development is at /app/data/scene.fcrc. You may read it while coding.

File format is .fcrc, custom binary, all little endian:

- Bytes 0-3 ASCII magic FCRC
- Bytes 4-7 uint32 version, currently 1
- Bytes 8-11 uint32 N = total int16 samples
- Bytes 12-15 uint32 data_offset = byte offset where current samples start
- Bytes 16-19 float32 sample interval in seconds (e.g. 0.00085), changes per file, must be read
- Bytes 20-23 float32 analog gain trim
- Bytes 24-27 uint32 baseline floor hint from firmware, do NOT trust, real baseline drifts with heater and RF
- Header may have random padding between byte 28 and data_offset, so use data_offset field. Hidden files use offsets 32 40 64 96 128.
- At data_offset: N little-endian int16 values, each is current in deci-mA: physical mA = value / 10.0

What is inside each trace? A slowly drifting thermal baseline plus sensor noise, one dominant implant pulse that is flat-topped in ideal form but smeared by the electrometer low-pass into a high peak with extended exponential-like tails, a few isolated micro-spikes far away from turbo pump microphonics, and a shallow wide hump from chamber outgassing that is low amplitude but spans many tens of samples. The wide hump contains less total charge than the main pulse despite its length.

Why naive thresholding fails? If you include every sample above a low threshold you also pick up the diffuse tail plus the shallow hump and you over-estimate by 60-90%. If you use a high threshold you cut off the genuine charge that lives in the faint tails and you under-estimate by 30-55%. No fixed absolute or relative threshold works across recipes because gain, drift slope, and smear width all change. The electrometer blur does not create or destroy charge, it only spreads it, so total charge is preserved.

Your task is to recover the main pulse charge only, excluding the outgassing hump and far spikes. You need to infer the drifting baseline without letting the pulse itself bias you, separate main pulse from unrelated artifacts, estimate the true plateau level that would be seen without blur and without being fooled by noise spikes, and capture the faint tail that belongs to the main pulse until it fades into the noise floor while not accidentally bridging to distant artifacts.

We grade at 3% relative. Threshold counting is far outside that window.

Implementation constraints: parse binary yourself, stdlib only. Allowed imports: struct, sys, math, random, tempfile, re, collections. Forbidden and will make test_from_scratch fail: numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, shutil, io, os, pty, importlib, runpy, ctypes and any other array/imaging/graph lib. Forbidden builtins: eval, exec, compile, __import__, chr, ord, breakpoint, bytes, bytearray. Forbidden runtime: subprocess, os.system, os.popen, os.exec, os.fork, os.walk, os.listdir, os.scandir, os.open, pty, importlib, runpy etc. plus path hiding via chr, bytes.fromhex, base64, b64decode, string concatenation building forbidden paths. Never try to open or list /tests directory, never mention test_outputs, heldout, reference_volume, _gen, GEOM_TRUTH, geometric_truth in solve.py. Must work on random temp path, not hardcoded.

Print charge in microcoulombs as final token. Example: 1234.56
