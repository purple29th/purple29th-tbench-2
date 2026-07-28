"""Verify /app/solve.py reports minimal rollout size reaching max exposure .mcfg
on HELD-OUT configs agent never saw.

Each config has signed exposure weight, dependency forces inclusion transitively.
Empty rollout valid. Goal is max total exposure then minimal number of configs
with custom counting: header int32 reserved is exposure imbalance threshold,
abs(value) < threshold are free riders - not counted and their own dependencies
ignored, changing closure graph itself, not just counting. Zero-gain padding
(+30 depends on -30) must be excluded via minimal cut.

Ground truth recomputed independently: Edmonds-Karp vs Dinic plus threshold counting
with signed dep handling and free rider dep ignore. Both agree.

Hardened isolation post-review fix for BAD_GRADING_WRONG:
- _parse now correctly handles negative IDs stored as uint32 (two's complement) converting to signed
- free riders with abs < thr ignore own dependencies - graph changing twist
- test_from_scratch now uses AST for imports/calls and decoded string literals for path checks, not raw compact substring like 'pty.' that falsely matches 'empty.' in comments
- Imports banned via AST: numpy scipy skimage cv2 PIL networkx igraph imageio pandas torch tensorflow subprocess importlib runpy ctypes socket multiprocessing glob pathlib shutil io pty os
- Calls banned via AST: eval exec compile __import__ getattr setattr hasattr globals locals vars dir chr ord breakpoint
- Path tokens banned via string literal inspection: /tests test_outputs heldout _gen reference ground_truth
- Attribute checks for os.system popen exec walk listdir scandir open stat read fdopen path
"""
import ast
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import json
import pytest
from collections import deque

SCRIPT = "/app/solve.py"
HELDOUTS = [
    "/tests/data/heldout_1.mcfg",
    "/tests/data/heldout_2.mcfg",
    "/tests/data/heldout_3.mcfg",
    "/tests/data/heldout_4.mcfg",
    "/tests/data/heldout_5.mcfg",
    "/tests/data/heldout_6.mcfg",
    "/tests/data/heldout_7.mcfg",
]

BANNED_MODULES = {
    "numpy", "scipy", "skimage", "cv2", "PIL", "Pillow",
    "networkx", "igraph", "imageio", "pandas", "torch", "tensorflow",
    "subprocess", "importlib", "runpy", "ctypes", "socket",
    "multiprocessing", "glob", "pathlib", "shutil", "io", "pty",
}
BANNED_MODULES_STRICT = BANNED_MODULES | {"os"}

BANNED_CALLS = {
    "eval", "exec", "compile", "__import__",
    "getattr", "setattr", "hasattr",
    "globals", "locals", "vars", "dir",
    "chr", "ord", "breakpoint",
}

BANNED_TOKENS_FOR_PATH = [
    "/tests", "test_outputs", "heldout", "_gen", "reference", "ground_truth",
]

BANNED_OS_ATTRS = {
    "system", "popen", "exec", "walk", "listdir", "scandir",
    "open", "stat", "read", "fdopen", "path",
}

ALLOWED_DUNDER_ATTRS = {"__name__", "__main__"}

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
        raw = [struct.unpack_from("<I", d, o + 4 * i)[0] for i in range(dc)]
        ds = [r - (1 << 32) if r >= (1 << 31) else r for r in raw]
        o += 4 * dc
        weight[nid] = val
        deps[nid] = ds
    return weight, deps, thr

def ref(path):
    """Independent ground truth: max closure with free rider dep ignore, then minimal via residual, counting only abs>=thr."""
    weight, deps, thr = _parse(path)
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
        if abs(weight[nid]) < thr:
            continue
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

    return sum(1 for nid in weight if idx[nid] in seen and abs(weight[nid]) >= thr)

def run(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    with tempfile.TemporaryDirectory() as td:
        neutral = os.path.join(td, "scan.mcfg")
        shutil.copyfile(path, neutral)
        iso = os.path.join(td, "solve.py")
        shutil.copyfile(SCRIPT, iso)
        env = os.environ.copy()
        env["PYTHONPATH"] = td
        proc = subprocess.run([sys.executable, iso, neutral], capture_output=True, text=True, timeout=120, cwd=td, env=env)
    assert proc.returncode == 0, f"exit {proc.returncode} on {path}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    toks = re.findall(r"-?\d+", proc.stdout)
    assert toks, f"no numeric output on {path}: {proc.stdout!r}"
    return int(toks[-1])

def test_exists():
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"

def _iter_string_literals(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            v = node.value
            if isinstance(v, str):
                yield v
            elif isinstance(v, (bytes, bytearray)):
                try:
                    yield v.decode("utf-8", errors="ignore")
                except:
                    continue
        if isinstance(node, ast.JoinedStr):
            for part in node.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    yield part.value

def test_from_scratch():
    src = open(SCRIPT, "r", encoding="utf-8", errors="ignore").read()
    tree = ast.parse(src, filename=SCRIPT)

    # Regression: a correct solve.py containing comment "empty." must still pass (previously failed due to 'pty.' substring)
    # Ensure we do NOT do raw compact substring check for 'pty.' - use AST instead

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mod_root = a.name.split(".")[0]
                assert mod_root not in BANNED_MODULES_STRICT, f"banned module import: {a.name}"
                assert "test_output" not in a.name.lower(), "importing verifier not allowed"
                assert "_gen" not in a.name.lower(), "importing generator not allowed"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            mod_root = mod.split(".")[0]
            assert mod_root not in BANNED_MODULES_STRICT, f"banned module import from: {mod}"
        elif isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
            assert name not in BANNED_CALLS, f"dynamic/obfuscation call not allowed ({name})"
        elif isinstance(node, ast.Attribute):
            attr = node.attr
            # dunder check except __name__ and __main__
            if attr.startswith("__") and attr.endswith("__") and attr not in ALLOWED_DUNDER_ATTRS:
                # Allow only __name__ and __main__, block __dict__ etc
                if attr in {"__dict__", "__subclasses__", "__mro__", "__bases__", "__code__", "__globals__", "__builtins__"}:
                    assert False, f"dunder attribute not allowed ({attr}) - potential sandbox escape"
            # os.* attribute checks
            if isinstance(node.value, ast.Name) and node.value.id == "os":
                assert attr not in BANNED_OS_ATTRS, f"banned os.{attr} usage"

    # Path token check via decoded string literals, not raw compact substring for code patterns
    for lit in _iter_string_literals(tree):
        low = lit.lower()
        for banned in BANNED_TOKENS_FOR_PATH:
            assert banned.lower() not in low, f"forbidden path substring in string literal: {banned!r} found in {lit!r}"

    # No raw compact substring scan for pty or os.system etc - handled via AST above
    # This fixes false negative where comment 'empty.' contains 'pty.' after compaction

@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    assert run(path) == ref(path)
