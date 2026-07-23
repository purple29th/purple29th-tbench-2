#!/usr/bin/env python3
"""Oracle: recover true inked area from capillary ink blot .inkb scan, stdlib only.

Ink on porous paper wicks via capillary diffusion plus lens PSF smears darkness.
Threshold fails (core saturated to amp while feathered filaments partial). Blur
conserves total ink: area_pixels = sum(bg-subtracted)/amp; area_mm2 = pixels*sx*sy.

Steps similar to volume tasks but 2D with 8-neighbour connectivity.
"""

import struct
import sys


def parse(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != b"INKB":
        raise ValueError("not INKB")
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
        raise ValueError("dtype")
    return nx, ny, sx, sy, [float(v) for v in vals]


def _median(sv):
    m = len(sv)
    return sv[m // 2] if m % 2 else 0.5 * (sv[m // 2 - 1] + sv[m // 2])


NEIGH = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]


def area_mm2(path):
    nx, ny, sx, sy, vals = parse(path)
    n = nx * ny

    def idx(x, y):
        return x + nx * y

    sv = sorted(vals)
    bg = _median(sv)
    lo = sv[: n // 2]
    med_lo = _median(lo)
    mad = _median(sorted(abs(v - med_lo) for v in lo))
    sigma = max(1e-6, 1.4826 * mad)

    r = [v - bg for v in vals]
    thr = 4.0 * sigma

    occ = [v > thr for v in r]
    seen = bytearray(n)
    best_mass = -1.0
    best_comp = None
    for y0 in range(ny):
        for x0 in range(nx):
            s = idx(x0, y0)
            if not occ[s] or seen[s]:
                continue
            stack = [(x0, y0)]
            seen[s] = 1
            comp = []
            mass = 0.0
            while stack:
                x, y = stack.pop()
                k = idx(x, y)
                comp.append(k)
                mass += r[k]
                for dx, dy in NEIGH:
                    a, b = x + dx, y + dy
                    if 0 <= a < nx and 0 <= b < ny:
                        kk = idx(a, b)
                        if occ[kk] and not seen[kk]:
                            seen[kk] = 1
                            stack.append((a, b))
            if mass > best_mass:
                best_mass = mass
                best_comp = comp
    if not best_comp:
        return 0.0

    filt = []
    for j in best_comp:
        x = j % nx
        y = j // nx
        acc = 0.0
        cnt = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                a, b = x + dx, y + dy
                if 0 <= a < nx and 0 <= b < ny:
                    acc += r[idx(a, b)]
                    cnt += 1
        filt.append(acc / cnt)
    filt.sort(reverse=True)
    amp = sum(filt[: max(1, min(8, len(filt)))]) / max(1, min(8, len(filt)))
    if amp <= 0:
        return 0.0

    region = set(best_comp)
    frontier = set(best_comp)
    floor = 1.0 * sigma
    for _ in range(40):
        shell = set()
        for j in frontier:
            x = j % nx
            y = j // nx
            for dx, dy in NEIGH:
                a, b = x + dx, y + dy
                if 0 <= a < nx and 0 <= b < ny:
                    k = idx(a, b)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        if sum(r[j] for j in shell) / len(shell) <= floor:
            break
        region |= shell
        frontier = shell

    mass = sum(r[j] for j in region)
    pixels = mass / amp
    return pixels * sx * sy


def main():
    if len(sys.argv) < 2:
        print(0)
        return
    print(area_mm2(sys.argv[1]))


if __name__ == "__main__":
    main()
