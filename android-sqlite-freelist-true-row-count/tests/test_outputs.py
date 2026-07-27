import os, struct, subprocess, pytest

SCRIPT = "/app/solve.py"
HELDOUTS = [
    "/tests/data/heldout_1.sdb",
    "/tests/data/heldout_2.sdb",
    "/tests/data/heldout_3.sdb",
]
HEADER = 64


def ref(p):
    d = open(p, "rb").read()
    assert d[:4] == b"SDB1"
    ps = struct.unpack_from("<I", d, 8)[0]
    pc = struct.unpack_from("<I", d, 12)[0]
    fh = struct.unpack_from("<I", d, 16)[0]
    free = set()
    x = fh
    visited = set()
    while x and x not in visited:
        visited.add(x)
        free.add(x)
        o = HEADER + (x - 1) * ps
        if o >= len(d) or d[o] != 0x00:
            break
        nxt = struct.unpack_from("<I", d, o + 1)[0]
        leaf_cnt = struct.unpack_from("<I", d, o + 5)[0]
        for i in range(leaf_cnt):
            if o + 9 + i * 4 + 4 > len(d):
                break
            lp = struct.unpack_from("<I", d, o + 9 + i * 4)[0]
            if lp:
                free.add(lp)
        x = nxt
    t = 0
    for pn in range(1, pc + 1):
        if pn in free:
            continue
        o = HEADER + (pn - 1) * ps
        if o >= len(d):
            continue
        typ = d[o]
        if typ == 0x05:
            continue
        if typ != 0x0D:
            continue
        cell = struct.unpack_from("<H", d, o + 1)[0]
        fb = struct.unpack_from("<H", d, o + 3)[0]
        intervals = []
        seen = set()
        while fb and fb not in seen:
            seen.add(fb)
            if o + fb + 4 > len(d):
                break
            nxt = struct.unpack_from("<H", d, o + fb)[0]
            sz = struct.unpack_from("<H", d, o + fb + 2)[0]
            if sz == 0:
                break
            intervals.append((fb, fb + sz))
            fb = nxt
        for i in range(cell):
            if o + 7 + i * 2 + 2 > len(d):
                break
            ptr = struct.unpack_from("<H", d, o + 7 + i * 2)[0]
            if ptr == 0 or ptr >= ps:
                continue
            if any(s <= ptr < e for s, e in intervals):
                continue
            t += 1
    return t


def run(p):
    assert os.path.exists(SCRIPT)
    o = subprocess.run(
        ["python3", SCRIPT, p], capture_output=True, text=True, timeout=60
    )
    assert o.returncode == 0, f"failed {o.stdout} {o.stderr}"
    return int(o.stdout.strip().split()[-1])


def test_exists():
    assert os.path.exists(SCRIPT)


def test_from_scratch():
    s = open(SCRIPT).read().replace(" ", "")
    for b in [
        "importsqlite3",
        "fromsqlite3",
        "importpandas",
        "importsqlalchemy",
        "importnumpy",
        "subprocess.",
        "os.system",
        "os.popen",
        "__import__(",
        "importlib",
    ]:
        assert b not in s


@pytest.mark.parametrize("p", HELDOUTS)
def test_heldout(p):
    assert run(p) == ref(p)
