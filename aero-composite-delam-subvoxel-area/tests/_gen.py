import struct, math, random, os, sys
from pathlib import Path

MAGIC = b"UDEL"


def gauss_kernel1d(sigma, radius):
    w = [math.exp(-(x * x) / (2 * sigma * sigma)) for x in range(-radius, radius + 1)]
    s = sum(w)
    return [v / s for v in w]


def blur_2d(vol, nx, ny, sig):
    r = max(1, int(math.ceil(3.5 * sig)))
    k = gauss_kernel1d(sig, r)

    def idx(x, y):
        return x + nx * y

    a = [0.0] * len(vol)
    for y in range(ny):
        base = nx * y
        for x in range(nx):
            acc = 0.0
            for t in range(-r, r + 1):
                xx = x + t
                if 0 <= xx < nx:
                    acc += vol[base + xx] * k[t + r]
            a[base + x] = acc
    b = [0.0] * len(vol)
    for x in range(nx):
        for y in range(ny):
            acc = 0.0
            for t in range(-r, r + 1):
                yy = y + t
                if 0 <= yy < ny:
                    acc += a[idx(x, yy)] * k[t + r]
            b[idx(x, y)] = acc
    return b


def build_field(cfg):
    nx, ny = cfg["dims"]
    n = nx * ny

    def idx(x, y):
        return x + nx * y

    clean = [0.0] * n
    true_occupancy = [0.0] * n
    true_set = set()

    def add_ellipse(cx, cy, rx, ry, partial=1.0):
        for y in range(ny):
            for x in range(nx):
                dx = (x - cx) / rx
                dy = (y - cy) / ry
                d2 = dx * dx + dy * dy
                if d2 <= 1.0:
                    # partial near edge to simulate subvoxel
                    if d2 > 0.7:
                        occ = partial * (1.0 - (d2 - 0.7) / 0.3 * 0.5)
                    else:
                        occ = partial
                    if occ > 0:
                        true_set.add(idx(x, y))
                        true_occupancy[idx(x, y)] = max(true_occupancy[idx(x, y)], occ)
                elif d2 <= 1.2:
                    # thin border partial
                    occ = partial * 0.3 * (1.0 - (d2 - 1.0) / 0.2)
                    if occ > 0.01:
                        true_occupancy[idx(x, y)] = max(true_occupancy[idx(x, y)], occ)

    def add_box(x0, x1, y0, y1, partial=1.0):
        for y in range(y0, y1):
            for x in range(x0, x1):
                if 0 <= x < nx and 0 <= y < ny:
                    true_set.add(idx(x, y))
                    true_occupancy[idx(x, y)] = max(true_occupancy[idx(x, y)], partial)

    def add_finger(x0, y0, length, angle, width=1.5):
        # thin feathered finger
        for i in range(length):
            t = i / length
            cx = x0 + math.cos(angle) * i
            cy = y0 + math.sin(angle) * i
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    x = int(round(cx + dx))
                    y = int(round(cy + dy))
                    if 0 <= x < nx and 0 <= y < ny:
                        dist = math.hypot(dx, dy)
                        if dist <= width:
                            occ = 0.4 * (1 - dist / width) * (1 - t * 0.3)
                            true_occupancy[idx(x, y)] = max(
                                true_occupancy[idx(x, y)], occ
                            )
                            if occ > 0.25:
                                true_set.add(idx(x, y))

    for shp in cfg["object"]:
        typ = shp[0]
        if typ == "ell":
            _, cx, cy, rx, ry, partial = shp
            add_ellipse(cx, cy, rx, ry, partial)
        elif typ == "box":
            _, x0, x1, y0, y1, partial = shp
            add_box(x0, x1, y0, y1, partial)
        elif typ == "finger":
            _, x0, y0, length, angle, width = shp
            add_finger(x0, y0, length, angle, width)

    amp = cfg["amp"]
    for i in range(n):
        clean[i] = true_occupancy[i] * amp

    # add specks far away
    for sx0, sy0, sr in cfg["specks"]:
        for y in range(ny):
            for x in range(nx):
                if (x - sx0) ** 2 + (y - sy0) ** 2 <= sr * sr:
                    clean[idx(x, y)] = max(clean[idx(x, y)], amp * 0.9)

    blurred = blur_2d(clean, nx, ny, cfg["sig"])

    bg = cfg["bg"]
    ns = cfg["noise"]
    rng = random.Random(cfg["seed"])
    field = [blurred[i] + bg + rng.gauss(0, ns) for i in range(n)]

    # true voxel count weighted by partial occupancy
    v_true = sum(true_occupancy)
    return field, v_true, true_occupancy


def pack_udel(cfg, field):
    nx, ny = cfg["dims"]
    sx, sy = cfg["spacing"]
    dtype = cfg["dtype"]
    n = nx * ny
    hdr = bytearray(64)
    hdr[0:4] = MAGIC
    struct.pack_into("<I", hdr, 4, 1)
    struct.pack_into("<I", hdr, 8, dtype)
    struct.pack_into("<II", hdr, 12, nx, ny)
    struct.pack_into("<ff", hdr, 20, sx, sy)
    struct.pack_into("<I", hdr, 28, 64)
    if dtype == 2:
        vals = [max(-32768, min(32767, int(round(v)))) for v in field]
        body = struct.pack("<%dh" % n, *vals)
    else:
        body = struct.pack("<%df" % n, *field)
    return bytes(hdr) + body


def geometric_truth_mm2(cfg, v_true):
    sx, sy = cfg["spacing"]
    return v_true * sx * sy


BASE_CONFIGS = {
    "scene": dict(
        dims=(80, 60),
        spacing=(0.5, 0.5),
        dtype=16,
        amp=1200,
        bg=80,
        sig=2.2,
        noise=12,
        seed=101,
        object=[
            ("ell", 40, 30, 12, 8, 1.0),
            ("box", 50, 62, 28, 32, 1.0),
            ("finger", 52, 30, 18, 0.3, 1.8),
            ("finger", 30, 30, 14, 2.9, 1.5),
        ],
        specks=[(12, 10, 2.5), (70, 50, 2.0)],
    ),
    "heldout_1": dict(
        dims=(72, 68),
        spacing=(0.45, 0.45),
        dtype=16,
        amp=1000,
        bg=60,
        sig=2.6,
        noise=10,
        seed=202,
        object=[
            ("ell", 35, 34, 10, 9, 1.0),
            ("box", 45, 58, 32, 36, 1.0),
            ("finger", 48, 34, 16, 0.1, 1.6),
            ("finger", 20, 34, 12, 3.0, 1.4),
        ],
        specks=[(10, 12, 2.2), (65, 55, 1.8), (60, 10, 1.5)],
    ),
    "heldout_2": dict(
        dims=(64, 64),
        spacing=(0.6, 0.6),
        dtype=2,
        amp=1400,
        bg=90,
        sig=1.9,
        noise=14,
        seed=303,
        object=[
            ("ell", 32, 32, 11, 7, 1.0),
            ("finger", 42, 32, 20, 0.5, 1.7),
            ("finger", 22, 32, 15, 2.7, 1.6),
            ("box", 30, 36, 20, 28, 0.8),
        ],
        specks=[(8, 8, 2.0), (58, 10, 1.9)],
    ),
    "heldout_3": dict(
        dims=(84, 56),
        spacing=(0.4, 0.55),
        dtype=16,
        amp=1100,
        bg=70,
        sig=2.4,
        noise=11,
        seed=404,
        object=[
            ("ell", 42, 28, 13, 8, 1.0),
            ("box", 55, 68, 26, 30, 1.0),
            ("finger", 58, 28, 22, 0.2, 1.8),
            ("finger", 28, 28, 18, 3.1, 1.5),
            ("box", 38, 45, 15, 24, 0.7),
        ],
        specks=[(12, 45, 2.3), (72, 12, 2.0)],
    ),
    "speck_heavy": dict(
        dims=(80, 60),
        spacing=(0.5, 0.5),
        dtype=16,
        amp=1200,
        bg=80,
        sig=2.2,
        noise=12,
        seed=101,
        object=[
            ("ell", 40, 30, 12, 8, 1.0),
            ("box", 50, 62, 28, 32, 1.0),
            ("finger", 52, 30, 18, 0.3, 1.8),
            ("finger", 30, 30, 14, 2.9, 1.5),
        ],
        specks=[(12, 10, 4.0), (70, 50, 3.5), (15, 50, 3.0)],
    ),
}

if __name__ == "__main__":
    out_dir = Path(__file__).parent / "data"
    out_dir.mkdir(exist_ok=True)
    for name, cfg in BASE_CONFIGS.items():
        field, v_true, occ = build_field(cfg)
        data = pack_udel(cfg, field)
        mm2 = geometric_truth_mm2(cfg, v_true)
        fname = "scene.udel" if name == "scene" else f"{name}.udel"
        (out_dir / fname).write_bytes(data)
        print(f"{name}: {mm2:.3f} mm2, dims {cfg['dims']}, v_true {v_true:.2f}")
    # also copy scene to env data
    env_data = Path(__file__).parent.parent / "environment/data"
    env_data.mkdir(parents=True, exist_ok=True)
    (env_data / "scene.udel").write_bytes((out_dir / "scene.udel").read_bytes())
    print("copied scene to env")
