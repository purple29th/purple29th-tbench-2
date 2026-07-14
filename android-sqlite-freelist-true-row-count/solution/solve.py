import sys, struct


def count_live(path):
    with open(path, "rb") as f:
        d = f.read()
    if d[:4] != b"SDB1":
        raise ValueError("not SDB1")
    ps = struct.unpack_from("<I", d, 8)[0]
    pc = struct.unpack_from("<I", d, 12)[0]
    fh = struct.unpack_from("<I", d, 16)[0]
    HEADER = 64
    free = set()
    p = fh
    while p:
        free.add(p)
        off = HEADER + (p - 1) * ps
        if off >= len(d) or d[off] != 0:
            break
        p = struct.unpack_from("<I", d, off + 1)[0]
    total = 0
    for pn in range(1, pc + 1):
        if pn in free:
            continue
        off = HEADER + (pn - 1) * ps
        if off >= len(d) or d[off] != 0x0D:
            continue
        cell_count = struct.unpack_from("<H", d, off + 1)[0]
        fb_off = struct.unpack_from("<H", d, off + 3)[0]
        # count freeblocks inside page to exclude deleted cells
        deleted = 0
        fb = fb_off
        while fb:
            deleted += 1
            if off + fb + 2 > len(d):
                break
            fb = struct.unpack_from("<H", d, off + fb)[0]
        total += max(0, cell_count - deleted)
    return total


if __name__ == "__main__":
    print(count_live(sys.argv[1]) if len(sys.argv) > 1 else 0)
