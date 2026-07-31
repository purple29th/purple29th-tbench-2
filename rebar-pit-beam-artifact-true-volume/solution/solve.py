#!/usr/bin/env python3
"""Oracle for rebar-pit-beam-artifact-true-volume: gradient + shape filter + conservation"""

import struct, sys


def parse_rpbv(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != b"RPBV":
        raise ValueError("not RPBV")
    dtype = struct.unpack_from("<I", data, 8)[0]
    nx, ny, nz = struct.unpack_from("<III", data, 12)
    sx, sy, sz = struct.unpack_from("<fff", data, 24)
    off = struct.unpack_from("<I", data, 36)[0]
    n = nx * ny * nz
    if dtype == 2:
        vals = list(struct.unpack_from("<%dh" % n, data, off))
    else:
        vals = list(struct.unpack_from("<%df" % n, data, off))
    return nx, ny, nz, float(sx), float(sy), float(sz), [float(v) for v in vals]


def _median(s):
    m = len(s)
    return s[m // 2] if m % 2 else 0.5 * (s[m // 2 - 1] + s[m // 2])


NEIGH26 = [
    (dx, dy, dz)
    for dz in (-1, 0, 1)
    for dy in (-1, 0, 1)
    for dx in (-1, 0, 1)
    if dx or dy or dz
]


def object_volume_mm3(path):
    nx, ny, nz, sx, sy, sz, voxels = parse_rpbv(path)
    n = nx * ny * nz

    def idx(x, y, z):
        return x + nx * (y + ny * z)

    sorted_vox = sorted(voxels)
    bg = _median(sorted_vox)
    lower = sorted_vox[: n // 2]
    med_low = _median(lower)
    mad = _median(sorted(abs(v - med_low) for v in lower))
    sigma = max(1e-6, 1.4826 * mad)

    residual = [v - bg for v in voxels]
    occ_thr = 4.0 * sigma
    occupied = [r > occ_thr for r in residual]
    seen = bytearray(n)
    comps = []
    for z0 in range(nz):
        for y0 in range(ny):
            for x0 in range(nx):
                s = idx(x0, y0, z0)
                if not occupied[s] or seen[s]:
                    continue
                stack = [(x0, y0, z0)]
                seen[s] = 1
                comp = []
                mass = 0.0
                minx = maxx = x0
                miny = maxy = y0
                minz = maxz = z0
                while stack:
                    x, y, z = stack.pop()
                    k = idx(x, y, z)
                    comp.append(k)
                    mass += residual[k]
                    if x < minx:
                        minx = x
                    if x > maxx:
                        maxx = x
                    if y < miny:
                        miny = y
                    if y > maxy:
                        maxy = y
                    if z < minz:
                        minz = z
                    if z > maxz:
                        maxz = z
                    for dx, dy, dz in NEIGH26:
                        a = x + dx
                        b = y + dy
                        c = z + dz
                        if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                            kk = idx(a, b, c)
                            if occupied[kk] and not seen[kk]:
                                seen[kk] = 1
                                stack.append((a, b, c))
                dxb = maxx - minx + 1
                dyb = maxy - miny + 1
                dzb = maxz - minz + 1
                min_ext = min(dxb, dyb, dzb)
                max_ext = max(dxb, dyb, dzb)
                aspect = max_ext / min_ext if min_ext > 0 else 99.0
                comps.append((mass, comp, aspect))

    if not comps:
        return 0.0

    # shape filter: elongated pits vs round bubbles
    elongated = [c for c in comps if c[2] >= 2.2]
    candidates = elongated if elongated else comps
    best_mass, best_comp, aspect = max(candidates, key=lambda x: x[0])

    # plateau via 3x3x3 mean top-8
    filtered = []
    for j in best_comp:
        x = j % nx
        y = (j // nx) % ny
        z = j // (nx * ny)
        acc = 0.0
        cnt = 0
        for dz in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    a = x + dx
                    b = y + dy
                    c = z + dz
                    if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                        acc += residual[idx(a, b, c)]
                        cnt += 1
        filtered.append(acc / cnt)
    filtered.sort(reverse=True)
    topk = filtered[: max(1, min(8, len(filtered)))]
    plateau = sum(topk) / len(topk)
    if plateau <= 0:
        return 0.0

    # halo growth, avoid other comps (round specks)
    occupied_set = set()
    for _, comp_inner, _ in comps:
        for k in comp_inner:
            occupied_set.add(k)
    best_set = set(best_comp)

    region = set(best_comp)
    frontier = set(best_comp)
    halo_floor = 1.0 * sigma
    for _ in range(40):
        shell = set()
        for j in frontier:
            x = j % nx
            y = (j // nx) % ny
            z = j // (nx * ny)
            for dx, dy, dz in NEIGH26:
                a = x + dx
                b = y + dy
                c = z + dz
                if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                    k = idx(a, b, c)
                    if k not in region and k not in occupied_set:
                        shell.add(k)
        if not shell:
            break
        mean_shell = sum(residual[k] for k in shell) / len(shell)
        if mean_shell <= halo_floor:
            break
        region |= shell
        frontier = shell

    total = sum(residual[k] for k in region)
    vc = total / plateau
    return vc * sx * sy * sz


def main():
    if len(sys.argv) < 2:
        print(0)
        return
    print(object_volume_mm3(sys.argv[1]))


if __name__ == "__main__":
    main()
