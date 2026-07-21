import sys, struct


def solve(p):
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
    # reachable from root id 0 iterative
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
    # Kosaraju first pass iterative
    order = []
    vis = set()
    adj_reach = {}
    for v in reachable:
        adj_reach[v] = [nb for nb in adj.get(v, []) if nb in reachable]
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
    radj = {}
    for v in reachable:
        radj[v] = []
    for p in reachable:
        for c in adj_reach.get(p, []):
            radj[c].append(p)
    vis2 = set()
    sccs = []
    for v in reversed(order):
        if v in vis2:
            continue
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


if __name__ == "__main__":
    print(solve(sys.argv[1]) if len(sys.argv) > 1 else 0)
