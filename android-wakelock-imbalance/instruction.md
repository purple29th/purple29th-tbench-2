You are in an Android power lab checking wakelock leaks after Doze. Power manager logs acquire and release events with timestamp and thread id. A buggy driver sometimes leaks, acquire without later release, draining battery. You dump the log using custom WKLK file and must report total leaked hold time.

Create a program at /app/solve.py invoked as python3 /app/solve.py <scan path>. Last word printed is taken as leaked total ms. Example: python3 /app/solve.py /path/to/scan.wklk

You are provided one example scan for local dev at /app/data/scene.wklk (a few MB, a few thousand events). You may read it while developing. Hidden grading uses different scans you never saw, with different dimensions, thread counts, event counts 20k to 50k, offsets, timing, leak totals, passed as random temporary files under different paths. Do not hardcode numbers or paths from example. Solver must work on any file path given as first argument.

Format .wklk custom binary little endian:

* Offset 0: magic WKLK four ASCII bytes.
* Offset 4: version uint32 value 1.
* Offset 8: event count N uint32.
* Offset 12: data offset uint32 where event array starts.
* Offset 16 to data offset minus 1: padding that may be garbage bytes, ignore. May contain fake WKLK magic.
* After data offset: N events, each 16 bytes: int32 id (signed, system wakelocks use negative range), uint32 type (1 acquire, 0 release), uint32 timestamp ms, uint32 thread id. Struct <iIII per event, header <4sIII plus padding. You must respect data offset, do not hardcode header size. Heldouts use varied offsets 16,20,24,32,40,64,96,128,192,256.

Each trace contains many wakelock ids observed across many threads. Same id can be independently held by several threads at same time. Each (id, thread) is independent hold. Several threads may hold same id at once, every hold still active at end counts separately.

Dump contains messy real patterns from concurrent logger: duplicate acquire logs while already held (driver logs again on rerequest, idempotent), dangling releases with no matching hold, cross thread release attempts from binder calls that do not actually release another thread holder, and reacquire after balanced cycles. System power manager thread with id 0 does force clear.

Kernel behavior:

* Each hold bound to (id, thread) pair. Acquire is idempotent per pair, holding stays 1 not incremented, and release when that pair not held is no op.
* Normal cross thread release attempts are evaluated only against releasing thread own (id, thread) state and are no ops if that thread does not hold it.
* System thread 0 is exception: a release event with thread id 0 for a given wakelock id releases all holders of that id across all threads (Doze force clear for that id). Unlike normal cross thread releases which are no ops.
* Additionally, a release event with thread id 0 and id 0 is a Doze entry that clears all wakelocks across all ids, not just id 0. This is full system suspend.
* Acquires from thread 0 are normal independent holds for (id,0) only.

Leak duration:

Dump is shuffled, concurrent logger does not preserve time order, so you must reconstruct chronological order by timestamp. Within same millisecond, logger write order is preserved and matters. Whether duplicate is seen before release decides if release finds holder, and a global thread 0 release at same ms must be ordered relative to other events for same id.

Also each pair stops being observed at different times. Some pairs go quiet early while unrelated wakelocks continue to fire thousands ms later. Hold age should reflect pair own timeline, not global trace end. If pair final leak is just a single acquire line with no later activity for that pair, its leaked age is zero. You need per-pair last observation, not global trace end, and final interval only (earlier balanced cycles irrelevant).

Hidden traces vary: up to 2500 ids (30 percent negative), up to 24 threads including system thread 0, up to 50000 events, 40 percent same timestamp collisions, many cross thread releases per acquire, 30 to 50 dangling, reacquire patterns where pair balances then leaks with duplicate noise, early leak with far global continuation, and system thread 0 force releases that clear holders including full clear of id 0.

Implementation: parse bytes yourself using only standard library. Allowed modules include struct, sys. Banned modules: numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, shutil, io, os, posixpath, ntpath, genericpath, importlib, runpy, ctypes, pty, base64, binascii, codecs, builtins, zlib. Allowed open is only open(sys.argv[1],rb) or open(path,rb) where path is input file argument derived directly from sys.argv[1] or unmodified function param. Banned calls include eval, exec, compile, __import__, getattr, setattr, hasattr, globals, locals, vars, dir, chr, ord, breakpoint. Do not open or list /tests, heldout, _gen, ground_truth, reference. Checker blocks literal and concatenated construction and base64 encoded paths. Solver must work on random temporary files.

Print total leaked duration ms as last token on stdout. O n log n sort, iterative, up to 50k events.
