"""Secure verifier for /app/solve.py - electroless nickel pit true area.

WLI lens PSF plus stage vibration blur conserves counts but inflates apparent
pit area. Threshold counting fails 2x over / 0.5x under. True area recoverable
via energy conservation, but global integration without speck removal fails.

Verifier generates heldouts at runtime with geometric truth from per-run random
seed at collection time (not a fixed table), runs solver in sandbox with hardened
audit hook that default-denies os.* namespace and blocks link/rename/symlink.
"""

import ast
import math
import os
import random
import re
import struct
import subprocess
import sys
import tempfile

import pytest

SCRIPT = os.environ.get("SOLVE_PATH", "/app/solve.py")
REL_TOL = 0.03

ALLOWED_MODULES = {"struct", "sys", "math", "random", "re"}
BANNED_CALLS = {"eval", "exec", "compile", "__import__", "chr"}
BANNED_OS_ATTRS = {
    "system",
    "popen",
    "exec",
    "execl",
    "execle",
    "execlp",
    "execlpe",
    "execv",
    "execve",
    "execvp",
    "execvpe",
    "spawnl",
    "spawnle",
    "spawnlp",
    "spawnlpe",
    "spawnv",
    "spawnve",
    "spawnvp",
    "spawnvpe",
    "posix_spawn",
    "posix_spawnp",
    "fork",
    "forkpty",
    "walk",
    "listdir",
    "scandir",
    "rglob",
    "__subclasses__",
    "__builtins__",
    "__code__",
    "__globals__",
    "__getattribute__",
    "link",
    "rename",
    "symlink",
    "replace",
}
BANNED_SUBSTRINGS_SRC = [
    "/tests",
    "test_outputs",
    "heldout",
    "GEOM_TRUTH",
    "geometric_truth",
    "reference_volume",
]
MAGIC = b"ENPP"


def _gauss_kernel1d(sigma, radius):
    w = [math.exp(-(x * x) / (2.0 * sigma * sigma)) for x in range(-radius, radius + 1)]
    s = sum(w)
    return [v / s for v in w]


def _blur_2d(vol, nx, ny, sig):
    r = max(1, int(math.ceil(3.5 * sig)))
    k = _gauss_kernel1d(sig, r)

    def idx(x, y):
        return x + nx * y

    a = [0.0] * len(vol)
    for y in range(ny):
        base = y * nx
        for x in range(nx):
            acc = 0.0
            for t in range(-r, r + 1):
                xx = x + t
                if 0 <= xx < nx:
                    acc += vol[base + xx] * k[t + r]
            a[base + x] = acc
    b = [0.0] * len(vol)
    for x in range(nx):
        for y in range(ny):
            acc = 0.0
            for t in range(-r, r + 1):
                yy = y + t
                if 0 <= yy < ny:
                    acc += a[idx(x, yy)] * k[t + r]
            b[idx(x, y)] = acc
    return b


def _lcg(seed):
    s = seed & 0xFFFFFFFF
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s / 0x7FFFFFFF


def build_field(cfg):
    nx, ny = cfg["dims"]
    n = nx * ny

    def idx(x, y):
        return x + nx * y

    clean = [0.0] * n
    true_set = set()

    def add_ell(cx, cy, rx, ry, factor=1.0):
        for y in range(ny):
            for x in range(nx):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    true_set.add(idx(x, y))
                    v = float(cfg["amp"] * factor)
                    if v > clean[idx(x, y)]:
                        clean[idx(x, y)] = v

    def add_box(x0, x1, y0, y1, factor=1.0):
        x0c = max(0, min(int(x0), int(x1)))
        x1c = min(nx, max(int(x0), int(x1)))
        y0c = max(0, min(int(y0), int(y1)))
        y1c = min(ny, max(int(y0), int(y1)))
        for y in range(y0c, y1c):
            for x in range(x0c, x1c):
                true_set.add(idx(x, y))
                v = float(cfg["amp"] * factor)
                if v > clean[idx(x, y)]:
                    clean[idx(x, y)] = v

    for shp in cfg["object"]:
        if not shp:
            continue
        typ = shp[0]
        if typ == "ell":
            if len(shp) == 5:
                _, cx, cy, rx, ry = shp
                add_ell(cx, cy, rx, ry, 1.0)
            else:
                _, cx, cy, rx, ry, factor = shp
                add_ell(cx, cy, rx, ry, float(factor))
        elif typ == "box":
            if len(shp) == 5:
                _, x0, x1, y0, y1 = shp
                add_box(x0, x1, y0, y1, 1.0)
            else:
                _, x0, x1, y0, y1, factor = shp
                add_box(x0, x1, y0, y1, float(factor))

    for sp in cfg["specks"]:
        if len(sp) == 3:
            sx0, sy0, sr = sp
            amp_dust = float(cfg["amp"])
        elif len(sp) == 4:
            sx0, sy0, sr, amp_dust = sp
            amp_dust = float(amp_dust)
        else:
            raise ValueError("speck len")
        r_int = int(math.ceil(sr + 1))
        x_min = max(0, int(sx0 - r_int))
        x_max = min(nx, int(sx0 + r_int + 1))
        y_min = max(0, int(sy0 - r_int))
        y_max = min(ny, int(sy0 + r_int + 1))
        sr2 = sr * sr
        for y in range(y_min, y_max):
            for x in range(x_min, x_max):
                if (x - sx0) ** 2 + (y - sy0) ** 2 <= sr2:
                    k = idx(x, y)
                    if amp_dust > clean[k]:
                        clean[k] = amp_dust

    blurred = _blur_2d(clean, nx, ny, cfg["sig"])
    bg = float(cfg["bg"])
    ns = float(cfg["noise"])
    tilt = cfg.get("tilt", (0.0, 0.0))
    tx, ty = float(tilt[0]), float(tilt[1])
    rng = _lcg(int(cfg["seed"]))
    field = [0.0] * n
    cx0 = nx / 2.0
    cy0 = ny / 2.0
    for y in range(ny):
        for x in range(nx):
            i = idx(x, y)
            tilt_contrib = tx * (x - cx0) + ty * (y - cy0)
            field[i] = blurred[i] + bg + tilt_contrib + (next(rng) - 0.5) * 2.0 * ns
    return field, len(true_set)


def pack_enpp(cfg, field):
    nx, ny = cfg["dims"]
    sx, sy = cfg["spacing"]
    dtype = cfg["dtype"]
    n = nx * ny
    hdr = bytearray(32)
    hdr[0:4] = MAGIC
    struct.pack_into("<I", hdr, 4, 1)
    struct.pack_into("<I", hdr, 8, dtype)
    struct.pack_into("<II", hdr, 12, nx, ny)
    struct.pack_into("<ff", hdr, 20, sx, sy)
    struct.pack_into("<I", hdr, 28, 32)
    if dtype == 2:
        vals = [max(-32768, min(32767, int(round(v)))) for v in field]
        body = struct.pack("<%dh" % n, *vals)
    elif dtype == 16:
        body = struct.pack("<%df" % n, *field)
    else:
        raise ValueError("dtype")
    return bytes(hdr) + body


def geometric_truth_mm2(cfg, v_true):
    sx, sy = cfg["spacing"]
    return v_true * sx * sy


# Fixed base configs known to be solvable at 3% – we jitter them per run to avoid byte-identical table
BASE_CONFIGS = {
    "heldout_1": dict(
        dims=(66, 62),
        spacing=(0.012, 0.018),
        dtype=16,
        amp=1100,
        bg=40,
        sig=2.2,
        noise=8,
        seed=101,
        tilt=(0.12, -0.10),
        object=[
            ("ell", 32, 30, 10, 9),
            ("box", 44, 50, 28, 33),
            ("box", 14, 20, 28, 33),
        ],
        specks=[(56, 8, 2.0), (8, 56, 1.8), (60, 60, 1.3)],
    ),
    "heldout_2": dict(
        dims=(64, 64),
        spacing=(0.015, 0.022),
        dtype=2,
        amp=1300,
        bg=60,
        sig=2.0,
        noise=10,
        seed=202,
        tilt=(0.18, 0.15),
        object=[("ell", 31, 32, 11, 10), ("box", 45, 52, 30, 35)],
        specks=[(55, 10, 1.9), (10, 55, 1.6)],
    ),
    "heldout_3": dict(
        dims=(70, 68),
        spacing=(0.011, 0.017),
        dtype=16,
        amp=1050,
        bg=45,
        sig=2.4,
        noise=9,
        seed=303,
        tilt=(-0.10, 0.20),
        object=[
            ("ell", 34, 33, 12, 11),
            ("box", 48, 56, 30, 35),
            ("box", 12, 20, 30, 35),
            ("box", 30, 35, 12, 20),
        ],
        specks=[(60, 8, 2.0), (8, 60, 1.7)],
    ),
    "speck_heavy": dict(
        dims=(66, 62),
        spacing=(0.012, 0.018),
        dtype=16,
        amp=1100,
        bg=40,
        sig=2.2,
        noise=8,
        seed=911,
        tilt=(0.12, -0.10),
        object=[
            ("ell", 32, 30, 10, 9),
            ("box", 44, 50, 28, 33),
            ("box", 14, 20, 28, 33),
        ],
        specks=[(56, 8, 4.0), (8, 56, 3.5), (60, 60, 3.2)],
    ),
}

EXTRA_RANDOM_BASE = dict(
    dims=(68, 64),
    spacing=(0.013, 0.019),
    dtype=2,
    amp=1200,
    bg=50,
    sig=2.3,
    noise=9,
    seed=404,
    tilt=(0.10, -0.08),
    object=[("ell", 33, 31, 10, 9), ("box", 46, 52, 29, 34), ("box", 16, 22, 29, 34)],
    specks=[(58, 9, 1.9), (9, 58, 1.7)],
)

TILTED_CONFIGS = {
    "tilted_strong_1": dict(
        dims=(68, 64),
        spacing=(0.013, 0.019),
        dtype=16,
        amp=1200,
        bg=50,
        sig=2.3,
        noise=9,
        seed=505,
        tilt=(0.35, -0.28),
        object=[
            ("ell", 33, 31, 10, 9),
            ("box", 46, 52, 29, 34),
            ("box", 16, 22, 29, 34),
        ],
        specks=[(58, 9, 1.9), (9, 58, 1.7)],
    ),
    "tilted_strong_2": dict(
        dims=(64, 66),
        spacing=(0.014, 0.021),
        dtype=2,
        amp=1150,
        bg=48,
        sig=2.1,
        noise=9,
        seed=606,
        tilt=(-0.30, 0.32),
        object=[
            ("ell", 32, 33, 11, 10),
            ("box", 45, 53, 31, 36),
            ("box", 16, 23, 31, 36),
        ],
        specks=[(56, 10, 2.0), (10, 58, 1.6)],
    ),
}

SCRATCH_CONFIGS = {
    "scratch_shallow": dict(
        dims=(74, 68),
        spacing=(0.012, 0.018),
        dtype=16,
        amp=1100,
        bg=42,
        sig=2.2,
        noise=8,
        seed=707,
        tilt=(0.10, -0.08),
        object=[
            ("ell", 26, 26, 9, 8),
            ("box", 36, 42, 24, 29),
            ("box", 10, 15, 24, 29),
        ],
        specks=[(62, 58, 14.0, 350.0), (60, 8, 1.8)],
    ),
    "scratch_anisotropic": dict(
        dims=(70, 70),
        spacing=(0.011, 0.019),
        dtype=2,
        amp=1250,
        bg=52,
        sig=2.3,
        noise=9,
        seed=808,
        tilt=(0.14, -0.12),
        object=[("ell", 30, 30, 10, 9), ("box", 42, 52, 28, 33)],
        specks=[(60, 60, 10.0, 380.0), (60, 8, 1.9)],
    ),
}

def _jitter_cfg(base, rng):
    # Small per-run jitter to make table not byte-identical, but keep solvable
    nx, ny = base["dims"]
    nx = max(60, min(80, nx + rng.randint(-2, 2)))
    ny = max(60, min(80, ny + rng.randint(-2, 2)))
    sx, sy = base["spacing"]
    sx = max(0.008, min(0.025, sx * rng.uniform(0.95, 1.05)))
    sy = max(0.008, min(0.025, sy * rng.uniform(0.95, 1.05)))
    amp = max(900, min(1400, base["amp"] + rng.randint(-80, 80)))
    bg = max(30, min(70, base["bg"] + rng.randint(-4, 4)))
    sig = max(1.9, min(2.6, base["sig"] + rng.uniform(-0.08, 0.08)))
    noise = max(6, min(12, base["noise"] + rng.randint(-1, 1)))
    seed = rng.randint(0, 1000000)
    tilt_x, tilt_y = base["tilt"]
    tilt = (tilt_x + rng.uniform(-0.04, 0.04), tilt_y + rng.uniform(-0.04, 0.04))
    # Jitter object shapes slightly
    new_objects = []
    for shp in base["object"]:
        typ = shp[0]
        if typ == "ell":
            _, cx, cy, rx, ry = shp[:5]
            cx = max(rx, min(nx - rx, cx + rng.randint(-2, 2)))
            cy = max(ry, min(ny - ry, cy + rng.randint(-2, 2)))
            new_objects.append(("ell", cx, cy, rx, ry))
        elif typ == "box":
            _, x0, x1, y0, y1 = shp[:5]
            x0 = max(0, min(nx-1, x0 + rng.randint(-2, 2)))
            x1 = max(x0+2, min(nx, x1 + rng.randint(-2, 2)))
            y0 = max(0, min(ny-1, y0 + rng.randint(-2, 2)))
            y1 = max(y0+2, min(ny, y1 + rng.randint(-2, 2)))
            new_objects.append(("box", x0, x1, y0, y1))
    # Jitter specks slightly, keep far distance
    new_specks = []
    for sp in base["specks"]:
        if len(sp) == 3:
            sx0, sy0, sr = sp
            sx0 = max(5, min(nx-5, sx0 + rng.randint(-2, 2)))
            sy0 = max(5, min(ny-5, sy0 + rng.randint(-2, 2)))
            new_specks.append((sx0, sy0, sr))
        else:
            sx0, sy0, sr, amp_dust = sp
            sx0 = max(5, min(nx-5, sx0 + rng.randint(-2, 2)))
            sy0 = max(5, min(ny-5, sy0 + rng.randint(-2, 2)))
            new_specks.append((sx0, sy0, sr, amp_dust))

    return dict(
        dims=(nx, ny),
        spacing=(sx, sy),
        dtype=base["dtype"],
        amp=amp,
        bg=bg,
        sig=sig,
        noise=noise,
        seed=seed,
        tilt=tilt,
        object=new_objects,
        specks=new_specks,
    )

_master_rng = random.Random(int.from_bytes(os.urandom(8), "little"))

_FIXED_TABLE = {
    "heldout_1": BASE_CONFIGS["heldout_1"],
    "heldout_2": BASE_CONFIGS["heldout_2"],
    "heldout_3": BASE_CONFIGS["heldout_3"],
    "speck_heavy": BASE_CONFIGS["speck_heavy"],
    "extra_random_base": EXTRA_RANDOM_BASE,
    "tilted_strong_1": TILTED_CONFIGS["tilted_strong_1"],
    "tilted_strong_2": TILTED_CONFIGS["tilted_strong_2"],
    "scratch_shallow": SCRATCH_CONFIGS["scratch_shallow"],
    "scratch_anisotropic": SCRATCH_CONFIGS["scratch_anisotropic"],
}

DYNAMIC_CONFIGS = {k: _jitter_cfg(v, _master_rng) for k, v in _FIXED_TABLE.items()}

ALL_TEST_CONFIGS = [(k, DYNAMIC_CONFIGS[k]) for k in [
    "heldout_1",
    "heldout_2",
    "heldout_3",
    "speck_heavy",
    "extra_random_base",
    "tilted_strong_1",
    "tilted_strong_2",
    "scratch_shallow",
    "scratch_anisotropic",
]]

def _make_random_cfg(rng, kind="normal"):
    # For extra fully random case – used by test_randomized_extra, fully random per run
    nx = rng.randint(62, 78)
    ny = rng.randint(60, 76)
    sx = rng.uniform(0.010, 0.022)
    sy = rng.uniform(0.010, 0.022)
    dtype = rng.choice([2, 16])
    amp = rng.randint(1000, 1300)
    bg = rng.randint(35, 65)
    sig = rng.uniform(2.0, 2.5)
    noise = rng.randint(7, 11)
    seed = rng.randint(0, 1000000)
    tilt = (rng.uniform(-0.20, 0.20), rng.uniform(-0.20, 0.20))
    if kind == "tilted":
        tilt = (rng.uniform(-0.35, 0.35), rng.uniform(-0.35, 0.35))
    cx = nx // 2 + rng.randint(-5, 5)
    cy = ny // 2 + rng.randint(-5, 5)
    rx = rng.randint(9, 12)
    ry = rng.randint(8, 11)
    object_shapes = [("ell", cx, cy, rx, ry)]
    for _ in range(rng.randint(1, 2)):
        side = rng.choice([-1, 1])
        bx = cx + side * rng.randint(rx, rx+4)
        by = cy + rng.randint(-3, 3)
        bw = rng.randint(4, 8)
        bh = rng.randint(3, 6)
        object_shapes.append(("box", bx, bx+bw, by, by+bh))
    specks = []
    def far_position():
        for _attempt in range(30):
            x = rng.choice([rng.randint(5, 15), rng.randint(nx-15, nx-5)])
            y = rng.choice([rng.randint(5, 15), rng.randint(ny-15, ny-5)])
            if math.hypot(x-cx, y-cy) > 25:
                return x, y
        return rng.randint(5, nx-5), rng.randint(5, ny-5)
    if kind == "scratch":
        fx, fy = far_position()
        large_r = rng.uniform(10.0, 14.0)
        large_amp = rng.uniform(300.0, 420.0)
        specks.append((fx, fy, large_r, large_amp))
        for _ in range(rng.randint(1, 2)):
            dx, dy = far_position()
            if math.hypot(dx-fx, dy-fy) < 15:
                continue
            specks.append((dx, dy, rng.uniform(1.5, 2.2)))
    elif kind == "speck_heavy":
        for _ in range(rng.randint(2, 3)):
            sx0, sy0 = far_position()
            specks.append((sx0, sy0, rng.uniform(3.0, 4.2)))
    else:
        for _ in range(rng.randint(1, 3)):
            sx0, sy0 = far_position()
            specks.append((sx0, sy0, rng.uniform(1.5, 2.2)))
    return dict(
        dims=(nx, ny),
        spacing=(sx, sy),
        dtype=dtype,
        amp=amp,
        bg=bg,
        sig=sig,
        noise=noise,
        seed=seed,
        tilt=tilt,
        object=object_shapes,
        specks=specks,
    )

SECURE_RUNNER_CODE = r"""
import sys, os, runpy
solve_path=sys.argv[1]
scan_path=sys.argv[2]
BLOCKED_SUBSTRS=["/tests","test_outputs","heldout","GEOM_TRUTH","geometric_truth","reference_volume"]
def is_blocked(p):
    s=str(p)
    for b in BLOCKED_SUBSTRS:
        if b in s:
            return True
    try:
        rp=os.path.realpath(s)
        for b in BLOCKED_SUBSTRS:
            if b in rp:
                return True
    except:
        pass
    return False

ALLOWED_OS_EVENTS = {
    "os.path.realpath",
    "os.realpath",
    "os.path.join",
    "os.path.abspath",
    "os.path.dirname",
    "os.path.basename",
    "os.path.exists",
    "os.listdir",
    "os.scandir",
    "os.walk",
    "os.stat",
    "os.lstat",
    "os.path.isdir",
    "os.path.isfile",
    "os.path.islink",
    "os.getcwd",
}

def audit_hook(event,args):
    if event=="open":
        path=args[0] if args else ""
        if is_blocked(path):
            raise RuntimeError(f"Blocked file access: {path}")
        try:
            rp=os.path.realpath(str(path))
            if rp.startswith("/tests") or "/tests" in rp:
                raise RuntimeError(f"Blocked realpath access: {path} -> {rp}")
            for blocked_candidate in ["/tests/test_outputs.py"]:
                try:
                    if os.path.exists(blocked_candidate):
                        if os.stat(path).st_ino == os.stat(blocked_candidate).st_ino:
                            raise RuntimeError(f"Blocked hardlink access: {path} inode matches {blocked_candidate}")
                except RuntimeError:
                    raise
                except:
                    pass
        except RuntimeError:
            raise
        except:
            pass
    elif event in ("os.listdir","os.scandir","os.walk"):
        path=args[0] if args else ""
        if is_blocked(path):
            raise RuntimeError(f"Blocked dir listing: {path}")
        try:
            rp=os.path.realpath(str(path)) if path else ""
            if rp in ("/","/tests","/tests/data") or rp.startswith("/tests"):
                raise RuntimeError(f"Blocked dir listing realpath: {path} -> {rp}")
        except RuntimeError:
            raise
        except:
            pass
        if str(path) in ("","/","/tests","/tests/data"):
            raise RuntimeError(f"Blocked listing of sensitive dir: {path}")
    if event in ("os.link", "os.symlink", "os.rename", "os.replace", "os.unlink", "os.remove"):
        raise RuntimeError(f"Blocked {event} - link/rename/symlink not allowed")
    if event.startswith("os."):
        if event not in ALLOWED_OS_EVENTS:
            if event.startswith("os.path."):
                if event not in ALLOWED_OS_EVENTS:
                    raise RuntimeError(f"Blocked {event} - default-deny os.* namespace")
            else:
                # Allow listdir/scandir/walk/stat that were checked above for sensitive paths
                if event not in ("os.listdir","os.scandir","os.walk","os.stat","os.lstat"):
                    raise RuntimeError(f"Blocked {event} - default-deny os.* namespace")
    if event.startswith("subprocess."):
        raise RuntimeError(f"Blocked {event}")
    if event.startswith("socket."):
        raise RuntimeError(f"Blocked {event}")
    if event=="import":
        mod=args[0] if args else ""
        base=mod.split(".")[0]
        banned_runtime={"numpy","scipy","skimage","cv2","PIL","Pillow","pandas","torch","tensorflow","subprocess","socket","multiprocessing","glob","pathlib","os","io","posixpath","ntpath","genericpath","tempfile"}
        if base in banned_runtime:
            raise RuntimeError(f"Blocked import {mod} - {base} not allowed")

sys.addaudithook(audit_hook)
sys.argv=[solve_path,scan_path]
runpy.run_path(solve_path,run_name="__main__")
"""


def run_agent_secure(enpp_bytes, expected_mm2, name="case"):
    assert os.path.exists(SCRIPT), f"{SCRIPT} missing"
    with tempfile.TemporaryDirectory() as td:
        enpp_path = os.path.join(td, f"input_{os.urandom(4).hex()}.enpp")
        with open(enpp_path, "wb") as f:
            f.write(enpp_bytes)
        secure_path = os.path.join(td, "_secure_runner.py")
        with open(secure_path, "w") as f:
            f.write(SECURE_RUNNER_CODE)
        proc = subprocess.run(
            ["python3", secure_path, SCRIPT, enpp_path],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=td,
        )
        assert proc.returncode == 0, (
            f"fail {name} (expected {expected_mm2:.5f} mm2)\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
        lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
        assert lines, f"no output for {name}"
        last = lines[-1]
        try:
            got = float(last)
        except ValueError:
            m = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", last)
            assert m, f"no float in last line: {last}"
            got = float(m[-1])
        return got


def test_script_exists():
    assert os.path.exists(SCRIPT)


def test_from_scratch():
    src = open(SCRIPT).read()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        pytest.fail(f"syntax error in solver: {e}")

    allowed_imports = {"struct", "sys", "math", "random", "re"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                base = a.name.split(".")[0]
                assert base in allowed_imports, f"import {a.name} not in allowlist {allowed_imports} - only struct, sys, math, random, re allowed (tempfile removed, see instruction)"
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod:
                assert mod in allowed_imports, f"from-import {node.module} not in allowlist {allowed_imports}"

        elif isinstance(node, ast.Call):
            fn = node.func
            name = ""
            if isinstance(fn, ast.Name):
                name = fn.id
            elif isinstance(fn, ast.Attribute):
                name = fn.attr
            assert name not in BANNED_CALLS, f"banned call {name} - see instruction eval/exec/compile/chr/fromhex/b64decode banned"

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if node.attr in BANNED_OS_ATTRS:
                cur = node
                is_os_qualified = False
                if isinstance(cur.value, ast.Name) and cur.value.id == "os":
                    is_os_qualified = True
                elif isinstance(cur.value, ast.Attribute):
                    def contains_os(n):
                        if isinstance(n, ast.Name):
                            return n.id == "os" or n.id == "_os"
                        elif isinstance(n, ast.Attribute):
                            return contains_os(n.value)
                        return False
                    if contains_os(cur.value):
                        is_os_qualified = True
                    try:
                        src_seg = ast.unparse(cur)
                        if "os." in src_seg or "_os." in src_seg:
                            if node.attr in {"link", "rename", "symlink", "replace", "system", "popen", "walk", "listdir", "scandir"}:
                                is_os_qualified = True
                    except:
                        pass
                if is_os_qualified:
                    assert False, f"banned os attribute {node.attr} via os-qualified access - plain helper named {node.attr}() is allowed, but os.{node.attr} is blocked per instruction. Use allowed imports struct, sys, math, random, re only."

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            low = node.value.lower()
            for banned in BANNED_SUBSTRINGS_SRC:
                if banned.lower() in low:
                    pytest.fail(
                        f"banned substring in string literal: {banned} in {node.value!r} - source must not contain /tests, test_outputs, heldout, GEOM_TRUTH, geometric_truth, reference_volume per instruction"
                    )
    compact = re.sub(r"\s+", "", src)
    compact_low = compact.lower()
    for tok in BANNED_SUBSTRINGS_SRC:
        t = tok.replace(" ", "").lower()
        assert t not in compact_low, f"banned token {tok} - source must not contain /tests etc. per instruction, plain helper allowed but os.* default-deny"
    lowered = src.lower()
    assert "chr(" not in lowered, "chr() banned - see instruction"
    assert "fromhex" not in lowered, "fromhex banned - see instruction"
    assert "b64decode" not in lowered, "b64decode banned - see instruction"


@pytest.mark.parametrize("cfg_name,cfg", ALL_TEST_CONFIGS)
def test_heldout_secure(cfg_name, cfg):
    field, v_true = build_field(cfg)
    enpp_bytes = pack_enpp(cfg, field)
    exp_mm2 = geometric_truth_mm2(cfg, v_true)
    got = run_agent_secure(enpp_bytes, exp_mm2, name=cfg_name)
    assert abs(got - exp_mm2) <= REL_TOL * exp_mm2, (
        f"{cfg_name}: got {got:.6f} mm2 expected {exp_mm2:.6f} \u00b1{REL_TOL * 100}%"
    )


def test_randomized_extra():
    rng = random.Random(int.from_bytes(os.urandom(4), "little"))
    cfg = _make_random_cfg(rng, kind="normal")
    field, v_true = build_field(cfg)
    enpp_bytes = pack_enpp(cfg, field)
    exp_mm2 = geometric_truth_mm2(cfg, v_true)
    got = run_agent_secure(enpp_bytes, exp_mm2, name="randomized_extra")
    assert abs(got - exp_mm2) <= REL_TOL * exp_mm2


def test_global_conservation_shortcut_fails_on_speck_heavy():
    cfg = DYNAMIC_CONFIGS["speck_heavy"]
    field, v_true = build_field(cfg)
    truth = geometric_truth_mm2(cfg, v_true)

    def naive_global():
        sv = sorted(field)
        bg = sv[len(sv) // 2]
        r = [v - bg for v in field]
        filt = sorted(r, reverse=True)
        topk = filt[:8]
        amp = sum(topk) / len(topk) if topk else 1
        sx, sy = cfg["spacing"]
        mass = sum(r)
        return mass / amp * sx * sy if amp > 0 else 0

    got = naive_global()
    assert abs(got - truth) > REL_TOL * truth, (
        f"Expected naive global to fail on speck_heavy, got {got:.5f} vs truth {truth:.5f}"
    )


def test_pixel_count_vs_mass_ranking():
    cfg = DYNAMIC_CONFIGS["scratch_shallow"]
    nx, ny = cfg["dims"]
    n = nx * ny

    def idx(x, y):
        return x + nx * y

    _, v_main = build_field(dict(cfg, specks=[]))
    sx0, sy0, sr, amp_dust = cfg["specks"][0]
    sr2 = sr * sr
    r_int = int(math.ceil(sr + 1))
    cnt_dust = 0
    for y in range(max(0, int(sy0 - r_int)), min(ny, int(sy0 + r_int + 1))):
        for x in range(max(0, int(sx0 - r_int)), min(nx, int(sx0 + r_int + 1))):
            if (x - sx0) ** 2 + (y - sy0) ** 2 <= sr2:
                cnt_dust += 1
    amp_main = cfg["amp"]
    mass_main = v_main * amp_main
    mass_dust = cnt_dust * amp_dust
    assert cnt_dust > v_main, (
        f"setup expects dust pixel count > main: dust {cnt_dust} main {v_main}"
    )
    assert mass_main > mass_dust, (
        f"setup expects main mass > dust mass: main {mass_main} dust {mass_dust}"
    )
    sx, sy = cfg["spacing"]
    area_main = v_main * sx * sy
    area_dust = cnt_dust * sx * sy
    assert abs(area_main - area_dust) > REL_TOL * area_main


def test_pixel_count_shortcut_fails_on_scratch():
    cfg = DYNAMIC_CONFIGS["scratch_shallow"]
    field, v_true = build_field(cfg)
    truth = geometric_truth_mm2(cfg, v_true)
    nx, ny = cfg["dims"]
    sx, sy = cfg["spacing"]
    n = nx * ny

    def idx(x, y):
        return x + nx * y

    entries = sorted(field)
    lower_vals = entries[: n // 2]
    bg = lower_vals[len(lower_vals) // 2] if lower_vals else 0

    resid = [v - bg for v in field]
    lower_res = [v - bg for v in lower_vals]
    lower_res_sorted = sorted(lower_res)
    med_low = lower_res_sorted[len(lower_res_sorted) // 2] if lower_res_sorted else 0
    abs_dev = sorted(abs(r - med_low) for r in lower_res)
    mad = abs_dev[len(abs_dev) // 2] if abs_dev else 1
    noise_sigma = max(1e-6, 1.4826 * mad)

    thr = 4.0 * noise_sigma
    occupied = [r > thr for r in resid]

    seen = bytearray(n)
    best_cnt = -1
    best = None
    NEIGH8 = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]
    for y0 in range(ny):
        for x0 in range(nx):
            k = idx(x0, y0)
            if not occupied[k] or seen[k]:
                continue
            stack = [(x0, y0)]
            seen[k] = 1
            comp = []
            while stack:
                x, y = stack.pop()
                kk = idx(x, y)
                comp.append(kk)
                for dx, dy in NEIGH8:
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < nx and 0 <= yy < ny:
                        nidx = idx(xx, yy)
                        if occupied[nidx] and not seen[nidx]:
                            seen[nidx] = 1
                            stack.append((xx, yy))
            if len(comp) > best_cnt:
                best_cnt = len(comp)
                best = comp

    assert best is not None, "naive found no component"
    naive_area = len(best) * sx * sy
    assert abs(naive_area - truth) > REL_TOL * truth, (
        f"Expected pixel-count shortcut to fail on scratch_shallow, got {naive_area:.5f} vs truth {truth:.5f}"
    )
