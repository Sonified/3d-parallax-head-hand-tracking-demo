"""
LID-DRIVEN CAVITY with ghost data swirling inside — VECTORIZED.

Collision fully vectorized (numpy matmul over full grid, no Python x/y loops).
Streaming loops over 19 directions only, vectorized body via np.add.at.

Grid: 13x13 total (11x11 fluid cells). ~100x faster than pure Python loops.
Re = U_lid * L / nu = 0.1 * 11 / 0.433 ≈ 2.5 (low Re, clear vortex, stable).
For Ghia comparison (Re=100+), use a larger grid or lower viscosity.

Ghost = 2^20 injected at center, rides the vortex.
"""
import numpy as np
import time

M = np.array([
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 1,-1, 0, 0, 0, 0, 1,-1, 1,-1, 1,-1, 1,-1, 0, 0, 0, 0],
    [0, 0, 0, 1,-1, 0, 0, 1, 1,-1,-1, 0, 0, 0, 0, 1,-1, 1,-1],
    [0, 0, 0, 0, 0, 1,-1, 0, 0, 0, 0, 1, 1,-1,-1, 1, 1,-1,-1],
    [-1,0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
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
    [0, 0, 0, 1, 1,-1,-1,-1,-1,-1,-1, 1, 1, 1, 1, 0, 0, 0, 0]
], dtype=np.int64)
W_int = np.arrasy([12,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1], dtype=np.int64)
EX = np.array([0,1,-1,0,0,0,0,1,-1,1,-1,1,-1,1,-1,0,0,0,0], dtype=np.int64)
EY = np.array([0,0,0,1,-1,0,0,1,1,-1,-1,0,0,0,0,1,-1,1,-1], dtype=np.int64)
EZ = np.array([0,0,0,0,0,1,-1,0,0,0,0,1,1,-1,-1,1,1,-1,-1], dtype=np.int64)
norms = np.array([np.sum(W_int * M[k]**2) for k in range(19)], dtype=np.int64)
LCD = int(np.lcm.reduce(norms))
Minv_s = np.zeros((19,19), dtype=np.int64)
for q in range(19):
    for k in range(19):
        Minv_s[q,k] = W_int[q]*M[k,q]*(LCD//norms[k])

opp = np.zeros(19, dtype=np.int64)
for q in range(19):
    for qq in range(19):
        if EX[qq]==-EX[q] and EY[qq]==-EY[q] and EZ[qq]==-EZ[q]: opp[q]=qq

CH = 18
NX = 102; NY = 102  # 100x100 fluid cells
SCALE = np.int64(10000)
RHO  = np.int64(10**9)
ON = np.int64(10); OD = np.int64(13)
U_LID = np.int64(1000)   # 0.1 lu
GHOST = np.int64(1 << 20)

nu = (1/3)*(float(OD)/float(ON) - 0.5)
L = NX - 2
Re = float(U_LID) / float(SCALE) * L / nu

# Precompute meshgrid for streaming (reused every tick)
x_arr = np.arange(1, NX-1)
y_arr = np.arange(1, NY-1)
XX, YY = np.meshgrid(x_arr, y_arr, indexing='ij')   # (NX-2, NY-2)

# Precompute lid correction per direction (uses global RHO approximation)
lid_cor = np.zeros(19, dtype=np.int64)
for q in range(19):
    lid_cor[q] = 2 * W_int[q] * RHO * 3 * int(EX[q]) * int(U_LID) // (36 * SCALE)

print(f"LID-DRIVEN CAVITY WITH GHOST — VECTORIZED")
print(f"Grid: {NX}x{NY}, fluid: {L}x{L}, Re = {Re:.1f}")
print(f"Ghost = 2^20, channel m[{CH}]")
print()


def make_eq_vec(rho, jx, jy):
    """Vectorized equilibrium. All inputs shape (H, W). Returns (H, W, 19)."""
    ux = jx * SCALE // np.where(rho != 0, rho, np.int64(1))
    uy = jy * SCALE // np.where(rho != 0, rho, np.int64(1))
    usq = ux*ux + uy*uy                                # (H, W)
    cu  = ux[..., np.newaxis] * EX + uy[..., np.newaxis] * EY  # (H, W, 19)
    r   = rho[..., np.newaxis]                         # (H, W, 1)
    u   = usq[..., np.newaxis]
    feq = (W_int * r // 36
         + W_int * r * 3 * cu // (36 * SCALE)
         + W_int * r * 9 * cu * cu // (36 * 2 * SCALE * SCALE)
         - W_int * r * 3 * u  // (36 * 2 * SCALE * SCALE))
    feq[..., 0] = rho - feq[..., 1:].sum(axis=-1)
    return feq


def step(f):
    """One tick: vectorized collision + streaming."""
    # ---- COLLISION (vectorized over all fluid cells) ----
    fluid = f[1:-1, 1:-1]                             # (NX-2, NY-2, 19)

    # Forward MRT transform: m[x,y,k] = sum_q M[k,q] * f[x,y,q]
    m = fluid @ M.T                                    # (NX-2, NY-2, 19)

    rho = m[..., 0]                                    # row 0 = density
    jx  = m[..., 1]                                    # row 1 = x-momentum
    jy  = m[..., 2]                                    # row 2 = y-momentum

    feq  = make_eq_vec(rho, jx, jy)
    meq  = feq @ M.T

    m_new = m.copy()
    m_new[..., 4:18] = ((OD-ON)*m[..., 4:18] + ON*meq[..., 4:18]) // OD
    # m_new[..., CH] untouched — ghost passthrough

    # Inverse MRT transform: split physical (k=0..17) + ghost (k=CH=18)
    # fc[x,y,q] = (sum_{k<18} Minv_s[q,k]*m_new[x,y,k] + LCD//2) // LCD
    #           + Minv_s[q,CH] * m_new[x,y,CH] // LCD
    phys = m_new[..., :18] @ Minv_s[:, :18].T         # (NX-2, NY-2, 19)
    fc_interior = (phys + LCD//2) // LCD
    fc_interior += m_new[..., CH:CH+1] * Minv_s[:, CH] // LCD

    fc = np.zeros_like(f)
    fc[1:-1, 1:-1] = fc_interior

    # ---- STREAMING (loop over 19 directions, vectorized body) ----
    fn = np.zeros_like(f)
    for q in range(19):
        dx_ = int(EX[q]); dy_ = int(EY[q])
        oq  = int(opp[q])
        src = fc[1:-1, 1:-1, q]                        # (NX-2, NY-2)

        dest_x = XX + dx_
        dest_y = YY + dy_

        side   = (dest_x <= 0) | (dest_x >= NX-1)
        bottom = ~side & (dest_y <= 0)
        lid    = ~side & ~bottom & (dest_y >= NY-1)
        free   = ~side & ~bottom & ~lid

        # Bounce-back: sides + bottom
        bounce = side | bottom
        if bounce.any():
            np.add.at(fn[:, :, oq], (XX[bounce], YY[bounce]), src[bounce])

        # Moving lid: bounce-back with momentum correction
        if lid.any():
            np.add.at(fn[:, :, oq], (XX[lid], YY[lid]),
                      (src - lid_cor[q])[lid])

        # Free streaming
        if free.any():
            np.add.at(fn[:, :, q], (dest_x[free], dest_y[free]), src[free])

    return fn


# ---- INITIALISE ----
f = np.zeros((NX, NY, 19), dtype=np.int64)
for x in range(NX):
    for y in range(NY):
        f[x, y] = np.array([W_int[q]*RHO//36 for q in range(19)], dtype=np.int64)
        f[x, y, 0] = RHO - f[x, y, 1:].sum()

# Inject ghost at center
cx, cy = NX//2, NY//2
mc = M @ f[cx, cy]
mc[CH] = GHOST * norms[CH]
for q in range(19):
    phys = np.int64(0)
    for k in range(18): phys += Minv_s[q, k] * mc[k]
    f[cx, cy, q] = (phys + LCD//2)//LCD + Minv_s[q, CH]*mc[CH]//LCD

# ---- RUN ----
t0 = time.time()
TICKS = 5000

for tick in range(TICKS + 1):
    if tick % 1000 == 0:
        gt = sum(int((M[CH] @ f[x, y])) for x in range(1,NX-1) for y in range(1,NY-1)) // int(norms[CH])
        ux_max = 0
        for x in range(1,NX-1):
            for y in range(1,NY-1):
                fi = f[x,y]; r = int(fi.sum())
                if r > 0: ux_max = max(ux_max, abs(int((EX*fi).sum())*int(SCALE)//r))
        print(f"  Tick {tick:>5d}: |ux|_max={ux_max}/{SCALE}  ghost={gt}({gt/float(GHOST)*100:.2f}%)  [{time.time()-t0:.1f}s]")
    f = step(f)

# ---- RESULTS ----
ux_f = np.zeros((NX, NY), dtype=np.int64)
uy_f = np.zeros((NX, NY), dtype=np.int64)
gh_f = np.zeros((NX, NY), dtype=np.int64)
for x in range(1,NX-1):
    for y in range(1,NY-1):
        fi = f[x,y]; r = int(fi.sum())
        if r > 0:
            ux_f[x,y] = int((EX*fi).sum())*int(SCALE)//r
            uy_f[x,y] = int((EY*fi).sum())*int(SCALE)//r
        gh_f[x,y] = int((M[CH] @ fi)) // int(norms[CH])

print()
print("="*56)
print("VELOCITY FIELD  (arrows, every cell, y top→bottom)")
print("="*56)
for y in range(NY-1, -1, -1):
    row = ""
    for x in range(NX):
        if x == 0 or x == NX-1 or y == 0:
            row += "|"
        elif y == NY-1:
            row += ">"
        else:
            ux = int(ux_f[x,y]); uy = int(uy_f[x,y])
            mag = (ux**2+uy**2)**0.5
            if mag < 3: row += "."
            elif abs(ux) > abs(uy)*2: row += (">" if ux>0 else "<")
            elif abs(uy) > abs(ux)*2: row += ("^" if uy>0 else "v")
            elif ux>0 and uy>0: row += "/"
            elif ux>0 and uy<0: row += "\\"
            elif ux<0 and uy>0: row += "\\"
            else: row += "/"
    lid = " <-- LID" if y == NY-1 else ""
    print(f"  y={y:>2d}: {row}{lid}")

print()
print("GHOST FIELD  (intensity map)")
gmax = max(abs(gh_f).max(), 1)
chars = " .:-=+*#%@"
for y in range(NY-1, -1, -1):
    row = ""
    for x in range(NX):
        if x==0 or x==NX-1 or y==0 or y==NY-1:
            row += "|"
        else:
            idx = min(len(chars)-1, int(abs(gh_f[x,y])/gmax*(len(chars)-1)))
            row += chars[idx]
    print(f"  y={y:>2d}: {row}")

gt_final = sum(int((M[CH] @ f[x,y])) for x in range(1,NX-1) for y in range(1,NY-1)) // int(norms[CH])
print()
print(f"Ghost conservation: {gt_final} / {GHOST} = {gt_final/float(GHOST)*100:.4f}%")

print()
print("Vertical centerline ux  (x=NX//2, for Ghia comparison):")
xm = NX//2
print(f"  {'y':>3s}  {'ux':>8s}  {'ux/U_lid':>10s}")
for y in range(NY):
    print(f"  {y:>3d}  {int(ux_f[xm,y]):>8d}  {int(ux_f[xm,y])/float(U_LID):>10.4f}")
