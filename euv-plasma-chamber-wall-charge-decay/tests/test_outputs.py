"""Verify /app/solve.py reports true charge uC for EUVC trace.
Ground truth from generator stored in ground_truth.json.
Uses audit hook sandbox to prevent solver from reading /tests.
"""

import ast
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import json
import pytest

SCRIPT = "/app/solve.py"
REL_TOL = 0.03
HELDOUTS = [
    "/tests/data/heldout_1.euvc",
    "/tests/data/heldout_2.euvc",
    "/tests/data/heldout_3.euvc",
    "/tests/data/heldout_4.euvc",
]

ALLOWED_MODULES = {"struct", "sys", "math", "random", "tempfile", "re", "collections"}

BANNED_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "chr",
    "ord",
    "breakpoint",
    "bytes",
    "bytearray",
}

BANNED_ATTRS = {
    "fromhex",
    "b64decode",
    "b64encode",
    "b16decode",
    "b32decode",
    "decodebytes",
    "decodestring",
}

BANNED_TOKENS_FOR_PATH = [
    "/tests",
    "test_outputs",
    "heldout",
    "_gen",
    "ground_truth",
    "reference volume",
    "reference_volume",
    "geometric truth",
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

RUNNER_TEMPLATE = r"""
import sys

FORBIDDEN = ["/tests", "test_outputs", "heldout", "_gen", "ground_truth", "reference volume", "geometric truth", "reference_volume"]

def _is_blocked(p):
    try:
        s = str(p).lower()
    except:
        return False
    for pat in FORBIDDEN:
        if pat.lower() in s:
            return True
    return False

def audit_hook(event, args):
    if event in ("open", "io.open"):
        if args:
            if _is_blocked(args[0]):
                raise RuntimeError(f"blocked open {args[0]}")
    elif event.startswith("os."):
        if event in ("os.system", "os.popen", "os.execv", "os.execve", "os.execl",
                     "os.execlp", "os.execle", "os.execvp", "os.execvpe",
                     "os.spawnl", "os.spawnle", "os.spawnlp", "os.spawnlpe",
                     "os.spawnv", "os.spawnve", "os.spawnvp", "os.spawnvpe",
                     "os.fork", "os.forkpty", "os.posix_spawn", "os.posix_spawnp"):
            raise RuntimeError(f"blocked {event}")
        if event == "os.open":
            if args and _is_blocked(args[0]):
                raise RuntimeError(f"blocked {event} {args[0]}")
        if event in ("os.listdir", "os.scandir", "os.walk",
                     "os.stat", "os.lstat", "os.path.exists",
                     "os.path.isdir", "os.path.isfile", "os.path.islink", "os.path.getsize"):
            if args and _is_blocked(args[0]):
                raise RuntimeError(f"blocked {event} {args[0]}")
    elif event.startswith("subprocess."):
        raise RuntimeError(f"blocked {event}")
    elif event in ("socket.getaddrinfo", "socket.gethostbyname", "socket.connect"):
        raise RuntimeError(f"blocked {event}")

sys.addaudithook(audit_hook)

if len(sys.argv) < 3:
    print("runner usage: runner.py <solver> <input>", file=sys.stderr)
    sys.exit(1)

solver_path = sys.argv[1]
input_path = sys.argv[2]
sys.argv = [solver_path, input_path]

with open(solver_path, "r", encoding="utf-8", errors="ignore") as fh:
    code_text = fh.read()

import builtins as _builtins
_globals = {"__name__": "__main__", "__file__": solver_path, "__builtins__": _builtins}
exec(compile(code_text, solver_path, "exec"), _globals)
"""


def ground_truth_charge(path):
    for base in [
        "/tests/data/ground_truth.json",
        "tests/data/ground_truth.json",
    ]:
        if os.path.exists(base):
            gt = json.load(open(base))
            fname = os.path.basename(path)
            if fname in gt:
                return float(gt[fname])
            base_no_ext = os.path.splitext(fname)[0]
            if base_no_ext in gt:
                return float(gt[base_no_ext])
    return 0.0


def run_agent(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    with tempfile.TemporaryDirectory() as td:
        neutral = os.path.join(td, "scan.euvc")
        shutil.copyfile(path, neutral)
        iso = os.path.join(td, "solve.py")
        shutil.copyfile(SCRIPT, iso)
        runner = os.path.join(td, "_runner.py")
        with open(runner, "w", encoding="utf-8") as rf:
            rf.write(RUNNER_TEMPLATE)
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        proc = subprocess.run(
            [sys.executable, runner, iso, neutral],
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
    m = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", last)
    assert m, f"no numeric charge on last line: {last!r}"
    return float(m[-1])


def test_script_exists():
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"


def _static_string_value(node):
    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, str):
            return v
        if isinstance(v, (bytes, bytearray)):
            try:
                return v.decode("utf-8", errors="ignore")
            except:
                return None
        return None
    if isinstance(node, ast.JoinedStr):
        parts = []
        for val in node.values:
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                parts.append(val.value)
            elif isinstance(val, ast.FormattedValue):
                inner = _static_string_value(val.value)
                if inner is None:
                    return None
                parts.append(inner)
            else:
                sv = _static_string_value(val)
                if sv is None:
                    return None
                parts.append(sv)
        return "".join(parts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _static_string_value(node.left)
        right = _static_string_value(node.right)
        if left is not None and right is not None:
            return left + right
        return None
    return None


def _iter_combined_strings(tree):
    for node in ast.walk(tree):
        sv = _static_string_value(node)
        if sv is not None and sv != "":
            yield sv


def _iter_string_literals(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            v = node.value
            if isinstance(v, str):
                yield v
            elif isinstance(v, (bytes, bytearray)):
                try:
                    yield v.decode("utf-8", errors="ignore")
                except:
                    continue
        if isinstance(node, ast.JoinedStr):
            for part in node.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    yield part.value


def test_from_scratch():
    src = open(SCRIPT, "r", encoding="utf-8", errors="ignore").read()
    tree = ast.parse(src, filename=SCRIPT)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mod_root = a.name.split(".")[0]
                assert mod_root in ALLOWED_MODULES, (
                    f"banned module import: {a.name} (allowed: {sorted(ALLOWED_MODULES)})"
                )
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            mod_root = mod.split(".")[0]
            assert mod_root in ALLOWED_MODULES, (
                f"banned module import from: {mod} (allowed: {sorted(ALLOWED_MODULES)})"
            )
        elif isinstance(node, ast.Call):
            fn = node.func
            name = (
                fn.id
                if isinstance(fn, ast.Name)
                else (fn.attr if isinstance(fn, ast.Attribute) else "")
            )
            assert name not in BANNED_CALLS, f"dynamic call not allowed ({name})"
            if isinstance(fn, ast.Attribute):
                assert fn.attr not in BANNED_ATTRS, (
                    f"obfuscation call not allowed ({fn.attr})"
                )
            if name in {
                "getattr",
                "setattr",
                "hasattr",
                "globals",
                "locals",
                "vars",
                "dir",
            }:
                assert False, f"reflection call not allowed ({name})"
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
                    "__class__",
                }:
                    assert False, f"dunder not allowed ({attr})"
            if isinstance(node.value, ast.Name) and node.value.id == "os":
                assert attr not in BANNED_OS_ATTRS, f"banned os.{attr} usage"
            if attr in BANNED_ATTRS:
                assert False, f"obfuscation attr not allowed ({attr})"

    all_strings = set(_iter_string_literals(tree)) | set(_iter_combined_strings(tree))
    for lit in all_strings:
        low = lit.lower()
        for banned in BANNED_TOKENS_FOR_PATH:
            if banned.lower() in low:
                assert False, f"forbidden token {banned!r} in string {lit!r}"


@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    got = run_agent(path)
    expected = ground_truth_charge(path)
    assert abs(got - expected) <= REL_TOL * expected, (
        f"{os.path.basename(path)}: got {got:.2f} expected {expected:.2f} +- {REL_TOL:.0%}"
    )


def test_hard_offset_guard():
    for off in [32, 40, 96, 128]:
        hdr = bytearray(off)
        hdr[0:4] = b"EUVC"
        struct.pack_into("<I", hdr, 4, 1)
        struct.pack_into("<I", hdr, 8, 10)
        struct.pack_into("<I", hdr, 12, off)
        struct.pack_into("<f", hdr, 16, 0.0007)
        struct.pack_into("<f", hdr, 20, 1.0)
        struct.pack_into("<I", hdr, 24, 100)
        body = struct.pack("<%dh" % 10, *[1000] * 10)
        data = bytes(hdr) + body
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "x.euvc")
            open(p, "wb").write(data)
            try:
                got = run_agent(p)
            except Exception as e:
                pytest.fail(f"offset {off} crashed: {e}")
