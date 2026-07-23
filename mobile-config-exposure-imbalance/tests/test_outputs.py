"""Verify /app/solve.py reports the minimum rollout size that reaches the maximum
total exposure of an .mcfg config file, on HELD-OUT files the agent never saw.

Ground truth is recomputed here independently with a different max-flow
implementation (BFS Edmonds-Karp) than the solution, then the smallest optimal
rollout is read off the residual graph (configs reachable from the source). A
hardcoded constant or a value memorised from the sample cannot match several
different held-outs, and simply reporting the maximum exposure value (rather than
the minimum rollout size) is wrong.

The agent must parse the binary and solve this FROM SCRATCH: numpy/scipy/
networkx/igraph/pandas (which ship graph or max-flow routines) and shelling out
are rejected by test_from_scratch().
"""

import ast
import os
import re
import shutil
import struct
import subprocess
import tempfile
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

BANNED_MODULES = {
    "numpy",
    "scipy",
    "skimage",
    "cv2",
    "PIL",
    "Pillow",
    "networkx",
    "igraph",
    "imageio",
    "pandas",
    "torch",
    "tensorflow",
    "subprocess",
    "importlib",
    "runpy",
    "ctypes",
    "socket",
    "multiprocessing",
    "glob",
}
BANNED_CALLS = {"eval", "exec", "compile", "__import__"}
BANNED_TOKENS = [
    "/tests",
    "test_outputs",
    "heldout",
    "reference",
    "os.system",
    "os.popen",
    "os.exec",
    "os.walk",
    "os.listdir",
    "os.scandir",
    "pty.",
    "importlib",
    "runpy",
]


def _parse(path):
    d = open(path, "rb").read()
    assert d[:4] == b"MCFG", f"{path}: bad magic"
    cnt = struct.unpack_from("<I", d, 8)[0]
    off = struct.unpack_from("<I", d, 12)[0]
    o = off
    weight, deps = {}, {}
    for _ in range(cnt):
        nid, val, dc = struct.unpack_from("<iiI", d, o)
        o += 12
        ds = [struct.unpack_from("<I", d, o + 4 * i)[0] for i in range(dc)]
        o += 4 * dc
        weight[nid] = val
        deps[nid] = ds
    return weight, deps


def ref(path):
    """Independent ground truth: max-weight closure via BFS Edmonds-Karp, then the
    smallest optimal rollout = configs reachable from the source in the residual
    graph."""
    weight, deps = _parse(path)
    idx = {nid: i for i, nid in enumerate(weight)}
    N = len(weight)
    s, t = N, N + 1
    cap = [dict() for _ in range(N + 2)]

    def add(u, v, c):
        cap[u][v] = cap[u].get(v, 0) + c
        cap[v].setdefault(u, 0)

    INF = sum(abs(w) for w in weight.values()) + 1
    for nid, w in weight.items():
        if w > 0:
            add(s, idx[nid], w)
        elif w < 0:
            add(idx[nid], t, -w)
    for nid, ds in deps.items():
        for d in ds:
            if d in idx:
                add(idx[nid], idx[d], INF)

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
            u = par[v]
            f = min(f, cap[u][v])
            v = u
        v = t
        while v != s:
            u = par[v]
            cap[u][v] -= f
            cap[v][u] += f
            v = u

    seen = {s}
    q = deque([s])
    while q:
        u = q.popleft()
        for v, c in cap[u].items():
            if c > 0 and v not in seen:
                seen.add(v)
                q.append(v)
    return sum(1 for nid in weight if idx[nid] in seen)


def run(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    # Isolated copy under neutral name, temp cwd, so agent cannot identify held-out
    # or reach verifier files under /tests (also blocked statically)
    with tempfile.TemporaryDirectory() as td:
        neutral = os.path.join(td, "scan.mcfg")
        shutil.copyfile(path, neutral)
        o = subprocess.run(
            ["python3", SCRIPT, neutral],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=td,
        )
    assert o.returncode == 0, (
        f"script exited {o.returncode} on {path}\nstdout:\n{o.stdout}\nstderr:\n{o.stderr}"
    )
    toks = re.findall(r"-?\d+", o.stdout)
    assert toks, f"no numeric output on {path}: {o.stdout!r}"
    return int(toks[-1])


def test_exists():
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"


def test_from_scratch():
    src = open(SCRIPT).read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                top = a.name.split(".")[0]
                assert top not in BANNED_MODULES, f"banned module import: {a.name}"
                assert "test_output" not in a.name, "importing verifier is not allowed"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            top = mod.split(".")[0]
            assert top not in BANNED_MODULES, f"banned module import: {mod}"
            assert "test_output" not in mod, "importing verifier is not allowed"
        elif isinstance(node, ast.Call):
            fn = node.func
            name = (
                fn.id
                if isinstance(fn, ast.Name)
                else (fn.attr if isinstance(fn, ast.Attribute) else "")
            )
            assert name not in BANNED_CALLS, f"dynamic execution not allowed ({name})"
    compact = re.sub(r"\s+", "", src)
    for tok in BANNED_TOKENS:
        assert tok.replace(" ", "") not in compact, f"forbidden usage detected ({tok})"


@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    assert run(path) == ref(path)
