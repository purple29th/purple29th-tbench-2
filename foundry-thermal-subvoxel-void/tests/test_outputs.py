"""Verify /app/solve.py reports mm^3 void volume in a .tiv thermal IR volume.

Thermal diffusion plus lens PSF spreads trapped heat but conserves total energy.
True void volume NOT recoverable by thresholding (thin cracks partial-volume).
IS recoverable by intensity conservation vs geometric ground truth from _gen.py.

Verifier uses generator's geometric voxel count for known held-outs (independent
of oracle), with stdlib-only fallback for arbitrary scans. No numpy/scipy needed.

Security: solve.py is executed in a sandbox where /tests and /app/data are
inaccessible. Static checks also reject filesystem-bypass tricks (pathlib,
dynamic path construction, chr/bytes tricks, etc.).
"""

import ast
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import textwrap

import pytest

SCRIPT = "/app/solve.py"
REL_TOL = 0.03
HELDOUTS = [
    "/tests/data/heldout_1.tiv",
    "/tests/data/heldout_2.tiv",
    "/tests/data/heldout_3.tiv",
]

# For local dev outside Docker, fallback locations
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_FALLBACK_SCRIPT_CANDIDATES = [
    os.path.join(_THIS_DIR, "..", "solution", "solve.py"),
    SCRIPT,
    "/app/solve.py",
]
_FALLBACK_DATA_DIR = os.path.join(_THIS_DIR, "data")


def _resolve_script_path():
    for p in _FALLBACK_SCRIPT_CANDIDATES:
        ap = os.path.abspath(p)
        if os.path.exists(ap):
            return ap
    return SCRIPT


def _resolve_heldout_path(p):
    if os.path.exists(p):
        return p
    base = os.path.basename(p)
    cand = os.path.join(_FALLBACK_DATA_DIR, base)
    if os.path.exists(cand):
        return cand
    # Also try absolute /tests/data alternative that exists in this dev container due to mixed tasks
    alt = os.path.join("/app", "data", base)
    if os.path.exists(alt):
        return alt
    return p


GEOM_TRUTH_MM3 = {
    "scene.tiv": 2459.968,
    "heldout_1.tiv": 3350.646,
    "heldout_2.tiv": 3423.2,
    "heldout_3.tiv": 3729.852,
}

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
BANNED_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "chr",
    "getattr",
    "setattr",
    "globals",
    "locals",
    "vars",
    "dir",
}
BANNED_TOKENS = [
    "/tests",
    "test_outputs",
    "heldout",
    "reference_volume",
    "GEOM_TRUTH",
    "_gen",
    "os.system",
    "os.popen",
    "os.exec",
    "os.walk",
    "os.listdir",
    "os.scandir",
    "os.open",
    "pty.",
    "importlib",
    "runpy",
    "pathlib",
    "posixpath",
    "ntpath",
    "genericpath",
    "__dict__",
    "__class__",
    "__subclasses__",
    "import os",
    "from os",
    "import pathlib",
    "from pathlib",
    "import io",
    "from io",
    "import glob",
    "from glob",
]

BANNED_SUBSTRINGS_IN_SOURCE = [
    "/tests",
    "test_outputs",
    "heldout",
    "GEOM_TRUTH",
]


def _median_sorted(sv):
    m = len(sv)
    return sv[m // 2] if m % 2 else 0.5 * (sv[m // 2 - 1] + sv[m // 2])


NEIGH26 = [
    (dx, dy, dz)
    for dz in (-1, 0, 1)
    for dy in (-1, 0, 1)
    for dx in (-1, 0, 1)
    if dx or dy or dz
]


def _parse_tiv(path):
    raw = open(path, "rb").read()
    assert raw[:4] == b"TIVR", f"{path}: bad magic"
    dtype = struct.unpack_from("<I", raw, 8)[0]
    nx, ny, nz = struct.unpack_from("<III", raw, 12)
    sx, sy, sz = struct.unpack_from("<fff", raw, 24)
    off = struct.unpack_from("<I", raw, 36)[0]
    n = nx * ny * nz
    if dtype == 2:
        vals = struct.unpack_from("<%dh" % n, raw, off)
    elif dtype == 16:
        vals = struct.unpack_from("<%df" % n, raw, off)
    else:
        raise ValueError(f"unsupported dtype {dtype}")
    return nx, ny, nz, float(sx), float(sy), float(sz), [float(v) for v in vals]


def _conservation_fallback(path):
    nx, ny, nz, sx, sy, sz, voxels = _parse_tiv(path)
    n = nx * ny * nz

    def idx(x, y, z):
        return x + nx * (y + ny * z)

    sorted_vals = sorted(voxels)
    bg = _median_sorted(sorted_vals)
    lower = sorted_vals[: n // 2]
    med_low = _median_sorted(lower)
    mad = _median_sorted(sorted(abs(v - med_low) for v in lower))
    sigma = max(1e-6, 1.4826 * mad)

    residual = [v - bg for v in voxels]
    occ_thr = 4.0 * sigma
    occupied = [r > occ_thr for r in residual]

    seen = bytearray(n)
    best_mass = -1.0
    best_comp = None
    for z0 in range(nz):
        for y0 in range(ny):
            for x0 in range(nx):
                s = idx(x0, y0, z0)
                if not occupied[s] or seen[s]:
                    continue
                stack = [(x0, y0, z0)]
                seen[s] = 1
                comp = []
                mass = 0.0
                while stack:
                    x, y, z = stack.pop()
                    k = idx(x, y, z)
                    comp.append(k)
                    mass += residual[k]
                    for dx, dy, dz in NEIGH26:
                        a, b, c = x + dx, y + dy, z + dz
                        if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                            kk = idx(a, b, c)
                            if occupied[kk] and not seen[kk]:
                                seen[kk] = 1
                                stack.append((a, b, c))
                if mass > best_mass:
                    best_mass = mass
                    best_comp = comp

    assert best_comp, f"no bright region in {path}"

    filt = []
    for j in best_comp:
        x = j % nx
        y = (j // nx) % ny
        z = j // (nx * ny)
        acc = 0.0
        cnt = 0
        for dz in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    a, b, c = x + dx, y + dy, z + dz
                    if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                        acc += residual[idx(a, b, c)]
                        cnt += 1
        filt.append(acc / cnt)
    filt.sort(reverse=True)
    top_n = max(1, min(6, len(filt)))
    plateau = sum(filt[:top_n]) / top_n
    assert plateau > 0

    region = set(best_comp)
    frontier = set(best_comp)
    floor = 1.0 * sigma
    for _ in range(40):
        shell = set()
        for j in frontier:
            x = j % nx
            y = (j // nx) % ny
            z = j // (nx * ny)
            for dx, dy, dz in NEIGH26:
                a, b, c = x + dx, y + dy, z + dz
                if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                    k = idx(a, b, c)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        if sum(residual[j] for j in shell) / len(shell) <= floor:
            break
        region |= shell
        frontier = shell

    total = sum(residual[j] for j in region)
    return total / plateau * sx * sy * sz


def reference_volume_mm3(path):
    base = os.path.basename(path)
    if base in GEOM_TRUTH_MM3:
        return GEOM_TRUTH_MM3[base]
    return _conservation_fallback(path)


_SANDBOX_RUNNER_CODE = textwrap.dedent(
    """
    import sys
    import os
    import builtins
    import io
    import pathlib
    import glob
    import runpy

    # Save originals
    _orig_open = builtins.open
    _orig_io_open = io.open
    _orig_os_open = os.open
    _orig_listdir = os.listdir
    _orig_scandir = os.scandir
    _orig_walk = os.walk
    _orig_path_open = pathlib.Path.open
    _orig_path_read_text = getattr(pathlib.Path, 'read_text', None)
    _orig_path_read_bytes = getattr(pathlib.Path, 'read_bytes', None)
    _orig_path_iterdir = pathlib.Path.iterdir
    _orig_path_glob = getattr(pathlib.Path, 'glob', None)
    _orig_path_rglob = getattr(pathlib.Path, 'rglob', None)
    _orig_glob_glob = glob.glob
    _orig_glob_iglob = glob.iglob

    td = sys.argv[1]
    neutral = sys.argv[2]
    solve_copy = sys.argv[3]

    allowed_prefix = os.path.abspath(td)
    DENIED_PREFIXES = ["/tests", "/app/data", "/app/tests"]

    def _abs_path(p):
        try:
            # os.fspath handles PathLike
            return os.path.abspath(os.fspath(p))
        except Exception:
            return os.path.abspath(str(p))

    def _is_allowed(p):
        ap = _abs_path(p)
        # Allow anything inside temp dir
        if ap == allowed_prefix or ap.startswith(allowed_prefix + os.sep):
            return True
        # Allow the neutral and solve copy explicitly (redundant with prefix check)
        if ap == os.path.abspath(neutral) or ap == os.path.abspath(solve_copy):
            return True
        # Deny specific prefixes
        for d in DENIED_PREFIXES:
            if ap == d or ap.startswith(d + os.sep):
                return False
        bn = os.path.basename(ap)
        if "heldout" in bn or "test_outputs" in bn or "_gen.py" in bn or "GEOM_TRUTH" in bn:
            return False
        # Allow stdlib / other system paths
        return True

    def _deny(p):
        raise PermissionError(f"Filesystem access denied: {p}")

    def _restricted_open(file, mode='r', *a, **kw):
        if isinstance(file, int):
            return _orig_open(file, mode, *a, **kw)
        try:
            fp = os.fspath(file)
        except Exception:
            fp = str(file)
        if not _is_allowed(fp):
            _deny(fp)
        return _orig_open(file, mode, *a, **kw)

    def _restricted_os_open(path, flags, *a, **kw):
        if not _is_allowed(path):
            _deny(path)
        return _orig_os_open(path, flags, *a, **kw)

    def _restricted_listdir(path='.'):
        if not _is_allowed(path):
            _deny(path)
        return _orig_listdir(path)

    def _restricted_scandir(path='.'):
        if not _is_allowed(path):
            _deny(path)
        return _orig_scandir(path)

    def _restricted_walk(top, *a, **kw):
        if not _is_allowed(top):
            _deny(top)
        return _orig_walk(top, *a, **kw)

    def _check_path_obj(p_obj):
        if not _is_allowed(str(p_obj)):
            _deny(str(p_obj))

    def _restricted_path_open(self, *a, **kw):
        _check_path_obj(self)
        return _orig_path_open(self, *a, **kw)

    def _restricted_path_iterdir(self):
        _check_path_obj(self)
        return _orig_path_iterdir(self)

    def _restricted_path_glob(self, *a, **kw):
        _check_path_obj(self)
        return _orig_path_glob(self, *a, **kw)

    def _restricted_path_rglob(self, *a, **kw):
        _check_path_obj(self)
        return _orig_path_rglob(self, *a, **kw)

    def _restricted_path_read_text(self, *a, **kw):
        _check_path_obj(self)
        return _orig_path_read_text(self, *a, **kw)

    def _restricted_path_read_bytes(self, *a, **kw):
        _check_path_obj(self)
        return _orig_path_read_bytes(self, *a, **kw)

    def _restricted_glob_glob(pathname, *a, **kw):
        s = str(pathname)
        if "/tests" in s or "heldout" in s or "test_outputs" in s:
            _deny(s)
        return _orig_glob_glob(pathname, *a, **kw)

    def _restricted_glob_iglob(pathname, *a, **kw):
        s = str(pathname)
        if "/tests" in s or "heldout" in s or "test_outputs" in s:
            _deny(s)
        return _orig_glob_iglob(pathname, *a, **kw)

    # Apply patches
    builtins.open = _restricted_open
    io.open = _restricted_open
    os.open = _restricted_os_open
    os.listdir = _restricted_listdir
    os.scandir = _restricted_scandir
    os.walk = _restricted_walk
    pathlib.Path.open = _restricted_path_open
    pathlib.Path.iterdir = _restricted_path_iterdir
    if _orig_path_glob:
        pathlib.Path.glob = _restricted_path_glob
    if _orig_path_rglob:
        pathlib.Path.rglob = _restricted_path_rglob
    if _orig_path_read_text:
        pathlib.Path.read_text = _restricted_path_read_text
    if _orig_path_read_bytes:
        pathlib.Path.read_bytes = _restricted_path_read_bytes
    glob.glob = _restricted_glob_glob
    glob.iglob = _restricted_glob_iglob

    # Run candidate: its argv should be [solve.py, scan.tiv]
    # We have solve_copy and neutral
    sys.argv = [solve_copy, neutral]
    runpy.run_path(solve_copy, run_name="__main__")
    """
)


def run_agent(path):
    resolved_path = _resolve_heldout_path(path)
    script_path = _resolve_script_path()
    assert os.path.exists(script_path), f"{SCRIPT} not found (tried {script_path})"
    assert os.path.exists(resolved_path), f"heldout not found: {path} / {resolved_path}"
    with tempfile.TemporaryDirectory() as td:
        neutral = os.path.join(td, "scan.tiv")
        shutil.copyfile(resolved_path, neutral)
        solve_copy = os.path.join(td, "solve.py")
        shutil.copyfile(script_path, solve_copy)
        runner_path = os.path.join(td, "_runner.py")
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(_SANDBOX_RUNNER_CODE)

        proc = subprocess.run(
            ["python3", runner_path, td, neutral, solve_copy],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=td,
        )
    assert proc.returncode == 0, (
        f"script failed on {path}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines, f"no stdout on {path} (stdout={proc.stdout!r} stderr={proc.stderr!r})"
    last = lines[-1]
    try:
        return float(last)
    except ValueError:
        m = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", last)
        assert m, f"no numeric volume on last line: {last!r}"
        return float(m[-1])


def _collect_string_literals(tree):
    """Collect all string literal values, including those built via BinOp + or JoinedStr attempts."""
    literals = []

    class Visitor(ast.NodeVisitor):
        def visit_Constant(self, node):
            if isinstance(node.value, str):
                literals.append(node.value)
            self.generic_visit(node)

        # For Python <3.8 compatibility, also check Str
        def visit_Str(self, node):
            literals.append(node.s)
            self.generic_visit(node)

        def visit_JoinedStr(self, node):
            # f-string - flag as suspicious if any part contains denied
            for v in node.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    literals.append(v.value)
            self.generic_visit(node)

    Visitor().visit(tree)
    return literals


def _has_dynamic_path_construction(src, tree):
    """Detect tricks like chr(47)+chr(116)... or bytes([...]).decode() building /tests."""
    low = src.lower()
    # chr() is never needed for honest .tiv parsing (struct only)
    # bytes([..]).decode() to build paths is cheating
    # bytearray([..]) with list of ascii codes is cheating, but bytearray(n) is honest
    # So we check more precisely
    if "chr(" in low:
        # honest solution doesn't use chr at all
        return True, "chr() usage (dynamic path construction)"
    if "bytes([" in low or "bytearray([" in low:
        return True, "bytes([ / bytearray([ pattern for dynamic path"
    if ".decode(" in low and ("bytes" in low or "bytearray" in low):
        return True, ".decode() after bytes/bytearray for dynamic path"

    # Check for string concatenation that builds denied substrings
    class ConcatVisitor(ast.NodeVisitor):
        def __init__(self):
            self.found = False
            self.detail = ""

        def visit_BinOp(self, node):
            if isinstance(node.op, ast.Add):

                def extract_str(n):
                    if isinstance(n, ast.Constant) and isinstance(n.value, str):
                        return n.value
                    if isinstance(n, ast.Str):
                        return n.s
                    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                        left = extract_str(n.left)
                        right = extract_str(n.right)
                        if left is not None and right is not None:
                            return left + right
                    return None

                combined = extract_str(node)
                if combined:
                    for deny in BANNED_SUBSTRINGS_IN_SOURCE:
                        if deny in combined:
                            self.found = True
                            self.detail = f"concatenated string builds forbidden {deny!r}: {combined!r}"
                            return
            self.generic_visit(node)

    cv = ConcatVisitor()
    cv.visit(tree)
    if cv.found:
        return True, cv.detail
    return False, ""


def test_script_exists():
    sp = _resolve_script_path()
    assert os.path.exists(sp), f"script not found at {sp}"


def test_from_scratch():
    sp = _resolve_script_path()
    src = open(sp, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        pytest.fail(f"syntax error in {SCRIPT}: {e}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                top = a.name.split(".")[0]
                assert top not in BANNED_MODULES, f"banned import {a.name}"
                assert "test_output" not in a.name.lower()
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            top = mod.split(".")[0]
            assert top not in BANNED_MODULES, f"banned import {mod}"
            assert "test_output" not in mod.lower()
        elif isinstance(node, ast.Call):
            fn = node.func
            name = (
                fn.id
                if isinstance(fn, ast.Name)
                else (fn.attr if isinstance(fn, ast.Attribute) else "")
            )
            assert name not in BANNED_CALLS, f"dynamic exec / bypass {name} not allowed"

    # Check for dynamic path tricks
    is_dyn, detail = _has_dynamic_path_construction(src, tree)
    assert not is_dyn, f"forbidden dynamic FS access: {detail}"

    compact = re.sub(r"\s+", "", src)
    for tok in BANNED_TOKENS:
        assert tok.replace(" ", "") not in compact, f"forbidden {tok}"

    # Also ensure no literal contains denied substrings directly via string collection
    lits = _collect_string_literals(tree)
    for lit in lits:
        for deny in BANNED_SUBSTRINGS_IN_SOURCE:
            # allow the neutral file name? but /tests is never legit
            if deny in lit:
                # exception: permit if lit is exactly "/tests" check already done but we want to catch
                assert False, f"forbidden literal {deny!r} in string {lit!r}"


def test_cheating_attempt_pathlib_construction_fails():
    """Negative test: a cheating solve.py that builds /tests path dynamically must be rejected."""
    cheating_code = textwrap.dedent(
        """
        import pathlib
        p = pathlib.Path("/") / "tests" / "test_outputs.py"
        print(p.read_text()[:10])
        """
    )
    with tempfile.TemporaryDirectory() as td:
        fake = os.path.join(td, "cheat.py")
        with open(fake, "w") as f:
            f.write(cheating_code)
        src = open(fake).read()
        tree = ast.parse(src)
        # Simulate test_from_scratch checks on this cheating code
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
        # Also check token
        compact = re.sub(r"\\s+", "", cheating_code)
        assert "pathlib" in compact


def test_cheating_attempt_chr_construction_fails():
    """Negative test: chr() concatenation to build /tests must be rejected."""
    cheating_code = "print(chr(47)+chr(116)+chr(101)+chr(115)+chr(116)+chr(115))"
    tree = ast.parse(cheating_code)
    is_dyn, detail = _has_dynamic_path_construction(cheating_code, tree)
    assert is_dyn, f"chr construction should be flagged, got {detail}"


@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    got = run_agent(path)
    exp = reference_volume_mm3(path)
    assert abs(got - exp) <= REL_TOL * exp, (
        f"{os.path.basename(path)}: got {got:.4f} expected {exp:.4f} +/- {REL_TOL:.0%}"
    )
