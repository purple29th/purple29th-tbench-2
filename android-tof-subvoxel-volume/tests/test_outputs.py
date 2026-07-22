"""Verify /app/solve.py reports the mm^3 volume of a ToF-scanned object in a
.tvol volume, on HELD-OUT scans the agent never saw.

The object's intensity is spread by the sensor point-spread function, so a
threshold-and-count approach cannot recover the volume. The blur is a normalized
kernel and therefore CONSERVES total intensity, so the ground truth is recovered
here independently with numpy/scipy by intensity conservation:

    object_voxels = sum(intensity - background over the object) / plateau_amplitude

computed on the largest-mass 26-connected component (so the far specks are
excluded). This is the same physical quantity the generator built (a binary
object of a known voxel count), recomputed from the bytes -- a hardcoded constant
or a value memorised from the visible sample cannot match several different
held-outs.

The agent must parse the binary format and implement the reasoning FROM SCRATCH:
numpy/scipy/imaging/graph libraries and shelling out are rejected by
test_from_scratch().
"""
import os
import re
import struct
import subprocess

import numpy as np
import pytest
from scipy import ndimage

SCRIPT = "/app/solve.py"
REL_TOL = 0.03
HELDOUTS = [
    "/tests/data/heldout_1.tvol",
    "/tests/data/heldout_2.tvol",
    "/tests/data/heldout_3.tvol",
]

BANNED_IMPORTS = [
    "numpy", "scipy", "skimage", "cv2", "PIL", "Pillow",
    "networkx", "igraph", "imageio", "pandas", "torch", "tensorflow",
]


def _parse(path):
    d = open(path, "rb").read()
    assert d[:4] == b"TVOL", f"{path}: bad magic"
    dtype = struct.unpack_from("<I", d, 8)[0]
    nx, ny, nz = struct.unpack_from("<III", d, 12)
    sx, sy, sz = struct.unpack_from("<fff", d, 24)
    off = struct.unpack_from("<I", d, 36)[0]
    npdt = {2: "<i2", 16: "<f4"}[dtype]
    arr = np.frombuffer(d, dtype=npdt, count=nx * ny * nz, offset=off).astype(np.float64)
    vol = arr.reshape((nz, ny, nx))  # x varies fastest
    return vol, (float(sx), float(sy), float(sz))


def reference_volume_mm3(path):
    """Independent ground truth by intensity conservation (numpy/scipy)."""
    vol, (sx, sy, sz) = _parse(path)

    # background floor + noise scale (robust)
    bg = float(np.median(vol))
    r = vol - bg
    lo = r[r < np.median(r)] if np.any(r < np.median(r)) else r
    noise_sigma = max(1e-6, 1.4826 * float(np.median(np.abs(lo - np.median(lo)))))

    # largest-MASS 26-connected component above the noise floor -> the object
    mask = r > 4.0 * noise_sigma
    structure = ndimage.generate_binary_structure(3, 3)  # 26-connectivity
    labels, n = ndimage.label(mask, structure=structure)
    assert n >= 1, f"no bright region in {path}"
    masses = ndimage.sum(np.where(r > 0, r, 0.0), labels, index=np.arange(1, n + 1))
    obj = int(np.argmax(masses)) + 1
    comp = labels == obj

    # plateau amplitude: 3x3x3 mean-filter peak over the object component
    filt = ndimage.uniform_filter(r, size=3, mode="nearest")
    fv = np.sort(filt[comp])[::-1]
    amp = float(np.mean(fv[: max(1, min(8, fv.size))]))
    assert amp > 0, f"non-positive amplitude in {path}"

    # adaptively grow to capture the faint blur halo, then integrate signed
    # residual over the bounded region
    region = comp.copy()
    for _ in range(40):
        grown = ndimage.binary_dilation(region, structure=structure)
        shell = grown & ~region
        if not shell.any():
            break
        if float(r[shell].mean()) <= noise_sigma:
            break
        region = grown

    voxels = float(r[region].sum()) / amp
    return voxels * sx * sy * sz


def run_agent(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    proc = subprocess.run(["python3", SCRIPT, path],
                          capture_output=True, text=True, timeout=120)
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
    src = open(SCRIPT).read()
    compact = re.sub(r"\s+", "", src)
    for pkg in BANNED_IMPORTS:
        for call in (f"import{pkg}", f"from{pkg}import"):
            assert call not in compact, f"banned library usage detected ({pkg}); parse from scratch"
    for forbidden in ("os.system", "os.popen", "subprocess.", "Popen(", "__import__(", "importlib"):
        assert re.sub(r"\s+", "", forbidden) not in compact, (
            f"shelling out / dynamic import is not allowed ({forbidden})")


@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    got = run_agent(path)
    expected = reference_volume_mm3(path)
    assert abs(got - expected) <= REL_TOL * expected, (
        f"{os.path.basename(path)}: got {got:.4f} mm^3, "
        f"expected {expected:.4f} mm^3 (+/- {REL_TOL:.0%})")
