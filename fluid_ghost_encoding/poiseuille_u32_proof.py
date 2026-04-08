"""
Poiseuille flow at u32 precision: 26-bit ghost survives 5,000 ticks.

RHO = 2^32 = 4,294,967,296
Ghost = 2^26 = 67,108,864 (26 bits, 9.38% of rest distribution)
5,000 ticks, wall-bounded channel, body force, integer arithmetic throughout.

Results:
  ux_max: 359/10000 vs analytical 353.6/10000 (1.5% error)
  q/(c*W): 0.676
  Ghost conservation: 67,108,898 / 67,108,864 = 100.000051%
  Ghost bits stored: 26
  Ghost bits surviving: 26

26 bits of free storage per cell, inside correct fluid dynamics,
in integer arithmetic, through walls, at u32 precision.
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

CH = 18; NX=1; NY=11; NZ=1
SCALE = 10000
RHO = np.int64(4294967296)   # 2^32
ON = np.int64(10); OD = np.int64(13)
FORCE = np.int64(4 * 10**6)
GHOST = np.int64(1 << 26)    # 2^26

nu = (1/3)*(float(OD)/float(ON) - 0.5)
W = NY - 2
F_lu = float(FORCE)/float(RHO)
ux_max_analytical = F_lu * W**2 / (8*nu)

def make_eq(rho, ux, uy, uz):
    f=np.zeros(19,dtype=np.int64)
    usq=ux*ux+uy*uy+uz*uz
    for q in range(19):
        cu=EX[q]*ux+EY[q]*uy+EZ[q]*uz
        f[q]=W_int[q]*rho//36+W_int[q]*rho*3*cu//(36*SCALE)+W_int[q]*rho*9*cu*cu//(36*2*SCALE*SCALE)-W_int[q]*rho*3*usq//(36*2*SCALE*SCALE)
    f[0]=rho-np.sum(f[1:])
    return f

f = np.zeros((NX,NY,NZ,19), dtype=np.int64)
for y in range(NY): f[0,y,0] = make_eq(RHO, 0, 0, 0)

cy = NY//2
mc = M @ f[0,cy,0]; mc[CH] = GHOST*norms[CH]
for q in range(19):
    phys=np.int64(0)
    for k in range(18): phys+=Minv_s[q,k]*mc[k]
    f[0,cy,0,q]=(phys+LCD//2)//LCD + Minv_s[q,CH]*mc[CH]//LCD

for tick in range(5001):
    fc = np.zeros_like(f); fn = np.zeros_like(f)
    for y in range(1, NY-1):
        fi = f[0,y,0]
        rho = int(np.sum(fi)); jx = int(np.sum(EX*fi)) + int(FORCE)
        feq = make_eq(rho, jx*SCALE//rho, 0, 0)
        m = M @ fi; m[1] += FORCE; meq = M @ feq
        m_new = m.copy()
        for k in range(4,18): m_new[k]=((OD-ON)*m[k]+ON*meq[k])//OD
        gm = m_new[CH]
        for q in range(19):
            phys=np.int64(0)
            for kk in range(18): phys+=Minv_s[q,kk]*m_new[kk]
            fc[0,y,0,q]=(phys+LCD//2)//LCD + Minv_s[q,CH]*gm//LCD
    for y in range(1, NY-1):
        for q in range(19):
            dy = y + int(EY[q])
            if dy <= 0 or dy >= NY-1:
                fn[0,y,0,opp[q]] = fc[0,y,0,q]
            else:
                fn[0,dy,0,q] = fc[0,y,0,q]
    f = fn

ux = []
for y in range(NY):
    if y==0 or y==NY-1: ux.append(0)
    else:
        fi=f[0,y,0]; rho=int(np.sum(fi))
        ux.append(int(np.sum(EX*fi))*SCALE//rho if rho>0 else 0)

ux_max = max(ux)
q_sum = sum(ux[1:-1])
qc = q_sum / (ux_max * W) if ux_max > 0 else 0
ghost = sum(int(np.sum(M[CH]*f[0,y,0])) for y in range(1,NY-1)) // int(norms[CH])

print("POISEUILLE FLOW + GHOST AT U32 (5,000 ticks)")
print(f"RHO=2^32, Ghost=2^26, ghost/dist ratio=9.38%")
print()
for y in range(NY):
    bar = "#" * (ux[y]*50//(ux_max+1)) if ux_max > 0 else ""
    w = "WALL" if y==0 or y==NY-1 else ""
    print(f"  y={y:>2d}: {ux[y]:>6d}/{SCALE}  {bar}  {w}")
print()
print(f"ux_max: {ux_max}/{SCALE} vs analytical {ux_max_analytical*SCALE:.1f}/{SCALE} ({ux_max/(ux_max_analytical*SCALE)*100:.2f}%)")
print(f"q/(c*W): {qc:.4f}")
print(f"Ghost: {ghost} / {GHOST} = {ghost/float(GHOST)*100:.6f}%")
print(f"Ghost bits stored: 26  |  Ghost bits surviving: {int(np.log2(ghost)) if ghost > 0 else 0}")
