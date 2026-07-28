"""Verify /app/solve.py reports count of ink affected touch cells .cdmr map
on HELD-OUT scans agent never saw.

Capacitive touch mura QA uses diffuser, ink pooling bright with saturated core + thin bleed fingers and dust. Threshold fails. Charge conserved: true count = sum residual / plateau.

Ground truth is geometric true count from generator integral sum occupancy rounded, stored in ground_truth.json. Heuristic reference matches true within 1 percent but grading uses true count with 3 percent tolerance.

Hardened isolation:
- _gen.py not mounted, only .cdmr heldouts and ground_truth.json
- solve.py executed in isolated TemporaryDirectory with neutral copy
- test_from_scratch bans pathlib os io shutil chr getattr base64 dunder and decodes literals for /tests paths
"""
import ast, os, re, shutil, struct, subprocess, sys, tempfile, json
import pytest

SCRIPT="/app/solve.py"
REL_TOL=0.03
HELDOUTS=[
    "/tests/data/heldout_1.cdmr",
    "/tests/data/heldout_2.cdmr",
    "/tests/data/heldout_3.cdmr",
]

BANNED_MODULES={
    "numpy","scipy","skimage","cv2","PIL","Pillow","networkx","igraph","imageio","pandas","torch","tensorflow",
    "subprocess","importlib","runpy","ctypes","socket","multiprocessing","glob","pathlib","shutil","io",
}
BANNED_MODULES_STRICT=BANNED_MODULES|{"os"}
BANNED_CALLS={"eval","exec","compile","__import__","getattr","setattr","hasattr","globals","locals","vars","dir","chr","ord","breakpoint"}
BANNED_TOKENS=[
    "/tests","test_outputs","heldout","_gen",
    "os.system","os.popen","os.exec","os.walk","os.listdir","os.scandir",
    "os.open","os.stat","os.read","os.fdopen","os.path",
    "pty.","importlib","runpy","pathlib","Path(","shutil","io.open",
    "builtins","dict","subclasses","mro",
    "base64","binascii","codecs",
]
BANNED_SUBSTRINGS_IN_STRLITS=["/tests","tests/data","heldout","_gen","test_output","test_outputs"]
ALLOWED_DUNDER_ATTRS={"__name__","__main__"}

NEIGH=[(dx,dy) for dy in (-1,0,1) for dx in (-1,0,1) if not (dx==0 and dy==0)]

def _parse(path):
    d=open(path,"rb").read()
    assert d[:4]==b"CDMR", f"{path}: bad magic {d[:4]}"
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
        neutral=os.path.join(td,"scan.cdmr")
        shutil.copyfile(path,neutral)
        isolated_script=os.path.join(td,"solve.py")
        shutil.copyfile(SCRIPT, isolated_script)
        env=os.environ.copy()
        env["PYTHONPATH"]=td
        proc=subprocess.run([sys.executable, isolated_script, neutral], capture_output=True, text=True, timeout=120, cwd=td, env=env)
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
                assert "test_output" not in a.name.lower(), "importing verifier not allowed"
                assert "_gen" not in a.name.lower(), "importing generator not allowed"
        elif isinstance(node, ast.ImportFrom):
            mod=node.module or ""
            mod_root=mod.split(".")[0]
            assert mod_root not in BANNED_MODULES_STRICT, f"banned module import from: {mod}"
            assert "test_output" not in mod.lower(), "importing verifier not allowed"
            assert "_gen" not in mod.lower(), "importing generator not allowed"
        elif isinstance(node, ast.Call):
            fn=node.func
            name=""
            if isinstance(fn, ast.Name):
                name=fn.id
            elif isinstance(fn, ast.Attribute):
                name=fn.attr
            assert name not in BANNED_CALLS, f"dynamic call not allowed ({name})"
            if isinstance(fn, ast.Name) and fn.id in BANNED_CALLS:
                raise AssertionError(f"banned call {fn.id}")
        elif isinstance(node, ast.Attribute):
            attr=node.attr
            if attr.startswith("__") and attr.endswith("__") and attr not in ALLOWED_DUNDER_ATTRS:
                assert False, f"dunder not allowed ({attr})"
            if attr in {"__dict__","__subclasses__","__mro__","__bases__","__code__","__globals__"}:
                assert False, f"introspection not allowed ({attr})"
    for lit in _iter_string_literals(tree):
        low=lit.lower()
        for banned in BANNED_SUBSTRINGS_IN_STRLITS:
            assert banned.lower() not in low, f"forbidden path {banned!r} in {lit!r}"
    compact=re.sub(r"\s+", "", src)
    compact_low=compact.lower()
    for tok in BANNED_TOKENS:
        t=tok.replace(" ", "")
        if t.lower() in ("pathlib","shutil","base64","binascii","codecs","importlib","runpy"):
            assert t.lower() not in compact_low, f"forbidden usage {tok}"
        else:
            assert t not in compact, f"forbidden usage {tok}"

@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    got=run_agent(path)
    expected=ground_truth_count(path)
    heur=reference_count(path)
    assert abs(heur-expected) <= max(2, 0.02*expected), f"heuristic diverged from true: heur {heur} true {expected}"
    tol=max(2, int(0.03*expected))
    assert abs(got-expected) <= tol, f"{os.path.basename(path)}: got {got} expected true {expected} +- {tol} heuristic {heur}"
