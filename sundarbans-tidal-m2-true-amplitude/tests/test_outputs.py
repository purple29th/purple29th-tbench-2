"""Secure verifier for tidal-harmonic-m2-amplitude-recovery"""

import ast
import math
import os
import re
import struct
import subprocess
import sys
import tempfile
import pytest

SCRIPT = os.environ.get("SOLVE_PATH", "/app/solve.py")
REL_TOL = 0.03

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
    "os",
    "io",
    "posixpath",
    "ntpath",
    "genericpath",
}
BANNED_CALLS = {"eval", "exec", "compile", "__import__", "chr"}
BANNED_ATTRS = {
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
}
BANNED_SUBSTRINGS_SRC = [
    "/tests",
    "test_outputs",
    "heldout",
    "_gen",
    "GEOM_TRUTH",
    "geometric_truth",
    "reference_volume",
]

MAGIC = b"THLD"
W_M2 = 2 * math.pi / (12.4206 * 3600.0)
W_S2 = 2 * math.pi / (12.0 * 3600.0)
W_O1 = 2 * math.pi / (25.81934 * 3600.0)
W_K1 = 2 * math.pi / (23.93447 * 3600.0)


def _lcg(seed):
    s = seed & 0xFFFFFFFF
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s / 0x7FFFFFFF


def build_field(cfg):
    n = cfg["n"]
    dt = cfg["dt"]
    gain = cfg.get("gain", 1.0)
    mean_offset = cfg.get("mean_offset", 0.0)
    drift_rate = cfg.get("drift_rate", 0.0)
    amps = cfg["amps"]
    phases = cfg["phases"]
    noise_sigma = cfg["noise"]
    spike_indices = cfg.get("spikes", [])
    seed = cfg["seed"]
    rng = _lcg(seed)
    field = []
    true_m2 = amps.get("M2", 0.0)
    for i in range(n):
        t = i * dt
        sig = 0.0
        sig += amps.get("M2", 0.0) * math.cos(W_M2 * t + phases.get("M2", 0.0))
        if "S2" in amps:
            sig += amps["S2"] * math.cos(W_S2 * t + phases.get("S2", 0.0))
        if "O1" in amps:
            sig += amps["O1"] * math.cos(W_O1 * t + phases.get("O1", 0.0))
        if "K1" in amps:
            sig += amps["K1"] * math.cos(W_K1 * t + phases.get("K1", 0.0))
        sig += mean_offset + drift_rate * t
        obs = sig * gain
        u1 = next(rng)
        u2 = next(rng)
        if u1 < 1e-9:
            u1 = 1e-9
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2 * math.pi * u2)
        obs += z0 * noise_sigma
        field.append(obs)
    for idx_pos, mag in spike_indices:
        if 0 <= idx_pos < n:
            field[idx_pos] += mag
    return field, true_m2


def pack_thld(cfg, field):
    n = cfg["n"]
    dt = cfg["dt"]
    dtype = cfg["dtype"]
    gain = cfg.get("gain", 1.0)
    mean_offset = cfg.get("mean_offset", 0.0)
    freq_count = cfg.get("freq_count", 4)
    off = cfg.get("data_offset", 64)
    hdr = bytearray(max(64, off))
    hdr[0:4] = MAGIC
    struct.pack_into("<I", hdr, 4, 1)
    struct.pack_into("<I", hdr, 8, dtype)
    struct.pack_into("<I", hdr, 12, n)
    struct.pack_into("<f", hdr, 16, dt)
    struct.pack_into("<f", hdr, 20, gain)
    struct.pack_into("<f", hdr, 24, mean_offset)
    struct.pack_into("<I", hdr, 28, freq_count)
    struct.pack_into("<I", hdr, 32, off)
    hdr_bytes = bytes(hdr)
    if len(hdr_bytes) < off:
        hdr_bytes += b"\x00" * (off - len(hdr_bytes))
    if dtype == 2:
        vals = [max(-32768, min(32767, int(round(v * 1000.0)))) for v in field]
        body = struct.pack("<%dh" % n, *vals)
    else:
        body = struct.pack("<%df" % n, *field)
    return hdr_bytes + body


def geometric_truth_m(cfg, true_m2):
    return true_m2


BASE_CONFIGS = {
    "heldout_1": dict(
        n=2400,
        dt=600.0,
        dtype=16,
        gain=1.12,
        mean_offset=0.15,
        freq_count=4,
        data_offset=64,
        amps={"M2": 1.25, "S2": 0.38, "O1": 0.22, "K1": 0.31},
        phases={"M2": 0.8, "S2": 2.0, "O1": 1.5, "K1": 0.3},
        drift_rate=0.8e-6,
        noise=0.05,
        seed=202,
        spikes=[(200, 1.6), (900, -1.4), (1800, 2.0)],
    ),
    "heldout_2": dict(
        n=1800,
        dt=900.0,
        dtype=2,
        gain=0.92,
        mean_offset=-0.1,
        freq_count=3,
        data_offset=64,
        amps={"M2": 2.10, "S2": 0.55, "O1": 0.40},
        phases={"M2": 1.2, "S2": 0.5, "O1": 2.2},
        drift_rate=-0.6e-6,
        noise=0.07,
        seed=303,
        spikes=[(100, -1.8), (1200, 1.7)],
    ),
    "heldout_3": dict(
        n=3000,
        dt=450.0,
        dtype=16,
        gain=1.0,
        mean_offset=0.3,
        freq_count=4,
        data_offset=64,
        amps={"M2": 0.95, "S2": 0.30, "O1": 0.25, "K1": 0.20},
        phases={"M2": 2.5, "S2": 1.0, "O1": 0.2, "K1": 1.8},
        drift_rate=1.5e-6,
        noise=0.09,
        seed=404,
        spikes=[(400, 2.2), (1000, -2.0), (2200, 1.5), (2600, -1.6)],
    ),
    "spike_heavy": dict(
        n=2200,
        dt=600.0,
        dtype=16,
        gain=1.25,
        mean_offset=0.0,
        freq_count=4,
        data_offset=64,
        amps={"M2": 1.45, "S2": 0.40, "O1": 0.28, "K1": 0.22},
        phases={"M2": 0.4, "S2": 2.5, "O1": 1.2, "K1": 2.8},
        drift_rate=0.5e-6,
        noise=0.06,
        seed=505,
        spikes=[
            (100, 2.5),
            (300, -2.3),
            (700, 2.4),
            (1100, -2.2),
            (1600, 2.0),
            (2000, -2.1),
        ],
    ),
    "multi_constituent_heavy": dict(
        n=2500,
        dt=500.0,
        dtype=16,
        gain=0.88,
        mean_offset=0.25,
        freq_count=4,
        data_offset=64,
        amps={"M2": 1.80, "S2": 0.75, "O1": 0.60, "K1": 0.55},
        phases={"M2": 1.0, "S2": 0.7, "O1": 2.0, "K1": 1.3},
        drift_rate=-1.0e-6,
        noise=0.08,
        seed=606,
        spikes=[(500, 1.4), (1500, -1.3)],
    ),
    "heldout_96": dict(
        n=2100,
        dt=600.0,
        dtype=16,
        gain=1.05,
        mean_offset=0.18,
        freq_count=4,
        data_offset=96,
        amps={"M2": 1.15, "S2": 0.35, "O1": 0.20, "K1": 0.28},
        phases={"M2": 0.9, "S2": 1.8, "O1": 1.0, "K1": 2.4},
        drift_rate=0.9e-6,
        noise=0.055,
        seed=707,
        spikes=[(250, 1.7), (1700, -1.6)],
    ),
    "heldout_128": dict(
        n=2600,
        dt=600.0,
        dtype=16,
        gain=1.18,
        mean_offset=0.22,
        freq_count=4,
        data_offset=128,
        amps={"M2": 2.30, "S2": 0.50, "O1": 0.35, "K1": 0.30},
        phases={"M2": 0.2, "S2": 2.2, "O1": 0.6, "K1": 1.9},
        drift_rate=1.1e-6,
        noise=0.06,
        seed=808,
        spikes=[(600, -1.9), (1300, 2.1), (2100, -1.7)],
    ),
    "heldout_48": dict(
        n=2200,
        dt=600.0,
        dtype=16,
        gain=1.08,
        mean_offset=0.12,
        freq_count=4,
        data_offset=48,
        amps={"M2": 1.35, "S2": 0.40, "O1": 0.28, "K1": 0.24},
        phases={"M2": 0.7, "S2": 1.2, "O1": 0.9, "K1": 2.1},
        drift_rate=0.6e-6,
        noise=0.05,
        seed=515,
        spikes=[(300, 1.5), (1500, -1.4)],
    ),
    "heldout_80": dict(
        n=2400,
        dt=720.0,
        dtype=16,
        gain=0.96,
        mean_offset=0.20,
        freq_count=4,
        data_offset=80,
        amps={"M2": 1.75, "S2": 0.45, "O1": 0.30, "K1": 0.27},
        phases={"M2": 1.1, "S2": 0.8, "O1": 1.7, "K1": 0.4},
        drift_rate=0.9e-6,
        noise=0.06,
        seed=612,
        spikes=[(400, -1.6), (1800, 1.8)],
    ),
}

RANDOM_CONFIG = dict(
    n=2300,
    dt=600.0,
    dtype=16,
    gain=0.97,
    mean_offset=0.10,
    freq_count=4,
    data_offset=64,
    amps={"M2": 1.70, "S2": 0.42, "O1": 0.27, "K1": 0.24},
    phases={"M2": 1.5, "S2": 0.9, "O1": 2.1, "K1": 0.5},
    drift_rate=-0.7e-6,
    noise=0.06,
    seed=909,
    spikes=[(300, 1.6), (1800, -1.5)],
)

ALL_TEST_CONFIGS = [
    ("heldout_1", BASE_CONFIGS["heldout_1"]),
    ("heldout_2", BASE_CONFIGS["heldout_2"]),
    ("heldout_3", BASE_CONFIGS["heldout_3"]),
    ("spike_heavy", BASE_CONFIGS["spike_heavy"]),
    ("multi_constituent_heavy", BASE_CONFIGS["multi_constituent_heavy"]),
    ("heldout_96", BASE_CONFIGS["heldout_96"]),
    ("heldout_128", BASE_CONFIGS["heldout_128"]),
    ("heldout_48", BASE_CONFIGS["heldout_48"]),
    ("heldout_80", BASE_CONFIGS["heldout_80"]),
    ("randomized", RANDOM_CONFIG),
]

SECURE_RUNNER_CODE = r"""
import sys, os, runpy
solve_path=sys.argv[1]; scan_path=sys.argv[2]
BLOCKED_SUBSTRS=["/tests","test_outputs","heldout","_gen","GEOM_TRUTH","geometric_truth","reference_volume"]
def is_blocked(p):
    s=str(p)
    for b in BLOCKED_SUBSTRS:
        if b in s: return True
    try:
        rp=os.path.realpath(s)
        for b in BLOCKED_SUBSTRS:
            if b in rp: return True
    except: pass
    return False
def audit_hook(event,args):
    if event=="open":
        path=args[0] if args else ""
        if is_blocked(path): raise RuntimeError(f"Blocked {path}")
    elif event in ("os.listdir","os.scandir","os.walk"):
        path=args[0] if args else ""
        if is_blocked(path): raise RuntimeError(f"Blocked dir {path}")
    elif event.startswith("os."):
        banned={"os.system","os.popen","os.spawnl","os.spawnle","os.spawnlp","os.spawnlpe","os.spawnv","os.spawnve","os.spawnvp","os.spawnvpe","os.exec","os.execl","os.execle","os.execlp","os.execlpe","os.execv","os.execve","os.execvp","os.execvpe","os.posix_spawn","os.posix_spawnp","os.fork","os.forkpty"}
        if event in banned: raise RuntimeError(f"Blocked {event}")
    elif event.startswith("subprocess."): raise RuntimeError(f"Blocked {event}")
    elif event.startswith("socket."): raise RuntimeError(f"Blocked {event}")
    elif event=="import":
        mod=args[0] if args else ""; base=mod.split(".")[0]
        banned={"numpy","scipy","skimage","cv2","PIL","pandas","torch","tensorflow","subprocess","socket","multiprocessing","glob","pathlib","os","io","posixpath","ntpath","genericpath"}
        if base in banned: raise RuntimeError(f"Blocked import {mod}")
sys.addaudithook(audit_hook)
sys.argv=[solve_path, scan_path]
runpy.run_path(solve_path, run_name="__main__")
"""


def run_agent_secure(thld_bytes, expected, name="case"):
    assert os.path.exists(SCRIPT), f"{SCRIPT} missing"
    with tempfile.TemporaryDirectory() as td:
        scan_path = os.path.join(td, f"input_{os.urandom(4).hex()}.thld")
        with open(scan_path, "wb") as f:
            f.write(thld_bytes)
        secure_path = os.path.join(td, "_secure_runner.py")
        with open(secure_path, "w") as f:
            f.write(SECURE_RUNNER_CODE)
        proc = subprocess.run(
            ["python3", secure_path, SCRIPT, scan_path],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=td,
        )
        assert proc.returncode == 0, (
            f"fail {name} exp {expected:.3f} m\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
        lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
        assert lines, f"no output {name}"
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
        pytest.fail(f"syntax error: {e}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                base = a.name.split(".")[0]
                assert base not in BANNED_MODULES, f"banned import {a.name}"
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            assert mod not in BANNED_MODULES, f"banned from-import {node.module}"
        elif isinstance(node, ast.Call):
            fn = node.func
            name = ""
            if isinstance(fn, ast.Name):
                name = fn.id
            elif isinstance(fn, ast.Attribute):
                name = fn.attr
            assert name not in BANNED_CALLS, f"banned call {name}"
        if isinstance(node, ast.Attribute):
            assert node.attr not in BANNED_ATTRS, f"banned attr {node.attr}"
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            low = node.value.lower()
            for banned in BANNED_SUBSTRINGS_SRC:
                if banned.lower() in low:
                    pytest.fail(
                        f"banned substring in string: {banned} in {node.value!r}"
                    )
    compact = re.sub(r"\s+", "", src)
    compact_low = compact.lower()
    for tok in BANNED_SUBSTRINGS_SRC:
        t = tok.replace(" ", "").lower()
        assert t not in compact_low, f"banned token {tok}"
    lowered = src.lower()
    assert "chr(" not in lowered
    assert "fromhex" not in lowered
    assert "b64decode" not in lowered
    assert "pathlib" not in lowered
    assert "rglob" not in lowered
    assert "glob(" not in lowered


@pytest.mark.parametrize("cfg_name,cfg", ALL_TEST_CONFIGS)
def test_heldout_secure(cfg_name, cfg):
    field, true_m2 = build_field(cfg)
    thld_bytes = pack_thld(cfg, field)
    exp = geometric_truth_m(cfg, true_m2)
    got = run_agent_secure(thld_bytes, exp, name=cfg_name)
    assert abs(got - exp) <= REL_TOL * exp, (
        f"{cfg_name}: got {got:.4f} m expected {exp:.4f} ±{REL_TOL * 100}%"
    )


def test_randomized_extra():
    cfg = dict(
        n=2400,
        dt=600.0,
        dtype=16,
        gain=1.10,
        mean_offset=0.12,
        freq_count=4,
        data_offset=64,
        amps={"M2": 1.55, "S2": 0.38, "O1": 0.26, "K1": 0.22},
        phases={"M2": 0.6, "S2": 1.5, "O1": 2.3, "K1": 0.8},
        drift_rate=0.7e-6,
        noise=0.06,
        seed=999,
        spikes=[(300, 1.9), (1700, -1.8)],
    )
    field, true_m2 = build_field(cfg)
    b = pack_thld(cfg, field)
    exp = geometric_truth_m(cfg, true_m2)
    got = run_agent_secure(b, exp, name="random_extra")
    assert abs(got - exp) <= REL_TOL * exp


def test_naive_rms_fails_on_spike_heavy():
    cfg = BASE_CONFIGS["spike_heavy"]
    field, true_m2 = build_field(cfg)
    truth = geometric_truth_m(cfg, true_m2)

    def naive():
        # RMS * sqrt(2) is common naive for amplitude of single sine
        # But with spikes and other constituents it overestimates
        # Compute de-meaned RMS
        m = sum(field) / len(field)
        var = sum((x - m) ** 2 for x in field) / len(field)
        rms = var**0.5
        return rms * 1.41421356

    got = naive()
    assert abs(got - truth) > REL_TOL * truth, (
        f"naive RMS should fail spike_heavy got {got:.2f} vs truth {truth:.2f}"
    )


def test_gain_ignored_fails():
    cfg = BASE_CONFIGS["heldout_1"]
    field, true_m2 = build_field(cfg)
    truth = geometric_truth_m(cfg, true_m2)
    gain = cfg["gain"]
    # If solver forgets to divide by gain, it will be off by gain factor
    # For gain 1.12, error 12% >3%
    naive_without_gain_correction = truth * gain
    if abs(gain - 1.0) > 0.05:
        assert abs(naive_without_gain_correction - truth) > REL_TOL * truth
