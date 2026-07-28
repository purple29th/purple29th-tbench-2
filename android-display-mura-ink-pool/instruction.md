hey so i am in display touch lab we chase ghost touches after ink leak in lamination. the panel capacitive grid logs raw capacitance. when ink pools you get high capacitance plus bleed lines plus far dust specks.

we dump grid via custom file cdmr. kotlin test writes ByteBuffer little endian via FileOutputStream.

your job is write /app/solve.py that reads path as first arg. we run python3 /app/solve.py /path/to/scan.cdmr and last token of stdout must be integer count of touch cells truly ink affected after you clean halo and dust.

sample at /app/data/scene.cdmr you can try locally. hidden grading uses other files you never saw with different ink sizes, gain, pitch, baseline drift, dust. dont hardcode sample.

cdmr format is my tiny container for capacitive mura.

first four bytes ascii CDMR magic
next four bytes u32 version 1
next four bytes u32 total cells
next four bytes u32 data offset
next four bytes f32 sx pitch mm per cell x
next four bytes f32 sy pitch mm per cell y
next four bytes u32 baseline capacitance floor
next four bytes two u32 nx ny
header at least 36 bytes plus padding, respect data offset

payload at offset is nx times ny int16 little endian capacitance values, x fastest so index equals x plus nx times y

content: one main ink pool where capacitance high plus thin bleed lines where cell partly filled mid value plus flat background baseline plus noise plus far dust blobs far away trash you must ignore and keep biggest mass cluster using 8 neighbours pick by mass not count.

simple fixed threshold fails. low threshold grabs halo and merges dust overcounts 70 percent, high threshold misses bleed lines undercounts.

real trick: capacitive smear conserves total charge. interior flat saturated but hidden by smear and noise. you need to estimate baseline robustly via median low half, get residual, 8 connected components above noise, keep biggest mass to drop dust, estimate plateau from interior via mean filter peak, integrate total residual over pool plus halo divided by plateau to get true affected cells count. exact numbers not prescribed must be robust.

parse binary yourself using only struct. banned are numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib shutil io os. also banned tricks like subprocess os system popen exec and dunder builtins dict subclasses mro and importlib runpy ctypes eval exec compile and getattr setattr hasattr globals locals vars dir chr ord base64 etc. do not open tests directory or heldout files.

at end print integer count as last token. grading exact int match with small tolerance against true count from ground_truth.json geometric truth.

files may have up to couple thousand cells, recursion will fail, use iterative.

this is ghost touch counting, not volume area. different from oled void which is mm3 IR volume.
