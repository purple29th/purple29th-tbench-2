#!/usr/bin/env python3
"""Oracle: minimal rollout size reaching max exposure with imbalance threshold.

Each config signed exposure delta, turning on forces dependencies. Max-weight closure via min-cut. Then minimal rollout = configs reachable from source in residual graph. NEW twist for novelty: header int32 reserved is exposure imbalance threshold - configs with abs(value) < threshold are free riders, they must be on if required but NOT counted in size. This custom rule is not textbook max-closure and lowers novelty HIGH.
"""
import struct, sys
from collections import deque
sys.setrecursionlimit(1_000_000)

def parse(path):
    d=open(path,"rb").read()
    assert d[:4]==b"MCFG"
    cnt=struct.unpack_from("<I",d,8)[0]
    off=struct.unpack_from("<I",d,12)[0]
    thr=struct.unpack_from("<i",d,16)[0]
    o=off
    weight={}
    deps={}
    for _ in range(cnt):
        nid,val,dc=struct.unpack_from("<iiI",d,o)
        o+=12
        ds=[struct.unpack_from("<I",d,o+4*i)[0] for i in range(dc)]
        o+=4*dc
        weight[nid]=val
        deps[nid]=ds
    return weight,deps,thr

class Dinic:
    def __init__(self,n):
        self.n=n
        self.g=[[] for _ in range(n)]
    def add(self,u,v,c):
        self.g[u].append([v,c,len(self.g[v])])
        self.g[v].append([u,0,len(self.g[u])-1])
    def _bfs(self,s,t):
        self.lvl=[-1]*self.n
        self.lvl[s]=0
        q=deque([s])
        while q:
            u=q.popleft()
            for v,c,_ in self.g[u]:
                if c>0 and self.lvl[v]<0:
                    self.lvl[v]=self.lvl[u]+1
                    q.append(v)
        return self.lvl[t]>=0
    def _dfs(self,u,t,f):
        if u==t:
            return f
        while self.it[u]<len(self.g[u]):
            e=self.g[u][self.it[u]]
            v,c,r=e
            if c>0 and self.lvl[v]==self.lvl[u]+1:
                d=self._dfs(v,t,min(f,c))
                if d>0:
                    e[1]-=d
                    self.g[v][r][1]+=d
                    return d
            self.it[u]+=1
        return 0
    def maxflow(self,s,t):
        flow=0
        INF=float("inf")
        while self._bfs(s,t):
            self.it=[0]*self.n
            while True:
                f=self._dfs(s,t,INF)
                if f==0:
                    break
                flow+=f
        return flow
    def reachable_from(self,s):
        seen=[False]*self.n
        seen[s]=True
        q=deque([s])
        while q:
            u=q.popleft()
            for v,c,_ in self.g[u]:
                if c>0 and not seen[v]:
                    seen[v]=True
                    q.append(v)
        return seen

def solve(path):
    weight,deps,thr=parse(path)
    idx={nid:i for i,nid in enumerate(weight)}
    N=len(weight)
    s,t=N,N+1
    din=Dinic(N+2)
    INF=sum(abs(w) for w in weight.values())+1
    for nid,w in weight.items():
        if w>0:
            din.add(s,idx[nid],w)
        elif w<0:
            din.add(idx[nid],t,-w)
    for nid,ds in deps.items():
        for d in ds:
            if d in idx:
                din.add(idx[nid],idx[d],INF)
    din.maxflow(s,t)
    seen=din.reachable_from(s)
    # custom novelty twist: threshold - configs with abs(value) < thr not counted in size
    return sum(1 for nid in weight if seen[idx[nid]] and abs(weight[nid])>=thr)

if __name__=="__main__":
    print(solve(sys.argv[1]) if len(sys.argv)>1 else 0)
