"""Verify /app/solve.py reports mm^3 volume of a ToF parcel in a .tvol cube
on HELD-OUT scans the agent never saw.

Android ToF uses VCSEL IR emitter; its lens PSF is anisotropic (wide XY from
lens, narrow Z from timing jitter) and creates a saturated core plus thin
partial-volume flaps plus flying-pixel specks from multipath. Threshold-and-count
overcounts halo or undercounts flaps. The blur kernel is normalized and therefore
CONSERVES total IR energy, so true voxel count is:

    parcel_voxels = sum(occupancy - ambient over parcel+halo) / plateau_amplitude

computed on the largest-mass 26-connected component (far specks excluded).
This physical quantity matches the generator's geometric truth within <1% (see
_gen.py geometric_truth_mm3), but is recomputed here from the bytes with a
different robust heuristic than the oracle, so an agent must derive it from
scratch rather than memorizing sample numbers.

The agent must parse the binary format and implement reasoning FROM SCRATCH:
array/imaging/graph libs, dynamic execution, and shelling out or reading the
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

NEIGH = [
    (dx, dy, dz)
    for dz in (-1, 0, 1)
    for dy in (-1, 0, 1)
    for dx in (-1, 0, 1)
    if not (dx == 0 and dy == 0 and dz == 0)
]


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
    return (
        sorted_vals[m // 2]
        if m % 2
        else 0.5 * (sorted_vals[m // 2 - 1] + sorted_vals[m // 2])
    )


def reference_volume_mm3(path):
    """Independent ground truth by intensity conservation, pure stdlib.

    This implementation is deliberately distinct from the oracle solve.py in
    several robust choices (different low-value selection for noise estimation,
    different sigma multiplier, clamped border handling, median-of-top-8 plateau,
    longer halo growth with 0.9-sigma stop) so it does not reward line-for-line
    reproduction. It still matches the generator geometric_truth_mm3 within ~1%
    and the oracle within <1% on heldouts, so 3% tolerance allows heuristic
    variation but rejects threshold shortcuts.
    """
    nx, ny, nz, sx, sy, sz, vals = _parse(path)
    n = nx * ny * nz

    def idx(x, y, z):
        return x + nx * (y + ny * z)

    sv = sorted(vals)
    bg = _median(sv)
    # distinct: low values are those strictly below bg (not lower half slice)
    low_vals = [v for v in vals if v < bg]
    if not low_vals:
        low_vals = sv[: n // 2]
    low_sorted = sorted(low_vals)
    med_low = _median(low_sorted)
    mad = _median(sorted(abs(v - med_low) for v in low_sorted))
    noise_sigma = max(1e-6, 1.4826 * mad)

    r = [v - bg for v in vals]
    thr = 4.2 * noise_sigma  # distinct multiplier vs oracle's 4.0

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
                    cur = idx(x, y, z)
                    comp.append(cur)
                    mass += r[cur]
                    for dx, dy, dz in NEIGH:
                        a = x + dx
                        b = y + dy
                        c = z + dz
                        if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                            k = idx(a, b, c)
                            if occ[k] and not seen[k]:
                                seen[k] = 1
                                stack.append((a, b, c))
                if mass > best_mass:
                    best_mass = mass
                    best_comp = comp
    assert best_comp, f"no bright region in {path}"

    # plateau amplitude: clamped 3x3x3 mean-filter peak, median of top-8 (vs oracle's
    # skipped-border mean-of-top-8). Intentionally different but still robust.
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
    top = filt[: max(1, min(8, len(filt)))]
    amp = _median(sorted(top))  # median vs oracle mean
    assert amp > 0, f"non-positive amplitude in {path}"

    # adaptively grow to capture the faint halo, 60 iters and 0.9-sigma stop
    # (vs oracle 40 iters and 1.0-sigma), distinct growth policy.
    region = set(best_comp)
    frontier = set(best_comp)
    for _ in range(60):
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
        mean_shell = sum(r[j] for j in shell) / len(shell) if shell else 0.0
        if mean_shell <= 0.9 * noise_sigma:
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
        proc = subprocess.run(
            ["python3", SCRIPT, neutral],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=td,
        )
    assert proc.returncode == 0, (
        f"script exited {proc.returncode} on {path}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
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
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"


def test_from_scratch():
    """AST import/exec audit (robust to spacing and aliasing) plus a token scan
    that blocks reading the verifier or held-out data and shelling out."""
    src = open(SCRIPT).read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in BANNED_MODULES, (
                    f"banned module import: {a.name}"
                )
                assert "test_output" not in a.name, (
                    "importing the verifier is not allowed"
                )
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert mod.split(".")[0] not in BANNED_MODULES, (
                f"banned module import: {mod}"
            )
            assert "test_output" not in mod, "importing the verifier is not allowed"
        elif isinstance(node, ast.Call):
            fn = node.func
            name = (
                fn.id
                if isinstance(fn, ast.Name)
                else (fn.attr if isinstance(fn, ast.Attribute) else "")
            )
            assert name not in BANNED_CALLS, (
                f"dynamic execution is not allowed ({name})"
            )
    compact = re.sub(r"\s+", "", src)
    for tok in BANNED_TOKENS:
        assert tok.replace(" ", "") not in compact, f"forbidden usage detected ({tok})"


@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    got = run_agent(path)
    expected = reference_volume_mm3(path)
    assert abs(got - expected) <= REL_TOL * expected, (
        f"{os.path.basename(path)}: got {got:.4f} mm^3, "
        f"expected {expected:.4f} mm^3 (+/- {REL_TOL:.0%})"
    )
