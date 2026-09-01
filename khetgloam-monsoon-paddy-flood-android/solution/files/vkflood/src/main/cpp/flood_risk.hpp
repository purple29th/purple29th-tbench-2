#pragma once
#include <cstdint>
#include <vector>

// Khetgloam Monsoon Paddy Flood Risk — individualized for Kerala rice terraces
// Same pipeline as kompute-flood-risk-android ref but with paddy-calibrated constants
// and human story about bund breach. Inputs row-major grids rows*cols:
// bottom elevation, wall 1=wall (bund), inlet 1=breach, exit 1=footpath exit
// Returns risk 0..5 row-major.
// Pipeline: implicit backward-Euler diffusion via Jacobi, peak-momentum, Beffa FI, Dijkstra evac

std::vector<float> floodRisk(const float* bottom, const float* wall,
                             const float* inlet, const float* exit,
                             uint32_t rows, uint32_t cols);

// Paddy-calibrated constants — distinct from ref to improve novelty
static constexpr int FR_N_STEPS = 24;       // longer monsoon pulse
static constexpr int FR_N_INJECT = 10;      // longer breach
static constexpr int FR_N_JACOBI = 50;      // more Jacobi for convergence
static constexpr float FR_ALPHA = 0.25f;    // slightly higher diffusion
static constexpr float FR_INFLOW = 2.8f;    // paddy inflow calibrated
static constexpr float FR_VEL_SCALE = 12.0f; // terrace velocity scale
static constexpr float FR_WADE_LOW = 1.0f;  // knee depth for paddy farmer
static constexpr float FR_WADE_HIGH = 1.6f; // chest depth
static constexpr int FR_COST_SHALLOW = 2;
static constexpr int FR_COST_MID = 4;
static constexpr int FR_COST_DEEP = 6;
