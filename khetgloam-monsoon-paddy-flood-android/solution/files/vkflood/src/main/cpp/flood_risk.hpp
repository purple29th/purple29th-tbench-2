#pragma once
#include <cstdint>
#include <vector>

// Per-cell flood-risk classification over an underground-space scenario, via GPU
// compute (raw Vulkan) for the hydraulic time-stepping. Inputs are four row-major
// grids of identical shape (rows x cols):
//   bottom   bottom elevation H (m)
//   wall     1.0 for wall/obstacle cells, 0.0 for open cells (rooms layout)
//   inlet    1.0 for stormwater inflow cells
//   exit     1.0 for exit cells
//
// Pipeline:
//   1. Hydraulic solve (GPU, raw Vulkan) with a storm pulse: inlet cells are FIXED at
//      INFLOW depth (Dirichlet) for the first N_INJECT steps, then RELEASED to
//      ordinary open cells. Each step advances eta = bottom + depth by an IMPLICIT
//      (backward-Euler) diffusion: solve (I - ALPHA*L) eta^{n+1} = eta^n (L = no-flux
//      graph Laplacian over open cells) by N_JACOBI Jacobi sweeps (the converged
//      field is unique). Run for N_STEPS, keeping every step's depth field.
//   2. Peak-momentum time (paper sec 4.3): at each step compute the spatial-mean
//      momentum (mean over open cells of depth*speed); the argmax step is the
//      risk-assessment time. FI / evacuation use the depth field at that step.
//   3. Flood intensity (Beffa): FI = depth * max(1, speed), speed = VEL_SCALE *
//      |grad(bottom+depth)| (central differences, self-eta at OOB/wall neighbours),
//      then tertile-classified over the open cells into levels 1/2/3.
//   4. Evacuation difficulty: depth-WEIGHTED shortest path (Dijkstra) over open
//      cells to the nearest exit -- entering a cell costs COST_SHALLOW / COST_MID /
//      COST_DEEP for shallow / mid / deep water (three regimes split at WADE_LOW /
//      WADE_HIGH, paper Table 1); evacuation times tertile-classified 1/2/3
//      (unreachable open cells = 3).
//   5. Risk = clamp(FI_level + difficulty - 1, 1, 5); walls report 0.
//
// Returns a dense row-major grid of length rows*cols (risk per cell, 0 on walls).
std::vector<float> floodRisk(const float* bottom, const float* wall,
                             const float* inlet, const float* exit,
                             uint32_t rows, uint32_t cols);

// Pipeline constants (must match the reference verifier).
static constexpr int FR_N_STEPS = 20;
static constexpr int FR_N_INJECT = 8;
static constexpr int FR_N_JACOBI = 40;   // Jacobi sweeps per implicit step (converged)
static constexpr float FR_ALPHA = 0.22f;
static constexpr float FR_INFLOW = 3.0f;
static constexpr float FR_VEL_SCALE = 10.0f;
// Evacuation wading cost (paper Table 1): three walking-speed regimes.
static constexpr float FR_WADE_LOW = 1.2f;
static constexpr float FR_WADE_HIGH = 1.8f;
static constexpr int FR_COST_SHALLOW = 3;
static constexpr int FR_COST_MID = 5;
static constexpr int FR_COST_DEEP = 7;
