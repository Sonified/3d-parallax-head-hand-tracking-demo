# Author: Robert Alexander
# 👻 Ghost Passthrough with Your Friendly Neighborhood Ghost
#
# The real test: inject ghost data ONCE, then run pure MRT collision
# with ghost modes set to passthrough (relaxation rate = 0).
# No re-injection. Does the data survive? Where does it go?
#
import numpy as np

M = np.array([
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 1,-1, 0, 0, 0, 0, 1,-1, 1,-1, 1,-1, 1,-1, 0, 0, 0, 0],
    [0, 0, 0, 1,-1, 0, 0, 1, 1,-1,-1, 0, 0, 0, 0, 1,-1, 1,-1],
    [0, 0, 0, 0, 0, 1,-1, 0, 0, 0, 0, 1, 1,-1,-1, 1, 1,-1,-1],
    [-1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1,-2,-2,-2,-2,-2,-2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 1, 1,-1,-1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,-1,-1,-1,-1],
    [0, 1, 1, 1, 1,-2,-2, 2, 2, 2, 2,-1,-1,-1,-1,-1,-1,-1,-1],
    [0, 0, 0, 0, 0, 0, 0, 1,-1,-1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,-1,-1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,-1,-1, 1, 0, 0, 0, 0],
    [0,-2, 2, 0, 0, 0, 0, 1,-1, 1,-1, 1,-1, 1,-1, 0, 0, 0, 0],
    [0, 0, 0,-2, 2, 0, 0, 1, 1,-1,-1, 0, 0, 0, 0, 1,-1, 1,-1],
    [0, 0, 0, 0, 0,-2, 2, 0, 0, 0, 0, 1, 1,-1,-1, 1, 1,-1,-1],
    [0, 0, 0, 0, 0, 0, 0, 1, 1,-1,-1, 0, 0, 0, 0,-1, 1,-1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1,-1,-1,-1,-1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 1,-1, 1,-1,-1, 1,-1, 1, 0, 0, 0, 0],
    [0, 2, 2,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1, 2, 2, 2, 2],
    [0, 0, 0, 1, 1,-1,-1,-1,-1,-1,-1, 1, 1, 1, 1, 0, 0, 0, 0],
], dtype=np.int64)

W = np.array([12, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], dtype=np.int64)
EX = [0, 1,-1, 0, 0, 0, 0, 1,-1, 1,-1, 1,-1, 1,-1, 0, 0, 0, 0]

norms = np.diag(M @ np.diag(W) @ M.T)
full_lcd = 144
Minv_scaled = np.zeros((19, 19), dtype=np.int64)
for q in range(19):
    for k in range(19):
        Minv_scaled[q, k] = int(W[q]) * int(M[k, q]) * (full_lcd // int(norms[k]))

ghost_channels = list(range(10, 19))
ghost_lcds = {10:4, 11:24, 12:24, 13:24, 14:8, 15:8, 16:8, 17:48, 18:16}

N = 64
TICKS = 100
omega_num = 5
omega_den = 10
rho0 = 500
ux0 = 80  # global flow velocity

# --- Init with velocity ---
def init_grid():
    f = np.zeros((N, 19), dtype=np.int64)
    for i in range(N):
        s = 0
        for q in range(1, 19):
            f[i, q] = (rho0 * int(W[q]) + 3 * EX[q] * ux0 * int(W[q])) // 36
            s += f[i, q]
        f[i, 0] = rho0 - s
    return f

# --- Inject ghost data into specific cells (one-time) ---
def inject_ghost(f, cells, channel, value):
    lcd = ghost_lcds[channel]
    for i in cells:
        total = int(np.sum(f[i]))
        m = M @ f[i]
        # Zero all ghost modes, set our channel
        for ch in ghost_channels:
            m[ch] = 0
        m[channel] = value * lcd
        # Inverse transform
        f_raw = Minv_scaled @ m
        for q in range(1, 19):
            if f_raw[q] >= 0:
                f[i, q] = (f_raw[q] + full_lcd // 2) // full_lcd
            else:
                f[i, q] = -((-f_raw[q] + full_lcd // 2) // full_lcd)
        f[i, 0] = total - np.sum(f[i, 1:])
    return f

# --- Read ghost value from a cell ---
def read_ghost(f, i, channel):
    lcd = ghost_lcds[channel]
    moment = int(M[channel] @ f[i])
    if moment >= 0:
        return (moment + lcd // 2) // lcd
    else:
        return -((-moment + lcd // 2) // lcd)

# --- MRT collision with ghost PASSTHROUGH ---
def collide_passthrough(f):
    f_post = np.zeros_like(f)
    for i in range(N):
        total = int(np.sum(f[i]))
        # Equilibrium with velocity
        momx = sum(EX[q] * int(f[i, q]) for q in range(19))
        feq = np.zeros(19, dtype=np.int64)
        feq_sum = 0
        for q in range(1, 19):
            feq[q] = (total * int(W[q]) + 3 * EX[q] * momx * int(W[q])) // 36
            feq_sum += feq[q]
        feq[0] = total - feq_sum

        # Forward MRT
        m_f = M @ f[i]
        m_eq = M @ feq

        # Relax ONLY physical modes (0-9)
        m_out = m_f.copy()
        for k in range(10):
            diff = int(m_f[k]) - int(m_eq[k])
            m_out[k] = int(m_f[k]) - (diff * omega_num) // omega_den

        # Ghost modes 10-18: PASSTHROUGH (no relaxation, no zeroing)
        # m_out[10:18] = m_f[10:18]  (already the case from .copy())

        # Inverse transform
        f_raw = Minv_scaled @ m_out
        for q in range(1, 19):
            if f_raw[q] >= 0:
                f_post[i, q] = (f_raw[q] + full_lcd // 2) // full_lcd
            else:
                f_post[i, q] = -((-f_raw[q] + full_lcd // 2) // full_lcd)
        f_post[i, 0] = total - np.sum(f_post[i, 1:])
    return f_post

# --- Stream (periodic) ---
def stream(f):
    f_new = np.zeros_like(f)
    for i in range(N):
        for q in range(19):
            f_new[i, q] = f[(i - EX[q]) % N, q]
    return f_new

# === RUN ===
print('=== FGE GHOST PASSTHROUGH TEST ===')
print(f'{N} cells, rho={rho0}, ux={ux0}, omega={omega_num}/{omega_den}')
print(f'Inject ghost=42 into channel 16 at cells 28-35, then run {TICKS} ticks')
print(f'NO re-injection. Ghost modes pass through collision untouched.')
print()

f = init_grid()

# Inject once
inject_cells = list(range(28, 36))
inject_val = 42
inject_ch = 16
f = inject_ghost(f, inject_cells, inject_ch, inject_val)

# Verify injection
print('After injection:')
for i in inject_cells:
    g = read_ghost(f, i, inject_ch)
    print(f'  cell {i}: ghost={g} (want {inject_val})')
print()

# Track total ghost across all cells
initial_ghost_total = sum(read_ghost(f, i, inject_ch) for i in range(N))
print(f'Initial ghost total: {initial_ghost_total}')
print()

# Run simulation
report_ticks = {0, 1, 2, 5, 10, 20, 50, 99}
print(f'{"Tick":>4} {"GhostTotal":>10} {"Peak":>6} {"PeakCell":>8} {"Spread":>6} {"Mass":>8}')
print(f'{"----":>4} {"----------":>10} {"------":>6} {"--------":>8} {"------":>6} {"--------":>8}')

for tick in range(TICKS):
    # Collide with ghost passthrough
    f = collide_passthrough(f)
    # Stream
    f = stream(f)

    if tick in report_ticks:
        # Read ghost values everywhere
        ghosts = [read_ghost(f, i, inject_ch) for i in range(N)]
        ghost_total = sum(ghosts)
        nonzero = [(i, g) for i, g in enumerate(ghosts) if g != 0]
        peak_val = max(g for _, g in nonzero) if nonzero else 0
        peak_cell = [i for i, g in nonzero if g == peak_val][0] if nonzero else -1
        spread = len(nonzero)
        total_mass = sum(int(np.sum(f[i])) for i in range(N))

        drift_pct = abs(ghost_total - initial_ghost_total) / max(initial_ghost_total, 1) * 100
        print(f'{tick+1:4d} {ghost_total:10d} {peak_val:6d} {peak_cell:8d} {spread:6d} {total_mass:8d}')

print()
final_ghost_total = sum(read_ghost(f, i, inject_ch) for i in range(N))
ghost_drift = abs(final_ghost_total - initial_ghost_total) / max(initial_ghost_total, 1) * 100
total_mass = sum(int(np.sum(f[i])) for i in range(N))
mass_drift = abs(total_mass - N * rho0) / (N * rho0) * 100

print(f'Ghost: {final_ghost_total} (initial {initial_ghost_total}) drift={ghost_drift:.2f}%')
print(f'Mass:  {total_mass} (initial {N * rho0}) drift={mass_drift:.4f}%')
print()
if ghost_drift < 5:
    print('GHOST DATA SURVIVES PASSTHROUGH')
else:
    print('GHOST DATA LOST')
