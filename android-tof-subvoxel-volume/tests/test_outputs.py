"""Verify /app/solve.py reports the mm^3 volume of a ToF-scanned object in a
.tvol volume, on HELD-OUT scans the agent never saw.

The object's intensity is spread by the sensor point-spread function, so a
threshold-and-count approach cannot recover the volume. The blur is a normalized
kernel and therefore CONSERVES total intensity, so the ground truth is recovered
here independently, in PURE standard-library Python (no third-party libraries are
needed at grade time), by intensity conservation:

    object_voxels = sum(intensity - background over the object) / plateau_amplitude

computed on the largest-mass 26-connected component (so the far specks are
excluded). This is the same physical quantity the generator built, recomputed
from the bytes -- a hardcoded constant or a value memorised from the sample
cannot match several different held-outs.

The agent must parse the binary format and implement the reasoning FROM SCRATCH:
array/imaging/graph libraries, dynamic execution, and shelling out or reading the
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
REL_TOL = 0.03
HELDOUTS = [
    "/tests/data/heldout_1.tvol",
    "/tests/data/heldout_2.tvol",
    "/tests/data/heldout_3.tvol",
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

NEIGH = [(dx, dy, dz)
         for dz in (-1, 0, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
         if not (dx == 0 and dy == 0 and dz == 0)]


def _parse(path):
    d = open(path, "rb").read()
    assert d[:4] == b"TVOL", f"{path}: bad magic"
    dtype = struct.unpack_from("<I", d, 8)[0]
    nx, ny, nz = struct.unpack_from("<III", d, 12)
    sx, sy, sz = struct.unpack_from("<fff", d, 24)
    off = struct.unpack_from("<I", d, 36)[0]
    n = nx * ny * nz
    fmt = {2: "<%dh", 16: "<%df"}[dtype] % n
    vals = [float(v) for v in struct.unpack_from(fmt, d, off)]
    return nx, ny, nz, float(sx), float(sy), float(sz), vals


def _median(sorted_vals):
    m = len(sorted_vals)
    if m == 0:
        return 0.0
    return sorted_vals[m // 2] if m % 2 else 0.5 * (sorted_vals[m // 2 - 1] + sorted_vals[m // 2])


def reference_volume_mm3(path):
    """Independent ground truth by intensity conservation, pure stdlib."""
    nx, ny, nz, sx, sy, sz, vals = _parse(path)
    n = nx * ny * nz

    def idx(x, y, z):
        return x + nx * (y + ny * z)

    sv = sorted(vals)
    bg = _median(sv)
    lo = [v for v in vals if v < bg] or vals
    med_lo = _median(sorted(lo))
    mad = _median(sorted(abs(v - med_lo) for v in lo))
    noise_sigma = max(1e-6, 1.4826 * mad)

    r = [v - bg for v in vals]
    thr = 4.0 * noise_sigma

    # largest-mass 26-connected component above the noise floor
    occ = [v > thr for v in r]
    seen = bytearray(n)
    best_mass = -1.0
    best_comp = None
    for z0 in range(nz):
        for y0 in range(ny):
            for x0 in range(nx):
                s = idx(x0, y0, z0)
                if not occ[s] or seen[s]:
                    continue
                stack = [(x0, y0, z0)]
                seen[s] = 1
                comp = []
                mass = 0.0
                while stack:
                    x, y, z = stack.pop()
                    comp.append(idx(x, y, z))
                    mass += r[idx(x, y, z)]
                    for dx, dy, dz in NEIGH:
                        a, b, c = x + dx, y + dy, z + dz
                        if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                            k = idx(a, b, c)
                            if occ[k] and not seen[k]:
                                seen[k] = 1
                                stack.append((a, b, c))
                if mass > best_mass:
                    best_mass = mass
                    best_comp = comp
    assert best_comp, f"no bright region in {path}"

    # plateau amplitude: mean of the top few 3x3x3 mean-filter values over the object
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
                    a = min(max(x + dx, 0), nx - 1)
                    b = min(max(y + dy, 0), ny - 1)
                    c = min(max(z + dz, 0), nz - 1)
                    acc += r[idx(a, b, c)]
                    cnt += 1
        filt.append(acc / cnt)
    filt.sort(reverse=True)
    topk = filt[: max(1, min(8, len(filt)))]
    amp = sum(topk) / len(topk)
    assert amp > 0, f"non-positive amplitude in {path}"

    # adaptively grow to capture the faint halo, then integrate signed residual
    region = set(best_comp)
    frontier = set(best_comp)
    for _ in range(40):
        shell = set()
        for j in frontier:
            x = j % nx
            y = (j // nx) % ny
            z = j // (nx * ny)
            for dx, dy, dz in NEIGH:
                a, b, c = x + dx, y + dy, z + dz
                if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                    k = idx(a, b, c)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        if sum(r[j] for j in shell) / len(shell) <= noise_sigma:
            break
        region |= shell
        frontier = shell

    voxels = sum(r[j] for j in region) / amp
    return voxels * sx * sy * sz


def run_agent(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    # Run the agent script on an isolated copy of the scan under a neutral name,
    # from a temp working directory: it receives only the input path, cannot tell
    # which held-out this is, and has no route to the mounted verifier / held-out
    # data under /tests (also blocked statically by test_from_scratch).
    with tempfile.TemporaryDirectory() as td:
        neutral = os.path.join(td, "scan.tvol")
        shutil.copyfile(path, neutral)
        proc = subprocess.run(["python3", SCRIPT, neutral],
                              capture_output=True, text=True, timeout=120, cwd=td)
    assert proc.returncode == 0, (
        f"script exited {proc.returncode} on {path}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
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
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"


def test_from_scratch():
    """AST import/exec audit (robust to spacing and aliasing) plus a token scan
    that blocks reading the verifier or held-out data and shelling out."""
    src = open(SCRIPT).read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in BANNED_MODULES, f"banned module import: {a.name}"
                assert "test_output" not in a.name, "importing the verifier is not allowed"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert mod.split(".")[0] not in BANNED_MODULES, f"banned module import: {mod}"
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
    expected = reference_volume_mm3(path)
    assert abs(got - expected) <= REL_TOL * expected, (
        f"{os.path.basename(path)}: got {got:.4f} mm^3, "
        f"expected {expected:.4f} mm^3 (+/- {REL_TOL:.0%})")
