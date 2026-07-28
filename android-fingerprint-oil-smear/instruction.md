I work on Android under-display optical fingerprint sensor qualification after factory glue assembly. Glue can leak oil that blocks light and appears as a bright smear in the captured frame. We see also narrow bleed lines where a pixel is partially covered and isolated dust spots far away from the main region.

We dump each captured frame into a custom file with extension fpos. Kotlin test code writes ByteBuffer little endian via FileOutputStream.

Your task is to write a program at /app/solve.py that takes a file path as its first argument. We execute python3 /app/solve.py /path/to/scan.fpos. The last token printed on stdout must be an integer count of pixels truly covered by oil after removing halo smear and far dust.

Sample input is available at /app/data/scene.fpos you can try locally. Hidden grading uses four other files you never saw with different oil extents, pitch, gain, baseline, and dust positions. Do not hardcode numbers from the sample.

FPOS binary layout little endian:

0 to 3: ASCII FPOS
4 to 7: u32 version = 1
8 to 11: u32 total pixels = nx * ny
12 to 15: u32 data offset
16 to 19: f32 sx pitch mm per pixel along x
20 to 23: f32 sy pitch mm per pixel along y
24 to 27: u32 baseline brightness floor
28 to 31: u32 nx width
32 to 35: u32 ny height
At least 36 bytes header, may have padding up to data offset. Respect data offset.

Payload at data offset is nx * ny int16 little endian brightness values. X is fastest, so linear index = x + nx * y.

Image content:
Flat background near baseline plus Gaussian-like sensor noise plus one dominant oil smear that raises brightness strongly plus narrow partially covered lines with intermediate values plus thin halo from optical blur plus several isolated dust blobs far away that should be ignored. Keep only the main oil region, ignore far dust.

Why naive counting fails:
If you count everything above a low cut, you include halo and distant dust and overcount by roughly 70 percent. If you use a strict high cut, you lose bleed lines and halo and undercount.

Key property:
Optical blur preserves integrated brightness energy. The peak is suppressed but total light is conserved. Interior of oil is flat saturated but hidden by blur and noise. Recovery must use total energy, not just bright pixel count.

Parsing:
Parse binary yourself using only struct. Allowed modules are struct, sys, collections, deque. Banned modules are numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, shutil, io, os, pty. Banned calls are eval, exec, compile, __import__, getattr, setattr, hasattr, globals, locals, vars, dir, chr, ord, breakpoint, base64, binascii, codecs. Banned runtime tricks are subprocess, os, system, popen, exec, walk, listdir, scandir, open, stat, read, fdopen, path and pathlib Path, shutil, io open, importlib, runpy, pty. Also banned dunder tricks like __dict__, __subclasses__, __mro__, __bases__, __code__, __globals__, __builtins__. Do not open or read tests directory, heldout files, _gen file, or ground truth file. We enforce via AST and literal scans.

Output grading:
We check last integer on last non-empty stdout line. Ground truth comes from generator canonical occupancy rounded sum (core plus partial border plus bleed strokes), stored in ground_truth.json, not from reference estimator. Tolerance is tol = max(2, int(0.03 * expected)) meaning 3 percent relative or 2 absolute. You have 4 hidden scenes all with offset 64.

Implementation notes:
Image may have up to few thousand pixels. Recursive flood fill will hit recursion limit, use iterative stack or deque.

This task is about optical fingerprint oil residue light attenuation counting, not about OLED subvoxel void volume mm3 IR, not about display capacitive ghost touch ink pool CDMR count, and not about battery BCTR capacity.

Good luck.
