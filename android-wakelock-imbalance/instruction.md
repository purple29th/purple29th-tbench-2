hey so i am in android framework lab we track wakelock leaks that kill battery after doze update. the system has power manager that logs wakelock acquire and release with timestamp and thread id from native.

we dump log via custom file wklk. kotlin test writes ByteBuffer little endian via FileOutputStream.

your job is write /app/solve.py that reads path as first arg. we run python3 /app/solve.py /path/to/scan.wklk and last token of stdout must be integer total leaked duration in ms for wakelocks that have imbalance.

sample at /app/data/scene.wklk you can try locally. hidden grading uses other files you never saw with different wakelock counts, acquire release patterns, timestamps, threads, all sorted by timestamp but many cross thread releases and duplicate acquires. dont hardcode sample.

wklk format is my tiny container.

first four bytes ascii WKLK magic
next four bytes u32 version 1
next four bytes u32 event count
next four bytes u32 data offset
header at least 16 bytes plus padding, respect data offset

each event: int32 id, u32 type 1 acquire 0 release, u32 timestamp ms, u32 thread id. all little endian.

trace contains many acquire and release events. most balanced but some leaked where acquire without matching release. need to compute per id and thread, not just per id: for each id and thread pair, duplicate acquire from same thread without intervening release is counted once, release without matching acquire from same thread ignored, thread scoped matching. So for each id thread pair that ends up held after processing events in timestamp order, duration equals last timestamp for that id thread minus first acquire timestamp for that id thread, sum across leaked id thread pairs.

simple per id counting of acquires minus releases fails because cross thread releases and duplicate acquires make naive overcount huge, we measured naive 1238 vs true 34 for one heldout.

parse binary yourself using only struct. banned modules are numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib shutil io os pty importlib runpy ctypes and any array image graph helper. banned calls are eval exec compile import builtins getattr setattr hasattr globals locals vars dir chr ord breakpoint base64 binascii codecs. banned runtime tricks are subprocess os system popen exec walk listdir scandir open stat read fdopen path and pathlib Path shutil io open and importlib runpy pty. also do not open or read tests directory or heldout files or gen file or ground truth file. we check via AST and decoded string literals.

at end print integer leaked duration as last token. grading exact int match against ground truth from ground_truth.json which is per id thread with dedup.

files up to few thousand events, use iterative.

this is android os wakelock leak detector, different from bitmap pool and display mura ink pool and battery pressure. now genuinely needs thread scoped reasoning not just trivial counting.

good luck.
