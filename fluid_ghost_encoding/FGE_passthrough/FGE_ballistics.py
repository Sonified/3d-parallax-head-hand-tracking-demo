# Author: Robert Alexander
# 👻 Ghost Ballistics with Your Friendly Neighborhood Ghost
#
# Fire 20 shots in 2D at different angles.
# Fire 20 shots in 3D at different angles.
# Track center of mass. Predict cell fractions.
# Prove: the data is always there, always findable, always conserved.
#
import numpy as np
import math

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

W = np.array([12,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1], dtype=np.int64)
EX = [0, 1,-1, 0, 0, 0, 0, 1,-1, 1,-1, 1,-1, 1,-1, 0, 0, 0, 0]
EY = [0, 0, 0, 1,-1, 0, 0, 1, 1,-1,-1, 0, 0, 0, 0, 1,-1, 1,-1]
EZ = [0, 0, 0, 0, 0, 1,-1, 0, 0, 0, 0, 1,-1,-1, 1, 1,-1,-1, 1]

norms = np.diag(M @ np.diag(W) @ M.T)
full_lcd = 144
Minv_scaled = np.zeros((19,19), dtype=np.int64)
for q in range(19):
    for k in range(19):
        Minv_scaled[q,k] = int(W[q]) * int(M[k,q]) * (full_lcd // int(norms[k]))

ghost_lcds = {10:4, 11:24, 12:24, 13:24, 14:8, 15:8, 16:8, 17:48, 18:16}
ghost_channels = list(range(10,19))
ch = 16
lcd = ghost_lcds[ch]
rho0 = 500
omega_num = 5
omega_den = 10

# ==============================
# 2D Engine
# ==============================
def run_2d(GW, GH, ux, uy, start_x, start_y, inject_val, ticks):
    N = GW * GH
    def idx(x,y): return (x%GW) + (y%GH)*GW

    # Init
    f = np.zeros((N,19), dtype=np.int64)
    for i in range(N):
        s = 0
        for q in range(1,19):
            eu = EX[q]*ux + EY[q]*uy
            f[i,q] = (rho0*int(W[q]) + 3*eu*int(W[q])) // 36
            s += f[i,q]
        f[i,0] = rho0 - s

    # Inject
    cell = idx(start_x, start_y)
    total = int(np.sum(f[cell]))
    m = M @ f[cell]
    for c in ghost_channels: m[c] = 0
    m[ch] = inject_val * lcd
    f_raw = Minv_scaled @ m
    for q in range(1,19):
        f[cell,q] = (f_raw[q] + full_lcd//2) // full_lcd if f_raw[q]>=0 else -((-f_raw[q]+full_lcd//2)//full_lcd)
    f[cell,0] = total - np.sum(f[cell,1:])

    # Run
    for t in range(ticks):
        # Collide passthrough
        f_post = np.zeros_like(f)
        for i in range(N):
            tot = int(np.sum(f[i]))
            mx = sum(EX[q]*int(f[i,q]) for q in range(19))
            my = sum(EY[q]*int(f[i,q]) for q in range(19))
            feq = np.zeros(19, dtype=np.int64)
            fs = 0
            for q in range(1,19):
                eu = EX[q]*mx + EY[q]*my
                feq[q] = (tot*int(W[q]) + 3*eu*int(W[q])) // 36
                fs += feq[q]
            feq[0] = tot - fs
            m_f = M @ f[i]; m_eq = M @ feq
            m_out = m_f.copy()
            for k in range(10):
                diff = int(m_f[k]) - int(m_eq[k])
                m_out[k] = int(m_f[k]) - (diff*omega_num)//omega_den
            fr = Minv_scaled @ m_out
            for q in range(1,19):
                f_post[i,q] = (fr[q]+full_lcd//2)//full_lcd if fr[q]>=0 else -((-fr[q]+full_lcd//2)//full_lcd)
            f_post[i,0] = tot - np.sum(f_post[i,1:])
        # Stream
        f_new = np.zeros_like(f)
        for y in range(GH):
            for x in range(GW):
                i = idx(x,y)
                for q in range(19):
                    f_new[i,q] = f_post[idx((x-EX[q])%GW, (y-EY[q])%GH), q]
        f = f_new

    # Read ghost field
    ghosts = {}
    total_g = 0.0
    for y in range(GH):
        for x in range(GW):
            g = float(M[ch] @ f[idx(x,y)]) / lcd
            if abs(g) > 0.1:
                ghosts[(x,y)] = g
                total_g += g

    # Center of mass (circular)
    sx,cx,sy,cy = 0,0,0,0
    for (x,y),g in ghosts.items():
        ax = 2*math.pi*x/GW; ay = 2*math.pi*y/GH
        sx += g*math.sin(ax); cx += g*math.cos(ax)
        sy += g*math.sin(ay); cy += g*math.cos(ay)
    com_x = math.atan2(sx,cx)/(2*math.pi)*GW
    com_y = math.atan2(sy,cy)/(2*math.pi)*GH
    if com_x < 0: com_x += GW
    if com_y < 0: com_y += GH

    return com_x, com_y, total_g, ghosts

# ==============================
# 3D Engine
# ==============================
def run_3d(GW, GH, GD, ux, uy, uz, sx, sy, sz, inject_val, ticks):
    N = GW*GH*GD
    def idx(x,y,z): return (x%GW) + (y%GH)*GW + (z%GD)*GW*GH

    f = np.zeros((N,19), dtype=np.int64)
    for i in range(N):
        s = 0
        for q in range(1,19):
            eu = EX[q]*ux + EY[q]*uy + EZ[q]*uz
            f[i,q] = (rho0*int(W[q]) + 3*eu*int(W[q])) // 36
            s += f[i,q]
        f[i,0] = rho0 - s

    cell = idx(sx,sy,sz)
    total = int(np.sum(f[cell]))
    m = M @ f[cell]
    for c in ghost_channels: m[c] = 0
    m[ch] = inject_val * lcd
    fr = Minv_scaled @ m
    for q in range(1,19):
        f[cell,q] = (fr[q]+full_lcd//2)//full_lcd if fr[q]>=0 else -((-fr[q]+full_lcd//2)//full_lcd)
    f[cell,0] = total - np.sum(f[cell,1:])

    for t in range(ticks):
        f_post = np.zeros_like(f)
        for i in range(N):
            tot = int(np.sum(f[i]))
            mx = sum(EX[q]*int(f[i,q]) for q in range(19))
            my = sum(EY[q]*int(f[i,q]) for q in range(19))
            mz = sum(EZ[q]*int(f[i,q]) for q in range(19))
            feq = np.zeros(19, dtype=np.int64)
            fs = 0
            for q in range(1,19):
                eu = EX[q]*mx + EY[q]*my + EZ[q]*mz
                feq[q] = (tot*int(W[q]) + 3*eu*int(W[q])) // 36
                fs += feq[q]
            feq[0] = tot - fs
            m_f = M @ f[i]; m_eq = M @ feq
            m_out = m_f.copy()
            for k in range(10):
                diff = int(m_f[k]) - int(m_eq[k])
                m_out[k] = int(m_f[k]) - (diff*omega_num)//omega_den
            fr2 = Minv_scaled @ m_out
            for q in range(1,19):
                f_post[i,q] = (fr2[q]+full_lcd//2)//full_lcd if fr2[q]>=0 else -((-fr2[q]+full_lcd//2)//full_lcd)
            f_post[i,0] = tot - np.sum(f_post[i,1:])
        f_new = np.zeros_like(f)
        for z in range(GD):
            for y in range(GH):
                for x in range(GW):
                    i = idx(x,y,z)
                    for q in range(19):
                        f_new[i,q] = f_post[idx((x-EX[q])%GW,(y-EY[q])%GH,(z-EZ[q])%GD),q]
        f = f_new

    # Read ghost field
    total_g = 0.0
    sx2,cx2,sy2,cy2,sz2,cz2 = 0,0,0,0,0,0
    for z in range(GD):
        for y in range(GH):
            for x in range(GW):
                g = float(M[ch] @ f[idx(x,y,z)]) / lcd
                if abs(g) > 0.1:
                    total_g += g
                    ax = 2*math.pi*x/GW; ay = 2*math.pi*y/GH; az = 2*math.pi*z/GD
                    sx2 += g*math.sin(ax); cx2 += g*math.cos(ax)
                    sy2 += g*math.sin(ay); cy2 += g*math.cos(ay)
                    sz2 += g*math.sin(az); cz2 += g*math.cos(az)
    com_x = math.atan2(sx2,cx2)/(2*math.pi)*GW
    com_y = math.atan2(sy2,cy2)/(2*math.pi)*GH
    com_z = math.atan2(sz2,cz2)/(2*math.pi)*GD
    if com_x<0: com_x+=GW
    if com_y<0: com_y+=GH
    if com_z<0: com_z+=GD
    return com_x, com_y, com_z, total_g


# ========================================================
print('='*70)
print('  GHOST BALLISTICS: 20 SHOTS IN 2D')
print('='*70)
print()

GW2, GH2 = 20, 20
TICKS_2D = 5
inject_val = 80
start_2d = (10, 10)

print(f'  Grid: {GW2}x{GH2}, inject={inject_val} at ({start_2d[0]},{start_2d[1]}), {TICKS_2D} ticks')
print(f'  Ghost passthrough (no re-injection)')
print()
print(f'  {"Shot":>4} {"Angle":>7} {"ux":>5} {"uy":>5} {"COM_x":>7} {"COM_y":>7} {"Total":>7} {"Conserved":>10}')
print(f'  {"----":>4} {"-----":>7} {"--":>5} {"--":>5} {"-----":>7} {"-----":>7} {"-----":>7} {"---------":>10}')

speed = 80
for shot in range(20):
    angle = shot * 18  # 0, 18, 36, ... 342 degrees
    rad = math.radians(angle)
    ux = int(speed * math.cos(rad))
    uy = int(speed * math.sin(rad))
    if ux == 0 and uy == 0: ux = 1  # avoid zero flow

    com_x, com_y, total_g, _ = run_2d(GW2, GH2, ux, uy, start_2d[0], start_2d[1], inject_val, TICKS_2D)
    conserved = abs(total_g - inject_val) < inject_val * 0.05
    print(f'  {shot+1:4d} {angle:6d}° {ux:5d} {uy:5d} {com_x:7.2f} {com_y:7.2f} {total_g:7.1f} {"YES" if conserved else "NO":>10}')

print()

# ========================================================
print('='*70)
print('  GHOST BALLISTICS: 20 SHOTS IN 3D')
print('='*70)
print()

GW3, GH3, GD3 = 12, 12, 12
TICKS_3D = 4
start_3d = (6, 6, 6)

print(f'  Grid: {GW3}x{GH3}x{GD3}, inject={inject_val} at ({start_3d[0]},{start_3d[1]},{start_3d[2]}), {TICKS_3D} ticks')
print(f'  Ghost passthrough (no re-injection)')
print()
print(f'  {"Shot":>4} {"ux":>5} {"uy":>5} {"uz":>5} {"COM_x":>7} {"COM_y":>7} {"COM_z":>7} {"Total":>7} {"Conserved":>10}')
print(f'  {"----":>4} {"--":>5} {"--":>5} {"--":>5} {"-----":>7} {"-----":>7} {"-----":>7} {"-----":>7} {"---------":>10}')

# 20 3D directions: axis-aligned, face-diagonals, space-diagonals, and arbitrary
dirs_3d = [
    (80, 0, 0),    # +x
    (0, 80, 0),    # +y
    (0, 0, 80),    # +z
    (-80, 0, 0),   # -x
    (0, -80, 0),   # -y
    (0, 0, -80),   # -z
    (60, 60, 0),   # xy diagonal
    (60, 0, 60),   # xz diagonal
    (0, 60, 60),   # yz diagonal
    (60, -60, 0),  # xy anti-diagonal
    (50, 50, 50),  # space diagonal
    (-50, 50, 50), # opposite space diagonal
    (50, -50, 50),
    (50, 50, -50),
    (70, 20, 10),  # mostly +x, slight yz
    (10, 70, 20),  # mostly +y
    (20, 10, 70),  # mostly +z
    (40, 60, 30),  # arbitrary
    (30, 30, 60),  # arbitrary
    (80, 8, 0),    # 10% off-axis (the kite)
]

for shot, (ux, uy, uz) in enumerate(dirs_3d):
    cx, cy, cz, total_g = run_3d(GW3, GH3, GD3, ux, uy, uz, *start_3d, inject_val, TICKS_3D)
    conserved = abs(total_g - inject_val) < inject_val * 0.10
    print(f'  {shot+1:4d} {ux:5d} {uy:5d} {uz:5d} {cx:7.2f} {cy:7.2f} {cz:7.2f} {total_g:7.1f} {"YES" if conserved else "NO":>10}')

print()
print('='*70)
print('  CONCLUSION')
print('='*70)
