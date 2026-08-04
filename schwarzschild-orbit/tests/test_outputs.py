"""Behavioral tests for Schwarzschild timelike geodesic integrator - pure base R"""

import math
import os
import subprocess
import tempfile
import pytest

APP_ROOT = "/app"


def schw_r(x, y, z):
    return math.sqrt(x * x + y * y + z * z)


def schw_metric(X, M):
    _, x, y, z = X
    r = schw_r(x, y, z)
    if r < 1e-12:
        r = 1e-12
    f = 2 * M / r
    l = [1.0, x / r, y / r, z / r]
    eta = [[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    return [[eta[i][j] + f * l[i] * l[j] for j in range(4)] for i in range(4)]


def matvec(g, v):
    return [sum(g[i][j] * v[j] for j in range(4)) for i in range(4)]


def invariants(X, u, M):
    g = schw_metric(X, M)
    ul = matvec(g, u)
    uu = sum(u[i] * ul[i] for i in range(4))
    E = -ul[0]
    # angular momentum p_i = g_{i nu} u^nu
    p = ul[1:]
    x, y, z = X[1], X[2], X[3]
    Lx = y * p[2] - z * p[1]
    Ly = z * p[0] - x * p[2]
    Lz = x * p[1] - y * p[0]
    L2 = Lx * Lx + Ly * Ly + Lz * Lz
    return dict(uu=uu, E=E, L2=L2, Lx=Lx, Ly=Ly, Lz=Lz)


def make_velocity(X, vx, vy, vz, M):
    g = schw_metric(X, M)
    A = g[0][0]
    B = 2 * (g[0][1] * vx + g[0][2] * vy + g[0][3] * vz)
    C = (
        g[1][1] * vx * vx
        + g[2][2] * vy * vy
        + g[3][3] * vz * vz
        + 2 * g[1][2] * vx * vy
        + 2 * g[1][3] * vx * vz
        + 2 * g[2][3] * vy * vz
    ) + 1.0
    disc = B * B - 4 * A * C
    ut = (-B - math.sqrt(disc)) / (2 * A)
    if ut < 0:
        ut = (-B + math.sqrt(disc)) / (2 * A)
    return [ut, vx, vy, vz]


def config(M, d_tau, tau_max, R0, vx, vy, vz):
    X0 = [0.0, R0, 0.0, 0.0]
    u0 = make_velocity(X0, vx, vy, vz, M)
    return dict(
        M=M, d_tau=d_tau, tau_max=tau_max, initial_position=X0, initial_velocity=u0
    )


DRIVER = r"""
args <- commandArgs(trailingOnly = TRUE)
source(args[1])
source(args[2])
res <- run_simulation(config)
fp <- as.numeric(res$final_position)
fv <- as.numeric(res$final_velocity)
con <- file(args[3], "w")
writeLines(c(
  as.character(res$termination_reason),
  paste(format(fp, digits=17, scientific=TRUE), collapse=" "),
  paste(format(fv, digits=17, scientific=TRUE), collapse=" "),
  format(as.numeric(res$max_velocity_drift), digits=17, scientific=TRUE),
  format(as.numeric(res$max_energy_drift), digits=17, scientific=TRUE),
  format(as.numeric(res$max_angular_momentum_drift), digits=17, scientific=TRUE)
), con)
close(con)
"""


def r_vec(v):
    return "c(" + ", ".join(repr(float(x)) for x in v) + ")"


def find_agent():
    import glob

    for p in sorted(
        glob.glob(os.path.join(APP_ROOT, "**", "*.R"), recursive=True)
        + glob.glob(os.path.join(APP_ROOT, "**", "*.r"), recursive=True)
    ):
        try:
            with open(p, encoding="utf-8", errors="ignore") as fh:
                src = fh.read()
        except OSError:
            continue
        if "run_simulation" in src:
            return p
    return None


def run_sim(cfg, timeout=540):
    agent = find_agent()
    assert agent is not None, "No .R file defining run_simulation found under /app."
    with tempfile.TemporaryDirectory() as d:
        drv = os.path.join(d, "driver.R")
        cfgp = os.path.join(d, "config.R")
        outp = os.path.join(d, "out.txt")
        with open(drv, "w") as fh:
            fh.write(DRIVER)
        with open(cfgp, "w") as fh:
            fh.write(
                "config <- list(\n"
                f"  M = {float(cfg['M'])!r},\n"
                f"  d_tau = {float(cfg['d_tau'])!r},\n"
                f"  tau_max = {float(cfg['tau_max'])!r},\n"
                f"  initial_position = {r_vec(cfg['initial_position'])},\n"
                f"  initial_velocity = {r_vec(cfg['initial_velocity'])}\n"
                ")\n"
            )
        proc = subprocess.run(
            ["Rscript", "--vanilla", drv, agent, cfgp, outp],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        assert proc.returncode == 0, (
            f"Rscript exit {proc.returncode}\nSTDOUT\n{proc.stdout[-2000:]}\nSTDERR\n{proc.stderr[-2000:]}"
        )
        assert os.path.exists(outp), f"no result\nSTDERR\n{proc.stderr[-2000:]}"
        with open(outp) as fh:
            lines = fh.read().splitlines()
    res = dict(
        reason=lines[0].strip(),
        final_position=[float(v) for v in lines[1].split()],
        final_velocity=[float(v) for v in lines[2].split()],
        max_velocity_drift=float(lines[3]),
        max_energy_drift=float(lines[4]),
        max_angular_drift=float(lines[5]),
    )
    M = cfg["M"]
    inv0 = invariants(cfg["initial_position"], cfg["initial_velocity"], M)
    invf = invariants(res["final_position"], res["final_velocity"], M)
    res["indep_uu"] = abs(invf["uu"] - inv0["uu"])
    res["indep_E"] = abs(invf["E"] - inv0["E"])
    res["indep_L2"] = abs(invf["L2"] - inv0["L2"])
    # also energy drift from start
    res["E0"] = inv0["E"]
    res["Ef"] = invf["E"]
    res["energy_drift"] = abs(invf["E"] - inv0["E"])
    return res


def check_shape(res):
    assert res["reason"] in ("escaped", "captured", "timeout")
    assert len(res["final_position"]) == 4
    assert len(res["final_velocity"]) == 4


TOL_UU = 1e-10
TOL_E = 1e-6
TOL_L2 = 1e-9
INDEP_TOL_UU = 1e-9
INDEP_TOL_E = 1e-6
INDEP_TOL_L2 = 1e-9


def assert_cons(res):
    assert res["max_velocity_drift"] < TOL_UU, res["max_velocity_drift"]
    assert res["max_energy_drift"] < TOL_E, res["max_energy_drift"]
    assert res["max_angular_drift"] < TOL_L2, res["max_angular_drift"]
    assert res["indep_uu"] < INDEP_TOL_UU, res["indep_uu"]
    assert res["indep_E"] < INDEP_TOL_E, res["indep_E"]
    assert res["indep_L2"] < INDEP_TOL_L2, res["indep_L2"]


def test_shape():
    res = run_sim(config(1.0, 0.8, 30.0, 10.0, 0.0, 0.3, 0.0))
    check_shape(res)


def test_conserves_bound():
    res = run_sim(config(1.0, 0.8, 100.0, 10.0, 0.0, 0.30, 0.02))
    check_shape(res)
    assert res["reason"] == "timeout"
    assert_cons(res)


def test_escape():
    res = run_sim(config(0.5, 0.2, 1000.0, 50.0, 0.9, 0.0, 0.0))
    check_shape(res)
    assert res["reason"] == "escaped"
    assert_cons(res)


def test_capture():
    res = run_sim(config(1.0, 0.02, 80.0, 6.0, -0.2, 0.15, 0.0))
    check_shape(res)
    assert res["reason"] == "captured"
    assert_cons(res)


def test_off_equatorial():
    res = run_sim(config(1.0, 0.8, 100.0, 10.0, 0.1, 0.25, 0.15))
    check_shape(res)
    assert res["reason"] == "timeout"
    assert_cons(res)


def test_nonunit_mass():
    res = run_sim(config(2.0, 0.8, 80.0, 12.0, 0.0, 0.32, 0.04))
    check_shape(res)
    assert res["reason"] == "timeout"
    assert_cons(res)


def test_polar():
    res = run_sim(config(1.0, 0.8, 80.0, 9.0, 0.0, 0.05, 0.32))
    check_shape(res)
    assert res["reason"] == "timeout"
    assert_cons(res)


def test_energy_blocks_reproj():
    res = run_sim(config(1.0, 0.8, 60.0, 8.0, 0.0, 0.35, 0.0))
    check_shape(res)
    assert res["energy_drift"] < TOL_E


def test_zoom_whirl():
    # near critical zoom-whirl just outside photon sphere, requires adaptive step and tight conservation
    res = run_sim(config(1.0, 0.8, 200.0, 7.0, 0.0, 0.42, 0.03))
    check_shape(res)
    assert res["reason"] in ("timeout", "captured")
    assert_cons(res)


def test_high_eccentric():
    # high eccentricity plunge from 30M that grazes near 4M, strong field precession
    res = run_sim(config(1.0, 0.8, 150.0, 30.0, -0.25, 0.18, 0.02))
    check_shape(res)
    assert res["reason"] in ("timeout", "captured", "escaped")
    assert_cons(res)


def test_close_pericenter():
    # close pericenter at 5M, tests horizon approaching robustness without NaN
    res = run_sim(config(1.0, 0.5, 80.0, 4.5, -0.15, 0.38, 0.02))
    check_shape(res)
    assert_cons(res)
