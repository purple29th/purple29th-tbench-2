#!/usr/bin/env python3
"""Oracle: minimal rollout size reaching max exposure with imbalance threshold.

Each config has signed exposure delta. Turning on forces dependencies transitively, but free riders with abs(value) < threshold have their own dependencies ignored, changing the closure graph itself. Among optimal exposure rollouts, report minimal counted size where only abs(value) >= threshold counted. This free rider dependency ignore rule is custom and not textbook closure.
"""

import struct, sys
from collections import deque

sys.setrecursionlimit(1_000_000)


def parse(path):
    d = open(path, "rb").read()
    assert d[:4] == b"MCFG"
    cnt = struct.unpack_from("<I", d, 8)[0]
    off = struct.unpack_from("<I", d, 12)[0]
    thr = struct.unpack_from("<i", d, 16)[0]
    o = off
    weight = {}
    deps = {}
    for _ in range(cnt):
        nid, val, dc = struct.unpack_from("<iiI", d, o)
        o += 12
        raw = [struct.unpack_from("<I", d, o + 4 * i)[0] for i in range(dc)]
        # dep ids stored as uint32 but may be negative signed ids (two's complement)
        ds = [r - (1 << 32) if r >= (1 << 31) else r for r in raw]
        o += 4 * dc
        weight[nid] = val
        deps[nid] = ds
    return weight, deps, thr


class Dinic:
    def __init__(self, n):
        self.n = n
        self.g = [[] for _ in range(n)]

    def add(self, u, v, c):
        self.g[u].append([v, c, len(self.g[v])])
        self.g[v].append([u, 0, len(self.g[u]) - 1])

    def _bfs(self, s, t):
        self.lvl = [-1] * self.n
        self.lvl[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for v, c, _ in self.g[u]:
                if c > 0 and self.lvl[v] < 0:
                    self.lvl[v] = self.lvl[u] + 1
                    q.append(v)
        return self.lvl[t] >= 0

    def _dfs_iter(self, s, t, flow_limit):
        # iterative DFS for blocking flow - avoids recursion, handles 2000 chain
        stack = [(s, flow_limit, 0)]  # node, flow up to node, next edge index to try
        path = []  # list of (u, edge_idx, v, rev_idx)
        while stack:
            u, f, i = stack[-1]
            if u == t:
                # augment path
                for pu, ei, pv, ri in path:
                    self.g[pu][ei][1] -= f
                    self.g[pv][ri][1] += f
                return f
            if i < len(self.g[u]):
                # advance iterator pointer for current node
                v, c, r = self.g[u][i]
                stack[-1] = (u, f, i + 1)
                if c > 0 and self.lvl[v] == self.lvl[u] + 1:
                    path.append((u, i, v, r))
                    stack.append((v, f if f < c else c, 0))
            else:
                stack.pop()
                if path:
                    path.pop()
        return 0

    def maxflow(self, s, t):
        flow = 0
        INF = 10**18
        while self._bfs(s, t):
            while True:
                pushed = self._dfs_iter(s, t, INF)
                if pushed == 0:
                    break
                flow += pushed
        return flow

    def reachable_from(self, s):
        seen = [False] * self.n
        seen[s] = True
        q = deque([s])
        while q:
            u = q.popleft()
            for v, c, _ in self.g[u]:
                if c > 0 and not seen[v]:
                    seen[v] = True
                    q.append(v)
        return seen


def solve(path):
    weight, deps, thr = parse(path)
    idx = {nid: i for i, nid in enumerate(weight)}
    N = len(weight)
    s, t = N, N + 1
    din = Dinic(N + 2)
    INF = sum(abs(w) for w in weight.values()) + 1
    for nid, w in weight.items():
        if w > 0:
            din.add(s, idx[nid], w)
        elif w < 0:
            din.add(idx[nid], t, -w)
    for nid, ds in deps.items():
        # free riders ignore their own dependencies - changes graph itself, not just counting
        if abs(weight[nid]) < thr:
            continue
        for d in ds:
            if d in idx:
                din.add(idx[nid], idx[d], INF)
    din.maxflow(s, t)
    seen = din.reachable_from(s)
    # threshold - configs with abs(value) < thr not counted in size, free riders exempt
    return sum(1 for nid in weight if seen[idx[nid]] and abs(weight[nid]) >= thr)


if __name__ == "__main__":
    print(solve(sys.argv[1]) if len(sys.argv) > 1 else 0)
