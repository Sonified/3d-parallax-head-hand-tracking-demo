# Author: Robert Alexander
# 👻 Off-Grid Shot with Your Friendly Neighborhood Ghost
#
# Fire a ghost value down a 2D grid. Then turn 10% to the right.
# Watch the fractions compute themselves across cell boundaries.
# We're off the grid.
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
# D3Q19 velocities
EX = [0, 1,-1, 0, 0, 0, 0, 1,-1, 1,-1, 1,-1, 1,-1, 0, 0, 0, 0]
EY = [0, 0, 0, 1,-1, 0, 0, 1, 1,-1,-1, 0, 0, 0, 0, 1,-1, 1,-1]

norms = np.diag(M @ np.diag(W) @ M.T)
full_lcd = 144
Minv_scaled = np.zeros((19, 19), dtype=np.int64)
for q in range(19):
    for k in range(19):
        Minv_scaled[q, k] = int(W[q]) * int(M[k, q]) * (full_lcd // int(norms[k]))

ghost_channels = list(range(10, 19))
ghost_lcds = {10:4, 11:24, 12:24, 13:24, 14:8, 15:8, 16:8, 17:48, 18:16}

# 2D grid (using x,y plane of the 3D lattice)
GW, GH = 24, 16
N = GW * GH
omega_num = 5
omega_den = 10
ch = 16
lcd = ghost_lcds[ch]

def idx(x, y):
    return (x % GW) + (y % GH) * GW

def init_grid(ux, uy):
    """Init with uniform velocity field."""
    f = np.zeros((N, 19), dtype=np.int64)
    rho = 500
    for i in range(N):
        s = 0
        for q in range(1, 19):
            eu = EX[q] * ux + EY[q] * uy
            f[i, q] = (rho * int(W[q]) + 3 * eu * int(W[q])) // 36
            s += f[i, q]
        f[i, 0] = rho - s
    return f

def inject_ghost(f, cell, value):
    total = int(np.sum(f[cell]))
    m = M @ f[cell]
    for c in ghost_channels:
        m[c] = 0
    m[ch] = value * lcd
    f_raw = Minv_scaled @ m
    for q in range(1, 19):
        if f_raw[q] >= 0:
            f[cell, q] = (f_raw[q] + full_lcd // 2) // full_lcd
        else:
            f[cell, q] = -((-f_raw[q] + full_lcd // 2) // full_lcd)
    f[cell, 0] = total - np.sum(f[cell, 1:])
    return f

def read_ghost_raw(f, i):
    return float(M[ch] @ f[i]) / lcd

def collide_passthrough(f):
    f_post = np.zeros_like(f)
    for i in range(N):
        total = int(np.sum(f[i]))
        momx = sum(EX[q] * int(f[i, q]) for q in range(19))
        momy = sum(EY[q] * int(f[i, q]) for q in range(19))
        feq = np.zeros(19, dtype=np.int64)
        feq_sum = 0
        for q in range(1, 19):
            eu = EX[q] * momx + EY[q] * momy
            feq[q] = (total * int(W[q]) + 3 * eu * int(W[q])) // 36
            feq_sum += feq[q]
        feq[0] = total - feq_sum

        m_f = M @ f[i]
        m_eq = M @ feq
        m_out = m_f.copy()
        for k in range(10):
            diff = int(m_f[k]) - int(m_eq[k])
            m_out[k] = int(m_f[k]) - (diff * omega_num) // omega_den
        # Ghost modes: PASSTHROUGH

        f_raw = Minv_scaled @ m_out
        for q in range(1, 19):
            if f_raw[q] >= 0:
                f_post[i, q] = (f_raw[q] + full_lcd // 2) // full_lcd
            else:
                f_post[i, q] = -((-f_raw[q] + full_lcd // 2) // full_lcd)
        f_post[i, 0] = total - np.sum(f_post[i, 1:])
    return f_post

def stream_2d(f):
    """Stream in x,y plane (periodic)."""
    f_new = np.zeros_like(f)
    for y in range(GH):
        for x in range(GW):
            i = idx(x, y)
            for q in range(19):
                sx = (x - EX[q]) % GW
                sy = (y - EY[q]) % GH
                f_new[i, q] = f[idx(sx, sy), q]
    return f_new

def find_center_of_mass(f):
    """Find ghost center of mass with periodic wrapping."""
    # Use circular mean to handle wrapping
    sin_x, cos_x = 0.0, 0.0
    sin_y, cos_y = 0.0, 0.0
    total = 0.0
    for y in range(GH):
        for x in range(GW):
            g = read_ghost_raw(f, idx(x, y))
            if abs(g) > 0.01:
                angle_x = 2 * np.pi * x / GW
                angle_y = 2 * np.pi * y / GH
                sin_x += g * np.sin(angle_x)
                cos_x += g * np.cos(angle_x)
                sin_y += g * np.sin(angle_y)
                cos_y += g * np.cos(angle_y)
                total += g
    if total < 0.01:
        return 0, 0, 0
    cx = np.arctan2(sin_x, cos_x) / (2 * np.pi) * GW
    cy = np.arctan2(sin_y, cos_y) / (2 * np.pi) * GH
    if cx < 0: cx += GW
    if cy < 0: cy += GH
    return cx, cy, total

def print_grid(f, label):
    """Print 2D ghost heatmap."""
    print(f'  {label}')
    print(f'  {"":>3}', end='')
    for x in range(GW):
        print(f'{x:5d}', end='')
    print()
    for y in range(GH):
        print(f'  {y:2d} ', end='')
        for x in range(GW):
            g = read_ghost_raw(f, idx(x, y))
            if abs(g) < 0.3:
                print('    .', end='')
            elif g > 0:
                print(f'{g:5.1f}', end='')
            else:
                print(f'{g:5.1f}', end='')
        print()
    print()

# === TEST 1: Straight shot along X ===
print('=' * 70)
print('TEST 1: STRAIGHT SHOT (pure +X, velocity 100)')
print('=' * 70)
ux, uy = 100, 0
f = init_grid(ux, uy)
start_x, start_y = 4, 8
f = inject_ghost(f, idx(start_x, start_y), 100)

cx, cy, total = find_center_of_mass(f)
print(f'  Injected ghost=100 at ({start_x},{start_y})')
print(f'  Flow: ux={ux}, uy={uy}')
print(f'  Center: ({cx:.2f}, {cy:.2f})  Total: {total:.1f}')
print()

for tick in range(8):
    f = collide_passthrough(f)
    f = stream_2d(f)
    cx, cy, total = find_center_of_mass(f)
    vel = ux / 500  # velocity in lattice units
    ex = (start_x + vel * (tick + 1)) % GW
    ey = start_y
    print(f'  Tick {tick+1}: center=({cx:.2f}, {cy:.2f})  expected=({ex:.2f}, {ey:.2f})  total={total:.1f}')

print()
print_grid(f, 'Ghost field after 8 ticks (straight shot):')

# === TEST 2: Angled shot, 10% to the right ===
print('=' * 70)
print('TEST 2: ANGLED SHOT (turn 10% to the right)')
print('=' * 70)
ux, uy = 100, 10  # 10% lateral
f = init_grid(ux, uy)
start_x, start_y = 4, 8
f = inject_ghost(f, idx(start_x, start_y), 100)

cx, cy, total = find_center_of_mass(f)
print(f'  Injected ghost=100 at ({start_x},{start_y})')
print(f'  Flow: ux={ux}, uy={uy} (10% lateral)')
print(f'  Center: ({cx:.2f}, {cy:.2f})  Total: {total:.1f}')
print()

for tick in range(12):
    f = collide_passthrough(f)
    f = stream_2d(f)
    cx, cy, total = find_center_of_mass(f)
    vel_x = ux / 500
    vel_y = uy / 500
    ex = (start_x + vel_x * (tick + 1)) % GW
    ey = (start_y + vel_y * (tick + 1)) % GH
    print(f'  Tick {tick+1:2d}: center=({cx:.2f}, {cy:.2f})  expected=({ex:.2f}, {ey:.2f})  total={total:.1f}')

print()
print_grid(f, 'Ghost field after 12 ticks (angled shot):')

# === TEST 3: 45 degree shot ===
print('=' * 70)
print('TEST 3: 45 DEGREE SHOT')
print('=' * 70)
ux, uy = 80, 80
f = init_grid(ux, uy)
start_x, start_y = 4, 4
f = inject_ghost(f, idx(start_x, start_y), 100)

cx, cy, total = find_center_of_mass(f)
print(f'  Injected ghost=100 at ({start_x},{start_y})')
print(f'  Flow: ux={ux}, uy={uy} (45 degrees)')
print(f'  Center: ({cx:.2f}, {cy:.2f})  Total: {total:.1f}')
print()

for tick in range(12):
    f = collide_passthrough(f)
    f = stream_2d(f)
    cx, cy, total = find_center_of_mass(f)
    vel_x = ux / 500
    vel_y = uy / 500
    ex = (start_x + vel_x * (tick + 1)) % GW
    ey = (start_y + vel_y * (tick + 1)) % GH
    print(f'  Tick {tick+1:2d}: center=({cx:.2f}, {cy:.2f})  expected=({ex:.2f}, {ey:.2f})  total={total:.1f}')

print()
print_grid(f, 'Ghost field after 12 ticks (45 degree shot):')
