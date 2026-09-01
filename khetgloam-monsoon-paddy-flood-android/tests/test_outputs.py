"""Verification for the raw-Vulkan flood-risk pipeline (Android library).

Required artifacts (produced by the agent under /app):
  - libvkflood_host.so   host x86_64 JNI library (raw Vulkan on host/lavapipe)
                         exporting
                         Java_com_example_vkflood_FloodRisk_floodRisk
                         (float[] bottom, float[] wall, float[] inlet, float[] exit,
                          int rows, int cols) -> float[rows*cols] dense risk grid
                         (risk level 1..5 per open cell, 0 on walls). The SAME
                         native code is shipped in the AAR for arm64.
  - risk.comp.spv        a compiled SPIR-V compute shader
  - an AAR under /app packaging an arm64-v8a native lib that links libvulkan and
    exposes a JNI entry point.

Pipeline (per the underground-inundation flood-risk methodology):
  1. Hydraulic time-stepping with a storm pulse: inlet cells are fixed at INFLOW
     depth (Dirichlet) for the first N_INJECT steps, then RELEASED to ordinary open
     cells. Each step advances the water-surface elevation eta = bottom + depth by an
     IMPLICIT (backward-Euler) diffusion -- solving the linear system
     (I - ALPHA*L) eta^{n+1} = eta^n by Jacobi iteration to convergence (walls block
     flow). Run for N_STEPS, keeping every step's depth field.
  2. Peak-momentum time (paper sec 4.3): at each step compute the spatial-mean
     momentum (mean over open cells of depth*speed, speed = VEL_SCALE*|grad eta|);
     the PEAK step (argmax) is the risk-assessment time. FI / evacuation below use
     the depth field at that peak step.
  3. Flood intensity (Beffa): FI = depth * max(1, speed) (FI = h when v<1, else v*h),
     then tertile-classified over the open cells into levels 1/2/3 (paper sec 3.2.1:
     nodes sorted by FI and split into tertiles -- no fixed magic thresholds).
  4. Evacuation difficulty: depth-WEIGHTED shortest path (Dijkstra) over open cells
     to the nearest exit -- entering a cell costs COST_SHALLOW / COST_MID / COST_DEEP
     for shallow / mid / deep water (paper Table 1, three walking-speed regimes split
     at WADE_LOW / WADE_HIGH). Classify the evacuation times into tertiles 1/2/3
     (3 = hardest; unreachable open cells are 3).
  5. Risk = FI_level + difficulty - 1 (clamped 1..5); walls report 0.

Scenarios are random, so outputs cannot be hardcoded.
"""

import glob
import os
import struct
import heapq
import subprocess
import tempfile

import numpy as np

APP = "/app"
HOST_SO = os.path.join(APP, "libvkflood_host.so")
SPV = os.path.join(APP, "risk.comp.spv")

# Pipeline constants (must match the agent's implementation).
# Storm pulse: inlets are held at INFLOW (Dirichlet) for the first N_INJECT steps,
# then RELEASED (treated as ordinary open cells) for the remaining steps, so the
# water spreads and stagnates -- the spatial-mean momentum rises then decays, giving
# an interior peak (paper sec 4.3, "Determination of Peak Risk").
N_STEPS = 20
N_INJECT = 8
ALPHA = np.float32(0.22)
INFLOW = np.float32(3.0)
VEL_SCALE = np.float32(10.0)

# IMPLICIT (backward-Euler) hydraulics: each step solves the linear system
# (I - ALPHA*L) eta^{n+1} = eta^n (L = no-flux graph Laplacian over open cells) by
# Jacobi iteration. The converged solution is UNIQUE -- independent of the iterative
# method or iteration count -- so the grade does not depend on which solver the agent
# picks (only on actually converging). The reference solves to a tight tolerance; the
# implicit step is well-conditioned (cond(I-ALPHA*L) <= 1 + 8*ALPHA regardless of
# grid size), so a fixed N_JACOBI sweeps reaches the same converged field everywhere.
N_JACOBI = 40            # fixed sweeps that reach convergence (oracle / agent guidance)
_JACOBI_TOL = 1e-10      # reference convergence tolerance (max per-cell eta change)
_JACOBI_MAX = 1000       # reference safety cap

# Peak-momentum window tolerance: steps whose spatial-mean momentum is within
# PEAK_TOL of the maximum (plus argmax +/-1) are candidate peak times; the grade is
# made invariant across the whole window so the exact float argmax does not matter.
PEAK_TOL = 0.02

# Evacuation walking cost (paper Table 1: walking speed drops in deeper water, so
# wading through a deep cell takes longer). THREE regimes: paper's 0.4 m / 0.6 m
# depth thresholds (scaled to this INFLOW) with walking speeds 0.7 / (mid) / 0.3 m/s
# -> integer wading costs whose deep/shallow ratio 7/3 ~= 0.7/0.3.
WADE_LOW = np.float32(1.2)   # below this: shallow/fast wading
WADE_HIGH = np.float32(1.8)  # above this: deep/slow wading
COST_SHALLOW = 3
COST_MID = 5
COST_DEEP = 7

# Max assumed per-cell depth drift between the agent's GPU pipeline and this numpy
# reference. GLSL permits floating-point contraction (depth + ALPHA*lap may fuse to
# an fma) and the clamp may compile to either a branch or a max(), so the GPU's last
# bit differs from numpy's and that ~1e-7/step round-off compounds over the steps to
# ~1e-4 (worst ~1e-3 observed). Drift can only change a DISCRETE output where a
# continuous depth feeds a threshold: the FI tertile boundaries, the two wading-cost
# edges (WADE_LOW/WADE_HIGH), the evac-time tertiles, and the peak-momentum argmax.
# DEPTH_DRIFT (>=10x the worst observed) bounds the drift envelope used to mark such
# cells don't-care -- no hand-tuned per-edge epsilon.
DEPTH_DRIFT = np.float32(1e-2)

RNG = np.random.default_rng(20240617)
_HARNESS_DIR = None

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


# --------------------------------------------------------------------------- #
# JNI harness (compiled once): loads the host .so and calls floodRisk
# --------------------------------------------------------------------------- #
def _harness_dir():
    global _HARNESS_DIR
    if _HARNESS_DIR is not None:
        return _HARNESS_DIR
    d = tempfile.mkdtemp(prefix="jniharness-")
    pkg = os.path.join(d, "com", "example", "vkflood")
    os.makedirs(pkg, exist_ok=True)
    with open(os.path.join(pkg, "FloodRisk.java"), "w") as f:
        f.write(
            "package com.example.vkflood;\n"
            "public final class FloodRisk {\n"
            "  public static native float[] floodRisk(float[] bottom, float[] wall,"
            " float[] inlet, float[] exit, int rows, int cols);\n"
            "}\n"
        )
    with open(os.path.join(d, "Harness.java"), "w") as f:
        f.write(
            "import com.example.vkflood.FloodRisk;\n"
            "import java.nio.file.*;\n"
            "public class Harness {\n"
            "  static float[] readGrid(String path, int n) throws Exception {\n"
            "    String[] t = new String(Files.readAllBytes(Paths.get(path))).trim().split(\"\\\\s+\");\n"
            "    float[] g = new float[n];\n"
            "    for (int i=0;i<n;i++) g[i]=Float.parseFloat(t[i]);\n"
            "    return g;\n"
            "  }\n"
            "  public static void main(String[] a) throws Exception {\n"
            "    System.load(a[0]);\n"
            "    int rows = Integer.parseInt(a[1]);\n"
            "    int cols = Integer.parseInt(a[2]);\n"
            "    int n = rows*cols;\n"
            "    float[] bottom = readGrid(a[3], n);\n"
            "    float[] wall = readGrid(a[4], n);\n"
            "    float[] inlet = readGrid(a[5], n);\n"
            "    float[] exit = readGrid(a[6], n);\n"
            "    float[] r = FloodRisk.floodRisk(bottom, wall, inlet, exit, rows, cols);\n"
            "    StringBuilder sb=new StringBuilder();\n"
            "    for (int i=0;i<r.length;i++){ if(i>0) sb.append(' '); sb.append(r[i]); }\n"
            # Write the result to a file (arg 7), NOT stdout, so any native-library
            # logging on stdout/stderr cannot corrupt the parsed result.
            "    Files.write(Paths.get(a[7]), sb.toString().getBytes());\n"
            "  }\n"
            "}\n"
        )
    r = subprocess.run(
        ["javac", "-d", d,
         os.path.join(pkg, "FloodRisk.java"), os.path.join(d, "Harness.java")],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"javac failed: {r.stderr}"
    _HARNESS_DIR = d
    return d


def _write_grid(path, grid2d):
    with open(path, "w") as f:
        f.write(" ".join(repr(float(x)) for x in grid2d.reshape(-1)))


def _detect(bottom, wall, inlet, exit, extra_env=None):
    rows, cols = bottom.shape
    d = _harness_dir()
    with tempfile.TemporaryDirectory() as t:
        paths = [os.path.join(t, n) for n in ("bottom.txt", "wall.txt", "inlet.txt", "exit.txt")]
        of = os.path.join(t, "out.txt")
        for p, g in zip(paths, (bottom, wall, inlet, exit)):
            _write_grid(p, g)
        env = dict(os.environ)
        if extra_env:
            env.update(extra_env)
        proc = subprocess.run(
            ["java", "-cp", d, "Harness", HOST_SO, str(rows), str(cols), *paths, of],
            capture_output=True, text=True, timeout=180, env=env,
        )
        assert proc.returncode == 0, f"JNI harness failed:\n{proc.stdout}\n{proc.stderr}"
        with open(of) as f:
            out_text = f.read()
    vals = [float(x) for x in out_text.split()]
    return vals, proc


# --------------------------------------------------------------------------- #
# Reference (float32), mirroring the GPU op order. GPU-vs-numpy disagreement comes
# only from small float drift in the diffusion (see DEPTH_DRIFT). It is absorbed as
# "don't care" at every place a continuous depth feeds a DISCRETE output, each via a
# drift-invariance envelope (no hand-tuned epsilon):
#   * Peak-momentum time: the FI/evac fields are taken at the step of maximum
#     spatial-mean momentum. A cell is graded only if its risk is identical across
#     the whole peak-candidate window (argmax +/-1 and steps within PEAK_TOL of the
#     max), so the exact float argmax does not matter.
#   * FI tertile level (_fi_confident): FI is tertile-classified, a data-dependent
#     percentile boundary. Grade a cell only if its FI level is the same at the
#     FI-min and FI-max corners of the +/-DEPTH_DRIFT box (bounding the depth term,
#     the gradient-amplified speed term, AND the drifting tertile boundaries).
#   * Evacuation band (_difficulty_confident): the depth->cost steps at WADE_LOW /
#     WADE_HIGH are discrete, so grade a cell only if its evac band is forced when
#     every near-edge cell's wading cost is taken cheapest vs most-expensive (which
#     also bounds the Dijkstra times and their tertile thresholds).
# Walls (expected risk 0) are computed exactly and always graded.
# --------------------------------------------------------------------------- #
def _simulate(bottom, wall, inlet):
    """Storm-pulse IMPLICIT (backward-Euler) diffusion of the water-surface
    elevation eta = bottom + depth. Each step solves the linear system
        (I - ALPHA*L) eta^{n+1} = eta^n          (L = no-flux graph Laplacian)
    i.e. eta_i = (eta^n_i + ALPHA*sum_{open nb} eta_nb) / (1 + ALPHA*deg_i), by Jacobi
    iteration to convergence (the converged field is the UNIQUE solution -- method/
    iteration-count independent). Inlets are Dirichlet (depth INFLOW, so eta =
    bottom+INFLOW) for the first N_INJECT steps, then released to ordinary open cells.
    Computed in float64 to a tight tolerance to define the unique ground truth;
    returns every step's depth field (float32) and the open mask."""
    H = bottom.astype(np.float64)
    open_ = wall < 0.5
    inl = inlet > 0.5
    a = float(ALPHA)
    inf = float(INFLOW)
    deg = np.zeros_like(H)  # number of open neighbours per cell (no-flux)
    for dy, dx in _NEIGHBORS:
        deg += np.where(np.roll(np.roll(open_, dy, 0), dx, 1), 1.0, 0.0)
    h = np.zeros_like(H)
    fields = []
    for t in range(N_STEPS):
        inject = t < N_INJECT
        hc = np.where(inl, inf, h) if inject else h
        rhs = H + hc          # eta^n (right-hand side of the implicit system)
        pin = H + inf          # Dirichlet eta at inlet cells during injection
        eta = rhs.copy()
        for _ in range(_JACOBI_MAX):
            ssum = np.zeros_like(H)
            for dy, dx in _NEIGHBORS:
                nb = np.roll(np.roll(eta, dy, 0), dx, 1)
                nbo = np.roll(np.roll(open_, dy, 0), dx, 1)
                ssum += np.where(nbo, nb, 0.0)
            new = (rhs + a * ssum) / (1.0 + a * deg)
            if inject:
                new = np.where(inl, pin, new)
            new = np.where(open_, new, eta)  # walls untouched (excluded from L)
            delta = np.max(np.abs((new - eta)[open_])) if open_.any() else 0.0
            eta = new
            if delta < _JACOBI_TOL:
                break
        h = np.maximum(eta - H, 0.0)
        h = np.where(open_, h, 0.0)
        if inject:
            h = np.where(inl, inf, h)  # inlet depth pinned to INFLOW
        fields.append(h.astype(np.float32).copy())
    return fields, open_


def _grad_abs(bottom, depth, open_):
    """Absolute central-difference gradient components (|gx|, |gy|) of
    eta = bottom + depth, with the cell's own eta substituted for out-of-bounds or
    wall neighbours (the domain border is walled, so np.roll's wrap lands on a wall
    and is masked to self-eta)."""
    eta = (bottom.astype(np.float32) + depth).astype(np.float32)
    etaR = np.where(np.roll(open_, -1, 1), np.roll(eta, -1, 1), eta)
    etaL = np.where(np.roll(open_, 1, 1), np.roll(eta, 1, 1), eta)
    etaU = np.where(np.roll(open_, 1, 0), np.roll(eta, 1, 0), eta)
    etaD = np.where(np.roll(open_, -1, 0), np.roll(eta, -1, 0), eta)
    gx = np.abs((etaR - etaL) * np.float32(0.5)).astype(np.float32)
    gy = np.abs((etaD - etaU) * np.float32(0.5)).astype(np.float32)
    return gx, gy


def _speed(bottom, depth, open_):
    """Flow speed = VEL_SCALE * |grad eta| (central differences, self-eta at
    walls/out-of-bounds)."""
    gx, gy = _grad_abs(bottom, depth, open_)
    return (np.sqrt(gx * gx + gy * gy) * VEL_SCALE).astype(np.float32)


def _mean_momentum(bottom, depth, open_):
    """Spatial-mean momentum (mean over open cells of depth*speed) at one step."""
    mom = (depth * _speed(bottom, depth, open_)).astype(np.float32)
    return float(mom[open_].mean()) if open_.any() else 0.0


def _peak_window(bottom, fields, open_):
    """Peak-momentum step (argmax of spatial-mean momentum) and the candidate window
    (argmax +/-1 plus any step within PEAK_TOL of the maximum)."""
    M = [_mean_momentum(bottom, f, open_) for f in fields]
    mx = max(M)
    tstar = int(np.argmax(M))
    win = {tstar - 1, tstar, tstar + 1}
    win |= {i for i, m in enumerate(M) if m >= (1.0 - PEAK_TOL) * mx}
    return tstar, sorted(i for i in win if 0 <= i < len(M))


def _tertile_bounds(vals):
    """Two ceil-tertile order statistics of a 1-D array (dtype preserved), or
    (None, None) when empty."""
    v = np.sort(vals)
    n = len(v)
    if n == 0:
        return None, None
    return v[int(np.ceil(n / 3)) - 1], v[int(np.ceil(2 * n / 3)) - 1]


def _cost_grid(depth):
    """Per-cell wading cost (paper Table 1, three walking-speed regimes):
    COST_SHALLOW below WADE_LOW, COST_MID between, COST_DEEP at/above WADE_HIGH."""
    return np.where(depth < WADE_LOW, COST_SHALLOW,
                    np.where(depth < WADE_HIGH, COST_MID, COST_DEEP)).astype(np.int64)


def _evac_times(open_, exit, w):
    """Evacuation "time" T[r,c] = min total wading cost from any exit (dist(exit)=0,
    entering a cell costs w[cell]) via Dijkstra over open cells. Returns (T, BIG);
    unreachable open cells (and walls) hold BIG."""
    R, C = open_.shape
    BIG = 1 << 30
    T = np.full((R, C), BIG, dtype=np.int64)
    pq = []
    for r in range(R):
        for c in range(C):
            if exit[r, c] > 0.5 and open_[r, c]:
                T[r, c] = 0
                heapq.heappush(pq, (0, r, c))
    while pq:
        d, r, c = heapq.heappop(pq)
        if d > T[r, c]:
            continue
        for dr, dc in _NEIGHBORS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and open_[nr, nc]:
                nd = d + int(w[nr, nc])  # cost to ENTER the neighbour
                if nd < T[nr, nc]:
                    T[nr, nc] = nd
                    heapq.heappush(pq, (nd, nr, nc))
    return T, BIG


def _evac_bands(open_, exit, w):
    """Evacuation difficulty (1/2/3) via a cost-WEIGHTED shortest path (Dijkstra),
    not a plain BFS hop-count. Reachable times are tertile-classified (3 = hardest);
    unreachable open cells -> 3; if nothing is reachable (no exits) every open
    cell -> 3."""
    T, BIG = _evac_times(open_, exit, w)
    reach = open_ & (T < BIG)
    t1, t2 = _tertile_bounds(T[reach])
    if t1 is None:
        return np.where(open_, 3, 0)
    # Half-open bands, consistent with the FI tertile (below lower boundary -> 1).
    # Evac times are integers with many ties exactly on t1/t2, so this must use the
    # SAME strict-`<` convention as FI; an inclusive `<=` here silently disagrees
    # with the natural reading on every tie cell.
    diff = np.where(T < t1, 1, np.where(T < t2, 2, 3))
    return np.where(open_ & (~reach), 3, diff)  # unreachable open cells: hardest


def _fi_levels(bottom, depth, open_):
    """Beffa FI = depth*max(1, speed), tertile-classified over the open cells into
    levels 1/2/3 (paper sec 3.2.1). Returns (level grid, FI grid)."""
    fi = (depth * np.maximum(np.float32(1.0), _speed(bottom, depth, open_))).astype(np.float32)
    t1, t2 = _tertile_bounds(fi[open_])
    if t1 is None:
        return np.zeros_like(depth, dtype=np.int64), fi
    lvl = np.where(fi < t1, 1, np.where(fi < t2, 2, 3))
    return lvl, fi


def _risk_at(bottom, depth, open_, exit):
    """Full risk grid at one depth field: tertile FI level + 3-band Dijkstra evac
    difficulty, combined as clamp(FI_level + difficulty - 1, 1, 5); walls -> 0."""
    fil, _ = _fi_levels(bottom, depth, open_)
    diff = _evac_bands(open_, exit, _cost_grid(depth))
    return np.where(open_, np.clip(fil + diff - 1, 1, 5), 0)


def _fi_confident(bottom, depth, open_):
    """FI tertile level invariant under +-DEPTH_DRIFT. FI = depth*max(1, speed) is
    monotone in depth and |grad|; bound depth in [depth-D, depth+D] and each |grad|
    component in [|g|-D, |g|+D] (opposite-sign neighbour drift moves a central
    difference by at most D) to get fi_lo/fi_hi. The data-dependent tertile
    boundaries are themselves bounded by the tertiles of fi_lo (smallest) and fi_hi
    (largest). A cell's level is forced iff it agrees at the level-minimising corner
    (small FI, large boundaries) and the level-maximising corner (large FI, small
    boundaries)."""
    D = DEPTH_DRIFT
    gx, gy = _grad_abs(bottom, depth, open_)
    sp_hi = (VEL_SCALE * np.sqrt((gx + D) ** 2 + (gy + D) ** 2)).astype(np.float32)
    sp_lo = (VEL_SCALE * np.sqrt(np.maximum(gx - D, np.float32(0.0)) ** 2
                                 + np.maximum(gy - D, np.float32(0.0)) ** 2)).astype(np.float32)
    fi_hi = ((depth + D) * np.maximum(np.float32(1.0), sp_hi)).astype(np.float32)
    fi_lo = (np.maximum(depth - D, np.float32(0.0))
             * np.maximum(np.float32(1.0), sp_lo)).astype(np.float32)
    t1_lo, t2_lo = _tertile_bounds(fi_lo[open_])  # smallest boundaries
    t1_hi, t2_hi = _tertile_bounds(fi_hi[open_])  # largest boundaries
    if t1_lo is None:
        return np.ones_like(open_, dtype=bool)
    band_min = np.where(fi_lo < t1_hi, 1, np.where(fi_lo < t2_hi, 2, 3))  # small fi, big bounds
    band_max = np.where(fi_hi < t1_lo, 1, np.where(fi_hi < t2_lo, 2, 3))  # big fi, small bounds
    return band_min == band_max


def _difficulty_confident(open_, exit, depth):
    """Evacuation band invariant under +-DEPTH_DRIFT. Drift can flip the wading cost
    of any cell within DEPTH_DRIFT of a cost edge: near WADE_LOW between COST_SHALLOW
    and COST_MID, near WADE_HIGH between COST_MID and COST_DEEP. The cheapest grid
    (ambiguous cells take the lower cost) gives the minimum times AND minimum tertile
    thresholds; the most-expensive grid gives the maxima (both monotone in the cost
    set). A cell's band is forced iff it agrees at the band-minimising corner
    (smallest time, largest thresholds) and the band-maximising corner. Reachability
    is cost-independent (all costs > 0), so unreachable open cells are always 3.

    Additionally, evacuation times are INTEGERS, so many cells tie exactly on a
    tertile boundary t1/t2. How ties are split is genuinely unspecified -- value
    threshold (t<t1 vs t<=t1) vs equal-size rank groups all disagree only on those
    ties -- so a cell whose nominal time equals t1 or t2 is don't-care (otherwise the
    grade would just test which tertile convention the agent happened to pick)."""
    D = DEPTH_DRIFT
    base = _cost_grid(depth)
    amb_low = open_ & (np.abs(depth - WADE_LOW) < D)
    amb_high = open_ & (np.abs(depth - WADE_HIGH) < D)
    cheap = np.where(amb_low, COST_SHALLOW, np.where(amb_high, COST_MID, base)).astype(np.int64)
    exp = np.where(amb_low, COST_MID, np.where(amb_high, COST_DEEP, base)).astype(np.int64)
    T_lo, BIG = _evac_times(open_, exit, cheap)  # min times
    T_hi, _ = _evac_times(open_, exit, exp)      # max times
    reach = open_ & (T_hi < BIG)
    t1_lo, t2_lo = _tertile_bounds(T_lo[reach])  # smallest thresholds (cheapest)
    t1_hi, t2_hi = _tertile_bounds(T_hi[reach])  # largest thresholds  (most expensive)
    if t1_lo is None:  # no exits -> every open cell band 3, drift-invariant
        return np.ones_like(open_, dtype=bool)
    band_min = np.where(T_lo < t1_hi, 1, np.where(T_lo < t2_hi, 2, 3))  # min T, max thr
    band_max = np.where(T_hi < t1_lo, 1, np.where(T_hi < t2_lo, 2, 3))  # max T, min thr
    conf = band_min == band_max
    # Drop integer-tie cells sitting exactly on a nominal tertile boundary: the
    # tertile-split convention (value vs rank, inclusive vs exclusive) is unspecified
    # and only ever disagrees on these ties.
    T_nom, _ = _evac_times(open_, exit, base)
    reach_nom = open_ & (T_nom < BIG)
    t1n, t2n = _tertile_bounds(T_nom[reach_nom])
    if t1n is not None:
        tie = reach_nom & ((T_nom == t1n) | (T_nom == t2n))
        conf = conf & ~tie
    return np.where(open_ & (~reach), True, conf)  # unreachable cells always confident


def _reference(bottom, wall, inlet, exit):
    fields, open_ = _simulate(bottom, wall, inlet)
    tstar, window = _peak_window(bottom, fields, open_)
    depth = fields[tstar]
    base = _risk_at(bottom, depth, open_, exit)
    # An open cell is graded only if its risk is invariant under GPU float drift up
    # to +/-DEPTH_DRIFT: identical across the whole peak-momentum window, AND its FI
    # tertile level and evacuation band both forced under the depth-drift envelope.
    # The rest are "don't care". Walls (expected risk 0) are exact and always graded.
    confident = np.ones_like(open_, dtype=bool)
    for t in window:  # peak-time argmax ambiguity
        confident &= (_risk_at(bottom, fields[t], open_, exit) == base) | ~open_
    confident &= ~open_ | _fi_confident(bottom, depth, open_)
    confident &= ~open_ | _difficulty_confident(open_, exit, depth)
    return base, confident, open_


def _check(bottom, wall, inlet, exit):
    rows, cols = bottom.shape
    got, _ = _detect(bottom, wall, inlet, exit)
    assert len(got) == rows * cols, f"expected {rows*cols} values, got {len(got)}"
    agent = np.array([int(round(v)) for v in got], dtype=np.int64).reshape(rows, cols)
    assert agent.min() >= 0 and agent.max() <= 5, f"risk values out of range [0,5]: {agent.min()}..{agent.max()}"

    ref, confident, _open = _reference(bottom, wall, inlet, exit)
    mism = confident & (agent != ref)
    n = int(mism.sum())
    if n:
        rs, cs = np.nonzero(mism)
        examples = [(int(r), int(c), int(agent[r, c]), int(ref[r, c])) for r, c in zip(rs[:10], cs[:10])]
        raise AssertionError(
            f"{n} confident cell(s) wrong (cell, got, expected): {examples}"
        )


# --------------------------------------------------------------------------- #
# Random scenario generation (bottom elevation, walls/rooms, inlets, exits)
# --------------------------------------------------------------------------- #
def _scenario(R, C, seed, n_internal=None):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:R, 0:C].astype(np.float32)
    H = (0.5 * xx / C + 0.3 * yy / R + 0.4 * rng.random((R, C))).astype(np.float32)
    wall = np.zeros((R, C), np.float32)
    wall[0, :] = wall[-1, :] = wall[:, 0] = wall[:, -1] = 1.0
    k = rng.integers(2, 5) if n_internal is None else n_internal
    for _ in range(int(k)):
        if rng.random() < 0.5:
            r = int(rng.integers(3, R - 3))
            wall[r, 2:C - 2] = 1.0
            wall[r, int(rng.integers(2, C - 2))] = 0.0  # doorway
        else:
            c = int(rng.integers(3, C - 3))
            wall[2:R - 2, c] = 1.0
            wall[int(rng.integers(2, R - 2)), c] = 0.0
    inlet = np.zeros((R, C), np.float32)
    for _ in range(2):
        inlet[int(rng.integers(2, R - 2)), int(rng.integers(2, C - 2))] = 1.0
    inlet *= (1.0 - wall)
    exit = np.zeros((R, C), np.float32)
    exit[1, 1] = 1.0
    exit[R - 2, C - 2] = 1.0
    exit *= (1.0 - wall)
    return H, wall, inlet, exit


# --------------------------------------------------------------------------- #
# 1. Host JNI lib correctness (gates the raw-Vulkan pipeline)
# --------------------------------------------------------------------------- #
def test_host_lib_exists_and_links_vulkan():
    assert os.path.isfile(HOST_SO), "missing /app/libvkflood_host.so"
    hdr = subprocess.run(["readelf", "-h", HOST_SO], capture_output=True, text=True).stdout
    assert "x86-64" in hdr.lower(), "host lib is not x86-64"
    dyn = subprocess.run(["readelf", "-d", HOST_SO], capture_output=True, text=True).stdout
    assert "libvulkan" in dyn, "host lib does not link libvulkan"
    syms = subprocess.run(["readelf", "--dyn-syms", "-W", HOST_SO], capture_output=True, text=True).stdout
    assert "Java_com_example_vkflood_FloodRisk_floodRisk" in syms, (
        "host lib does not export the required JNI symbol"
    )


def test_host_lib_uses_vulkan_at_runtime():
    _, proc = _detect(*_scenario(24, 24, 1), extra_env={"VK_LOADER_DEBUG": "driver"})
    blob = (proc.stderr + proc.stdout).lower()
    assert ("icd" in blob) or ("lvp" in blob) or ("llvmpipe" in blob), (
        "no Vulkan driver loaded at runtime (compute likely not done on Vulkan)"
    )


def test_uses_raw_vulkan_not_kompute():
    # The compute must be hand-written against the RAW Vulkan API. The Kompute
    # framework (which hides exactly the GPU engineering this task is about) is NOT
    # accepted. Checked on both the host .so and the AAR's arm64 lib.
    host_nm = subprocess.run(["nm", "-CD", HOST_SO], capture_output=True, text=True).stdout
    host_str = subprocess.run(["strings", HOST_SO], capture_output=True, text=True).stdout
    low = host_str.lower()
    assert "kp::" not in host_nm and "kompute" not in low, (
        "host lib uses the Kompute framework; raw Vulkan is required"
    )
    assert ("vkCreateInstance" in host_nm) or ("vkCreateInstance" in host_str), (
        "host lib does not call the raw Vulkan API (no vkCreateInstance); "
        "the compute must be written directly against Vulkan"
    )
    aar = _find_aar()
    with tempfile.TemporaryDirectory() as d:
        for rel in _aar_arm64_libs(aar):
            subprocess.run(["unzip", "-o", aar, rel, "-d", d],
                           capture_output=True, text=True, check=True)
            so = os.path.join(d, rel)
            s = subprocess.run(["strings", so], capture_output=True, text=True).stdout.lower()
            assert "kompute" not in s, (
                f"AAR arm64 lib {rel} uses Kompute; raw Vulkan is required"
            )


# --------------------------------------------------------------------------- #
# 2. Pipeline correctness over random scenarios
# --------------------------------------------------------------------------- #
def test_basic_scenario():
    _check(*_scenario(36, 44, 10))


def test_dims_not_multiple_of_workgroup():
    _check(*_scenario(30, 37, 11))
    _check(*_scenario(50, 50, 12))


def test_large_domain():
    _check(*_scenario(96, 96, 13))


def test_open_hall_no_internal_walls():
    _check(*_scenario(40, 52, 14, n_internal=0))


def test_dense_rooms():
    _check(*_scenario(48, 60, 15, n_internal=6))


def test_multiple_seeds():
    for s in (20, 21, 22):
        _check(*_scenario(34, 41, s))


def test_no_exit_all_unreachable():
    # No exit cells -> no BFS sources -> n == 0 reachable open cells -> the spec's
    # "difficulty 3 everywhere" branch. Risk then = clamp(FI_level + 3 - 1, 1, 5).
    bottom, wall, inlet, exit = _scenario(34, 41, 23)
    _check(bottom, wall, inlet, np.zeros_like(exit))


# --------------------------------------------------------------------------- #
# 3. AAR packages a real AArch64 native lib that uses Vulkan via JNI
# --------------------------------------------------------------------------- #
def _find_aar():
    preferred = os.path.join(APP, "vkflood.aar")
    if os.path.isfile(preferred):
        return preferred
    hits = glob.glob(os.path.join(APP, "**", "*.aar"), recursive=True)
    assert hits, "no .aar found anywhere under /app"
    return hits[0]


def _aar_arm64_libs(aar):
    listing = subprocess.run(["unzip", "-l", aar], capture_output=True, text=True).stdout
    libs = []
    for line in listing.splitlines():
        for tok in line.split():
            if tok.startswith("jni/arm64-v8a/") and tok.endswith(".so"):
                libs.append(tok)
    return libs


def test_aar_has_arm64_vulkan_jni_lib():
    aar = _find_aar()
    libs = _aar_arm64_libs(aar)
    assert libs, "AAR contains no arm64-v8a native library (jni/arm64-v8a/*.so)"
    with tempfile.TemporaryDirectory() as d:
        found = None
        reasons = []
        for rel in libs:
            subprocess.run(["unzip", "-o", aar, rel, "-d", d],
                           capture_output=True, text=True, check=True)
            so = os.path.join(d, rel)
            hdr = subprocess.run(["readelf", "-h", so], capture_output=True, text=True).stdout
            if "AArch64" not in hdr or "ELF64" not in hdr:
                reasons.append(f"{rel}: not AArch64/ELF64")
                continue
            # Raw Vulkan links libvulkan directly, so a NEEDED-libvulkan entry is
            # required (the dlopen exception that applied to Kompute no longer does).
            dyn = subprocess.run(["readelf", "-d", so], capture_output=True, text=True).stdout
            if "libvulkan" not in dyn:
                reasons.append(f"{rel}: does not link libvulkan")
                continue
            syms = subprocess.run(["readelf", "--dyn-syms", "-W", so],
                                  capture_output=True, text=True).stdout
            if "Java_" not in syms and "JNI_OnLoad" not in syms:
                reasons.append(f"{rel}: no JNI entry point")
                continue
            found = rel
            break
        assert found, f"no arm64-v8a Vulkan JNI .so found in AAR. Checked: {reasons}"


# --------------------------------------------------------------------------- #
# 4. SPIR-V artifact
# --------------------------------------------------------------------------- #
def test_spirv_artifact_is_valid():
    assert os.path.isfile(SPV), "missing /app/risk.comp.spv"
    with open(SPV, "rb") as f:
        word = struct.unpack("<I", f.read(4))[0]
    assert word == 0x07230203, f"not a SPIR-V module (magic={word:#x})"
