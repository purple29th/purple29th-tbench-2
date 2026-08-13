"""Secure verifier for music-harmonic-tonic-balance-recovery"""

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

MAGIC = b"MTHB"
THIRD_RATIO = 2 ** (4 / 12)
FIFTH_RATIO = 2 ** (7 / 12)


def _lcg(seed):
    s = seed & 0xFFFFFFFF
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s / 0x7FFFFFFF


def get_freqs(f0):
    return {
        "tonic": f0,
        "third": f0 * THIRD_RATIO,
        "fifth": f0 * FIFTH_RATIO,
        "octave": f0 * 2.0,
        "harm2": f0 * 3.0,
    }


def build_field(cfg):
    n = cfg["n"]
    dt = cfg["dt"]
    f0 = cfg["f0"]
    gain = cfg.get("gain", 1.0)
    mean_offset = cfg.get("mean_offset", 0.0)
    drift_rate = cfg.get("drift_rate", 0.0)
    amps = cfg["amps"]
    phases = cfg["phases"]
    noise_sigma = cfg["noise"]
    spikes = cfg.get("spikes", [])
    seed = cfg["seed"]
    freqs = get_freqs(f0)
    rng = _lcg(seed)
    field = []
    true_tonic = amps.get("tonic", 0.0)
    for i in range(n):
        t = i * dt
        sig = 0.0
        for key in amps:
            if key in freqs:
                f = freqs[key]
                sig += amps[key] * math.cos(2 * math.pi * f * t + phases.get(key, 0.0))
        sig += mean_offset + drift_rate * t
        obs = sig * gain
        u1 = next(rng)
        u2 = next(rng)
        if u1 < 1e-12:
            u1 = 1e-12
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2 * math.pi * u2)
        obs += z0 * noise_sigma
        field.append(obs)
    for idx_pos, mag in spikes:
        if 0 <= idx_pos < n:
            field[idx_pos] += mag
    return field, true_tonic


def pack_mthb(cfg, field):
    n = cfg["n"]
    dt = cfg["dt"]
    f0 = cfg["f0"]
    dtype = cfg["dtype"]
    gain = cfg.get("gain", 1.0)
    mean_offset = cfg.get("mean_offset", 0.0)
    freq_count = cfg.get("freq_count", 5)
    off = cfg.get("data_offset", 64)
    hdr = bytearray(max(64, off))
    hdr[0:4] = MAGIC
    struct.pack_into("<I", hdr, 4, 1)
    struct.pack_into("<I", hdr, 8, dtype)
    struct.pack_into("<I", hdr, 12, n)
    struct.pack_into("<f", hdr, 16, dt)
    struct.pack_into("<f", hdr, 20, f0)
    struct.pack_into("<f", hdr, 24, gain)
    struct.pack_into("<f", hdr, 28, mean_offset)
    struct.pack_into("<I", hdr, 32, freq_count)
    struct.pack_into("<I", hdr, 36, off)
    hdr_bytes = bytes(hdr)
    if len(hdr_bytes) < off:
        hdr_bytes += b"\x00" * (off - len(hdr_bytes))
    if dtype == 2:
        vals = [max(-32768, min(32767, int(round(v * 1000.0)))) for v in field]
        body = struct.pack("<%dh" % n, *vals)
    else:
        body = struct.pack("<%df" % n, *field)
    return hdr_bytes + body


def geometric_truth(cfg, true_tonic):
    return true_tonic


BASE_CONFIGS = {
    "heldout_1": dict(
        n=4000,
        dt=0.0005,
        f0=220.0,
        dtype=16,
        gain=1.12,
        mean_offset=0.15,
        freq_count=5,
        data_offset=64,
        amps={
            "tonic": 1.25,
            "third": 0.38,
            "fifth": 0.22,
            "octave": 0.28,
            "harm2": 0.20,
        },
        phases={"tonic": 0.8, "third": 2.0, "fifth": 1.5, "octave": 0.3, "harm2": 1.2},
        drift_rate=0.015,
        noise=0.05,
        seed=202,
        spikes=[(400, 1.6), (1800, -1.4), (3200, 2.0)],
    ),
    "heldout_2": dict(
        n=3000,
        dt=0.0008,
        f0=110.0,
        dtype=2,
        gain=0.92,
        mean_offset=-0.1,
        freq_count=3,
        data_offset=64,
        amps={"tonic": 2.10, "third": 0.55, "fifth": 0.40},
        phases={"tonic": 1.2, "third": 0.5, "fifth": 2.2},
        drift_rate=-0.02,
        noise=0.07,
        seed=303,
        spikes=[(200, -1.8), (2000, 1.7)],
    ),
    "heldout_3": dict(
        n=5000,
        dt=0.0004,
        f0=330.0,
        dtype=16,
        gain=1.0,
        mean_offset=0.3,
        freq_count=5,
        data_offset=64,
        amps={
            "tonic": 0.95,
            "third": 0.30,
            "fifth": 0.25,
            "octave": 0.22,
            "harm2": 0.18,
        },
        phases={"tonic": 2.5, "third": 1.0, "fifth": 0.2, "octave": 1.8, "harm2": 0.9},
        drift_rate=0.03,
        noise=0.09,
        seed=404,
        spikes=[(800, 2.2), (1800, -2.0), (3500, 1.5), (4200, -1.6)],
    ),
    "spike_heavy": dict(
        n=4000,
        dt=0.0005,
        f0=440.0,
        dtype=16,
        gain=1.25,
        mean_offset=0.0,
        freq_count=5,
        data_offset=64,
        amps={
            "tonic": 1.45,
            "third": 0.40,
            "fifth": 0.28,
            "octave": 0.25,
            "harm2": 0.20,
        },
        phases={"tonic": 0.4, "third": 2.5, "fifth": 1.2, "octave": 2.8, "harm2": 1.0},
        drift_rate=0.01,
        noise=0.06,
        seed=505,
        spikes=[
            (200, 2.5),
            (600, -2.3),
            (1400, 2.4),
            (2000, -2.2),
            (2800, 2.0),
            (3600, -2.1),
        ],
    ),
    "arrangement_heavy": dict(
        n=4500,
        dt=0.0005,
        f0=196.0,
        dtype=16,
        gain=0.88,
        mean_offset=0.25,
        freq_count=5,
        data_offset=64,
        amps={
            "tonic": 1.80,
            "third": 0.75,
            "fifth": 0.60,
            "octave": 0.55,
            "harm2": 0.45,
        },
        phases={"tonic": 1.0, "third": 0.7, "fifth": 2.0, "octave": 1.3, "harm2": 0.4},
        drift_rate=-0.02,
        noise=0.08,
        seed=606,
        spikes=[(1000, 1.4), (3000, -1.3)],
    ),
    "heldout_96": dict(
        n=3800,
        dt=0.0005,
        f0=261.63,
        dtype=16,
        gain=1.05,
        mean_offset=0.18,
        freq_count=5,
        data_offset=96,
        amps={
            "tonic": 1.15,
            "third": 0.35,
            "fifth": 0.20,
            "octave": 0.26,
            "harm2": 0.19,
        },
        phases={"tonic": 0.9, "third": 1.8, "fifth": 1.0, "octave": 2.4, "harm2": 0.7},
        drift_rate=0.02,
        noise=0.055,
        seed=707,
        spikes=[(500, 1.7), (3000, -1.6)],
    ),
    "heldout_128": dict(
        n=4200,
        dt=0.0005,
        f0=329.63,
        dtype=16,
        gain=1.18,
        mean_offset=0.22,
        freq_count=5,
        data_offset=128,
        amps={
            "tonic": 2.30,
            "third": 0.50,
            "fifth": 0.35,
            "octave": 0.30,
            "harm2": 0.28,
        },
        phases={"tonic": 0.2, "third": 2.2, "fifth": 0.6, "octave": 1.9, "harm2": 1.1},
        drift_rate=0.025,
        noise=0.06,
        seed=808,
        spikes=[(1000, -1.9), (2200, 2.1), (3600, -1.7)],
    ),
}

RANDOM_CONFIG = dict(
    n=4000,
    dt=0.0005,
    f0=220.0,
    dtype=16,
    gain=0.97,
    mean_offset=0.10,
    freq_count=5,
    data_offset=64,
    amps={"tonic": 1.70, "third": 0.42, "fifth": 0.27, "octave": 0.24, "harm2": 0.21},
    phases={"tonic": 1.5, "third": 0.9, "fifth": 2.1, "octave": 0.5, "harm2": 1.3},
    drift_rate=-0.015,
    noise=0.06,
    seed=909,
    spikes=[(600, 1.6), (3200, -1.5)],
)

ALL_TEST_CONFIGS = [
    ("heldout_1", BASE_CONFIGS["heldout_1"]),
    ("heldout_2", BASE_CONFIGS["heldout_2"]),
    ("heldout_3", BASE_CONFIGS["heldout_3"]),
    ("spike_heavy", BASE_CONFIGS["spike_heavy"]),
    ("arrangement_heavy", BASE_CONFIGS["arrangement_heavy"]),
    ("heldout_96", BASE_CONFIGS["heldout_96"]),
    ("heldout_128", BASE_CONFIGS["heldout_128"]),
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


def run_agent_secure(mthb_bytes, expected, name="case"):
    assert os.path.exists(SCRIPT), f"{SCRIPT} missing"
    with tempfile.TemporaryDirectory() as td:
        scan_path = os.path.join(td, f"input_{os.urandom(4).hex()}.mthb")
        with open(scan_path, "wb") as f:
            f.write(mthb_bytes)
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
            f"fail {name} exp {expected:.3f} V\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
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
    field, true_tonic = build_field(cfg)
    mthb_bytes = pack_mthb(cfg, field)
    exp = geometric_truth(cfg, true_tonic)
    got = run_agent_secure(mthb_bytes, exp, name=cfg_name)
    assert abs(got - exp) <= REL_TOL * exp, (
        f"{cfg_name}: got {got:.4f} V expected {exp:.4f} ±{REL_TOL * 100}%"
    )


def test_randomized_extra():
    cfg = dict(
        n=4000,
        dt=0.0005,
        f0=220.0,
        dtype=16,
        gain=1.10,
        mean_offset=0.12,
        freq_count=5,
        data_offset=64,
        amps={
            "tonic": 1.55,
            "third": 0.38,
            "fifth": 0.26,
            "octave": 0.22,
            "harm2": 0.20,
        },
        phases={"tonic": 0.6, "third": 1.5, "fifth": 2.3, "octave": 0.8, "harm2": 1.1},
        drift_rate=0.015,
        noise=0.06,
        seed=999,
        spikes=[(600, 1.9), (3000, -1.8)],
    )
    field, true_tonic = build_field(cfg)
    b = pack_mthb(cfg, field)
    exp = geometric_truth(cfg, true_tonic)
    got = run_agent_secure(b, exp, name="random_extra")
    assert abs(got - exp) <= REL_TOL * exp


def test_naive_rms_fails_on_spike_heavy():
    cfg = BASE_CONFIGS["spike_heavy"]
    field, true_tonic = build_field(cfg)
    truth = geometric_truth(cfg, true_tonic)

    def naive():
        m = sum(field) / len(field)
        var = sum((x - m) ** 2 for x in field) / len(field)
        rms = var**0.5
        return rms * 1.4142

    got = naive()
    assert abs(got - truth) > REL_TOL * truth, (
        f"naive RMS should fail spike_heavy got {got:.2f} vs truth {truth:.2f}"
    )


def test_gain_ignored_fails():
    cfg = BASE_CONFIGS["heldout_1"]
    field, true_tonic = build_field(cfg)
    truth = geometric_truth(cfg, true_tonic)
    gain = cfg["gain"]
    naive_without_gain = truth * gain
    if abs(gain - 1.0) > 0.05:
        assert abs(naive_without_gain - truth) > REL_TOL * truth
