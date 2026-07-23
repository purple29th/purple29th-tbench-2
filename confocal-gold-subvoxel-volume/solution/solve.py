#!/usr/bin/env python3
"""Oracle: recover the physical volume of a gold nanocluster-labeled tumor
from a confocal fluorescence .gvol volume, standard library only.

Gold labeling makes the tumor bright with a concentrated core but the microscope
Airy disk point spread smears light everywhere, so threshold and count fails
(the solid core is saturated while thin infiltrating strands have partial-volume
intensity below any usable threshold). The blur is normalized and conserves total
fluorescence, therefore:

    object_voxels = sum(intensity - background over object+halo) / plateau_amplitude
    volume_mm3    = object_voxels * sx * sy * sz

Steps:
  1. Parse binary header and voxel array x-fastest.
  2. Estimate background floor and noise scale robustly and form residual.
  3. Label bright connected components and keep largest-mass component to drop
     far gold dust specks.
  4. Estimate interior plateau amplitude from filtered peak over object.
  5. Grow region to capture faint halo while shell still carries signal, then
     integrate residual over grown region.
  6. Divide by amplitude and multiply by per-axis voxel size.
"""

import struct
import sys


def parse(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != b"GVOL":
        raise ValueError("not a GVOL file")
    dtype = struct.unpack_from("<I", data, 8)[0]
    nx, ny, nz = struct.unpack_from("<III", data, 12)
    sx, sy, sz = struct.unpack_from("<fff", data, 24)
    off = struct.unpack_from("<I", data, 36)[0]
    n = nx * ny * nz
    if dtype == 2:
        vals = list(struct.unpack_from("<%dh" % n, data, off))
    elif dtype == 16:
        vals = list(struct.unpack_from("<%df" % n, data, off))
    else:
        raise ValueError("unsupported dtype %d" % dtype)
    return nx, ny, nz, sx, sy, sz, [float(v) for v in vals]


def _median(sorted_vals):
    m = len(sorted_vals)
    return (
        sorted_vals[m // 2]
        if m % 2
        else 0.5 * (sorted_vals[m // 2 - 1] + sorted_vals[m // 2])
    )


NEIGH = [
    (dx, dy, dz)
    for dz in (-1, 0, 1)
    for dy in (-1, 0, 1)
    for dx in (-1, 0, 1)
    if not (dx == 0 and dy == 0 and dz == 0)
]


def object_volume_mm3(path):
    nx, ny, nz, sx, sy, sz, vals = parse(path)
    n = nx * ny * nz

    def idx(x, y, z):
        return x + nx * (y + ny * z)

    # 1) background floor + noise scale (robust)
    sv = sorted(vals)
    bg = _median(sv)
    lo = sv[: n // 2]
    med_lo = _median(lo)
    mad = _median(sorted(abs(v - med_lo) for v in lo))
    noise_sigma = max(1e-6, 1.4826 * mad)

    r = [v - bg for v in vals]
    thr = 4.0 * noise_sigma

    # 2) largest-mass 26-connected component above the noise floor -> the object
    occ = [v > thr for v in r]
    seen = bytearray(n)
    best_mass = -1.0
    best_comp = None
    for z0 in range(nz):
        for y0 in range(ny):
            for x0 in range(nx):
                s = idx(x0, y0, z0)
                if not occ[s] or seen[s]:
                    continue
                stack = [(x0, y0, z0)]
                seen[s] = 1
                comp = []
                mass = 0.0
                while stack:
                    x, y, z = stack.pop()
                    comp.append(idx(x, y, z))
                    mass += r[idx(x, y, z)]
                    for dx, dy, dz in NEIGH:
                        a, b, c = x + dx, y + dy, z + dz
                        if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                            k = idx(a, b, c)
                            if occ[k] and not seen[k]:
                                seen[k] = 1
                                stack.append((a, b, c))
                if mass > best_mass:
                    best_mass = mass
                    best_comp = comp
    if not best_comp:
        return 0.0

    # 3) plateau amplitude: 3x3x3 mean-filter peak over the object component
    filt = []
    for j in best_comp:
        x = j % nx
        y = (j // nx) % ny
        z = j // (nx * ny)
        acc = 0.0
        cnt = 0
        for dz in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    a, b, c = x + dx, y + dy, z + dz
                    if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                        acc += r[idx(a, b, c)]
                        cnt += 1
        filt.append(acc / cnt)
    filt.sort(reverse=True)
    topk = filt[: max(1, min(8, len(filt)))]
    amp = sum(topk) / len(topk)
    if amp <= 0:
        return 0.0

    # 4) adaptively grow to capture the faint blur halo, then integrate the
    #    signed residual (noise cancels) over the bounded region
    region = set(best_comp)
    frontier = set(best_comp)
    floor = 1.0 * noise_sigma
    for _ in range(40):
        shell = set()
        for j in frontier:
            x = j % nx
            y = (j // nx) % ny
            z = j // (nx * ny)
            for dx, dy, dz in NEIGH:
                a, b, c = x + dx, y + dy, z + dz
                if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                    k = idx(a, b, c)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        if sum(r[j] for j in shell) / len(shell) <= floor:
            break
        region |= shell
        frontier = shell

    mass = sum(r[j] for j in region)
    voxels = mass / amp
    return voxels * sx * sy * sz


def main():
    if len(sys.argv) < 2:
        print(0)
        return
    print(object_volume_mm3(sys.argv[1]))


if __name__ == "__main__":
    main()
