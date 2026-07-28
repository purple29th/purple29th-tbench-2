"""Verify /app/solve.py reports mm2 area of display mura ink pool .dmip map
on HELD-OUT scans agent never saw.

Display lamination QA uses under-display RGB sensor with diffuser. Adhesive diffuses wide XY so ink pooling appears bright with saturated core + thin bleed fingers and dust artefacts. Threshold fails. Light conserved: true area = sum(residual)/plateau * pixel pitch.

Ground truth is geometric true area from generator occupancy sum * sx*sy, stored in ground_truth.json. This is physical truth, not heuristic. Reference heuristic reference_area_mm2 is recomputed stdlib with distinct heuristics vs oracle and matches true within 1 percent, but grading uses true area to avoid penalizing valid alternative constants.

Hardened isolation:
- _gen.py with exact scan definitions NOT mounted under /tests (removed from bundle)
- solve.py executed in isolated TemporaryDirectory with neutral copy scan.dmip and copy of solve.py itself, PYTHONPATH=td
- test_from_scratch bans pathlib os io shutil chr getattr base64 dunder and decodes string literals for obfuscated /tests paths
"""

import ast, os, re, shutil, struct, subprocess, sys, tempfile, json
import pytest

SCRIPT = "/app/solve.py"
REL_TOL = 0.03
HELDOUTS = [
    "/tests/data/heldout_1.dmip",
    "/tests/data/heldout_2.dmip",
    "/tests/data/heldout_3.dmip",
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
    (dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if not (dx == 0 and dy == 0)
]


def _parse(path):
    d = open(path, "rb").read()
    assert d[:4] == b"DMIP", f"{path}: bad magic {d[:4]}"
    dtype = struct.unpack_from("<I", d, 8)[0]
    nx, ny = struct.unpack_from("<II", d, 12)
    sx, sy = struct.unpack_from("<ff", d, 20)
    off = struct.unpack_from("<I", d, 28)[0]
    n = nx * ny
    fmt = {2: "<%dh", 16: "<%df"}[dtype] % n
    vals = [float(v) for v in struct.unpack_from(fmt, d, off)]
    return nx, ny, float(sx), float(sy), vals


def _median(s):
    m = len(s)
    if m == 0:
        return 0.0
    return s[m // 2] if m % 2 else 0.5 * (s[m // 2 - 1] + s[m // 2])


def reference_area_mm2(path):
    # independent heuristic, matches true within 1 percent, kept for sanity not grading
    nx, ny, sx, sy, vals = _parse(path)
    n = nx * ny

    def idx(x, y):
        return x + nx * y

    sv = sorted(vals)
    bg = _median(sv)
    low = [v for v in vals if v < bg]
    if not low:
        low = sv[: n // 2]
    low_sorted = sorted(low)
    med_low = _median(low_sorted)
    mad = _median(sorted(abs(v - med_low) for v in low_sorted))
    noise_sigma = max(1e-6, 1.4826 * mad)
    r = [v - bg for v in vals]
    thr = 4.0 * noise_sigma
    occ = [v > thr for v in r]
    seen = bytearray(n)
    best_mass = -1.0
    best_comp = None
    for y0 in range(ny):
        for x0 in range(nx):
            s = idx(x0, y0)
            if not occ[s] or seen[s]:
                continue
            stack = [(x0, y0)]
            seen[s] = 1
            comp = []
            mass = 0.0
            while stack:
                x, y = stack.pop()
                cur = idx(x, y)
                comp.append(cur)
                mass += r[cur]
                for dx, dy in NEIGH:
                    a = x + dx
                    b = y + dy
                    if 0 <= a < nx and 0 <= b < ny:
                        k = idx(a, b)
                        if occ[k] and not seen[k]:
                            seen[k] = 1
                            stack.append((a, b))
            if mass > best_mass:
                best_mass = mass
                best_comp = comp
    assert best_comp
    filt = []
    for j in best_comp:
        x = j % nx
        y = j // nx
        acc = 0.0
        cnt = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                a = min(max(x + dx, 0), nx - 1)
                b = min(max(y + dy, 0), ny - 1)
                acc += r[idx(a, b)]
                cnt += 1
        filt.append(acc / cnt)
    filt.sort(reverse=True)
    top = filt[: max(1, min(8, len(filt)))]
    amp = _median(sorted(top))
    assert amp > 0
    region = set(best_comp)
    frontier = set(best_comp)
    for _ in range(50):
        shell = set()
        for j in frontier:
            x = j % nx
            y = j // nx
            for dx, dy in NEIGH:
                a = x + dx
                b = y + dy
                if 0 <= a < nx and 0 <= b < ny:
                    k = idx(a, b)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        mean_shell = sum(r[j] for j in shell) / len(shell) if shell else 0.0
        if mean_shell <= 0.9 * noise_sigma:
            break
        region |= shell
        frontier = shell
    pixels = sum(r[j] for j in region) / amp
    return pixels * sx * sy


def ground_truth_area(path):
    # Load geometric true area from ground_truth.json
    # ground_truth.json maps filename -> true area
    # Try /tests/data/ground_truth.json first, then local fallback
    for base in ["/tests/data/ground_truth.json", "tests/data/ground_truth.json"]:
        if os.path.exists(base):
            gt = json.load(open(base))
            fname = os.path.basename(path)
            if fname in gt:
                return float(gt[fname])
    # fallback to heuristic if json missing (should not happen in grading)
    return reference_area_mm2(path)


def run_agent(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    with tempfile.TemporaryDirectory() as td:
        neutral = os.path.join(td, "scan.dmip")
        shutil.copyfile(path, neutral)
        isolated_script = os.path.join(td, "solve.py")
        shutil.copyfile(SCRIPT, isolated_script)
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
        assert m, f"no numeric area on last line: {last!r}"
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
            name = ""
            if isinstance(fn, ast.Name):
                name = fn.id
            elif isinstance(fn, ast.Attribute):
                name = fn.attr
            assert name not in BANNED_CALLS, (
                f"dynamic/obfuscation call not allowed ({name})"
            )
            if isinstance(fn, ast.Name) and fn.id in BANNED_CALLS:
                raise AssertionError(f"banned call {fn.id}")
        elif isinstance(node, ast.Attribute):
            attr = node.attr
            if (
                attr.startswith("__")
                and attr.endswith("__")
                and attr not in ALLOWED_DUNDER_ATTRS
            ):
                assert False, f"dunder attribute not allowed ({attr})"
            if attr in {
                "__dict__",
                "__subclasses__",
                "__mro__",
                "__bases__",
                "__code__",
                "__globals__",
            }:
                assert False, f"introspection attribute not allowed ({attr})"
    for lit in _iter_string_literals(tree):
        low = lit.lower()
        for banned in BANNED_SUBSTRINGS_IN_STRLITS:
            assert banned.lower() not in low, (
                f"forbidden path substring in string literal: {banned!r} found in {lit!r}"
            )
    compact = re.sub(r"\s+", "", src)
    compact_low = compact.lower()
    for tok in BANNED_TOKENS:
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
    expected = ground_truth_area(path)
    # also ensure heuristic close to ground truth for sanity (within 2 percent)
    heur = reference_area_mm2(path)
    assert abs(heur - expected) <= 0.02 * expected, (
        f"heuristic diverged from true: heur {heur:.4f} true {expected:.4f}"
    )
    assert abs(got - expected) <= REL_TOL * expected, (
        f"{os.path.basename(path)}: got {got:.4f} mm2, expected true {expected:.4f} mm2 (+/- {REL_TOL:.0%}) heuristic {heur:.4f}"
    )
