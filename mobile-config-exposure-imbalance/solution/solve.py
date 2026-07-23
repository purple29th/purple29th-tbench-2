#!/usr/bin/env python3
"""Oracle: maximum-weight dependency closure (project selection), from scratch.

Choose a set S of configs to activate. If config u is in S, every config it
depends on (that exists in the file) must also be in S. Each config has a signed
exposure weight. Maximise the total weight of S; the empty set (0) is always
allowed; if the best total is below the header threshold, print 0.

Key insight: this is the maximum-weight closure problem, solved by a min-cut.
Build a flow network with a super source s and super sink t:
  * s -> v with capacity  w   for every config with weight w > 0  (and add w to P)
  * v -> t with capacity -w   for every config with weight w < 0
  * u -> v with capacity INF  for every dependency edge (u depends on v)
The maximum closure weight is  P - maxflow(s, t).

Parsed from raw bytes with struct; standard library only.
"""
import struct
import sys
from collections import deque

sys.setrecursionlimit(1_000_000)


def parse(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:4] == b"MCFG", "bad magic"
    cnt = struct.unpack_from("<I", data, 8)[0]
    off = struct.unpack_from("<I", data, 12)[0]
    thr = struct.unpack_from("<i", data, 16)[0]
    o = off
    weight = {}
    deps = {}
    for _ in range(cnt):
        nid, val, dc = struct.unpack_from("<iiI", data, o)
        o += 12
        ds = [struct.unpack_from("<I", data, o + 4 * i)[0] for i in range(dc)]
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

    def _dfs(self, u, t, f):
        if u == t:
            return f
        while self.it[u] < len(self.g[u]):
            e = self.g[u][self.it[u]]
            v, c, r = e
            if c > 0 and self.lvl[v] == self.lvl[u] + 1:
                d = self._dfs(v, t, min(f, c))
                if d > 0:
                    e[1] -= d
                    self.g[v][r][1] += d
                    return d
            self.it[u] += 1
        return 0

    def maxflow(self, s, t):
        flow = 0
        INF = float("inf")
        while self._bfs(s, t):
            self.it = [0] * self.n
            while True:
                f = self._dfs(s, t, INF)
                if f == 0:
                    break
                flow += f
        return flow


def solve(path):
    weight, deps, thr = parse(path)
    idx = {nid: i for i, nid in enumerate(weight)}
    N = len(weight)
    s, t = N, N + 1
    din = Dinic(N + 2)
    INF = sum(abs(w) for w in weight.values()) + 1
    pos = 0
    for nid, w in weight.items():
        if w > 0:
            din.add(s, idx[nid], w)
            pos += w
        elif w < 0:
            din.add(idx[nid], t, -w)
    for nid, ds in deps.items():
        for d in ds:
            if d in idx:                       # dangling deps impose no constraint
                din.add(idx[nid], idx[d], INF)
    best = pos - din.maxflow(s, t)
    return best if best >= thr else 0


if __name__ == "__main__":
    print(solve(sys.argv[1]) if len(sys.argv) > 1 else 0)
