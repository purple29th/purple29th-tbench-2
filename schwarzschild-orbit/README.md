# schwarzschild-orbit

A massive test particle geodesic around a Schwarzschild black hole in Cartesian Kerr-Schild coordinates. Pure base R numerical scientific computing with conservation.

## Description

Agent must write /app/schwarzschild_orbit.R exposing run_simulation(config) that integrates Schwarzschild geodesic with adaptive Dormand-Prince RK45 implemented from scratch in base R. Config contains M, d_tau, tau_max, initial_position and initial_velocity in Cartesian Kerr-Schild.

The metric is g = eta + f l l, f = 2 M / r, l_t =1, l_i = x_i / r, r = sqrt(x^2 + y^2 + z^2). Christoffels via fourth order central differences of g. Integration with error control holds u.u = -1 to 1e-10, Killing energy E = -g_{t nu} u^nu to 1e-6, and total angular momentum squared L2 = |r cross p|^2 where p_i = g_{i nu} u^nu to 1e-8. Loop terminates escaped r > 1000 M, captured r < 2M + 0.1, or timeout.

Naive approaches fail: using Schwarzschild coordinates blows up at horizon, low order integrator cannot hold invariants, ignoring drift of energy or angular momentum, or re-projecting u to -1 each step hides local drift but fails energy and angular momentum gates. The contract returns final velocity, so harness independently recomputes invariants from final state and catches fake drift.

## Completion Rates

Measured by platform, not local model runtime:

| Model | Pass rate |
|---|---|
| Oracle | 3/3 (8 tests) |
| Avocado | expected 1/5 to 2/5 due to needing correct Kerr-Schild metric and conserving integrator |
| Opus | expected 2/5 |
| GPT | expected 2/5 |

## Anti-Cheating

* Fresh varied configs per test (different M, initial position/velocity) so no constant return can conserve invariants
* Independent recompute: harness recomputes u.u, energy, L2 from returned final position and final velocity and asserts independent drifts, so fake self report fails
* Tests live in /tests not /app
* No external R packages installed, only r-base-core

Author Tosin Daniel Jimoh purple29th at meta.com
