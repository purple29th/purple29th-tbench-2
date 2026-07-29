You are in an Android power lab checking wakelock leaks after Doze. After Doze entry, the power manager logs acquire/release events with timestamp and thread id to track which wakelocks prevent deep sleep. A buggy driver occasionally leaks – acquire without later matching release – draining battery. You dump the log via a custom WKLK file and must report total leaked hold time.

Create a program that reports the true leaked duration in milliseconds, not a naive count. Precision matters for battery blame.

Your program must be saved as `/app/solve.py`. It will be invoked as `python3 /app/solve.py <scan_path>` and the last word it prints will be taken as the leaked total. Example invoke: `python3 /app/solve.py /path/to/scan.wklk`

You are provided one example scan for local testing at `/app/data/scene.wklk` (a few MB, ~3-4k events). You may read this file while developing – you can run your solver locally to see its total – but hidden grading uses different scans you have never seen, with different dimensions, thread counts, event counts (20k-50k), offsets, timing patterns, and leak totals (tens to hundreds of millions ms), passed as random temporary files under different paths. Do not hardcode numbers or paths from the example; your solver must work on any file path given as the first argument. Hardcoding the sample leaked total will fail hidden checks that vary in size, offset, and timing.

Format .wklk is a custom binary for power manager traces. Everything is little-endian:

* Offset 0: magic `WKLK` four ASCII bytes.
* Offset 4: version uint32 (1).
* Offset 8: event count N uint32.
* Offset 12: data_offset uint32 where event array starts.
* Offset 16..data_offset-1: padding that may be garbage bytes, ignore. May contain fake WKLK magic and random bytes.
* After data_offset: N events, each 16 bytes: `int32 id` (signed, system wakelocks use negative range), `uint32 type` (1=acquire, 0=release), `uint32 timestamp ms`, `uint32 thread_id`. Struct format `"<iIII"` little-endian per event, but header is `<4sIII` plus padding. You must respect data_offset – don't hardcode header size. Heldouts use varied offsets 16,20,24,32,40,64,96,128, plus larger 192,256.

Each trace contains many wakelock ids observed across many threads. The same wakelock id can be independently held by multiple threads at the same time. Each (id, thread) is an independent hold — several threads may hold the same id at once, and every hold still active at the end is counted separately; a release only affects the releasing thread's own hold. Most pairs end up balanced, but some are leaked – still held at end.

The dump contains messy real-world patterns from a concurrent logger: duplicate acquire logs while already held (driver logs again on re-request), dangling releases with no matching hold, cross-thread release attempts from binder calls that do not actually release another thread's holder, and re-acquire after balanced cycles. There is also a system power manager thread with id 0 that force-releases: a release event with thread_id 0 for a given wakelock id releases all holders of that id across all threads (Doze force-clear), unlike normal cross-thread releases which are no-ops. Acquires from thread 0 are normal independent holds for (id,0) only.

Kernel behavior you must infer from the logs (real driver semantics, not just counting): each hold is bound to the (id, thread_id) pair. Binder logs that try to release an id from a different thread than the holder appear but do not release another thread's hold; they are evaluated only against the releasing thread's own (id, thread) state and are no-ops if that thread does not hold it. Except thread 0 system releases which are global for that id. The kernel's acquire is idempotent per (id, thread) pair – holding stays 1, not incremented – and release when that pair is not held is a no-op. A wakelock id may be acquired and released many times through the night across different threads; earlier balanced cycles for a given pair are irrelevant for leak blame.

That leak duration is not trivial. The dump is shuffled – concurrent logger does not preserve time order – so you must reconstruct chronological order. Within the same millisecond, the logger's write order is preserved and matters: whether a duplicate is seen before a release decides if the release finds a holder, and a global thread-0 release at same ms must be ordered relative to other events for same id. Also, each pair stops being observed at different times – some pairs go quiet early while unrelated wakelocks continue to fire thousands of ms later. The hold's age should reflect the pair's own timeline, not the global trace end. If a pair's final leak is just a single acquire line with no later activity for that pair, its leaked age is zero.

Simple shortcuts are off by a large margin. In our measurements on sample + 3 heldouts (exact integer grading):

* per-id counting or single-owner-per-id (ignoring independent (id, thread) holds) undercounts ~60-70% because several threads can hold the same id at once and each leak must be summed, and also overcounts 60-92% when cross-thread release noise is mistaken as balancing the true holder.
* file order instead of timestamp order overcounts 30-55% and undercounts 20-40% randomly.
* using global trace end instead of per-pair last observation overcounts 42-73% – a leaked pair that went quiet early should not be measured to the far future where unrelated ids are still active. This is analogous to including far specks in foundry thermal void.
* using first-ever acquire instead of final interval start overcounts 120-310% – earlier balanced cycles must be forgotten.
* ignoring duplicate-acquire idempotency (restarting interval on duplicate) overcounts 20-45% and mishandles last observation.
* ignoring thread 0 global force-release overcounts 25-45% – leaked pairs that were actually cleared by system release are counted as still leaking.
* unsigned parsing of signed int32 ids misgroups 20% of pairs (system wakelocks use negative ids) and overcounts 10-25%.
* hardcoding data_offset 64 fails 6/8 heldouts that use varied offsets with garbage padding.

No fixed shortcut passes within exact match tolerance. Only a genuine precise method that reconstructs true thread-scoped holds, handles system force-releases correctly, separates cross-thread noise, and measures final interval age correctly with stable timestamp order will pass. That is the hard part – similar to estimating background without bias and plateau without noise in thermal void tasks.

Hidden traces vary heavily – up to 2500 ids (30% negative), up to 24 threads including system thread 0, up to 50000 events, 40% same-timestamp collisions, 8-12 cross-thread releases per true acquire, 30-50 dangling releases, reacquire patterns where a pair balances then leaks with duplicate noise, early leak with far global continuation to trap global-end method, and system thread 0 force-releases that clear 10-20% of ids. Logs require O(n log n) sorting, iterative processing.

Implementation constraints: parse bytes yourself using only the standard library. Allowed modules include `struct`, `sys`. The following are banned and will be rejected by `test_from_scratch`: `numpy`, `scipy`, `skimage`, `cv2`, `PIL`, `Pillow`, `networkx`, `igraph`, `imageio`, `pandas`, `torch`, `tensorflow`, `socket`, `multiprocessing`, `glob`, `pathlib`, `shutil`, `io`, `os`, `posixpath`, `ntpath`, `genericpath`, `importlib`, `runpy`, `ctypes`, `pty`, `base64`, `binascii`, `codecs`, `builtins`, `zlib`. Allowed open is only built-in `open(sys.argv[1],'rb')` or `open(path,'rb')` where path is input file argument derived directly from sys.argv[1] or unmodified function param – that's the only file you may open. Banned calls include `eval`, `exec`, `compile`, `__import__`, `getattr`, `setattr`, `hasattr`, `globals`, `locals`, `vars`, `dir`, `chr`, `ord`, `breakpoint`. Do not attempt to open or list `/tests`, `heldout`, `_gen`, `ground_truth`, `reference`. Checker blocks literal and concatenated construction and base64 encoded paths. Your solver must work on random temporary files, not hardcoded paths.

Print the total leaked duration ms as last token on stdout.

Efficiency: O(n log n) sort, iterative, traces up to 50k events.
