Write a standalone R script to /app/schwarzschild_orbit.R that simulates a massive test particle geodesic around a Schwarzschild black hole. Use base R only, no external packages.

Expose a globally callable function run_simulation(config) where config is a named list with keys:

- M black hole mass
- d_tau proper time step size
- tau_max maximum proper time
- initial_position numeric vector of four spacetime coordinates t x y z in Cartesian Kerr-Schild
- initial_velocity numeric vector of four-velocity components in same coordinates

Assume mostly plus signature and natural units. The interface basis is strictly pinned to Cartesian Kerr-Schild coordinates t x y z.

Objective is to evaluate continuous geodesic motion by integrating with a bespoke high order adaptive integrator you write entirely in base R.

You must derive the exact Schwarzschild metric in these regular coordinates and its Christoffels. Then integrate the exact timelike geodesic equation.

You must identify and track the fundamental kinematic and conserved quantities in this setup. There are three: the local velocity norm that must stay minus one, the global conserved energy from stationarity, and the global total angular momentum magnitude squared from spherical symmetry. Evaluate each continuously at every substep and track raw unmodified maximum absolute drift from initial.

Velocity drift tolerance is 1e-10 absolute. Energy tolerance is 1e-6 absolute. Angular momentum magnitude squared tolerance is 1e-8 absolute.

Integration must stop early if radial coordinate exceeds 1000 times M as escaped, or falls below 2M as captured, or tau exceeds tau_max as timeout.

Do not cap or re-project state vectors to fake invariants. Harness independently recomputes invariants from your returned final position and final velocity and will catch fake self report.

Return named list with final_position length 4, final_velocity length 4, termination_reason escaped captured timeout, max_velocity_drift, max_energy_drift, max_angular_momentum_drift.

Write to /app/schwarzschild_orbit.R
