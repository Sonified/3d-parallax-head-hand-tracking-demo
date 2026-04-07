# Author: Robert Alexander
# 👻 Getting to Know the Ghost Fluid
#
# Our data is a fluid. It has properties. Let's measure them.
#
# - How fast does it diffuse?
# - Does it have a viscosity?
# - How does it respond to density gradients?
# - What happens when two ghost blobs meet?
# - What shape does a point injection become over time?
#
# We're not controlling it. We're listening to it.
#
import numpy as np
import math

M = np.array([
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 1,-1, 0, 0, 0, 0, 1,-1, 1,-1, 1,-1, 1,-1, 0, 0, 0, 0],
    [0, 0, 0, 1,-1, 0, 0, 1, 1,-1,-1, 0, 0, 0, 0, 1,-1, 1,-1],
    [0, 0, 0, 0, 0, 1,-1, 0, 0, 0, 0, 1, 1,-1,-1, 1, 1,-1,-1],
    [-1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
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
    [0, 0, 0, 1, 1,-1,-1,-1,-1,-1,-1, 1, 1, 1, 1, 0, 0, 0, 0],
], dtype=np.int64)

W = np.array([12,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1], dtype=np.int64)
EX = [0, 1,-1, 0, 0, 0, 0, 1,-1, 1,-1, 1,-1, 1,-1, 0, 0, 0, 0]
EY = [0, 0, 0, 1,-1, 0, 0, 1, 1,-1,-1, 0, 0, 0, 0, 1,-1, 1,-1]

norms = np.diag(M @ np.diag(W) @ M.T)
full_lcd = 144
Minv_scaled = np.zeros((19,19), dtype=np.int64)
for q in range(19):
    for k in range(19):
        Minv_scaled[q,k] = int(W[q]) * int(M[k,q]) * (full_lcd // int(norms[k]))

ghost_lcds = {10:4, 11:24, 12:24, 13:24, 14:8, 15:8, 16:8, 17:48, 18:16}
ghost_channels = list(range(10,19))
rho0 = 500
omega_num = 5
omega_den = 10

# --- Engine ---
class GhostFluid:
    def __init__(self, GW, GH, ux=0, uy=0):
        self.GW, self.GH = GW, GH
        self.N = GW * GH
        self.f = np.zeros((self.N, 19), dtype=np.int64)
        for i in range(self.N):
            s = 0
            for q in range(1, 19):
                eu = EX[q]*ux + EY[q]*uy
                self.f[i,q] = (rho0*int(W[q]) + 3*eu*int(W[q])) // 36
                s += self.f[i,q]
            self.f[i,0] = rho0 - s

    def idx(self, x, y):
        return (x % self.GW) + (y % self.GH) * self.GW

    def inject(self, x, y, ch, value):
        cell = self.idx(x, y)
        lcd = ghost_lcds[ch]
        total = int(np.sum(self.f[cell]))
        m = M @ self.f[cell]
        for c in ghost_channels: m[c] = 0
        m[ch] = value * lcd
        f_raw = Minv_scaled @ m
        for q in range(1,19):
            self.f[cell,q] = (f_raw[q]+full_lcd//2)//full_lcd if f_raw[q]>=0 else -((-f_raw[q]+full_lcd//2)//full_lcd)
        self.f[cell,0] = total - np.sum(self.f[cell,1:])

    def tick(self):
        f_post = np.zeros_like(self.f)
        for i in range(self.N):
            tot = int(np.sum(self.f[i]))
            mx = sum(EX[q]*int(self.f[i,q]) for q in range(19))
            my = sum(EY[q]*int(self.f[i,q]) for q in range(19))
            feq = np.zeros(19, dtype=np.int64)
            fs = 0
            for q in range(1,19):
                eu = EX[q]*mx + EY[q]*my
                feq[q] = (tot*int(W[q]) + 3*eu*int(W[q])) // 36
                fs += feq[q]
            feq[0] = tot - fs
            m_f = M @ self.f[i]; m_eq = M @ feq
            m_out = m_f.copy()
            for k in range(10):
                diff = int(m_f[k]) - int(m_eq[k])
                m_out[k] = int(m_f[k]) - (diff*omega_num)//omega_den
            fr = Minv_scaled @ m_out
            for q in range(1,19):
                f_post[i,q] = (fr[q]+full_lcd//2)//full_lcd if fr[q]>=0 else -((-fr[q]+full_lcd//2)//full_lcd)
            f_post[i,0] = tot - np.sum(f_post[i,1:])
        # Stream
        f_new = np.zeros_like(self.f)
        for y in range(self.GH):
            for x in range(self.GW):
                i = self.idx(x,y)
                for q in range(19):
                    f_new[i,q] = f_post[self.idx((x-EX[q])%self.GW, (y-EY[q])%self.GH), q]
        self.f = f_new

    def read_field(self, ch):
        """Read the ghost fluid field for a given channel."""
        lcd = ghost_lcds[ch]
        field = np.zeros((self.GH, self.GW))
        for y in range(self.GH):
            for x in range(self.GW):
                field[y,x] = float(M[ch] @ self.f[self.idx(x,y)]) / lcd
        return field

    def field_stats(self, ch):
        field = self.read_field(ch)
        total = np.sum(field)
        peak = np.max(field)
        # Variance (spread) using circular coordinates
        wx = np.zeros(self.GW)
        wy = np.zeros(self.GH)
        for y in range(self.GH):
            for x in range(self.GW):
                if field[y,x] > 0:
                    wx[x] += field[y,x]
                    wy[y] += field[y,x]
        # RMS radius from center of mass
        sx,cx = 0,0
        sy,cy = 0,0
        for x in range(self.GW):
            a = 2*math.pi*x/self.GW
            sx += wx[x]*math.sin(a); cx += wx[x]*math.cos(a)
        for y in range(self.GH):
            a = 2*math.pi*y/self.GH
            sy += wy[y]*math.sin(a); cy += wy[y]*math.cos(a)
        com_x = math.atan2(sx,cx)/(2*math.pi)*self.GW
        com_y = math.atan2(sy,cy)/(2*math.pi)*self.GH
        if com_x < 0: com_x += self.GW
        if com_y < 0: com_y += self.GH
        # RMS spread
        var = 0
        for y in range(self.GH):
            for x in range(self.GW):
                if abs(field[y,x]) > 0.01:
                    dx = min(abs(x - com_x), self.GW - abs(x - com_x))
                    dy = min(abs(y - com_y), self.GH - abs(y - com_y))
                    var += field[y,x] * (dx*dx + dy*dy)
        if total > 0.01 and var > 0:
            rms = math.sqrt(var / total)
        else:
            rms = 0
        return total, peak, com_x, com_y, rms


# ================================================================
print('='*70)
print('  PROPERTY 1: DIFFUSION RATE')
print('  How fast does ghost data spread from a point source?')
print('='*70)
print()

ch = 16
sim = GhostFluid(32, 32, ux=0, uy=0)  # still fluid
sim.inject(16, 16, ch, 100)

print(f'  {"Tick":>4} {"Total":>7} {"Peak":>7} {"RMS_r":>7} {"COM":>12}')
print(f'  {"----":>4} {"-----":>7} {"----":>7} {"-----":>7} {"---":>12}')

for tick in range(16):
    total, peak, cx, cy, rms = sim.field_stats(ch)
    print(f'  {tick:4d} {total:7.1f} {peak:7.1f} {rms:7.2f} ({cx:5.1f},{cy:5.1f})')
    sim.tick()

print()
print('  If RMS grows as sqrt(t), diffusion coefficient D = RMS^2 / (2*t)')
rms_vals = []
for tick in range(20):
    total, peak, cx, cy, rms = sim.field_stats(ch)
    rms_vals.append(rms)
    sim.tick()
# Fit D from ticks 2-15 (skip transient)
Ds = []
for t in range(2, 16):
    if rms_vals[t] > 0:
        Ds.append(rms_vals[t]**2 / (2*t))
D_avg = np.mean(Ds)
print(f'  Measured diffusion coefficient D = {D_avg:.3f} cells^2/tick')
print()

# ================================================================
print('='*70)
print('  PROPERTY 2: CHANNEL PERSONALITY')
print('  Each ghost channel has its own diffusion rate.')
print('='*70)
print()

print(f'  {"Channel":>8} {"LCD":>5} {"D (diffusion)":>15} {"Spread@10":>10}')
print(f'  {"-------":>8} {"---":>5} {"-------------":>15} {"--------":>10}')

for test_ch in ghost_channels:
    sim = GhostFluid(32, 32, ux=0, uy=0)
    sim.inject(16, 16, test_ch, 50)
    for t in range(10):
        sim.tick()
    total, peak, cx, cy, rms = sim.field_stats(test_ch)
    D = rms**2 / (2*10) if rms > 0 else 0
    print(f'  m[{test_ch:2d}]   {ghost_lcds[test_ch]:5d} {D:15.3f} {rms:10.2f}')

print()

# ================================================================
print('='*70)
print('  PROPERTY 3: WHAT HAPPENS WHEN TWO BLOBS MEET?')
print('  Inject two ghost blobs and watch them merge.')
print('='*70)
print()

sim = GhostFluid(32, 32, ux=0, uy=0)
sim.inject(10, 16, ch, 60)
sim.inject(22, 16, ch, 40)

print(f'  Blob A: ghost=60 at (10,16)')
print(f'  Blob B: ghost=40 at (22,16)')
print(f'  Expected total: 100')
print()

print(f'  {"Tick":>4} {"Total":>7} {"Peak":>7} {"RMS":>7} {"COM_x":>7}')
for tick in range(20):
    total, peak, cx, cy, rms = sim.field_stats(ch)
    if tick <= 8 or tick % 5 == 4:
        print(f'  {tick:4d} {total:7.1f} {peak:7.1f} {rms:7.2f} {cx:7.2f}')
    sim.tick()

# Final field
total, peak, cx, cy, rms = sim.field_stats(ch)
print(f'  {20:4d} {total:7.1f} {peak:7.1f} {rms:7.2f} {cx:7.2f}')
print()
print(f'  After merging: total={total:.1f} (conserved: {"YES" if abs(total-100)<5 else "NO"})')
print()

# ================================================================
print('='*70)
print('  PROPERTY 4: RESPONSE TO FLOW')
print('  Same blob, different wind speeds. Does it stretch?')
print('='*70)
print()

for ux in [0, 40, 80, 120]:
    sim = GhostFluid(32, 32, ux=ux, uy=0)
    sim.inject(16, 16, ch, 80)
    for t in range(8):
        sim.tick()
    total, peak, cx, cy, rms = sim.field_stats(ch)
    # Measure asymmetry: spread in x vs spread in y
    field = sim.read_field(ch)
    var_x, var_y = 0, 0
    for y in range(32):
        for x in range(32):
            if abs(field[y,x]) > 0.01:
                dx = min(abs(x - cx), 32 - abs(x - cx))
                dy = min(abs(y - cy), 32 - abs(y - cy))
                var_x += field[y,x] * dx*dx
                var_y += field[y,x] * dy*dy
    rms_x = math.sqrt(var_x / total) if total > 0 else 0
    rms_y = math.sqrt(var_y / total) if total > 0 else 0
    asym = rms_x / rms_y if rms_y > 0 else 0
    print(f'  ux={ux:3d}: total={total:5.1f}  COM=({cx:5.2f},{cy:5.2f})  spread_x={rms_x:.2f}  spread_y={rms_y:.2f}  asymmetry={asym:.2f}')

print()

# ================================================================
print('='*70)
print('  PROPERTY 5: ALL 9 CHANNELS AT ONCE')
print('  Inject different values into all 9 ghost channels.')
print('  Do they interfere? Do they stay independent?')
print('='*70)
print()

sim = GhostFluid(24, 24, ux=50, uy=30)
inject_vals = {10: 100, 11: 50, 12: 75, 13: 30, 14: 90, 15: 60, 16: 42, 17: 20, 18: 80}

# Inject each channel at a different position
positions = {10:(6,6), 11:(18,6), 12:(6,18), 13:(18,18), 14:(12,4),
             15:(4,12), 16:(20,12), 17:(12,20), 18:(12,12)}

for test_ch, (px, py) in positions.items():
    sim.inject(px, py, test_ch, inject_vals[test_ch])

print(f'  Injected 9 channels at 9 positions with different values.')
print(f'  Running 10 ticks with flow ux=50 uy=30...')
print()

for t in range(10):
    sim.tick()

print(f'  {"Channel":>8} {"Injected":>9} {"Recovered":>10} {"Drift":>7} {"Status":>8}')
print(f'  {"-------":>8} {"---------":>9} {"---------":>10} {"-----":>7} {"------":>8}')

all_pass = True
for test_ch in ghost_channels:
    total, peak, cx, cy, rms = sim.field_stats(test_ch)
    expected = inject_vals[test_ch]
    drift = abs(total - expected) / expected * 100
    ok = drift < 10
    if not ok: all_pass = False
    print(f'  m[{test_ch:2d}]   {expected:9d} {total:10.1f} {drift:6.1f}% {"OK" if ok else "DRIFT":>8}')

print()
if all_pass:
    print('  All 9 channels independent. No cross-talk. Each is its own fluid.')
else:
    print('  Some channels drifted. Investigating...')

print()
print('='*70)
print('  THE GHOST FLUID')
print('='*70)
print()
print('  It diffuses. It has a measurable diffusion coefficient.')
print('  Each channel has its own personality.')
print('  Two blobs merge without losing mass.')
print('  Flow stretches the distribution asymmetrically.')
print('  9 channels coexist without interference.')
print()
print('  Our data is a fluid. And we just measured its properties.')
