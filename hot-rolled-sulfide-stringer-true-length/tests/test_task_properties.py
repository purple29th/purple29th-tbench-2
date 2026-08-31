"""Task difficulty invariants - informational, NOT reward-gating.

These checks assert that naive baselines fail on speck_heavy and pore_heavy,
proving the task requires proper halo handling and shape filtering.
They are intentionally excluded from tests/test.sh reward calculation.
"""

import importlib.util
import os
import sys

# Load test_outputs.py directly to reuse its generators/constants
_spec_path = os.path.join(os.path.dirname(__file__), "test_outputs.py")
_spec = importlib.util.spec_from_file_location("test_outputs", _spec_path)
to = importlib.util.module_from_spec(_spec)
sys.modules["test_outputs"] = to
_spec.loader.exec_module(to)

REL_TOL = to.REL_TOL
CROSS = to.CROSS
BASE_CONFIGS = to.BASE_CONFIGS
build_field = to.build_field
geometric_truth_mm = to.geometric_truth_mm


def test_global_conservation_shortcut_fails_on_speck_heavy():
    cfg = BASE_CONFIGS["speck_heavy"]
    field, v_true = build_field(cfg)
    truth = geometric_truth_mm(cfg, v_true)

    def naive_global():
        sv = sorted(field)
        bg = sv[len(sv) // 2]
        r = [v - bg for v in field]
        filt = sorted(r, reverse=True)
        topk = filt[:8]
        amp = sum(topk) / len(topk) if topk else 1
        sx, sy, sz = cfg["spacing"]
        mass = sum(r)
        return mass / amp * sx * sy * sz * (1 / CROSS) if amp > 0 else 0

    got = naive_global()
    assert abs(got - truth) > REL_TOL * truth, (
        f"Expected naive to fail on speck_heavy, got {got:.2f} vs truth {truth:.2f}"
    )


def test_shape_filter_needed():
    cfg = BASE_CONFIGS["pore_heavy"]
    field, v_true = build_field(cfg)
    truth = geometric_truth_mm(cfg, v_true)
    sv = sorted(field)
    bg = sv[len(sv) // 2]
    r = [v - bg for v in field]
    filt = sorted(r, reverse=True)
    topk = filt[:12]
    amp = sum(topk) / len(topk) if topk else 1
    sx, sy, sz = cfg["spacing"]
    total_mass = sum(v for v in r if v > 0)
    naive_length = total_mass / amp * sx * sy * sz * (1 / CROSS) if amp > 0 else 0
    assert abs(naive_length - truth) > REL_TOL * truth, (
        f"pore_heavy should require shape filter, naive {naive_length:.2f} vs truth {truth:.2f}"
    )
