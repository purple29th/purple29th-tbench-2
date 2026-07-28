"""Verify /app/solve.py reports true capacity mAh for BCTR trace.
Ground truth is integral true capacity from generator stored in ground_truth.json.
"""

import ast
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

import pytest

SCRIPT = "/app/solve.py"
REL_TOL = 0.03
HELDOUTS = [
    "/tests/data/heldout_1.bctr",
    "/tests/data/heldout_2.bctr",
    "/tests/data/heldout_3.bctr",
    "/tests/data/heldout_4.bctr",
]

# True allowlist as per instruction: only struct, sys, collections are allowed.
# This addresses BAD_GRADING_WEAK: previously banlist allowed arbitrary imports.
ALLOWED_MODULES = {"struct", "sys", "collections"}

# Still explicitly ban risky modules even if allowlist would catch them, for clear errors.
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
    "pathlib",
    "shutil",
    "io",
    "pty",
    "os",
}

BANNED_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "getattr",
    "setattr",
    "hasattr",
    "globals",
    "locals",
    "vars",
    "dir",
    "chr",
    "ord",
    "breakpoint",
}
BANNED_TOKENS_FOR_PATH = [
    "/tests",
    "test_outputs",
    "heldout",
    "_gen",
    "reference",
    "ground_truth",
]
BANNED_OS_ATTRS = {
    "system",
    "popen",
    "exec",
    "walk",
    "listdir",
    "scandir",
    "open",
    "stat",
    "read",
    "fdopen",
    "path",
}
ALLOWED_DUNDER_ATTRS = {"__name__", "__main__"}


def ground_truth_cap(path):
    for base in ["/tests/data/ground_truth.json", "tests/data/ground_truth.json"]:
        if os.path.exists(base):
            gt = json.load(open(base))
            fname = os.path.basename(path)
            if fname in gt:
                return float(gt[fname])
    return 0.0


def parse_bctr_header(path):
    d = open(path, "rb").read()
    if d[:4] != b"BCTR":
        raise ValueError(f"bad magic {d[:4]} in {path}")
    total = struct.unpack_from("<I", d, 8)[0]
    off = struct.unpack_from("<I", d, 12)[0]
    interval = struct.unpack_from("<f", d, 16)[0]
    gain = struct.unpack_from("<f", d, 20)[0]
    baseline = struct.unpack_from("<I", d, 24)[0]
    return {
        "total": total,
        "offset": off,
        "interval": float(interval),
        "gain": float(gain),
        "baseline": baseline,
    }


def run_agent(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    with tempfile.TemporaryDirectory() as td:
        neutral = os.path.join(td, "scan.bctr")
        shutil.copyfile(path, neutral)
        iso = os.path.join(td, "solve.py")
        shutil.copyfile(SCRIPT, iso)
        env = os.environ.copy()
        env["PYTHONPATH"] = td
        proc = subprocess.run(
            [sys.executable, iso, neutral],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=td,
            env=env,
        )
    assert proc.returncode == 0, (
        f"exit {proc.returncode} on {path}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines, f"no stdout on {path}"
    last = lines[-1]
    m = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", last)
    assert m, f"no numeric cap on last line: {last!r}"
    return float(m[-1])


def test_script_exists():
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
                except Exception:
                    continue
        if isinstance(node, ast.JoinedStr):
            for part in node.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    yield part.value


def test_from_scratch():
    src = open(SCRIPT, "r", encoding="utf-8", errors="ignore").read()
    tree = ast.parse(src, filename=SCRIPT)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mod_root = a.name.split(".")[0]
                # Enforce true allowlist: only struct, sys, collections permitted
                assert mod_root in ALLOWED_MODULES, (
                    f"import {a.name} not allowed; allowed={ALLOWED_MODULES}"
                )
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            mod_root = mod.split(".")[0]
            assert mod_root in ALLOWED_MODULES, (
                f"import from {mod} not allowed; allowed={ALLOWED_MODULES}"
            )
        elif isinstance(node, ast.Call):
            fn = node.func
            name = (
                fn.id
                if isinstance(fn, ast.Name)
                else (fn.attr if isinstance(fn, ast.Attribute) else "")
            )
            assert name not in BANNED_CALLS, f"dynamic call not allowed ({name})"
        elif isinstance(node, ast.Attribute):
            attr = node.attr
            if (
                attr.startswith("__")
                and attr.endswith("__")
                and attr not in ALLOWED_DUNDER_ATTRS
            ):
                if attr in {
                    "__dict__",
                    "__subclasses__",
                    "__mro__",
                    "__bases__",
                    "__code__",
                    "__globals__",
                    "__builtins__",
                }:
                    assert False, f"dunder not allowed ({attr})"
            if isinstance(node.value, ast.Name) and node.value.id == "os":
                assert attr not in BANNED_OS_ATTRS, f"banned os.{attr} usage"
    for lit in _iter_string_literals(tree):
        low = lit.lower()
        for banned in BANNED_TOKENS_FOR_PATH:
            assert banned.lower() not in low, f"forbidden path {banned!r} in {lit!r}"


def test_heldout_headers_varied():
    """R06 coverage: ensure heldouts actually vary offset and interval and gain.
    Fails if generator forgot to vary them (previous bug: all intervals 0.5, gain 1.0)."""
    intervals = set()
    offsets = set()
    gains = set()
    found = 0
    for p in HELDOUTS:
        alt = p.replace("/tests/data/", "tests/data/")
        real_path = p if os.path.exists(p) else alt
        if not os.path.exists(real_path):
            continue
        hdr = parse_bctr_header(real_path)
        intervals.add(round(hdr["interval"], 3))
        offsets.add(hdr["offset"])
        gains.add(round(hdr["gain"], 3))
        found += 1
    # Only enforce if we found at least 2 files (local run may have only some)
    if found >= 2:
        assert len(offsets) >= 2, f"heldout offsets not varied: {offsets}"
        assert len(intervals) >= 2, (
            f"heldout intervals not varied (all 0.5 before fix): {intervals}"
        )
        assert len(gains) >= 2, f"heldout gains not varied: {gains}"


def test_sample_header_gain_disambig():
    """Ensure sample file gain != 1.0 to disambiguate multiply vs divide.
    This addresses human review medium-low: sample with gain=1.0 hides direction."""
    candidates = [
        "/app/data/scene.bctr",
        "/tests/data/scene.bctr",
        "tests/data/scene.bctr",
        "environment/data/scene.bctr",
    ]
    path = None
    for c in candidates:
        if os.path.exists(c):
            path = c
            break
    if path is None:
        pytest.skip("scene.bctr not found locally")
    hdr = parse_bctr_header(path)
    # Sample should have gain !=1.0 after fix (e.g., 0.95) and interval 0.5
    assert abs(hdr["gain"] - 1.0) > 0.01, (
        f"sample gain {hdr['gain']} is 1.0, ambiguous for multiply/divide"
    )
    assert hdr["offset"] >= 28, f"offset too small: {hdr['offset']}"
    assert hdr["interval"] > 0, "interval must be positive"


def test_sample_runs():
    """Sample-scene assertion: run solver on scene.bctr to catch format drift.
    New after fix: scene gain is 0.95 to disambiguate multiply vs divide."""
    candidates = [
        "/app/data/scene.bctr",
        "/tests/data/scene.bctr",
        "tests/data/scene.bctr",
        "environment/data/scene.bctr",
    ]
    path = None
    for c in candidates:
        if os.path.exists(c):
            path = c
            break
    if path is None:
        pytest.skip("scene.bctr not found")
    got = run_agent(path)
    # Plausible range for battery capacity: 400-1500 mAh after fix (was 943)
    assert 300 < got < 2000, f"sample capacity {got} out of plausible range 300-2000"
    # Strict check for scene: expected about 896 mAh with gain 0.95
    expected = ground_truth_cap(path)
    if expected == 0.0:
        # Fallback hardcoded expected when ground_truth.json has no scene entry
        # 49.2*1380/10*0.5*0.95/3.6 = 895.85
        expected = 895.85
    assert abs(got - expected) <= REL_TOL * expected, (
        f"scene: got {got:.2f} expected {expected:.2f} +- {REL_TOL:.0%}"
    )


@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    got = run_agent(path)
    expected = ground_truth_cap(path)
    # If ground truth missing (local dev without /tests), skip strict check but still ensure run succeeded
    if expected == 0.0:
        pytest.skip(f"ground truth missing for {path}")
    assert abs(got - expected) <= REL_TOL * expected, (
        f"{os.path.basename(path)}: got {got:.2f} expected {expected:.2f} +- {REL_TOL:.0%}"
    )
