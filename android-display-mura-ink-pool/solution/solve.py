#!/usr/bin/env python3
"""Oracle for android-display-mura-ink-pool: count of ink affected touch cells via charge conservation."""
import struct, sys

def parse(path):
    d=open(path,"rb").read()
    if d[:4]!=b"CDMR":
        raise ValueError(f"bad magic {d[:4]}")
    total=struct.unpack_from("<I",d,8)[0]
    off=struct.unpack_from("<I",d,12)[0]
    sx=struct.unpack_from("<f",d,16)[0]
    sy=struct.unpack_from("<f",d,20)[0]
    baseline=struct.unpack_from("<I",d,24)[0]
    nx,ny=struct.unpack_from("<II",d,28)
    n=nx*ny
    vals=list(struct.unpack_from(f"<{n}h",d,off))
    return nx,ny,float(sx),float(sy),int(baseline),[float(v) for v in vals]

def median_of_sorted(s):
    m=len(s)
    if m==0:
        return 0.0
    if m%2==1:
        return float(s[m//2])
    else:
        return 0.5*(float(s[m//2-1])+float(s[m//2]))

def solve_one(path):
    nx,ny,sx,sy,baseline_file,vals=parse(path)
    n=nx*ny
    def idx(x,y): return x+nx*y
    sv=sorted(vals)
    bg=median_of_sorted(sv)
    lo=sv[:n//2]
    med_lo=median_of_sorted(lo)
    mad=median_of_sorted(sorted(abs(v-med_lo) for v in lo))
    noise_sigma=max(1e-6,1.4826*mad)
    r=[v-bg for v in vals]
    thr=4.0*noise_sigma
    occ=[v>thr for v in r]
    seen=bytearray(n)
    NEIGH=[(dx,dy) for dy in (-1,0,1) for dx in (-1,0,1) if not (dx==0 and dy==0)]
    best_mass=-1.0
    best_comp=None
    for y0 in range(ny):
        for x0 in range(nx):
            s=idx(x0,y0)
            if not occ[s] or seen[s]:
                continue
            stack=[(x0,y0)]
            seen[s]=1
            comp=[]
            mass=0.0
            while stack:
                x,y=stack.pop()
                cur=idx(x,y)
                comp.append(cur)
                mass+=r[cur]
                for dx,dy in NEIGH:
                    a=x+dx
                    b=y+dy
                    if 0<=a<nx and 0<=b<ny:
                        k=idx(a,b)
                        if occ[k] and not seen[k]:
                            seen[k]=1
                            stack.append((a,b))
            if mass>best_mass:
                best_mass=mass
                best_comp=comp
    if not best_comp:
        print(0)
        return
    filt=[]
    for j in best_comp:
        x=j%nx
        y=j//nx
        acc=0.0
        cnt=0
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                a=min(max(x+dx,0),nx-1)
                b=min(max(y+dy,0),ny-1)
                acc+=r[idx(a,b)]
                cnt+=1
        filt.append(acc/cnt)
    filt.sort(reverse=True)
    top=filt[:max(1,min(8,len(filt)))]
    amp=median_of_sorted(sorted(top))
    if amp<=0:
        print(0)
        return
    region=set(best_comp)
    frontier=set(best_comp)
    for _ in range(50):
        shell=set()
        for j in frontier:
            x=j%nx
            y=j//nx
            for dx,dy in NEIGH:
                a=x+dx
                b=y+dy
                if 0<=a<nx and 0<=b<ny:
                    k=idx(a,b)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        mean_shell=sum(r[j] for j in shell)/len(shell) if shell else 0.0
        if mean_shell<=1.0*noise_sigma:
            break
        region|=shell
        frontier=shell
    mass=sum(r[j] for j in region)
    count=mass/amp
    print(int(round(count)))

if __name__=="__main__":
    if len(sys.argv)<2:
        print(0)
    else:
        solve_one(sys.argv[1])
