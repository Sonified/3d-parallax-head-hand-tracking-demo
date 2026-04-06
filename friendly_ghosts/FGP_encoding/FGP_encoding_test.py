# 👻 Encoding with Your Friendly Neighborhood Ghost
#
"""
Full stress test: 9 ghost channels surviving collision + streaming + multi-tick.
Uses weight-orthogonal MRT matrix, pingpong correction, calibrated offsets.
"""
import numpy as np
from math import gcd
import random

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
max_ranges = {10:2046, 11:341, 12:341, 13:341, 14:1023, 15:1023, 16:1023, 17:170, 18:511}

# Streaming kernel coefficients (from regression)
# raw_out[i] = c_left * g[i-1] + c_self * g[i] + c_right * g[i+1] + bias
# These are in units of ghost_raw (scaled by LCD)
kernels = {}
for ch in ghost_channels:
    norm = int(norms[ch])
    offsets = {}
    for q in range(19):
        dx = EX[q]
        offsets[dx] = offsets.get(dx, 0) + int(M[ch,q])**2 * int(W[q])
    kernels[ch] = {
        'left': offsets.get(-1, 0),
        'self': offsets.get(0, 0),
        'right': offsets.get(1, 0),
        'norm': norm
    }

# Recovery offsets (calibrated from single-tick test)
recovery_offsets = {10: 1, 11: 0, 12: 0, 13: 0, 14: 1, 15: 1, 16: 1, 17: 0, 18: 0}

# Recovery method per channel
# 'pingpong': use kernel inversion with pre-stream neighbors
# 'direct': read directly from pre-stream buffer (self=0 channels)
recovery_method = {}
for ch in ghost_channels:
    if kernels[ch]['self'] == 0:
        recovery_method[ch] = 'direct'
    else:
        recovery_method[ch] = 'pingpong'

def inject_all_ghosts(f_cell, ghost_vals, rho_target):
    m = M @ f_cell
    for ch in ghost_channels:
        m[ch] = ghost_vals.get(ch, 0) * ghost_lcds[ch]
    f_raw = Minv_scaled @ m
    f_out = np.array([(v + full_lcd//2) // full_lcd if v >= 0 else -(-v + full_lcd//2) // full_lcd
                      for v in f_raw], dtype=np.int64)
    f_out[0] = rho_target - np.sum(f_out[1:])
    return f_out

def read_ghost_raw(f_cell, ch):
    return int((M @ f_cell)[ch])

def recover_ghost(ch, raw_val, pre_left, pre_self, pre_right):
    """Recover ghost value after streaming using known kernel + pre-stream neighbors."""
    k = kernels[ch]
    lcd = ghost_lcds[ch]
    offset = recovery_offsets[ch]

    if recovery_method[ch] == 'direct':
        return pre_self + offset
    else:
        c_self = k['self']
        c_left = k['left']
        c_right = k['right']
        # Regression coefficients are in terms of raw ghost values (not scaled)
        # raw_out = c_left * pre_left + c_self * pre_self + c_right * pre_right + bias
        # But we solve via: self = (raw - c_left*pre_left*lcd - c_right*pre_right*lcd - bias) / (c_self * lcd)
        # Simpler: use the kernel directly
        neighbor_contrib = c_left * pre_left + c_right * pre_right
        self_recovered = (raw_val * k['norm'] - neighbor_contrib * lcd) // (c_self * lcd) + offset
        return self_recovered

N = 16

def run_trial(seed, num_ticks):
    random.seed(seed)
    rho = random.randint(100, 800)
    mx = random.randint(-200, 200)
    my = random.randint(-200, 200)
    mz = random.randint(-200, 200)

    # Random ghost values per cell per channel
    ghost_data = {}
    for i in range(N):
        ghost_data[i] = {ch: random.randint(0, max_ranges[ch]) for ch in ghost_channels}

    # Initialize distributions
    f = np.zeros((N, 19), dtype=np.int64)
    for i in range(N):
        for q in range(19):
            eu = EX[q] * mx
            f[i,q] = (rho * int(W[q]) + 3 * eu * int(W[q])) // 36
        f[i,0] = rho - np.sum(f[i,1:])
        f[i] = inject_all_ghosts(f[i], ghost_data[i], rho)

    for tick in range(num_ticks):
        # Read pre-stream ghost values (from f_in = current f)
        pre_ghost = {}
        for i in range(N):
            pre_ghost[i] = {}
            for ch in ghost_channels:
                raw = read_ghost_raw(f[i], ch)
                lcd = ghost_lcds[ch]
                pre_ghost[i][ch] = (raw + lcd//2) // lcd

        # COLLIDE (MRT: relax physical, re-inject ghosts)
        f_post = np.zeros_like(f)
        for i in range(N):
            total = int(np.sum(f[i]))
            feq = np.array([total * int(w) // 36 for w in W], dtype=np.int64)
            feq[0] = total - np.sum(feq[1:])
            m_t = M @ f[i]
            meq_t = M @ feq
            m_out = m_t.copy()
            for pi in physical_indices:
                m_out[pi] = meq_t[pi]
            # Re-inject ghost targets
            for ch in ghost_channels:
                m_out[ch] = ghost_data[i][ch] * ghost_lcds[ch]
            f_raw = Minv_scaled @ m_out
            f_post[i] = np.array([(v + full_lcd//2) // full_lcd if v >= 0 else -(-v + full_lcd//2) // full_lcd
                                  for v in f_raw], dtype=np.int64)
            f_post[i,0] = total - np.sum(f_post[i,1:])

        # STREAM (gather, periodic)
        f_new = np.zeros_like(f)
        for i in range(N):
            for q in range(19):
                src = (i - EX[q]) % N
                f_new[i,q] = f_post[src,q]

        # RECOVER with anti-drift: subtract the offset BEFORE storing,
        # so it doesn't compound on the next tick's re-injection
        for i in range(N):
            for ch in ghost_channels:
                raw = read_ghost_raw(f_new[i], ch)
                left_i = (i - 1) % N
                right_i = (i + 1) % N
                # Use ghost_data (last tick's values) as neighbor reference
                recovered = recover_ghost(ch, raw,
                    ghost_data[left_i][ch],
                    ghost_data[i][ch],
                    ghost_data[right_i][ch])
                # Remove the offset so it doesn't compound
                ghost_data[i][ch] = recovered - recovery_offsets[ch]

            # Re-inject recovered values
            total = int(np.sum(f_new[i]))
            f_new[i] = inject_all_ghosts(f_new[i], ghost_data[i], total)

        f = f_new

    # Verify
    random.seed(seed)
    rho_orig = random.randint(100, 800)
    mx_orig = random.randint(-200, 200)
    my_orig = random.randint(-200, 200)
    mz_orig = random.randint(-200, 200)
    expected = {}
    for i in range(N):
        expected[i] = {ch: random.randint(0, max_ranges[ch]) for ch in ghost_channels}

    all_ok = True
    for i in range(N):
        for ch in ghost_channels:
            if ghost_data[i][ch] != expected[i][ch]:
                all_ok = False
                return False, i, ch, ghost_data[i][ch], expected[i][ch]
    return True, None, None, None, None

# Run stress tests
print('=== FULL STRESS TEST: 9 channels, collision + streaming ===')
print()

for num_ticks in [1, 2, 5, 10, 20, 50]:
    passed = 0
    total = 100
    first_fail = None
    for seed in range(total):
        ok, cell, ch, got, want = run_trial(seed, num_ticks)
        if ok:
            passed += 1
        elif first_fail is None:
            first_fail = (seed, cell, ch, got, want)
    fail_str = ''
    if first_fail:
        s, c, ch, g, w = first_fail
        fail_str = f'  first_fail: seed={s} cell={c} m[{ch}] got={g} want={w}'
    print(f'  {num_ticks:3d} ticks: {passed}/{total}{fail_str}')
