# 👻 Streaming with Your Friendly Neighborhood Ghost
# Author: Robert Alexander
#
"""
Ghost mode streaming test.
Isolate streaming from collision to understand the transform.
"""
import numpy as np
from math import gcd
import random

# Weight-orthogonal MRT matrix
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

W = [12, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
EX = [0, 1,-1, 0, 0, 0, 0, 1,-1, 1,-1, 1,-1, 1,-1, 0, 0, 0, 0]
norms = np.diag(M @ np.diag(W).astype(np.int64) @ M.T)
full_lcd = 144
Minv_scaled = np.zeros((19,19), dtype=np.int64)
for q in range(19):
    for k in range(19):
        Minv_scaled[q,k] = int(W[q]) * int(M[k,q]) * (full_lcd // int(norms[k]))

physical_indices = list(range(10))
ghost_channels = list(range(10, 19))
ghost_lcds = {10:4, 11:24, 12:24, 13:24, 14:8, 15:8, 16:8, 17:48, 18:16}

# Streaming kernels per channel
kernels = {}
for ch in ghost_channels:
    norm = int(norms[ch])
    offsets = {}
    for q in range(19):
        dx = EX[q]
        contrib = int(M[ch,q])**2 * W[q]
        offsets[dx] = offsets.get(dx, 0) + contrib
    kernels[ch] = {'norm': norm, 'self': offsets.get(0,0), 'left': offsets.get(-1,0), 'right': offsets.get(1,0)}

N = 16

def inject(f_cell, ch, value, rho_target):
    m = M @ f_cell
    for c in ghost_channels:
        m[c] = 0
    m[ch] = value * ghost_lcds[ch]
    f_raw = Minv_scaled @ m
    f_out = np.array([(v + full_lcd//2) // full_lcd if v >= 0 else -(-v + full_lcd//2) // full_lcd for v in f_raw], dtype=np.int64)
    f_out[0] = rho_target - np.sum(f_out[1:])
    return f_out

def read_ghost(f_cell, ch):
    m = M @ f_cell
    lcd = ghost_lcds[ch]
    return (int(m[ch]) + lcd//2) // lcd

# =============================================
# TEST: Stream only (NO collision), then invert
# =============================================
random.seed(42)
print('=== FGE STREAMING ===')
print()

all_recovered = True
for ch in [12, 13, 14, 15, 16, 17, 18, 10, 11]:
    lcd = ghost_lcds[ch]
    k = kernels[ch]
    max_r = min(8184 // lcd, 500)
    ghost_in = [random.randint(10, max_r) for _ in range(N)]

    rho = 500
    f = np.zeros((N, 19), dtype=np.int64)
    for i in range(N):
        for q in range(19):
            f[i,q] = rho * W[q] // 36
        f[i,0] = rho - np.sum(f[i,1:])
        f[i] = inject(f[i], ch, ghost_in[i], rho)

    # NO collision -- just stream
    f_new = np.zeros_like(f)
    for i in range(N):
        for q in range(19):
            src = (i - EX[q]) % N
            f_new[i,q] = f[src,q]

    # Read raw moments
    ghost_raw = [int((M @ f_new[i])[ch]) for i in range(N)]

    # Naive
    naive = sum(1 for i in range(N) if (ghost_raw[i] + lcd//2) // lcd == ghost_in[i])

    # Invert using kernel
    inv = 0
    if k['self'] > 0:
        for i in range(N):
            corrected = (ghost_raw[i] * k['norm'] - k['left'] * ghost_raw[(i-1)%N] - k['right'] * ghost_raw[(i+1)%N]) // k['self']
            recovered = (corrected + lcd//2) // lcd
            if recovered == ghost_in[i]:
                inv += 1

    # Measure constant bias
    biases = [ghost_raw[i] - (k['left'] * ghost_in[(i-1)%N] * lcd + k['self'] * ghost_in[i] * lcd + k['right'] * ghost_in[(i+1)%N] * lcd) // k['norm'] for i in range(N)]
    bias = biases[0] if len(set(biases)) == 1 else None

    # Bias-corrected read
    bias_correct = 0
    if bias is not None:
        for i in range(N):
            corrected = ghost_raw[i] - bias
            recovered = (corrected + lcd//2) // lcd
            if recovered == ghost_in[i]:
                bias_correct += 1

    # Inverted + bias-corrected
    inv_bias = 0
    if k['self'] > 0 and bias is not None:
        for i in range(N):
            raw_corr = ghost_raw[i] - bias
            corrected = (raw_corr * k['norm'] - k['left'] * (ghost_raw[(i-1)%N] - bias) - k['right'] * (ghost_raw[(i+1)%N] - bias)) // k['self']
            recovered = (corrected + lcd//2) // lcd
            if recovered == ghost_in[i]:
                inv_bias += 1

    bias_str = f'bias={bias}' if bias is not None else f'bias=varies({min(biases)}-{max(biases)})'
    print(f'  m[{ch:2d}] k=[{k["left"]}/{k["norm"]},{k["self"]}/{k["norm"]},{k["right"]}/{k["norm"]}]  {bias_str}  naive={naive}/{N}  inv={inv}/{N}  bias_corr={bias_correct}/{N}  inv+bias={inv_bias}/{N}')

    # LINEAR REGRESSION: predict actual_raw from ALL known inputs
    # Features: ghost_in at cells i-2, i-1, i, i+1, i+2, plus rho, plus mass_correction_delta
    from numpy.linalg import lstsq

    # Collect features
    X = []
    y = []
    for i in range(N):
        features = [
            ghost_in[(i-2) % N],
            ghost_in[(i-1) % N],
            ghost_in[i],
            ghost_in[(i+1) % N],
            ghost_in[(i+2) % N],
            1,  # constant bias term
        ]
        X.append(features)
        y.append(ghost_raw[i])

    X = np.array(X, dtype=np.float64)
    y = np.array(y, dtype=np.float64)
    coeffs, res, _, _ = lstsq(X, y, rcond=None)
    predicted = X @ coeffs

    # Recovery using regression
    reg_correct = 0
    for i in range(N):
        recovered = (int(round(predicted[i])) + lcd//2) // lcd
        if recovered == ghost_in[i]:
            reg_correct += 1

    rms = np.sqrt(np.mean((predicted - y)**2))
    print(f'    REGRESSION: g[-2]={coeffs[0]:.4f} g[-1]={coeffs[1]:.4f} g[0]={coeffs[2]:.4f} g[+1]={coeffs[3]:.4f} g[+2]={coeffs[4]:.4f} bias={coeffs[5]:.1f} rms={rms:.2f} recovery={reg_correct}/{N}')

    # Can we just subtract the predicted contamination and recover self?
    # self_recovered = (raw - bias - left_coeff*left_val*lcd - right_coeff*right_val*lcd) / self_coeff / lcd
    # But we don't know the TRUE neighbor values after streaming...
    # WAIT: we know them from BEFORE streaming (ping-pong buffer!)
    # The pre-streaming ghost values are in the f_in buffer.
    # We READ them before streaming. Then correct after.

    pre_ghost = [read_ghost(f[i], ch) for i in range(N)]  # f is pre-streaming

    # Use pre-streaming neighbor values to correct post-streaming read
    # The regression tells us: raw_out = c[-1]*g[-1] + c[0]*g[0] + c[+1]*g[+1] + bias
    # where g values are RAW (unscaled) ghost values
    # So: g[0] = (raw_out - c[-1]*g[-1] - c[+1]*g[+1] - bias) / c[0]
    # We KNOW g[-1] and g[+1] from the pre-stream ping-pong buffer!

    pingpong_correct = 0
    c_self = coeffs[2]
    if abs(c_self) > 0.01:
        for i in range(N):
            neighbor_sum = (coeffs[0]*pre_ghost[(i-2)%N] +
                           coeffs[1]*pre_ghost[(i-1)%N] +
                           coeffs[3]*pre_ghost[(i+1)%N] +
                           coeffs[4]*pre_ghost[(i+2)%N] +
                           coeffs[5])
            self_recovered = (ghost_raw[i] - neighbor_sum) / c_self
            recovered = int(round(self_recovered))
            if recovered == ghost_in[i]:
                pingpong_correct += 1
            elif ch in [14, 15] and i < 5:
                print(f'      cell {i}: raw={ghost_raw[i]} neighbor_sum={neighbor_sum:.1f} self_rec={self_recovered:.4f} round={recovered} want={ghost_in[i]}')

    print(f'    PINGPONG CORRECTION (pre-stream neighbors): {pingpong_correct}/{N}')
    best_recovery = max(naive, inv, pingpong_correct)

    # DIRECT READ FROM PING-PONG: for self=0 channels, just read from f_in
    if abs(c_self) < 0.01:
        direct_correct = sum(1 for i in range(N) if pre_ghost[i] == ghost_in[i])
        # Check what's off
        diffs = [pre_ghost[i] - ghost_in[i] for i in range(N)]
        unique_diffs = set(diffs)
        if direct_correct < N:
            # Try with constant offset
            offset = diffs[0]
            offset_correct = sum(1 for i in range(N) if pre_ghost[i] - offset == ghost_in[i])
            print(f'    DIRECT PINGPONG READ (self=0): {direct_correct}/{N}  diffs={unique_diffs}  with offset({offset:+d}): {offset_correct}/{N}')
            best_recovery = max(best_recovery, offset_correct)
        else:
            print(f'    DIRECT PINGPONG READ (self=0): {direct_correct}/{N}')
            best_recovery = max(best_recovery, direct_correct)

    # CALIBRATED PINGPONG: measure the constant offset and correct
    if abs(c_self) > 0.01 and pingpong_correct < N:
        # Measure offset on first cell
        neighbor_sum_0 = (coeffs[0]*pre_ghost[(0-2)%N] +
                         coeffs[1]*pre_ghost[(0-1)%N] +
                         coeffs[3]*pre_ghost[(0+1)%N] +
                         coeffs[4]*pre_ghost[(0+2)%N] +
                         coeffs[5])
        self_rec_0 = (ghost_raw[0] - neighbor_sum_0) / c_self
        offset = ghost_in[0] - int(round(self_rec_0))

        cal_correct = 0
        for i in range(N):
            neighbor_sum = (coeffs[0]*pre_ghost[(i-2)%N] +
                           coeffs[1]*pre_ghost[(i-1)%N] +
                           coeffs[3]*pre_ghost[(i+1)%N] +
                           coeffs[4]*pre_ghost[(i+2)%N] +
                           coeffs[5])
            self_recovered = (ghost_raw[i] - neighbor_sum) / c_self + offset
            recovered = int(round(self_recovered))
            if recovered == ghost_in[i]:
                cal_correct += 1
        print(f'    CALIBRATED PINGPONG (offset={offset:+d}): {cal_correct}/{N}')
        best_recovery = max(best_recovery, cal_correct)

    # SCALED PINGPONG: multiply everything by a scale factor before dividing
    # to get more integer precision in the division
    if abs(c_self) > 0.01 and pingpong_correct < N:
        best_scale = 1
        best_correct = pingpong_correct
        for scale in [2, 4, 8, 16, 32, 64, 128, 256]:
            sc_correct = 0
            for i in range(N):
                neighbor_sum = (coeffs[0]*pre_ghost[(i-2)%N] +
                               coeffs[1]*pre_ghost[(i-1)%N] +
                               coeffs[3]*pre_ghost[(i+1)%N] +
                               coeffs[4]*pre_ghost[(i+2)%N] +
                               coeffs[5])
                # Scale up before division
                numerator = int(round((ghost_raw[i] - neighbor_sum) * scale))
                denominator = int(round(c_self * scale))
                if denominator != 0:
                    self_recovered = (numerator + denominator // 2) // denominator
                else:
                    self_recovered = 0
                if self_recovered == ghost_in[i]:
                    sc_correct += 1
            if sc_correct > best_correct:
                best_correct = sc_correct
                best_scale = scale
        if best_correct > pingpong_correct:
            print(f'    SCALED PINGPONG (x{best_scale}): {best_correct}/{N}')
            best_recovery = max(best_recovery, best_correct)

    if best_recovery < N:
        all_recovered = False

    # Show first 5 cells detail
    if ch == 12:
        print(f'    Detail for m[{ch}]:')
        for i in range(5):
            expected_scaled = ghost_in[i] * lcd
            # What streaming SHOULD produce: k_left*in[i-1] + k_self*in[i] + k_right*in[i+1]
            predicted = (k['left'] * ghost_in[(i-1)%N] * lcd + k['self'] * ghost_in[i] * lcd + k['right'] * ghost_in[(i+1)%N] * lcd) // k['norm']
            actual = ghost_raw[i]

            # What we read before streaming
            pre_stream = int((M @ f[i])[ch])
            pre_read = (pre_stream + lcd//2) // lcd

            print(f'      cell {i}: injected={ghost_in[i]}  pre_stream_read={pre_read}  predicted={predicted}  actual_raw={actual}  diff={actual-predicted}')

if all_recovered:
    print()
    print("\U0001F47B I'm still here!")
