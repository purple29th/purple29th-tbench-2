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
    threshold = struct.unpack_from("<I", d, 16)[0]
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
    adj_reach = {}
    for v in reachable:
        adj_reach[v] = [nb for nb in adj.get(v, []) if nb in reachable]
    order = []
    vis = set()
    for start in reachable:
        if start in vis:
            continue
        dfs_stack = [(start, 0)]
        while dfs_stack:
            v, idx = dfs_stack[-1]
            if idx == 0:
                if v in vis:
                    dfs_stack.pop()
                    continue
                vis.add(v)
            neighbors = adj_reach.get(v, [])
            if idx < len(neighbors):
                w = neighbors[idx]
                dfs_stack[-1] = (v, idx + 1)
                if w not in vis:
                    dfs_stack.append((w, 0))
            else:
                order.append(v)
                dfs_stack.pop()
    radj = {v: [] for v in reachable}
    for p in reachable:
        for c in adj_reach.get(p, []):
            radj[c].append(p)
    vis2 = set()
    sccs = []
    for v in reversed(order):
        if v not in vis2:
            comp_stack = [v]
            vis2.add(v)
            comp = []
            while comp_stack:
                cur = comp_stack.pop()
                comp.append(cur)
                for nb in radj.get(cur, []):
                    if nb not in vis2:
                        vis2.add(nb)
                        comp_stack.append(nb)
            sccs.append(comp)
    best = 0
    for scc in sccs:
        s = sum(nodes.get(n, 0) for n in scc if n != 0)
        if s >= threshold and s > best:
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
    s = open(SCRIPT).read().replace(" ", "").lower()
    for b in [
        "importnumpy",
        "fromnumpy",
        "importscipy",
        "fromscipy",
        "importnetworkx",
        "fromnetworkx",
        "importigraph",
        "fromigraph",
        "importpandas",
        "frompandas",
        "subprocess.",
        "os.system",
        "os.popen",
        "__import__(",
        "importlib",
        "eval(",
        "exec(",
        "compile(",
        "ctypes",
    ]:
        assert b not in s


@pytest.mark.parametrize("p", HELDOUTS)
def test_heldout(p):
    assert run(p) == ref(p)
