You are in an Android power lab checking wakelock leaks after Doze. Power manager logs acquire and release events with timestamp and thread id. A buggy driver sometimes leaks, acquire without later release, draining battery. You dump the log using custom WKLK file and must report total leaked hold time.

Create a program that reports true leaked duration in milliseconds. It will be saved as /app/solve.py and invoked as python3 /app/solve.py <scan path> and last word it prints is taken as leaked total. Example: python3 /app/solve.py /path/to/scan.wklk

You are provided one example scan for local dev at /app/data/scene.wklk (a few MB, a few thousand events). You may read this file while developing. You can run your solver locally. Hidden grading uses different scans you have never seen, with different dimensions, thread counts, event counts 20k to 50k, offsets, timing patterns, leak totals, passed as random temporary files under different paths. Do not hardcode numbers or paths from example. Solver must work on any file path given as first argument. Hardcoding sample total will fail hidden checks.

Format .wklk is custom binary for power manager traces. Everything little endian:

* Offset 0: magic WKLK four ASCII bytes.
* Offset 4: version uint32 value 1.
* Offset 8: event count N uint32.
* Offset 12: data offset uint32 where event array starts.
* Offset 16 to data offset minus 1: padding that may be garbage bytes, ignore. May contain fake WKLK magic and random bytes.
* After data offset: N events, each 16 bytes: int32 id (signed, system wakelocks use negative range), uint32 type (1 is acquire, 0 is release), uint32 timestamp ms, uint32 thread id. Struct format <iIII little endian per event, but header is <4sIII plus padding. You must respect data offset, do not hardcode header size. Heldouts use varied offsets 16,20,24,32,40,64,96,128, plus larger 192,256.

Each trace contains many wakelock ids observed across many threads. Same id can be independently held by several threads at same time. Each (id, thread) is independent hold. Several threads may hold same id at once, every hold still active at end is counted separately for leak total.

Dump contains messy real world patterns from concurrent logger: duplicate acquire logs while already held (driver logs again on rerequest), dangling releases with no matching hold, cross thread release attempts from binder calls that do not actually release another thread holder, and reacquire after balanced cycles. System power manager thread with id 0 does force clear when it logs releases. Its release semantics are broader than normal cross thread releases which are no ops for other holders. Look at sample to infer exact scope and typical Doze behavior where system clears. Some clears affect more than just one id.

Kernel behavior you must infer from logs and sample: each hold is bound to (id, thread) pair. Acquire is idempotent per pair, holding stays 1 not incremented. Release when that pair not held is no op. Normal cross thread release attempts are evaluated only against releasing thread own (id, thread) state and are no ops if that thread does not hold it. System thread 0 is exception with broader clear. Acquires from thread 0 themselves are tracked.

Leak duration is not trivial. Dump is shuffled, concurrent logger does not preserve time order, so you must reconstruct chronological order. Within same millisecond, logger write order is preserved and matters whether duplicate is seen before release etc. Also each pair stops being observed at different times. Some pairs go quiet early while unrelated wakelocks continue to fire thousands of ms later. Hold age should reflect pair own timeline, not global trace end. If pair final leak is just a single acquire line with no later activity for that pair, its leaked age is zero.

Hidden traces vary heavily. Up to 2500 ids (30 percent negative), up to 24 threads including system thread 0, up to 50000 events, 40 percent same timestamp collisions, many cross thread releases per true acquire, 30 to 50 dangling releases, reacquire patterns where pair balances then leaks with duplicate noise, early leak with far global continuation, and system thread 0 force releases that clear holders. Some Doze entries clear more than one id. Logs require O n log n sorting, iterative processing. You must inspect sample file behavior to get force clear scope right.

Implementation constraints: parse bytes yourself using only standard library. Allowed modules include struct, sys. The following are banned and will be rejected by test from scratch: numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, shutil, io, os, posixpath, ntpath, genericpath, importlib, runpy, ctypes, pty, base64, binascii, codecs, builtins, zlib. Allowed open is only built in open(sys.argv[1],rb) or open(path,rb) where path is input file argument derived directly from sys.argv[1] or unmodified function param. That is only file you may open. Banned calls include eval, exec, compile, __import__, getattr, setattr, hasattr, globals, locals, vars, dir, chr, ord, breakpoint. Do not attempt to open or list /tests, heldout, _gen, ground_truth, reference. Checker blocks literal and concatenated construction and base64 encoded paths. Solver must work on random temporary files, not hardcoded paths.

Print total leaked duration ms as last token on stdout.

Efficiency: O n log n sort, iterative, traces up to 50k events.
