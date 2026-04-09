# FGE Bitwise Identity: Ghost Is Invisible to Physics

Proves that a ghost-carrying simulation and an identical no-ghost simulation produce bitwise identical velocity fields.

## File

- `ghost_physics_independence_u32.py`

## What it proves

Two identical u32 Poiseuille simulations run in parallel:
- Run A: RHO=2^32, Ghost=2^26 injected at center cell
- Run B: RHO=2^32, no ghost

After 5,000 ticks, at every cell:

```
Total absolute velocity difference: 0/10000
Ghost effect on physics: ZERO — bitwise identical
```

This is not statistical equivalence. It is integer-exact bitwise identity. The ghost value 2^26 (9.38% of the rest distribution) produces zero measurable effect on any velocity at any cell after 5,000 ticks.

## Results

```
ux_max WITH ghost:  359/10000  (101.52% of analytical)
ux_max NO ghost:    359/10000  (101.52% of analytical)
Velocity difference at every cell: EXACTLY 0
```

## Claim support

Supports **I.K**: "a direct cell-by-cell comparison between the ghost-carrying simulation and an identical no-ghost simulation yields a total velocity difference of exactly 0 counts across all cells." The ghost is invisible to the physics at the level of individual integer values.
