#!/usr/bin/env python3
import struct
import sys

MAGIC = b"LRPW"
COEFF = 2.43
NEIGH = [
    (dx, dy, dz)
    for dz in (-1, 0, 1)
    for dy in (-1, 0, 1)
    for dx in (-1, 0, 1)
    if dx or dy or dz
]


def load_lrpw(p):
    d = open(p, "rb").read()
    if d[:4] != MAGIC:
        raise ValueError("bad magic")
    dtype = struct.unpack_from("<I", d, 8)[0]
    nx, ny, nz = struct.unpack_from("<III", d, 12)
    sx, sy, sz = struct.unpack_from("<fff", d, 24)
    off = struct.unpack_from("<I", d, 36)[0]
    gain = 1.0
    try:
        gain = struct.unpack_from("<f", d, 40)[0]
    except:
        gain = 1.0
    n = nx * ny * nz
    if dtype == 2:
        vals = list(struct.unpack_from("<%dh" % n, d, off))
    else:
        vals = list(struct.unpack_from("<%df" % n, d, off))
    return (
        nx,
        ny,
        nz,
        float(sx),
        float(sy),
        float(sz),
        float(gain),
        [float(v) for v in vals],
    )


def median_calc(a):
    s = sorted(a)
    m = len(s) // 2
    return s[m] if len(s) % 2 == 1 else 0.5 * (s[m - 1] + s[m])


def solve(p):
    nx, ny, nz, sx, sy, sz, gain, vox = load_lrpw(p)
    n = nx * ny * nz

    def lin(x, y, z):
        return x + nx * (y + ny * z)

    order = sorted(vox)
    bg = median_calc(order[: int(n * 0.8)])
    low = order[: n // 2]
    ml = median_calc(low)
    mad = median_calc(sorted(abs(v - ml) for v in low))
    sig = max(1e-6, 1.4826 * mad)
    res = [v - bg for v in vox]
    thr = 8.0 * sig
    occ = [r > thr for r in res]
    seen = [False] * n
    comps = []
    for z0 in range(nz):
        for y0 in range(ny):
            for x0 in range(nx):
                i0 = lin(x0, y0, z0)
                if not occ[i0] or seen[i0]:
                    continue
                stack = [(x0, y0, z0)]
                seen[i0] = True
                comp = []
                mass = 0.0
                min_x = max_x = x0
                min_y = max_y = y0
                min_z = max_z = z0
                while stack:
                    x, y, z = stack.pop()
                    k = lin(x, y, z)
                    comp.append(k)
                    mass += res[k]
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
                    min_z = min(min_z, z)
                    max_z = max(max_z, z)
                    for dx, dy, dz in NEIGH:
                        a, b, c = x + dx, y + dy, z + dz
                        if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                            kk = lin(a, b, c)
                            if occ[kk] and not seen[kk]:
                                seen[kk] = True
                                stack.append((a, b, c))
                comps.append(
                    (
                        mass,
                        comp,
                        max_x - min_x + 1,
                        max_y - min_y + 1,
                        max_z - min_z + 1,
                    )
                )
    if not comps:
        print(0)
        return
    comps_with = []
    for mass, comp, dx, dy, dz in comps:
        dims = sorted([dx, dy, dz])
        is_round = dims[2] <= 35 and dims[2] <= 3.0 * dims[0]
        comps_with.append((mass, comp, dx, dy, dz, is_round))
    comps_with.sort(key=lambda x: x[0], reverse=True)
    largest = comps_with[0][0] if comps_with else 0
    main_groups = []
    for mass, comp, dx, dy, dz, is_round in comps_with:
        if is_round and mass >= 0.22 * largest:
            main_groups.append(comp)
    if not main_groups:
        main_groups = [comps_with[0][1]] if comps_with else []
    best = []
    for g in main_groups:
        best.extend(g)
    kept = set(best)
    dust = set()
    for _, comp, _, _, _, _ in comps_with:
        for ii in comp:
            if ii not in kept:
                dust.add(ii)
    peak = [res[j] for j in best]
    peak.sort(reverse=True)
    top = peak[: max(1, min(4, len(peak)))]
    plat = sum(top) / len(top) if top else 0
    if plat <= 0:
        print(0)
        return
    region = set(best)
    frontier = set(best)
    floor = 1.0 * sig
    for _ in range(40):
        shell = set()
        for j in frontier:
            x = j % nx
            y = (j // nx) % ny
            z = j // (nx * ny)
            for dx, dy, dz in NEIGH:
                a, b, c = x + dx, y + dy, z + dz
                if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                    k = lin(a, b, c)
                    if k not in region and k not in dust:
                        shell.add(k)
        if not shell:
            break
        if sum(res[k] for k in shell) / len(shell) <= floor:
            break
        region |= shell
        frontier = shell
    tot = sum(res[k] for k in region)
    vcount = tot / plat if plat else 0
    vol = vcount * sx * sy * sz
    weight = vol * COEFF * gain
    print(weight)


if __name__ == "__main__":
    solve(sys.argv[1] if len(sys.argv) > 1 else "/app/data/scene.lrpw")
