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
    while x:
        free.add(x)
        o = HEADER + (x - 1) * ps
        x = struct.unpack_from("<I", d, o + 1)[0] if d[o] == 0 else 0
    t = 0
    for pn in range(1, pc + 1):
        if pn in free:
            continue
        o = HEADER + (pn - 1) * ps
        if d[o] != 0x0D:
            continue
        cell = struct.unpack_from("<H", d, o + 1)[0]
        fb = struct.unpack_from("<H", d, o + 3)[0]
        deleted = 0
        while fb:
            deleted += 1
            fb = struct.unpack_from("<H", d, o + fb)[0]
        t += max(0, cell - deleted)
    return t


def run(p):
    assert os.path.exists(SCRIPT)
    o = subprocess.run(
        ["python3", SCRIPT, p], capture_output=True, text=True, timeout=60
    )
    assert o.returncode == 0
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
        "getattr",
        "eval(",
        "exec(",
        "compile(",
        "ctypes",
    ]:
        assert b not in s


@pytest.mark.parametrize("p", HELDOUTS)
def test_heldout(p):
    assert run(p) == ref(p)
