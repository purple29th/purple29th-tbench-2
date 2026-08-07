#!/usr/bin/env python3
"""Oracle: true pit area via energy conservation with tilt-robust background plane.

Method:
 - Parse ENPP
 - Fit background plane from lower half histogram to handle tilt
 - MAD noise from lower-half residuals
 - Largest-mass 8-connected component (mass = sum residual)
 - Plateau via 3x3 filtered top-K
 - Halo growth to noise floor
 - area = energy/plateau * sx*sy
"""

import struct
import sys
import math


def parse_enpp(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != b"ENPP":
        raise ValueError("not ENPP")
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


def _median(sorted_vals):
    m = len(sorted_vals)
    if m == 0:
        return 0.0
    if m % 2:
        return float(sorted_vals[m // 2])
    return 0.5 * (sorted_vals[m // 2 - 1] + sorted_vals[m // 2])


def _solve_3x3(M, B):
    """Solve M*x=B for 3x3 via Gaussian elimination with partial pivot. Returns [a,b,c] or None if singular."""
    # copy
    A = [row[:] for row in M]
    b = B[:]
    n = 3
    for col in range(n):
        # pivot
        pivot_row = col
        max_abs = abs(A[col][col])
        for r in range(col + 1, n):
            if abs(A[r][col]) > max_abs:
                max_abs = abs(A[r][col])
                pivot_row = r
        if max_abs < 1e-12:
            return None
        if pivot_row != col:
            A[col], A[pivot_row] = A[pivot_row], A[col]
            b[col], b[pivot_row] = b[pivot_row], b[col]
        # normalize pivot row
        piv = A[col][col]
        for c in range(col, n):
            A[col][c] /= piv
        b[col] /= piv
        # eliminate other rows
        for r in range(n):
            if r == col:
                continue
            factor = A[r][col]
            if factor == 0:
                continue
            for c in range(col, n):
                A[r][c] -= factor * A[col][c]
            b[r] -= factor * b[col]
    return b


NEIGH8 = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]


def pit_area_mm2(path):
    nx, ny, sx, sy, pixels = parse_enpp(path)
    n = nx * ny

    def idx(x, y):
        return x + nx * y

    # Collect (value, x, y, linear_idx) for sorting
    entries = []
    for y in range(ny):
        base = y * nx
        for x in range(nx):
            i = base + x
            entries.append((pixels[i], x, y, i))
    entries_sorted = sorted(entries, key=lambda e: e[0])
    lower = entries_sorted[: n // 2]

    # Fit background plane to lower half to handle tilt
    # Plane: z = a*x + b*y + c
    Sx = Sy = Sxx = Syy = Sxy = Sv = Sxv = Syv = 0.0
    nn = float(len(lower))
    for v, x, y, _ in lower:
        Sx += x
        Sy += y
        Sv += v
        Sxx += x * x
        Syy += y * y
        Sxy += x * y
        Sxv += x * v
        Syv += y * v

    M = [
        [Sxx, Sxy, Sx],
        [Sxy, Syy, Sy],
        [Sx, Sy, nn],
    ]
    B = [Sxv, Syv, Sv]
    sol = _solve_3x3(M, B)
    if sol is None:
        # fallback to constant median background
        sorted_vals = sorted(pixels)
        bg = _median(sorted_vals[: n // 2])
        a = b_ = 0.0
        c = bg
    else:
        a, b_, c = sol[0], sol[1], sol[2]

    # residual after plane subtraction
    residual = [0.0] * n
    for y in range(ny):
        for x in range(nx):
            i = idx(x, y)
            bg_plane = a * x + b_ * y + c
            residual[i] = pixels[i] - bg_plane

    # noise from lower half residuals
    lower_res = []
    for v, x, y, _ in lower:
        bg_plane = a * x + b_ * y + c
        lower_res.append(v - bg_plane)
    lower_res_sorted = sorted(lower_res)
    med_low = _median(lower_res_sorted)
    # MAD
    abs_dev = sorted(abs(r - med_low) for r in lower_res)
    mad = _median(abs_dev)
    noise_sigma = max(1e-6, 1.4826 * mad)

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
                    aa, bb = x + dx, y + dy
                    if 0 <= aa < nx and 0 <= bb < ny:
                        kk = idx(aa, bb)
                        if occupied[kk] and not seen[kk]:
                            seen[kk] = 1
                            stack.append((aa, bb))
            if mass > best_mass:
                best_mass = mass
                best_comp = comp

    if not best_comp:
        return 0.0

    filtered = []
    for j in best_comp:
        x = j % nx
        y = j // nx
        acc = 0.0
        cnt = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                aa, bb = x + dx, y + dy
                if 0 <= aa < nx and 0 <= bb < ny:
                    acc += residual[idx(aa, bb)]
                    cnt += 1
        filtered.append(acc / cnt if cnt else residual[j])
    filtered.sort(reverse=True)
    topk = filtered[: max(1, min(8, len(filtered)))]
    plateau = sum(topk) / len(topk)
    if plateau <= 0:
        return 0.0

    region = set(best_comp)
    frontier = set(best_comp)
    halo_floor = 1.0 * noise_sigma
    for _ in range(25):
        shell = set()
        for j in frontier:
            x = j % nx
            y = j // nx
            for dx, dy in NEIGH8:
                aa, bb = x + dx, y + dy
                if 0 <= aa < nx and 0 <= bb < ny:
                    k = idx(aa, bb)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        avg_shell = sum(residual[j] for j in shell) / len(shell) if shell else 0.0
        if avg_shell <= halo_floor:
            break
        region |= shell
        frontier = shell

    total_energy = sum(residual[j] for j in region)
    pixel_count = total_energy / plateau
    return pixel_count * sx * sy


def main():
    if len(sys.argv) < 2:
        print(0)
        return
    print(pit_area_mm2(sys.argv[1]))


if __name__ == "__main__":
    main()
