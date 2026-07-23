#!/usr/bin/env python3
"""Oracle: recover parcel physical volume from an Android ToF LiDAR .tvol cube,
stdlib only.

Phone rear ToF sensor uses VCSEL IR emitter; lens PSF is wide laterally, narrow
axially due to timing jitter, plus multipath flying pixels. This creates a
saturated core (parcel interior) plus thin flaps / straps with partial-volume
intensity below any usable threshold, so threshold-and-count fails (20-130% off).
VCSEL blur is normalized and CONSERVES total IR energy, therefore:

    parcel_voxels = sum(occupancy - ambient_IR over parcel+halo) / plateau_amp
    volume_mm3    = parcel_voxels * sx * sy * sz

Steps:
  1. Parse TVOL header + voxel payload x-fastest from ARCore Depth dump.
  2. Estimate ambient IR floor as median (background dominates volume) and noise
     via MAD on low half, form residual.
  3. Label 26-connected components above noise floor and keep largest integrated
     mass -> main parcel (drops far flying-pixel specks).
  4. Estimate saturated core plateau via 3x3x3 mean-filter peak over component.
  5. Adaptively dilate to capture faint halo while shell mean remains above noise,
     then integrate signed residual over grown region.
  6. Voxels / amplitude * anisotropic pitch -> mm^3.
"""

import struct
import sys


def parse(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != b"TVOL":
        raise ValueError("not a TVOL file")
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
