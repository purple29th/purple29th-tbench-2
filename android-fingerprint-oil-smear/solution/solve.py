#!/usr/bin/env python3
"""Oracle for fingerprint oil smear via integrated light energy recovery.
Reads FPOS binary: header with pitch and baseline and nx ny, payload int16 brightness.
Recovers true oil pixel count by background median, MAD noise sigma, dominant blob
by residual mass using 8-direction flood fill, dust exclusion, peak from smoothed
top values, halo expansion until shell mean below sigma, then mass/amp.
"""

import struct
import sys


def parse_fpos(p):
    blob = open(p, "rb").read()
    if blob[:4] != b"FPOS":
        raise ValueError("bad magic")
    total = struct.unpack_from("<I", blob, 8)[0]
    off = struct.unpack_from("<I", blob, 12)[0]
    sx = struct.unpack_from("<f", blob, 16)[0]
    sy = struct.unpack_from("<f", blob, 20)[0]
    bfloor = struct.unpack_from("<I", blob, 24)[0]
    nx, ny = struct.unpack_from("<II", blob, 28)
    n = nx * ny
    vals = struct.unpack_from(f"<{n}h", blob, off)
    return nx, ny, float(sx), float(sy), int(bfloor), [float(v) for v in vals]


def median_sorted(arr):
    L = len(arr)
    if L == 0:
        return 0.0
    mid = L // 2
    if L % 2 == 1:
        return float(arr[mid])
    return 0.5 * (float(arr[mid - 1]) + float(arr[mid]))


def solve_one(path):
    nx, ny, sx, sy, base_file, raw = parse_fpos(path)
    N = nx * ny

    def lin(x, y):
        return x + nx * y

    sorted_raw = sorted(raw)
    bg0 = median_sorted(sorted_raw)
    lower = sorted_raw[: N // 2]
    med_low = median_sorted(lower)
    mad = median_sorted(sorted(abs(v - med_low) for v in lower))
    sigma = max(1e-6, 1.4826 * mad)
    resid = [v - bg0 for v in raw]
    thresh = 4.0 * sigma

    visited = bytearray(N)
    neigh_offsets = [
        (dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if not (dx == 0 and dy == 0)
    ]

    best_region = None
    best_mass_val = -1.0

    for yy in range(ny):
        for xx in range(nx):
            idx0 = lin(xx, yy)
            if resid[idx0] <= thresh or visited[idx0]:
                continue
            stack = [(xx, yy)]
            visited[idx0] = 1
            cur_comp = []
            cur_mass = 0.0
            while stack:
                cx, cy = stack.pop()
                cidx = lin(cx, cy)
                cur_comp.append(cidx)
                cur_mass += resid[cidx]
                for dx, dy in neigh_offsets:
                    ax = cx + dx
                    by = cy + dy
                    if 0 <= ax < nx and 0 <= by < ny:
                        aidx = lin(ax, by)
                        if resid[aidx] > thresh and not visited[aidx]:
                            visited[aidx] = 1
                            stack.append((ax, by))
            if cur_mass > best_mass_val:
                best_mass_val = cur_mass
                best_region = cur_comp

    if not best_region:
        print(0)
        return

    # estimate peak amplitude from smoothed top values inside best region
    smoothed = []
    for q in best_region:
        qx = q % nx
        qy = q // nx
        acc = 0.0
        cnt = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ax = min(max(qx + dx, 0), nx - 1)
                by = min(max(qy + dy, 0), ny - 1)
                acc += resid[lin(ax, by)]
                cnt += 1
        smoothed.append(acc / cnt if cnt else 0.0)

    smoothed.sort(reverse=True)
    k_top = max(1, min(8, len(smoothed)))
    top_vals = smoothed[:k_top]
    amp = median_sorted(sorted(top_vals))
    if amp <= 0:
        print(0)
        return

    # grow halo outward until shell mean below noise sigma
    region_set = set(best_region)
    frontier = set(best_region)
    for _ in range(60):
        shell = set()
        for q in frontier:
            qx = q % nx
            qy = q // nx
            for dx, dy in neigh_offsets:
                ax = qx + dx
                by = qy + dy
                if 0 <= ax < nx and 0 <= by < ny:
                    aidx = lin(ax, by)
                    if aidx not in region_set:
                        shell.add(aidx)
        if not shell:
            break
        shell_mean = sum(resid[i] for i in shell) / len(shell) if shell else 0.0
        if shell_mean <= 1.0 * sigma:
            break
        region_set.update(shell)
        frontier = shell

    total_mass = sum(resid[i] for i in region_set)
    pixel_count = int(round(total_mass / amp)) if amp else 0
    print(pixel_count)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(0)
    else:
        solve_one(sys.argv[1])
