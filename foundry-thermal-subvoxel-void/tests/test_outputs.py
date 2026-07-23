"""Verify /app/solve.py reports mm^3 void volume in a .tiv thermal IR volume.

Thermal diffusion plus lens PSF spreads trapped heat but conserves total energy.
True void volume NOT recoverable by thresholding (thin cracks partial-volume).
IS recoverable by intensity conservation vs geometric ground truth from _gen.py.

Verifier uses generator's geometric voxel count for known held-outs (independent
of oracle), with stdlib-only fallback for arbitrary scans. No numpy/scipy needed.
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
REL_TOL = 0.03
HELDOUTS = [
    "/tests/data/heldout_1.tiv",
    "/tests/data/heldout_2.tiv",
    "/tests/data/heldout_3.tiv",
]

GEOM_TRUTH_MM3 = {
    "scene.tiv": 2459.968,
    "heldout_1.tiv": 3350.646,
    "heldout_2.tiv": 3423.2,
    "heldout_3.tiv": 3729.852,
}

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
    "reference_volume",
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


def _median_sorted(sv):
    m = len(sv)
    return sv[m // 2] if m % 2 else 0.5 * (sv[m // 2 - 1] + sv[m // 2])


NEIGH26 = [
    (dx, dy, dz)
    for dz in (-1, 0, 1)
    for dy in (-1, 0, 1)
    for dx in (-1, 0, 1)
    if dx or dy or dz
]


def _parse_tiv(path):
    raw = open(path, "rb").read()
    assert raw[:4] == b"TIVR", f"{path}: bad magic"
    dtype = struct.unpack_from("<I", raw, 8)[0]
    nx, ny, nz = struct.unpack_from("<III", raw, 12)
    sx, sy, sz = struct.unpack_from("<fff", raw, 24)
    off = struct.unpack_from("<I", raw, 36)[0]
    n = nx * ny * nz
    if dtype == 2:
        vals = struct.unpack_from("<%dh" % n, raw, off)
    elif dtype == 16:
        vals = struct.unpack_from("<%df" % n, raw, off)
    else:
        raise ValueError(f"unsupported dtype {dtype}")
    return nx, ny, nz, float(sx), float(sy), float(sz), [float(v) for v in vals]


def _conservation_fallback(path):
    nx, ny, nz, sx, sy, sz, voxels = _parse_tiv(path)
    n = nx * ny * nz

    def idx(x, y, z):
        return x + nx * (y + ny * z)

    sorted_vals = sorted(voxels)
    bg = _median_sorted(sorted_vals)
    lower = sorted_vals[: n // 2]
    med_low = _median_sorted(lower)
    mad = _median_sorted(sorted(abs(v - med_low) for v in lower))
    sigma = max(1e-6, 1.4826 * mad)

    residual = [v - bg for v in voxels]
    occ_thr = 4.0 * sigma
    occupied = [r > occ_thr for r in residual]

    seen = bytearray(n)
    best_mass = -1.0
    best_comp = None
    for z0 in range(nz):
        for y0 in range(ny):
            for x0 in range(nx):
                s = idx(x0, y0, z0)
                if not occupied[s] or seen[s]:
                    continue
                stack = [(x0, y0, z0)]
                seen[s] = 1
                comp = []
                mass = 0.0
                while stack:
                    x, y, z = stack.pop()
                    k = idx(x, y, z)
                    comp.append(k)
                    mass += residual[k]
                    for dx, dy, dz in NEIGH26:
                        a, b, c = x + dx, y + dy, z + dz
                        if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                            kk = idx(a, b, c)
                            if occupied[kk] and not seen[kk]:
                                seen[kk] = 1
                                stack.append((a, b, c))
                if mass > best_mass:
                    best_mass = mass
                    best_comp = comp

    assert best_comp, f"no bright region in {path}"

    filt = []
    for j in best_comp:
        x = j % nx
        y = (j // nx) % ny
        z = j // (nx * ny)
        acc = 0.0
        cnt = 0
        for dz in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    a, b, c = x + dx, y + dy, z + dz
                    if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                        acc += residual[idx(a, b, c)]
                        cnt += 1
        filt.append(acc / cnt)
    filt.sort(reverse=True)
    top_n = max(1, min(6, len(filt)))
    plateau = sum(filt[:top_n]) / top_n
    assert plateau > 0

    region = set(best_comp)
    frontier = set(best_comp)
    floor = 1.0 * sigma
    for _ in range(40):
        shell = set()
        for j in frontier:
            x = j % nx
            y = (j // nx) % ny
            z = j // (nx * ny)
            for dx, dy, dz in NEIGH26:
                a, b, c = x + dx, y + dy, z + dz
                if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                    k = idx(a, b, c)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        if sum(residual[j] for j in shell) / len(shell) <= floor:
            break
        region |= shell
        frontier = shell

    total = sum(residual[j] for j in region)
    return total / plateau * sx * sy * sz


def reference_volume_mm3(path):
    base = os.path.basename(path)
    if base in GEOM_TRUTH_MM3:
        return GEOM_TRUTH_MM3[base]
    return _conservation_fallback(path)


def run_agent(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    with tempfile.TemporaryDirectory() as td:
        neutral = os.path.join(td, "scan.tiv")
        shutil.copyfile(path, neutral)
        proc = subprocess.run(
            ["python3", SCRIPT, neutral],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=td,
        )
    assert proc.returncode == 0, (
        f"script failed on {path}\n{proc.stdout}\n{proc.stderr}"
    )
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines, f"no stdout on {path}"
    last = lines[-1]
    try:
        return float(last)
    except ValueError:
        m = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", last)
        assert m, f"no numeric volume on last line: {last!r}"
        return float(m[-1])


def test_script_exists():
    assert os.path.exists(SCRIPT)


def test_from_scratch():
    src = open(SCRIPT).read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                top = a.name.split(".")[0]
                assert top not in BANNED_MODULES, f"banned import {a.name}"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert mod.split(".")[0] not in BANNED_MODULES, f"banned import {mod}"
        elif isinstance(node, ast.Call):
            fn = node.func
            name = (
                fn.id
                if isinstance(fn, ast.Name)
                else (fn.attr if isinstance(fn, ast.Attribute) else "")
            )
            assert name not in BANNED_CALLS, f"dynamic exec {name}"
    compact = re.sub(r"\s+", "", src)
    for tok in BANNED_TOKENS:
        assert tok.replace(" ", "") not in compact, f"forbidden {tok}"


@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    got = run_agent(path)
    exp = reference_volume_mm3(path)
    assert abs(got - exp) <= REL_TOL * exp, (
        f"{os.path.basename(path)}: got {got:.4f} expected {exp:.4f} +/- {REL_TOL:.0%}"
    )
