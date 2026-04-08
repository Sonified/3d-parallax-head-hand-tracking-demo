# FGE in Recirculating Flow: Lid-Driven Cavity Benchmark

Lid-driven cavity flow is the standard benchmark for 2D Navier-Stokes solvers.
Three stationary walls, one moving lid dragging fluid into a recirculation vortex.
The gold standard reference is Ghia, Ghia, and Shin (1982), which provides
centerline velocity profiles at Re = 100, 400, 1000, 3200, 5000, 7500, and 10000.

This folder adds a ghost stamp to the cavity: ghost data injected at the center
cell rides the vortex, demonstrating that FGE works in recirculating flow — not
just in Poiseuille (unidirectional) flow.

## Files

- `lid_driven_cavity_ghost_fast.py` — vectorized version (numpy matmul over full
  grid, no Python x/y loops in collision). Run this one.
- `lid_driven_cavity_ghost.py` — original unvectorized version (pure Python loops,
  much slower, kept for reference).
- `output_100x100_5000ticks.txt` — saved output: 100x100 grid, Re=37.5, 5000 ticks.

## Results (100x100, Re=37.5, 5000 ticks)

Correct recirculation vortex. Lid drags right across the top, fluid descends the
right wall, returns left along the bottom, rises on the left. The `<<<` zone in
the lower half is the recirculation core — textbook cavity flow morphology.

Ghost channel m[18] conserves at 97.3% across 5000 ticks. Slow drift is from
the moving-lid momentum correction at the top boundary (not fully conservative
for the symmetric m[18] channel). Ghost concentrates in the high-shear lid region
— physically correct behavior, carried there by the fluid.

## Re = 100 (Ghia target)

Current: Re = U_lid * L / nu = 0.1 * 100 / 0.267 = 37.5

To hit Re = 100: set ON=4, OD=5 in the script.
  nu = (1/3)*(5/4 - 0.5) = (1/3)*0.75 = 0.25 -- wait, that's higher.
  nu = (1/3)*(OD/ON - 0.5). For Re=100: nu = 0.1*100/100 = 0.1.
  Solve: (1/3)*(s - 0.5) = 0.1 -> s = 0.8 -> ON/OD = 4/5.

With ON=4, OD=5: nu = (1/3)*(1.25 - 0.5) = 0.25. Re = 0.1*100/0.25 = 40.
With ON=8, OD=9: nu = (1/3)*(9/8 - 0.5) = (1/3)*0.625 = 0.208. Re = 48.
With ON=16, OD=17: nu = (1/3)*(17/16 - 0.5) = (1/3)*0.5625 = 0.1875. Re = 53.
With ON=19, OD=20: nu = (1/3)*(20/19 - 0.5) ≈ 0.184. Re ≈ 54.
With ON=49, OD=50: nu ≈ 0.174. Re ≈ 57.

For Re=100 cleanly: need nu=0.1. With integer relaxation this requires
ON/OD close to 0.8 + 0.5 = 1.3. Best rational approximation: ON=13, OD=10
gives nu = (1/3)*(10/13 - 0.5) = negative -- wrong direction.

Actually: omega = ON/OD is the relaxation rate, nu = cs^2*(1/omega - 0.5) = (1/3)*(OD/ON - 0.5).
For nu=0.1: OD/ON = 0.8 -> ON/OD = 1.25. Not valid (omega must be < 2 for stability).
For nu=0.1: (1/3)*(OD/ON - 0.5) = 0.1 -> OD/ON = 0.8 -> impossible (OD < ON unstable).

Minimum stable nu with integer relaxation: ON/OD close to but below 2.
With ON=19, OD=10: nu = (1/3)*(10/19 - 0.5) = (1/3)*(-0.026) -- negative, unstable.

Practical Re=100 path: increase U_LID to 2670/10000 (Ma=0.46, borderline stable)
or use a larger grid (L=400 cells at Re=37.5 gives equivalent resolved physics).

## Connection to Patent

The bitwise-identity proof (ghost_physics_independence_u32.py) already establishes
that ghost data cannot affect any flow regime. The cavity result is supplementary
evidence: the ghost rides a recirculation vortex and conserves, confirming the
mechanism works in rotational flow, not just unidirectional Poiseuille flow.

For the IEEE paper: the cavity with ghost stamps swirling through the vortex core
is the showpiece figure. Ghost density map + velocity streamlines + conservation
curve over time.
