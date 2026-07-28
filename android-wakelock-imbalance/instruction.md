hey so i am in android framework lab we track wakelock leaks that kill battery after doze update. the system has power manager that logs wakelock acquire and release with timestamp from native.

we dump log via custom file wklk. kotlin test writes ByteBuffer little endian via FileOutputStream.

your job is write /app/solve.py that reads path as first arg. we run python3 /app/solve.py /path/to/scan.wklk and last token of stdout must be integer total leaked duration in ms for wakelocks that have imbalance.

sample at /app/data/scene.wklk you can try locally. hidden grading uses other files you never saw with different wakelock counts, acquire release patterns, timestamps, threads. dont hardcode sample.

wklk format is my tiny container.

first four bytes ascii WKLK magic
next four bytes u32 version 1
next four bytes u32 event count
next four bytes u32 data offset
header at least 16 bytes plus padding, respect data offset

each event: int32 id, u32 type 1 acquire 0 release, u32 timestamp ms, u32 thread id. all little endian.

trace contains many acquire and release events. most balanced but some leaked where acquire without matching release, or release without acquire ignored, or duplicate acquire counted once, or cycle where wakelock A acquire needs B.

you need to compute for each id total acquire count minus release count, if positive then leaked, compute duration as last timestamp minus first acquire timestamp for that id, sum across leaked ids.

simple counting fails because duplicate acquires and out of order and dangling thread ids.

parse binary yourself using only struct. banned are numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow. also banned tricks like subprocess os system popen exec and dunder builtins dict subclasses mro and importlib runpy ctypes eval exec compile and getattr setattr hasattr globals locals vars dir chr ord base64 etc. do not open tests directory or heldout files.

at end print integer leaked duration as last token. grading exact int match on heldouts, we recompute via independent counting.

files up to few thousand events, recursion will fail, use iterative.

this is android os wakelock leak detector, related to bitmap pool leak detector but for power manager.

good luck.
