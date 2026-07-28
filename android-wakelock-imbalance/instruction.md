hey so i am in android framework lab we track wakelock leaks that kill battery after doze update. the system has power manager that logs wakelock acquire and release with timestamp and thread id from native.

we dump log via custom file wklk. kotlin test writes ByteBuffer little endian via FileOutputStream.

your job is write /app/solve.py that reads path as first arg. we run python3 /app/solve.py /path/to/scan.wklk and last token of stdout must be integer total leaked duration in ms for wakelocks that have imbalance.

sample at /app/data/scene.wklk you can try locally. expected timestamp-order leaked total for sample is 358620 ms (file-order would be 464265, so you must sort). hidden grading uses other files you never saw with different wakelock counts (500-750 ids, 8000-11500 events), acquire release patterns, timestamps, threads up to 12, varied data offsets (16,24,40,96,128,20,32 etc), signed ids including negative, same-timestamp collisions 15 percent requiring stable sort, and shuffled file order. dont hardcode sample.

wklk format is my tiny container.

first four bytes ascii WKLK magic
next four bytes u32 version 1
next four bytes u32 event count
next four bytes u32 data offset
header at least 16 bytes plus padding, respect data offset - parser must use header data_offset field, not hardcode 64, as heldouts use varied offsets (16,24,40,96,128 etc). padding between header end and offset may contain garbage 0xAA pattern, you must ignore, start reading events at offset.

each event: int32 id (signed, may be negative), u32 type 1 acquire 0 release, u32 timestamp ms, u32 thread id. all little endian, fixed 16 bytes per event.

trace contains many acquire and release events. most balanced but some leaked where acquire without matching release. need to compute per id and thread, not just per id: for each id and thread pair, duplicate acquire from same thread without intervening release is counted once (dedup), release without matching acquire from same thread ignored, thread scoped matching. So for each id thread pair that ends up held after processing events in timestamp order, duration equals last timestamp seen for that same id thread pair minus first acquire timestamp of its final still-held interval.

ordering contract: file order is NOT timestamp order. records in the file may be shuffled. you must process events in stable timestamp order increasing, preserving original file order for equal timestamps (python stable sort by timestamp). if you process in file order you will fail hidden tests. sample demonstrates this: file-order total 464265 vs timestamp-order 358620, grading expects timestamp-order. do not assume sorted.

Clarification on duration: if same (id, thread) has earlier balanced acquire/release cycles then later acquires and stays held, only the final continuously-held interval counts. Example: acquire@10 release@20 acquire@30 duplicate@40 leak (last event for that pair at 40) => held interval starts at 30, duration = last_ts_for_pair - 30 = 10, not 40-10=30. If final leak has only single acquire, duration = 0 (last==first). Sum across leaked id thread pairs.

same-timestamp collisions: multiple events may share same timestamp. you must handle stable order: when timestamps equal, keep file order (python's sort is stable if you sort only by timestamp). this matters for acquire/release at same ms.

simple per id counting of acquires minus releases fails because cross thread releases and duplicate acquires make naive overcount huge, we measured naive 1238 vs true 34 for one heldout, and file-order vs timestamp-order mismatch makes gpt fail.

parse binary yourself using only struct. allowed: you may use built-in open(sys.argv[1], 'rb').read() or open(path,'rb').read() where path is the function argument for the scan file; this is the only permitted file read for the input trace. banned modules are numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib shutil io os pty importlib runpy ctypes and any array image graph helper. banned calls are eval exec compile import builtins getattr setattr hasattr globals locals vars dir chr ord breakpoint base64 binascii codecs and os.system os.popen etc. banned runtime tricks that remain banned: subprocess, walk, listdir, scandir, stat, fdopen, path and pathlib Path shutil io open (except built-in open for the given scan path) and importlib runpy pty. also do not try to open or read tests directory or heldout files or gen file or ground truth file. we check via AST and decoded string literals plus construction via concatenation - the checker enforces banned modules and checks you don't have forbidden path literals like "/tests", "heldout", "_gen", "ground_truth" even via "/tes"+"ts/data" concatenation.

at end print integer leaked duration as last token. grading exact int match against ground truth which is per id thread with dedup and final-interval rule and timestamp-order.

files up to many thousand events (8000-11500 for hidden, 400+ for sample, may grow), use iterative, not recursion. need efficient O(n log n) sort.

this is android os wakelock leak detector, different from bitmap pool and display mura ink pool and battery pressure. now genuinely needs thread scoped reasoning and timestamp sorting not just trivial counting.

good luck.
