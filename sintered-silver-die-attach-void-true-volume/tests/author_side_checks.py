"""Author-side calibration checks (not graded).

These verify that shortcut methods fail on the trap configs.
They are NOT part of the graded verifier (test_outputs.py).
Moved per review to avoid counting calibration as agent grade.
"""

import math
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from test_outputs import build_field, geometric_truth_mm3, BASE_CONFIGS


def check_global_conservation_fails_on_speck_heavy():
    cfg = BASE_CONFIGS["speck_heavy"]
    field, v_true = build_field(cfg)
    truth = geometric_truth_mm3(cfg, v_true)

    def naive_global():
        sv = sorted(field)
        bg = sv[len(sv) // 2]
        r = [v - bg for v in field]
        filt = sorted(r, reverse=True)
        topk = filt[:8]
        amp = sum(topk) / len(topk) if topk else 1
        sx, sy, sz = cfg["spacing"]
        mass = sum(r)
        return mass / amp * sx * sy * sz if amp > 0 else 0

    got = naive_global()
    assert abs(got - truth) > 0.03 * truth, (
        f"Expected naive global to fail on speck_heavy, got {got:.5f} vs truth {truth:.5f}"
    )
    print(
        f"speck_heavy calibration: naive {got:.5f} vs truth {truth:.5f} FAIL as expected"
    )


def check_pixel_count_fails_on_pixel_trap():
    cfg = BASE_CONFIGS["pixel_count_trap"]
    field, v_true = build_field(cfg)
    truth = geometric_truth_mm3(cfg, v_true)
    nx, ny, nz = cfg["dims"]
    sx, sy, sz = cfg["spacing"]

    def idx(x, y, z):
        return x + nx * (y + ny * z)

    sv = sorted(field)
    lower = sv[: len(sv) // 2]
    bg = lower[len(lower) // 2] if lower else 0
    resid = [v - bg for v in field]
    lower_res = sorted([v - bg for v in lower])
    med_low = lower_res[len(lower_res) // 2] if lower_res else 0
    abs_dev = sorted(abs(r - med_low) for r in lower_res)
    mad = abs_dev[len(abs_dev) // 2] if abs_dev else 1
    sigma = max(1e-6, 1.4826 * mad)
    thr = 4.0 * sigma
    occ = [r > thr for r in resid]

    seen = bytearray(len(field))
    best_cnt = -1
    best = None
    NEIGH = [
        (dx, dy, dz)
        for dz in (-1, 0, 1)
        for dy in (-1, 0, 1)
        for dx in (-1, 0, 1)
        if dx or dy or dz
    ]
    for z0 in range(nz):
        for y0 in range(ny):
            for x0 in range(nx):
                k = idx(x0, y0, z0)
                if not occ[k] or seen[k]:
                    continue
                stack = [(x0, y0, z0)]
                seen[k] = 1
                comp = []
                while stack:
                    x, y, z = stack.pop()
                    kk = idx(x, y, z)
                    comp.append(kk)
                    for dx, dy, dz in NEIGH:
                        xx, yy, zz = x + dx, y + dy, z + dz
                        if 0 <= xx < nx and 0 <= yy < ny and 0 <= zz < nz:
                            nn = idx(xx, yy, zz)
                            if occ[nn] and not seen[nn]:
                                seen[nn] = 1
                                stack.append((xx, yy, zz))
                if len(comp) > best_cnt:
                    best_cnt = len(comp)
                    best = comp

    assert best is not None
    naive_vol = len(best) * sx * sy * sz
    assert abs(naive_vol - truth) > 0.03 * truth, (
        f"Expected pixel-count to fail, got {naive_vol:.5f} vs truth {truth:.5f}"
    )
    print(
        f"pixel_count_trap calibration: naive {naive_vol:.5f} vs truth {truth:.5f} FAIL as expected"
    )


if __name__ == "__main__":
    check_global_conservation_fails_on_speck_heavy()
    check_pixel_count_fails_on_pixel_trap()
    print("Author calibration checks PASS (shortcuts fail as intended)")
