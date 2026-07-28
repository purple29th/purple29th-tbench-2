#!/usr/bin/env python3
"""Oracle for android-display-mura-ink-pool: ink pool area via light conservation.

Display lamination QA uses under-display RGB sensor with diffuser. Pool interior = saturated plateau where ink pooling brightest. Thin bleed fingers + border pixels partially filled -> dim. Light conserved: true pixels = sum(residual over pool+halo)/plateau * pixel pitch area.

Steps:
 1. Parse DMIP little-endian header + x-fastest payload (magic DMIP, version, dtype 2=int16/16=float32, nx ny, sx sy, offset)
 2. Background median + MAD low half -> residual
 3. 8-connected components above noise, keep largest mass -> main pool
 4. Plateau via 3x3 mean-filter peak median top-8
 5. Adaptive dilation capturing halo while shell mean > noise
 6. Integrate residual / plateau * sx*sy
"""
import struct, sys

def parse(path):
    d=open(path,"rb").read()
    if d[:4]!=b"DMIP":
        raise ValueError(f"bad magic {d[:4]}")
    dtype=struct.unpack_from("<I",d,8)[0]
    nx,ny=struct.unpack_from("<II",d,12)
    sx,sy=struct.unpack_from("<ff",d,20)
    off=struct.unpack_from("<I",d,28)[0]
    n=nx*ny
    if dtype==2:
        vals=list(struct.unpack_from(f"<{n}h",d,off))
    elif dtype==16:
        vals=list(struct.unpack_from(f"<{n}f",d,off))
    else:
        raise ValueError(f"bad dtype {dtype}")
    return nx,ny,float(sx),float(sy),[float(v) for v in vals]

def median_of_sorted(s):
    m=len(s)
    if m==0:
        return 0.0
    if m%2==1:
        return s[m//2]
    else:
        return 0.5*(s[m//2-1]+s[m//2])

def solve_one(path):
    nx,ny,sx,sy,vals=parse(path)
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
        print(0.0)
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
        print(0.0)
        return
    region=set(best_comp)
    frontier=set(best_comp)
    for _ in range(40):
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
        mean_shell=sum(r[k] for k in shell)/len(shell) if shell else 0.0
        if mean_shell<=1.0*noise_sigma:
            break
        region|=shell
        frontier=shell
    mass=sum(r[j] for j in region)
    pixels=mass/amp
    area=pixels*sx*sy
    print(area)

if __name__=="__main__":
    if len(sys.argv)<2:
        print(0)
    else:
        solve_one(sys.argv[1])
