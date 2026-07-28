#!/usr/bin/env python3
"""Oracle for android-wakelock-imbalance: total leaked duration via counting."""
import struct, sys
from collections import defaultdict

def parse(path):
    d=open(path,"rb").read()
    if d[:4]!=b"WKLK":
        raise ValueError(f"bad magic {d[:4]}")
    total=struct.unpack_from("<I",d,8)[0]
    off=struct.unpack_from("<I",d,12)[0]
    events=[]
    o=off
    for _ in range(total):
        if o+16>len(d):
            break
        eid,etype,ts,tid=struct.unpack_from("<iIII",d,o)
        o+=16
        events.append((eid,etype,ts,tid))
    return events

def solve_one(path):
    events=parse(path)
    # per id tracking
    acq_times=defaultdict(list)
    rel_times=defaultdict(list)
    last_ts=defaultdict(int)
    first_acq=defaultdict(lambda: None)
    # events already sorted by timestamp from generator, but we should handle any order
    # We'll process as we go, tracking first acquire as earliest acquire timestamp
    for eid,etype,ts,tid in events:
        # track last timestamp overall per id
        if last_ts[eid]==0 or ts>last_ts[eid]:
            last_ts[eid]=ts
        if etype==1:  # acquire
            acq_times[eid].append(ts)
            if first_acq[eid] is None or ts < first_acq[eid]:
                first_acq[eid]=ts
        else:  # release
            rel_times[eid].append(ts)
    total_leaked=0
    for eid in acq_times:
        acq=len(acq_times[eid])
        rel=len(rel_times.get(eid,[]))
        if acq>rel:
            # leaked duration = last timestamp - first acquire
            last=last_ts.get(eid, 0)
            first=first_acq.get(eid)
            if first is not None:
                total_leaked+= (last - first)
    # Also need to consider ids that have only releases? Spec says release without acquire ignored
    print(total_leaked)

if __name__=="__main__":
    if len(sys.argv)<2:
        print(0)
    else:
        solve_one(sys.argv[1])
