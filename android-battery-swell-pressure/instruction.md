hey so i am in android battery lab we track pouch swelling after fast charge in heat. the phone has strain gauge on pouch that logs pressure. when gas builds you get pressure spike that is smeared by sensor filter plus baseline drift plus dust blips.

we dump trace via custom file bswp. kotlin test writes ByteBuffer little endian via FileOutputStream.

your job is write /app/solve.py that reads path as first arg. we run python3 /app/solve.py /path/to/scan.bswp and last token of stdout must be float that is true pressure peak in kPa after you clean baseline and dust.

sample at /app/data/scene.bswp you can try locally. hidden grading uses other files you never saw with different pressure peaks, widths, gain, baseline, noise, dust blips. dont hardcode sample.

bswp format is my tiny container.

first four bytes ascii BSWP magic
next four bytes u32 version 1
next four bytes u32 total samples
next four bytes u32 data offset
next four bytes f32 sample rate hz
next four bytes f32 gain
next four bytes u32 baseline floor kPa times 10 maybe
header at least 36 bytes plus padding, respect data offset

payload at offset is total int16 little endian pressure values times 10, x fastest.

trace has flat background baseline plus noise plus one main pressure spike where gas builds. spike has thick core where pressure flat high plus thin tails from filter smear. some files have one or two tiny blips far away dust artefacts trash you must ignore and keep biggest mass cluster.

simple fixed threshold fails. low threshold grabs halo and overestimates, high threshold misses tails and underestimates. no fixed cut works because gain baseline shift per batch.

real trick: filter smear conserves total pressure, interior flat saturated but hidden. best clue is where pressure most concentrated not just how many bright samples.

parse binary yourself using only struct. banned are numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib shutil io os. also banned tricks like subprocess os system popen exec and dunder builtins dict subclasses mro and importlib runpy ctypes eval exec compile and getattr setattr hasattr globals locals vars dir chr ord base64 etc. do not open tests directory or heldout files.

at end print float peak kPa as last token. grading at 3 percent tolerance against true peak from ground truth. we have 3 hidden traces with different peaks gains baselines dust.

files may have up to few thousand samples, recursion will fail, use iterative.

this is battery swell pressure, not subvoxel volume. different from oled bond void which is mm3 IR volume and display mura ink pool which is count.

good luck.
