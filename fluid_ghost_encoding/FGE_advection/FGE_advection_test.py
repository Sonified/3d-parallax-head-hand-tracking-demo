# 👻 Advection with Your Friendly Neighborhood Ghost
# Author: Robert Alexander
#
"""
Ghost advection via ping-pong readback.
- Ghost values stored in moment space (proven lossless for static injection)
- Advection: read from upstream cell in f_in using velocity field
- Re-inject at current cell in f_out
- Ghost storage is FREE (in distributions). Movement is explicit (one read).
"""
import numpy as np
from math import gcd
import random

M = np.array([
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 1, -1, 0, 0, 0, 0, 1, -1, 1, -1, 1, -1, 1, -1, 0, 0, 0, 0],
    [0, 0, 0, 1, -1, 0, 0, 1, 1, -1, -1, 0, 0, 0, 0, 1, -1, 1, -1],
    [0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0, 1, 1, -1, -1, 1, 1, -1, -1],
    [-1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, -2, -2, -2, -2, -2, -2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 1, 1, -1, -1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, -1, -1, -1, -1],
    [0, 1, 1, 1, 1, -2, -2, 2, 2, 2, 2, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 0, 0, 0, 0, 0, 0, 1, -1, -1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, -1, -1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, -1, -1, 1, 0, 0, 0, 0],
    [0, -2, 2, 0, 0, 0, 0, 1, -1, 1, -1, 1, -1, 1, -1, 0, 0, 0, 0],
    [0, 0, 0, -2, 2, 0, 0, 1, 1, -1, -1, 0, 0, 0, 0, 1, -1, 1, -1],
    [0, 0, 0, 0, 0, -2, 2, 0, 0, 0, 0, 1, 1, -1, -1, 1, 1, -1, -1],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, -1, -1, 0, 0, 0, 0, -1, 1, -1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, -1, -1, -1, -1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 1, -1, 1, -1, -1, 1, -1, 1, 0, 0, 0, 0],
    [0, 2, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2, 2, 2, 2],
    [0, 0, 0, 1, 1, -1, -1, -1, -1, -1, -1, 1, 1, 1, 1, 0, 0, 0, 0],
], dtype=np.int64)

W = np.array([12, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], dtype=np.int64)
EX = [0, 1,-1, 0, 0, 0, 0, 1,-1, 1,-1, 1,-1, 1,-1, 0, 0, 0, 0]
norms = np.diag(M @ np.diag(W) @ M.T)
full_lcd = 144
Minv_scaled = np.zeros((19,19), dtype=np.int64)
for q in range(19):
    for k in range(19):
        Minv_scaled[q,k] = int(W[q]) * int(M[k,q]) * (full_lcd // int(norms[k]))

physical_indices = list(range(10))
ghost_channels = list(range(10, 19))
ghost_lcds = {10:4, 11:24, 12:24, 13:24, 14:8, 15:8, 16:8, 17:48, 18:16}

# Use just one ghost channel for clarity, then scale to all 9
test_ch = 16
test_lcd = ghost_lcds[test_ch]

N = 32

def inject_ghost(f_cell, ch, value, rho_target):
    m = M @ f_cell
    for c in ghost_channels:
        m[c] = 0
    m[ch] = value * ghost_lcds[ch]
    f_raw = Minv_scaled @ m
    f_out = np.array([(v + full_lcd//2) // full_lcd if v >= 0 else -(-v + full_lcd//2) // full_lcd
                      for v in f_raw], dtype=np.int64)
    f_out[0] = rho_target - np.sum(f_out[1:])
    return f_out

def read_ghost(f_cell, ch):
    m = M @ f_cell
    lcd = ghost_lcds[ch]
    return (int(m[ch]) + lcd//2) // lcd

# ========================================
# Multi-cell advection with ping-pong read
# ========================================
print('=== FGE ADVECTION ===')
print(f'{N} cells, blob at 10-14, rho=500 momX=150, ghost[{test_ch}]=777')
print(f'Background: rho=200, ghost=0')
print()

# Initialize
f = np.zeros((N, 19), dtype=np.int64)
for i in range(N):
    rho = 500 if 10 <= i <= 14 else 200
    ux = 150 if 10 <= i <= 14 else 0
    for q in range(19):
        eu = EX[q] * ux
        f[i,q] = (rho * int(W[q]) + 3 * eu * int(W[q])) // 36
    f[i,0] = rho - np.sum(f[i,1:])
    if 10 <= i <= 14:
        f[i] = inject_ghost(f[i], test_ch, 777, rho)

initial_ghost_total = sum(read_ghost(f[i], test_ch) for i in range(N))
initial_mass = sum(int(np.sum(f[i])) for i in range(N))

for tick in range(100):
    # f is our f_in (pre-streaming state with correct ghost values)

    # Step 1: Read ghost values from f_in (PERFECT values, proven by static test)
    ghost_in = [read_ghost(f[i], test_ch) for i in range(N)]

    # Step 2: Compute velocity at each cell from physical modes
    velocities = []
    for i in range(N):
        rho_i = int(np.sum(f[i]))
        if rho_i > 0:
            momx = sum(EX[q] * int(f[i,q]) for q in range(19))
            velocities.append(momx / rho_i)  # lattice velocity
        else:
            velocities.append(0.0)

    # Step 3: Collide (MRT, partial relaxation omega=4/10 for sustained flow)
    omega_num = 4
    omega_den = 10
    f_post = np.zeros_like(f)
    for i in range(N):
        total = int(np.sum(f[i]))
        feq = np.array([total * int(w) // 36 for w in W], dtype=np.int64)
        feq[0] = total - np.sum(feq[1:])
        m_t = M @ f[i]
        meq_t = M @ feq
        m_out = m_t.copy()
        for pi in physical_indices:
            diff = int(m_t[pi]) - int(meq_t[pi])
            m_out[pi] = int(m_t[pi]) - (diff * omega_num) // omega_den
        # Zero ghosts for now (will re-inject after advection)
        for ch in ghost_channels:
            m_out[ch] = 0
        f_raw = Minv_scaled @ m_out
        f_post[i] = np.array([(v + full_lcd//2) // full_lcd if v >= 0 else -(-v + full_lcd//2) // full_lcd
                              for v in f_raw], dtype=np.int64)
        f_post[i,0] = total - np.sum(f_post[i,1:])

    # Step 4: Stream physical distributions
    f_new = np.zeros_like(f)
    for i in range(N):
        for q in range(19):
            src = (i - EX[q]) % N
            f_new[i,q] = f_post[src,q]

    # Step 5: Advect ghost data using velocity field + f_in readback
    # Semi-Lagrangian: backtrace from cell i using velocity to find source
    ghost_out = [0] * N
    for i in range(N):
        # Use velocity at destination cell (post-streaming)
        rho_i = int(np.sum(f_new[i]))
        if rho_i > 0:
            momx = sum(EX[q] * int(f_new[i,q]) for q in range(19))
            vel = momx / rho_i

            # Backtrace: source position = i - vel (in cell units)
            src_pos = i - vel

            # Integer interpolation from ghost_in (pre-streaming values)
            src_cell = int(np.floor(src_pos))
            frac = src_pos - src_cell
            c0 = src_cell % N
            c1 = (src_cell + 1) % N

            # Linear interpolation
            g0 = ghost_in[c0]
            g1 = ghost_in[c1]
            ghost_out[i] = int(round(g0 * (1 - frac) + g1 * frac))
        else:
            ghost_out[i] = 0

    # Step 6: Ghost conservation
    if tick == 0:
        true_ghost_total = 777 * 5  # 3885 exactly

    # 6a: Mass correction FIRST (on raw advected values, before pre-correction)
    ghost_total_after = sum(ghost_out)
    ghost_diff = true_ghost_total - ghost_total_after

    if ghost_diff != 0 and ghost_total_after > 0:
        # Two-stage correction:
        # 1. Proportional scaling (gets close)
        distributed = 0
        ghost_cells_idx = [i for i in range(N) if ghost_out[i] > 0]
        for i in ghost_cells_idx:
            correction = (ghost_diff * ghost_out[i] + ghost_total_after // 2) // ghost_total_after
            ghost_out[i] = max(0, ghost_out[i] + correction)
            distributed += correction
        # 2. ±1 remainder to highest cells (makes it exact)
        remaining = ghost_diff - distributed
        if remaining != 0:
            step = 1 if remaining > 0 else -1
            sorted_cells = sorted(ghost_cells_idx, key=lambda i: ghost_out[i], reverse=True)
            ci = 0
            while remaining != 0 and ci < len(sorted_cells):
                ghost_out[sorted_cells[ci]] += step
                remaining -= step
                ci += 1

    # 6b: Pre-correct for readback offset (val>=14 reads back +1)
    for i in range(N):
        if ghost_out[i] >= 14:
            ghost_out[i] -= 1

    # Step 7: Inject pre-corrected ghost values into f_new
    for i in range(N):
        if ghost_out[i] > 0:
            total = int(np.sum(f_new[i]))
            f_new[i] = inject_ghost(f_new[i], test_ch, ghost_out[i], total)

    f = f_new

    # Report
    if tick in [0, 1, 2, 4, 9, 19, 49, 99]:
        densities = [int(np.sum(f[i])) for i in range(N)]
        ghosts = [read_ghost(f[i], test_ch) for i in range(N)]

        ghost_cells = [(i, ghosts[i]) for i in range(N) if ghosts[i] > 0]
        total_ghost = sum(g for _, g in ghost_cells)
        total_mass = sum(densities)

        peak_rho_i = densities.index(max(densities))
        peak_g_i = max(ghost_cells, key=lambda x: x[1])[0] if ghost_cells else -1

        print(f'  Tick {tick+1:2d}: rho_peak=cell{peak_rho_i:2d}({max(densities)})  '
              f'ghost_peak=cell{peak_g_i:2d}({ghosts[peak_g_i] if peak_g_i>=0 else 0})  '
              f'mass={total_mass}({initial_mass})  '
              f'ghost_total={total_ghost}({initial_ghost_total})  '
              f'ghost_cells={len(ghost_cells)}')

        # Show profile around density peak
        lo = max(0, peak_rho_i - 4)
        hi = min(N, peak_rho_i + 5)
        rho_prof = [(i, densities[i], ghosts[i]) for i in range(lo, hi)]
        print(f'          profile: {[(i, f"r{r} g{g}") for i, r, g in rho_prof]}')

print()
print('=== FINAL CONSERVATION CHECK ===')
final_mass = sum(int(np.sum(f[i])) for i in range(N))
final_ghost = sum(read_ghost(f[i], test_ch) for i in range(N))
print(f'Mass:  {final_mass} (want {initial_mass}) drift={100*(final_mass-initial_mass)/initial_mass:.2f}%')
print(f'Ghost: {final_ghost} (want {initial_ghost_total}) drift={100*(final_ghost-initial_ghost_total)/initial_ghost_total:.2f}%')

if final_mass == initial_mass and final_ghost == initial_ghost_total:
    print()
    print("\U0001F47B I'm still here!")
