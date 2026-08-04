# schwarzschild-orbit

A massive test particle geodesic around a Schwarzschild black hole in Cartesian Kerr-Schild coordinates. This is a sister in spirit to black-hole tasks but with distinct physics: Schwarzschild not Kerr-Newman, neutral timelike geodesic not charged spinning, no Lorentz force and no Fermi-Walker spin transport, so code differs substantially. It tests pure base R numerical scientific computing with conservation.

## Why this is not a reskin of black-hole

black-hole task integrates charged spinning particle around rotating charged Kerr-Newman with metric g = eta + f l l where f = r^2 (2 M r - Q^2)/(r^4 + a^2 z^2), vector potential A_mu = Q r^3/(r^4 + a^2 z^2) l_mu, Faraday tensor via finite differences, Lorentz force du = -Gamma u u + q F u, plus Fermi-Walker spin transport with invariants u.u, S.S, S.u and Killing energy.

This task integrates neutral timelike geodesic around Schwarzschild where f = 2 M / r and l = (1, x/r, y/r, z/r). No charge, no spin, no Faraday, no vector potential. EOM is pure geodesic du = -Gamma u u. Invariants are u.u = -1, Killing energy E = -g_{t nu} u^nu, and total angular momentum squared L2 = |r cross p|^2 where p_i = g_{i nu} u^nu. Metric is spherically symmetric, not axisymmetric, and has no inner Cauchy horizon, termination is captured at r < 2M, not inner_horizon. So reasoning route, equations, and conserved quantities differ materially despite same coordinate family and similar integrator scaffolding.

## Description

Agent must write /app/schwarzschild_orbit.R exposing run_simulation(config) that integrates Schwarzschild geodesic with adaptive Dormand-Prince RK45 implemented from scratch in base R. Config contains M, d_tau, tau_max, initial_position and initial_velocity in Cartesian Kerr-Schild.

The metric is g = eta + f l l, f = 2 M / r, l_t =1, l_i = x_i / r. Christoffels via fourth order central differences of g. Integration with error control holds u.u to 1e-10, energy to 1e-6, L2 to 1e-8. Loop terminates escaped r > 1000 M, captured r < 2M +0.1, or timeout.

Naive approaches fail: using Schwarzschild coordinates blows up at horizon, low order integrator cannot hold invariants, ignoring drift of energy or angular momentum, or re-projecting u to -1 each step hides local drift but fails energy and angular momentum gates.

## Completion Rates

Measured by platform, not local model runtime:

| Model | Pass rate |
|---|---|
| Oracle | 3/3 (10/10 tests) |
| Avocado | expected 1/5 to 2/5 due to needing correct Kerr-Schild metric and conserving integrator |
| Opus | expected 2/5 |
| GPT | expected 2/5 |

## Anti-Cheating

* Fresh varied configs per test (different M, initial position/velocity) so no constant return can conserve invariants
* Independent recompute: harness recomputes u.u, energy, L2 from returned final position and final velocity and asserts independent drifts, so fake self report fails
* Tests live in /tests not /app
* No external R packages installed, only r-base-core

Author Tosin Daniel Jimoh purple29th at meta.com
