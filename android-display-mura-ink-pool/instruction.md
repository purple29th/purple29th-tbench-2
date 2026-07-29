hey so i am in display touch lab we chase ghost touches after ink leak in lamination. the panel capacitive grid logs raw capacitance. when ink pools you get high capacitance plus bleed lines plus far dust specks that look bright but far. sometimes center is near edge of panel.

we dump grid via custom file cdmr. kotlin test writes ByteBuffer little endian via FileOutputStream.

your job is write /app/solve.py that reads path as first arg. we run python3 /app/solve.py /path/to/scan.cdmr and last token of stdout must be integer count of touch cells truly ink affected after you clean halo and dust.

sample at /app/data/scene.cdmr you can try locally. hidden grading uses other files you never saw with different ink sizes, gain, pitch, baseline drift, dust count and brightness, and off-center pools. dont hardcode sample.

cdmr format is my tiny container.

first four bytes ascii CDMR magic
next four bytes u32 version 1 or 2 may vary
next four bytes u32 total cells
next four bytes u32 data offset varies 64 to around 128 due to padding you must read it and seek do not hardcode 64
next four bytes f32 sx pitch mm per cell x
next four bytes f32 sy pitch mm per cell y
next four bytes u32 baseline capacitance floor
next four bytes two u32 nx ny
header at least 36 bytes plus padding, respect data offset

payload at offset is nx times ny int16 little endian capacitance values, x fastest so index equals x plus nx times y

content: one main ink pool where capacitance high plus thin bleed lines where cell partly filled mid value plus flat background baseline plus noise plus far dust blobs far away. dust may be many blobs (up to 6) with total charge comparable to main pool, and may be brighter (up to 1.5x plateau) or larger area than main but lower total charge. some dust blobs may have larger area than main pool so selecting by area fails.

true count definition: this is NOT just number of cells above threshold. each touch cell has fractional occupancy due to partial fill. interior fully filled =1.0, border annulus partial, bleed lines partial. sum over all y,x of occupancy gives fractional count, then rounded to nearest int. that is the ground truth. it equals total conserved charge divided by saturated interior plateau. blur spreads but conserves total charge, so you can recover true count despite smear.

why threshold fails: low threshold grabs halo and merges dust overcounts; high threshold misses bleed lines undercounts; fixed cut fails because gain/baseline shift per batch and psf changes.

real challenge: smear conserves total charge but hides true plateau. you must separate main pool from far dust, estimate background without bias from main pool itself, estimate true plateau level without being fooled by noise or dust, and decide how far faint halo extends without merging dust. hint: main pool has largest total excess charge mass not largest area. halo contains significant charge beyond initial bright mask especially when psf large and noise high, skipping halo growth undercounts by more than tolerance. dust isolation and halo inclusion are both required.

sample: scene.cdmr has true count integral 249. grading tolerance is +- max(2, 3 percent of expected). so 249 +-7 allowed locally. hidden maps have similar tolerance.

parse binary yourself using only struct. banned are numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib shutil io os. also banned tricks like subprocess os system popen exec and dunder builtins dict subclasses mro and importlib runpy ctypes eval exec compile and getattr setattr hasattr globals locals vars dir chr ord base64 etc. do not open tests directory or heldout files.

at end print integer count as last token. grading compares last stdout int against ground truth integral with tolerance 3 percent.

files may have up to few thousand cells (48x48 up to 80x80 and 72x72), long runs may cause recursion error, use iterative.
