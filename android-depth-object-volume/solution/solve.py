import sys
import struct

THRESHOLD = 200.0  # any cutoff in the empty band between background and object

def parse_avol(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != b"AVOL":
        raise ValueError("not an AVOL file")
    (dtype,) = struct.unpack_from("<I", data, 8)
    nx, ny, nz = struct.unpack_from("<III", data, 12)
    sx, sy, sz = struct.unpack_from("<fff", data, 24)
    (off,) = struct.unpack_from("<I", data, 36)
    n = nx * ny * nz
    if dtype == 2:
        vals = list(struct.unpack_from("<%dh" % n, data, off))
    elif dtype == 16:
        vals = list(struct.unpack_from("<%df" % n, data, off))
    else:
        raise ValueError("unsupported dtype %d" % dtype)
    return nx, ny, nz, sx, sy, sz, vals

def largest_component_voxels(nx, ny, nz, vals):
    occ = [v > THRESHOLD for v in vals]
    seen = bytearray(len(occ))
    neigh = [(dx, dy, dz)
             for dz in (-1, 0, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
             if not (dx == 0 and dy == 0 and dz == 0)]

    def I(x, y, z):
        return x + nx * (y + ny * z)

    best = 0
    for z0 in range(nz):
        for y0 in range(ny):
            for x0 in range(nx):
                s = I(x0, y0, z0)
                if not occ[s] or seen[s]:
                    continue
                stack = [(x0, y0, z0)]
                seen[s] = 1
                count = 0
                while stack:
                    x, y, z = stack.pop()
                    count += 1
                    for dx, dy, dz in neigh:
                        a, b, c = x + dx, y + dy, z + dz
                        if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                            j = I(a, b, c)
                            if occ[j] and not seen[j]:
                                seen[j] = 1
                                stack.append((a, b, c))
                if count > best:
                    best = count
    return best

def main():
    if len(sys.argv) < 2:
        print(0)
        return
    nx, ny, nz, sx, sy, sz, vals = parse_avol(sys.argv[1])
    voxels = largest_component_voxels(nx, ny, nz, vals)
    print(voxels * sx * sy * sz)

if __name__ == "__main__":
    main()
