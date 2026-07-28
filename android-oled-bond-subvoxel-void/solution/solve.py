#!/usr/bin/env python3
"""Oracle for android-oled-bond-subvoxel-void: OLED bond void volume via IR energy conservation.

Pixel OLED bonding QA uses under-display VCSEL diffuser IR scanner. OLED stack diffuses wide in XY, bond thin -> narrow Z. Void interior = saturated plateau where air scattering brightest. Thin delam fingers + border voxels partially filled -> dim. PSF normalized conserves energy: true voxels = sum(residual over void+halo)/plateau * voxel_pitch_volume.

Steps:
  1. Parse OBVL little-endian header + x-fastest payload (magic OBVL, version, dtype 2=int16/16=float32, nx ny nz, sx sy sz, offset)
  2. Estimate DC background as median (background dominates) + noise via MAD on low half -> residual
  3. 26-connected components above noise floor, keep largest mass -> main void (drops dust specks)
  4. Plateau via 3x3x3 mean-filter peak median of top-8 over component
  5. Adaptive dilation capturing faint halo while shell mean > noise
  6. Integrate residual / plateau * sx*sy*sz
"""
import struct
import sys

def parse(path):
    d = open(path, "rb").read()
    if d[:4] != b"OBVL":
        raise ValueError(f"{path}: bad magic {d[:4]}")
    dtype = struct.unpack_from("<I", d, 8)[0]
    nx, ny, nz = struct.unpack_from("<III", d, 12)
    sx, sy, sz = struct.unpack_from("<fff", d, 24)
    off = struct.unpack_from("<I", d, 36)[0]
    n = nx*ny*nz
    if dtype == 2:
        vals = list(struct.unpack_from(f"<{n}h", d, off))
    elif dtype == 16:
        vals = list(struct.unpack_from(f"<{n}f", d, off))
    else:
        raise ValueError(f"unsupported dtype {dtype}")
    return nx, ny, nz, float(sx), float(sy), float(sz), [float(v) for v in vals]

def _median(s):
    m=len(s)
    return s[m//2] if m%2 else 0.5*(s[m//2-1]+s[m//2])

NEIGH=[(dx,dy,dz) for dz in (-1,0,1) for dy in (-1,0,1) for dx in (-1,0,1) if not (dx==0 and dy==0 and dz==0)]

def void_volume_mm3(path):
    nx,ny,nz,sx,sy,sz,vals=parse(path)
    n=nx*ny*nz
    def idx(x,y,z): return x + nx*(y+ ny*z)
    sv=sorted(vals)
    bg=_median(sv)
    lo=sv[:n//2]
    med_lo=_median(lo)
    mad=_median(sorted(abs(v-med_lo) for v in lo))
    noise_sigma=max(1e-6,1.4826*mad)
    r=[v-bg for v in vals]
    thr=4.0*noise_sigma

    occ=[v>thr for v in r]
    seen=bytearray(n)
    best_mass=-1.0
    best_comp=None
    for z0 in range(nz):
        for y0 in range(ny):
            for x0 in range(nx):
                s=idx(x0,y0,z0)
                if not occ[s] or seen[s]: continue
                stack=[(x0,y0,z0)]
                seen[s]=1
                comp=[]
                mass=0.0
                while stack:
                    x,y,z=stack.pop()
                    k=idx(x,y,z)
                    comp.append(k)
                    mass+=r[k]
                    for dx,dy,dz in NEIGH:
                        a,b,c=x+dx,y+dy,z+dz
                        if 0<=a<nx and 0<=b<ny and 0<=c<nz:
                            nb=idx(a,b,c)
                            if occ[nb] and not seen[nb]:
                                seen[nb]=1
                                stack.append((a,b,c))
                if mass>best_mass:
                    best_mass=mass
                    best_comp=comp
    if not best_comp:
        return 0.0

    # plateau amplitude via filtered peak
    filt=[]
    for j in best_comp:
        x=j%nx
        y=(j//nx)%ny
        z=j//(nx*ny)
        acc=0.0
        cnt=0
        for dz in (-1,0,1):
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    a,b,c=x+dx,y+dy,z+dz
                    if 0<=a<nx and 0<=b<ny and 0<=c<nz:
                        acc+=r[idx(a,b,c)]
                        cnt+=1
        filt.append(acc/cnt)
    filt.sort(reverse=True)
    topk=filt[:max(1,min(8,len(filt)))]
    amp=sum(topk)/len(topk)
    if amp<=0:
        return 0.0

    region=set(best_comp)
    frontier=set(best_comp)
    floor=1.0*noise_sigma
    for _ in range(40):
        shell=set()
        for j in frontier:
            x=j%nx
            y=(j//nx)%ny
            z=j//(nx*ny)
            for dx,dy,dz in NEIGH:
                a,b,c=x+dx,y+dy,z+dz
                if 0<=a<nx and 0<=b<ny and 0<=c<nz:
                    k=idx(a,b,c)
                    if k not in region:
                        shell.add(k)
        if not shell: break
        mean_shell=sum(r[k] for k in shell)/len(shell) if shell else 0.0
        if mean_shell<=floor: break
        region|=shell
        frontier=shell

    mass=sum(r[j] for j in region)
    voxels=mass/amp
    return voxels*sx*sy*sz

def main():
    if len(sys.argv)<2:
        print(0)
        return
    print(void_volume_mm3(sys.argv[1]))

if __name__=="__main__":
    main()
