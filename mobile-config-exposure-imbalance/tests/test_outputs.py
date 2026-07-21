import os, struct, subprocess, pytest

SCRIPT = "/app/solve.py"
HELDOUTS = [
    "/tests/data/heldout_1.mcfg",
    "/tests/data/heldout_2.mcfg",
    "/tests/data/heldout_3.mcfg",
]
HEADER = 64


def ref(p):
    d = open(p, "rb").read()
    assert d[:4] == b"MCFG"
    cnt = struct.unpack_from("<I", d, 8)[0]
    off = struct.unpack_from("<I", d, 12)[0]
    adj = {}
    nodes = {}
    o = off
    for _ in range(cnt):
        nid, val, dc = struct.unpack_from("<iiI", d, o)
        o += 12
        deps = []
        for _ in range(dc):
            deps.append(struct.unpack_from("<I", d, o)[0])
            o += 4
        nodes[nid] = val
        for c in deps:
            adj.setdefault(nid, []).append(c)
    stack = [0]
    seen = set()
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        for ch in adj.get(n, []):
            if ch not in seen:
                stack.append(ch)
    reachable = seen
    order = []
    vis = set()

    def dfs(v):
        vis.add(v)
        for nb in adj.get(v, []):
            if nb in reachable and nb not in vis:
                dfs(nb)
        order.append(v)

    for v in reachable:
        if v not in vis:
            dfs(v)
    radj = {}
    for p in adj:
        for c in adj[p]:
            if p in reachable and c in reachable:
                radj.setdefault(c, []).append(p)
    vis2 = set()
    sccs = []

    def rdfs(v, comp):
        vis2.add(v)
        comp.append(v)
        for nb in radj.get(v, []):
            if nb not in vis2:
                rdfs(nb, comp)

    for v in reversed(order):
        if v not in vis2:
            comp = []
            rdfs(v, comp)
            sccs.append(comp)
    best = 0
    for scc in sccs:
        s = sum(nodes.get(n, 0) for n in scc if n != 0)
        if s > best:
            best = s
    return best


def run(p):
    assert os.path.exists(SCRIPT)
    o = subprocess.run(
        ["python3", SCRIPT, p], capture_output=True, text=True, timeout=60
    )
    assert o.returncode == 0
    return int(o.stdout.strip().split()[-1])


def test_exists():
    assert os.path.exists(SCRIPT)


def test_from_scratch():
    s = open(SCRIPT).read().replace(" ", "")
    for b in [
        "networkx",
        "igraph",
        "importnumpy",
        "importpandas",
        "importscipy",
        "subprocess.",
        "os.system",
        "os.popen",
        "__import__(",
        "importlib",
        "getattr",
        "eval(",
        "exec(",
        "compile(",
        "ctypes",
    ]:
        assert b not in s


@pytest.mark.parametrize("p", HELDOUTS)
def test_heldout(p):
    assert run(p) == ref(p)
