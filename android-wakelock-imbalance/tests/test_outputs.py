"""Verify /app/solve.py reports total leaked duration ms for WKLK trace.
Ground truth from ground_truth.json.
"""
import ast, os, re, shutil, struct, subprocess, sys, tempfile, json
import pytest

SCRIPT="/app/solve.py"
HELDOUTS=[
    "/tests/data/heldout_1.wklk",
    "/tests/data/heldout_2.wklk",
    "/tests/data/heldout_3.wklk",
    "/tests/data/heldout_4.wklk",
]

BANNED_MODULES={
    "numpy","scipy","skimage","cv2","PIL","Pillow","networkx","igraph","imageio","pandas","torch","tensorflow",
    "subprocess","importlib","runpy","ctypes","socket","multiprocessing","glob","pathlib","shutil","io","pty",
}
BANNED_MODULES_STRICT=BANNED_MODULES|{"os"}
BANNED_CALLS={"eval","exec","compile","__import__","getattr","setattr","hasattr","globals","locals","vars","dir","chr","ord","breakpoint"}
BANNED_TOKENS_FOR_PATH=["/tests","test_outputs","heldout","_gen","reference","ground_truth"]
BANNED_OS_ATTRS={"system","popen","exec","walk","listdir","scandir","open","stat","read","fdopen","path"}
ALLOWED_DUNDER_ATTRS={"__name__","__main__"}

def ground_truth_leak(path):
    for base in ["/tests/data/ground_truth.json","tests/data/ground_truth.json"]:
        if os.path.exists(base):
            gt=json.load(open(base))
            fname=os.path.basename(path)
            if fname in gt:
                return int(gt[fname])
    return 0

def run_agent(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    with tempfile.TemporaryDirectory() as td:
        neutral=os.path.join(td,"scan.wklk")
        shutil.copyfile(path,neutral)
        iso=os.path.join(td,"solve.py")
        shutil.copyfile(SCRIPT, iso)
        env=os.environ.copy()
        env["PYTHONPATH"]=td
        proc=subprocess.run([sys.executable, iso, neutral], capture_output=True, text=True, timeout=60, cwd=td, env=env)
    assert proc.returncode==0, f"exit {proc.returncode} on {path}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    lines=[ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines, f"no stdout on {path}"
    last=lines[-1]
    m=re.findall(r"-?\d+", last)
    assert m, f"no numeric leak on last line: {last!r}"
    return int(m[-1])

def test_script_exists():
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"

def _iter_string_literals(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            v=node.value
            if isinstance(v,str):
                yield v
            elif isinstance(v,(bytes,bytearray)):
                try:
                    yield v.decode("utf-8", errors="ignore")
                except:
                    continue
        if isinstance(node, ast.JoinedStr):
            for part in node.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    yield part.value

def test_from_scratch():
    src=open(SCRIPT,"r",encoding="utf-8",errors="ignore").read()
    tree=ast.parse(src, filename=SCRIPT)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mod_root=a.name.split(".")[0]
                assert mod_root not in BANNED_MODULES_STRICT, f"banned module import: {a.name}"
        elif isinstance(node, ast.ImportFrom):
            mod=node.module or ""
            mod_root=mod.split(".")[0]
            assert mod_root not in BANNED_MODULES_STRICT, f"banned module import from: {mod}"
        elif isinstance(node, ast.Call):
            fn=node.func
            name=fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
            assert name not in BANNED_CALLS, f"dynamic call not allowed ({name})"
        elif isinstance(node, ast.Attribute):
            attr=node.attr
            if attr.startswith("__") and attr.endswith("__") and attr not in ALLOWED_DUNDER_ATTRS:
                if attr in {"__dict__","__subclasses__","__mro__","__bases__","__code__","__globals__","__builtins__"}:
                    assert False, f"dunder not allowed ({attr})"
            if isinstance(node.value, ast.Name) and node.value.id == "os":
                assert attr not in BANNED_OS_ATTRS, f"banned os.{attr} usage"
    for lit in _iter_string_literals(tree):
        low=lit.lower()
        for banned in BANNED_TOKENS_FOR_PATH:
            assert banned.lower() not in low, f"forbidden path {banned!r} in {lit!r}"

@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    got=run_agent(path)
    expected=ground_truth_leak(path)
    assert got==expected, f"{os.path.basename(path)}: got {got} expected {expected}"
