import sys
import struct

HEADER = 64


def count_live(path):
    with open(path, "rb") as f:
        d = f.read()
    if d[:4] != b"SDB1":
        raise ValueError("not SDB1")
    ps = struct.unpack_from("<I", d, 8)[0]
    pc = struct.unpack_from("<I", d, 12)[0]
    fh = struct.unpack_from("<I", d, 16)[0]

    free = set()
    x = fh
    visited = set()
    while x and x not in visited:
        visited.add(x)
        free.add(x)
        off = HEADER + (x - 1) * ps
        if off >= len(d) or d[off] != 0x00:
            break
        nxt = struct.unpack_from("<I", d, off + 1)[0]
        leaf_cnt = struct.unpack_from("<I", d, off + 5)[0]
        for i in range(leaf_cnt):
            if off + 9 + i * 4 + 4 > len(d):
                break
            lp = struct.unpack_from("<I", d, off + 9 + i * 4)[0]
            if lp:
                free.add(lp)
        x = nxt

    total = 0
    for pn in range(1, pc + 1):
        if pn in free:
            continue
        off = HEADER + (pn - 1) * ps
        if off >= len(d):
            continue
        typ = d[off]
        if typ == 0x05:
            continue
        if typ != 0x0D:
            continue
        cell_count = struct.unpack_from("<H", d, off + 1)[0]
        fb_off = struct.unpack_from("<H", d, off + 3)[0]

        intervals = []
        seen = set()
        fb = fb_off
        while fb and fb not in seen:
            seen.add(fb)
            if off + fb + 4 > len(d):
                break
            nxt = struct.unpack_from("<H", d, off + fb)[0]
            sz = struct.unpack_from("<H", d, off + fb + 2)[0]
            if sz == 0:
                break
            intervals.append((fb, fb + sz))
            fb = nxt

        for i in range(cell_count):
            if off + 7 + i * 2 + 2 > len(d):
                break
            ptr = struct.unpack_from("<H", d, off + 7 + i * 2)[0]
            if ptr == 0 or ptr >= ps:
                continue
            if any(s <= ptr < e for s, e in intervals):
                continue
            total += 1
    return total


if __name__ == "__main__":
    print(count_live(sys.argv[1]) if len(sys.argv) > 1 else 0)
