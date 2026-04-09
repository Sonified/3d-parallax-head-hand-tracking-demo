# FGE Bit Depth Scaling: Ghost Capacity vs Integer Precision

Characterizes how ghost encoding capacity scales with the integer word size of the simulation.

## File

- `ghost-stamp-bit-depth-scaling.py`

## What it proves

Runs the ghost stamp test across seven integer precisions: u8, u10, u12, u16, u20, u24, u32. For each precision, sets RHO to the maximum value where distributions stay within range, then measures ghost conservation over 100 ticks on a 3x9x3 = 81-cell periodic grid.

### Results

| Depth | RHO | Ghost bits | Per-cell | Conservation |
|-------|-----|-----------|---------|-------------|
| u8 | 765 | 2 | 0 | DEAD (too small) |
| u16 | 49,140 | 8 | 1 | Rough |
| u20 | 786,420 | 12 | varies | Good |
| u24 | 12,582,720 | 17 | varies | Great |
| u32 | 3,221,225,472 | 26 | varies | Excellent |

Ghost bits available scale approximately as: `word_bits - 6` (6 bits consumed by the lattice weights and equilibrium scaling).

## Key insight

At u32, 26 bits of ghost data survive 5,000 ticks of driven Poiseuille flow. After spreading to V cells, approximately `26 - log2(V)` bits remain readable per cell.

## Claim support

Supports **I.A** and **I.K**: "the stamp capacity at u32 precision may support 26 or more bits of distinguishable stamp values per single-cell injection; after spreading to a domain of V cells, approximately 26 - log2(V) bits remain readable per cell."
