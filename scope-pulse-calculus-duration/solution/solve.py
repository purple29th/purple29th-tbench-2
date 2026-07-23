#!/usr/bin/env python3
"""Oracle: recover true pulse duration from smeared photodiode .plse dump, stdlib only.

Shaper PSF is normalized Gaussian, conserves total charge. True duration NOT recoverable by thresholding (thin extensions partial). IS recoverable by charge conservation: true_samples = sum(residual)/plateau; duration_ns = true_samples*dt.

Steps:
 1. Parse binary header and samples
 2. Estimate baseline floor and noise sigma robustly
 3. Keep largest-mass contiguous component above noise to drop afterpulses
 4. Estimate plateau amplitude via moving-average peak
 5. Grow to capture smeared halo then integrate
 6. Duration = voxels*dt
"""

import struct
import sys


def parse(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != b"PLSE":
        raise ValueError("not PLSE")
    dtype = struct.unpack_from("<I", data, 8)[0]
    n = struct.unpack_from("<I", data, 12)[0]
    dt = struct.unpack_from("<f", data, 16)[0]
    off = struct.unpack_from("<I", data, 20)[0]
    if dtype == 2:
        vals = list(struct.unpack_from("<%dh" % n, data, off))
    elif dtype == 16:
        vals = list(struct.unpack_from("<%df" % n, data, off))
    else:
        raise ValueError("dtype")
    return n, dt, [float(v) for v in vals]


def _median(sv):
    m = len(sv)
    return sv[m // 2] if m % 2 else 0.5 * (sv[m // 2 - 1] + sv[m // 2])


def duration_ns(path):
    n, dt, vals = parse(path)

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
    for s in range(n):
        if not occ[s] or seen[s]:
            continue
        # BFS contiguous in 1D
        stack = [s]
        seen[s] = 1
        comp = []
        mass = 0.0
        while stack:
            cur = stack.pop()
            comp.append(cur)
            mass += r[cur]
            for nb in (cur - 1, cur + 1):
                if 0 <= nb < n and occ[nb] and not seen[nb]:
                    seen[nb] = 1
                    stack.append(nb)
        if mass > best_mass:
            best_mass = mass
            best_comp = comp
    if not best_comp:
        return 0.0

    # plateau via 3-point moving average peak
    filt = []
    for j in best_comp:
        acc = 0.0
        cnt = 0
        for d in (-1, 0, 1):
            a = j + d
            if 0 <= a < n:
                acc += r[a]
                cnt += 1
        filt.append(acc / cnt)
    filt.sort(reverse=True)
    amp = sum(filt[: max(1, min(8, len(filt)))]) / max(1, min(8, len(filt)))
    if amp <= 0:
        return 0.0

    region = set(best_comp)
    frontier = set(best_comp)
    floor = 1.0 * sigma
    for _ in range(60):
        shell = set()
        for j in frontier:
            for nb in (j - 1, j + 1):
                if 0 <= nb < n and nb not in region:
                    shell.add(nb)
        if not shell:
            break
        if sum(r[j] for j in shell) / len(shell) <= floor:
            break
        region |= shell
        frontier = shell

    mass = sum(r[j] for j in region)
    width_samples = mass / amp
    return width_samples * dt


def main():
    if len(sys.argv) < 2:
        print(0)
        return
    print(duration_ns(sys.argv[1]))


if __name__ == "__main__":
    main()
