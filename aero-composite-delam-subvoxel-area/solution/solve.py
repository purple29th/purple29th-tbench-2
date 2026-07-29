import struct, sys, math, collections


def parse_udel(path):
    with open(path, "rb") as f:
        data = f.read()
    magic = data[0:4]
    assert magic == b"UDEL"
    dtype = struct.unpack_from("<I", data, 8)[0]
    nx, ny = struct.unpack_from("<II", data, 12)
    sx, sy = struct.unpack_from("<ff", data, 20)
    data_offset = struct.unpack_from("<I", data, 28)[0]
    n = nx * ny
    if dtype == 2:
        fmt = "<%dh" % n
        vals = struct.unpack_from(fmt, data, data_offset)
        field = [float(v) for v in vals]
    else:
        fmt = "<%df" % n
        vals = struct.unpack_from(fmt, data, data_offset)
        field = list(vals)
    return field, nx, ny, sx, sy


def main():
    if len(sys.argv) < 2:
        print("usage: solve.py <path>", file=sys.stderr)
        sys.exit(1)
    path = sys.argv[1]
    field, nx, ny, sx, sy = parse_udel(path)

    def idx(x, y):
        return x + nx * y

    border = []
    for x in range(nx):
        border.append(field[idx(x, 0)])
        border.append(field[idx(x, ny - 1)])
    for y in range(1, ny - 1):
        border.append(field[idx(0, y)])
        border.append(field[idx(nx - 1, y)])
    border_sorted = sorted(border)
    bg_median = border_sorted[len(border_sorted) // 2]
    mean_bg = sum(border) / len(border)
    var_bg = sum((v - mean_bg) * (v - mean_bg) for v in border) / len(border)
    noise = math.sqrt(var_bg) if var_bg > 0 else 1.0
    bg_est = bg_median

    residual = [v - bg_est for v in field]
    max_res = max(residual) if residual else 0
    thresh = max(3 * noise, 0.15 * max_res, 1.0)
    hot_mask = [1 if r > thresh else 0 for r in residual]

    visited = [0] * len(field)
    components = []
    for y in range(ny):
        for x in range(nx):
            i = idx(x, y)
            if hot_mask[i] == 0 or visited[i]:
                continue
            q = collections.deque([i])
            visited[i] = 1
            comp = []
            while q:
                cur = q.popleft()
                comp.append(cur)
                cx = cur % nx
                cy = cur // nx
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx2 = cx + dx
                        ny2 = cy + dy
                        if 0 <= nx2 < nx and 0 <= ny2 < ny:
                            ni = idx(nx2, ny2)
                            if hot_mask[ni] and not visited[ni]:
                                visited[ni] = 1
                                q.append(ni)
            components.append(comp)

    if not components:
        print("0.0")
        return

    def comp_mass(c):
        return sum(residual[i] for i in c)

    components.sort(key=comp_mass, reverse=True)
    main = components[0]

    main_res = [residual[i] for i in main]
    main_res_sorted = sorted(main_res, reverse=True)
    idx95 = int(len(main_res_sorted) * 0.05)
    plateau = main_res_sorted[idx95] if main_res_sorted else max_res
    if plateau <= 0:
        plateau = max_res if max_res > 0 else 1.0

    in_mask = [0] * len(field)
    for i in main:
        in_mask[i] = 1
    current_frontier = set(main)

    for _ in range(15):
        next_frontier = set()
        for cur in current_frontier:
            cx = cur % nx
            cy = cur // nx
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx2 = cx + dx
                    ny2 = cy + dy
                    if 0 <= nx2 < nx and 0 <= ny2 < ny:
                        ni = idx(nx2, ny2)
                        if not in_mask[ni]:
                            next_frontier.add(ni)
        if not next_frontier:
            break
        vals = [residual[i] for i in next_frontier]
        mean_front = sum(vals) / len(vals) if vals else 0
        if mean_front < max(noise * 0.5, plateau * 0.01):
            filtered = [i for i in next_frontier if residual[i] > noise * 0.3]
            for i in filtered:
                in_mask[i] = 1
            break
        to_add = [i for i in next_frontier if residual[i] > noise * 0.1]
        if not to_add:
            break
        for i in to_add:
            in_mask[i] = 1
        current_frontier = set(to_add)
        if len([1 for v in in_mask if v]) > nx * ny * 0.6:
            break

    integrated = sum(
        residual[i] for i in range(len(field)) if in_mask[i] and residual[i] > 0
    )
    voxel_area = integrated / plateau if plateau > 0 else 0
    mm2 = voxel_area * sx * sy
    print(f"{mm2:.6f}")


if __name__ == "__main__":
    main()
