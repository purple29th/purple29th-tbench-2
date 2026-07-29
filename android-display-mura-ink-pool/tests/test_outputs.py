"""Verify /app/solve.py reports count of touch cells .cdmr map on HELD-OUT scans.

Ground truth is geometric true count = integral of fractional occupancy rounded.
Occupancy: interior fully filled 1.0, border partial, bleed lines partial.
Sum rounded = true count, equivalent to total conserved charge / plateau.
Grading uses true count from ground_truth.json with tolerance max(2, 3% of expected).
Dust blobs are far, many, with significant total charge and may be brighter or larger area than main.
Off-center pools near edge test center assumption. Data offset varies 64-128.

Hardened isolation: _gen.py not mounted, solve.py executed in isolated
TemporaryDirectory with neutral copy, bans many modules and tokens.
Enforces mass-based selection and halo growth via shortcut-failure tests.
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
from collections import deque

import pytest

SCRIPT = "/app/solve.py"
HELDOUTS = [
    "/tests/data/heldout_1.cdmr",
    "/tests/data/heldout_2.cdmr",
    "/tests/data/heldout_3.cdmr",
    "/tests/data/heldout_4.cdmr",
    "/tests/data/heldout_5.cdmr",
    "/tests/data/heldout_6.cdmr",
    "/tests/data/heldout_7.cdmr",
    "/tests/data/heldout_8.cdmr",
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
    "pathlib",
    "shutil",
    "io",
    "pty",
}
BANNED_MODULES_STRICT = BANNED_MODULES | {"os"}
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
BANNED_SUBSTRINGS_IN_STRLITS = [
    "/tests",
    "tests/data",
    "heldout",
    "_gen",
    "test_output",
    "test_outputs",
]
ALLOWED_DUNDER_ATTRS = {"__name__", "__main__"}

NEIGH = [
    (dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if not (dx == 0 and dy == 0)
]


def _parse(path):
    d = open(path, "rb").read()
    assert d[:4] == b"CDMR", f"{path}: bad magic {d[:4]}"
    off = struct.unpack_from("<I", d, 12)[0]
    nx, ny = struct.unpack_from("<II", d, 28)
    n = nx * ny
    fmt = "<%dh" % n
    vals = [float(v) for v in struct.unpack_from(fmt, d, off)]
    return nx, ny, vals


def _median_sorted(s):
    m = len(s)
    if m == 0:
        return 0.0
    return s[m // 2] if m % 2 else 0.5 * (s[m // 2 - 1] + s[m // 2])


def ground_truth_count(path):
    for base in ["/tests/data/ground_truth.json", "tests/data/ground_truth.json"]:
        if os.path.exists(base):
            gt = json.load(open(base))
            fname = os.path.basename(path)
            if fname in gt:
                return int(gt[fname])
    return reference_count(path)


def reference_count(path):
    """
    Fallback estimator when ground_truth.json missing.
    Independent implementation using deque BFS (vs stack in oracle) but same
    charge-conservation logic. Primary grading uses geometric truth from json,
    so this is backup for sample. Matches true within 3% on all heldouts.
    Distinct from solution/solve.py in data structures and naming but similar constants
    (4 sigma, 50 halo iters, 1 sigma shell, top-8 median) because those are physics-based.
    """
    nx, ny, vals = _parse(path)
    n = nx * ny

    def idx(x, y):
        return x + nx * y

    sorted_vals = sorted(vals)
    bg = _median_sorted(sorted_vals)

    low_half = sorted_vals[: n // 2]
    med_low = _median_sorted(low_half)
    mad = _median_sorted(sorted(abs(v - med_low) for v in low_half))
    noise_sigma = max(1e-6, 1.4826 * mad)

    residual = [v - bg for v in vals]
    thr = 4.0 * noise_sigma
    occupied = [r > thr for r in residual]

    seen = bytearray(n)
    best_mass = -1.0
    best_comp = None

    for y0 in range(ny):
        for x0 in range(nx):
            s = idx(x0, y0)
            if not occupied[s] or seen[s]:
                continue
            q = deque()
            q.append((x0, y0))
            seen[s] = 1
            comp = []
            mass = 0.0
            while q:
                x, y = q.popleft()
                cur = idx(x, y)
                comp.append(cur)
                mass += residual[cur]
                for dx, dy in NEIGH:
                    ax = x + dx
                    by = y + dy
                    if 0 <= ax < nx and 0 <= by < ny:
                        k = idx(ax, by)
                        if occupied[k] and not seen[k]:
                            seen[k] = 1
                            q.append((ax, by))
            if mass > best_mass:
                best_mass = mass
                best_comp = comp

    if not best_comp:
        return 0

    smoothed = []
    for j in best_comp:
        x = j % nx
        y = j // nx
        acc = 0.0
        cnt = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                a = min(max(x + dx, 0), nx - 1)
                b = min(max(y + dy, 0), ny - 1)
                acc += residual[idx(a, b)]
                cnt += 1
        smoothed.append(acc / cnt)
    smoothed.sort(reverse=True)
    top = smoothed[: max(1, min(8, len(smoothed)))]
    amp = _median_sorted(sorted(top))
    if amp <= 0:
        return 0

    region = set(best_comp)
    frontier = set(best_comp)
    for _ in range(50):
        shell = set()
        for j in frontier:
            x = j % nx
            y = j // nx
            for dx, dy in NEIGH:
                a = x + dx
                b = y + dy
                if 0 <= a < nx and 0 <= b < ny:
                    k = idx(a, b)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        mean_shell = sum(residual[j] for j in shell) / len(shell) if shell else 0.0
        if mean_shell <= 1.0 * noise_sigma:
            break
        region |= shell
        frontier = shell

    total = sum(residual[j] for j in region)
    return int(round(total / amp))


def run_agent(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    with tempfile.TemporaryDirectory() as td:
        neutral = os.path.join(td, "scan.cdmr")
        shutil.copyfile(path, neutral)
        isolated_script = os.path.join(td, "solve.py")
        shutil.copyfile(SCRIPT, isolated_script)
        env = os.environ.copy()
        env["PYTHONPATH"] = td
        proc = subprocess.run(
            [sys.executable, isolated_script, neutral],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=td,
            env=env,
        )
    assert proc.returncode == 0, (
        f"exit {proc.returncode} on {path}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines, f"no stdout on {path}"
    last = lines[-1]
    m = re.findall(r"-?\d+", last)
    assert m, f"no numeric count on last line: {last!r}"
    return int(m[-1])


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
                assert mod_root not in BANNED_MODULES_STRICT, (
                    f"banned module import: {a.name}"
                )
                assert "test_output" not in a.name.lower(), (
                    "importing verifier not allowed"
                )
                assert "_gen" not in a.name.lower(), "importing generator not allowed"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            mod_root = mod.split(".")[0]
            assert mod_root not in BANNED_MODULES_STRICT, (
                f"banned module import from: {mod}"
            )
            assert "test_output" not in mod.lower(), "importing verifier not allowed"
            assert "_gen" not in mod.lower(), "importing generator not allowed"
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
                    assert False, f"dunder attribute not allowed ({attr})"
            if isinstance(node.value, ast.Name) and node.value.id == "os":
                assert attr not in BANNED_OS_ATTRS, f"banned os.{attr} usage"
    for lit in _iter_string_literals(tree):
        low = lit.lower()
        for banned in BANNED_SUBSTRINGS_IN_STRLITS:
            assert banned.lower() not in low, f"forbidden path {banned!r} in {lit!r}"
        for banned in BANNED_TOKENS_FOR_PATH:
            assert banned.lower() not in low, (
                f"forbidden path substring in string literal: {banned!r} found in {lit!r}"
            )


@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    got = run_agent(path)
    expected = ground_truth_count(path)
    tol = max(2, int(0.03 * expected))
    assert abs(got - expected) <= tol, (
        f"{os.path.basename(path)}: got {got} expected {expected} +- {tol}"
    )


def test_data_offset_varied():
    offsets = set()
    for p in HELDOUTS:
        data = open(p, "rb").read()
        off = struct.unpack_from("<I", data, 12)[0]
        offsets.add(off)
    # at least 2 distinct offsets, and at least one !=64 to catch hardcoding
    assert len(offsets) > 1, f"expected varied data_offset, got only {offsets}"
    assert any(o != 64 for o in offsets), "need at least one non-64 offset"


def _shortcut_estimate(path, use_area=False, use_halo=True):
    """Reference shortcut estimators for grading coverage checks"""
    nx, ny, vals = _parse(path)
    n = nx * ny

    def idx(x, y):
        return x + nx * y

    sorted_vals = sorted(vals)
    bg = _median_sorted(sorted_vals)
    low_half = sorted_vals[: n // 2]
    med_low = _median_sorted(low_half)
    mad = _median_sorted(sorted(abs(v - med_low) for v in low_half))
    noise_sigma = max(1e-6, 1.4826 * mad)
    residual = [v - bg for v in vals]
    thr = 4.0 * noise_sigma
    occupied = [r > thr for r in residual]
    seen = bytearray(n)
    comps = []
    for y0 in range(ny):
        for x0 in range(nx):
            s = idx(x0, y0)
            if not occupied[s] or seen[s]:
                continue
            q = deque()
            q.append((x0, y0))
            seen[s] = 1
            comp = []
            mass = 0.0
            while q:
                x, y = q.popleft()
                cur = idx(x, y)
                comp.append(cur)
                mass += residual[cur]
                for dx, dy in NEIGH:
                    ax = x + dx
                    by = y + dy
                    if 0 <= ax < nx and 0 <= by < ny:
                        k = idx(ax, by)
                        if occupied[k] and not seen[k]:
                            seen[k] = 1
                            q.append((ax, by))
            comps.append((comp, mass, len(comp)))
    if not comps:
        return 0
    if use_area:
        best = max(comps, key=lambda x: x[2])
    else:
        best = max(comps, key=lambda x: x[1])
    best_comp = best[0]
    smoothed = []
    for j in best_comp:
        x = j % nx
        y = j // nx
        acc = 0.0
        cnt = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                a = min(max(x + dx, 0), nx - 1)
                b = min(max(y + dy, 0), ny - 1)
                acc += residual[idx(a, b)]
                cnt += 1
        smoothed.append(acc / cnt)
    smoothed.sort(reverse=True)
    top = smoothed[: max(1, min(8, len(smoothed)))]
    amp = _median_sorted(sorted(top))
    if amp <= 0:
        return 0
    if not use_halo:
        total = sum(residual[j] for j in best_comp)
        return int(round(total / amp))
    region = set(best_comp)
    frontier = set(best_comp)
    for _ in range(50):
        shell = set()
        for j in frontier:
            x = j % nx
            y = j // nx
            for dx, dy in NEIGH:
                a = x + dx
                b = y + dy
                if 0 <= a < nx and 0 <= b < ny:
                    k = idx(a, b)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        mean_shell = sum(residual[j] for j in shell) / len(shell) if shell else 0.0
        if mean_shell <= 1.0 * noise_sigma:
            break
        region |= shell
        frontier = shell
    total = sum(residual[j] for j in region)
    return int(round(total / amp))


def test_mass_selection_required():
    """Area-based component selection should fail on at least one heldout (mass vs area)"""
    fails = 0
    for p in HELDOUTS:
        exp = ground_truth_count(p)
        tol = max(2, int(0.03 * exp))
        got_area = _shortcut_estimate(p, use_area=True, use_halo=True)
        if abs(got_area - exp) > tol:
            fails += 1
    assert fails >= 1, (
        "expected at least one heldout where area-selection fails, need large-area dust case"
    )


def test_halo_growth_required():
    """Skipping halo growth should fail on at least one heldout"""
    fails = 0
    for p in HELDOUTS:
        exp = ground_truth_count(p)
        tol = max(2, int(0.03 * exp))
        got_nohalo = _shortcut_estimate(p, use_area=False, use_halo=False)
        if abs(got_nohalo - exp) > tol:
            fails += 1
    assert fails >= 1, (
        "expected at least one heldout where no-halo shortcut fails, need large PSF + bleed case"
    )


def test_global_sum_fails():
    """Naive global sum of positive excess should fail on heavy dust"""
    fails = 0
    for p in HELDOUTS:
        nx, ny, vals = _parse(p)
        sorted_vals = sorted(vals)
        bg = _median_sorted(sorted_vals)
        residual = [v - bg for v in vals]
        pos_sum = sum(r for r in residual if r > 0)
        # estimate amp via global top median
        resid_sorted = sorted(residual, reverse=True)
        top = resid_sorted[:8]
        amp = _median_sorted(sorted(top)) if top else 1
        got = int(round(pos_sum / amp)) if amp > 0 else 0
        exp = ground_truth_count(p)
        tol = max(2, int(0.03 * exp))
        if abs(got - exp) > tol:
            fails += 1
    assert fails >= 2, "expected global sum to fail on at least 2 heavy dust maps"
