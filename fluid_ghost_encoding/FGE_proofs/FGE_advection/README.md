# FGE_advection: Breath Ping-Pong Directed Advection

Proves directed ghost advection through Poiseuille flow using **only** the two
wall-safe breath channels (m[17] and m[18]) as alternating re-injection buffers.

## What it proves

| Claim | Result |
|-------|--------|
| Ghost centroid tracks macroscopic flow velocity | 100.0% accuracy: 3.949 vs 3.950 expected cells of drift in 100 ticks |
| m[17] and m[18] survive bounce-back walls without sign inversion | Confirmed by symmetry proof and conservation result |
| Ghost mass conserved through walls and advection | 99.9919% conservation over 100 ticks |
| No external persistent buffer required | Channels alternate as double buffer; no numpy array persists between ticks |

## Architecture

The ping-pong mechanism uses the two wall-safe breath channels as the LBM
equivalent of a double-buffered advection scheme:

```
TICK t:
  1. ghost_pre = read m[PING] from all cells
  2. collision: zero m[PING], passthrough m[PONG]
  3. streaming
  4. for each cell: backtrace to x - ux*dt; interpolate ghost_pre; inject into m[PONG]
  5. swap PING/PONG

TICK t+1: m[PONG] is now the active channel
```

The ghost_pre snapshot is a transient computation buffer (one tick's lifetime),
not a persistent state. In a GPU implementation this would live in shared memory
or registers. The persistent state lives entirely in the distributions.

## Why wall-safe channels matter

m[17] and m[18] are symmetric under bounce-back: M[ch][q] == M[ch][opp[q]] for
all q. This means when a distribution carrying ghost in m[17] or m[18] bounces
off a wall, the sign is preserved and ghost mass is not destroyed. The beam and
cross channels (m[11]-m[16]) are anti-symmetric and would lose ghost at walls.

## Relation to passthrough diffusion (I.A)

Under passthrough only (no re-injection), ghost diffuses isotropically -- the
kernel K[i] = W[i] * M[k][i]^2 / d_k has no velocity term. This advection test
is a separate mechanism: explicit semi-Lagrangian re-injection per tick, which
adds compute cost proportional to one backtrace + interpolation per cell per tick.
These are the two mechanisms described in I.A: passthrough = free isotropic
diffusion; re-injection = directed advection at per-tick cost.

## Running

```bash
python fluid_ghost_encoding/FGE_proofs/FGE_advection/breath_pingpong_advection.py
```

Runs in approximately 10 seconds on a modern laptop.

## Claims supported

- I.A (re-injection mechanism, directed advection)
- I.N (wall-safe breath channels used for persistence through boundaries)
