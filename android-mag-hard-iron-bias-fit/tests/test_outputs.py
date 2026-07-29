"""
Evaluation for android-mag-hard-iron-bias-fit
Tests estimate_hard_iron_bias from mag_calibration.py
"""

import os
import sys
import json
import numpy as np
import pytest

# Ensure /app is on path, as T-Bench runs from working dir
sys.path.insert(0, "/app")
sys.path.insert(0, os.getcwd())


def generate_orbit(N, radius, bias, noise_std=0.0, coverage=1.0, seed=0):
    """Generate synthetic orbit data.
    coverage: 1.0 = full sphere, 0.6 = 60% azimuth coverage for partial test
    """
    rng = np.random.default_rng(seed)
    # uniform sphere via normal method, but adjust phi coverage
    if coverage >= 0.999:
        pts = rng.standard_normal((N, 3))
        pts = pts / np.linalg.norm(pts, axis=1, keepdims=True) * radius
    else:
        # partial coverage: limit azimuth phi to fraction of 2pi
        # theta uniform [0, pi], phi uniform [0, 2pi*coverage]
        # this creates a missing wedge
        u = rng.random(N)
        theta = np.arccos(2 * u - 1)  # [0, pi]
        phi = rng.random(N) * 2 * np.pi * coverage
        pts = np.zeros((N, 3))
        pts[:, 0] = radius * np.sin(theta) * np.cos(phi)
        pts[:, 1] = radius * np.sin(theta) * np.sin(phi)
        pts[:, 2] = radius * np.cos(theta)
    bias = np.array(bias, dtype=float)
    raw = pts + bias
    if noise_std > 0:
        raw = raw + rng.normal(0, noise_std, size=raw.shape)
    return raw


def load_agent_module():
    if not os.path.exists("/app/mag_calibration.py") and not os.path.exists(
        "mag_calibration.py"
    ):
        pytest.fail(
            "Required file mag_calibration.py not found in /app or cwd. Create /app/mag_calibration.py with function estimate_hard_iron_bias"
        )
    # try import
    try:
        import mag_calibration

        # reload if needed
        import importlib

        importlib.reload(mag_calibration)
    except Exception as e:
        pytest.fail(f"Failed to import mag_calibration.py: {e}")
    if not hasattr(mag_calibration, "estimate_hard_iron_bias"):
        pytest.fail(
            "mag_calibration.py must define function estimate_hard_iron_bias(mag_xyz: np.ndarray) -> dict"
        )
    return mag_calibration


def assert_result_close(
    result, true_bias, true_radius, bias_tol, radius_tol, case_name=""
):
    assert isinstance(result, dict), (
        f"{case_name}: result must be dict, got {type(result)}"
    )
    for k in ["bx", "by", "bz", "radius"]:
        assert k in result, f"{case_name}: result missing key '{k}'"
        val = result[k]
        assert isinstance(val, (float, int, np.floating)), (
            f"{case_name}: {k} must be float, got {type(val)}"
        )
    bx, by, bz, r = (
        float(result["bx"]),
        float(result["by"]),
        float(result["bz"]),
        float(result["radius"]),
    )
    assert r > 0, f"{case_name}: radius must be >0, got {r}"
    true_bias = np.array(true_bias)
    err_bx = abs(bx - true_bias[0])
    err_by = abs(by - true_bias[1])
    err_bz = abs(bz - true_bias[2])
    err_r = abs(r - true_radius)
    assert err_bx <= bias_tol, (
        f"{case_name}: bx error {err_bx:.3f} > tol {bias_tol}, got bx={bx:.2f} vs true {true_bias[0]:.2f}"
    )
    assert err_by <= bias_tol, f"{case_name}: by error {err_by:.3f} > tol {bias_tol}"
    assert err_bz <= bias_tol, f"{case_name}: bz error {err_bz:.3f} > tol {bias_tol}"
    assert err_r <= radius_tol, (
        f"{case_name}: radius error {err_r:.3f} > tol {radius_tol}, got R={r:.2f} vs true {true_radius:.2f}"
    )


def test_file_exists():
    assert os.path.exists("/app/mag_calibration.py") or os.path.exists(
        "mag_calibration.py"
    )


def test_import_and_signature():
    mod = load_agent_module()
    # quick smoke
    data = generate_orbit(100, 45.0, [0, 0, 0], 0.0, 1.0, seed=1)
    res = mod.estimate_hard_iron_bias(data)
    assert isinstance(res, dict)


def test_clean_orbit():
    mod = load_agent_module()
    true_bias = [15.0, -20.0, 8.0]
    true_r = 45.0
    data = generate_orbit(300, true_r, true_bias, noise_std=0.0, coverage=1.0, seed=100)
    result = mod.estimate_hard_iron_bias(data)
    assert_result_close(
        result, true_bias, true_r, bias_tol=0.3, radius_tol=0.3, case_name="clean_orbit"
    )


def test_noisy_orbit():
    mod = load_agent_module()
    true_bias = [15.0, -20.0, 8.0]
    true_r = 45.0
    data = generate_orbit(500, true_r, true_bias, noise_std=1.0, coverage=1.0, seed=200)
    result = mod.estimate_hard_iron_bias(data)
    assert_result_close(
        result, true_bias, true_r, bias_tol=0.8, radius_tol=0.8, case_name="noisy_orbit"
    )


def test_partial_orbit():
    mod = load_agent_module()
    true_bias = [10.0, 5.0, -12.0]
    true_r = 50.0
    data = generate_orbit(200, true_r, true_bias, noise_std=0.5, coverage=0.6, seed=300)
    result = mod.estimate_hard_iron_bias(data)
    assert_result_close(
        result,
        true_bias,
        true_r,
        bias_tol=1.5,
        radius_tol=1.5,
        case_name="partial_orbit",
    )


def test_strong_bias():
    mod = load_agent_module()
    true_bias = [55.0, -60.0, 35.0]
    true_r = 48.0
    data = generate_orbit(400, true_r, true_bias, noise_std=0.8, coverage=1.0, seed=400)
    result = mod.estimate_hard_iron_bias(data)
    assert_result_close(
        result, true_bias, true_r, bias_tol=1.0, radius_tol=1.0, case_name="strong_bias"
    )


def test_random_stress():
    mod = load_agent_module()
    rng = np.random.default_rng(999)
    for i in range(5):
        true_bias = rng.uniform(-50, 50, size=3).tolist()
        true_r = float(rng.uniform(30, 60))
        N = int(rng.integers(100, 800))
        noise = float(rng.uniform(0.2, 1.2))
        data = generate_orbit(
            N, true_r, true_bias, noise_std=noise, coverage=1.0, seed=500 + i
        )
        result = mod.estimate_hard_iron_bias(data)
        tol = max(0.8, noise * 1.2)
        assert_result_close(
            result,
            true_bias,
            true_r,
            bias_tol=tol,
            radius_tol=tol,
            case_name=f"random_stress_{i}",
        )


def test_small_variation_radius():
    mod = load_agent_module()
    # low radius case
    true_bias = [-5.0, 10.0, 2.0]
    true_r = 32.0
    data = generate_orbit(250, true_r, true_bias, noise_std=0.3, coverage=1.0, seed=700)
    result = mod.estimate_hard_iron_bias(data)
    assert_result_close(
        result, true_bias, true_r, bias_tol=0.6, radius_tol=0.6, case_name="low_radius"
    )


def test_output_types_json_serializable():
    mod = load_agent_module()
    data = generate_orbit(150, 45.0, [1, 2, 3], 0.2, 1.0, seed=800)
    result = mod.estimate_hard_iron_bias(data)
    try:
        json.dumps(result)
    except Exception as e:
        pytest.fail(f"Result not JSON serializable: {e}")


def test_determinism():
    mod = load_agent_module()
    data = generate_orbit(200, 45.0, [15, -20, 8], 0.5, 1.0, seed=123)
    r1 = mod.estimate_hard_iron_bias(data)
    r2 = mod.estimate_hard_iron_bias(data)
    for k in ["bx", "by", "bz", "radius"]:
        assert abs(float(r1[k]) - float(r2[k])) < 1e-6, (
            f"Non-deterministic result for {k}: {r1[k]} vs {r2[k]}"
        )
