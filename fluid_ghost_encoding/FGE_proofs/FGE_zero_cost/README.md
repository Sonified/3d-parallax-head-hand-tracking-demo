# FGE Zero Cost: Ghost Rides Free

Proves that ghost encoding and decoding are not additional operations -- they are the MRT collision steps already being performed.

## File

- `ghost_zero_cost_proof.py`

## What it proves

The standard MRT pipeline is:
1. `m = M @ f` (forward transform)
2. Relax physical moments (collision)
3. Ghost moment unchanged (passthrough: relaxation rate = 0)
4. `f = M_inv @ m` (inverse transform)
5. Stream f to neighbors

Step 1 **is** the ghost decode: `ghost_value = m[CH] / norms[CH]`.
Step 4 **is** the ghost encode: setting `m[CH]` before the inverse transform encodes the ghost into all 19 distributions.

No additional read passes, write passes, or computation beyond what the collision already performs.

## Claim support

Supports **I.A**: "zero additional computation beyond one moment-space read per ghost channel from the upstream cell." The ghost encodes and decodes inside the transform the simulation already pays for.
