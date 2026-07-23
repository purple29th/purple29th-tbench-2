import os, struct, subprocess, pytest

SCRIPT = "/app/solve.py"
HELDOUTS = [
    "/tests/data/heldout_1.mcfg",
    "/tests/data/heldout_2.mcfg",
    "/tests/data/heldout_3.mcfg",
]
HEADER = 64


def ref(p):
    """
    Independent oracle using different traversal order than solution.
    Parses MCFG, filters reachable from root 0, finds mutual dependency groups, excludes root value, checks threshold.
    """
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
    # reachable from root 0
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

    # lowlink iterative method independent from solution order
    index = 0
    indices = {}
    lowlink = {}
    onstack = set()
    tarjan_stack = []
    sccs = []
    call_stack = []

    for start in reachable:
        if start in indices:
            continue
        call_stack.append([start, 0])
        while call_stack:
            v, child_idx = call_stack[-1]
            if child_idx == 0:
                if v not in indices:
                    indices[v] = index
                    lowlink[v] = index
                    index += 1
                    tarjan_stack.append(v)
                    onstack.add(v)
            neighbors = adj_reach.get(v, [])
            if child_idx < len(neighbors):
                w = neighbors[child_idx]
                call_stack[-1][1] += 1
                if w not in indices:
                    call_stack.append([w, 0])
                elif w in onstack:
                    lowlink[v] = min(lowlink[v], indices[w])
            else:
                if lowlink[v] == indices[v]:
                    comp = []
                    while True:
                        w = tarjan_stack.pop()
                        onstack.remove(w)
                        comp.append(w)
                        if w == v:
                            break
                    sccs.append(comp)
                call_stack.pop()
                if call_stack:
                    parent_v = call_stack[-1][0]
                    if v in lowlink:
                        lowlink[parent_v] = min(lowlink[parent_v], lowlink[v])

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
    ]:
        assert b not in s


@pytest.mark.parametrize("p", HELDOUTS)
def test_heldout(p):
    assert run(p) == ref(p)
