#!/usr/bin/env python3
"""Oracle for android-wakelock-imbalance: total leaked duration per (id, thread) with dedup."""

import struct
import sys
from collections import defaultdict


def parse(path):
    d = open(path, "rb").read()
    if len(d) < 16 or d[:4] != b"WKLK":
        raise ValueError("bad magic")
    total = struct.unpack_from("<I", d, 8)[0]
    off = struct.unpack_from("<I", d, 12)[0]
    events = []
    o = off
    for _ in range(total):
        if o + 16 > len(d):
            break
        eid, etype, ts, tid = struct.unpack_from("<iIII", d, o)
        o += 16
        events.append((eid, etype, ts, tid))
    return events


def solve_one(path):
    events = parse(path)
    # sort by timestamp to respect log order
    events.sort(key=lambda x: x[2])

    held = {}
    first_acq = {}
    last_ts = {}

    for eid, etype, ts, tid in events:
        key = (eid, tid)
        if key not in last_ts or ts > last_ts[key]:
            last_ts[key] = ts
        if etype == 1:  # acquire
            if held.get(key, False):
                # duplicate acquire without intervening release: count once
                continue
            held[key] = True
            if key not in first_acq:
                first_acq[key] = ts
            else:
                if ts < first_acq[key]:
                    first_acq[key] = ts
        else:  # release
            if not held.get(key, False):
                # dangling release: no matching acquire from same thread, ignore
                continue
            held[key] = False

    total_leaked = 0
    for key, is_held in held.items():
        if is_held:
            total_leaked += last_ts[key] - first_acq[key]

    print(total_leaked)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(0)
    else:
        solve_one(sys.argv[1])
