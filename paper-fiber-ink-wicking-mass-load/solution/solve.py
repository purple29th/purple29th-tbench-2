#!/usr/bin/env python3
import struct
import sys

MAGIC = b"INKW"
RHO = 0.85

NEIGH8 = [(dx,dy) for dy in (-1,0,1) for dx in (-1,0,1) if dx or dy]

def parse_inkw(path):
    d=open(path,"rb").read()
    if d[:4]!=MAGIC:
        raise ValueError("bad magic")
    dtype=struct.unpack_from("<I", d, 8)[0]
    nx,ny=struct.unpack_from("<II", d, 12)
    sx,sy=struct.unpack_from("<ff", d, 20)
    off=struct.unpack_from("<I", d, 28)[0]
    gain=1.0
    try:
        gain=struct.unpack_from("<f", d, 40)[0]
    except:
        gain=1.0
    n=nx*ny
    if dtype==2:
        vals=list(struct.unpack_from("<%dh"%n, d, off))
    else:
        vals=list(struct.unpack_from("<%df"%n, d, off))
    return nx,ny,float(sx),float(sy),float(gain),[float(v) for v in vals]

def median_calc(a):
    s=sorted(a)
    m=len(s)//2
    return s[m] if len(s)%2==1 else 0.5*(s[m-1]+s[m])

def solve(p):
    nx,ny,sx,sy,gain,vox=parse_inkw(p)
    n=nx*ny
    def idx(x,y): return x+nx*y
    order=sorted(vox)
    bg=median_calc(order[:int(n*0.7)])
    low=order[:n//2]
    ml=median_calc(low)
    mad=median_calc(sorted(abs(v-ml) for v in low))
    sig=max(1e-6,1.4826*mad)
    res=[v-bg for v in vox]
    thr=4.0*sig
    occ=[r>thr for r in res]
    seen=[False]*n
    comps=[]
    for y0 in range(ny):
        for x0 in range(nx):
            i0=idx(x0,y0)
            if not occ[i0] or seen[i0]: continue
            stack=[(x0,y0)]
            seen[i0]=True
            comp=[]; mass=0.0
            min_x=max_x=x0; min_y=max_y=y0
            while stack:
                x,y=stack.pop()
                k=idx(x,y)
                comp.append(k); mass+=res[k]
                min_x=min(min_x,x); max_x=max(max_x,x); min_y=min(min_y,y); max_y=max(max_y,y)
                for dx,dy in NEIGH8:
                    a,b=x+dx,y+dy
                    if 0<=a<nx and 0<=b<ny:
                        kk=idx(a,b)
                        if occ[kk] and not seen[kk]:
                            seen[kk]=True
                            stack.append((a,b))
            dx_=max_x-min_x+1
            dy_=max_y-min_y+1
            dims=sorted([dx_,dy_])
            is_elong=dims[1]>=10 and dims[1]>1.6*dims[0] and dims[1]<=35
            comps.append((mass,comp,dx_,dy_,is_elong))
    if not comps:
        print(0)
        return
    comps.sort(key=lambda x:x[0], reverse=True)
    largest=comps[0][0]
    main_groups=[]
    for mass,comp,dx,dy,is_elong in comps:
        if is_elong and mass>=0.35*largest:
            main_groups.append(comp)
    if not main_groups:
        main_groups=[comps[0][1]]
    best=[]
    for g in main_groups:
        best.extend(g)
    kept=set(best)
    dust=set()
    for _,comp,_,_,_ in comps:
        for ii in comp:
            if ii not in kept:
                dust.add(ii)
    peak=[res[j] for j in best]
    peak.sort(reverse=True)
    top=peak[:max(1,min(4,len(peak)))]
    plat=sum(top)/len(top) if top else 0
    if plat<=0:
        print(0)
        return
    region=set(best)
    frontier=set(best)
    floor=1.0*sig
    for _ in range(50):
        shell=set()
        for j in frontier:
            x=j%nx; y=j//nx
            for dx,dy in NEIGH8:
                a,b=x+dx,y+dy
                if 0<=a<nx and 0<=b<ny:
                    k=idx(a,b)
                    if k not in region and k not in dust:
                        shell.add(k)
        if not shell: break
        if sum(res[k] for k in shell)/len(shell) <= floor:
            break
        region|=shell
        frontier=shell
    tot=sum(res[k] for k in region)
    area=tot/plat * sx * sy if plat else 0
    mass=area * RHO * gain
    print(mass)

if __name__=="__main__":
    solve(sys.argv[1] if len(sys.argv)>1 else "/app/data/scene.inkw")
