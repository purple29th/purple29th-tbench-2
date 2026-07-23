"""Verify /app/solve.py recovers the total true number of events from a dead-time
limited counter log, on HELD-OUT files the agent never saw.

Ground truth is recomputed here independently (pure standard library, a different
algebraic form than a typical solution) by inverting the non-paralyzable dead-time
relation per bin and summing. Simply summing the recorded counts undercounts the
truth badly at high rates, so a naive or memorised-constant answer cannot match
several different held-outs (dt and tau vary per file).

The agent must parse the binary and do the recovery FROM SCRATCH: numpy/scipy/
imaging/graph libraries, dynamic execution, and shelling out or reading the
verifier / held-out data are rejected by test_from_scratch().
"""
import ast
import os
import re
import shutil
import struct
import subprocess
import tempfile

import pytest

SCRIPT = "/app/solve.py"
REL_TOL = 0.02
HELDOUTS = [
    "/tests/data/heldout_1.flux",
    "/tests/data/heldout_2.flux",
    "/tests/data/heldout_3.flux",
]

BANNED_MODULES = {
    "numpy", "scipy", "skimage", "cv2", "PIL", "Pillow",
    "networkx", "igraph", "imageio", "pandas", "torch", "tensorflow",
    "subprocess", "importlib", "runpy", "ctypes", "socket",
    "multiprocessing", "glob",
}
BANNED_CALLS = {"eval", "exec", "compile", "__import__"}
BANNED_TOKENS = [
    "/tests", "test_outputs", "heldout",
    "os.system", "os.popen", "os.exec", "os.walk", "os.listdir", "os.scandir",
    "pty.", "importlib", "runpy",
]


def _parse(path):
    d = open(path, "rb").read()
    assert d[:4] == b"FLUX", f"{path}: bad magic"
    dtype = struct.unpack_from("<I", d, 8)[0]
    nbins = struct.unpack_from("<I", d, 12)[0]
    dt = struct.unpack_from("<f", d, 16)[0]
    tau = struct.unpack_from("<f", d, 20)[0]
    off = struct.unpack_from("<I", d, 24)[0]
    fmt = {2: "<%dH", 4: "<%dI"}[dtype] % nbins
    counts = list(struct.unpack_from(fmt, d, off))
    return counts, float(dt), float(tau)


def reference_total(path):
    """Independent ground truth: invert the dead-time relation per bin. Written in
    the algebraically-equivalent form true = M*dt / (dt - M*tau)."""
    counts, dt, tau = _parse(path)
    total = 0.0
    for M in counts:
        denom = dt - M * tau
        if denom <= 0:
            denom = 1e-12
        total += (M * dt) / denom
    return round(total)


def run_agent(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    # Run the agent script on an isolated copy under a neutral name, from a temp
    # cwd: it receives only the input path and cannot identify the held-out or
    # reach the mounted verifier / held-out data under /tests.
    with tempfile.TemporaryDirectory() as td:
        neutral = os.path.join(td, "log.flux")
        shutil.copyfile(path, neutral)
        proc = subprocess.run(["python3", SCRIPT, neutral],
                              capture_output=True, text=True, timeout=120, cwd=td)
    assert proc.returncode == 0, (
        f"script exited {proc.returncode} on {path}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
    toks = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", proc.stdout)
    assert toks, f"no numeric output on {path}: {proc.stdout!r}"
    return float(toks[-1])


def test_script_exists():
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"


def test_from_scratch():
    """AST import/exec audit plus a token scan that blocks reading the verifier or
    held-out data and shelling out."""
    src = open(SCRIPT).read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in BANNED_MODULES, f"banned module: {a.name}"
                assert "test_output" not in a.name, "importing the verifier is not allowed"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert mod.split(".")[0] not in BANNED_MODULES, f"banned module: {mod}"
            assert "test_output" not in mod, "importing the verifier is not allowed"
        elif isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
            assert name not in BANNED_CALLS, f"dynamic execution is not allowed ({name})"
    compact = re.sub(r"\s+", "", src)
    for tok in BANNED_TOKENS:
        assert tok.replace(" ", "") not in compact, f"forbidden usage detected ({tok})"


@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    got = run_agent(path)
    expected = reference_total(path)
    assert abs(got - expected) <= REL_TOL * expected, (
        f"{os.path.basename(path)}: got {got:.1f}, expected {expected} (+/- {REL_TOL:.0%})")
