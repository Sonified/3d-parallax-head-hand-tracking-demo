# 👻 Roundtrip with Your Friendly Neighborhood Ghost
#
"""
Test: can ghost mode injection survive an integer M / M_inv round-trip?

An earlier test used f32 Gram-Schmidt basis -> float rounding killed it.
We're an integer engine. Use the standard D3Q19 MRT matrix (all integer entries)
and test with exact or near-exact integer arithmetic.
"""
import numpy as np
from fractions import Fraction

# D3Q19 velocity vectors
#        0     1    2    3    4    5    6    7    8    9   10   11   12   13   14   15   16   17   18
EX = [   0,    1,  -1,   0,   0,   0,   0,   1,  -1,   1,  -1,   1,  -1,   1,  -1,   0,   0,   0,   0]
EY = [   0,    0,   0,   1,  -1,   0,   0,   1,   1,  -1,  -1,   0,   0,   0,   0,   1,  -1,   1,  -1]
EZ = [   0,    0,   0,   0,   0,   1,  -1,   0,   0,   0,   0,   1,   1,  -1,  -1,   1,   1,  -1,  -1]

# Standard D3Q19 MRT matrix from d'Humieres et al. (2002)
# All entries are integers.
# Rows: rho, e, eps, jx, qx, jy, qy, jz, qz, 3pxx, 3pixx, pww, piww, pxy, pyz, pxz, mx, my, mz
M = np.array([
    # m0: rho = sum of all
    [1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1],
    # m1: e (energy)
    [-30, -11, -11, -11, -11, -11, -11, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8],
    # m2: eps (energy square)
    [12, -4, -4, -4, -4, -4, -4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    # m3: jx (x-momentum)
    [0, 1, -1, 0, 0, 0, 0, 1, -1, 1, -1, 1, -1, 1, -1, 0, 0, 0, 0],
    # m4: qx (x-energy flux)
    [0, -4, 4, 0, 0, 0, 0, 1, -1, 1, -1, 1, -1, 1, -1, 0, 0, 0, 0],
    # m5: jy (y-momentum)
    [0, 0, 0, 1, -1, 0, 0, 1, 1, -1, -1, 0, 0, 0, 0, 1, -1, 1, -1],
    # m6: qy (y-energy flux)
    [0, 0, 0, -4, 4, 0, 0, 1, 1, -1, -1, 0, 0, 0, 0, 1, -1, 1, -1],
    # m7: jz (z-momentum)
    [0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0, 1, 1, -1, -1, 1, 1, -1, -1],
    # m8: qz (z-energy flux)
    [0, 0, 0, 0, 0, -4, 4, 0, 0, 0, 0, 1, 1, -1, -1, 1, 1, -1, -1],
    # m9: 3pxx (stress)
    [0, 2, 2, -1, -1, -1, -1, 1, 1, 1, 1, 1, 1, 1, 1, -2, -2, -2, -2],
    # m10: 3pixx (ghost - energy flux of stress)
    [0, -4, -4, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, -2, -2, -2, -2],
    # m11: pww (stress)
    [0, 0, 0, 1, 1, -1, -1, 1, 1, 1, 1, -1, -1, -1, -1, 0, 0, 0, 0],
    # m12: piww (ghost)
    [0, 0, 0, -2, -2, 2, 2, 1, 1, 1, 1, -1, -1, -1, -1, 0, 0, 0, 0],
    # m13: pxy (stress)
    [0, 0, 0, 0, 0, 0, 0, 1, -1, -1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    # m14: pyz (stress)
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, -1, -1, 1],
    # m15: pxz (stress)
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, -1, -1, 1, 0, 0, 0, 0],
    # m16: mx (ghost)
    [0, 0, 0, 0, 0, 0, 0, 1, -1, 1, -1, -1, 1, -1, 1, 0, 0, 0, 0],
    # m17: my (ghost)
    [0, 0, 0, 0, 0, 0, 0, -1, -1, 1, 1, 0, 0, 0, 0, 1, -1, 1, -1],
    # m18: mz (ghost)
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, -1, -1, -1, -1, 1, 1],
], dtype=np.int64)

print("M matrix shape:", M.shape)
print("All entries integer:", np.all(M == M.astype(int)))

# Compute M_inv using exact rational arithmetic (Fraction)
print("\n=== Computing M_inv with exact rational arithmetic ===")
M_frac = [[Fraction(int(M[i, j])) for j in range(19)] for i in range(19)]

# Gauss-Jordan elimination to find exact inverse
def exact_inverse(mat):
    n = len(mat)
    # Augment with identity
    aug = [[mat[i][j] for j in range(n)] + [Fraction(1) if i == j else Fraction(0) for j in range(n)] for i in range(n)]

    for col in range(n):
        # Find pivot
        pivot = None
        for row in range(col, n):
            if aug[row][col] != 0:
                pivot = row
                break
        if pivot is None:
            return None
        aug[col], aug[pivot] = aug[pivot], aug[col]

        # Scale pivot row
        scale = aug[col][col]
        for j in range(2 * n):
            aug[col][j] /= scale

        # Eliminate
        for row in range(n):
            if row != col:
                factor = aug[row][col]
                for j in range(2 * n):
                    aug[row][j] -= factor * aug[col][j]

    return [[aug[i][n + j] for j in range(n)] for i in range(n)]

Minv_frac = exact_inverse(M_frac)

# Find all unique denominators
denoms = set()
for row in Minv_frac:
    for val in row:
        denoms.add(val.denominator)

print("Unique denominators in M_inv:", sorted(denoms))

# Find LCD (least common denominator)
from math import lcm
lcd = 1
for d in denoms:
    lcd = lcm(lcd, d)
print(f"Least common denominator: {lcd}")

# Scale M_inv by LCD to get integer matrix
Minv_scaled = np.array([[int(Minv_frac[i][j] * lcd) for j in range(19)] for i in range(19)], dtype=np.int64)
print(f"M_inv * {lcd} = all integers:", np.all(Minv_scaled == Minv_scaled.astype(int)))

# Verify: M_inv_scaled * M should equal lcd * I
product = Minv_scaled @ M
expected = np.eye(19, dtype=np.int64) * lcd
print(f"M_inv_scaled @ M == {lcd} * I:", np.array_equal(product, expected))

# === THE TEST ===
# Can we inject a value into a ghost moment and recover it exactly?

print("\n=== Ghost Injection Round-Trip Test ===")

# Create test distributions (equilibrium at rho=500)
rho = 500
# Simple equilibrium: f0 gets most, rest split
weights_num = [12, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # sum = 36
f = np.array([rho * w // 36 for w in weights_num], dtype=np.int64)
# Mass correct f[0]
f[0] = rho - np.sum(f[1:])

print(f"Initial distributions: {f}")
print(f"Initial mass: {np.sum(f)}")

# Step 1: Forward transform (exact -- integer * integer)
m = M @ f
print(f"\nMoment space: {m}")
print(f"  m[0] (density): {m[0]}")
print(f"  m[3] (jx): {m[3]}")
print(f"  Ghost modes m[10]: {m[10]}, m[12]: {m[12]}, m[16]: {m[16]}, m[17]: {m[17]}, m[18]: {m[18]}")

# Step 2: Inject value into ghost channel
GHOST_INDICES = [10, 12, 16, 17, 18]  # the non-physical modes
# Also 1 (energy), 2 (eps), 4 (qx), 6 (qy), 8 (qz) might be ghost-like
# but let's use the clearly non-physical ones

inject_channel = 16  # ghost mode mx
inject_value = 500
original_ghost = m[inject_channel]
m[inject_channel] = inject_value
print(f"\nInjected {inject_value} into ghost channel {inject_channel} (was {original_ghost})")

# Step 3: Inverse transform (using scaled integer matrix)
# f_new = M_inv @ m = (M_inv_scaled @ m) / lcd
f_new_scaled = Minv_scaled @ m
# Check divisibility
remainders = f_new_scaled % lcd
print(f"\nRemainders after dividing by {lcd}: {remainders}")
print(f"All exactly divisible: {np.all(remainders == 0)}")

f_new = f_new_scaled // lcd
print(f"New distributions: {f_new}")
print(f"New mass: {np.sum(f_new)}")
print(f"Mass changed: {np.sum(f_new) - np.sum(f)}")

# Step 4: Forward transform again -- do we get our value back?
m_recovered = M @ f_new
print(f"\nRecovered moments:")
print(f"  m[0] (density): {m_recovered[0]} (was {rho})")
print(f"  m[3] (jx): {m_recovered[3]}")
print(f"  Ghost {inject_channel}: {m_recovered[inject_channel]} (injected {inject_value})")

# Check ALL channels
print(f"\n=== Channel Independence Check ===")
m_original = M @ f  # moments before injection
m_original[inject_channel] = inject_value  # what we expect

for i in range(19):
    diff = m_recovered[i] - m_original[i]
    if i == inject_channel:
        status = "INJECTED" if m_recovered[i] == inject_value else f"WRONG (expected {inject_value})"
    elif diff == 0:
        status = "clean"
    else:
        status = f"LEAKED by {diff}"
    label = "PHYS" if i in [0,3,5,7,9,11,13,14,15] else "GHOST"
    print(f"  m[{i:2d}] ({label}): {m_recovered[i]:8d}  {status}")

# Step 5: Multi-tick test with mass correction
print(f"\n=== Multi-Tick Simulation (10 ticks) -- NAIVE (no mass correction) ===")

# Reset
f_sim = np.array([rho * w // 36 for w in weights_num], dtype=np.int64)
f_sim[0] = rho - np.sum(f_sim[1:])

# Inject into ghost
m_sim = M @ f_sim
m_sim[16] = 500  # ghost channel
m_sim[17] = 300  # second ghost channel

injected_16 = 500
injected_17 = 300

f_sim = (Minv_scaled @ m_sim) // lcd

for tick in range(10):
    total_mass = np.sum(f_sim)
    feq = np.array([total_mass * w // 36 for w in weights_num], dtype=np.int64)
    feq[0] = total_mass - np.sum(feq[1:])

    m_tick = M @ f_sim
    meq = M @ feq

    m_out = m_tick.copy()
    physical_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 13, 14, 15]
    ghost_indices = [10, 12, 16, 17, 18]

    for i in physical_indices:
        m_out[i] = meq[i]
    for i in ghost_indices:
        m_out[i] = m_tick[i]

    f_sim_scaled = Minv_scaled @ m_out
    f_sim = f_sim_scaled // lcd

    m_check = M @ f_sim
    remainders = f_sim_scaled % lcd
    max_remainder = np.max(np.abs(remainders))

    print(f"  Tick {tick+1}: mass={np.sum(f_sim)}, ghost16={m_check[16]} (want {injected_16}), "
          f"ghost17={m_check[17]} (want {injected_17}), max_remainder={max_remainder}")

# ============================================================
# Step 6: HEADROOM APPROACH -- scale up, transform, mass-correct
# ============================================================
print(f"\n=== Multi-Tick WITH HEADROOM + MASS CORRECTION (50 ticks) ===")
print(f"LCD = {lcd}, max scaled value = {lcd * 1023} vs i64 max = {2**63}")
print(f"Headroom ratio: {2**63 // (lcd * 1023):.0f}x")

f_sim2 = np.array([rho * w // 36 for w in weights_num], dtype=np.int64)
f_sim2[0] = rho - np.sum(f_sim2[1:])
original_mass = np.sum(f_sim2)

# Scale UP into headroom space
f_scaled = f_sim2 * lcd

# Forward transform in scaled space (exact)
m_scaled = M @ f_scaled

# Inject ghosts (also scaled)
m_scaled[16] = injected_16 * lcd
m_scaled[17] = injected_17 * lcd

for tick in range(50):
    # Inverse transform (exact -- Minv_scaled * m_scaled / lcd gives f * lcd... wait)
    # Actually: m_scaled is in units of lcd already.
    # m = M @ (f * lcd) = lcd * (M @ f)
    # To get f back: f = Minv @ m = (Minv_scaled @ m) / lcd
    # But m is already scaled by lcd, so:
    # f_unscaled = (Minv_scaled @ m_scaled) / (lcd * lcd)
    # Hmm, that doubles the denominator. Let me rethink.

    # Better approach: work in UNSCALED space but use round-to-nearest + mass correction

    # Unscale moments back
    m_unscaled = m_scaled // lcd  # This IS lossy... unless we track remainders

    # Actually, let me try a different approach entirely:
    # The issue is the inverse transform truncation.
    # What if we do: f_new = (Minv_scaled @ m + lcd//2) // lcd  (round to nearest)
    # Then mass correct f[0] = total_mass - sum(f[1:])

    # Start fresh each tick from f_sim2
    if tick == 0:
        f_current = f_sim2.copy()
        # Do initial injection
        m_current = M @ f_current
        m_current[16] = injected_16
        m_current[17] = injected_17
        # Inverse with round-to-nearest
        f_raw = Minv_scaled @ m_current
        f_current = np.array([(v + lcd // 2) // lcd if v >= 0 else -(-v + lcd // 2) // lcd for v in f_raw], dtype=np.int64)
        # Mass correction: f[0] absorbs truncation
        f_current[0] = original_mass - np.sum(f_current[1:])

    # MRT collision
    total_mass_now = np.sum(f_current)
    feq = np.array([total_mass_now * w // 36 for w in weights_num], dtype=np.int64)
    feq[0] = total_mass_now - np.sum(feq[1:])

    # Forward transform (exact)
    m_tick = M @ f_current
    meq = M @ feq

    # Relax physical modes, preserve ghosts
    m_out = m_tick.copy()
    for i in physical_indices:
        m_out[i] = meq[i]
    for i in ghost_indices:
        m_out[i] = m_tick[i]

    # Inverse transform with round-to-nearest
    f_raw = Minv_scaled @ m_out
    f_new = np.array([(v + lcd // 2) // lcd if v >= 0 else -(-v + lcd // 2) // lcd for v in f_raw], dtype=np.int64)

    # Mass correction: f[0] absorbs all truncation
    f_new[0] = total_mass_now - np.sum(f_new[1:])

    f_current = f_new

    # Check ghost values
    m_check = M @ f_current

    if tick < 10 or tick % 10 == 9:
        print(f"  Tick {tick+1:3d}: mass={np.sum(f_current):5d}, "
              f"ghost16={m_check[16]:5d} (want {injected_16}), "
              f"ghost17={m_check[17]:5d} (want {injected_17}), "
              f"g10={m_check[10]:5d}, g12={m_check[12]:5d}, g18={m_check[18]:5d}")

print(f"\n=== Final Channel Independence After 50 Ticks ===")
m_final = M @ f_current
for i in range(19):
    label = "PHYS" if i in physical_indices else "GHOST"
    expected = ""
    if i == 16: expected = f" (want {injected_16})"
    elif i == 17: expected = f" (want {injected_17})"
    print(f"  m[{i:2d}] ({label}): {m_final[i]:8d}{expected}")

# ============================================================
# Step 7: RE-INJECT after each collision (the correct approach)
# ============================================================
print(f"\n=== REINJECT APPROACH: correct ghost values each tick (50 ticks) ===")
print(f"Ghost values are RE-SET to target after each MRT collision.")
print(f"This costs: one forward transform readback to detect drift, then correction.\n")

f_current2 = np.array([rho * w // 36 for w in weights_num], dtype=np.int64)
f_current2[0] = rho - np.sum(f_current2[1:])
original_mass2 = np.sum(f_current2)

# Initial injection
m_init = M @ f_current2
m_init[16] = injected_16
m_init[17] = injected_17
f_raw = Minv_scaled @ m_init
f_current2 = np.array([(v + lcd // 2) // lcd if v >= 0 else -(-v + lcd // 2) // lcd for v in f_raw], dtype=np.int64)
f_current2[0] = original_mass2 - np.sum(f_current2[1:])

for tick in range(50):
    total_mass_now = np.sum(f_current2)

    # MRT collision
    m_tick = M @ f_current2

    # Compute equilibrium
    feq = np.array([total_mass_now * w // 36 for w in weights_num], dtype=np.int64)
    feq[0] = total_mass_now - np.sum(feq[1:])
    meq = M @ feq

    # Relax physical modes
    m_out = m_tick.copy()
    for i in physical_indices:
        m_out[i] = meq[i]

    # RE-INJECT ghost values (correct any drift)
    m_out[16] = injected_16
    m_out[17] = injected_17
    # Zero out other ghosts to prevent accumulation
    for i in ghost_indices:
        if i not in [16, 17]:
            m_out[i] = 0

    # Inverse transform with round-to-nearest
    f_raw = Minv_scaled @ m_out
    f_new = np.array([(v + lcd // 2) // lcd if v >= 0 else -(-v + lcd // 2) // lcd for v in f_raw], dtype=np.int64)
    # Mass correction
    f_new[0] = total_mass_now - np.sum(f_new[1:])

    f_current2 = f_new

    m_check = M @ f_current2

    if tick < 10 or tick % 10 == 9:
        print(f"  Tick {tick+1:3d}: mass={np.sum(f_current2):5d}, "
              f"ghost16={m_check[16]:5d} (want {injected_16}), "
              f"ghost17={m_check[17]:5d} (want {injected_17}), "
              f"g10={m_check[10]:5d}, g12={m_check[12]:5d}, g18={m_check[18]:5d}")

print(f"\n=== Final Channel Check (Reinject) ===")
m_final2 = M @ f_current2
for i in range(19):
    label = "PHYS" if i in physical_indices else "GHOST"
    expected = ""
    if i == 16: expected = f" (want {injected_16})"
    elif i == 17: expected = f" (want {injected_17})"
    print(f"  m[{i:2d}] ({label}): {m_final2[i]:8d}{expected}")
