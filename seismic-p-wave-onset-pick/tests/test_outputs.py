"""Verify /app/solve.py reports P onset sample index on SEIS traces.

Ground truth is true P index from ground_truth.json.
Grading tolerance max(2 samples, 2 percent of S-P gap or 5 samples).
Traces have S larger than P and spike noise, variable dt and offset, P near edge.
Hardened isolation: _gen.py not mounted, solve.py executed in isolated temp dir with neutral copy.
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
import pytest

SCRIPT = "/app/solve.py"
HELDOUTS = [
    "/tests/data/heldout_1.seis",
    "/tests/data/heldout_2.seis",
    "/tests/data/heldout_3.seis",
    "/tests/data/heldout_4.seis",
    "/tests/data/heldout_5.seis",
    "/tests/data/heldout_6.seis",
    "/tests/data/heldout_7.seis",
    "/tests/data/heldout_8.seis",
]

BANNED_MODULES = {
    "numpy","scipy","obspy","pandas","torch","tensorflow","sklearn","skimage","cv2","PIL","Pillow","networkx","igraph","imageio","subprocess","importlib","runpy","ctypes","socket","multiprocessing","glob","pathlib","shutil","io","pty"
}
BANNED_MODULES_STRICT = BANNED_MODULES | {"os"}
BANNED_CALLS = {"eval","exec","compile","__import__","getattr","setattr","hasattr","globals","locals","vars","dir","chr","ord","breakpoint"}
BANNED_TOKENS = ["/tests","test_outputs","heldout","_gen","ground_truth","reference"]
BANNED_OS_ATTRS = {"system","popen","exec","walk","listdir","scandir","open","stat","read","fdopen","path"}
BANNED_SUBSTR = ["/tests","tests/data","heldout","_gen","test_output"]

ALLOWED_DUNDER = {"__name__","__main__"}

def _parse(path):
    d=open(path,"rb").read()
    assert d[:4]==b"SEIS", f"{path} bad magic"
    off=struct.unpack_from("<I",d,8)[0]
    n=struct.unpack_from("<I",d,12)[0]
    fmt=f"<{n}h"
    vals=[float(v) for v in struct.unpack_from(fmt,d,off)]
    dt=struct.unpack_from("<f",d,16)[0]
    return n,dt,vals

def ground_truth(path):
    for base in ["/tests/data/ground_truth.json","tests/data/ground_truth.json"]:
        if os.path.exists(base):
            gt=json.load(open(base))
            fn=os.path.basename(path)
            if fn in gt:
                return int(gt[fn])
    return 0

def run_agent(path):
    assert os.path.exists(SCRIPT), f"{SCRIPT} not found"
    with tempfile.TemporaryDirectory() as td:
        neutral=os.path.join(td,"trace.seis")
        shutil.copyfile(path, neutral)
        isolated=os.path.join(td,"solve.py")
        shutil.copyfile(SCRIPT, isolated)
        env=os.environ.copy()
        env["PYTHONPATH"]=td
        proc=subprocess.run([sys.executable, isolated, neutral], capture_output=True, text=True, timeout=60, cwd=td, env=env)
    assert proc.returncode==0, f"exit {proc.returncode} on {path}\nstdout:{proc.stdout}\nstderr:{proc.stderr}"
    lines=[ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines, f"no stdout on {path}"
    last=lines[-1]
    m=re.findall(r"-?\d+", last)
    assert m, f"no int on last line {last!r}"
    return int(m[-1])

def test_script_exists():
    assert os.path.exists(SCRIPT)

def _iter_lits(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            v=node.value
            if isinstance(v,str):
                yield v
            elif isinstance(v,(bytes,bytearray)):
                try:
                    yield v.decode("utf-8",errors="ignore")
                except:
                    continue
        if isinstance(node, ast.JoinedStr):
            for p in node.values:
                if isinstance(p, ast.Constant) and isinstance(p.value,str):
                    yield p.value

def test_from_scratch():
    src=open(SCRIPT,"r",encoding="utf-8",errors="ignore").read()
    tree=ast.parse(src, filename=SCRIPT)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                root=a.name.split(".")[0]
                assert root not in BANNED_MODULES_STRICT, f"banned import {a.name}"
                assert "test_output" not in a.name.lower()
                assert "_gen" not in a.name.lower()
        elif isinstance(node, ast.ImportFrom):
            mod=node.module or ""
            root=mod.split(".")[0]
            assert root not in BANNED_MODULES_STRICT, f"banned from {mod}"
        elif isinstance(node, ast.Call):
            fn=node.func
            name=fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
            assert name not in BANNED_CALLS, f"banned call {name}"
        elif isinstance(node, ast.Attribute):
            attr=node.attr
            if attr.startswith("__") and attr.endswith("__") and attr not in ALLOWED_DUNDER:
                if attr in {"__dict__","__subclasses__","__mro__","__bases__","__code__","__globals__","__builtins__"}:
                    assert False, f"dunder {attr} not allowed"
            if isinstance(node.value, ast.Name) and node.value.id=="os":
                assert attr not in BANNED_OS_ATTRS, f"banned os.{attr}"
    for lit in _iter_lits(tree):
        low=lit.lower()
        for b in BANNED_SUBSTR:
            assert b.lower() not in low, f"forbidden {b!r} in {lit!r}"

@pytest.mark.parametrize("path", HELDOUTS)
def test_heldout(path):
    got=run_agent(path)
    exp=ground_truth(path)
    tol=max(2, int(0.02*exp)+2)  # at least 2, more generous for edge
    # tighter: 5 samples absolute, but also allow small percent
    tol = max(5, tol)
    assert abs(got-exp) <= tol, f"{os.path.basename(path)} got {got} exp {exp} +- {tol}"

def test_data_offset_varied():
    offs=set()
    for p in HELDOUTS:
        d=open(p,"rb").read()
        off=struct.unpack_from("<I",d,8)[0]
        offs.add(off)
    assert len(offs)>1, f"expected varied offset, got {offs}"
    assert any(o!=64 for o in offs)

def test_amplitude_pick_fails():
    """Max amplitude picks S, not P, should fail at least 2 heldouts"""
    fails=0
    for p in HELDOUTS:
        n,dt,vals=_parse(p)
        # naive max abs amplitude index
        max_idx = max(range(len(vals)), key=lambda i: abs(vals[i]))
        exp=ground_truth(p)
        tol=max(5, int(0.02*exp)+2)
        if abs(max_idx-exp) > tol:
            fails+=1
    assert fails>=2, "expected max amplitude shortcut to fail on at least 2 maps where S larger than P"

def test_fixed_window_fails():
    """Hardcoding STA 25 samples LTA 100 samples should fail when dt varies 0.001 vs 0.004"""
    fails=0
    for p in HELDOUTS:
        n,dt,vals=_parse(p)
        # simple fixed window STA/LTA without dt scaling (common mistake)
        # use fixed 25 and 100 samples
        def cumsum(arr):
            cs=[0]
            for x in arr:
                cs.append(cs[-1]+abs(x))
            return cs
        cs=cumsum(vals)
        def mean_abs(a,b):
            if a<0: a=0
            if b>n: b=n
            if b<=a: return 0
            return (cs[b]-cs[a])/(b-a)
        sta_n_fixed=25
        lta_n_fixed=100
        # find first ratio >3.5 with fixed windows
        got=0
        for i in range(100,n):
            sta=mean_abs(i-sta_n_fixed+1,i+1)
            lta=mean_abs(i-sta_n_fixed-lta_n_fixed+1,i-sta_n_fixed+1)
            if lta==0: continue
            if sta/lta > 3.5 and abs(vals[i])>20:
                got=i
                break
        exp=ground_truth(p)
        tol=max(5, int(0.02*exp)+2)
        if abs(got-exp) > tol:
            fails+=1
    assert fails>=2, "expected fixed sample window to fail when dt varies"
