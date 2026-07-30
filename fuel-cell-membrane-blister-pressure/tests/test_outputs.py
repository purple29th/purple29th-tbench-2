"""Verify /app/solve.py reports true blister pressure kPa for BLPR trace.
Ground truth is integral true pressure from generator stored in ground_truth_fuel.json.
"""

import ast, os, re, shutil, struct, subprocess, sys, tempfile, json
import pytest

SCRIPT = "/app/solve.py"
REL_TOL = 0.03
HELDOUTS = [
    "/tests/data/heldout_1.blpr",
    "/tests/data/heldout_2.blpr",
    "/tests/data/heldout_3.blpr",
    "/tests/data/heldout_4.blpr",
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


def ground_truth_charge(path):
    for base in [
        "/tests/data/ground_truth_fuel.json",
        "tests/data/ground_truth_fuel.json",
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
        neutral = os.path.join(td, f"scan_{os.urandom(4).hex()}.blpr")
        shutil.copyfile(path, neutral)
        iso = os.path.join(td, "solve.py")
        shutil.copyfile(SCRIPT, iso)
        # Secure runner with audit hook to block /tests reads, fixes R07 reward hacking
        secure_runner = f'''
import sys, os, runpy, tempfile, shutil, re
BLOCKED_SUBSTRS = ["/tests", "test_outputs", "heldout", "_gen", "ground_truth", "reference_volume"]
def is_blocked(p):
    s = str(p)
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
            rp = os.path.realpath(str(path))
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
            rp = os.path.realpath(str(path)) if path else ""
            if rp in ("/", "/tests", "/tests/data") or rp.startswith("/tests"):
                raise RuntimeError(f"Blocked dir listing realpath: {{path}} -> {{rp}}")
        except RuntimeError:
            raise
        except:
            pass
        if str(path) in ("", "/", "/tests", "/tests/data"):
            raise RuntimeError(f"Blocked listing of sensitive dir: {{path}}")
    elif event.startswith("os."):
        banned = {"os.system","os.popen","os.spawnl","os.spawnle","os.spawnlp","os.spawnlpe","os.spawnv","os.spawnve","os.spawnvp","os.spawnvpe","os.exec","os.execl","os.execle","os.execlp","os.execlpe","os.execv","os.execve","os.execvp","os.execvpe","os.posix_spawn","os.posix_spawnp","os.fork","os.forkpty"}
        if event in banned:
            raise RuntimeError(f"Blocked {{event}}")
    elif event.startswith("subprocess."):
        raise RuntimeError(f"Blocked {{event}}")
    elif event.startswith("socket."):
        raise RuntimeError(f"Blocked {{event}}")
    elif event == "import":
        mod = args[0] if args else ""
        base = mod.split(".")[0]
        banned_imports = {"numpy","scipy","skimage","cv2","PIL","pandas","torch","tensorflow","subprocess","socket","multiprocessing","glob","pathlib","shutil","io","os","pty","importlib","runpy","ctypes"}
        if base in banned_imports:
            raise RuntimeError(f"Blocked import {{mod}}")

sys.addaudithook(audit_hook)
sys.argv = ["{iso}", "{neutral}"]
runpy.run_path("{iso}", run_name="__main__")
'''
        runner_path = os.path.join(td, "_secure_runner.py")
        open(runner_path, "w").write(secure_runner)
        proc = subprocess.run(
            [sys.executable, runner_path],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=td,
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
                assert mod_root not in BANNED_MODULES_STRICT, (
                    f"banned module import: {a.name}"
                )
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            mod_root = mod.split(".")[0]
            assert mod_root not in BANNED_MODULES_STRICT, (
                f"banned module import from: {mod}"
            )
        elif isinstance(node, ast.Call):
            fn = node.func
            name = (
                fn.id
                if isinstance(fn, ast.Name)
                else (fn.attr if isinstance(fn, ast.Attribute) else "")
            )
            assert name not in BANNED_CALLS, f"dynamic call not allowed ({name})"
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
    for lit in _iter_string_literals(tree):
        low = lit.lower()
        for banned in BANNED_TOKENS_FOR_PATH:
            assert banned.lower() not in low, f"forbidden path {banned!r} in {lit!r}"


@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    got = run_agent(path)
    expected = ground_truth_charge(path)
    assert abs(got - expected) <= REL_TOL * expected, (
        f"{os.path.basename(path)}: got {got:.2f} expected {expected:.2f} +- {REL_TOL:.0%}"
    )


def test_hard_offset_guard():
    """Hardcoded offset 64 fails on 32/40/96/128 - BLPR float32 version"""
    for off in [32, 40, 96, 128]:
        hdr = bytearray(off)
        hdr[0:4] = b"BLPR"
        struct.pack_into("<I", hdr, 4, 1)
        struct.pack_into("<I", hdr, 8, 10)
        struct.pack_into("<I", hdr, 12, off)
        struct.pack_into("<f", hdr, 16, 0.0008)
        struct.pack_into("<f", hdr, 20, 1.0)
        struct.pack_into("<I", hdr, 24, 100)
        body = struct.pack("<%df" % 10, *[10.0] * 10)
        data = bytes(hdr) + body
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "x.blpr")
            open(p, "wb").write(data)
            # run agent, should not crash, should respect offset
            try:
                got = run_agent(p)
            except Exception as e:
                pytest.fail(f"offset {off} crashed: {e}")
