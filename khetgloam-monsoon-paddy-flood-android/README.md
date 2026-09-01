# kompute-flood-risk-android

## Description

The agent must implement a multi-stage **underground-space flood-risk pipeline**
with **raw Vulkan compute (no Kompute)** and ship it as a reusable **Android
library (AAR)**, built from scratch — Gradle library module, host build, JNI
bridge, CMake wired for Vulkan on host x86-64 and Android arm64, the raw-Vulkan
compute orchestration (`flood_risk.cpp`: instance/device/descriptors/pipeline/
command buffers + an **iterated, ping-pong, storm-pulse dispatch loop**), and the
GLSL compute shader (`risk.comp`).

The library's native method
`floodRisk(bottom, wall, inlet, exit, rows, cols)` takes four row-major grids
describing an underground space (bottom elevation, wall/room mask, stormwater
inlet mask, exit mask) and returns a dense `rows*cols` grid of per-cell flood-risk
levels (1–5; walls report 0), via this pipeline:

1. **Hydraulic solve with a storm pulse (IMPLICIT time-stepping PDE).** Inlet cells
   are **fixed at the inflow depth** (Dirichlet) for the first `N_INJECT` steps, then
   **released** to ordinary open cells. Each step advances the water-surface
   elevation `eta = bottom + depth` by an **implicit (backward-Euler)** diffusion —
   i.e. it **solves the linear system** `(I − ALPHA·L) ηⁿ⁺¹ = ηⁿ` (`L` = no-flux
   graph Laplacian over open cells) by **Jacobi iteration to convergence** on the
   GPU. The converged field is **unique** (independent of the iterative method/count),
   so the result is well-defined. Run for `N_STEPS`, **keeping every step's depth
   field**.
2. **Peak-momentum time (paper §4.3).** At each step compute the spatial-mean
   momentum (mean over open cells of `depth · speed`, `speed = VEL_SCALE · |∇(bottom
   +depth)|`). The **argmax step** is the risk-assessment time; the pulse makes the
   mean momentum rise then decay, giving an interior peak. FI and evacuation below
   use the depth field **at that peak step** — not the final field.
3. **Flood intensity (Beffa), tertile-classified.** `FI = depth · max(1, speed)`
   (i.e. `FI = h` when `v<1`, else `v·h`), then **tertile-classified** over the open
   cells into levels 1/2/3 (paper §3.2.1 — nodes sorted by FI and split into
   tertiles; no fixed magic thresholds).
4. **Evacuation difficulty (weighted shortest path + tertiles).** Evacuation *time*
   to the nearest exit via a depth-weighted shortest path (multi-source Dijkstra):
   entering a cell costs `COST_SHALLOW`/`COST_MID`/`COST_DEEP` for shallow/mid/deep
   water — **three** walking-speed regimes split at `WADE_LOW`/`WADE_HIGH` (paper
   Table 1: 0.7 / 0.3 m/s, ratio ≈ 7/3), walls block. Times are tertile-classified
   1/2/3 (unreachable open cells are 3). This is *not* a plain BFS hop-count.
5. **Risk matrix.** `risk = clamp(FI_level + difficulty − 1, 1, 5)` (this additive
   clamp **is** the paper's Fig. 5 consequence–probability matrix).

It tests RAW Vulkan compute API usage from scratch (instance/physical-device/queue,
descriptor set layouts, compute pipeline, command buffers, fences, host-visible
buffer memory) driving a **nested implicit solver** — an outer time-step loop, and
an inner **Jacobi iteration** that ping-pongs `eta` buffers and must run to
convergence (a per-sweep `inject` push constant; the RHS `= ηⁿ` rebuilt each step) —
none of which a high-level wrapper hides — plus the non-multiple-of-16 bounds guard,
a **temporal argmax** over per-step spatial-mean momentum, **two** global
ceil-tertile classifications (FI and evacuation time), a three-regime depth-weighted
shortest path (Dijkstra), and the Android NDK/Gradle/JNI offline-AAR packaging path.
A naive CPU loop won't satisfy the "runs on Vulkan" check, and each stage is easy to
get subtly wrong (no-flux walls, the storm-pulse inlet release, finding the
peak-momentum step, central-difference speed with self-eta at boundaries, the `v=1`
FI regime switch, tertile-classifying FI rather than fixed thresholds, three-band
wading costs vs a plain BFS, ceil-tertile ties). Correctness is verified by driving
the agent's **host** raw-Vulkan `.so` across a JNI harness on **lavapipe** (software
Vulkan, no emulator) against a numpy reference over random scenarios. GLSL permits
floating-point contraction (fma) and branch-vs-`max` codegen, so the GPU's depth
field drifts from numpy's by ~1e-4 over the diffusion; the reference absorbs this
with a **drift-invariance envelope** (bound `DEPTH_DRIFT`): an open cell is graded
only if its risk is invariant under that drift — identical across the whole
peak-momentum window, **and** its FI tertile level and evacuation band both forced
anywhere in the `±DEPTH_DRIFT` box (including the FI-percentile and wading-cost
boundary shifts). The GPU and reference therefore agree on every graded cell with no
hand-tuned per-edge epsilon.

This task is derived from the flood-risk methodology of Han, Shin, Eum & Song,
*"Inundation Risk Assessment of Underground Space Using Consequence-Probability
Matrix"*, Appl. Sci. 2019, 9, 1196 (flood intensity §3.2.1 / Fig. 3, evacuation
difficulty §3.2.2, and the flood-risk matrix §3.2.3 / Fig. 5).

## Required artifacts (under `/app`)

- `libvkflood_host.so` — host x86-64 raw-Vulkan JNI lib exporting
  `Java_com_example_vkflood_FloodRisk_floodRisk(float[] bottom, float[] wall,
  float[] inlet, float[] exit, int rows, int cols)`.
- `risk.comp.spv` — the compiled SPIR-V compute shader.
- `vkflood.aar` — Android library packaging the arm64-v8a raw-Vulkan JNI lib.

## Completion Rates

> Calibration target: Avocado **or** Opus must pass at least once **and** fail at
> least once out of 5 runs.
>
> ℹ️ The task was rebuilt to **raw Vulkan** (no Kompute) with the full paper
> pipeline — storm-pulse hydraulics, peak-momentum time (§4.3), tertile FI (§3.2.1),
> a three-band wading cost (Table 1) — and a drift-invariance envelope (peak-momentum
> window + FI tertile + evacuation band). The **oracle is verified** (below); the
> per-model rates are **pending** an `Opus 4.6` / `Avocado -k5` calibration run.

Rates are for the full paper pipeline (storm-pulse eta diffusion + peak-momentum time +
tertile Beffa FI + three-band depth-weighted Dijkstra evacuation + risk matrix).

| Model | Pass rate |
|-------|-----------|
| Oracle | **3/3** (verified locally on lavapipe, non-flaky; all 12 checks) |
| Opus 4.6 | **2/5** (verified locally; 2 trials pass all 12 checks, 3 fail scenario checks) |
| Avocado | **0/5** (verified locally; all 5 structural/engineering checks pass every trial, but the scenario-correctness checks fail with large multi-cell errors) |

## Model Analysis

> ⚠️ **Pending re-measurement.** This pipeline was hardened to full paper fidelity
> (storm pulse + peak-momentum time + tertile FI + three-band cost), so per-model
> pass/fail counts and the dominant-failure breakdown must be filled in from a fresh
> cloud run. The list below is the **expected** set of genuine, drift-independent
> failure modes the re-run should surface (the drift-invariance envelope excuses the
> earlier numerics-only single-cell flips — e.g. the `(31,35)` case from the previous
> fixed-threshold pipeline — that motivated the envelope in the first place).

**Oracle — 3/3.** The reference solution passes all 12 checks on 3/3 `-k3` runs
(verified locally on lavapipe), confirming the raw-Vulkan pipeline is solvable and
reproducible (no flakiness; the GPU output matches the numpy reference on the
confident cells across every scenario).

**Avocado — 0/5 (verified locally).** In every one of the 5 trials Avocado cleared
the **engineering** bar — all 5 structural checks pass: it wrote working raw Vulkan
(host `.so` + arm64 AAR build, links libvulkan, runs on lavapipe, **no Kompute**,
valid SPIR-V). It failed every trial on **algorithm correctness**: the scenario
checks (`basic`, non-multiple-of-16, large, open-hall, dense, multi-seed) fail 5/5
and `no-exit` 4/5, each with **71–112 confident cells wrong** (e.g. `got 4, expected
5`). These are large, multi-cell, envelope-proof errors — a genuine implementation
gap in the multi-stage pipeline (peak-momentum step, tertile FI, three-band evac),
not numerical drift or an unspecified convention. So the task's difficulty is fair
and real: the raw-Vulkan engineering is achievable, but getting the full algorithm
right is the discriminator.

**Expected genuine failure modes (preserved by the envelope).** These are structural
bugs that produce *large, multi-cell* errors far from any threshold, so they survive
the drift-invariance mask and remain discriminating:

- **Storm-pulse inlet handling** — failing to release inlets after `N_INJECT` (or
  mishandling the Dirichlet pin during injection) gives the wrong depth field for the
  whole rest of the run.
- **Peak-momentum step** — using the final (or a hardcoded) step instead of the
  argmax of per-step spatial-mean momentum picks the wrong fields for every cell.
- **Non-multiple-of-16 shader bounds guard** — the unaligned 36×44 / 30×37 grids
  expose a missing or wrong workgroup bounds check, corrupting whole edge rows/cols.
- **Central-difference speed self-eta at walls/out-of-bounds** — substituting a wall
  neighbour's eta instead of the cell's own shifts the gradient (and FI) on whole
  wall-adjacent bands.
- **Tertile FI vs fixed thresholds** — using fixed FI cutoffs instead of per-scenario
  tertiles lands most cells in the wrong consequence level.
- **Push-constant encoding** — bit-casting `uint` rows/cols (or the `inject` flag)
  through the `float` push vector mis-decodes and breaks the grid.
- **Plain BFS / two-band cost instead of three-band Dijkstra** — diverges wherever
  evacuation routes cross flooded cells (a structural, not near-threshold, error).

**Why these are reasoning gaps, not task-setup issues.** They are drift-independent:
each changes many cells far from any FI/tertile edge, so the envelope cannot mask them
and the float64-vs-float32 cross-check (below) confirms they are not reference
artifacts.

**Numerical robustness of the reference.** With the drift-invariance envelope
(`DEPTH_DRIFT = 1e-2`, ≥10× the worst ~1e-3 depth divergence observed and ~100× the
~1e-4 typical), the float32 reference has **0 unfair flips** on the graded cells
(~14.7k of ~21.7k open cells, 68%, across 9 scenarios + the no-exit case) under
(a) a float64 re-run of the whole pipeline (diffusion + peak-momentum argmax) and
(b) ±3e-3 random depth perturbations on the peak-step field — i.e. no graded cell
changes risk anywhere in the design drift envelope, while risk still spans 1–5. The
C++ oracle's host-side stages (peak-momentum, tertile FI, three-band Dijkstra) were
cross-checked to produce a bit-identical grid to the numpy reference on shared
diffusion fields.

## Anti-Cheating Analysis

- **Hardcoded outputs:** scenarios (bottom/walls/inlets/exits) are random (numpy
  `default_rng`) and the full pipeline is recomputed per scenario; the risk grid
  cannot be hardcoded.
- **Overfitting to visible tests:** tests are mounted at verify time and absent
  from the agent's container; multiple shapes/layouts are graded (odd dims, large
  multi-workgroup, open hall, dense rooms, multiple seeds, and a no-exit case that
  exercises the all-unreachable "difficulty 3 everywhere" branch).
- **Modifying test files:** the agent only sees `environment/`; the verifier
  supplies `test.sh` + the pytest suite.
- **Bypassing the intended solution path:** the host lib must export the JNI symbol,
  link `libvulkan`, and load a Vulkan driver at runtime (`VK_LOADER_DEBUG`), so a
  CPU-only shortcut fails; the AAR must contain a real AArch64 Vulkan JNI `.so`; a
  valid SPIR-V artifact must be produced.
- **Must use raw Vulkan (not Kompute):** `test_uses_raw_vulkan_not_kompute` asserts
  the host `.so` calls the raw Vulkan API (`vkCreateInstance`) and that neither the
  host `.so` nor the AAR's arm64 `.so` contains Kompute (no `kp::` symbols / "kompute"
  strings), rejecting a high-level wrapper that would hide the GPU engineering.
- **Implicit solve can't be skipped or under-converged:** FI derives from the
  storm-pulse depth field produced by the implicit (backward-Euler) diffusion — each
  step must solve `(I − ALPHA·L) η = ηⁿ` to convergence (no-flux walls, inlet
  inject/release pulse, non-multiple-of-16 bounds guard). An explicit single-pass
  stencil, an under-converged solve, or a CPU shortcut diverges from the reference on
  the confident cells. (Because the *converged* solution is unique, any convergent
  iterative method — Jacobi/Gauss–Seidel/CG — is accepted; only *failing to
  converge* is penalised.)
- **Peak-momentum time can't be guessed:** the risk-assessment step is the argmax of
  per-step spatial-mean momentum, which varies by scenario (e.g. step 3 for a large
  open domain vs step 14 for walled grids), so hardcoding "use the last/first/inject
  step" diverges; the agent must run the full pulse and reduce momentum over time.
- **FI is tertile-classified, not fixed thresholds:** FI levels are data-dependent
  tertiles of the per-scenario FI distribution, so a solution using fixed magic
  cutoffs lands in the wrong band on most scenarios.
- **Evacuation is three-band weighted, not hop-count:** difficulty requires a
  depth-weighted shortest path (Dijkstra) with three wading-cost regimes (shallow/
  mid/deep); a plain BFS hop-count, or a two-band cost, diverges from the reference
  wherever evacuation routes cross flooded cells.
