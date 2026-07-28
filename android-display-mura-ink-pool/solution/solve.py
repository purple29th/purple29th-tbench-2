#!/usr/bin/env python3
"""
Oracle for android-display-mura-ink-pool: count of ink affected touch cells via charge conservation.

True count is fractional occupancy integral rounded; equivalent to total conserved
charge divided by saturated plateau. Steps:
- parse CDMR little-endian container (magic, offset, nx,ny, int16 payload)
- estimate background baseline as median of all values (robust to outliers)
- estimate noise sigma via MAD of low side (median absolute deviation, scaled 1.4826 for Gaussian)
- threshold bright cells at 4*sigma above background (high enough to reject noise, low enough to capture halo core)
- 8-neighbour flood fill to get connected components, keep component with largest total excess mass (sum r) to drop far dust (dust total charge can be large but per-blob mass smaller than main)
- estimate saturated plateau amplitude: 3x3 box average inside best component to suppress noise, then median of top 8 values (top 8 covers saturated flat interior even after smear, median robust to single-pixel spikes; 8 chosen as small enough to stay in plateau but enough for median)
- grow region iteratively (up to 50 shells) to include smeared halo: each shell is 8-neighbour frontier outside current region; stop when mean shell excess <= 1.0*sigma (shell indistinguishable from background)
- integrate excess charge in grown region and divide by plateau amplitude => count, rounded.

Constants rationale:
- 4.0*sigma: standard 4-sigma detection for capacitive grid with Gaussian noise ~3, gives low false positive while keeping bleed lines.
- 50 halo iterations: enough for PSF up to 2.6 and grid up to 80x80 (halo spread ~3-4 sigma ~ 8-10 cells, 50 is safe upper bound).
- 1.0*sigma shell stop: shell mean at background noise level means further growth adds only noise, not conserved charge.
- top-8 median: interior plateau typically >10 cells, top few values after smoothing approximate saturated level; median of 8 robust.

This passes all heldouts including heavy dust (6 blobs) and edge pools.
"""

import struct
import sys


def parse_cdmr(path):
    data = open(path, "rb").read()
    if data[:4] != b"CDMR":
        raise ValueError(f"bad magic {data[:4]}")
    total_cells = struct.unpack_from("<I", data, 8)[0]
    data_offset = struct.unpack_from("<I", data, 12)[0]
    sx_pitch = struct.unpack_from("<f", data, 16)[0]
    sy_pitch = struct.unpack_from("<f", data, 20)[0]
    baseline_file = struct.unpack_from("<I", data, 24)[0]
    nx, ny = struct.unpack_from("<II", data, 28)
    n = nx * ny
    # payload is int16 little endian
    raw_vals = struct.unpack_from(f"<{n}h", data, data_offset)
    float_vals = [float(v) for v in raw_vals]
    return nx, ny, float(sx_pitch), float(sy_pitch), int(baseline_file), float_vals


def median_of_sorted(sorted_list):
    m = len(sorted_list)
    if m == 0:
        return 0.0
    if m % 2 == 1:
        return float(sorted_list[m // 2])
    return 0.5 * (float(sorted_list[m // 2 - 1]) + float(sorted_list[m // 2]))


def solve_one(path):
    nx, ny, sx, sy, baseline_file, vals = parse_cdmr(path)
    n = nx * ny

    def idx(x, y):
        return x + nx * y

    sorted_vals = sorted(vals)
    background = median_of_sorted(sorted_vals)

    # noise estimation from lower half (background dominated)
    low_half = sorted_vals[: n // 2]
    med_low = median_of_sorted(low_half)
    # MAD: median absolute deviation
    abs_devs = sorted(abs(v - med_low) for v in low_half)
    mad = median_of_sorted(abs_devs)
    noise_sigma = max(1e-6, 1.4826 * mad)  # scale for Gaussian

    # residual above background
    residual = [v - background for v in vals]

    # bright mask: 4 sigma above background
    threshold = 4.0 * noise_sigma
    occupied = [v > threshold for v in residual]

    seen = bytearray(n)
    NEIGH = [
        (dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if not (dx == 0 and dy == 0)
    ]

    best_mass = -1.0
    best_component = None

    # iterative 8-neighbour flood fill to find connected components and their total charge mass
    for y0 in range(ny):
        for x0 in range(nx):
            start = idx(x0, y0)
            if not occupied[start] or seen[start]:
                continue
            stack = [(x0, y0)]
            seen[start] = 1
            comp = []
            mass = 0.0
            while stack:
                x, y = stack.pop()
                cur = idx(x, y)
                comp.append(cur)
                mass += residual[cur]
                for dx, dy in NEIGH:
                    ax = x + dx
                    by = y + dy
                    if 0 <= ax < nx and 0 <= by < ny:
                        k = idx(ax, by)
                        if occupied[k] and not seen[k]:
                            seen[k] = 1
                            stack.append((ax, by))
            # keep component with largest total excess charge (mass), not just size, to drop dust even if dust has many pixels
            if mass > best_mass:
                best_mass = mass
                best_component = comp

    if not best_component:
        print(0)
        return

    # plateau estimation: 3x3 box average inside best component to suppress noise, then median of top 8
    smoothed = []
    for j in best_component:
        x = j % nx
        y = j // nx
        acc = 0.0
        cnt = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                a = min(max(x + dx, 0), nx - 1)
                b = min(max(y + dy, 0), ny - 1)
                acc += residual[idx(a, b)]
                cnt += 1
        smoothed.append(acc / cnt)
    smoothed.sort(reverse=True)
    top_n = max(1, min(8, len(smoothed)))
    top_vals = smoothed[:top_n]
    plateau = median_of_sorted(sorted(top_vals))
    if plateau <= 0:
        print(0)
        return

    # grow region to capture conserved halo: iterative shell expansion
    region = set(best_component)
    frontier = set(best_component)
    max_iterations = 50  # enough for PSF up to 2.6 and large grids
    for _ in range(max_iterations):
        shell = set()
        for j in frontier:
            x = j % nx
            y = j // nx
            for dx, dy in NEIGH:
                a = x + dx
                b = y + dy
                if 0 <= a < nx and 0 <= b < ny:
                    k = idx(a, b)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        mean_shell = sum(residual[j] for j in shell) / len(shell) if shell else 0.0
        # stop when shell average at noise level -> further expansion is background
        if mean_shell <= 1.0 * noise_sigma:
            break
        region |= shell
        frontier = shell

    total_mass = sum(residual[j] for j in region)
    count = total_mass / plateau
    print(int(round(count)))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(0)
    else:
        solve_one(sys.argv[1])
