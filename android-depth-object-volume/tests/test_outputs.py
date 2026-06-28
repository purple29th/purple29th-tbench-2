"""Verify /app/solve.py reports the mm^3 volume of the scanned object (the
largest bright connected component) in an .avol depth volume, on HELD-OUT scans
the agent never saw.

Ground truth is computed here independently with numpy + scipy.ndimage
(26-connectivity), so a hardcoded constant or a value memorized from the sample
cannot match several different held-outs. The agent must parse the binary format
and implement connected-component labeling FROM SCRATCH: numpy/scipy/imaging/
graph libraries and shelling out are rejected by test_from_scratch().
"""
import os
import re
import struct
import subprocess

import numpy as np
import pytest
from scipy import ndimage

SCRIPT = "/app/solve.py"
THRESHOLD = 200.0      # sits in the empty band between background and object
REL_TOL = 0.05
HELDOUTS = [
    "/tests/data/heldout_1.avol",
    "/tests/data/heldout_2.avol",
    "/tests/data/heldout_3.avol",
]

BANNED_IMPORTS = [
    "numpy", "scipy", "skimage", "cv2", "PIL", "Pillow",
    "networkx", "igraph", "imageio", "pandas",
]

def _parse(path):
    d = open(path, "rb").read()
    assert d[:4] == b"AVOL", f"{path}: bad magic"
    dtype = struct.unpack_from("<I", d, 8)[0]
    nx, ny, nz = struct.unpack_from("<III", d, 12)
    sx, sy, sz = struct.unpack_from("<fff", d, 24)
    off = struct.unpack_from("<I", d, 36)[0]
    npdt = {2: "<i2", 16: "<f4"}[dtype]
    arr = np.frombuffer(d, dtype=npdt, count=nx * ny * nz, offset=off).astype(np.float64)
    vol = arr.reshape((nz, ny, nx))  # x varies fastest
    return vol, (float(sx), float(sy), float(sz))

def reference_volume_mm3(path):
    vol, (sx, sy, sz) = _parse(path)
    mask = vol > THRESHOLD
    structure = ndimage.generate_binary_structure(3, 3)  # 26-connectivity
    labels, n = ndimage.label(mask, structure=structure)
    assert n >= 1, f"no bright region in {path}"
    sizes = ndimage.sum(mask, labels, index=np.arange(1, n + 1))
    largest = int(np.argmax(sizes)) + 1
    voxels = int((labels == largest).sum())
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
        f"{os.path.basename(path)}: got {got:.4f} mm^3, expected {expected:.4f} mm^3 (+/- {REL_TOL:.0%})")
