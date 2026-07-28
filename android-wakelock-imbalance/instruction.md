You are in an Android power lab checking wakelock leaks after Doze. After Doze entry, the power manager logs acquire/release events with timestamp and thread id to track which wakelocks prevent deep sleep. A buggy driver occasionally leaks – acquire without later matching release – draining battery. You dump the log via a custom WKLK file and must report total leaked hold time.

Create a program that reports the true leaked duration in milliseconds, not a naive count. Precision matters for battery blame.

Your program must be saved as `/app/solve.py`. It will be invoked as `python3 /app/solve.py <scan_path>` and the last word it prints will be taken as the leaked total. Example invoke: `python3 /app/solve.py /path/to/scan.wklk`

You are provided one example scan for local testing at `/app/data/scene.wklk` (a few MB, ~1-2k events). You may read this file while developing – you can run your solver locally to see its total – but hidden grading uses different scans you have never seen, with different dimensions, thread counts, event counts (15k-25k), offsets, timing patterns, and leak totals (tens of millions ms), passed as random temporary files under different paths. Do not hardcode numbers or paths from the example; your solver must work on any file path given as the first argument. Hardcoding the sample leaked total will fail hidden checks that vary in size, offset, and timing.

Format .wklk is a custom binary for power manager traces. Everything is little-endian:

* Offset 0: magic `WKLK` four ASCII bytes.
* Offset 4: version uint32 (1).
* Offset 8: event count N uint32.
* Offset 12: data_offset uint32 where event array starts.
* Offset 16..data_offset-1: padding that may be garbage bytes, ignore.
* After data_offset: N events, each 16 bytes: `int32 id` (signed, system wakelocks use negative range), `uint32 type` (1=acquire, 0=release), `uint32 timestamp ms`, `uint32 thread_id`. Struct format `"<iIII"` little-endian per event, but header is `<4sIII` plus padding. You must respect data_offset – don't hardcode header size. Heldouts use varied offsets 16,20,24,32,40,64,96,128.

Each trace contains many wakelock ids observed across many threads. Most acquire/release pairs end up balanced, but some are leaked – still held at end. Apart from real holds, the dump contains messy real-world patterns: duplicate acquire logs while already held, dangling releases with no matching hold, cross-thread release attempts from binder calls that do not actually release, and re-acquire after balanced cycles.

Kernel behavior you must infer from the logs (real driver semantics, not just counting):

Wakelocks are thread-affine in this driver. You see binder logs that try to release from a different thread – those attempts appear in the file but do not actually release the holder. Similarly, some logs contain duplicate acquires while already held (driver logs again on re-request) and dangling releases where nothing is held. The kernel's acquire is idempotent – holding stays 1, not incremented – and release when not held is a no-op in the kernel. A wakelock may be acquired and released many times through the night; earlier balanced cycles are irrelevant for leak blame. Only the final continuous hold per pair matters: if at the end of chronological processing a pair is still held, it is leaking, and we want how long that final hold has been active.

That leak duration is not trivial. The dump is shuffled – concurrent logger does not preserve time order – so you must reconstruct chronological order. Within the same millisecond, the logger's write order is preserved and matters: whether a duplicate is seen before a release decides if the release finds a holder. Also, each pair stops being observed at different times – some pairs go quiet early while unrelated wakelocks continue to fire thousands of ms later. The hold's age should reflect the pair's own last observation, not the global trace end. If a pair's final leak is just a single acquire line with no later activity for that pair, its leaked age is zero.

Simple shortcuts are off by a large margin. In our measurements on sample + 3 heldouts (exact integer grading):

* per-id counting (ignoring thread) overcounts 60-92% because cross-thread release noise is mistaken as balancing the true holder.
* file order instead of timestamp order overcounts 30-55% and undercounts 20-40% randomly – chronology matters.
* using global trace end instead of per-pair last observation overcounts 42-73% – a leaked pair that went quiet early should not be measured to the far future where unrelated ids are still active. This is the largest trap, analogous to including far specks in foundry.
* using first-ever acquire instead of final interval start overcounts 120-310% – earlier balanced cycles must be forgotten; only final continuous interval counts.
* ignoring duplicate-acquire idempotency (restarting interval on duplicate) overcounts 20-45% and also mishandles last observation.
* unsigned parsing of signed int32 ids misgroups 20% of pairs (system wakelocks use negative ids) and overcounts 10-25%.
* hardcoding data_offset 64 fails 6/7 heldouts that use 16,20,24,32,40,96,128 with garbage padding.

No fixed shortcut passes within exact match tolerance. Only a genuine precise method that reconstructs true thread-scoped holds, separates cross-thread noise (like separating far spatter specks), dedupes idempotent acquires without biasing interval start, ignores dangling releases, isolates final continuous interval per pair, and measures its age to its own last observation with stable timestamp order will pass. That is the hard part – similar to estimating background without bias and plateau without noise in thermal void tasks.

Hidden traces vary heavily – up to 1300 ids (20% negative), up to 16 threads, up to 25k events, 30% same-timestamp collisions, 3-6 cross-thread releases per true acquire, 20-40 dangling releases, reacquire patterns where a pair balances then leaks with duplicate noise that updates its last observation. Logs up to 25k events require O(n log n) sorting, iterative processing.

Hidden traces vary heavily – up to 1300 ids, up to 16 threads, up to 25000 events, 30% same-timestamp collisions, 20% negative ids, 3-6 cross-thread releases per true acquire, 20-40 dangling releases, reacquire patterns with balanced then leaked.

Implementation constraints: parse bytes yourself using only the standard library. Allowed modules include `struct`, `sys`. The following are banned and will be rejected by `test_from_scratch`: `numpy`, `scipy`, `skimage`, `cv2`, `PIL`, `Pillow`, `networkx`, `igraph`, `imageio`, `pandas`, `torch`, `tensorflow`, `socket`, `multiprocessing`, `glob`, `pathlib`, `shutil`, `io`, `os`, `posixpath`, `ntpath`, `genericpath`, `importlib`, `runpy`, `ctypes`, `pty`, `base64`, `binascii`, `codecs`, `builtins`, `zlib`. Allowed open is only built-in `open(sys.argv[1],'rb')` or `open(path,'rb')` where path is input file argument derived directly from sys.argv[1] or unmodified function param – that's the only file you may open. Banned calls include `eval`, `exec`, `compile`, `__import__`, `getattr`, `setattr`, `hasattr`, `globals`, `locals`, `vars`, `dir`, `chr`, `ord`, `breakpoint`. Do not attempt to open or list `/tests`, `heldout`, `_gen`, `ground_truth`, `reference`. Checker blocks literal and concatenated construction and base64 encoded paths. Your solver must work on random temporary files, not hardcoded paths.

Print the total leaked duration ms as last token on stdout.

Efficiency: O(n log n) sort, iterative, traces up to 25k events.
