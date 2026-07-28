I work on Android battery fuel gauge team chasing capacity drift after fast charge. The gauge has Coulomb counter that logs charge current. When battery swells you get current spike that is smeared by low pass filter plus baseline drift plus random blips from connector noise.

We dump the coulomb trace via custom file bctr. The test app writes little endian using ByteBuffer and FileOutputStream.

Your job is to write a program at /app/solve.py that reads a file path from sys argv 1. We run python3 /app/solve.py /path/to/scan.bctr and your stdout last token must be a float that is true charge capacity in mAh for the main swell event after you clean baseline and ignore far blips.

Sample file is at /app/data/scene.bctr you can try locally. Expected true capacity for sample is about 943.0 mAh (within 3% relative). Hidden grading uses other files you never saw with different capacities (roughly 659, 916, 1006, 955 mAh range), charge rates, baseline drift, gain, noise, dust blips including a wide low-amplitude blip. Do not hardcode sample.

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

Trace contains slowly drifting background baseline plus Gaussian random noise plus one main charge event that jumps high and has long thin tails from low-pass filter smear. Some traces have 2-5 tiny blips far from main event from connector noise that must be ignored. The main event is the one with dominant electrochemical charge, not merely the one with most samples above some cutoff.

Why fixed threshold fails: low cut includes halo and dust and overestimates, high cut misses long low-amplitude tails and underestimates. No fixed cut works because gain and baseline shift per batch and per board. The smear is charge-conserving: total charge under blurred curve equals ideal occupancy * plateau, so total area is preserved even though peak is smeared lower and wider. The true capacity is defined as integral of the ideal (non-blurred) occupancy, which equals integral of the blurred residual over its full extent.

Goal is coulomb counting for the main swell: estimate background current robustly in presence of slow linear drift and noise, distinguish main event from far sparse blips by how much charge it actually carries, recover the low-amplitude smeared tails that hold significant charge despite not looking bright, and integrate residual current over time to get mAh using the header interval, shunt gain, and proper unit conversion (payload is deci-mA, 1 mAh = 3600 mA·s). Think about what distinguishes concentrated charge dumps from connector noise, and how to decide where the smeared halo ends and pure noise begins without a fixed global cutoff.

Sample: scene has interval 0.5 sec, gain 1.0. Grading checks within 3 percent relative tolerance.

Parse binary yourself using only struct. Allowed modules are struct, sys, collections. Banned modules are numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, shutil, io, os, pty, importlib, runpy, ctypes. Banned calls are eval, exec, compile, __import__, getattr, setattr, hasattr, globals, locals, vars, dir, chr, ord, breakpoint, base64, binascii, codecs. Banned runtime tricks are subprocess, os system popen exec, walk listdir scandir stat fdopen path and pathlib Path shutil io open, importlib runpy pty. Do not open or read tests directory or heldout files or gen file or ground truth file. Checks via AST and literal scan; we block /tests, heldout, _gen, ground_truth strings.

At end print capacity mAh as last token (float). Grading checks within 3 percent relative tolerance against true capacity from ground_truth.json which is canonical value from generator occupancy integral.

Files up to few thousand samples (2048-3072), recursion will fail, use iterative approach.

This is battery fuel gauge capacity mAh, distinct from display mura ink pool count (2D) and OLED void volume mm3. Battery is 1D time-series, not 2D image.

Good luck.
