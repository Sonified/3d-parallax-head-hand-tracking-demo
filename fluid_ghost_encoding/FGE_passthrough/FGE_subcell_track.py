# Author: Robert Alexander
# 👻 Sub-Cell Ghost Tracking with Your Friendly Neighborhood Ghost
#
# One cell. One ghost value. Let it flow.
# Watch it spread across neighbors. Find the center of mass.
# The ghost isn't in a cell. It's BETWEEN cells. Always.
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

N = 32
omega_num = 5
omega_den = 10
rho0 = 500
ux0 = 80
ch = 16
lcd = ghost_lcds[ch]

def init_grid():
    f = np.zeros((N, 19), dtype=np.int64)
    for i in range(N):
        s = 0
        for q in range(1, 19):
            f[i, q] = (rho0 * int(W[q]) + 3 * EX[q] * ux0 * int(W[q])) // 36
            s += f[i, q]
        f[i, 0] = rho0 - s
    return f

def inject_ghost(f, cell, channel, value):
    lcd_ch = ghost_lcds[channel]
    total = int(np.sum(f[cell]))
    m = M @ f[cell]
    for c in ghost_channels:
        m[c] = 0
    m[channel] = value * lcd_ch
    f_raw = Minv_scaled @ m
    for q in range(1, 19):
        if f_raw[q] >= 0:
            f[cell, q] = (f_raw[q] + full_lcd // 2) // full_lcd
        else:
            f[cell, q] = -((-f_raw[q] + full_lcd // 2) // full_lcd)
    f[cell, 0] = total - np.sum(f[cell, 1:])
    return f

def read_ghost(f, i, channel):
    lcd_ch = ghost_lcds[channel]
    moment = int(M[channel] @ f[i])
    if moment >= 0:
        return (moment + lcd_ch // 2) // lcd_ch
    else:
        return -((-moment + lcd_ch // 2) // lcd_ch)

def read_ghost_raw(f, i, channel):
    """Return the raw moment (before LCD division) for sub-cell precision."""
    return float(M[channel] @ f[i]) / ghost_lcds[channel]

def collide_passthrough(f):
    f_post = np.zeros_like(f)
    for i in range(N):
        total = int(np.sum(f[i]))
        momx = sum(EX[q] * int(f[i, q]) for q in range(19))
        feq = np.zeros(19, dtype=np.int64)
        feq_sum = 0
        for q in range(1, 19):
            feq[q] = (total * int(W[q]) + 3 * EX[q] * momx * int(W[q])) // 36
            feq_sum += feq[q]
        feq[0] = total - feq_sum

        m_f = M @ f[i]
        m_eq = M @ feq
        m_out = m_f.copy()
        for k in range(10):
            diff = int(m_f[k]) - int(m_eq[k])
            m_out[k] = int(m_f[k]) - (diff * omega_num) // omega_den
        # Ghost modes 10-18: PASSTHROUGH

        f_raw = Minv_scaled @ m_out
        for q in range(1, 19):
            if f_raw[q] >= 0:
                f_post[i, q] = (f_raw[q] + full_lcd // 2) // full_lcd
            else:
                f_post[i, q] = -((-f_raw[q] + full_lcd // 2) // full_lcd)
        f_post[i, 0] = total - np.sum(f_post[i, 1:])
    return f_post

def stream(f):
    f_new = np.zeros_like(f)
    for i in range(N):
        for q in range(19):
            f_new[i, q] = f[(i - EX[q]) % N, q]
    return f_new

# === RUN ===
print('=== SUB-CELL GHOST TRACKING ===')
print(f'{N} cells, rho={rho0}, ux={ux0}, omega={omega_num}/{omega_den}')
print(f'Inject ghost=42 into ONE cell (cell 16), then watch it spread')
print()

f = init_grid()
f = inject_ghost(f, 16, ch, 42)

print(f'Tick 0: injected ghost=42 at cell 16')
print()

for tick in range(20):
    f = collide_passthrough(f)
    f = stream(f)

    # Read ghost values from ALL cells (raw, sub-cell precision)
    ghosts_raw = [read_ghost_raw(f, i, ch) for i in range(N)]
    ghosts_int = [read_ghost(f, i, ch) for i in range(N)]
    total_raw = sum(ghosts_raw)
    total_int = sum(ghosts_int)

    # Find center of mass
    weighted_pos = sum(i * ghosts_raw[i] for i in range(N))
    if total_raw > 0.01:
        center = weighted_pos / total_raw
    else:
        center = -1

    # Expected position: initial pos + velocity * ticks
    # velocity = ux0/rho0 lattice units per tick
    vel = ux0 / rho0
    expected_center = (16 + vel * (tick + 1)) % N

    # Find cells with significant ghost data
    active = [(i, ghosts_raw[i]) for i in range(N) if abs(ghosts_raw[i]) > 0.5]

    if tick < 10 or tick == 19:
        print(f'--- Tick {tick+1} ---')
        print(f'  Total (raw):  {total_raw:.2f}')
        print(f'  Total (int):  {total_int}')
        print(f'  Center of mass: {center:.2f}  (expected: {expected_center:.2f})')
        print(f'  Active cells: {len(active)}')
        if len(active) <= 12:
            for i, g in active:
                print(f'    cell {i:2d}: {g:6.2f}')
        else:
            # Show top 6
            active.sort(key=lambda x: -abs(x[1]))
            for i, g in active[:6]:
                print(f'    cell {i:2d}: {g:6.2f}')
            print(f'    ... and {len(active)-6} more cells')
        print()
