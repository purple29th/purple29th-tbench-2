"""Verify /app/solve.py reports total leaked duration ms for WKLK trace.
Hardened isolation: no ground_truth.json, expected computed directly from wklk.
Bans base64/binascii/codecs and encoded path bypass, enforces strict open(argv) dataflow.
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
    "b64encode",  # also block encode attempts to hide
}
BANNED_TOKENS_FOR_PATH = [
    "/tests",
    "test_outputs",
    "heldout",
    "_gen",
    "reference",
    "ground_truth",
    "scene.wklk",  # prevent reading scene via hardcoded path bypass? scene is allowed at /app/data but not via /tests
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
    # stable sort by timestamp only
    ev = sorted(events, key=lambda x: x[2])
    held = {}
    first_acq = {}
    last_ts = {}
    for eid, etype, ts, tid in ev:
        key = (eid, tid)
        if key not in last_ts or ts > last_ts[key]:
            last_ts[key] = ts
        if etype == 1:
            if held.get(key, False):
                continue
            held[key] = True
            first_acq[key] = ts
        else:
            if not held.get(key, False):
                continue
            held[key] = False
            first_acq[key] = None
    total = 0
    for k, is_held in held.items():
        if is_held:
            f = first_acq.get(k)
            if f is not None:
                total += last_ts[k] - f
    return total


def ground_truth_leak(path):
    # compute directly, no json
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
            timeout=60,
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
            timeout=60,
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
    # garbage padding to catch hardcoded offset
    for i in range(16, offset):
        hdr[i] = (i * 37 + 11) % 256
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
    # try to detect base64-encoded banned paths
    s = s.strip()
    if len(s) < 16:
        return None
    # base64 chars only and padding
    b64chars = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r"
    )
    if not all(c in b64chars for c in s):
        return None
    try:
        # add padding if needed
        missing = len(s) % 4
        if missing:
            s_padded = s + "=" * (4 - missing)
        else:
            s_padded = s
        decoded = base64.b64decode(s_padded, validate=False)
        # try utf-8 decode
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

    # track assignments for dataflow
    argv_derived = set()
    assigned_names = set()
    tainted = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned_names.add(target.id)
                    # check RHS
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
                        # check for banned decode attrs
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
                        # if call constructs path via bytes decode, mark tainted
                        # for safety, if call has any arg that is base64 literal
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
        # check base64 encoded bypass
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
            # must be argv_derived or param that was never assigned/tainted
            if fid in argv_derived:
                continue
            if fid in param_names and fid not in assigned_names and fid not in tainted:
                continue
            # allow if fid is param and all assignments to fid are argv_derived (i.e., fid in argv_derived) already handled
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
    got = run_agent(path)
    expected = ground_truth_leak(path)
    assert got == expected, f"{os.path.basename(path)}: got {got} expected {expected}"


def test_varied_offset_hardcode_guard():
    events = [(1, 1, 100, 1), (1, 1, 120, 1)]
    expected = _compute_true(events)
    assert expected == 20
    for offset in [16, 24, 40, 96, 128, 32]:
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
    for offset in [16, 64, 128]:
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


def test_randomized_dynamic():
    rnd = random.Random(42)
    offsets = [16, 24, 32, 40, 64, 96, 128]
    for i in range(3):
        ev = []
        num_ids = rnd.randint(8, 14)
        for id_ in range(1, num_ids + 1):
            base = rnd.randint(0, 2000)
            tids = rnd.sample([1, 2, 3, 4, 5], rnd.randint(1, 3))
            for tid in tids:
                pat = rnd.choice([0, 1, 2, 3, 4])
                if pat == 0:
                    a = base + rnd.randint(0, 100)
                    r = a + rnd.randint(10, 100)
                    ev.append((id_, 1, a, tid))
                    ev.append((id_, 0, r, tid))
                elif pat == 1:
                    a = base + rnd.randint(0, 100)
                    ev.append((id_, 1, a, tid))
                    if rnd.random() < 0.6:
                        ev.append((id_, 1, a + rnd.randint(1, 20), tid))
                elif pat == 2:
                    a = base + rnd.randint(0, 100)
                    ev.append((id_, 1, a, tid))
                    ev.append((id_, 1, a + 5, tid))
                    ev.append((id_, 0, a + 20, tid))
                elif pat == 3:
                    a = base + rnd.randint(0, 100)
                    ev.append((id_, 1, a, tid))
                    other = rnd.choice([t for t in [1, 2, 3, 4, 5] if t != tid])
                    ev.append((id_, 0, a + 30, other))
                else:
                    a1 = base + rnd.randint(0, 100)
                    r1 = a1 + 20
                    a2 = r1 + 10
                    ev.append((id_, 1, a1, tid))
                    ev.append((id_, 0, r1, tid))
                    ev.append((id_, 1, a2, tid))
                    if rnd.random() < 0.5:
                        ev.append((id_, 1, a2 + 10, tid))
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
    for i in range(30):
        ev.append(
            (i % 6 + 1, rnd.choice([0, 1]), rnd.randint(0, 200), rnd.randint(1, 4))
        )
    rnd.shuffle(ev)
    expected = _compute_true(ev)

    def file_order_true(ev2):
        held = {}
        first = {}
        last = {}
        for eid, etype, ts, tid in ev2:
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
    events = [(-5, 1, 10, 1), (-5, 1, 20, 1), (-10, 1, 15, 2), (-10, 0, 25, 2)]
    expected = _compute_true(events)
    # (-5) leaks 10, (-10) balanced
    assert expected == 10
    data = _pack_wklk(events, offset=32)
    got = run_agent_bytes(data)
    assert got == expected


def test_same_timestamp_stable_order():
    # acquire then release same ts in file order => balanced if stable preserves order
    events_file_order = [
        (1, 1, 100, 1),
        (1, 0, 100, 1),
        (2, 0, 100, 1),
        (2, 1, 100, 1),
    ]
    # timestamp order stable: first two => acquire@100 then release@100 => balanced 0
    # second pair: release then acquire same ts => release ignored, acquire leaks 0
    expected = _compute_true(events_file_order)
    assert expected == 0
    data = _pack_wklk(events_file_order, offset=24)
    got = run_agent_bytes(data)
    assert got == expected

    # reverse order would give different if not stable? Actually both 0 leak duration but logic of order matters
    # create case where order matters for duration calc: duplicate after release same ts
    events2 = [
        (1, 1, 50, 1),
        (1, 0, 100, 1),
        (
            1,
            1,
            100,
            1,
        ),  # acquire same ts as release, file order release then acquire => leak
    ]
    # sorted stable keeps file order: release@100 then acquire@100? Wait file order is acq50, rel100, acq100. Sorted by ts: 50,100,100 stable preserves rel then acq => after processing: acq50 held, rel100 releases, acq100 leaks duration 0 => total 0
    # if file order were acq50, acq100, rel100 same ts: acq50 held, duplicate acq100 ignored, rel100 releases => 0 as well. Need more distinct.
    # For test, just ensure stable sort behavior doesn't crash
    expected2 = _compute_true(events2)
    data2 = _pack_wklk(events2, offset=40)
    got2 = run_agent_bytes(data2)
    assert got2 == expected2
