"""Verify /app/solve.py reports total leaked duration ms for WKLK trace.
Ground truth from ground_truth.json. Includes varied data_offset and reacquire tests.
Hardened isolation: copies only single trace to temp dir, bans path construction via concatenation.
"""

import ast
import json
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
BANNED_TOKENS_FOR_PATH = [
    "/tests",
    "test_outputs",
    "heldout",
    "_gen",
    "reference",
    "ground_truth",
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

# Allowed names for file path argument (input trace)
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


def ground_truth_leak(path):
    for base in ["/tests/data/ground_truth.json", "tests/data/ground_truth.json"]:
        if os.path.exists(base):
            gt = json.load(open(base))
            fname = os.path.basename(path)
            if fname in gt:
                return int(gt[fname])
    return 0


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
    """Helper to run agent on raw wklk bytes without touching filesystem leaking path."""
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


# ---- independent oracle for dynamic generation (same as solution but isolated) ----
def _pack_wklk(events, offset=64):
    n = len(events)
    hdr = bytearray(offset)
    hdr[0:4] = b"WKLK"
    struct.pack_into("<I", hdr, 4, 1)
    struct.pack_into("<I", hdr, 8, n)
    struct.pack_into("<I", hdr, 12, offset)
    body = bytearray()
    for eid, etype, ts, tid in events:
        body += struct.pack("<iIII", eid, etype, ts, tid)
    return bytes(hdr) + bytes(body)


def _compute_true(events):
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
    """Try to evaluate AST node as constant string via concatenation."""
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
        # concatenate constant parts of f-string
        parts = []
        for p in node.values:
            if isinstance(p, ast.Constant) and isinstance(p.value, str):
                parts.append(p.value)
            else:
                # if contains formatted value, cannot fully evaluate
                return None
        return "".join(parts) if parts else None
    return None


def _is_argv_one(node):
    """Check if node is sys.argv[1]"""
    # sys.argv[1] is Subscript(value=Attribute(value=Name(sys) attr=argv) slice=Constant(1))
    if isinstance(node, ast.Subscript):
        # value should be Attribute
        val = node.value
        if isinstance(val, ast.Attribute):
            if (
                isinstance(val.value, ast.Name)
                and val.value.id == "sys"
                and val.attr == "argv"
            ):
                # slice
                sl = node.slice
                if isinstance(sl, ast.Constant) and sl.value == 1:
                    return True
                # Python 3.8 compatibility where slice is Index
                if isinstance(sl, ast.Index):
                    inner = sl.value
                    if isinstance(inner, ast.Constant) and inner.value == 1:
                        return True
    return False


def test_from_scratch():
    src = open(SCRIPT, "r", encoding="utf-8", errors="ignore").read()
    tree = ast.parse(src, filename=SCRIPT)

    # Collect function param names to allow as path args
    param_names = set(ALLOWED_PATH_NAMES)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args:
                param_names.add(arg.arg)
            for arg in node.args.kwonlyargs:
                param_names.add(arg.arg)
            if node.args.vararg:
                param_names.add(node.args.vararg.arg)

    open_calls = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mod_root = a.name.split(".")[0]
                assert mod_root not in BANNED_MODULES_STRICT, (
                    f"banned module import: {a.name}"
                )
                # also block importing verifier
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
            # Track open calls
            if name == "open":
                open_calls.append(node)
            # Also detect io.open, pathlib.Path etc already banned via module
            if isinstance(fn, ast.Attribute) and fn.attr == "open":
                # e.g., io.open or Path.open
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
        # Check for constructed strings via BinOp Add
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            const_val = _get_const_str(node)
            if const_val:
                low = const_val.lower()
                for banned in BANNED_TOKENS_FOR_PATH:
                    assert banned.lower() not in low, (
                        f"forbidden path via concatenation {banned!r} in {const_val!r}"
                    )
                # Also block absolute paths like /tests or /app/tests if constructed
                if "/tests" in low or "ground_truth" in low:
                    assert False, f"forbidden absolute path via concat {const_val!r}"

    # Check string literals directly
    for lit in _iter_string_literals(tree):
        low = lit.lower()
        for banned in BANNED_TOKENS_FOR_PATH:
            assert banned.lower() not in low, f"forbidden path {banned!r} in {lit!r}"
        # Block any attempt to hide via split
        if "ground" in low and "truth" in low:
            assert False, f"forbidden ground_truth mention {lit!r}"

    # Check open calls: must be only for argv path or allowed param names, not constant paths
    for call in open_calls:
        if not call.args:
            continue
        first_arg = call.args[0]
        # Allow sys.argv[1]
        if _is_argv_one(first_arg):
            continue
        # Allow Name that is in param_names
        if isinstance(first_arg, ast.Name):
            assert first_arg.id in param_names, (
                f"open with disallowed variable name {first_arg.id!r} not in allowed {param_names}. Only open(sys.argv[1]) or open(path) where path is input arg is allowed."
            )
            continue
        # Allow if constant string is exactly the neutral scan name used in verifier (scan.wklk) - but solver shouldn't have that
        const_val = _get_const_str(first_arg)
        if const_val is not None:
            # Any constant string containing / or .wklk is forbidden
            low = const_val.lower()
            assert "/" not in const_val and "\\" not in const_val, (
                f"open with constant path {const_val!r} not allowed, only open(argv path)"
            )
            for banned in BANNED_TOKENS_FOR_PATH:
                assert banned.lower() not in low, (
                    f"open constant contains banned {banned!r}"
                )
            # also block if looks like absolute or contains tests
            if "tests" in low or "ground" in low or "heldout" in low:
                assert False, f"open constant forbidden {const_val!r}"
            # If constant is simple like 'rb' second arg, first arg must be variable, so this is second arg? Actually first arg const is bad
            assert False, f"open with constant file path {const_val!r} not allowed"
        # If first arg is BinOp (concatenated path), block
        if isinstance(first_arg, ast.BinOp):
            const_val = _get_const_str(first_arg)
            if const_val:
                assert False, f"open with concatenated path {const_val!r} not allowed"
            else:
                # dynamic construction, still disallow
                assert False, (
                    "open with dynamically constructed path not allowed, only sys.argv[1] or input path variable"
                )
        # If it's something else like Call, block
        if isinstance(first_arg, ast.Call):
            assert False, "open with call-constructed path not allowed"

    # Limit number of open calls to prevent multiple file reads
    assert len(open_calls) <= 2, (
        f"too many open calls {len(open_calls)}, only 1-2 allowed for input trace"
    )


@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    got = run_agent(path)
    expected = ground_truth_leak(path)
    assert got == expected, f"{os.path.basename(path)}: got {got} expected {expected}"


# ---- additional coverage: varied offset ----
def test_varied_offset_hardcode_guard():
    """Ensure parser respects data_offset: file with offset 16 vs 64 should be parsed correctly.
    If implementation hardcodes 64, this will fail because payload at 16 would be misaligned.
    """
    events = [(1, 1, 100, 1), (1, 1, 120, 1)]
    expected = _compute_true(events)
    assert expected == 20
    for offset in [16, 24, 40, 96, 128, 32]:
        data = _pack_wklk(events, offset=offset)
        got = run_agent_bytes(data)
        assert got == expected, f"offset {offset} failed: got {got} expected {expected}"


def test_reacquire_final_interval_semantics():
    """Check final-interval rule: acquire-release-acquire leak should count only final interval.
    Example: acq@10 rel@20 acq@30 dup@40 leak.
    Final interval = 30..40 => duration 10. First-ever would give 30.
    """
    events = [
        (1, 1, 10, 1),
        (1, 0, 20, 1),
        (1, 1, 30, 1),
        (1, 1, 40, 1),
    ]
    expected = _compute_true(events)  # should be 10
    assert expected == 10
    for offset in [16, 64, 128]:
        data = _pack_wklk(events, offset=offset)
        got = run_agent_bytes(data)
        assert got == expected, (
            f"reacquire semantics failed at offset {offset}: got {got} expected {expected}, should use final interval not first-ever"
        )


def test_cross_thread_and_dedup():
    """Balanced after duplicate and cross-thread release ignored."""
    events = [
        (1, 1, 10, 1),
        (1, 1, 12, 1),  # duplicate
        (1, 0, 20, 1),  # release balances
        (2, 1, 15, 2),  # acquire thread 2
        (
            2,
            0,
            25,
            1,
        ),  # release in different thread -> should be ignored, so thread 2 leaks
        (2, 1, 30, 2),  # duplicate while still held (dedup) -> last_ts updates to 30
    ]
    expected = _compute_true(events)
    assert expected == 15
    data = _pack_wklk(events, offset=40)
    got = run_agent_bytes(data)
    assert got == expected


def test_randomized_dynamic():
    """Generate few random traces at grading time to harden against overfit."""
    rnd = random.Random(42)
    offsets = [16, 24, 32, 40, 64, 96, 128]
    for i in range(3):
        ev = []
        num_ids = rnd.randint(5, 10)
        for id_ in range(1, num_ids + 1):
            base = rnd.randint(0, 2000)
            tids = rnd.sample([1, 2, 3, 4], rnd.randint(1, 2))
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
                    if rnd.random() < 0.5:
                        ev.append((id_, 1, a + rnd.randint(1, 20), tid))
                elif pat == 2:
                    a = base + rnd.randint(0, 100)
                    ev.append((id_, 1, a, tid))
                    ev.append((id_, 1, a + 5, tid))
                    ev.append((id_, 0, a + 20, tid))
                elif pat == 3:
                    a = base + rnd.randint(0, 100)
                    ev.append((id_, 1, a, tid))
                    other = rnd.choice([t for t in [1, 2, 3, 4] if t != tid])
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
        ev.sort(key=lambda x: x[2])
        expected = _compute_true(ev)
        offset = rnd.choice(offsets)
        data = _pack_wklk(ev, offset=offset)
        got = run_agent_bytes(data)
        assert got == expected, (
            f"random dynamic {i} offset {offset} failed: got {got} expected {expected}"
        )


def test_timestamp_order_required():
    """Ensure solver sorts by timestamp: file order shuffled, grading expects timestamp order."""
    # Create trace where file order and timestamp order give different results
    # File order: acquire id1@100, release id1@10 (out of order) => if file order, would be balanced? Let's craft
    # Timestamp order: acquire@10 release@100 => balanced 0 leaked
    # File order: acquire@100 first, then release@10 (release ignored because not held yet?) Actually logic: first acquire@100 held, then release@10 ignored because timestamp earlier but file order processes release after acquire? Wait file-order processing checks held state regardless of timestamp, so release@10 would release the held acquire@100 => balanced, 0.
    # Need case where file-order leaks but timestamp-order balanced.
    # Use: release@20, acquire@10 in file order: file-order: release ignored, acquire leaks => duration (last - first) = 0 (if single)
    # timestamp-order: acquire@10 release@20 => balanced 0. So same.
    # Better: two pairs with interleaving.
    # Let's use events where timestamp order requires dedup handling that file order breaks.
    # Simpler: use existing scene verification: file-order total 254995 vs timestamp-order 105615, ensure solver returns timestamp-order.
    # We'll generate a small custom trace where file order shuffled.
    events_file_order = [
        (1, 1, 100, 1),  # acquire at 100
        (1, 0, 10, 1),  # release at 10 (earlier timestamp, but in file after)
        (2, 1, 20, 1),  # acquire at 20
        (2, 1, 30, 1),  # duplicate at 30
    ]

    # Timestamp order sorted: (1,0,10), (2,1,20), (2,1,30), (1,1,100)
    # Processing timestamp order: release@10 ignored (no held), acquire@20 held first=20, duplicate@30 held last=30, acquire@100 id1 held first=100 last=100
    # Leaked: id2: 30-20=10, id1: 0 => total 10
    # File order processing: acquire@100 held first100 last100, release@10 -> release id1 held? At that point held True (from 100) so release would clear it (even though timestamp earlier), then acquire@20 held, duplicate@30 held => total 10 again same? Let's brute compute
    def file_order_true(ev):
        held = {}
        first = {}
        last = {}
        for eid, etype, ts, tid in ev:
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

    expected_ts = _compute_true(events_file_order)
    expected_file = file_order_true(events_file_order)
    # For this specific case they happen same, need more distinct
    # Use case where same timestamp collisions: file order matters for stability
    events_same_ts = [
        (1, 1, 10, 1),  # acquire
        (1, 0, 10, 1),  # release same ts, file order acquire then release => balanced
    ]
    # If stable sort preserves file order, timestamp order will keep acquire before release => balanced 0
    # If reverse file order (release then acquire same ts), timestamp order stable preserves release then acquire => leaked duration 0 (acquire last)
    # Actually both give 0? Let's think: release then acquire same ts: timestamp order keeps release first (ignored), acquire second leaks duration 0
    # So same.
    # Need case where file order shuffled causes different leak total vs timestamp order, as demonstrated by scene.wklk 254995 vs 105615
    # We'll just assert solver must output timestamp-order for scene-like shuffled data
    # Generate random shuffled events and check solver uses timestamp sort
    rnd = random.Random(123)
    ev = []
    for i in range(20):
        ev.append(
            (i % 5 + 1, rnd.choice([0, 1]), rnd.randint(0, 100), rnd.randint(1, 3))
        )
    # Shuffle file order
    rnd.shuffle(ev)
    expected = _compute_true(ev)
    data = _pack_wklk(ev, offset=64)
    got = run_agent_bytes(data)
    assert got == expected, (
        f"timestamp sorting required: got {got} expected timestamp-order {expected}, file-order would be {file_order_true(ev)}"
    )
