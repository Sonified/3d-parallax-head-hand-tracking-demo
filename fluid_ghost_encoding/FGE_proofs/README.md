# FGE Proof Suite

Experimental validation for the Fluid Ghost Encoding patent disclosure (`FGE-TECHNICAL-DISCLOSURE.md`). Each folder contains one or more Python scripts proving a specific claim, plus a README mapping results to claim language.

## Index

| Folder | What it proves | Claim |
|--------|---------------|-------|
| [FGE_poiseuille](FGE_poiseuille/) | Ghost coexists with correct Poiseuille flow at RHO=10^9 and RHO=2^32. 26-bit ghost survives 5,000 ticks at u32 precision. | I.A, I.B |
| [FGE_zero_cost](FGE_zero_cost/) | Ghost encode/decode are the MRT collision steps already being performed. No additional computation. | I.A |
| [FGE_bitwise_identity](FGE_bitwise_identity/) | Ghost-carrying and no-ghost simulations produce bitwise identical velocity fields. Total velocity difference: exactly 0. | I.K |
| [FGE_noise_floor](FGE_noise_floor/) | Integer rounding defines a per-cell noise floor (~16 counts). Velocity deviation constant at 3/1000 regardless of ghost magnitude. Operational envelope: floor=ghost/cells>16, ceiling=RHO/144. | I.K |
| [FGE_two_population](FGE_two_population/) | Two ghost populations in 128x128 domain. 128/128 correct classification for 32 seconds. Gradient direction is the information carrier. | I.L, I.M |
| [FGE_bit_depth_scaling](FGE_bit_depth_scaling/) | Ghost capacity scales with integer word size. At u32: 26 bits. After spreading to V cells: 26 - log2(V) bits per cell. | I.A, I.K |

## Running the proofs

All scripts are pure Python with numpy. Run from any directory:

```bash
python fluid_ghost_encoding/FGE_proofs/FGE_poiseuille/poiseuille_u32_proof.py
python fluid_ghost_encoding/FGE_proofs/FGE_bitwise_identity/ghost_physics_independence_u32.py
python fluid_ghost_encoding/FGE_proofs/FGE_noise_floor/noise_floor_sweep.py
python fluid_ghost_encoding/FGE_proofs/FGE_two_population/two_population_isolation.py
```

The two_population test runs for approximately 2.5 minutes on a modern laptop (128x128 = 16,384 cells, 3,840 ticks).

## Proof chain summary

1. **Physics works** (FGE_poiseuille): correct Poiseuille flow with ghost present
2. **Ghost is free** (FGE_zero_cost): encode/decode inside existing collision, zero overhead
3. **Ghost is invisible** (FGE_bitwise_identity): zero velocity difference vs no-ghost control
4. **Operational envelope** (FGE_noise_floor): floor and ceiling bounds, no guards needed within
5. **Populations isolate** (FGE_two_population): 32-second classification lifetime, gradient as carrier
6. **Scales with precision** (FGE_bit_depth_scaling): 26 bits at u32, predictable scaling formula

Each proof is independent and reproducible. Together they form the evidentiary basis for the FGE provisional patent filing.
