I work on Android battery fuel gauge team chasing capacity drift after fast charge. The gauge has Coulomb counter that logs charge current. When battery swells you get current spike that is smeared by low pass filter plus baseline drift plus random blips from connector noise.

We dump the coulomb trace via custom file bctr. The test app writes little endian using ByteBuffer and FileOutputStream.

Your job is write program at /app/solve.py that reads file path from sys argv 1. We will run python3 /app/solve.py /path/to/scan.bctr and your stdout last token must be float that is true charge capacity in mAh for the main swell event after you clean baseline and ignore far blips.

Sample file is available at /app/data/scene.bctr you can run locally. Hidden grading uses other files you never saw with different capacities, charge rates, baseline drift, gain, noise, dust blips. Do not hardcode sample number.

File format is my own invented battery charge trace, magic BCTR.

Layout little endian:

Bytes 0 to 3 ascii BCTR
Bytes 4 to 7 u32 version equals 1
Bytes 8 to 11 u32 total samples
Bytes 12 to 15 u32 data offset
Bytes 16 to 19 f32 sample interval seconds
Bytes 20 to 23 f32 shunt gain
Bytes 24 to 27 u32 baseline current floor
Header at least 28 bytes plus padding up to data offset, respect offset

Payload at offset is total int16 little endian current values where each value is real current in mA times 10. So divide payload by 10 to get mA.

Trace contains flat background baseline plus noise plus one main charge event where current jumps high flat plus thin tails from filter smear. Some traces have one or two tiny blips far away from connector noise that must be ignored, keep biggest mass cluster via 1D contiguous grouping by mass not count.

Fixed threshold counting fails. Low cut includes halo overestimates, high cut misses tails underestimates. No fixed cut works because gain baseline shifts per batch.

Real trick: low pass filter conserves total charge. Interior flat but hidden by smear and noise. Best clue is where charge most concentrated.

Parse binary yourself using only struct. Allowed are struct sys collections deque. Banned are numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib shutil io os pty importlib runpy ctypes and any array image graph helper. Banned calls are eval exec compile import builtins getattr setattr hasattr globals locals vars dir chr ord breakpoint base64 binascii codecs. Banned runtime tricks are subprocess os system popen exec walk listdir scandir open stat read fdopen path and pathlib Path shutil io open and importlib runpy pty. also do not open or read tests directory or heldout files or gen file or ground truth file. We check via audit hook that blocks open of tests paths.

At end print capacity mAh as last token. Grading at 3 percent tolerance against true capacity from ground truth that is derived from conserved charge over main event. We have 4 hidden traces with different capacities gains baselines, all with non 64 data offset to test padding.

Files up to few thousand samples, recursion will fail, use iterative.

This is battery fuel gauge capacity, not display mura ink pool count and not OLED void volume mm3.

Good luck, the key is separating main charge from dust and recovering smeared tails.
