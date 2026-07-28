"""Verify /app/solve.py reports mm^3 volume of OLED bond void .obvl cube
on HELD-OUT scans agent never saw.

Pixel OLED bonding QA uses under-display VCSEL diffuser IR scanner. OLED stack diffuses wide XY, bond thin -> narrow Z. Air bubbles appear bright due to scattering, anisotropic PSF creates saturated core + thin delam fingers with partial-volume dim values + dust speck artefacts far away. Threshold fails. Blur conserves energy, so true volume = sum(residual)/plateau * voxel_pitch.

Independent ground truth recomputed stdlib only with distinct heuristics vs oracle, so memorizing fails. 3%% tolerance.
"""
import ast, os, re, shutil, struct, subprocess, tempfile
import pytest

SCRIPT="/app/solve.py"
REL_TOL=0.03
HELDOUTS=[
    "/tests/data/heldout_1.obvl",
    "/tests/data/heldout_2.obvl",
    "/tests/data/heldout_3.obvl",
]

BANNED_MODULES={
    "numpy","scipy","skimage","cv2","PIL","Pillow","networkx","igraph","imageio","pandas","torch","tensorflow",
    "subprocess","importlib","runpy","ctypes","socket","multiprocessing","glob",
}
BANNED_CALLS={"eval","exec","compile","__import__"}
BANNED_TOKENS=[
    "/tests","test_outputs","heldout","os.system","os.popen","os.exec","os.walk","os.listdir","os.scandir","pty.",
    "importlib","runpy",
]

NEIGH=[(dx,dy,dz) for dz in (-1,0,1) for dy in (-1,0,1) for dx in (-1,0,1) if not (dx==0 and dy==0 and dz==0)]

def _parse(path):
    d=open(path,"rb").read()
    assert d[:4]==b"OBVL", f"{path}: bad magic {d[:4]}"
    dtype=struct.unpack_from("<I",d,8)[0]
    nx,ny,nz=struct.unpack_from("<III",d,12)
    sx,sy,sz=struct.unpack_from("<fff",d,24)
    off=struct.unpack_from("<I",d,36)[0]
    n=nx*ny*nz
    fmt={2: "<%dh", 16: "<%df"}[dtype] % n
    vals=[float(v) for v in struct.unpack_from(fmt,d,off)]
    return nx,ny,nz,float(sx),float(sy),float(sz),vals

def _median(sorted_vals):
    m=len(sorted_vals)
    if m==0: return 0.0
    return sorted_vals[m//2] if m%2 else 0.5*(sorted_vals[m//2-1]+sorted_vals[m//2])

def reference_volume_mm3(path):
    nx,ny,nz,sx,sy,sz,vals=_parse(path)
    n=nx*ny*nz
    def idx(x,y,z): return x+nx*(y+ny*z)
    sv=sorted(vals)
    bg=_median(sv)
    low_vals=[v for v in vals if v<bg]
    if not low_vals: low_vals=sv[:n//2]
    low_sorted=sorted(low_vals)
    med_low=_median(low_sorted)
    mad=_median(sorted(abs(v-med_low) for v in low_sorted))
    noise_sigma=max(1e-6,1.4826*mad)
    r=[v-bg for v in vals]
    thr=4.2*noise_sigma

    occ=[v>thr for v in r]
    seen=bytearray(n)
    best_mass=-1.0
    best_comp=None
    for z0 in range(nz):
        for y0 in range(ny):
            for x0 in range(nx):
                s=idx(x0,y0,z0)
                if not occ[s] or seen[s]: continue
                stack=[(x0,y0,z0)]
                seen[s]=1
                comp=[]
                mass=0.0
                while stack:
                    x,y,z=stack.pop()
                    cur=idx(x,y,z)
                    comp.append(cur)
                    mass+=r[cur]
                    for dx,dy,dz in NEIGH:
                        a=x+dx; b=y+dy; c=z+dz
                        if 0<=a<nx and 0<=b<ny and 0<=c<nz:
                            k=idx(a,b,c)
                            if occ[k] and not seen[k]:
                                seen[k]=1
                                stack.append((a,b,c))
                if mass>best_mass:
                    best_mass=mass
                    best_comp=comp
    assert best_comp, f"no bright region in {path}"
    filt=[]
    for j in best_comp:
        x=j%nx; y=(j//nx)%ny; z=j//(nx*ny)
        acc=0.0; cnt=0
        for dz in (-1,0,1):
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    a=min(max(x+dx,0),nx-1); b=min(max(y+dy,0),ny-1); c=min(max(z+dz,0),nz-1)
                    acc+=r[idx(a,b,c)]; cnt+=1
        filt.append(acc/cnt)
    filt.sort(reverse=True)
    top=filt[:max(1,min(8,len(filt)))]
    amp=_median(sorted(top))
    assert amp>0, f"non-positive amp in {path}"

    region=set(best_comp)
    frontier=set(best_comp)
    for _ in range(60):
        shell=set()
        for j in frontier:
            x=j%nx; y=(j//nx)%ny; z=j//(nx*ny)
            for dx,dy,dz in NEIGH:
                a,b,c=x+dx,y+dy,z+dz
                if 0<=a<nx and 0<=b<ny and 0<=c<nz:
                    k=idx(a,b,c)
                    if k not in region: shell.add(k)
        if not shell: break
        mean_shell=sum(r[j] for j in shell)/len(shell) if shell else 0.0
        if mean_shell<=0.9*noise_sigma: break
        region|=shell
        frontier=shell

    voxels=sum(r[j] for j in region)/amp
    return voxels*sx*sy*sz

def run_agent(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    with tempfile.TemporaryDirectory() as td:
        neutral=os.path.join(td,"scan.obvl")
        shutil.copyfile(path,neutral)
        proc=subprocess.run(["python3",SCRIPT,neutral], capture_output=True, text=True, timeout=120, cwd=td)
    assert proc.returncode==0, f"exit {proc.returncode} on {path}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    lines=[ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines, f"no stdout on {path}"
    last=lines[-1]
    try:
        return float(last)
    except ValueError:
        m=re.findall(r"[-+]?\d*\.\d+|[-+]?\d+",last)
        assert m, f"no numeric volume on last line: {last!r}"
        return float(m[-1])

def test_script_exists():
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"

def test_from_scratch():
    src=open(SCRIPT).read()
    tree=ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in BANNED_MODULES, f"banned module import: {a.name}"
                assert "test_output" not in a.name, "importing verifier not allowed"
        elif isinstance(node, ast.ImportFrom):
            mod=node.module or ""
            assert mod.split(".")[0] not in BANNED_MODULES, f"banned module import: {mod}"
            assert "test_output" not in mod, "importing verifier not allowed"
        elif isinstance(node, ast.Call):
            fn=node.func
            name=fn.id if isinstance(fn,ast.Name) else (fn.attr if isinstance(fn,ast.Attribute) else "")
            assert name not in BANNED_CALLS, f"dynamic execution not allowed ({name})"
    compact=re.sub(r"\s+","",src)
    for tok in BANNED_TOKENS:
        assert tok.replace(" ","") not in compact, f"forbidden usage ({tok})"

@pytest.mark.parametrize("path",HELDOUTS)
def test_heldout(path):
    got=run_agent(path)
    expected=reference_volume_mm3(path)
    assert abs(got-expected) <= REL_TOL*expected, f"{os.path.basename(path)}: got {got:.4f} mm3, expected {expected:.4f} mm3 (+/- {REL_TOL:.0%})"
