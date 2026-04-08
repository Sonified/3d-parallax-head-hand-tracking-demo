"""
LID-DRIVEN CAVITY with ghost data swirling inside.
The final stamp.

21x21 cavity (19x19 fluid cells), moving lid at top, bounce-back walls.
Ghost injected at center, rides the vortex.

For comparison against Ghia et al. (1982) centerline velocity profiles.
"""
import numpy as np

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
W_int = np.array([12,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1], dtype=np.int64)
EX = np.array([0,1,-1,0,0,0,0,1,-1,1,-1,1,-1,1,-1,0,0,0,0], dtype=np.int64)
EY = np.array([0,0,0,1,-1,0,0,1,1,-1,-1,0,0,0,0,1,-1,1,-1], dtype=np.int64)
EZ = np.array([0,0,0,0,0,1,-1,0,0,0,0,1,1,-1,-1,1,1,-1,-1], dtype=np.int64)
norms = np.array([np.sum(W_int * M[k]**2) for k in range(19)], dtype=np.int64)
LCD = int(np.lcm.reduce(norms))
Minv_s = np.zeros((19,19), dtype=np.int64)
for q in range(19):
    for k in range(19):
        Minv_s[q,k] = W_int[q]*M[k,q]*(LCD//norms[k])

opp = np.zeros(19, dtype=int)
for q in range(19):
    for qq in range(19):
        if EX[qq]==-EX[q] and EY[qq]==-EY[q] and EZ[qq]==-EZ[q]: opp[q]=qq

CH = 18
NX = 21; NY = 21; NZ = 1
SCALE = 10000
RHO = np.int64(10**9)
ON = np.int64(10); OD = np.int64(13)
U_LID = np.int64(1000)  # lid velocity = 1000/10000 = 0.1 lu
GHOST = np.int64(1 << 20)

nu = (1/3)*(float(OD)/float(ON)-0.5)
L = NX - 2  # 19
Re = (U_LID/SCALE) * L / nu

print(f"LID-DRIVEN CAVITY WITH GHOST")
print(f"Grid: {NX}x{NY}x{NZ}, cavity = {L}x{L}")
print(f"Lid velocity: {U_LID}/{SCALE} = {U_LID/SCALE:.2f} lu")
print(f"nu = {nu:.4f}, Re = {Re:.1f}")
print(f"Ghost = 2^20 at center ({NX//2},{NY//2},0)")
print()

def make_eq(rho, ux, uy, uz):
    f=np.zeros(19,dtype=np.int64)
    usq=ux*ux+uy*uy+uz*uz
    for q in range(19):
        cu=EX[q]*ux+EY[q]*uy+EZ[q]*uz
        f[q]=W_int[q]*rho//36+W_int[q]*rho*3*cu//(36*SCALE)+W_int[q]*rho*9*cu*cu//(36*2*SCALE*SCALE)-W_int[q]*rho*3*usq//(36*2*SCALE*SCALE)
    f[0]=rho-np.sum(f[1:])
    return f

f = np.zeros((NX,NY,NZ,19), dtype=np.int64)
for x in range(NX):
    for y in range(NY):
        f[x,y,0] = make_eq(RHO, 0, 0, 0)

# Inject ghost at center
cx, cy = NX//2, NY//2
mc = M @ f[cx,cy,0]; mc[CH] = GHOST*norms[CH]
for q in range(19):
    phys=np.int64(0)
    for k in range(18): phys+=Minv_s[q,k]*mc[k]
    f[cx,cy,0,q]=(phys+LCD//2)//LCD + Minv_s[q,CH]*mc[CH]//LCD

import time
t0 = time.time()

for tick in range(10001):
    fc = np.zeros_like(f); fn = np.zeros_like(f)

    for x in range(1, NX-1):
        for y in range(1, NY-1):
            fi = f[x,y,0]; rho = int(np.sum(fi))
            if rho == 0: rho = 1
            jx = int(np.sum(EX*fi)); jy = int(np.sum(EY*fi))
            feq = make_eq(rho, jx*SCALE//rho, jy*SCALE//rho, 0)
            m = M@fi; meq = M@feq; m_new = m.copy()
            for k in range(4,18): m_new[k]=((OD-ON)*m[k]+ON*meq[k])//OD
            gm = m_new[CH]
            for q in range(19):
                phys=np.int64(0)
                for kk in range(18): phys+=Minv_s[q,kk]*m_new[kk]
                fc[x,y,0,q]=(phys+LCD//2)//LCD + Minv_s[q,CH]*gm//LCD

    for x in range(1, NX-1):
        for y in range(1, NY-1):
            for q in range(19):
                dx = x + int(EX[q]); dy = y + int(EY[q])

                if dx <= 0 or dx >= NX-1:
                    # Side walls: standard bounce-back
                    fn[x,y,0,opp[q]] = fc[x,y,0,q]
                elif dy <= 0:
                    # Bottom wall: standard bounce-back
                    fn[x,y,0,opp[q]] = fc[x,y,0,q]
                elif dy >= NY-1:
                    # LID (top wall): moving bounce-back
                    lid_correction = 2 * W_int[q] * RHO * 3 * int(EX[q]) * int(U_LID) // (36 * SCALE)
                    fn[x,y,0,opp[q]] = fc[x,y,0,q] - lid_correction
                else:
                    fn[dx,dy,0,q] = fc[x,y,0,q]
    f = fn

    if tick % 2000 == 0:
        ghost_total = 0
        ux_max = 0; uy_max = 0
        for x in range(1,NX-1):
            for y in range(1,NY-1):
                fi = f[x,y,0]; rho = int(np.sum(fi))
                if rho > 0:
                    ux = abs(int(np.sum(EX*fi))*SCALE//rho)
                    uy = abs(int(np.sum(EY*fi))*SCALE//rho)
                    ux_max = max(ux_max, ux)
                    uy_max = max(uy_max, uy)
                ghost_total += int(np.sum(M[CH]*fi))
        ghost_dec = ghost_total // int(norms[CH])
        elapsed = time.time()-t0
        print(f"  Tick {tick:>5d}: |ux|_max={ux_max}/{SCALE} |uy|_max={uy_max}/{SCALE}  ghost={ghost_dec}({ghost_dec/float(GHOST)*100:.2f}%)  [{elapsed:.0f}s]")

# Final: flow field and ghost field
print()
print("="*60)
print("CAVITY FLOW FIELD (ux at z=0, shown as arrows)")
print("="*60)

ux_field = np.zeros((NX,NY))
uy_field = np.zeros((NX,NY))
ghost_field = np.zeros((NX,NY))

for x in range(1,NX-1):
    for y in range(1,NY-1):
        fi = f[x,y,0]; rho = int(np.sum(fi))
        if rho > 0:
            ux_field[x,y] = int(np.sum(EX*fi))*SCALE//rho
            uy_field[x,y] = int(np.sum(EY*fi))*SCALE//rho
        ghost_field[x,y] = int(np.sum(M[CH]*fi)) // int(norms[CH])

print()
print("Velocity arrows (every 2 cells):")
for y in range(NY-1, -1, -1):
    if y % 2 != 0 and y > 0 and y < NY-1: continue
    row = ""
    for x in range(NX):
        if x % 2 != 0 and x > 0 and x < NX-1: continue
        if x == 0 or x == NX-1 or y == 0:
            row += " | "
        elif y == NY-1:
            row += " >>>"
        else:
            ux = ux_field[x,y]; uy = uy_field[x,y]
            mag = (ux**2 + uy**2)**0.5
            if mag < 5:
                row += " . "
            elif abs(ux) > abs(uy) * 2:
                row += " > " if ux > 0 else " < "
            elif abs(uy) > abs(ux) * 2:
                row += " ^ " if uy > 0 else " v "
            elif ux > 0 and uy > 0: row += " / "
            elif ux > 0 and uy < 0: row += " \\ "
            elif ux < 0 and uy > 0: row += " / "
            else: row += " \\ "
    lid_mark = " <-- LID" if y == NY-1 else ""
    print(f"  y={y:>2d}: {row}{lid_mark}")

print()
print("Ghost field (m[18] decoded, every 2 cells):")
gmax = max(abs(ghost_field.max()), abs(ghost_field.min()), 1)
chars = " .:-=+*#%@"
for y in range(NY-1, -1, -1):
    if y % 2 != 0 and y > 0 and y < NY-1: continue
    row = ""
    for x in range(NX):
        if x % 2 != 0 and x > 0 and x < NX-1: continue
        g = ghost_field[x,y]
        if x == 0 or x == NX-1 or y == 0 or y == NY-1:
            row += " | "
        else:
            idx = min(len(chars)-1, int(abs(g)/gmax*(len(chars)-1)))
            row += f" {chars[idx]} "
    print(f"  y={y:>2d}: {row}")

ghost_total = sum(int(np.sum(M[CH]*f[x,y,0])) for x in range(1,NX-1) for y in range(1,NY-1))
ghost_dec = ghost_total // int(norms[CH])
print()
print(f"Ghost conservation: {ghost_dec} / {GHOST} = {ghost_dec/float(GHOST)*100:.4f}%")

print()
print("Vertical centerline ux (x=NX//2, for Ghia et al. comparison):")
x_mid = NX//2
print(f"  {'y':>3s}  {'ux':>8s}  {'ux/U_lid':>10s}")
for y in range(NY):
    ux = int(ux_field[x_mid, y])
    print(f"  {y:>3d}  {ux:>8d}  {ux/float(U_LID):>10.4f}")
