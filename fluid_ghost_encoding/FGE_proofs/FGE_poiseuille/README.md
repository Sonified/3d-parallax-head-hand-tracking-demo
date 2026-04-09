# FGE Poiseuille: Physics Validation

Proves that ghost data coexists with correct fluid dynamics across 5,000 ticks of driven Poiseuille flow.

## Files

- `poiseuille_ghost_proof.py` — Ghost at RHO=10^9, Ghost=2^18. Proves correct parabolic velocity profile and ghost conservation simultaneously.
- `poiseuille_u32_proof.py` — Ghost at RHO=2^32, Ghost=2^26 (9.38% of rest distribution). Proves 26-bit ghost encoding in full u32 integer arithmetic.

## Results

| Run | RHO | Ghost | ux_max | vs analytical | Ghost conservation |
|-----|-----|-------|--------|---------------|-------------------|
| poiseuille_ghost_proof.py | 10^9 | 2^18 | 386/10000 | 101.7% | 100.016% |
| poiseuille_u32_proof.py | 2^32 | 2^26 | 359/10000 | 101.5% | 100.000051% |

Ghost bits stored: 26. Ghost bits surviving: 26. Physics accuracy: 1.5% (correct for 9-cell discrete LBM).

## Claim support

Supports **I.A** (ghost encoding capacity) and **I.B** (weight-orthogonal passthrough mechanism). The u32 run establishes the scaling relationship between integer word size and available ghost capacity.
