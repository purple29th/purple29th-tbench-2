"""Verify /app/solve.py reports total leaked duration ms for WKLK trace.
Hardened v0.14: foundry-inspired difficulty + thread 0 system force-release.

- No ground_truth.json, expected computed directly from wklk via oracle _compute_true
- Bans base64/binascii/codecs and encoded path bypass, enforces strict open(argv) dataflow
- Banned modules include os, pathlib, io, etc like foundry
- Adds discriminators: per-pair last vs global, final vs first, duplicate updates last, cross-thread heavy, stable order, thread 0 global force-release
- Larger traces 20k-50k events, 1500-2500 ids, 24 threads including thread 0, 40% same-ts, 30% negative, 8-12 cross-thread, plus system thread 0 force-releases
"""

import ast
import base64
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import random

import pytest

SCRIPT = "/app/solve.py"
HELDOUTS = [
    "/tests/data/heldout_1.wklk",
    "/tests/data/heldout_2.wklk",
    "/tests/data/heldout_3.wklk",
    "/tests/data/heldout_4.wklk",
    "/tests/data/heldout_5.wklk",
    "/tests/data/heldout_6.wklk",
    "/tests/data/heldout_7.wklk",
    "/tests/data/heldout_8.wklk",
    "/tests/data/heldout_9.wklk",
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
    "base64",
    "binascii",
    "codecs",
    "builtins",
    "zlib",
    "posixpath",
    "ntpath",
    "genericpath",
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
BANNED_DECODE_ATTRS = {
    "b64decode",
    "b32decode",
    "b16decode",
    "b85decode",
    "a85decode",
    "decodebytes",
    "decodestring",
    "decompress",
    "b64encode",
}
BANNED_TOKENS_FOR_PATH = [
    "/tests",
    "test_outputs",
    "heldout",
    "_gen",
    "reference",
    "ground_truth",
    "scene.wklk",
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
ALLOWED_DUNDER_ATTRS = {"__name__", "__main__"}

ALLOWED_PATH_NAMES = {
    "path",
    "file_path",
    "filepath",
    "input_path",
    "scan_path",
    "fname",
    "filename",
    "fpath",
    "file",
    "input_file",
    "wklk_path",
    "trace_path",
}


def _parse_wklk_file(path):
    data = open(path, "rb").read()
    if len(data) < 16 or data[:4] != b"WKLK":
        raise ValueError("bad magic")
    count = struct.unpack_from("<I", data, 8)[0]
    off = struct.unpack_from("<I", data, 12)[0]
    events = []
    o = off
    for _ in range(count):
        if o + 16 > len(data):
            break
        eid, etype, ts, tid = struct.unpack_from("<iIII", data, o)
        o += 16
        events.append((eid, etype, ts, tid))
    return events


def _compute_true(events):
    # v0.21: even ref-counted, odd binary, plus global all-clear id0
    ev = sorted(events, key=lambda x: x[2])
    held = {}
    held_count = {}
    first_acq = {}
    last_ts = {}
    for eid, etype, ts, tid in ev:
        if tid == 0 and etype == 0:
            if eid == 0:
                key0 = (0, 0)
                if key0 not in last_ts or ts > last_ts[key0]:
                    last_ts[key0] = ts
                for kk in list(held.keys()):
                    if held.get(kk, False):
                        held[kk] = False
                        first_acq[kk] = None
                        held_count[kk] = 0
                continue
            key0 = (eid, 0)
            if key0 not in last_ts or ts > last_ts[key0]:
                last_ts[key0] = ts
            for k in list(held.keys()):
                if k[0] == eid and held.get(k, False):
                    held[k] = False
                    first_acq[k] = None
                    held_count[k] = 0
            continue
        key = (eid, tid)
        if key not in last_ts or ts > last_ts[key]:
            last_ts[key] = ts
        is_even = (abs(eid) % 2 == 0)
        if etype == 1:
            if is_even:
                cnt = held_count.get(key, 0) + 1
                held_count[key] = cnt
                if cnt == 1:
                    held[key] = True
                    first_acq[key] = ts
            else:
                if held.get(key, False):
                    continue
                held[key] = True
                first_acq[key] = ts
                held_count[key] = 1
        else:
            if is_even:
                cnt = held_count.get(key, 0)
                if cnt == 0:
                    continue
                cnt -= 1
                held_count[key] = cnt
                if cnt == 0:
                    held[key] = False
                    first_acq[key] = None
            else:
                if not held.get(key, False):
                    continue
                held[key] = False
                first_acq[key] = None
                held_count[key] = 0
    total = 0
    for k, is_held in held.items():
        if is_held:
            f = first_acq.get(k)
            if f is not None:
                total += last_ts[k] - f
    return total




def ground_truth_leak(path):
    events = _parse_wklk_file(path)
    return _compute_true(events)


def run_agent(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    with tempfile.TemporaryDirectory() as td:
        neutral = os.path.join(td, "scan.wklk")
        shutil.copyfile(path, neutral)
        iso = os.path.join(td, "solve.py")
        shutil.copyfile(SCRIPT, iso)
        env = os.environ.copy()
        env["PYTHONPATH"] = td
        proc = subprocess.run(
            [sys.executable, iso, neutral],
            capture_output=True,
            text=True,
            timeout=90,
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
    assert m, f"no numeric leak on last line: {last!r}"
    return int(m[-1])


def run_agent_bytes(data_bytes):
    assert os.path.exists(SCRIPT)
    with tempfile.TemporaryDirectory() as td:
        fpath = os.path.join(td, "scan.wklk")
        open(fpath, "wb").write(data_bytes)
        iso = os.path.join(td, "solve.py")
        shutil.copyfile(SCRIPT, iso)
        env = os.environ.copy()
        env["PYTHONPATH"] = td
        proc = subprocess.run(
            [sys.executable, iso, fpath],
            capture_output=True,
            text=True,
            timeout=90,
            cwd=td,
            env=env,
        )
    assert proc.returncode == 0, (
        f"agent failed\nstdout:{proc.stdout}\nstderr:{proc.stderr}"
    )
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines
    m = re.findall(r"-?\d+", lines[-1])
    assert m
    return int(m[-1])


def _pack_wklk(events, offset=64):
    n = len(events)
    hdr = bytearray(offset)
    hdr[0:4] = b"WKLK"
    struct.pack_into("<I", hdr, 4, 1)
    struct.pack_into("<I", hdr, 8, n)
    struct.pack_into("<I", hdr, 12, offset)
    for i in range(16, offset):
        if i % 17 == 0 and i + 4 < offset:
            hdr[i : i + 4] = b"WKLK"
        else:
            hdr[i] = (i * 37 + 11 + (i * i)) % 256
    body = bytearray()
    for eid, etype, ts, tid in events:
        body += struct.pack("<iIII", eid, etype, ts, tid)
    return bytes(hdr) + bytes(body)


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


def _get_const_str(node):
    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, str):
            return v
        if isinstance(v, (bytes, bytearray)):
            try:
                return v.decode("utf-8", errors="ignore")
            except Exception:
                return None
        return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _get_const_str(node.left)
        right = _get_const_str(node.right)
        if left is not None and right is not None:
            return left + right
        return None
    if isinstance(node, ast.JoinedStr):
        parts = []
        for p in node.values:
            if isinstance(p, ast.Constant) and isinstance(p.value, str):
                parts.append(p.value)
            else:
                return None
        return "".join(parts) if parts else None
    return None


def _is_argv_one(node):
    if isinstance(node, ast.Subscript):
        val = node.value
        if isinstance(val, ast.Attribute):
            if (
                isinstance(val.value, ast.Name)
                and val.value.id == "sys"
                and val.attr == "argv"
            ):
                sl = node.slice
                if isinstance(sl, ast.Constant) and sl.value == 1:
                    return True
                if isinstance(sl, ast.Index):
                    inner = sl.value
                    if isinstance(inner, ast.Constant) and inner.value == 1:
                        return True
    return False


def _try_b64_decode(s):
    s = s.strip()
    if len(s) < 16:
        return None
    b64chars = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r"
    )
    if not all(c in b64chars for c in s):
        return None
    try:
        missing = len(s) % 4
        if missing:
            s_padded = s + "=" * (4 - missing)
        else:
            s_padded = s
        decoded = base64.b64decode(s_padded, validate=False)
        txt = decoded.decode("utf-8", errors="ignore")
        return txt
    except Exception:
        return None


def test_from_scratch():
    src = open(SCRIPT, "r", encoding="utf-8", errors="ignore").read()
    tree = ast.parse(src, filename=SCRIPT)

    param_names = set(ALLOWED_PATH_NAMES)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args:
                param_names.add(arg.arg)
            for arg in node.args.kwonlyargs:
                param_names.add(arg.arg)
            if node.args.vararg:
                param_names.add(node.args.vararg.arg)

    argv_derived = set()
    assigned_names = set()
    tainted = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned_names.add(target.id)
                    if _is_argv_one(node.value):
                        argv_derived.add(target.id)
                    elif isinstance(node.value, ast.Name):
                        if node.value.id in argv_derived or (
                            node.value.id in param_names
                            and node.value.id not in tainted
                        ):
                            argv_derived.add(target.id)
                    elif isinstance(node.value, ast.Call):
                        func = node.value.func
                        call_name = ""
                        if isinstance(func, ast.Attribute):
                            call_name = func.attr
                        elif isinstance(func, ast.Name):
                            call_name = func.id
                        if (
                            call_name in BANNED_DECODE_ATTRS
                            or call_name in BANNED_CALLS
                        ):
                            raise AssertionError(
                                f"banned decode/call {call_name} used to assign {target.id}"
                            )
                        for arg in node.value.args:
                            const_str = _get_const_str(arg)
                            if const_str:
                                dec = _try_b64_decode(const_str)
                                if dec:
                                    low = dec.lower()
                                    for banned in BANNED_TOKENS_FOR_PATH:
                                        if banned.lower() in low:
                                            raise AssertionError(
                                                f"base64 encoded banned path {banned} in assignment to {target.id}: {const_str[:40]}"
                                            )
                        tainted.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name):
                assigned_names.add(target.id)
                if node.value and _is_argv_one(node.value):
                    argv_derived.add(target.id)
                else:
                    tainted.add(target.id)
        elif isinstance(node, ast.For):
            if isinstance(node.target, ast.Name):
                assigned_names.add(node.target.id)
                tainted.add(node.target.id)

    open_calls = []

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
            if isinstance(fn, ast.Attribute):
                assert fn.attr not in BANNED_DECODE_ATTRS, (
                    f"banned decode attr {fn.attr} not allowed"
                )
            if name == "open" or (isinstance(fn, ast.Attribute) and fn.attr == "open"):
                open_calls.append(node)
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
                    assert False, f"dunder not allowed ({attr})"
            if isinstance(node.value, ast.Name) and node.value.id == "os":
                assert attr not in BANNED_OS_ATTRS, f"banned os.{attr} usage"
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            const_val = _get_const_str(node)
            if const_val:
                low = const_val.lower()
                for banned in BANNED_TOKENS_FOR_PATH:
                    assert banned.lower() not in low, (
                        f"forbidden path via concatenation {banned!r} in {const_val!r}"
                    )
                if "/tests" in low or "ground_truth" in low:
                    assert False, f"forbidden absolute path via concat {const_val!r}"

    for lit in _iter_string_literals(tree):
        low = lit.lower()
        for banned in BANNED_TOKENS_FOR_PATH:
            assert banned.lower() not in low, f"forbidden path {banned!r} in {lit!r}"
        if "ground" in low and "truth" in low:
            assert False, f"forbidden ground_truth mention {lit!r}"
        dec = _try_b64_decode(lit)
        if dec:
            dlow = dec.lower()
            for banned in BANNED_TOKENS_FOR_PATH:
                if banned.lower() in dlow:
                    assert False, (
                        f"base64 encoded banned path {banned!r} decoded from {lit[:40]!r}"
                    )

    for call in open_calls:
        if not call.args:
            continue
        first_arg = call.args[0]
        if _is_argv_one(first_arg):
            continue
        if isinstance(first_arg, ast.Name):
            fid = first_arg.id
            if fid in argv_derived:
                continue
            if fid in param_names and fid not in assigned_names and fid not in tainted:
                continue
            assert False, (
                f"open with disallowed variable {fid!r}. Only open(sys.argv[1]) or variable directly derived from sys.argv[1] or unmodified function param is allowed. Found assigned={fid in assigned_names} tainted={fid in tainted} argv_derived={argv_derived}"
            )
        const_val = _get_const_str(first_arg)
        if const_val is not None:
            assert False, f"open with constant path {const_val!r} not allowed"
        if isinstance(first_arg, ast.BinOp):
            assert False, "open with dynamically constructed path not allowed"
        if isinstance(first_arg, ast.Call):
            assert False, "open with call-constructed path not allowed"

    assert len(open_calls) <= 2, (
        f"too many open calls {len(open_calls)}, only 1-2 allowed"
    )


@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    # skip if file not present (for local dev without all heldouts)
    if not os.path.exists(path):
        pytest.skip(f"{path} not present")
    got = run_agent(path)
    expected = ground_truth_leak(path)
    assert got == expected, f"{os.path.basename(path)}: got {got} expected {expected}"


def test_varied_offset_hardcode_guard():
    events = [(1, 1, 100, 1), (1, 1, 120, 1)]
    expected = _compute_true(events)
    assert expected == 20
    for offset in [16, 20, 24, 32, 40, 64, 96, 128, 192, 256]:
        data = _pack_wklk(events, offset=offset)
        got = run_agent_bytes(data)
        assert got == expected, f"offset {offset} failed: got {got} expected {expected}"


def test_reacquire_final_interval_semantics():
    events = [
        (1, 1, 10, 1),
        (1, 0, 20, 1),
        (1, 1, 30, 1),
        (1, 1, 40, 1),
    ]
    expected = _compute_true(events)
    assert expected == 10
    for offset in [16, 64, 128, 192]:
        data = _pack_wklk(events, offset=offset)
        got = run_agent_bytes(data)
        assert got == expected, (
            f"reacquire semantics failed at offset {offset}: got {got} expected {expected}"
        )


def test_cross_thread_and_dedup():
    events = [
        (1, 1, 10, 1),
        (1, 1, 12, 1),
        (1, 0, 20, 1),
        (2, 1, 15, 2),
        (2, 0, 25, 1),
        (2, 1, 30, 2),
    ]
    expected = _compute_true(events)
    assert expected == 15
    data = _pack_wklk(events, offset=40)
    got = run_agent_bytes(data)
    assert got == expected


def test_per_pair_last_vs_global():
    """Discriminator like foundry speck heavy: per-pair last observation vs global trace end."""
    events = [
        (1, 1, 10, 1),
        (1, 1, 50, 1),
        (99, 1, 1000, 2),
        (99, 0, 2000, 2),
        (100, 1, 5000, 3),
        (100, 0, 10000, 3),
    ]
    expected = _compute_true(events)
    assert expected == 40
    naive_global = 10000 - 10
    assert naive_global != expected
    assert naive_global > expected + 1000
    data = _pack_wklk(events, offset=32)
    got = run_agent_bytes(data)
    assert got == expected, (
        f"per-pair last vs global failed: got {got} expected {expected}"
    )


def test_final_interval_vs_first_ever():
    events = [
        (1, 1, 10, 1),
        (1, 0, 20, 1),
        (1, 1, 1000, 1),
        (1, 1, 1050, 1),
    ]
    expected = _compute_true(events)
    assert expected == 50
    naive_first = 1050 - 10
    assert naive_first != expected
    assert naive_first > expected + 500
    data = _pack_wklk(events, offset=64)
    got = run_agent_bytes(data)
    assert got == expected, f"final vs first ever failed: got {got} expected {expected}"


def test_duplicate_updates_last_ts():
    events = [
        (1, 1, 10, 1),
        (1, 1, 500, 1),
    ]
    expected = _compute_true(events)
    assert expected == 490
    data = _pack_wklk(events, offset=40)
    got = run_agent_bytes(data)
    assert got == expected, f"duplicate last_ts failed: got {got} expected {expected}"


def test_cross_thread_heavy():
    events = []
    base = 100
    events.append((1, 1, base, 1))
    events.append((1, 1, 800, 1))
    for other_tid in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
        events.append((1, 0, base + 200, other_tid))
        events.append((1, 0, base + 400, other_tid))
    events.append((2, 1, 150, 2))
    events.append((2, 0, 250, 2))
    events.append((2, 0, 200, 3))
    expected = _compute_true(events)
    assert expected == 700
    data = _pack_wklk(events, offset=96)
    got = run_agent_bytes(data)
    assert got == expected, f"cross-thread heavy failed: got {got} expected {expected}"


def test_multi_thread_same_id_independent_holds():
    events = [
        (1, 1, 10, 1),
        (1, 1, 60, 1),
        (1, 1, 15, 2),
        (1, 1, 115, 2),
        (1, 1, 20, 3),
        (1, 1, 70, 3),
    ]
    expected = _compute_true(events)
    assert expected == 200, f"test setup error expected 200 got {expected}"
    data = _pack_wklk(events, offset=40)
    got = run_agent_bytes(data)
    assert got == expected, (
        f"multi-thread same-id failed: got {got} expected {expected}"
    )

    events2 = [
        (5, 1, 10, 1),
        (5, 1, 90, 1),
        (5, 1, 20, 2),
        (5, 1, 120, 2),
        (5, 0, 30, 3),
        (5, 0, 40, 4),
    ]
    expected2 = _compute_true(events2)
    assert expected2 == 180
    data2 = _pack_wklk(events2, offset=32)
    got2 = run_agent_bytes(data2)
    assert got2 == expected2, (
        f"multi-thread same-id with cross noise failed: got {got2} expected {expected2}"
    )


def test_stable_order_matters():
    events_file_order_A = [
        (1, 1, 10, 1),
        (1, 0, 100, 1),
        (1, 1, 100, 1),
        (1, 1, 150, 1),
    ]
    expected_A = _compute_true(events_file_order_A)
    assert expected_A == 50

    events_file_order_B = [
        (1, 1, 10, 1),
        (1, 1, 100, 1),
        (1, 0, 100, 1),
        (1, 1, 150, 1),
    ]
    expected_B = _compute_true(events_file_order_B)
    assert expected_B == 0
    assert expected_A != expected_B, "stable order test setup must differ"

    data_A = _pack_wklk(events_file_order_A, offset=40)
    got_A = run_agent_bytes(data_A)
    assert got_A == expected_A, (
        f"stable order A failed: got {got_A} expected {expected_A}"
    )

    data_B = _pack_wklk(events_file_order_B, offset=40)
    got_B = run_agent_bytes(data_B)
    assert got_B == expected_B, (
        f"stable order B failed: got {got_B} expected {expected_B}"
    )


def test_thread_0_global_force_release():
    """Thread 0 release is global force-release for that id, unlike normal cross-thread no-ops."""
    # Two threads leak same id, then system thread 0 releases -> both cleared, final leak 0
    events = [
        (1, 1, 10, 1),
        (1, 1, 20, 2),
        (1, 0, 30, 0),  # global release clears both (1,1) and (1,2)
    ]
    expected = _compute_true(events)
    assert expected == 0
    # Without handling thread 0 global, naive per-thread would get 10+10=20? Actually 10? Let's compute:
    # (1,1) acq 10 last 10, (1,2) acq 20 last 20, both still held if ignoring global => 0+0? No, if single acq no later activity age 0, so both 0, total 0. Need better case with later dup.
    # Better: leak with later observation, then global release
    events2 = [
        (1, 1, 10, 1),
        (1, 1, 100, 1),  # leak 90 for (1,1)
        (1, 1, 20, 2),
        (1, 1, 150, 2),  # leak 130 for (1,2) total 220 if not cleared
        (1, 0, 200, 0),  # global release clears both => 0
    ]
    expected2 = _compute_true(events2)
    assert expected2 == 0
    # Naive per-thread ignoring global would get 90+130=220
    naive_ignore_global = 90 + 130
    assert naive_ignore_global != expected2

    data = _pack_wklk(events2, offset=64)
    got = run_agent_bytes(data)
    assert got == expected2, (
        f"thread 0 global force-release failed: got {got} expected {expected2}"
    )

    # Second scenario: leak, global release, then re-acquire and leak again
    events3 = [
        (5, 1, 10, 1),
        (5, 1, 50, 1),  # would be 40 if not cleared
        (5, 0, 60, 0),  # global clears
        (5, 1, 100, 1),
        (5, 1, 180, 1),  # final leak 80
    ]
    expected3 = _compute_true(events3)
    assert expected3 == 80
    data3 = _pack_wklk(events3, offset=40)
    got3 = run_agent_bytes(data3)
    assert got3 == expected3, (
        f"thread 0 re-acquire after global failed: got {got3} expected {expected3}"
    )

    # Third: global release for one id should not affect other ids
    events4 = [
        (1, 1, 10, 1),
        (1, 1, 100, 1),  # leak 90 for id 1
        (2, 1, 20, 1),
        (2, 1, 120, 1),  # leak 100 for id 2
        (1, 0, 150, 0),  # global release only id 1 => clears id1, id2 still leaks 100
    ]
    expected4 = _compute_true(events4)
    assert expected4 == 100
    data4 = _pack_wklk(events4, offset=32)
    got4 = run_agent_bytes(data4)
    assert got4 == expected4, (
        f"thread 0 selective id failed: got {got4} expected {expected4}"
    )


def test_randomized_dynamic():
    """5 random traces with heavy patterns including thread 0 force-releases."""
    rnd = random.Random(42)
    offsets = [16, 20, 24, 32, 40, 64, 96, 128, 192, 256]
    for i in range(5):
        ev = []
        num_ids = rnd.randint(15, 25)
        for id_ in range(1, num_ids + 1):
            base = rnd.randint(0, 5000)
            tids = rnd.sample(
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], rnd.randint(2, 6)
            )
            for tid in tids:
                pat = rnd.choice([0, 1, 2, 3, 4, 5, 6, 7, 9])
                if pat == 0:
                    a = base + rnd.randint(0, 100)
                    r = a + rnd.randint(10, 100)
                    ev.append((id_, 1, a, tid))
                    ev.append((id_, 0, r, tid))
                elif pat == 1:
                    a = base + rnd.randint(0, 100)
                    ev.append((id_, 1, a, tid))
                    if rnd.random() < 0.8:
                        ev.append((id_, 1, a + rnd.randint(1, 20), tid))
                    if rnd.random() < 0.6:
                        ev.append((id_, 1, a + rnd.randint(100, 500), tid))
                elif pat == 2:
                    a = base + rnd.randint(0, 100)
                    ev.append((id_, 1, a, tid))
                    ev.append((id_, 1, a + 5, tid))
                    ev.append((id_, 0, a + 20, tid))
                elif pat == 3:
                    a = base + rnd.randint(0, 100)
                    ev.append((id_, 1, a, tid))
                    for _ in range(rnd.randint(3, 8)):
                        other = rnd.choice(
                            [t for t in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] if t != tid]
                        )
                        ev.append((id_, 0, a + rnd.randint(20, 200), other))
                elif pat == 4:
                    a1 = base + rnd.randint(0, 100)
                    r1 = a1 + 20
                    a2 = r1 + 10
                    ev.append((id_, 1, a1, tid))
                    ev.append((id_, 0, r1, tid))
                    ev.append((id_, 1, a2, tid))
                    if rnd.random() < 0.8:
                        ev.append((id_, 1, a2 + rnd.randint(5, 15), tid))
                    if rnd.random() < 0.6:
                        ev.append((id_, 1, a2 + rnd.randint(100, 300), tid))
                elif pat == 5:
                    a1 = base + rnd.randint(0, 100)
                    r1 = a1 + rnd.randint(20, 50)
                    a2 = r1 + rnd.randint(10, 50)
                    r2 = a2 + rnd.randint(20, 80)
                    ev.append((id_, 1, a1, tid))
                    ev.append((id_, 0, r1, tid))
                    ev.append((id_, 1, a2, tid))
                    ev.append((id_, 0, r2, tid))
                else:
                    a = base + rnd.randint(0, 50)
                    ev.append((id_, 1, a, tid))
                    ev.append((id_, 1, a + rnd.randint(30, 80), tid))
                # add system force-release trap 20% of time
                if rnd.random() < 0.20:
                    # force-release this id from system thread 0 after some time
                    force_t = base + rnd.randint(300, 600)
                    ev.append((id_, 0, force_t, 0))
                    # re-acquire after force-release 50% chance
                    if rnd.random() < 0.5:
                        reacq = force_t + rnd.randint(20, 100)
                        ev.append((id_, 1, reacq, tid))
                        if rnd.random() < 0.6:
                            ev.append((id_, 1, reacq + rnd.randint(50, 200), tid))
        for _ in range(rnd.randint(15, 30)):
            ev.append(
                (rnd.randint(1000, 5000), 0, rnd.randint(0, 5000), rnd.randint(0, 12))
            )
        expected = _compute_true(ev)
        offset = rnd.choice(offsets)
        data = _pack_wklk(ev, offset=offset)
        got = run_agent_bytes(data)
        assert got == expected, (
            f"random dynamic {i} offset {offset} failed: got {got} expected {expected}"
        )


def test_timestamp_order_required():
    rnd = random.Random(123)
    ev = []
    for i in range(80):
        ev.append(
            (i % 8 + 1, rnd.choice([0, 1]), rnd.randint(0, 500), rnd.randint(0, 12))
        )
    rnd.shuffle(ev)
    expected = _compute_true(ev)

    def file_order_true(ev2):
        held = {}
        first = {}
        last = {}
        for eid, etype, ts, tid in ev2:
            if tid == 0 and etype == 0:
                key0 = (eid, 0)
                if key0 not in last or ts > last[key0]:
                    last[key0] = ts
                for k in list(held.keys()):
                    if k[0] == eid and held.get(k, False):
                        held[k] = False
                        first[k] = None
                continue
            key = (eid, tid)
            if key not in last or ts > last[key]:
                last[key] = ts
            if etype == 1:
                if held.get(key, False):
                    continue
                held[key] = True
                first[key] = ts
            else:
                if not held.get(key, False):
                    continue
                held[key] = False
                first[key] = None
        total = 0
        for k, v in held.items():
            if v:
                f = first.get(k)
                if f is not None:
                    total += last[k] - f
        return total

    data = _pack_wklk(ev, offset=64)
    got = run_agent_bytes(data)
    assert got == expected, (
        f"timestamp sorting required: got {got} expected {expected} file-order {file_order_true(ev)}"
    )


def test_negative_ids():
    events = [
        (-5, 1, 10, 1),
        (-5, 1, 20, 1),
        (-10, 1, 15, 2),
        (-10, 0, 25, 2),
        (-5, 1, 800, 1),
    ]
    expected = _compute_true(events)
    assert expected == 790
    data = _pack_wklk(events, offset=32)
    got = run_agent_bytes(data)
    assert got == expected


def test_same_timestamp_stable_order():
    events_file_order = [
        (1, 1, 100, 1),
        (1, 0, 100, 1),
        (2, 0, 100, 1),
        (2, 1, 100, 1),
    ]
    expected = _compute_true(events_file_order)
    assert expected == 0
    data = _pack_wklk(events_file_order, offset=24)
    got = run_agent_bytes(data)
    assert got == expected

    events2 = [
        (1, 1, 50, 1),
        (1, 0, 100, 1),
        (1, 1, 100, 1),
    ]
    expected2 = _compute_true(events2)
    data2 = _pack_wklk(events2, offset=40)
    got2 = run_agent_bytes(data2)
    assert got2 == expected2


def test_thread_0_with_same_timestamp_order():
    """Within same ms, global release order matters relative to other events."""
    events_A = [
        (1, 1, 10, 1),
        (1, 0, 100, 0),
        (1, 1, 100, 1),
        (1, 1, 150, 1),
    ]
    expected_A = _compute_true(events_A)
    assert expected_A == 50

    events_B = [
        (1, 1, 10, 1),
        (1, 1, 100, 1),
        (1, 0, 100, 0),
        (1, 1, 150, 1),
    ]
    expected_B = _compute_true(events_B)
    assert expected_B == 0
    assert expected_A != expected_B

    data_A = _pack_wklk(events_A, offset=40)
    got_A = run_agent_bytes(data_A)
    assert got_A == expected_A, (
        f"thread0 same-ts A failed: got {got_A} expected {expected_A}"
    )

    data_B = _pack_wklk(events_B, offset=40)
    got_B = run_agent_bytes(data_B)
    assert got_B == expected_B, (
        f"thread0 same-ts B failed: got {got_B} expected {expected_B}"
    )


def test_global_all_clear_id_0():
    """Hidden Doze entry: release id 0 from thread 0 clears ALL ids, not just id 0. Must be inferred from sample."""
    # Two ids leak, then global all-clear (0,0,0) clears both, total 0
    events = [
        (1, 1, 10, 1),
        (1, 1, 100, 1),
        (2, 1, 20, 2),
        (2, 1, 150, 2),
        (0, 0, 200, 0),
    ]
    expected = _compute_true(events)
    assert expected == 0, f"global all-clear should clear all, got {expected}"
    data = _pack_wklk(events, offset=32)
    got = run_agent_bytes(data)
    assert got == expected, f"global all-clear failed: got {got} expected {expected}"

    # After global clear, re-acquire and leak again
    events2 = [
        (1, 1, 10, 1),
        (1, 1, 50, 1),
        (0, 0, 60, 0),
        (1, 1, 100, 1),
        (1, 1, 180, 1),
        (2, 1, 110, 2),
        (2, 1, 200, 2),
    ]
    expected2 = _compute_true(events2)
    # first interval cleared, final: (1,1) 80 + (2,2) 90 = 170
    assert expected2 == 170, f"setup error got {expected2}"
    data2 = _pack_wklk(events2, offset=64)
    got2 = run_agent_bytes(data2)
    assert got2 == expected2, (
        f"global all-clear re-acquire failed: got {got2} expected {expected2}"
    )

    # Naive solver that only clears id 0 would keep leaks for id 1 and 2 before clear
    # That naive would give 40+? Actually before clear leaks 40, after clear 80+90=170 total 210 if not clearing all, vs 170 correct
    # More dramatic: leaks before clear only
    events3 = [
        (1, 1, 10, 1),
        (1, 1, 100, 1),
        (2, 1, 20, 2),
        (2, 1, 200, 2),
        (0, 0, 250, 0),
    ]
    expected3 = _compute_true(events3)
    assert expected3 == 0
    naive_ignore_all = 90 + 180  # if ignoring global all-clear
    assert naive_ignore_all != expected3
    data3 = _pack_wklk(events3, offset=40)
    got3 = run_agent_bytes(data3)
    assert got3 == expected3


def test_global_all_clear_same_ts_order():
    events = [
        (1, 1, 10, 1),
        (0, 0, 100, 0),
        (1, 1, 100, 1),
        (1, 1, 150, 1),
    ]
    expected = _compute_true(events)
    assert expected == 50
    data = _pack_wklk(events, offset=40)
    got = run_agent_bytes(data)
    assert got == expected


def test_even_refcount_vs_odd_binary():
    """Even ids ref-counted, odd binary idempotent — discriminates simple idempotent solvers."""
    # Odd id 1: acquire, acquire dup, release -> cleared, leak 0
    events_odd = [
        (1, 1, 10, 1),
        (1, 1, 20, 1),
        (1, 0, 30, 1),
    ]
    expected_odd = _compute_true(events_odd)
    assert expected_odd == 0, f"odd should be binary cleared, got {expected_odd}"
    data_odd = _pack_wklk(events_odd, offset=32)
    got_odd = run_agent_bytes(data_odd)
    assert got_odd == expected_odd, (
        f"odd binary failed: got {got_odd} expected {expected_odd}"
    )

    # Even id 2: acquire, acquire dup, release -> still held count 1, leak from 10 to 30? Actually last is 30, first 10 => 20
    events_even = [
        (2, 1, 10, 1),
        (2, 1, 20, 1),
        (2, 0, 30, 1),
    ]
    expected_even = _compute_true(events_even)
    assert expected_even == 20, (
        f"even should be refcounted still held 20, got {expected_even}"
    )
    data_even = _pack_wklk(events_even, offset=32)
    got_even = run_agent_bytes(data_even)
    assert got_even == expected_even, (
        f"even refcount failed: got {got_even} expected {expected_even}"
    )

    # Even needs two releases to clear
    events_even2 = [
        (2, 1, 10, 1),
        (2, 1, 20, 1),
        (2, 0, 30, 1),
        (2, 0, 40, 1),
    ]
    expected_even2 = _compute_true(events_even2)
    assert expected_even2 == 0, (
        f"even double release should clear, got {expected_even2}"
    )
    data_even2 = _pack_wklk(events_even2, offset=32)
    got_even2 = run_agent_bytes(data_even2)
    assert got_even2 == expected_even2

    # Mixed: even leak with odd interleaved
    events_mixed = [
        (2, 1, 10, 1),
        (2, 1, 15, 1),
        (1, 1, 12, 1),
        (1, 1, 18, 1),
        (2, 0, 20, 1),
        (1, 0, 25, 1),
    ]
    expected_mixed = _compute_true(events_mixed)
    # odd cleared, even still held count 1 with last 20 first 10 => 10
    assert expected_mixed == 10
    data_mixed = _pack_wklk(events_mixed, offset=40)
    got_mixed = run_agent_bytes(data_mixed)
    assert got_mixed == expected_mixed
