#!/usr/bin/env python3
"""Oracle for android-wakelock-imbalance v0.14 hard.

Foundry-inspired hardening: thread-affine, idempotent acquire, cross-thread noise,
final interval only, per-pair last observation, stable timestamp order, plus
thread 0 system force-release (global for that id).

Leak = sum over (id,thread) still held at end of chronological processing of
(last_ts_observed_for_that_pair - first_acq_of_final_interval). If just one
acquire with no later activity for that pair, duration 0. Duplicate while held
updates last_ts but does not restart interval. Cross-thread release ignored for
state but counts as observation for its own (id,other_tid) pair. Release with
thread_id 0 is special: it force-releases all holders of that id across all
threads (Doze force-clear), unlike normal cross-thread no-ops.
"""

import struct
import sys


def parse(path):
    d = open(path, "rb").read()
    if len(d) < 16 or d[:4] != b"WKLK":
        raise ValueError("bad magic")
    total = struct.unpack_from("<I", d, 8)[0]
    off = struct.unpack_from("<I", d, 12)[0]
    events = []  # (eid, etype, ts, tid, orig_idx)
    o = off
    idx = 0
    for _ in range(total):
        if o + 16 > len(d):
            break
        eid, etype, ts, tid = struct.unpack_from("<iIII", d, o)
        o += 16
        events.append((eid, etype, ts, tid, idx))
        idx += 1
    return events


def solve_one(path):
    events = parse(path)
    # stable timestamp order: sort by ts, then orig file order to preserve logger write order within same ms
    events_sorted = sorted(events, key=lambda x: (x[2], x[4]))

    held = {}  # (id,tid) -> bool
    first_acq = {}  # (id,tid) -> ts of first acquire of final still-held interval
    last_ts = {}  # (id,tid) -> max ts seen for that pair (any event type)

    for eid, etype, ts, tid, _orig in events_sorted:
        # Thread 0 release is global force-release for that id, plus hidden id 0 clears ALL
        if tid == 0 and etype == 0:
            if eid == 0:
                # hidden Doze entry: clears ALL wakelocks across all ids
                key0 = (0, 0)
                if key0 not in last_ts or ts > last_ts[key0]:
                    last_ts[key0] = ts
                for k in list(held.keys()):
                    if held.get(k, False):
                        held[k] = False
                        first_acq[k] = None
                continue
            key0 = (eid, 0)
            if key0 not in last_ts or ts > last_ts[key0]:
                last_ts[key0] = ts
            for k in list(held.keys()):
                if k[0] == eid and held.get(k, False):
                    held[k] = False
                    first_acq[k] = None
            continue

        key = (eid, tid)
        # per-pair last observation: any event for this exact (id,thread) pair, even dup/dangling, counts
        if key not in last_ts or ts > last_ts[key]:
            last_ts[key] = ts
        if etype == 1:  # acquire
            if held.get(key, False):
                # idempotent - already held, duplicate log is harmless no-op, but last_ts already updated
                continue
            held[key] = True
            first_acq[key] = ts
        else:  # release
            if not held.get(key, False):
                # dangling or cross-thread attempt already filtered by key mismatch for cross-thread,
                # but for same key dangling is noise
                continue
            held[key] = False
            first_acq[key] = None

    total_leaked = 0
    for key, is_held in held.items():
        if is_held:
            f = first_acq.get(key)
            if f is not None:
                # per-pair last, not global trace end - if pair stopped early, don't extend to global max
                total_leaked += last_ts[key] - f

    print(total_leaked)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(0)
    else:
        solve_one(sys.argv[1])
