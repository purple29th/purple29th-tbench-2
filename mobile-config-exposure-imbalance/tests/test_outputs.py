"""Verify /app/solve.py reports the maximum-weight dependency closure of an .mcfg
config file, on HELD-OUT files the agent never saw.

Ground truth is recomputed here independently with a different max-flow
implementation (BFS Edmonds-Karp) than the solution, so a hardcoded constant or a
value memorised from the sample cannot match several different held-outs. The
agent must parse the binary and solve the closure/min-cut FROM SCRATCH:
numpy/scipy/networkx/igraph/pandas (which ship graph or max-flow routines) and
shelling out are rejected by test_from_scratch().
"""
import os
import re
import struct
import subprocess
from collections import deque

import pytest

SCRIPT = "/app/solve.py"
HELDOUTS = [
    "/tests/data/heldout_1.mcfg",
    "/tests/data/heldout_2.mcfg",
    "/tests/data/heldout_3.mcfg",
    "/tests/data/heldout_4.mcfg",
    "/tests/data/heldout_5.mcfg",
]


def _parse(path):
    d = open(path, "rb").read()
    assert d[:4] == b"MCFG", f"{path}: bad magic"
    cnt = struct.unpack_from("<I", d, 8)[0]
    off = struct.unpack_from("<I", d, 12)[0]
    thr = struct.unpack_from("<i", d, 16)[0]
    o = off
    weight, deps = {}, {}
    for _ in range(cnt):
        nid, val, dc = struct.unpack_from("<iiI", d, o)
        o += 12
        ds = [struct.unpack_from("<I", d, o + 4 * i)[0] for i in range(dc)]
        o += 4 * dc
        weight[nid] = val
        deps[nid] = ds
    return weight, deps, thr


def ref(path):
    """Independent ground truth: maximum-weight closure via BFS Edmonds-Karp
    max-flow (answer = sum(positive) - min_st_cut), floored at the threshold."""
    weight, deps, thr = _parse(path)
    idx = {nid: i for i, nid in enumerate(weight)}
    N = len(weight)
    s, t = N, N + 1
    cap = [dict() for _ in range(N + 2)]

    def add(u, v, c):
        cap[u][v] = cap[u].get(v, 0) + c
        cap[v].setdefault(u, 0)

    INF = sum(abs(w) for w in weight.values()) + 1
    pos = 0
    for nid, w in weight.items():
        if w > 0:
            add(s, idx[nid], w); pos += w
        elif w < 0:
            add(idx[nid], t, -w)
    for nid, ds in deps.items():
        for d in ds:
            if d in idx:
                add(idx[nid], idx[d], INF)

    flow = 0
    while True:
        par = {s: s}
        q = deque([s])
        while q:
            u = q.popleft()
            if u == t:
                break
            for v, c in cap[u].items():
                if c > 0 and v not in par:
                    par[v] = u
                    q.append(v)
        if t not in par:
            break
        f = INF * 10
        v = t
        while v != s:
            u = par[v]; f = min(f, cap[u][v]); v = u
        v = t
        while v != s:
            u = par[v]; cap[u][v] -= f; cap[v][u] += f; v = u
        flow += f
    best = pos - flow
    return best if best >= thr else 0


def run(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    o = subprocess.run(["python3", SCRIPT, path],
                       capture_output=True, text=True, timeout=120)
    assert o.returncode == 0, (
        f"script exited {o.returncode} on {path}\nstdout:\n{o.stdout}\nstderr:\n{o.stderr}")
    toks = re.findall(r"-?\d+", o.stdout)
    assert toks, f"no numeric output on {path}: {o.stdout!r}"
    return int(toks[-1])


def test_exists():
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"


def test_from_scratch():
    s = open(SCRIPT).read().replace(" ", "").lower()
    for b in [
        "importnumpy", "fromnumpy", "importscipy", "fromscipy",
        "importnetworkx", "fromnetworkx", "importigraph", "fromigraph",
        "importpandas", "frompandas",
        "subprocess.", "os.system", "os.popen", "__import__(", "importlib",
        "eval(", "exec(",
    ]:
        assert b not in s, f"banned usage detected: {b}"


@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    assert run(path) == ref(path)
