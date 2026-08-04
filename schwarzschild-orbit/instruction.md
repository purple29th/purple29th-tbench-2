Write a standalone R script to /app/schwarzschild_orbit.R that simulates a massive test particle geodesic around a Schwarzschild black hole. Use base R only, no external packages.

Expose a globally callable function run_simulation(config) where config is a named list with keys:

- M black hole mass
- d_tau proper time step size
- tau_max maximum proper time
- initial_position numeric vector of four spacetime coordinates t x y z in Cartesian Kerr-Schild
- initial_velocity numeric vector of four-velocity components in same coordinates

Assume mostly plus metric signature minus plus plus plus and natural units G=c=1.

You must derive the Schwarzschild metric in Cartesian Kerr-Schild form. The metric can be written as g equals eta plus f times l tensor l where f equals 2 M divided by r and l is null vector with l_t equals 1 and spatial part equals x over r, y over r, z over r, with r equals sqrt of x squared plus y squared plus z squared. Then compute Christoffel symbols from the metric via fourth order central finite differences. Then integrate the geodesic equation du mu over d tau equals minus Gamma mu alpha beta u alpha u beta.

Use a bespoke high order adaptive integrator you write yourself, for example Dormand-Prince RK45 with error control. Do not use external ODE packages.

You must track invariants at every substep and report max absolute drift from initial:

- velocity norm u dot u equals g_uv u^u u^v should stay -1 for timelike. Tolerance for passing is 1e-10 absolute.

- Killing energy from time translation symmetry E equals minus g_{t nu} u^nu. This is conserved along true geodesic. Tolerance 1e-6.

- Total angular momentum magnitude squared L2. Compute spatial momentum p_i equals g_{i nu} u^nu, then L equals r cross p, L2 equals dot of L with itself. This is conserved for Schwarzschild due to spherical symmetry. Tolerance 1e-8 for L2 drift.

The loop must terminate early if r exceeds 1000 times M as escaped, or r falls below 2M plus small epsilon 0.1 as captured, or tau exceeds tau_max as timeout. Return reason as string escaped, captured, or timeout.

Do not cap, re-project, or falsify state vectors or drift values to hide error. The harness independently recomputes u dot u and energy and angular momentum from your returned final position and final velocity and will fail if your self reported drifts are low but returned state is not on shell or does not conserve.

When run_simulation is called, evaluate up to tau_max and return a named list with keys final_position numeric length 4, final_velocity length 4, termination_reason string, max_velocity_drift, max_energy_drift, max_angular_momentum_drift.

Write the R script to /app/schwarzschild_orbit.R
