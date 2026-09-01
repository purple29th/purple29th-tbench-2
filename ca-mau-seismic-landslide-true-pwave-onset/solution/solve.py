#!/usr/bin/env python3
"""Oracle: recover true p-wave onset from smeared seismic SEIS dump, stdlib only, with embed fix.

Geophone shaper PSF is normalized Gaussian, conserves energy. True onset NOT recoverable by thresholding. Recoverable by charge conservation: true_samples = sum(residual)/plateau; onset_ns = true_samples*dt*gain.

Embed fix: data_offset at 28 can be 48/64/80/96/128, gain at 40 scales final ns, hidden 1.22 at 96.

Steps:
 1. Parse SEIS header and samples, read offset@28 and gain@40
 2. Estimate baseline and noise sigma robustly
 3. Keep largest-mass contiguous component above noise to drop afterpulses
 4. Plateau via moving average peak
 5. Grow to capture halo then integrate
 6. Onset = voxels*dt*gain
"""

import struct
import sys
import math


MAGIC = b"SEIS"


def parse(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != MAGIC:
        raise ValueError("not SEIS")
    # dtype at 8, n at 12, dt at 16, sx@20 sy@24 placeholder, data_offset@28, gain@40
    dtype = struct.unpack_from("<I", data, 8)[0]
    n = struct.unpack_from("<I", data, 12)[0]
    dt = struct.unpack_from("<f", data, 16)[0]
    try:
        off = struct.unpack_from("<I", data, 28)[0]
    except Exception:
        off = 64
    try:
        gain = struct.unpack_from("<f", data, 40)[0]
    except Exception:
        gain = 1.0
    if not (math.isfinite(gain) and 0.2 < gain < 5.0):
        gain = 1.0
    if off < 48 or off > 256:
        off = 64
    if dtype == 2:
        vals = list(struct.unpack_from("<%dh" % n, data, off))
    elif dtype == 16:
        vals = list(struct.unpack_from("<%df" % n, data, off))
    else:
        raise ValueError("dtype")
    return n, dt, gain, [float(v) for v in vals]


def _median(sv):
    m = len(sv)
    return sv[m // 2] if m % 2 else 0.5 * (sv[m // 2 - 1] + sv[m // 2])


def onset_ns(path):
    n, dt, gain, vals = parse(path)

    sv = sorted(vals)
    # robust background from dimmest 30% to avoid contamination by pulse and blur
    k_bg = max(10, n // 3)
    lo = sv[:k_bg]
    bg = _median(lo)
    med_lo = _median(lo)
    mad = _median(sorted(abs(v - med_lo) for v in lo))
    # avoid zero sigma when no noise, but keep small enough to not swallow halo
    sigma = max(0.5, 1.4826 * mad)
    # if still tiny due to zero noise, use modest floor based on bg scale
    if sigma < 1e-6:
        sigma = 0.5

    r = [v - bg for v in vals]
    thr = 4.0 * sigma

    occ = [v > thr for v in r]
    seen = bytearray(n)
    components = []
    for s in range(n):
        if not occ[s] or seen[s]:
            continue
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
        components.append((mass, comp))
    if not components:
        return 0.0
    components.sort(key=lambda x: x[0], reverse=True)
    biggest = components[0][0]
    # keep all with mass >=0.35*biggest to sum distant ruptures (e.g., two far boxes)
    kept_comps = []
    for mass, comp in components:
        if mass >= 0.35 * biggest:
            kept_comps.append(comp)
    if not kept_comps:
        kept_comps = [components[0][1]]
    best_comp = []
    for c in kept_comps:
        best_comp.extend(c)

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
    k = max(1, min(8, len(filt)))
    amp = sum(filt[:k]) / k
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
    return width_samples * dt * gain


def main():
    if len(sys.argv) < 2:
        print(0)
        return
    print(onset_ns(sys.argv[1]))


if __name__ == "__main__":
    main()
