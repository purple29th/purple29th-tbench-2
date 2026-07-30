#!/usr/bin/env python3
"""Oracle v0.21 - even ref-counted, odd binary, plus thread0 per-id and all-clear id0."""
import struct, sys
def parse(path):
    d = open(path, "rb").read()
    if len(d) < 16 or d[:4] != b"WKLK":
        raise ValueError("bad magic")
    total = struct.unpack_from("<I", d, 8)[0]
    off = struct.unpack_from("<I", d, 12)[0]
    events = []
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
    events_sorted = sorted(events, key=lambda x: (x[2], x[4]))
    held = {}
    held_count = {}
    first_acq = {}
    last_ts = {}
    for eid, etype, ts, tid, _orig in events_sorted:
        if tid == 0 and etype == 0:
            if eid == 0:
                key0 = (0, 0)
                if key0 not in last_ts or ts > last_ts[key0]:
                    last_ts[key0] = ts
                for k in list(held.keys()):
                    if held.get(k, False):
                        held[k] = False
                        first_acq[k] = None
                        held_count[k] = 0
                continue
            key0 = (eid, 0)
            if key0 not in last_ts or ts > last_ts[key0]:
                last_ts[key0] = ts
            for k in list(held.keys()):
                if k[0] == eid and held.get(k, False):
                    held[k] = False
                    first_acq[k] = None
                    held_count[k] = 0
            continue
        key = (eid, tid)
        if key not in last_ts or ts > last_ts[key]:
            last_ts[key] = ts
        is_even = (abs(eid) % 2 == 0)
        if etype == 1:
            if is_even:
                cnt = held_count.get(key, 0) + 1
                held_count[key] = cnt
                if cnt == 1:
                    held[key] = True
                    first_acq[key] = ts
            else:
                if held.get(key, False):
                    continue
                held[key] = True
                first_acq[key] = ts
                held_count[key] = 1
        else:
            if is_even:
                cnt = held_count.get(key, 0)
                if cnt == 0:
                    continue
                cnt -= 1
                held_count[key] = cnt
                if cnt == 0:
                    held[key] = False
                    first_acq[key] = None
            else:
                if not held.get(key, False):
                    continue
                held[key] = False
                first_acq[key] = None
                held_count[key] = 0
    total = 0
    for k, is_held in held.items():
        if is_held:
            f = first_acq.get(k)
            if f is not None:
                total += last_ts[k] - f
    print(total)
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(0)
    else:
        solve_one(sys.argv[1])
