import ast
import math
import os
import pwd
import re
import struct
import subprocess
import sys
import tempfile
import textwrap
import random
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
    "modules",
    "import_module",
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
BANNED_OBFUSCATION_SUBSTRS = [
    "fromhex",
    "b64decode",
    "b32decode",
    "b16decode",
    "b85decode",
]

MAGIC = b"PMAR"


def _gauss_kernel1d(sigma, radius):
    w = [math.exp(-(x * x) / (2.0 * sigma * sigma)) for x in range(-radius, radius + 1)]
    s = sum(w)
    return [v / s for v in w]


def _blur_1d(vol, total, sigma):
    r = max(1, int(math.ceil(3.5 * sigma)))
    k = _gauss_kernel1d(sigma, r)
    out = [0.0] * total
    for i in range(total):
        acc = 0.0
        for t in range(-r, r + 1):
            j = i + t
            if 0 <= j < total:
                acc += vol[j] * k[t + r]
        out[i] = acc
    return out


def _lcg(seed):
    s = seed & 0xFFFFFFFF
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s / 0x7FFFFFFF


def build_field(cfg):
    total = cfg["total"]
    interval = cfg["interval"]
    gain = cfg["gain"]
    baseline = cfg["baseline"]
    amp = cfg["amp"]
    width = cfg["width"]
    psf = cfg["psf"]
    drift = cfg["drift"]
    noise_sigma = cfg["noise"]
    seed = cfg["seed"]
    wide_width1 = cfg.get("wide_width1", cfg.get("wide_width", 66))
    wide_width2 = cfg.get("wide_width2", 58)
    rf_amp = cfg.get("rf_amp", 0.0)
    rf_period = cfg.get("rf_period", 0.0)
    occupancy = [0.0] * total
    rng = _lcg(seed)
    c = total // 3 + int((next(rng) - 0.5) * 60)
    for i in range(c - width // 2, c + width // 2):
        if 0 <= i < total:
            occupancy[i] = 1.0
    for i in range(c - width // 2 - 4, c - width // 2):
        if 0 <= i < total:
            occupancy[i] = max(occupancy[i], 0.38)
    for i in range(c + width // 2, c + width // 2 + 4):
        if 0 <= i < total:
            occupancy[i] = max(occupancy[i], 0.38)
    true_charge = sum(occupancy) * amp / 10.0 * interval * gain * 1000.0

    ideal = [amp * occ for occ in occupancy]
    blurred = _blur_1d(ideal, total, psf)

    # drift + RF sinusoidal
    field = []
    rng2 = _lcg(seed + 1)
    phase = next(rng2) * 2 * math.pi
    for i in range(total):
        n = (next(rng) - 0.5) * 2.0 * noise_sigma
        drift_val = drift * (i / total)
        rf = (
            rf_amp * math.sin(2 * math.pi * i / rf_period + phase) if rf_period else 0.0
        )
        field.append(baseline + drift_val + rf + blurred[i] + n)

    offset_dir = 1 if next(rng2) > 0.5 else -1
    ww1 = wide_width1
    amp_factor1 = (0.28 + next(rng2) * 0.14) * 0.55
    c2 = c + offset_dir * (width // 2 + ww1 // 2 + int(next(rng2) * 45 + 25))
    for i in range(c2 - ww1 // 2, c2 + ww1 // 2):
        if 0 <= i < total:
            field[i] += (
                amp * amp_factor1 * math.exp(-((i - c2) ** 2) / (2 * (ww1 / 4) ** 2))
            )

    ww2 = wide_width2
    amp_factor2 = (0.24 + next(rng2) * 0.14) * 0.52
    offset_dir2 = -offset_dir if next(rng2) > 0.3 else offset_dir
    c3 = c + offset_dir2 * (width // 2 + ww2 // 2 + int(next(rng2) * 50 + 60))
    if abs(c3 - c2) < (ww1 + ww2) // 2 + 15:
        c3 = c2 + offset_dir2 * ((ww1 + ww2) // 2 + 20)
    for i in range(c3 - ww2 // 2, c3 + ww2 // 2):
        if 0 <= i < total:
            field[i] += (
                amp * amp_factor2 * math.exp(-((i - c3) ** 2) / (2 * (ww2 / 4) ** 2))
            )

    n_dust = 3 + int(next(rng2) * 3)
    placed = 0
    attempts = 0
    while placed < n_dust and attempts < 250:
        attempts += 1
        c4 = int(next(rng2) * total)
        if (
            abs(c4 - c) < width + 25
            or abs(c4 - c2) < ww1 // 2 + 12
            or abs(c4 - c3) < ww2 // 2 + 12
        ):
            continue
        w = 4 + int(next(rng2) * 9)
        amp_dust = amp * (0.10 + next(rng2) * 0.16)
        for i in range(c4 - w // 2, c4 + w // 2):
            if 0 <= i < total:
                field[i] += amp_dust * (1.0 - abs(i - c4) / (w / 2))
        placed += 1

    return field, true_charge, c, c2, c3


def pack_pmar(cfg, field):
    total = cfg["total"]
    interval = cfg["interval"]
    gain = cfg["gain"]
    baseline = cfg["baseline"]
    offset = cfg.get("data_offset", 64)
    hdr = bytearray(offset)
    hdr[0:4] = MAGIC
    struct.pack_into("<I", hdr, 4, 1)
    struct.pack_into("<I", hdr, 8, total)
    struct.pack_into("<I", hdr, 12, offset)
    struct.pack_into("<f", hdr, 16, interval)
    struct.pack_into("<f", hdr, 20, gain)
    struct.pack_into("<I", hdr, 24, baseline)
    for i in range(28, offset):
        hdr[i] = (i * 73 + 19) % 256
    vals = [int(max(min(v, 32767), -32768)) for v in field]
    body = struct.pack("<%dh" % total, *vals)
    return bytes(hdr) + body


BASE_CONFIGS = {
    "heldout_1": dict(
        total=2150,
        data_offset=64,
        interval=0.00082,
        gain=1.03,
        baseline=104,
        amp=1360,
        width=34,
        psf=4.4,
        drift=13.0,
        noise=8.2,
        wide_width1=92,
        wide_width2=88,
        rf_amp=3.5,
        rf_period=180,
        seed=121,
    ),
    "heldout_2": dict(
        total=2400,
        data_offset=32,
        interval=0.00090,
        gain=1.13,
        baseline=99,
        amp=1280,
        width=32,
        psf=5.0,
        drift=19.0,
        noise=9.6,
        wide_width1=94,
        wide_width2=90,
        rf_amp=4.2,
        rf_period=210,
        seed=222,
    ),
    "heldout_3": dict(
        total=2200,
        data_offset=32,
        interval=0.00076,
        gain=0.98,
        baseline=109,
        amp=1490,
        width=36,
        psf=4.2,
        drift=12.0,
        noise=7.6,
        wide_width1=90,
        wide_width2=86,
        rf_amp=3.0,
        rf_period=160,
        seed=323,
    ),
    "heldout_4": dict(
        total=2600,
        data_offset=48,
        interval=0.00086,
        gain=1.08,
        baseline=104,
        amp=1340,
        width=34,
        psf=4.7,
        drift=16.0,
        noise=9.0,
        wide_width1=92,
        wide_width2=88,
        rf_amp=3.8,
        rf_period=190,
        seed=424,
    ),
    "heldout_extra": dict(
        total=2500,
        data_offset=80,
        interval=0.00081,
        gain=1.02,
        baseline=104,
        amp=1220,
        width=32,
        psf=5.2,
        drift=23.0,
        noise=10.6,
        wide_width1=90,
        wide_width2=84,
        rf_amp=4.5,
        rf_period=220,
        seed=525,
    ),
}

ALL_TEST_CONFIGS = [
    ("heldout_1", BASE_CONFIGS["heldout_1"]),
    ("heldout_2", BASE_CONFIGS["heldout_2"]),
    ("heldout_3", BASE_CONFIGS["heldout_3"]),
    ("heldout_4", BASE_CONFIGS["heldout_4"]),
    ("heldout_extra", BASE_CONFIGS["heldout_extra"]),
]


def test_script_exists():
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"


def _get_static_str_value(node):
    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, str):
            return v
        if isinstance(v, (bytes, bytearray)):
            try:
                return v.decode("utf-8", "ignore")
            except Exception:
                return None
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _get_static_str_value(node.left)
        right = _get_static_str_value(node.right)
        if left is not None and right is not None:
            return left + right
    elif isinstance(node, ast.JoinedStr):
        parts = []
        for vv in node.values:
            if isinstance(vv, ast.Constant) and isinstance(vv.value, str):
                parts.append(vv.value)
            else:
                cv = _get_static_str_value(vv)
                if cv is None:
                    return None
                parts.append(cv)
        return "".join(parts)
    return None


def test_from_scratch():
    src = open(SCRIPT, "r", encoding="utf-8", errors="ignore").read()
    tree = ast.parse(src, filename="solve.py")
    lower_src = src.lower()

    for bad in BANNED_OBFUSCATION_SUBSTRS:
        if bad in lower_src:
            raise AssertionError(f"banned obfuscation {bad!r}")
    if "base64" in lower_src:
        raise AssertionError("banned substring base64")
    if "sys.modules" in src:
        raise AssertionError("banned sys.modules access")
    if "import_module" in src:
        raise AssertionError("banned import_module usage")
    if "ctypes" in lower_src:
        raise AssertionError("banned ctypes reference")
    assert "chr(" not in src
    assert "base64" not in src.lower()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in BANNED_MODULES:
                    raise AssertionError(f"banned import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            root = mod.split(".")[0]
            if root in BANNED_MODULES:
                raise AssertionError(f"banned import from {mod}")
        elif isinstance(node, ast.Call):
            fn = node.func
            name = (
                fn.id
                if isinstance(fn, ast.Name)
                else (fn.attr if isinstance(fn, ast.Attribute) else "")
            )
            if name in BANNED_CALLS:
                raise AssertionError(f"banned call {name}")
            if isinstance(fn, ast.Attribute):
                if fn.attr in BANNED_ATTRS:
                    raise AssertionError(f"banned attr {fn.attr}")
        elif isinstance(node, ast.Attribute):
            if node.attr in BANNED_ATTRS:
                raise AssertionError(f"banned attr {node.attr}")

        s_val = _get_static_str_value(node)
        if s_val is not None:
            for bad in BANNED_SUBSTRINGS_SRC:
                if bad in s_val:
                    raise AssertionError(
                        f"banned substring {bad!r} in static value {s_val!r}"
                    )
            low = s_val.lower()
            for bm in BANNED_MODULES:
                if len(bm) <= 2:
                    continue
                if bm.lower() in low:
                    raise AssertionError(f"banned module substring {bm!r} in {s_val!r}")

        if isinstance(node, ast.Constant):
            v = node.value
            if isinstance(v, str):
                for bad in BANNED_SUBSTRINGS_SRC:
                    if bad in v:
                        raise AssertionError(f"banned substring {bad!r}")
                low = v.lower()
                if len(v) <= 128:
                    for bm in BANNED_MODULES:
                        if len(bm) <= 2:
                            continue
                        if bm.lower() in low:
                            raise AssertionError(
                                f"banned module name {bm!r} in string constant {v!r}"
                            )
            elif isinstance(v, (bytes, bytearray)):
                try:
                    decoded = (
                        v.decode("utf-8", "ignore")
                        if isinstance(v, (bytes, bytearray))
                        else ""
                    )
                except Exception:
                    decoded = ""
                for bad in BANNED_SUBSTRINGS_SRC:
                    if bad.encode() in (v if isinstance(v, bytes) else bytes(v)):
                        raise AssertionError(f"banned substring bytes {bad!r}")
                    if bad in decoded:
                        raise AssertionError(
                            f"banned substring {bad!r} in bytes literal"
                        )
                low = decoded.lower()
                for bm in BANNED_MODULES:
                    if len(bm) <= 2:
                        continue
                    if bm.lower() in low:
                        raise AssertionError(
                            f"banned module {bm!r} in bytes literal {decoded!r}"
                        )

        if isinstance(node, ast.Subscript):
            slice_node = node.slice
            if isinstance(slice_node, ast.Constant):
                sv = slice_node.value
                if isinstance(sv, str):
                    low = sv.lower()
                    for bm in BANNED_MODULES:
                        if len(bm) <= 2:
                            continue
                        if bm.lower() == low or bm.lower() in low:
                            raise AssertionError(
                                f"banned subscript {sv!r} accessing {bm}"
                            )
                    for bad in BANNED_SUBSTRINGS_SRC:
                        if bad.lower() in low:
                            raise AssertionError(
                                f"banned substring in subscript {sv!r}"
                            )
                elif isinstance(sv, (bytes, bytearray)):
                    try:
                        dec = (
                            sv.decode("utf-8", "ignore").lower()
                            if isinstance(sv, (bytes, bytearray))
                            else ""
                        )
                    except Exception:
                        dec = ""
                    for bm in BANNED_MODULES:
                        if len(bm) <= 2:
                            continue
                        if bm.lower() in dec:
                            raise AssertionError(f"banned bytes subscript {dec!r}")
            if isinstance(node.value, ast.Attribute) and node.value.attr == "modules":
                raise AssertionError("banned sys.modules subscript access")


def run_agent_secure(pmar_bytes, expected_uc, name="case"):
    with tempfile.TemporaryDirectory() as td:
        try:
            os.chmod(td, 0o755)
        except Exception:
            pass
        pmar_path = os.path.join(td, f"input_{os.urandom(4).hex()}.pmar")
        with open(pmar_path, "wb") as f:
            f.write(pmar_bytes)
        try:
            os.chmod(pmar_path, 0o644)
        except Exception:
            pass
        secure_code = textwrap.dedent(f"""
            import sys, os, runpy
            solve_path = sys.argv[1]
            pmar_path = sys.argv[2]
            BLOCKED_SUBSTRS = ["/tests", "test_outputs", "heldout", "_gen", "GEOM_TRUTH", "geometric_truth", "reference_volume"]
            def _to_str(p):
                if isinstance(p, (bytes, bytearray)):
                    try:
                        return p.decode('utf-8', 'ignore')
                    except Exception:
                        return str(p)
                return str(p)
            def is_blocked(p):
                s = _to_str(p)
                for b in BLOCKED_SUBSTRS:
                    if b in s:
                        return True
                try:
                    rp = os.path.realpath(s)
                    for b in BLOCKED_SUBSTRS:
                        if b in rp:
                            return True
                except:
                    pass
                return False
            def audit_hook(event, args):
                if event == "open":
                    path = args[0] if args else ""
                    if is_blocked(path):
                        raise RuntimeError(f"Blocked file access: {{path}}")
                    try:
                        sp = _to_str(path)
                        rp = os.path.realpath(sp)
                        if rp.startswith("/tests") or "/tests" in rp:
                            raise RuntimeError(f"Blocked realpath access: {{path}} -> {{rp}}")
                    except RuntimeError:
                        raise
                    except:
                        pass
                elif event in ("os.listdir", "os.scandir", "os.walk"):
                    path = args[0] if args else ""
                    if is_blocked(path):
                        raise RuntimeError(f"Blocked dir listing: {{path}}")
                    try:
                        sp = _to_str(path) if path else ""
                        rp = os.path.realpath(sp) if sp else ""
                        if rp in ("/", "/tests", "/tests/data") or rp.startswith("/tests"):
                            raise RuntimeError(f"Blocked dir listing realpath: {{path}} -> {{rp}}")
                    except RuntimeError:
                        raise
                    except:
                        pass
                    if _to_str(path) in ("", "/", "/tests", "/tests/data"):
                        raise RuntimeError(f"Blocked listing of sensitive dir: {{path}}")
                elif event.startswith("os."):
                    banned = {{"os.system","os.popen","os.spawnl","os.spawnle","os.spawnlp","os.spawnlpe","os.spawnv","os.spawnve","os.spawnvp","os.spawnvpe","os.exec","os.execl","os.execle","os.execlp","os.execlpe","os.execv","os.execve","os.execvp","os.execvpe","os.posix_spawn","os.posix_spawnp","os.fork","os.forkpty"}}
                    if event in banned:
                        raise RuntimeError(f"Blocked {{event}}")
                elif event.startswith("subprocess."):
                    raise RuntimeError(f"Blocked {{event}}")
                elif event.startswith("socket."):
                    raise RuntimeError(f"Blocked {{event}}")
                elif event == "import":
                    mod = args[0] if args else ""
                    base = mod.split(".")[0]
                    banned_imports = {{"numpy","scipy","skimage","cv2","PIL","pandas","torch","tensorflow","subprocess","socket","multiprocessing","glob","pathlib","os","io","posixpath","ntpath","genericpath","ctypes","importlib","runpy"}}
                    if base in banned_imports:
                        raise RuntimeError(f"Blocked import {{mod}}")
            sys.addaudithook(audit_hook)
            sys.argv = [solve_path, pmar_path]
            runpy.run_path(solve_path, run_name="__main__")
        """)
        secure_path = os.path.join(td, "_secure_runner.py")
        with open(secure_path, "w") as f:
            f.write(secure_code)
        try:
            os.chmod(secure_path, 0o644)
        except Exception:
            pass

        demote_fn = None
        try:
            pw = pwd.getpwnam("pmar_restricted_user")

            def _demote():
                try:
                    os.setgid(pw.pw_gid)
                    try:
                        os.setgroups([])
                    except Exception:
                        pass
                    os.setuid(pw.pw_uid)
                    os.umask(0o077)
                except Exception:
                    pass

            demote_fn = _demote
        except KeyError:
            demote_fn = None
        except Exception:
            demote_fn = None

        proc = subprocess.run(
            ["python3", secure_path, SCRIPT, pmar_path],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=td,
            preexec_fn=demote_fn,
        )
        assert proc.returncode == 0, (
            f"fail {name} (expected {expected_uc:.2f} uC)\\nstdout:\\n{proc.stdout}\\nstderr:\\n{proc.stderr}"
        )
        lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
        assert lines, f"no output for {name}"
        last = lines[-1]
        try:
            got = float(last)
        except ValueError:
            m = re.findall(r"[-+]?\\d*\\.\\d+|[-+]?\\d+", last)
            assert m, f"no float in last line: {last}"
            got = float(m[-1])
        return got


@pytest.mark.parametrize("cfg_name,cfg", ALL_TEST_CONFIGS)
def test_heldout_secure(cfg_name, cfg):
    field, true_charge, _, _, _ = build_field(cfg)
    pmar_bytes = pack_pmar(cfg, field)
    got = run_agent_secure(pmar_bytes, true_charge, name=cfg_name)
    assert abs(got - true_charge) <= REL_TOL * true_charge, (
        f"{cfg_name}: got {got:.4f} uC expected {true_charge:.4f} ±{REL_TOL * 100}%"
    )


def test_randomized_extra():
    cfg = dict(
        total=2300,
        data_offset=32,
        interval=0.00084,
        gain=1.03,
        baseline=104,
        amp=1300,
        width=44,
        psf=4.5,
        drift=13.5,
        noise=8.2,
        wide_width1=68,
        wide_width2=60,
        rf_amp=3.6,
        rf_period=185,
        seed=789,
    )
    field, true_charge, _, _, _ = build_field(cfg)
    pmar_bytes = pack_pmar(cfg, field)
    got = run_agent_secure(pmar_bytes, true_charge, name="randomized_extra")
    assert abs(got - true_charge) <= REL_TOL * true_charge


def test_global_conservation_shortcut_fails_on_wide_bump():
    cfg = BASE_CONFIGS["heldout_1"]
    field, true_charge, main_c, wide_c, wide_c2 = build_field(cfg)

    def naive_global():
        sv = sorted(field)
        bg = sv[len(sv) // 2]
        r = [v - bg for v in field]
        total = sum(r)
        top = sorted(r, reverse=True)[:8]
        amp = sum(top) / len(top) if top else 1
        interval = cfg["interval"]
        gain = cfg["gain"]
        return total / 10.0 * interval * gain * 1000.0 if amp > 0 else 0

    got = naive_global()
    assert abs(got - true_charge) > REL_TOL * true_charge, (
        f"Expected naive global to fail on wide bump, got {got:.2f} vs truth {true_charge:.2f}"
    )


def test_count_based_clustering_fails_on_wide_bump():
    """Dual wide humps together have more samples than main but less charge."""
    cfg = BASE_CONFIGS["heldout_1"]
    field, true_charge, main_c, wide_c, wide_c2 = build_field(cfg)

    def count_based_picker():
        sv = sorted(field)
        bg = sv[len(sv) // 2]
        lo = sv[: len(sv) // 2]
        med_lo = lo[len(lo) // 2]
        mad = sorted(abs(v - med_lo) for v in lo)[len(lo) // 2]
        sigma = max(1.0, 1.4826 * mad)
        r = [v - bg for v in field]
        thr = 3.5 * sigma
        n = len(field)
        visited = [False] * n
        comps = []
        for i in range(n):
            if r[i] <= thr or visited[i]:
                continue
            stack = [i]
            visited[i] = True
            comp = []
            mass = 0.0
            while stack:
                cur = stack.pop()
                comp.append(cur)
                mass += r[cur]
                for nb in (cur - 1, cur + 1):
                    if 0 <= nb < n and not visited[nb] and r[nb] > thr:
                        visited[nb] = True
                        stack.append(nb)
            comps.append((comp, mass, len(comp)))
        if not comps:
            return 0.0
        longest = max(comps, key=lambda x: x[2])
        total_res = sum(r[idx] for idx in longest[0])
        return total_res / 10.0 * cfg["interval"] * cfg["gain"] * 1000.0

    got = count_based_picker()
    assert abs(got - true_charge) > REL_TOL * true_charge, (
        f"Expected count-based to fail, got {got:.2f} vs truth {true_charge:.2f}"
    )


def test_dual_wide_bump_count_trap():
    """Specifically tests that two wide humps combined count > main count."""
    cfg = BASE_CONFIGS["heldout_2"]
    field, true_charge, main_c, wide_c, wide_c2 = build_field(cfg)
    # wide humps widths from config
    ww1 = cfg["wide_width1"]
    ww2 = cfg["wide_width2"]
    main_w = cfg["width"]
    # The sum of wide widths should exceed main width, making count trap real
    assert ww1 + ww2 > main_w + 10, (
        f"dual wide trap not set: {ww1}+{ww2} vs main {main_w}"
    )


def test_cheating_attempt_pathlib_construction_fails():
    cheating_code = """
import pathlib
p = pathlib.Path("/") / "tests" / "test_outputs.py"
print(p.read_text()[:10])
"""
    tree = ast.parse(cheating_code)
    banned_import_found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] in BANNED_MODULES:
                    banned_import_found = True
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in BANNED_MODULES:
                banned_import_found = True
    assert banned_import_found, "cheating pathlib import should be banned"


def test_cheating_attempt_chr_construction_fails():
    cheating_code = "print(chr(47)+chr(116)+chr(101)+chr(115)+chr(116)+chr(115))"
    tree = ast.parse(cheating_code)
    src = cheating_code
    low = src.lower()
    assert "chr(" in low, "chr construction should be flagged"
