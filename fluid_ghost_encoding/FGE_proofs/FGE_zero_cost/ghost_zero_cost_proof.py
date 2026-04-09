"""
Proof: The MRT collision step IS the ghost encode/decode.
No additional operations. Zero extra cost.

The standard MRT collision pipeline:
  1. m = M @ f          (transform to moment space)
  2. relax physical m    (collision)
  3. ghost m unchanged   (passthrough: relaxation rate = 0)
  4. f = M_inv @ m       (transform back)
  5. stream f            (copy f_i to neighbors)

Claim: step 1 IS the decode. Step 4 IS the encode.
Ghost data rides for free inside the collision you're already paying for.
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
EX = np.array([0, 1,-1, 0, 0, 0, 0, 1,-1, 1,-1, 1,-1, 1,-1, 0, 0, 0, 0])
EY = np.array([0, 0, 0, 1,-1, 0, 0, 1, 1,-1,-1, 0, 0, 0, 0, 1,-1, 1,-1])
EZ = np.array([0, 0, 0, 0, 0, 1,-1, 0, 0, 0, 0, 1, 1,-1,-1, 1, 1,-1,-1])

norms = np.diag(M @ np.diag(W) @ M.T)
full_lcd = 144
ghost_channels = list(range(10, 19))
ghost_lcds = {10:4, 11:24, 12:24, 13:24, 14:8, 15:8, 16:8, 17:48, 18:16}

# Precompute scaled inverse
Minv_scaled = np.zeros((19, 19), dtype=np.int64)
for q in range(19):
    for k in range(19):
        Minv_scaled[q, k] = int(W[q]) * int(M[k, q]) * (full_lcd // int(norms[k]))


def int_div(v, d):
    """Integer division with rounding toward nearest."""
    if v >= 0:
        return (v + d // 2) // d
    else:
        return -((-v + d // 2) // d)


def mrt_collide_with_passthrough(f_cell, omega=0.5, rho_target=None):
    """
    Standard MRT collision. Ghost modes pass through unchanged.
    Returns (f_out, moments) — the moments are FREE, already computed.
    """
    # Step 1: M @ f  (this IS the ghost decode — it's inside collision)
    m = M @ f_cell
    
    # Steps 2-3: Relax physical moments, leave ghost modes alone
    # For simplicity, we only relax the stress modes (rows 4-9)
    # Conserved modes (0-3) are untouched
    # Ghost modes (10-18) are untouched (passthrough)
    rho = m[0]
    jx, jy, jz = m[1], m[2], m[3]
    
    # Compute equilibrium for stress modes (simplified)
    # In real code this is the BGK/MRT relaxation
    # For this test we just apply light relaxation to rows 4-9
    for k in range(4, 10):
        m_eq = 0  # simplified: equilibrium stress is ~0 at low velocity
        m[k] = m[k] - int_div(int(omega * 10) * (m[k] - m_eq), 10)
    
    # Ghost modes m[10:18] — UNTOUCHED. Passthrough. Zero ops on them.
    
    # Step 4: M_inv @ m  (this IS the ghost encode — it's inside collision)
    f_raw = Minv_scaled @ m
    f_out = np.array([int_div(int(v), full_lcd) for v in f_raw], dtype=np.int64)
    
    if rho_target is not None:
        f_out[0] = rho_target - np.sum(f_out[1:])
    
    return f_out, m  # Return moments — ghost values are m[10:18]


# ============================================================
# THE TEST: Full collide-stream loop, read ghosts from collision
# ============================================================

N = 16  # 1D grid (x-axis)
rho_base = 500
center = N // 2
test_channel = 12
lcd = ghost_lcds[test_channel]
ghost_val = 42

print("=" * 70)
print("PROOF: MRT COLLISION IS THE GHOST ENCODE/DECODE")
print("=" * 70)
print()
print(f"Grid: {N} cells, 1D (x-axis)")
print(f"Ghost channel: m[{test_channel}] (LCD={lcd})")
print(f"Ghost value: {ghost_val}")
print(f"Base density: {rho_base}")
print()

# Initialize grid at equilibrium
f = np.zeros((N, 19), dtype=np.int64)
for i in range(N):
    for q in range(19):
        f[i, q] = rho_base * int(W[q]) // 36
    f[i, 0] = rho_base - np.sum(f[i, 1:])

# INITIAL INJECTION: modify ghost moment at center during first collision
# This is the ONE TIME you intervene. After this, it's all automatic.
print("--- TICK 0: Initial injection during collision ---")
m_init = M @ f[center]
print(f"  Ghost m[{test_channel}] before injection: {m_init[test_channel]}")
m_init[test_channel] = ghost_val * lcd  # Set the ghost value
print(f"  Ghost m[{test_channel}] after injection:  {m_init[test_channel]} (= {ghost_val} * {lcd})")

# Complete collision (M_inv transform encodes it into distributions)
# This is NOT an extra step. This is the standard collision M_inv @ m.
f_raw = Minv_scaled @ m_init
f[center] = np.array([int_div(int(v), full_lcd) for v in f_raw], dtype=np.int64)
f[center, 0] = rho_base - np.sum(f[center, 1:])

# Verify it's encoded
m_check = M @ f[center]
print(f"  Readback: m[{test_channel}] = {m_check[test_channel]}, decoded = {int_div(int(m_check[test_channel]), lcd)}")
print()

# ============================================================
# RUN COLLIDE-STREAM LOOP
# Zero additional ghost operations. Ghost values read from collision.
# ============================================================

print("--- TICKS 1-5: Collide-stream loop (zero ghost ops) ---")
print()
print(f"  {'Tick':>4s}  {'Operation':>30s}  {'Ghost values (cells around center)':>50s}  {'Total':>8s}")
print(f"  {'----':>4s}  {'------------------------------':>30s}  {'--------------------------------------------------':>50s}  {'--------':>8s}")

# Kernel prediction
K = (W.astype(np.float64) * M[test_channel].astype(np.float64)**2) / float(norms[test_channel])
K_x = {}
for q in range(19):
    dx = int(EX[q])
    K_x[dx] = K_x.get(dx, 0.0) + K[q]

for tick in range(1, 6):
    # ---- STREAM ----
    f_new = np.zeros_like(f)
    for i in range(N):
        for q in range(19):
            src = (i - int(EX[q])) % N
            f_new[i, q] = f[src, q]
    f = f_new
    
    # Read ghost values AFTER streaming, BEFORE collision
    # (This is what m = M @ f gives you at the start of collision)
    ghost_post_stream = {}
    for i in range(N):
        m_i = M @ f[i]
        gv = int(m_i[test_channel])
        if gv != 0:
            ghost_post_stream[i] = gv
    
    total_post_stream = sum(ghost_post_stream.values())
    
    # Format: show cells around center
    cells_str = ""
    for di in range(-3, 4):
        ci = (center + di) % N
        if ci in ghost_post_stream:
            cells_str += f"[{ci}]={ghost_post_stream[ci]:>5d} "
        else:
            cells_str += f"[{ci}]=    . "
    
    print(f"  {tick:>4d}  {'after stream (M@f = free read)':>30s}  {cells_str}  {total_post_stream:>8d}")
    
    # ---- COLLIDE (with passthrough) ----
    # The collision step does M@f (already done above), relaxes physical,
    # leaves ghost alone, does M_inv@m. Ghost data re-encoded automatically.
    
    ghost_moments_from_collision = {}
    for i in range(N):
        f[i], m_collision = mrt_collide_with_passthrough(f[i], omega=0.5, rho_target=rho_base)
        gv = int(m_collision[test_channel])
        if gv != 0:
            ghost_moments_from_collision[i] = gv
    
    total_post_collide = sum(ghost_moments_from_collision.values())
    
    cells_str2 = ""
    for di in range(-3, 4):
        ci = (center + di) % N
        if ci in ghost_moments_from_collision:
            cells_str2 += f"[{ci}]={ghost_moments_from_collision[ci]:>5d} "
        else:
            cells_str2 += f"[{ci}]=    . "
    
    print(f"  {'':>4s}  {'after collide (passthrough)':>30s}  {cells_str2}  {total_post_collide:>8d}")
    print()

print()

# ============================================================
# KERNEL PREDICTION COMPARISON
# ============================================================

print("--- KERNEL PREDICTION vs ACTUAL (tick 1) ---")
print()

# Re-run from scratch, just 1 tick
f2 = np.zeros((N, 19), dtype=np.int64)
for i in range(N):
    for q in range(19):
        f2[i, q] = rho_base * int(W[q]) // 36
    f2[i, 0] = rho_base - np.sum(f2[i, 1:])

# Inject
m_init2 = M @ f2[center]
m_init2[test_channel] = ghost_val * lcd
f_raw2 = Minv_scaled @ m_init2
f2[center] = np.array([int_div(int(v), full_lcd) for v in f_raw2], dtype=np.int64)
f2[center, 0] = rho_base - np.sum(f2[center, 1:])

# Stream
f2_new = np.zeros_like(f2)
for i in range(N):
    for q in range(19):
        src = (i - int(EX[q])) % N
        f2_new[i, q] = f2[src, q]

# Read ghost from M@f (the collision decode step)
print(f"  {'Cell':>6s}  {'Actual (M@f)':>12s}  {'Predicted (K)':>13s}  {'Error':>8s}")
print(f"  {'------':>6s}  {'------------':>12s}  {'-------------':>13s}  {'--------':>8s}")

total_actual = 0
total_predicted = 0
max_error = 0

for i in range(N):
    m_i = M @ f2_new[i]
    actual = int(m_i[test_channel])
    
    # Kernel prediction: sum of K_x[dx] * (ghost_val * lcd) for dx where i = center + dx
    dx = (i - center) % N
    if dx > N // 2:
        dx -= N
    predicted = K_x.get(dx, 0.0) * ghost_val * lcd
    
    if actual != 0 or predicted != 0:
        err = abs(actual - predicted)
        max_error = max(max_error, err)
        total_actual += actual
        total_predicted += predicted
        print(f"  {i:>6d}  {actual:>12d}  {predicted:>13.1f}  {err:>8.1f}")

print()
print(f"  Total actual:    {total_actual}")
print(f"  Total predicted: {total_predicted:.1f}")
print(f"  Max error:       {max_error:.1f}")
print(f"  Kernel match:    {'PASS' if max_error < 0.5 else 'FAIL'}")

print()
print("=" * 70)
print("CONCLUSION")
print("=" * 70)
print()
print("The MRT collision pipeline (M@f -> relax -> M_inv@m) already")
print("computes ghost mode values at every cell every tick as a byproduct")
print("of the forward transform M@f. Under passthrough (ghost relaxation = 0),")
print("the inverse transform M_inv@m re-encodes them into distributions")
print("automatically. Streaming transports them to neighbors.")
print()
print("Additional ghost operations per tick: ZERO.")
print("Additional memory per tick: ZERO.")
print("Additional bandwidth per tick: ZERO.")
print()
print("The ghost data encode, transport, and decode are all free")
print("because they are the MRT collision step itself.")
print()

# ============================================================
# ALL 9 CHANNELS
# ============================================================

print("=" * 70)
print("ALL 9 GHOST CHANNELS: Single-tick kernel match")
print("=" * 70)
print()

all_pass = True
for ch in ghost_channels:
    lcd_ch = ghost_lcds[ch]
    
    # Fresh grid
    fg = np.zeros((N, 19), dtype=np.int64)
    for i in range(N):
        for q in range(19):
            fg[i, q] = rho_base * int(W[q]) // 36
        fg[i, 0] = rho_base - np.sum(fg[i, 1:])
    
    # Inject during collision
    mg = M @ fg[center]
    mg[ch] = ghost_val * lcd_ch
    f_raw_g = Minv_scaled @ mg
    fg[center] = np.array([int_div(int(v), full_lcd) for v in f_raw_g], dtype=np.int64)
    fg[center, 0] = rho_base - np.sum(fg[center, 1:])
    
    # Stream
    fg_new = np.zeros_like(fg)
    for i in range(N):
        for q in range(19):
            src = (i - int(EX[q])) % N
            fg_new[i, q] = fg[src, q]
    
    # Read ghost from M@f (free — inside collision)
    K_ch = (W.astype(np.float64) * M[ch].astype(np.float64)**2) / float(norms[ch])
    K_x_ch = {}
    for q in range(19):
        dx = int(EX[q])
        K_x_ch[dx] = K_x_ch.get(dx, 0.0) + K_ch[q]
    
    max_err = 0
    total = 0
    for i in range(N):
        m_i = M @ fg_new[i]
        actual = int(m_i[ch])
        dx = (i - center) % N
        if dx > N // 2:
            dx -= N
        predicted = K_x_ch.get(dx, 0.0) * ghost_val * lcd_ch
        err = abs(actual - predicted)
        max_err = max(max_err, err)
        total += actual
    
    expected_total = ghost_val * lcd_ch
    conservation = total / expected_total * 100 if expected_total != 0 else 0
    status = "PASS" if max_err < 0.5 else "FAIL"
    if status == "FAIL":
        all_pass = False
    
    # 1D kernel
    k_left = K_x_ch.get(-1, 0)
    k_self = K_x_ch.get(0, 0)
    k_right = K_x_ch.get(1, 0)
    
    print(f"  m[{ch:2d}] LCD={lcd_ch:>2d}  kernel=[{k_left:.4f} | {k_self:.4f} | {k_right:.4f}]  "
          f"total={total:>6d} (expect {expected_total:>6d})  "
          f"conservation={conservation:>7.2f}%  max_err={max_err:.1f}  {status}")

print()
if all_pass:
    print("  ALL 9 CHANNELS: PASS")
    print()
    print("  K_i = W[i] * M[k][i]^2 / d_k")
    print()
    print("  Encode: free (M_inv @ m, inside collision)")
    print("  Transport: free (streaming)")
    print("  Decode: free (M @ f, inside collision)")
    print()
    print("  Total additional cost: ZERO")
else:
    print("  SOME CHANNELS FAILED")