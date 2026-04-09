"""
The ghost in different bit-depth worlds.
Same physics. Same grid. Different precision.
How does the stamp hold up?
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
LCD = int(np.lcm.reduce(norms))  # 144
Minv_s = np.zeros((19,19), dtype=np.int64)
for q in range(19):
    for k in range(19):
        Minv_s[q,k] = W_int[q]*M[k,q]*(LCD//norms[k])

CH = 18
NX=3; NY=9; NZ=3  # 81 cells
N_CELLS = NX*NY*NZ
ON=10; OD=13
SCALE=1000

sd = np.zeros((NX,NY,NZ,19,3), dtype=int)
for x in range(NX):
    for y in range(NY):
        for z in range(NZ):
            for q in range(19):
                sd[x,y,z,q]=[(x+int(EX[q]))%NX,(y+int(EY[q]))%NY,(z+int(EZ[q]))%NZ]

def make_eq(rho, ux, uy, uz):
    f=np.zeros(19,dtype=np.int64)
    usq=ux*ux+uy*uy+uz*uz
    for q in range(19):
        cu=EX[q]*ux+EY[q]*uy+EZ[q]*uz
        f[q]=W_int[q]*rho//36+W_int[q]*rho*3*cu//(36*SCALE)+W_int[q]*rho*9*cu*cu//(36*2*SCALE*SCALE)-W_int[q]*rho*3*usq//(36*2*SCALE*SCALE)
    f[0]=rho-np.sum(f[1:])
    return f

def mrt_tick(f):
    fn=np.zeros_like(f); fc=np.zeros_like(f)
    for x in range(NX):
        for y in range(NY):
            for z in range(NZ):
                fi=f[x,y,z]; rho=int(np.sum(fi))
                if rho == 0: rho = 1
                feq=make_eq(rho,int(np.sum(EX*fi))*SCALE//rho,int(np.sum(EY*fi))*SCALE//rho,int(np.sum(EZ*fi))*SCALE//rho)
                m=M@fi; meq=M@feq; m_new=m.copy()
                for k in range(4,18): m_new[k]=((OD-ON)*m[k]+ON*meq[k])//OD
                gm=m_new[CH]
                for q in range(19):
                    phys=np.int64(0)
                    for kk in range(18): phys+=Minv_s[q,kk]*m_new[kk]
                    fc[x,y,z,q]=(phys+LCD//2)//LCD + Minv_s[q,CH]*gm//LCD
    for x in range(NX):
        for y in range(NY):
            for z in range(NZ):
                for q in range(19):
                    dx,dy,dz=sd[x,y,z,q]; fn[dx,dy,dz,q]=fc[x,y,z,q]
    return fn

import math

print("THE GHOST IN DIFFERENT BIT-DEPTH WORLDS")
print(f"Grid: {NX}x{NY}x{NZ} = {N_CELLS} cells, periodic")
print(f"MRT with correct equilibrium, m[{CH}] passthrough")
print(f"100 ticks each")
print()

# For each bit depth:
# RHO = largest value where each f[q] fits in the bit depth
# f[q] ≈ W[q]*RHO/36. Largest W=12, so f[0] ≈ RHO/3.
# Need f[0] < 2^bits, so RHO < 3 * 2^bits.
# But also need room for ghost perturbation: max ±2*ghost
# So f[q] + 2*ghost < 2^bits and f[q] - 2*ghost > 0

# Ghost max: smallest f[q] = W=1 direction ≈ RHO/36
# Need RHO/36 - 2*ghost > 0 → ghost < RHO/72
# And ghost must be multiple of... nothing, since norms[18]=16 divides LCD exactly

results = []

for bits, label in [(8,"u8"), (10,"u10"), (12,"u12"), (16,"u16"), (20,"u20"), (24,"u24"), (32,"u32")]:
    max_f = (1 << bits) - 1
    RHO = max_f * 36 // 12  # ensure f[0] = 12*RHO/36 ≤ max_f
    
    # Ghost: use ~25% of smallest distribution (RHO/36) as ghost headroom
    ghost_max = RHO // 144  # conservative
    if ghost_max < 1:
        ghost_max = 1
    
    ghost_bits = int(math.log2(ghost_max)) if ghost_max > 1 else 0
    GHOST = ghost_max  # use maximum ghost for this bit depth
    
    # Per-cell after spreading to 81 cells
    per_cell = GHOST // N_CELLS if GHOST >= N_CELLS else 0
    stamp_bits = int(math.log2(per_cell)) if per_cell > 1 else 0
    
    # Actually run it
    f = np.zeros((NX,NY,NZ,19), dtype=np.int64)
    for x in range(NX):
        for y in range(NY):
            for z in range(NZ):
                f[x,y,z] = make_eq(RHO, 0, 2, 0)  # gentle y-flow
    
    # Inject at center
    cx,cy,cz = NX//2, NY//2, NZ//2
    mc = M @ f[cx,cy,cz]
    mc[CH] = GHOST * int(norms[CH])
    for q in range(19):
        phys = np.int64(0)
        for k in range(18): phys += Minv_s[q,k]*mc[k]
        f[cx,cy,cz,q] = (phys+LCD//2)//LCD + Minv_s[q,CH]*mc[CH]//LCD
    
    # Verify no overflow
    f_max = int(np.max(np.abs(f)))
    f_min = int(np.min(f))
    overflow = f_max > max_f or f_min < 0
    
    # Run 100 ticks
    initial_total = int(np.sum(M[CH] @ f.reshape(N_CELLS,19).T)) // int(norms[CH])
    
    stable = True
    for t in range(100):
        f = mrt_tick(f)
        # Check for blowup
        if int(np.max(np.abs(f))) > max_f * 10:
            stable = False
            break
    
    if stable:
        final_total = int(np.sum(M[CH] @ f.reshape(N_CELLS,19).T)) // int(norms[CH])
        conservation = final_total / float(initial_total) * 100 if initial_total != 0 else 0
        
        # Read per-cell values after equilibration
        per_cell_actual = final_total // N_CELLS if N_CELLS > 0 else 0
    else:
        final_total = 0
        conservation = 0
        per_cell_actual = 0
    
    results.append((label, bits, RHO, GHOST, ghost_bits, stamp_bits, 
                     initial_total, final_total, conservation, overflow, stable, per_cell_actual))

# Print results
print(f"{'Depth':>6s}  {'RHO':>12s}  {'Ghost':>10s}  {'G bits':>6s}  {'Stamp':>6s}  {'Init':>10s}  {'Final':>10s}  {'Conserv':>8s}  {'Cell':>8s}  {'OK':>4s}")
print("-"*100)

for label, bits, RHO, GHOST, gb, sb, init, final, cons, overflow, stable, pca in results:
    ok = "YES" if stable and cons > 99 and not overflow else ("OVF" if overflow else ("BLOW" if not stable else "LOW"))
    print(f"{label:>6s}  {RHO:>12d}  {GHOST:>10d}  {gb:>6d}  {sb:>6d}  {init:>10d}  {final:>10d}  {cons:>7.2f}%  {pca:>8d}  {ok:>4s}")

print()
print("INTERPRETATION:")
print()
for label, bits, RHO, GHOST, gb, sb, init, final, cons, overflow, stable, pca in results:
    if stable and cons > 99:
        levels = pca if pca > 0 else 1
        useful_bits = int(math.log2(levels)) if levels > 1 else 0
        print(f"  {label}: Ghost survives with {gb} bits injected, {useful_bits} bits per cell after stamp")
        print(f"         {levels} distinguishable levels per cell. {N_CELLS}x redundancy.")
        if useful_bits >= 1:
            print(f"         Could encode: {'color' if useful_bits >= 8 else 'team ID' if useful_bits >= 3 else 'boolean flag'} ({useful_bits} bits)")
        print()
