hey so i am in android fingerprint lab we see oil smear that blocks sensor after factory assembly. the under display optical fingerprint sensor captures raw image. when oil from display glue leaks it pools and makes bright smear plus thin bleed lines plus dust specks far away.

we dump the image via custom file fpos. kotlin test writes ByteBuffer little endian via FileOutputStream.

your job is write /app/solve.py that reads file path as first arg. we run python3 /app/solve.py /path/to/scan.fpos and last token of stdout must be integer count of fingerprint pixels truly oil affected after you clean halo and dust.

sample at /app/data/scene.fpos you can try locally. hidden grading uses other files you never saw with different oil sizes, gain, pitch, baseline, dust. dont hardcode sample.

fpos format is my tiny container for fingerprint oil smear.

first four bytes ascii FPOS magic
next four bytes u32 version 1
next four bytes u32 total pixels
next four bytes u32 data offset
next four bytes f32 sx pitch mm per pixel x
next four bytes f32 sy pitch mm per pixel y
next four bytes u32 baseline floor
next four bytes two u32 nx ny
header at least 36 bytes plus padding, respect data offset

payload at offset is nx times ny int16 little endian brightness values, x fastest so index equals x plus nx times y

content: one main oil smear where brightness high plus thin bleed lines where cell partly filled mid value plus flat background baseline plus noise plus far dust blobs far away trash you must ignore and keep biggest mass cluster using 8 neighbours pick by mass not count.

simple fixed threshold fails. low threshold grabs halo and merges dust overcounts 70 percent, high threshold misses bleed lines undercounts.

real trick: smear conserves total light. interior saturated flat but hidden by smear and noise. best clue is where light most concentrated not just how many bright pixels.

parse binary yourself using only struct. banned are numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib shutil io os. also banned tricks like subprocess os system popen exec and dunder builtins dict subclasses mro and importlib runpy ctypes eval exec compile and getattr setattr hasattr globals locals vars dir chr ord base64 etc. do not open tests directory or heldout files.

at end print integer count as last token. grading exact int match with small tolerance against true count from ground truth.

files may have up to few thousand pixels, recursion will fail, use iterative.

this is fingerprint oil smear counting, not oled void volume mm3 and not display mura ink pool count cdmr. different sensor optical fingerprint vs capacitive touch vs IR.

good luck.
