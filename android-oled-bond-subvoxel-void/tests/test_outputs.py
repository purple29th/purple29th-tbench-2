"""Verify /app/solve.py reports mm^3 volume of OLED bond void .obvl cube
on HELD-OUT scans agent never saw.

Pixel OLED bonding QA uses under-display VCSEL diffuser IR scanner. OLED stack diffuses wide XY, bond thin -> narrow Z. Air bubbles appear bright due to scattering, anisotropic PSF creates saturated core + thin delam fingers with partial-volume dim values + dust speck artefacts far away. Threshold fails. Blur conserves energy, so true volume = sum(residual)/plateau * voxel_pitch.

Independent ground truth recomputed stdlib only with distinct heuristics vs oracle, so memorizing fails. 3%% tolerance.

Hardened isolation (post-review fix for BAD_LEAKAGE):
- _gen.py with exact hidden scan definitions is NO LONGER mounted under /tests (removed from bundle). Ground truth recomputed from physics, not generator.
- solve.py is executed in an isolated TemporaryDirectory containing only a neutral copy of the scan and a copy of solve.py itself (cwd=td). It cannot import from /tests via relative path.
- test_from_scratch performs strong static audit: banned libs, banned filesystem traversal APIs (pathlib, os.open/stat/read/fdopen, shutil, io.open, os.walk/listdir/scandir/system/popen/exec), banned dynamic tricks (getattr/setattr/hasattr, globals/locals/vars/dir, __builtins__, chr/ord, base64/binascii/codecs, importlib/runpy, __dict__/__subclasses__/__mro__), plus string-literal decoding for obfuscated "/tests", "heldout", "_gen", "test_output" paths. Dunder attributes other than __name__/__main__ are rejected.
"""

import ast
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import pytest

SCRIPT = "/app/solve.py"
REL_TOL = 0.03
HELDOUTS = [
    "/tests/data/heldout_1.obvl",
    "/tests/data/heldout_2.obvl",
    "/tests/data/heldout_3.obvl",
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
    "io",  # filesystem traversal APIs - not needed for parsing
}

# os module itself is highly sensitive: we allow it only if no banned attribute is accessed,
# but we also add it to soft-ban via attribute checks. To prevent trivial directory listing,
# we ban importing os outright in strict mode - oracle uses only struct+sys.
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

BANNED_TOKENS = [
    "/tests",
    "test_outputs",
    "heldout",
    "_gen",
    "os.system",
    "os.popen",
    "os.exec",
    "os.walk",
    "os.listdir",
    "os.scandir",
    "os.open",
    "os.stat",
    "os.read",
    "os.fdopen",
    "os.path",
    "pty.",
    "importlib",
    "runpy",
    "pathlib",
    "Path(",
    "shutil",
    "io.open",
    "__builtins__",
    "builtins",
    "__dict__",
    "__subclasses__",
    "__mro__",
    "base64",
    "binascii",
    "codecs",
]

# Decoded string literal substrings that must not appear (lowercased)
BANNED_SUBSTRINGS_IN_STRLITS = [
    "/tests",
    "tests/data",
    "heldout",
    "_gen",
    "test_output",
    "test_outputs",
]

ALLOWED_DUNDER_ATTRS = {"__name__", "__main__"}

NEIGH = [
    (dx, dy, dz)
    for dz in (-1, 0, 1)
    for dy in (-1, 0, 1)
    for dx in (-1, 0, 1)
    if not (dx == 0 and dy == 0 and dz == 0)
]


def _parse(path):
    d = open(path, "rb").read()
    assert d[:4] == b"OBVL", f"{path}: bad magic {d[:4]}"
    dtype = struct.unpack_from("<I", d, 8)[0]
    nx, ny, nz = struct.unpack_from("<III", d, 12)
    sx, sy, sz = struct.unpack_from("<fff", d, 24)
    off = struct.unpack_from("<I", d, 36)[0]
    n = nx * ny * nz
    fmt = {2: "<%dh", 16: "<%df"}[dtype] % n
    vals = [float(v) for v in struct.unpack_from(fmt, d, off)]
    return nx, ny, nz, float(sx), float(sy), float(sz), vals


def _median(sorted_vals):
    m = len(sorted_vals)
    if m == 0:
        return 0.0
    return (
        sorted_vals[m // 2]
        if m % 2
        else 0.5 * (sorted_vals[m // 2 - 1] + sorted_vals[m // 2])
    )


def reference_volume_mm3(path):
    nx, ny, nz, sx, sy, sz, vals = _parse(path)
    n = nx * ny * nz

    def idx(x, y, z):
        return x + nx * (y + ny * z)

    sv = sorted(vals)
    bg = _median(sv)
    low_vals = [v for v in vals if v < bg]
    if not low_vals:
        low_vals = sv[: n // 2]
    low_sorted = sorted(low_vals)
    med_low = _median(low_sorted)
    mad = _median(sorted(abs(v - med_low) for v in low_sorted))
    noise_sigma = max(1e-6, 1.4826 * mad)
    r = [v - bg for v in vals]
    thr = 4.2 * noise_sigma

    occ = [v > thr for v in r]
    seen = bytearray(n)
    best_mass = -1.0
    best_comp = None
    for z0 in range(nz):
        for y0 in range(ny):
            for x0 in range(nx):
                s = idx(x0, y0, z0)
                if not occ[s] or seen[s]:
                    continue
                stack = [(x0, y0, z0)]
                seen[s] = 1
                comp = []
                mass = 0.0
                while stack:
                    x, y, z = stack.pop()
                    cur = idx(x, y, z)
                    comp.append(cur)
                    mass += r[cur]
                    for dx, dy, dz in NEIGH:
                        a = x + dx
                        b = y + dy
                        c = z + dz
                        if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                            k = idx(a, b, c)
                            if occ[k] and not seen[k]:
                                seen[k] = 1
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
                    a = min(max(x + dx, 0), nx - 1)
                    b = min(max(y + dy, 0), ny - 1)
                    c = min(max(z + dz, 0), nz - 1)
                    acc += r[idx(a, b, c)]
                    cnt += 1
        filt.append(acc / cnt)
    filt.sort(reverse=True)
    top = filt[: max(1, min(8, len(filt)))]
    amp = _median(sorted(top))
    assert amp > 0, f"non-positive amp in {path}"

    region = set(best_comp)
    frontier = set(best_comp)
    for _ in range(60):
        shell = set()
        for j in frontier:
            x = j % nx
            y = (j // nx) % ny
            z = j // (nx * ny)
            for dx, dy, dz in NEIGH:
                a, b, c = x + dx, y + dy, z + dz
                if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                    k = idx(a, b, c)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        mean_shell = sum(r[j] for j in shell) / len(shell) if shell else 0.0
        if mean_shell <= 0.9 * noise_sigma:
            break
        region |= shell
        frontier = shell

    voxels = sum(r[j] for j in region) / amp
    return voxels * sx * sy * sz


def run_agent(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    with tempfile.TemporaryDirectory() as td:
        neutral = os.path.join(td, "scan.obvl")
        shutil.copyfile(path, neutral)
        # Isolated copy of solve.py - prevents /app path traversal via __file__
        isolated_script = os.path.join(td, "solve.py")
        shutil.copyfile(SCRIPT, isolated_script)
        # Run with cwd=td and restricted PYTHONPATH to only td
        env = os.environ.copy()
        env["PYTHONPATH"] = td
        proc = subprocess.run(
            [sys.executable, isolated_script, neutral],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=td,
            env=env,
        )
    assert proc.returncode == 0, (
        f"exit {proc.returncode} on {path}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines, f"no stdout on {path}"
    last = lines[-1]
    try:
        return float(last)
    except ValueError:
        m = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", last)
        assert m, f"no numeric volume on last line: {last!r}"
        return float(m[-1])


def test_script_exists():
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"


def _iter_string_literals(tree):
    """Yield all decoded string literals (including bytes decoded as utf-8 ignoring errors)."""
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
        # f-strings: ast.JoinedStr contains FormattedValue + Constant parts
        if isinstance(node, ast.JoinedStr):
            for part in node.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    yield part.value


def test_from_scratch():
    src = open(SCRIPT, "r", encoding="utf-8", errors="ignore").read()
    tree = ast.parse(src, filename=SCRIPT)

    # 1. Import bans
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

        # 2. Banned calls via direct call
        elif isinstance(node, ast.Call):
            fn = node.func
            name = ""
            if isinstance(fn, ast.Name):
                name = fn.id
            elif isinstance(fn, ast.Attribute):
                name = fn.attr
            assert name not in BANNED_CALLS, (
                f"dynamic/obfuscation call not allowed ({name})"
            )
            # Also catch builtins like __import__ via Name
            if isinstance(fn, ast.Name) and fn.id in BANNED_CALLS:
                raise AssertionError(f"banned call {fn.id}")

        # 3. Dunder attribute access (except __name__, __main__)
        elif isinstance(node, ast.Attribute):
            attr = node.attr
            if (
                attr.startswith("__")
                and attr.endswith("__")
                and attr not in ALLOWED_DUNDER_ATTRS
            ):
                # Allow __name__ and __main__ only - block __dict__, __subclasses__, __builtins__, etc.
                assert False, (
                    f"dunder attribute not allowed ({attr}) - potential sandbox escape"
                )
            if attr in {
                "__dict__",
                "__subclasses__",
                "__mro__",
                "__bases__",
                "__code__",
                "__globals__",
            }:
                assert False, f"introspection attribute not allowed ({attr})"

    # 4. Decoded string literal inspection (catches "\x2f\x74\x65\x73\x74\x73" -> "/tests")
    for lit in _iter_string_literals(tree):
        low = lit.lower()
        for banned in BANNED_SUBSTRINGS_IN_STRLITS:
            assert banned.lower() not in low, (
                f"forbidden path substring in string literal: {banned!r} found in {lit!r}"
            )

    # 5. Token scan on whitespace-stripped source (catches direct /tests etc.)
    compact = re.sub(r"\s+", "", src)
    compact_low = compact.lower()
    for tok in BANNED_TOKENS:
        # token check is case-sensitive for path, case-insensitive for module names
        t = tok.replace(" ", "")
        if t.lower() in (
            "pathlib",
            "shutil",
            "base64",
            "binascii",
            "codecs",
            "importlib",
            "runpy",
        ):
            assert t.lower() not in compact_low, f"forbidden usage ({tok})"
        else:
            assert t not in compact, f"forbidden usage ({tok})"


@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    got = run_agent(path)
    expected = reference_volume_mm3(path)
    assert abs(got - expected) <= REL_TOL * expected, (
        f"{os.path.basename(path)}: got {got:.4f} mm3, expected {expected:.4f} mm3 (+/- {REL_TOL:.0%})"
    )
