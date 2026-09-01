#!/usr/bin/env python3
import struct as st
import sys as _sys
import math as _mh

_HDR_MAGIC = b"SAPF"
_INV_REPEAT = 5.555555555555555  # 1 / factor for mm/s


def _read_hdr(p):
    buf = open(p, "rb").read()
    if buf[0:4] != _HDR_MAGIC:
        raise RuntimeError("magic mismatch")
    # little endian header
    dtype_id = st.unpack_from("<I", buf, 8)[0]
    w = st.unpack_from("<I", buf, 12)[0]
    h = st.unpack_from("<I", buf, 16)[0]
    px = st.unpack_from("<f", buf, 20)[0]
    py = st.unpack_from("<f", buf, 24)[0]
    data_off = st.unpack_from("<I", buf, 28)[0]
    try:
        mult = st.unpack_from("<f", buf, 40)[0]
    except Exception:
        mult = 1.0
    # sanity: mult absurd -> fallback 1
    if not (_mh.isfinite(mult) and 0.2 < mult < 5.0):
        mult = 1.0
    cnt = w * h
    if dtype_id == 2:
        fmt = "<%dh" % cnt
        vals = st.unpack_from(fmt, buf, data_off)
    else:
        fmt = "<%df" % cnt
        vals = st.unpack_from(fmt, buf, data_off)
    # convert to float list
    return w, h, float(px), float(py), float(mult), [float(v) for v in vals]


def _robust_med(arr):
    # arr is list, returns median
    a = sorted(arr)
    L = len(a)
    if L == 0:
        return 0.0
    mid = L // 2
    if L % 2:
        return float(a[mid])
    return 0.5 * (a[mid - 1] + a[mid])


def _solve_one(path):
    W, H, sx, sy, gain, flat = _read_hdr(path)
    N = W * H

    # linear index helper
    def _lin(x, y):
        return x + W * y

    ordered = sorted(flat)
    # base from dimmest 70% to avoid bias from bright cords
    k70 = int(N * 0.70)
    base = _robust_med(ordered[:k70] if k70 else ordered)

    lower_half = ordered[: N // 2]
    med_low = _robust_med(lower_half)
    devs = sorted(abs(v - med_low) for v in lower_half)
    mad = _robust_med(devs)
    sigma = max(1e-9, 1.4826 * mad)

    resid = [v - base for v in flat]
    # candidate mask
    thr = 4.0 * sigma
    active = [1 if r > thr else 0 for r in resid]

    visited = [0] * N
    blobs = []  # list of (integrated, indices, wbox, hbox, elongated)

    # 8-neighbour offsets
    neigh = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]

    for yy in range(H):
        for xx in range(W):
            p0 = _lin(xx, yy)
            if active[p0] == 0 or visited[p0]:
                continue
            # flood
            stack = [(xx, yy)]
            visited[p0] = 1
            idxs = []
            tot = 0.0
            xmin = xmax = xx
            ymin = ymax = yy
            while stack:
                x, y = stack.pop()
                q = _lin(x, y)
                idxs.append(q)
                tot += resid[q]
                if x < xmin:
                    xmin = x
                if x > xmax:
                    xmax = x
                if y < ymin:
                    ymin = y
                if y > ymax:
                    ymax = y
                for dx, dy in neigh:
                    nx = x + dx
                    ny = y + dy
                    if 0 <= nx < W and 0 <= ny < H:
                        nid = _lin(nx, ny)
                        if active[nid] and not visited[nid]:
                            visited[nid] = 1
                            stack.append((nx, ny))
            bw = xmax - xmin + 1
            bh = ymax - ymin + 1
            small, large = (bw, bh) if bw <= bh else (bh, bw)
            elong = (large >= 10) and (large > 1.6 * small) and (large <= 35)
            blobs.append((tot, idxs, bw, bh, elong))

    if not blobs:
        print(0)
        return

    # sort by integrated brightness descending
    blobs.sort(key=lambda b: b[0], reverse=True)
    top_energy = blobs[0][0]

    keep_groups = []
    for e, ids, _, _, is_el in blobs:
        if is_el and e >= 0.35 * top_energy:
            keep_groups.append(ids)

    if not keep_groups:
        keep_groups = [blobs[0][1]]

    # union of kept
    kept_set = set()
    for g in keep_groups:
        kept_set.update(g)

    # everything else is dust / bacterial
    dust_set = set()
    for _, ids, _, _, _ in blobs:
        for ii in ids:
            if ii not in kept_set:
                dust_set.add(ii)

    # plateau estimate: mean of 4 brightest resid inside kept
    bright_vals = sorted((resid[i] for i in kept_set), reverse=True)
    k = max(1, min(4, len(bright_vals)))
    plateau = sum(bright_vals[:k]) / k if k else 0.0
    if plateau <= 0:
        print(0)
        return

    region = set(kept_set)
    frontier = set(kept_set)
    floor_val = 1.0 * sigma

    for _ in range(60):
        # one ring outward
        ring = set()
        for pid in frontier:
            x = pid % W
            y = pid // W
            for dx, dy in neigh:
                nx = x + dx
                ny = y + dy
                if 0 <= nx < W and 0 <= ny < H:
                    nid = _lin(nx, ny)
                    if nid not in region and nid not in dust_set:
                        ring.add(nid)
        if not ring:
            break
        # average residual in ring
        avg_ring = sum(resid[i] for i in ring) / len(ring) if ring else 0.0
        if avg_ring <= floor_val:
            break
        region.update(ring)
        frontier = ring

    total_energy = sum(resid[i] for i in region)
    true_pixels = total_energy / plateau if plateau else 0.0
    area_mm2 = true_pixels * sx * sy
    length_mm = area_mm2 * _INV_REPEAT * gain
    # final token
    print(length_mm)


if __name__ == "__main__":
    arg = _sys.argv[1] if len(_sys.argv) > 1 else "/app/data/scene.mycr"
    _solve_one(arg)
