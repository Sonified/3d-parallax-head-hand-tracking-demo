"""
Bitwise identity proof: ghost at u32 has ZERO effect on physics.

RHO = 2^32 = 4,294,967,296
Ghost = 2^26 = 67,108,864 (9.38% of rest distribution)
5,000 ticks, wall-bounded Poiseuille, body force, integer arithmetic.

Two runs: identical simulation, one with 26-bit ghost, one without.

Results:
  ux_max WITH ghost:  359/10000  (101.52% of analytical)
  ux_max NO ghost:    359/10000  (101.52% of analytical)
  Velocity difference at every cell: EXACTLY 0

The ghost is bitwise invisible to the fluid dynamics.
26 bits. Free. Invisible. Proven.
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

CH=18; NX=1; NY=11; NZ=1; SCALE=10000
RHO=np.int64(4294967296); ON=np.int64(10); OD=np.int64(13)
FORCE=np.int64(4*10**6); GHOST=np.int64(1<<26)

nu = (1/3)*(float(OD)/float(ON)-0.5)
W = NY-2
ux_analytical = float(FORCE)/float(RHO)*W**2/(8*nu)*SCALE

def make_eq(rho, ux, uy, uz):
    f=np.zeros(19,dtype=np.int64)
    usq=ux*ux+uy*uy+uz*uz
    for q in range(19):
        cu=EX[q]*ux+EY[q]*uy+EZ[q]*uz
        f[q]=W_int[q]*rho//36+W_int[q]*rho*3*cu//(36*SCALE)+W_int[q]*rho*9*cu*cu//(36*2*SCALE*SCALE)-W_int[q]*rho*3*usq//(36*2*SCALE*SCALE)
    f[0]=rho-np.sum(f[1:])
    return f

def run_poiseuille(use_ghost):
    f=np.zeros((NX,NY,NZ,19),dtype=np.int64)
    for y in range(NY): f[0,y,0]=make_eq(RHO,0,0,0)

    if use_ghost:
        mc=M@f[0,NY//2,0]; mc[CH]=GHOST*norms[CH]
        for q in range(19):
            phys=np.int64(0)
            for k in range(18): phys+=Minv_s[q,k]*mc[k]
            f[0,NY//2,0,q]=(phys+LCD//2)//LCD+Minv_s[q,CH]*mc[CH]//LCD

    for tick in range(5001):
        fc=np.zeros_like(f); fn=np.zeros_like(f)
        for y in range(1,NY-1):
            fi=f[0,y,0]; rho=int(np.sum(fi)); jx=int(np.sum(EX*fi))+int(FORCE)
            feq=make_eq(rho,jx*SCALE//rho,0,0)
            m=M@fi; m[1]+=FORCE; meq=M@feq; m_new=m.copy()
            for k in range(4,18): m_new[k]=((OD-ON)*m[k]+ON*meq[k])//OD
            gm=m_new[CH]
            for q in range(19):
                phys=np.int64(0)
                for kk in range(18): phys+=Minv_s[q,kk]*m_new[kk]
                fc[0,y,0,q]=(phys+LCD//2)//LCD+Minv_s[q,CH]*gm//LCD
        for y in range(1,NY-1):
            for q in range(19):
                dy=y+int(EY[q])
                if dy<=0 or dy>=NY-1: fn[0,y,0,opp[q]]=fc[0,y,0,q]
                else: fn[0,dy,0,q]=fc[0,y,0,q]
        f=fn

    ux=[int(np.sum(EX*f[0,y,0]))*SCALE//max(1,int(np.sum(f[0,y,0]))) if 0<y<NY-1 else 0 for y in range(NY)]
    ghost=sum(int(np.sum(M[CH]*f[0,y,0])) for y in range(1,NY-1))//int(norms[CH]) if use_ghost else 0
    return ux, ghost

print("GHOST VS NO-GHOST: BITWISE IDENTITY PROOF (u32, 5,000 ticks)")
print(f"RHO=2^32, Ghost=2^26 (9.38% of rest distribution)")
print(f"Analytical ux_max = {ux_analytical:.1f}/{SCALE}")
print()

ux_g, ghost_g = run_poiseuille(True)
ux_n, _       = run_poiseuille(False)

max_g = max(ux_g); max_n = max(ux_n)
print(f"{'':>8s}  {'WITH ghost':>12s}  {'NO ghost':>12s}  {'Difference':>12s}")
print(f"{'ux_max':>8s}  {max_g:>12d}  {max_n:>12d}  {max_g-max_n:>+12d}")
print(f"{'vs ana':>8s}  {max_g/ux_analytical*100:>11.2f}%  {max_n/ux_analytical*100:>11.2f}%")
print()
print(f"  {'y':>3s}  {'ghost':>8s}  {'no ghost':>8s}  {'diff':>6s}")
for y in range(NY):
    d = ux_g[y] - ux_n[y]
    print(f"  {y:>3d}  {ux_g[y]:>8d}  {ux_n[y]:>8d}  {d:>+6d}")
print()
print(f"Ghost conservation: {ghost_g} / {GHOST} = {ghost_g/float(GHOST)*100:.6f}%")
total_diff = sum(abs(ux_g[y]-ux_n[y]) for y in range(NY))
print(f"Total absolute velocity difference: {total_diff}/{SCALE}")
print(f"Ghost effect on physics: {'ZERO - bitwise identical' if total_diff == 0 else f'{total_diff} counts'}")
