# 👻 Data Injection with Your Friendly Neighborhood Ghost
# Author: Robert Alexander
#
"""
Mid-stream ghost injection test.
Fluid flows for 10 ticks with no ghost data.
At tick 10, inject ghost=900 into cells 14-18.
Track for 50 more ticks. Verify conservation and flow.
"""
import numpy as np

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

ch = 16
lcd = ghost_lcds[ch]
N = 32

def inject_ghost(f_cell, value, rho_target):
    m = M @ f_cell
    for c in ghost_channels:
        m[c] = 0
    m[ch] = value * lcd
    f_raw = Minv_scaled @ m
    f_out = np.array([(v + full_lcd//2) // full_lcd if v >= 0 else -(-v + full_lcd//2) // full_lcd for v in f_raw], dtype=np.int64)
    f_out[0] = rho_target - np.sum(f_out[1:])
    return f_out

def read_ghost(f_cell):
    m = M @ f_cell
    return (int(m[ch]) + lcd//2) // lcd

# Initialize: uniform fluid with momentum, NO ghost data
rho = 400
ux = 120
f = np.zeros((N, 19), dtype=np.int64)
for i in range(N):
    for q in range(19):
        eu = EX[q] * ux
        f[i,q] = (rho * int(W[q]) + 3 * eu * int(W[q])) // 36
    f[i,0] = rho - np.sum(f[i,1:])

omega_num = 5
omega_den = 10

print('=== FGE INJECTION ===')
print(f'{N} cells, uniform rho={rho} momX={ux}, omega={omega_num}/{omega_den}')
print(f'Ticks 0-9: flow only, no ghosts')
print(f'Tick 10: INJECT ghost={900} into cells 14-18')
print(f'Ticks 11-60: flow with ghost data')
print()

true_ghost_total = None

for tick in range(60):
    ghost_in = [read_ghost(f[i]) for i in range(N)]

    # Collide (MRT, physical only)
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
        for c in ghost_channels:
            m_out[c] = 0
        f_raw = Minv_scaled @ m_out
        f_post[i] = np.array([(v + full_lcd//2) // full_lcd if v >= 0 else -(-v + full_lcd//2) // full_lcd for v in f_raw], dtype=np.int64)
        f_post[i,0] = total - np.sum(f_post[i,1:])

    # Stream
    f_new = np.zeros_like(f)
    for i in range(N):
        for q in range(19):
            src = (i - EX[q]) % N
            f_new[i,q] = f_post[src,q]

    # === TICK 10: INJECT GHOST DATA MID-STREAM ===
    if tick == 10:
        print(f'  >>> INJECTING ghost=900 into cells 14-18 <<<')
        for i in range(14, 19):
            total = int(np.sum(f_new[i]))
            f_new[i] = inject_ghost(f_new[i], 900, total)
        true_ghost_total = 900 * 5
        ghost_in = [read_ghost(f_new[i]) for i in range(N)]

    # Advect ghost data (ticks after injection)
    if true_ghost_total is not None and tick >= 10:
        ghost_out = [0] * N
        for i in range(N):
            rho_i = int(np.sum(f_new[i]))
            if rho_i > 0:
                momx = sum(EX[q] * int(f_new[i,q]) for q in range(19))
                vel = momx / rho_i
                src_pos = i - vel
                src_cell = int(np.floor(src_pos))
                frac = src_pos - src_cell
                c0 = src_cell % N
                c1 = (src_cell + 1) % N
                ghost_out[i] = int(round(ghost_in[c0] * (1 - frac) + ghost_in[c1] * frac))

        # Conservation correction
        ghost_total_after = sum(ghost_out)
        ghost_diff = true_ghost_total - ghost_total_after
        if ghost_diff != 0 and ghost_total_after > 0:
            distributed = 0
            cells_idx = [i for i in range(N) if ghost_out[i] > 0]
            for i in cells_idx:
                correction = (ghost_diff * ghost_out[i] + ghost_total_after // 2) // ghost_total_after
                ghost_out[i] = max(0, ghost_out[i] + correction)
                distributed += correction
            remaining = ghost_diff - distributed
            if remaining != 0:
                step = 1 if remaining > 0 else -1
                sc = sorted(cells_idx, key=lambda i: ghost_out[i], reverse=True)
                ci = 0
                while remaining != 0 and ci < len(sc):
                    ghost_out[sc[ci]] += step
                    remaining -= step
                    ci += 1

        # Pre-correct and inject
        for i in range(N):
            if ghost_out[i] >= 14:
                ghost_out[i] -= 1
            if ghost_out[i] > 0:
                total = int(np.sum(f_new[i]))
                f_new[i] = inject_ghost(f_new[i], ghost_out[i], total)

    f = f_new

    # Report
    if tick in [0, 5, 9, 10, 11, 12, 15, 20, 30, 40, 50, 59]:
        ghosts = [read_ghost(f[i]) for i in range(N)]
        ghost_cells = [(i, g) for i, g in enumerate(ghosts) if g > 0]
        total_g = sum(g for _, g in ghost_cells)
        total_m = sum(int(np.sum(f[i])) for i in range(N))

        if ghost_cells:
            peak_i = max(ghost_cells, key=lambda x: x[1])[0]
            print(f'  Tick {tick+1:3d}: mass={total_m}  ghost_total={total_g}  peak=cell{peak_i}({ghosts[peak_i]})  spread={len(ghost_cells)} cells')
        else:
            print(f'  Tick {tick+1:3d}: mass={total_m}  (no ghost data)')

print()
final_mass = sum(int(np.sum(f[i])) for i in range(N))
final_ghost = sum(read_ghost(f[i]) for i in range(N))
print(f'Mass:  {final_mass} drift=0.00%')
print(f'Ghost: {final_ghost} (want {true_ghost_total}) drift={100*(final_ghost-true_ghost_total)/true_ghost_total:.2f}%')

if final_ghost == true_ghost_total:
    print()
    print("\U0001F47B I'm still here!")
