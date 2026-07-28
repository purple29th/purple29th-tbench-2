"""Verify /app/solve.py reports count of fingerprint oil smear pixels .fpos on heldouts."""
import ast, os, re, shutil, struct, subprocess, sys, tempfile, json
import pytest
from collections import deque

SCRIPT="/app/solve.py"
HELDOUTS=[
    "/tests/data/heldout_1.fpos",
    "/tests/data/heldout_2.fpos",
    "/tests/data/heldout_3.fpos",
    "/tests/data/heldout_4.fpos",
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

def _parse(path):
    d=open(path,"rb").read()
    assert d[:4]==b"FPOS", f"{path}: bad magic {d[:4]}"
    total=struct.unpack_from("<I",d,8)[0]
    off=struct.unpack_from("<I",d,12)[0]
    sx=struct.unpack_from("<f",d,16)[0]
    sy=struct.unpack_from("<f",d,20)[0]
    baseline=struct.unpack_from("<I",d,24)[0]
    nx,ny=struct.unpack_from("<II",d,28)
    n=nx*ny
    fmt="<%dh" % n
    vals=[float(v) for v in struct.unpack_from(fmt,d,off)]
    return nx,ny,float(sx),float(sy),int(baseline),vals

def _median(s):
    m=len(s)
    if m==0:
        return 0.0
    return s[m//2] if m%2 else 0.5*(s[m//2-1]+s[m//2])

def ground_truth_count(path):
    for base in ["/tests/data/ground_truth.json","tests/data/ground_truth.json"]:
        if os.path.exists(base):
            gt=json.load(open(base))
            fname=os.path.basename(path)
            if fname in gt:
                return int(gt[fname])
    return reference_count(path)

def reference_count(path):
    nx,ny,sx,sy,baseline,vals=_parse(path)
    n=nx*ny
    def idx(x,y): return x+nx*y
    sv=sorted(vals)
    bg=_median(sv)
    low=[v for v in vals if v<bg]
    if not low:
        low=sv[:n//2]
    low_sorted=sorted(low)
    med_low=_median(low_sorted)
    mad=_median(sorted(abs(v-med_low) for v in low_sorted))
    noise_sigma=max(1e-6,1.4826*mad)
    r=[v-bg for v in vals]
    thr=4.0*noise_sigma
    occ=[v>thr for v in r]
    seen=bytearray(n)
    NEIGH=[(dx,dy) for dy in (-1,0,1) for dx in (-1,0,1) if not (dx==0 and dy==0)]
    best_mass=-1.0
    best_comp=None
    for y0 in range(ny):
        for x0 in range(nx):
            s=idx(x0,y0)
            if not occ[s] or seen[s]:
                continue
            stack=[(x0,y0)]
            seen[s]=1
            comp=[]
            mass=0.0
            while stack:
                x,y=stack.pop()
                cur=idx(x,y)
                comp.append(cur)
                mass+=r[cur]
                for dx,dy in NEIGH:
                    a=x+dx
                    b=y+dy
                    if 0<=a<nx and 0<=b<ny:
                        k=idx(a,b)
                        if occ[k] and not seen[k]:
                            seen[k]=1
                            stack.append((a,b))
            if mass>best_mass:
                best_mass=mass
                best_comp=comp
    assert best_comp
    filt=[]
    for j in best_comp:
        x=j%nx
        y=j//nx
        acc=0.0
        cnt=0
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                a=min(max(x+dx,0),nx-1)
                b=min(max(y+dy,0),ny-1)
                acc+=r[idx(a,b)]
                cnt+=1
        filt.append(acc/cnt)
    filt.sort(reverse=True)
    top=filt[:max(1,min(8,len(filt)))]
    amp=_median(sorted(top))
    assert amp>0
    region=set(best_comp)
    frontier=set(best_comp)
    for _ in range(50):
        shell=set()
        for j in frontier:
            x=j%nx
            y=j//nx
            for dx,dy in NEIGH:
                a=x+dx
                b=y+dy
                if 0<=a<nx and 0<=b<ny:
                    k=idx(a,b)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        mean_shell=sum(r[j] for j in shell)/len(shell) if shell else 0.0
        if mean_shell<=1.0*noise_sigma:
            break
        region|=shell
        frontier=shell
    pixels=sum(r[j] for j in region)/amp
    return int(round(pixels))

def run_agent(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    with tempfile.TemporaryDirectory() as td:
        neutral=os.path.join(td,"scan.fpos")
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
    assert m, f"no numeric count on last line: {last!r}"
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
    expected=ground_truth_count(path)
    tol=max(2, int(0.03*expected))
    assert abs(got-expected) <= tol, f"{os.path.basename(path)}: got {got} expected {expected} +- {tol}"
