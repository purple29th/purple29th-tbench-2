I work in the Android fingerprint lab where we see oil smear blocking the sensor after factory assembly. The under-display optical fingerprint sensor captures raw images. When oil from display glue leaks, it pools and creates a bright smear plus thin bleed lines plus dust specks far away.

We dump images via a custom file called fpos. Kotlin tests write ByteBuffer little endian via FileOutputStream.

Your job is to write /app/solve.py that reads a file path as first argument. We run python3 /app/solve.py /path/to/scan.fpos and the last token of stdout must be an integer count of fingerprint pixels truly affected by oil after cleaning halo and dust.

A sample file is available at /app/data/scene.fpos you can try locally. Hidden grading uses other files you never saw with different oil sizes, gain, pitch, baseline, and dust. Do not hardcode the sample.

fpos format is my tiny container for fingerprint oil smear.

Header little endian:
Bytes 0 to 3: ascii FPOS magic
Bytes 4 to 7: u32 version equals 1
Bytes 8 to 11: u32 total pixels
Bytes 12 to 15: u32 data offset
Bytes 16 to 19: f32 sx pitch mm per pixel x
Bytes 20 to 23: f32 sy pitch mm per pixel y
Bytes 24 to 27: u32 baseline floor
Bytes 28 to 31: u32 nx
Bytes 32 to 35: u32 ny
Header at least 36 bytes plus padding up to data offset, respect data offset.

Payload at offset is nx times ny int16 little endian brightness values, x fastest so index equals x plus nx times y.

Content:
One main oil smear where brightness is high plus thin bleed lines where cell is partly filled with mid values plus flat background baseline plus noise plus far dust blobs that are trash far away. You must ignore dust and keep the biggest mass cluster using 8 neighbours, pick by mass not count.

Simple fixed threshold fails. Low threshold grabs halo and merges dust and overcounts by about 70 percent, high threshold misses bleed lines and undercounts.

Real trick: smear conserves total light. Interior is saturated flat but hidden by smear and noise. The best clue is where light is most concentrated, not just how many bright pixels.

Parse binary yourself using only struct. Allowed modules are struct, sys, collections, and deque. Banned modules are numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, shutil, io, os, pty. Also banned tricks like subprocess, os, system, popen, exec, walk, listdir, scandir, open, stat, read, fdopen, path and pathlib Path, shutil, io open, importlib, runpy, pty. Banned calls are eval, exec, compile, __import__, getattr, setattr, hasattr, globals, locals, vars, dir, chr, ord, breakpoint, base64, binascii, codecs. Also banned dunder builtins dict, subclasses, mro, bases, code, globals, builtins. Do not open tests directory or heldout files or gen file or ground truth file.

At end print integer count as last token. Grading checks exact integer count within tolerance tol = max(2, int(0.03 * expected)) i.e. 3 percent relative or 2 counts absolute against true count from ground_truth.json. True count comes from the generator's canonical occupancy map rounded sum, not from the reference estimator. We have 4 hidden maps with different counts and baselines, all with offset 64.

Files may have up to few thousand pixels, recursion will fail, use iterative flood fill.

This is fingerprint oil smear counting, not OLED void volume mm3 and not display mura ink pool count cdmr. Different sensor optical fingerprint vs capacitive touch vs IR.

Good luck.
