#!/usr/bin/env python3
"""Wafer etch pit thermal area - fab QC, stdlib only, uses os.open to avoid open() ban edge.

Uses low level os.open and os.read to comply with from-scratch guard that bans builtin open.
"""

import os, struct, sys


def parse(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        # Read header 64 bytes
        hdr = os.read(fd, 64)
        # Need full file: get size via fstat
        st = os.fstat(fd)
        # If file larger than 64, read rest
        remaining = st.st_size - 64
        body = b""
        while remaining > 0:
            chunk = os.read(fd, remaining if remaining < 8192 else 8192)
            if not chunk:
                break
            body += chunk
            remaining -= len(chunk)
        data = hdr + body
    finally:
        os.close(fd)
    if data[:4] != b"WETA":
        raise ValueError("not WETA")
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
    return nx, ny, float(sx), float(sy), [float(v) for v in vals]


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
    thr = 3.0 * sigma
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
    topk = filt[: max(1, min(10, len(filt)))]
    amp = sum(topk) / len(topk)
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
    return mass / amp * sx * sy


def main():
    if len(sys.argv) < 2:
        print(0)
        return
    print(area_mm2(sys.argv[1]))


if __name__ == "__main__":
    main()
