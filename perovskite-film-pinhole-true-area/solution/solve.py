#!/usr/bin/env python3
"""Oracle for solar-wafer-microcrack-true-area: true dead area via intensity conservation (2D)."""

import struct, sys


def parse_ppha(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != b"PPHA":
        raise ValueError("not PPHA")
    dtype = struct.unpack_from("<I", data, 8)[0]
    nx, ny = struct.unpack_from("<II", data, 12)
    sx, sy = struct.unpack_from("<ff", data, 20)
    off = struct.unpack_from("<I", data, 28)[0]
    n = nx * ny
    if dtype == 2:
        vals = list(struct.unpack_from("<%dh" % n, data, off))
    elif dtype == 16:
        vals = list(struct.unpack_from("<%df" % n, data, off))
    else:
        raise ValueError(dtype)
    return nx, ny, float(sx), float(sy), [float(v) for v in vals]


def _median(s):
    m = len(s)
    return s[m // 2] if m % 2 else 0.5 * (s[m // 2 - 1] + s[m // 2])


NEIGH8 = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]


def object_area_mm2(path):
    nx, ny, sx, sy, voxels = parse_ppha(path)
    n = nx * ny

    def idx(x, y):
        return x + nx * y

    sorted_vox = sorted(voxels)
    background = _median(sorted_vox)
    lower_half = sorted_vox[: n // 2]
    med_low = _median(lower_half)
    mad = _median(sorted(abs(v - med_low) for v in lower_half))
    noise_sigma = max(1e-6, 1.4826 * mad)

    residual = [v - background for v in voxels]
    occ_thr = 4.0 * noise_sigma
    occupied = [r > occ_thr for r in residual]
    seen = bytearray(n)
    best_mass = -1.0
    best_comp = None
    for y0 in range(ny):
        for x0 in range(nx):
            s = idx(x0, y0)
            if not occupied[s] or seen[s]:
                continue
            stack = [(x0, y0)]
            seen[s] = 1
            comp = []
            mass = 0.0
            while stack:
                x, y = stack.pop()
                k = idx(x, y)
                comp.append(k)
                mass += residual[k]
                for dx, dy in NEIGH8:
                    a = x + dx
                    b = y + dy
                    if 0 <= a < nx and 0 <= b < ny:
                        kk = idx(a, b)
                        if occupied[kk] and not seen[kk]:
                            seen[kk] = 1
                            stack.append((a, b))
            if mass > best_mass:
                best_mass = mass
                best_comp = comp

    if not best_comp:
        return 0.0

    # filtered plateau via 3x3 local mean
    filtered = []
    for j in best_comp:
        x = j % nx
        y = j // nx
        acc = 0.0
        cnt = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                a = x + dx
                b = y + dy
                if 0 <= a < nx and 0 <= b < ny:
                    acc += residual[idx(a, b)]
                    cnt += 1
        filtered.append(acc / cnt)
    filtered.sort(reverse=True)
    topk = filtered[: max(1, min(12, len(filtered)))]
    plateau = sum(topk) / len(topk)
    if plateau <= 0:
        return 0.0

    # grow halo
    region = set(best_comp)
    frontier = set(best_comp)
    halo_floor = 1.0 * noise_sigma
    for _ in range(50):
        shell = set()
        for j in frontier:
            x = j % nx
            y = j // nx
            for dx, dy in NEIGH8:
                a = x + dx
                b = y + dy
                if 0 <= a < nx and 0 <= b < ny:
                    k = idx(a, b)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        if sum(residual[j] for j in shell) / len(shell) <= halo_floor:
            break
        region |= shell
        frontier = shell

    total = sum(residual[j] for j in region)
    pix_count = total / plateau
    return pix_count * sx * sy


def main():
    if len(sys.argv) < 2:
        print(0)
        return
    print(object_area_mm2(sys.argv[1]))


if __name__ == "__main__":
    main()
