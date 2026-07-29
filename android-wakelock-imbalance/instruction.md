You are in an Android power lab checking wakelock leaks after Doze. Power manager logs acquire and release events with timestamp and thread id. A buggy driver sometimes leaks, acquire without later release, draining battery. You dump the log using custom WKLK file and must report total leaked hold time.

Create a program at /app/solve.py invoked as python3 /app/solve.py <scan path>. Last word printed is taken as leaked total ms.

You are provided one example scan for local dev at /app/data/scene.wklk (a few MB, a few thousand events). You may read it while developing. Hidden grading uses different scans you never saw, with different dimensions, thread counts, event counts 20k to 50k, offsets, timing, leak totals, passed as random temporary files under different paths. Do not hardcode numbers or paths from example.

Format .wklk custom binary little endian:

* Offset 0: magic WKLK four ASCII bytes.
* Offset 4: version uint32 value 1.
* Offset 8: event count N uint32.
* Offset 12: data offset uint32 where event array starts.
* Offset 16 to data offset minus 1: padding that may be garbage bytes, ignore. May contain fake WKLK magic.
* After data offset: N events, each 16 bytes: int32 id (signed, system wakelocks use negative range), uint32 type (1 acquire, 0 release), uint32 timestamp ms, uint32 thread id. Struct <iIII per event, header <4sIII plus padding. You must respect data offset, do not hardcode header size.

Each trace contains many wakelock ids observed across many threads. Each (id, thread) is an independent hold — several threads may hold the same id at once, and every hold still active at the end is counted separately; a release only affects the releasing thread's own hold.

Dump contains messy real patterns from concurrent logger: duplicate acquire logs while already held (driver logs again on rerequest, idempotent, holding stays 1 not incremented), dangling releases with no matching hold, cross thread release attempts from binder calls that do not actually release another thread holder, and reacquire after balanced cycles. System power manager thread with id 0 does force clear.

Kernel behavior:

* Each hold bound to (id, thread) pair. Acquire is idempotent per pair, release when that pair not held is no op.
* Normal cross thread release attempts are evaluated only against releasing thread own (id, thread) state and are no ops if that thread does not hold it.
* System thread 0 is exception: a release event with thread id 0 for a given wakelock id releases all holders of that id across all threads (Doze force clear for that id).
* Additionally, a release event with thread id 0 and id 0 is a Doze entry that clears all wakelocks across all ids, not just id 0.
* Acquires from thread 0 are normal independent holds for (id,0) only.

Why naive counting fails:

If you count per id ignoring thread, you miss independent holds and overcount when cross-thread noise is mistaken as balancing. If you use file order not timestamp order, you mix chronology. If you use global trace end instead of pair own timeline, you overcount early quiet pairs that stopped long before unrelated ids continued. If you use first-ever acquire instead of last still-held interval, you overcount earlier balanced cycles. If you ignore duplicate idempotency or ignore thread 0 force clears, you overcount.

Key property:

A leaked hold is measured from first acquire of its final still-held interval to its own last observation, not to global end. Earlier balanced acquire-release cycles for same pair are irrelevant. If pair only has one acquire with no later activity for that pair, its duration is zero. Duplicate acquires while held do not restart interval but do update its last observation time. Stable timestamp order matters: dump is shuffled, reconstruct chronological order, and within same millisecond logger write order is preserved.

Hidden traces vary: up to 2500 ids (30 percent negative), up to 24 threads including system thread 0, up to 50000 events, many same timestamp collisions, many cross thread releases per acquire, dangling releases, reacquire patterns, early leak with far global continuation, and system thread 0 force releases including full clear of id 0.

Implementation: parse bytes yourself using only standard library. Allowed modules include struct, sys. Banned modules: numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, shutil, io, os, posixpath, ntpath, genericpath, importlib, runpy, ctypes, pty, base64, binascii, codecs, builtins, zlib. Allowed open is only open(sys.argv[1],rb) or open(path,rb) where path is input file argument derived directly from sys.argv[1] or unmodified function param. Banned calls include eval, exec, compile, __import__, getattr, setattr, hasattr, globals, locals, vars, dir, chr, ord, breakpoint. Do not open or list /tests, heldout, _gen, ground_truth, reference. Checker blocks literal and concatenated construction and base64 encoded paths.

Print total leaked duration ms as last token on stdout. O n log n sort, iterative, up to 50k events.
