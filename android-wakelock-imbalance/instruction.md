we track wakelock leaks after doze. power manager logs acquire/release with timestamp and thread id. we dump via custom WKLK file.

write /app/solve.py; we run python3 /app/solve.py /path/to/scan.wklk and your stdout's last token must be integer total leaked duration ms.

sample trace at /app/data/scene.wklk – you can test locally. expected leaked total is 566249. hidden evaluation uses other traces you haven't seen, with more ids and events.

WKLK format (little endian):
- 0..3: ascii 'WKLK'
- 4..7: u32 version (1)
- 8..11: u32 event count N
- 12..15: u32 data_offset
- 16..data_offset-1: padding (may be garbage, ignore)
- then N events at data_offset, each 16 bytes:
    int32 id (signed, can be negative)
    u32 type (1=acquire, 0=release)
    u32 timestamp ms
    u32 thread_id
all little endian, struct "<iIII"

You must respect data_offset – don't hardcode header size. Heldouts use varied offsets.

Trace semantics:
most acquire/release pairs are balanced but some are leaked (acquire without later matching release). We measure leak per (wakelock id, thread id) pair, not per id alone. Releases are thread-scoped – a release only matches an acquire from the same thread. The dump may contain duplicate acquires and dangling releases; handle them so that at most one hold is tracked per pair at a time. If a pair had earlier balanced cycles then later leaks, only its final continuous held interval should contribute.

Leaked duration per pair: last timestamp observed for that (id,thread) pair minus first acquire timestamp of its final still-held interval. If final leak is just one acquire, duration 0. Sum across all pairs that end up held.

Ordering:
File order is not timestamp order – log is shuffled. You need to process in timestamp order. If timestamps equal, preserve original file order (the logger's write order within same ms matters for acquire vs release at same ms).

Edge traits in hidden traces: 700-900 distinct ids, up to 12 threads, 10000-16000 events, negative ids, many shuffled records, same-timestamp collisions (20-25%), varied offsets (16,24,40,96,128,32 etc), duplicate acquires, cross-thread releases, final-interval reacquire patterns.

Output: print integer sum as last token. No extra file reads.

Constraints: parser must be stdlib only (struct). Allowed open is only built-in open(sys.argv[1],'rb') or open(path,'rb') where path is input file argument – that's the only file you may open. Banned: numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib shutil io os pty importlib runpy ctypes base64 binascii codecs builtins sub* etc. Also banned eval exec compile __import__ getattr setattr hasattr globals locals vars dir chr ord breakpoint. Don't try to open /tests, heldout, _gen, ground_truth, reference – checker blocks literal and concatenated construction and base64 encoded paths.

Efficiency: O(n log n) sort, iterative, traces up to 16k events.

This is wakelock leak detector, not bitmap pool or battery swell. Good luck.
