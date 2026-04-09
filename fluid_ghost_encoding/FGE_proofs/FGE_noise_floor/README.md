# FGE Noise Floor: Operational Envelope

Characterizes the integer rounding noise floor and defines the operational envelope for ghost injection.

## File

- `noise_floor_sweep.py`

## What it proves

Sweeps ghost injection values from 1 to 1,000,000 across a 5x5x5 periodic domain. Measures conservation accuracy and velocity deviation versus a no-ghost control.

### Conservation by per-cell share

| Per-cell share | Conservation error | Status |
|---|---|---|
| < 8 | DESTROYED (e.g. ghost=1 reads 3000%) | DEAD |
| 8–16 | 1–3% error | ROUGH |
| 16–80 | < 1% error | GOOD |
| 80–160 | < 0.3% error | GREAT |
| > 160 | < 0.05% error | EXCELLENT |

### Velocity deviation

Constant at **3/1000** regardless of ghost magnitude across the entire range. The ghost does not push the fluid harder at larger values.

### Alignment finding

Odd numbers and non-multiples of 16 perform identically to aligned values. Arithmetic alignment provides no survival advantage. Survival is governed entirely by per-cell share exceeding the noise floor.

## Operational envelope

```
FLOOR:   ghost_injected / cells_reached > ~16
CEILING: ghost_injected < RHO / 144  (~29.8M at u32)
```

Within this envelope: zero negative cells, no guards, no clamping, no re-injection. ~10 bits of usable dynamic range between floor and ceiling.

## Claim support

Supports **I.K**: "survival is governed entirely by whether the per-cell share exceeds the rounding noise floor, not by any alignment property of the injected value." Defines the floor and ceiling bounds cited in the disclosure.
