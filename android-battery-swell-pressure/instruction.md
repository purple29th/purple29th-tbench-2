I work on Android battery fuel gauge team chasing capacity drift after fast charge. The gauge has Coulomb counter that logs charge current. When battery swells you get current spike that is smeared by low pass filter plus baseline drift plus random blips from connector noise.

We dump the coulomb trace via custom file bctr. The test app writes little endian using ByteBuffer and FileOutputStream.

Your job is to write a program at /app/solve.py that reads a file path from sys argv 1. We run python3 /app/solve.py /path/to/scan.bctr and your stdout last token must be a float that is true charge capacity in mAh for the main swell event after you clean baseline and ignore far blips.

Sample file is at /app/data/scene.bctr you can try locally. Expected true capacity for sample is about 1321.67 mAh (within 3% relative). Hidden grading uses other files you never saw with different capacities (1232, 1426, 1297, 1560 mAh range), charge rates, baseline drift, gain, noise, dust blips. Do not hardcode sample.

File format is my own invented battery charge trace, magic BCTR.

Layout little endian:

Bytes 0 to 3: ascii BCTR
Bytes 4 to 7: u32 version = 1
Bytes 8 to 11: u32 total samples
Bytes 12 to 15: u32 data offset
Bytes 16 to 19: f32 sample interval seconds
Bytes 20 to 23: f32 shunt gain
Bytes 24 to 27: u32 baseline current floor
Header at least 28 bytes plus padding up to data offset, respect offset - parser must use header data_offset field not hardcode 64, heldouts use varied offsets 32,40,64,96 to test padding.

Payload at offset is total int16 little endian current values where each value is real current in mA times 10. Divide by 10 to get mA.

Trace contains flat background baseline plus noise plus one main charge event that jumps high and has thin tails from filter smear. Some traces have one or two tiny blips far from main event from connector noise that must be ignored. Keep biggest mass cluster via 1D contiguous grouping by integrated residual mass, not by sample count.

Why fixed threshold fails: low cut includes halo and dust and overestimates, high cut misses tails and underestimates. No fixed cut works because gain and baseline shift per batch. The smear is charge-conserving: total charge under blurred curve equals ideal occupancy * plateau, so total area is preserved even though peak is smeared. Interior of main event is saturated flat but hidden by smear and noise. Best clue is where charge most concentrated not just how many bright samples.

Steps that reliably work (similar to display mura ink pool count but 1D):
- estimate background baseline via median of all values or median of low half (robust)
- estimate noise sigma via MAD (median absolute deviation) scaled 1.4826
- detect bright samples > ~3.5 sigma above background
- 1D contiguous flood fill (group neighboring samples that are above threshold) to get clusters, keep cluster with largest integrated residual mass (sum excess) to drop far dust blips (dust has smaller mass than main even if many samples)
- estimate plateau amplitude from interior of main cluster (e.g., top few values median) - plateau is saturated current level before smear
- grow cluster iteratively to include smeared tails: dilate by 1 sample each side, include shell if mean residual > ~0.5 sigma, stop when shell at noise level, up to ~40 iterations (tail spread)
- integrate total residual over grown region and convert to mAh: capacity = total_residual /10 * interval_seconds * gain /3.6 . The /10 is because payload is mA*10, interval*current gives mA*s, /3.6 converts coulomb to mAh.

Sample: scene has interval 0.5 sec, gain 1.0, true capacity 1321.67 mAh. Grading checks within 3 percent relative tolerance.

Parse binary yourself using only struct. Allowed modules are struct, sys, collections, deque. Banned modules are numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, shutil, io, os, pty, importlib, runpy, ctypes. Banned calls are eval, exec, compile, __import__, getattr, setattr, hasattr, globals, locals, vars, dir, chr, ord, breakpoint, base64, binascii, codecs. Banned runtime tricks are subprocess, os system popen exec, walk listdir scandir stat fdopen path and pathlib Path shutil io open, importlib runpy pty. Do not open or read tests directory or heldout files or gen file or ground truth file. Checks via AST and literal scan; we block /tests, heldout, _gen, ground_truth strings.

At end print capacity mAh as last token (float). Grading checks within 3 percent relative tolerance against true capacity from ground_truth.json which is canonical value from generator occupancy integral.

Files up to few thousand samples (2048-2560), recursion will fail, use iterative.

This is battery fuel gauge capacity mAh, not display mura ink pool count (2D) and not OLED void volume mm3. Different from mura which is 2D flood fill, battery is 1D contiguous grouping.

Good luck.
