#!/usr/bin/env python3
import struct
import sys

MAGIC = b"INKW"
RHO = 0.85

NEIGH8 = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]


def parse_inkw(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != MAGIC:
        raise ValueError("not INKW")
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


def _median(s):
    m = len(s)
    return s[m // 2] if m % 2 else 0.5 * (s[m // 2 - 1] + s[m // 2])


def charge_from_path(path):
    nx, ny, sx, sy, vox = parse_inkw(path)
    n = nx * ny

    def idx(x, y):
        return x + nx * y

    sorted_vox = sorted(vox)
    background = _median(sorted_vox)
    lower = sorted_vox[: n // 2]
    med_low = _median(lower)
    mad = _median(sorted(abs(v - med_low) for v in lower))
    noise_sigma = max(1e-6, 1.4826 * mad)
    residual = [v - background for v in vox]
    occ_thr = 4.0 * noise_sigma
    occupied = [r > occ_thr for r in residual]
    seen = bytearray(n)
    components = []
    for y0 in range(ny):
        for x0 in range(nx):
            s = idx(x0, y0)
            if not occupied[s] or seen[s]:
                continue
            stack = [(x0, y0)]
            seen[s] = 1
            comp = []
            mass = 0.0
            min_x = max_x = x0
            min_y = max_y = y0
            while stack:
                x, y = stack.pop()
                k = idx(x, y)
                comp.append(k)
                mass += residual[k]
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y
                for dx, dy in NEIGH8:
                    a, b = x + dx, y + dy
                    if 0 <= a < nx and 0 <= b < ny:
                        kk = idx(a, b)
                        if occupied[kk] and not seen[kk]:
                            seen[kk] = 1
                            stack.append((a, b))
            dx_ = max_x - min_x + 1
            dy_ = max_y - min_y + 1
            components.append((mass, comp, dx_, dy_))
    if not components:
        return 0.0
    # keep elongated patch along draw direction (x)
    # elongated if longest>=10 and >1.6*shortest
    c_sorted = sorted(components, key=lambda x: x[0], reverse=True)
    best = None
    for mass, comp, dx_, dy_ in c_sorted:
        dims = sorted([dx_, dy_])
        if dims[1] >= 10 and dims[1] > 1.6 * dims[0]:
            best = (mass, comp, dx_, dy_)
            break
    if best is None:
        best = c_sorted[0]
    mass_best, comp_best, _, _ = best
    # plateau via 3x3 filtered top 4 mean (more robust for thin patches with heavy blur, avoids undercount)
    filtered = []
    for j in comp_best:
        x = j % nx
        y = j // nx
        acc = 0.0
        cnt = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                a, b = x + dx, y + dy
                if 0 <= a < nx and 0 <= b < ny:
                    acc += residual[idx(a, b)]
                    cnt += 1
        filtered.append(acc / cnt)
    filtered.sort(reverse=True)
    topk = filtered[: max(1, min(4, len(filtered)))]
    plateau = sum(topk) / len(topk) if topk else 0
    if plateau <= 0:
        return 0.0
    region = set(comp_best)
    frontier = set(comp_best)
    halo_floor = 1.0 * noise_sigma
    for _ in range(50):
        shell = set()
        for j in frontier:
            x = j % nx
            y = j // nx
            for dx_, dy_ in NEIGH8:
                a, b = x + dx_, y + dy_
                if 0 <= a < nx and 0 <= b < ny:
                    k = idx(a, b)
                    if k not in region:
                        shell.add(k)
        if not shell:
            break
        mean_shell = sum(residual[j] for j in shell) / len(shell) if shell else 0
        if mean_shell <= halo_floor:
            break
        region |= shell
        frontier = shell
    total = sum(residual[j] for j in region)
    pixel_count = total / plateau
    return pixel_count * sx * sy * RHO


def main():
    if len(sys.argv) < 2:
        print(0)
        return
    print(charge_from_path(sys.argv[1]))


if __name__ == "__main__":
    main()
