# TRT Poiseuille: SpellARia Fluid Engine Proof

Proves that Two-Relaxation-Time (TRT) collision produces correct Poiseuille flow using pure integer arithmetic. This is the collision method used by the SpellARia fluid engine.

## File

- `trt_poiseuille_proof.py`

## What it proves

D3Q19 TRT collision with integer arithmetic produces the analytical Poiseuille parabola to under 1% error at the optimal force. Mass conservation is exact. No floating point anywhere.

### Key result

FORCE=300000, RHO=10^9, SCALE=10000, tau1=1.3, 3000 ticks on 4x32x4 grid:

- Error: < 1% vs analytical Poiseuille
- Mass drift: 0.000000%
- Mach number: 0.234

### Why TRT instead of MRT

| Property | Full MRT | TRT |
|----------|----------|-----|
| FLOPs/cell | 912 | 36 |
| Matrix transform | 19x19 (twice per tick) | None |
| Ghost modes | 9 (must compute, store, relax or passthrough) | 0 (architecturally absent) |
| Wall accuracy | Viscosity-dependent error | Exact (magic parameter) |
| Registers | High (19-wide vectors) | Low (pair-local) |

TRT achieves the same physical accuracy through parity decomposition (symmetric + antisymmetric splitting of each direction pair) without ever entering moment space. Ghost modes don't exist because the moment transform is never computed.

### TRT collision (36 FLOPs)

For each of 9 inversion pairs (q, q_bar):

```
f_neq_plus  = (f[q] - feq[q] + f[q_bar] - feq[q_bar]) / 2
f_neq_minus = (f[q] - feq[q] - f[q_bar] + feq[q_bar]) / 2

f_post[q]     = feq[q]     + s_plus * f_neq_plus + s_minus * f_neq_minus
f_post[q_bar] = feq[q_bar] + s_plus * f_neq_plus - s_minus * f_neq_minus
```

Where s_plus = (OD1-ON1)/OD1 controls viscosity, s_minus = (OD2-ON2)/OD2 controls wall accuracy.

### Integer precision note

At u10 storage (RHO=1008, SCALE=32), the minimum force quantum (FORCE=1) is below the equilibrium distribution resolution. The velocity perturbation rounds to zero. This is not a TRT limitation; it is a precision floor. The proof uses RHO=10^9 to demonstrate correctness. The SpellARia engine uses u10 for storage with i32 registers during collision; game-scale forces (spell injection) are well above the u10 resolution floor.

## Claim support

Validates the SpellARia fluid engine architecture: integer-deterministic D3Q19 TRT at 36 FLOPs/cell with exact mass conservation and no ghost mode overhead.
