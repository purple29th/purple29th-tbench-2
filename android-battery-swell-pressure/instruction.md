I work on Android battery fuel gauge team chasing capacity drift after fast charge. The gauge has Coulomb counter that logs charge current. When battery swells you get current spike that is smeared by low pass filter plus baseline drift plus random blips from connector noise.

We dump the coulomb trace via custom file bctr. The test app writes little endian using ByteBuffer and FileOutputStream.

Your job is to write a program at /app/solve.py that reads a file path from sys argv 1. We run python3 /app/solve.py /path/to/scan.bctr and your stdout last token must be a float that is true charge capacity in mAh for the main swell event after you clean baseline and ignore far blips.

Sample file is at /app/data/scene.bctr you can try locally. Hidden grading uses other files you never saw with different capacities, charge rates, baseline drift, gain, noise, dust blips. Do not hardcode sample.

File format is my own invented battery charge trace, magic BCTR.

Layout little endian:

Bytes 0 to 3: ascii BCTR
Bytes 4 to 7: u32 version = 1
Bytes 8 to 11: u32 total samples
Bytes 12 to 15: u32 data offset
Bytes 16 to 19: f32 sample interval seconds
Bytes 20 to 23: f32 shunt gain
Bytes 24 to 27: u32 baseline current floor
Header at least 28 bytes plus padding up to data offset, respect offset

Payload at offset is total int16 little endian current values where each value is real current in mA times 10. Divide by 10 to get mA.

Trace contains flat background baseline plus noise plus one main charge event that jumps high and has thin tails from filter smear. Some traces have one or two tiny blips far from main event from connector noise that must be ignored. Keep biggest mass cluster via 1D contiguous grouping by integrated residual mass, not by pixel count.

Fixed threshold counting fails. Low cut includes halo and overestimates, high cut misses tails and underestimates. No fixed cut works because gain and baseline shift per batch.

Parse binary yourself using only struct. Allowed modules are struct, sys, collections, deque. Banned modules are numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, shutil, io, os, pty, importlib, runpy, ctypes. Banned calls are eval, exec, compile, __import__, getattr, setattr, hasattr, globals, locals, vars, dir, chr, ord, breakpoint, base64, binascii, codecs. Banned runtime tricks are subprocess, os, system, popen, exec, walk, listdir, scandir, open, stat, read, fdopen, path and pathlib Path, shutil, io open, importlib, runpy, pty. Do not open or read tests directory or heldout files or gen file or ground truth file. Checks via AST and literal scan.

At end print capacity mAh as last token. Grading checks within 3 percent relative tolerance against true capacity from ground_truth.json which is canonical value from generator occupancy integral. Tolerance is 0.03 relative. We have 4 hidden traces with different capacities, gains, baselines, all with offset 64 to test padding.

Files up to few thousand samples, recursion will fail, use iterative.

This is battery fuel gauge capacity mAh, not display mura ink pool count and not OLED void volume mm3.

Good luck.
