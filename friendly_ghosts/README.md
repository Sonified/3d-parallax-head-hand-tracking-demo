# 👻 FGP: Your Friendly Neighborhood Ghost

Lossless metadata transport in the null space of integer Lattice Boltzmann distributions.

*The new guys nobody expected. Turns out they were carrying everything.*

D3Q19 LBM has 19 distributions per cell but only 10 physical degrees of freedom. The remaining 9 are ghost modes -- orthogonal to all physics, invisible to the fluid, free to carry data.

## The Tests

| Test | Question | Answer |
|------|----------|--------|
| [FG_roundtrip](FG_roundtrip/) | Can ghost data survive the MRT transform? | Yes. 9 channels, 85 bits, exact. |
| [FG_streaming](FG_streaming/) | What happens to ghost data when distributions stream? | Known kernel per channel. All recoverable. |
| [FG_encoding](FG_encoding/) | Can ghost data survive collision + streaming over many ticks? | 200/200 random trials, 50 ticks, perfect. |
| [FG_advection](FG_advection/) | Does ghost data flow with the fluid? | Yes. 100 ticks, 0.00% drift. |
| [FG_midstream](FG_midstream/) | Can you inject ghost data into flowing fluid? | Yes. 0.00% drift, immediate lock-in. |

## How It Works

1. Construct a weight-orthogonal MRT transformation matrix (integer entries, exact in integer arithmetic)
2. Transform distributions to moment space: m = M * f
3. Ghost moments m[10]-m[18] are orthogonal to physics. Write data there.
4. Scale values by channel LCD (4, 8, 16, 24, 48) for exact division on readback
5. Transform back: f = M_inv * m. Mass correction absorbs truncation.
6. Advect via ping-pong readback: read ghost from upstream cell in f_in using velocity field
7. Conservation: track total as external invariant, force-correct after advection

## The Channels

| Channel | LCD | Bits | Max Value |
|---------|-----|------|-----------|
| m[10] | 4 | 11 | 2046 |
| m[11] | 24 | 9 | 341 |
| m[12] | 24 | 9 | 341 |
| m[13] | 24 | 9 | 341 |
| m[14] | 8 | 10 | 1023 |
| m[15] | 8 | 10 | 1023 |
| m[16] | 8 | 10 | 1023 |
| m[17] | 48 | 8 | 170 |
| m[18] | 16 | 9 | 511 |

85 bits per cell. Zero additional memory. Flows with the fluid. Integer exact.
