# Fluid Sim Review — Full Remediation Spec (reviewed 2026-07-05)

Scope: `fluid_sandbox/` u16 integer D3Q19 TRT LBM on WebGPU, for Spellaria. Files reviewed line-by-line: `packed-lbm-bench.html`, `sim_batch_u16.html`, `dormant-validate.html`, `dormant-bench.html` (structure), `run-bench.mjs`, `fluid-sim-best-practices.md`. Line numbers are as of the 2026-07-05 working tree; verify before editing.

**Trust hierarchy established by this review:** `sim_batch_u16.html` is the only kernel that is both physics-correct (right TRT pairs, ping-pong streaming, clamped writeback) and physics-validated (Poiseuille, 53 levels, the clean53 png). Treat it as the reference implementation. Everything AA-based is unvalidated and broken as detailed below.

**How to run any bench:** `cd fluid_sandbox && npx http-server . -p 8765` then `node run-bench.mjs http://localhost:8765/<file>.html`. Results emitted as `RESULT:{json}` console lines; the runner waits for "Done." in `#log`.

---

## Architecture primer (read before fixing anything)

- **Storage:** f[0] is never stored. u10 packing = 6 u32/cell (3×10-bit dists per word, `q=1..18 → word (q-1)/3, slot (q-1)%3`). u16 packing = 9 u32/cell (2×16-bit per word, `word (q-1)/2, slot (q-1)%2`). Buffer layout is SoA: `word_idx * NCELLS + cell_idx`.
- **f[0] derivation:** every kernel does `f[0] = RHO0 - sum(f[1..18]); rho = RHO0` with RHO0 a compile-time constant (18000 in u16 benches, 500 in u10, 24000 in sim_batch_u16 configs). This makes mass exact by construction — and deletes pressure (Finding 3).
- **TRT integer form:** relaxation is `fc = feq + (OD-ON)*fneq/OD`, i.e. omega = ON/OD, tau = OD/ON. Game target: ON1=1, OD1=75 (tau+ = 75), ON2=8, OD2=5 (tau- = 0.625, via negative factor (5-8)/5 = -0.6, legal over-relaxation).
- **TWO DIRECTION CONVENTIONS EXIST. This caused Finding 2.**
  - Convention A (`sim_batch_u16.html:16-20`): EX/EY/EZ with x-first ordering. Faces: 1..6 = +x,-x,+y,-y,+z,-z. Edges 7..18. Opposite pairs: (1,2)(3,4)(5,6)(7,10)(8,9)(11,14)(12,13)(15,18)(16,17). OPP = [0,2,1,4,3,6,5,10,9,8,7,14,13,12,11,18,17,16,15].
  - Convention B (all six bench HTMLs, e.g. `packed-lbm-bench.html:52-54`): DX/DY/DZ with y-first ordering. q1..6 = +y,-y,+x,-x,+z,-z. Edge vectors: 7=(1,1,0) 8=(-1,-1,0) 9=(1,-1,0) 10=(-1,1,0) 11=(0,1,1) 12=(0,-1,-1) 13=(0,1,-1) 14=(0,-1,1) 15=(1,0,1) 16=(-1,0,-1) 17=(1,0,-1) 18=(-1,0,1). Opposite pairs: (1,2)(3,4)(5,6)(7,8)(9,10)(11,12)(13,14)(15,16)(17,18). OPP = [0,2,1,4,3,6,5,8,7,10,9,12,11,14,13,16,15,18,17].
  - Long-term fix: one shared `lbm-kernels.mjs` module, one convention, OPP and TRT pairs **derived programmatically** from the direction table (search for the q' with e_q' = -e_q), WGSL snippets exported from there. That makes Finding 2's whole bug class unrepresentable.

---

## Finding 1 (CRITICAL): the "AA" single-buffer kernel is wrong twice

**Where:** `GATHER_AA`/`WRITEBACK_AA` template strings, shared verbatim by ALL SIX bench files. Canonical copy: `dormant-validate.html:108-141`; also `packed-lbm-bench.html:850-898` (AA benchmark 3 and u16 AA benchmark 6, lines 1281-1352). Tick parity is written as `writeBuffer(tickBuf, new Uint32Array([t % 2]))`, so tick 0 has `is_even=0`. WGSL `select(a, b, cond)` returns `b` when cond true: `read_q = select(q, OPP[q], is_even == 1u)` means tick 0 reads slot q, tick 1 reads slot OPP[q].

**Bug 1a — data race.** The kernel reads neighbor cells' packed words and writes its own cell's words, in one dispatch, on ONE `read_write` buffer. Cell X writes all 18 of its slots; each of X's 18 neighbors reads one of X's slots in the same dispatch. No ordering guarantee exists between workgroups, so whether a neighbor observes X's tick-(t-1) or tick-t data depends on GPU scheduling. The in-code comment (`packed-lbm-bench.html:819-821`, "the read and write access DIFFERENT slots in the packed word, so there's no race") addresses intra-word slot aliasing, not the actual inter-thread read/write hazard. On Apple Silicon the scheduling may be reproducible so it *looks* fine; on a different GPU/driver the interleaving differs → different physics → **breaks Claim IV bit-exact P2P determinism**, which is the entire point of the integer engine.

**Bug 1b — the parity label choreography is self-inconsistent.** Trace with canonical initial layout (slot q at cell C = population moving in direction q, which is how `initData` is written):

- Tick 0 (`is_even=0`): f[q] := (X−e_q).slot[q] — correct gather streaming. Writeback slot q := col[q] — layout stays canonical. ✓
- Tick 1 (`is_even=1`): f[q] := (X−e_q).slot[OPP[q]]. Under canonical layout that slot holds col[OPP[q]] — the population moving AWAY from X. Reversed streaming. ✗
- No parity/initialization assignment repairs this: because the writeback always targets SELF, a population's storage cell never moves, so it must be read at the same relative offset every tick; alternating slot labels is only coherent when storage location alternates between self and neighbor (which is what real AA does). Provable by exhaustive case check on the four (read_q, write_q) parity combos.
- Boundary branch is wrong the same way: `read_slot(idx, select(oq, q, is_even == 1u))` gives correct bounce-back (own slot OPP[q]) on tick 0, wrong slot (own q) on tick 1.

**Correct AA (Bailey 2009), derived and race-checked — implement exactly this:**

- **Even step (pure local, no neighbor access):** for cell x: `f_i = load(x, i)`; collide; `store(x, OPP[i]) = f*_i`. Reads and writes only cell x → race-free trivially.
- **Odd step (fused stream, remote):** for cell x: `f_i = load(x − e_i, slot OPP[i])`; collide; `store(x + e_i, slot i) = f*_i`. The read set {(x−e_i, OPP[i])} and write set {(x+e_i, i)} are the SAME set of memory locations (substitute j=OPP[i]), and location (y, j) belongs to exactly one thread (x = y − e_j) → race-free, provided the kernel does ALL gathers into registers before any store (current code structure already does).
- **Odd-step boundaries (bounce-back):** read side, if x−e_i out of grid: `f_i = load(x, i)` (the even step parked the reflected population there — even stored f*_{OPP[i]} at slot i). Write side, if x+e_i out of grid: `store(x, OPP[i]) = f*_i`. That location is only otherwise touched by the (nonexistent) out-of-grid thread → still race-free.
- After an even+odd pair the layout returns to canonical, so readback/rendering code should sample on even-tick boundaries or handle the swapped layout.

**Verification recipe (run before trusting the fix):** (1) From a non-equilibrium init (inject the dormant-validate force pulse), run 2 ticks of fixed-AA vs 2 ticks of the ping-pong reference kernel (same collision code, same pairs); diff all 18 dists per cell — must be bit-exact zero. (2) Run the same AA sim twice back-to-back and diff — must be zero (determinism). (3) Re-run the 53-level Poiseuille through the AA path, compare profile to sim_batch_u16's. Note test (2) alone is insufficient — a race can be reproducible on one GPU; test (1) is the decisive one.

**Timing impact of the fix:** none expected. Same memory traffic, same instruction mix; the 1.73/1.79 ms u10/u16 AA numbers and the u16 ≈ +3.5% conclusion should survive. If the fixed odd step benches slower due to scattered writes, that's real information — re-measure before quoting old numbers.

---

## Finding 2 (CRITICAL in 3 files): TRT pair tables pair non-opposite directions

**Where:** `packed-lbm-bench.html:68-69`, and identical constants in `grid-size-bench.html` and `tiling-bench.html`:
`PAIRS_A = (1,3,5,7,8,11,12,15,16); PAIRS_B = (2,4,6,10,9,14,13,18,17)`.
These are Convention A's opposite pairs, but all three files use Convention B directions. Under Convention B, the table pairs 7=(1,1,0) with 10=(-1,1,0) — not opposites. TRT's symmetric/antisymmetric decomposition `fneq± = (fneq_a ± fneq_b)/2` is only meaningful over opposite pairs, so the collision operator in these files is not TRT — it's an unnamed linear operator with undefined viscosity/stability properties.

**Correct table for Convention B:** `PAIRS_A = (1,3,5,7,9,11,13,15,17); PAIRS_B = (2,4,6,8,10,12,14,16,18)` — i.e. simply (2k-1, 2k). Cross-check against the file's own OPP array (line 529/580/835), which is correct.

**Already-correct code to crib from:** `dormant-validate.html:84-92` (and dormant-bench, compute-opt-bench) use explicit `pairBlock(a,b,w,cuExpr)` calls with pairs (1,2)(3,4)(5,6)(7,8)(9,10)(11,12)(13,14)(15,16)(17,18) and cu expressions uy / ux / uz / ux+uy / ux−uy / uy+uz / uy−uz / ux+uz / ux−uz — verified correct against Convention B, including the elegant `feq_b = feq_a - 2*linear` opposite-direction shortcut.

**Impact:** timing results from the 3 affected files are valid (identical FLOP count). Any *physics* output from them (the mass-conservation "stability" check in packed-lbm-bench passed only because the test state was uniform rest, where any collision is identity) is not TRT. Fix = replace the two constant arrays, or better, delete the tables in favor of the shared-module derivation.

---

## Finding 3 (CRITICAL, unvalidated physics): constant-rho derived f[0] removes pressure entirely

**Where:** every kernel: `f[0] = RHO0 - sum_f; let rho = RHO0;` (`packed-lbm-bench.html:617-619`, `dormant-validate.html:124-127`, `sim_batch_u16.html:267-271`).

**Why it kills pressure:** in LBM the pressure force enters via the equilibrium momentum flux Π^eq_αβ = cs²·rho·δ_αβ + rho·u_α·u_β. With rho pinned to a global constant in feq, the cs²·rho·δ term is spatially constant → its divergence (the −∇p force) is identically zero. What remains is momentum advection + viscous stress + body force: a pressureless (Burgers-like) momentum equation. Density fluctuations still exist transiently in the stored f's (sum18 varies) but live only in fneq, which at tau+=75 relaxes glacially — they stream around as unphysical lattice-speed artifacts rather than acoustics, and they exert no equilibrium pressure force. Consequences for the game: flow will NOT properly divert around porous/solid obstacles (deflection is a pressure effect), colliding jets won't splash, explosions won't push outward as pressure waves — the exact features `fluid-sim-best-practices.md` celebrates ("LBM captures pressure waves at physical speed of sound") are architecturally absent.

**Why no test caught it:** body-force-driven Poiseuille with periodic streamwise BCs has ∂p/∂x = 0 and u_y = 0 — the unique canonical validation flow with zero pressure involvement. The FGE lid-driven cavity (pressure-driven) was float Python and is deprecated. The integer engine has never run a pressure-sensitive flow.

**Fix options (in order of preference):**
1. **Store per-cell rho as a 10th u32 word** (u16 engine: 40 B/cell vs 36; still 47% under unpacked 76 B). f[0] = rho_local − sum18, feq uses rho_local. Restores full weakly-compressible LBM. Bandwidth cost ~+11%, and the sim is compute-bound anyway (measured), so real cost is likely ~nil.
2. **He-Luo incompressible LBM:** feq_q = W_q·(p + rho0·(3cu + 4.5(cu)² − 1.5u²)) with per-cell pressure scalar p — same storage cost as option 1, better Galilean behavior at low Mach.
3. Keep constant-rho ONLY if the decisive experiment (below) shows the visual result is acceptable for gameplay — that's a legitimate art-directed choice, but it must be chosen, not stumbled into.

**Decisive experiment before engine commit:** flow past a solid square block (bounce-back walls) at moderate forcing, integer engine vs a float32 reference of the same LBM: constant-rho version will show flow punching through-ish/piling at the obstacle with weak lateral deflection and no vortex street; correct version deflects around and (at low enough viscosity) sheds. Second test: two opposing jets — constant-rho interpenetrates, correct version stagnates and splashes radially.

---

## Finding 4 (CRITICAL, latent): i32 overflow in usq_t + missing writeback clamps

**Overflow.** In the ORIGINAL `EQUILIBRIUM` (`packed-lbm-bench.html:94-95`) and in `pairBlock` (`dormant-validate.html:53-54`, also dormant-bench, compute-opt-bench):
`usq_c = W*rho*3/72; usq_t = usq_c * usq / (SCALE*SCALE)`.
At rho=18000, W=2 (face dirs): usq_c = 1500. UMAX = 0.75·1024 = 768, so usq = ux²+uy²+uz² can reach 3·768² = 1,769,472, and 1500 × 1,769,472 = 2.654e9 > i32 max 2.147e9. **Overflow threshold: usq > 1,431,655**, i.e. all-three-axes |u| ≥ ~691 (0.674·SCALE), or two axes at 768 plus third ≥ ~502 — inside the legal clamp range, reachable exactly when a spell pushes velocity to the (tanh-soft-clamped) limit. Two-axis max (1,179,648·1500 = 1.77e9) is safe; single-axis always safe. u10 (rho=500, usq_c=41) never overflows. `sim_batch_u16.html:311-312` has the same expression with rho=24000 (usq_c=2000, threshold usq > 1,073,741): safe at the winning SCALE=256 config (usq ≤ 110,592) but overflowed in the sweep's SCALE ≥ ~700 high-UMAX configs — treat those sweep rows as suspect.

**Fix:** divide first, multiply second: `let usq_s = usq / SCALE_I; let usq_t = usq_c * usq_s / SCALE_I;` — max intermediate 1500·1728 = 2.6e6. This is exactly what `OPTIMIZED_EQUILIBRIUM` (`packed-lbm-bench.html:150-156`) already does; the dormant files' pairBlock regressed to the unsafe ordering. One extra truncation, ≤1 LSB, irrelevant.

**Missing clamps.** `WRITEBACK_AA` (`dormant-validate.html:136-140` + all AA copies): `u32(out[...]) & 0xFFFFu` — WGSL u32() of a negative i32 wraps two's-complement, so col = −1 stores as 65535 → instant explosion the first time strong forcing drives a distribution negative. u10 packed-tick writeback (`packed-lbm-bench.html:623-628`): `u32(col[...]) & 0x3FFu` wraps mod 1024, both signs. **Fix: clamp before packing** — the correct pattern already exists at `sim_batch_u16.html:346-352` (`clamp(fc, 0, 65535)`). Note clamping trims mass out of moving populations and the derived f[0] silently absorbs it (momentum corrupted, mass "conserved") — so also add a debug counter (atomicAdd on clamp-hit) to know when it fires; in production it should be ~never.

---

## Secondary findings (design tensions and test-quality issues)

**S1. tau+ = 75 means creeping flow — the unresolved core tension.** nu = (tau − 0.5)/3 ≈ 24.8 lattice units. A 32-cell vortex diffuses out in L²/nu ≈ 41 ticks ≈ 5 frames at 8 ticks/frame; Re over a 128-cell obstacle at u≈0.1c is < 1. Swirling smoke/fire is impossible in this regime. Why the sweep (tau 25–200, `sim_batch_u16.html:75`) lives up there: integer TRT retains fneq via factor (OD−ON)/OD; at game-pretty tau≈0.6 the factor is small and stored-integer fneq of a few counts truncates to zero each tick → a quantization viscosity floor. The 53-level result and the honey viscosity are the same coin. Candidate paths, none yet explored: (a) error-feedback rounding — keep a small per-cell residue of the truncated collision remainder and re-inject next tick (costs storage, kills the truncation floor); (b) accept high nu and inject curl aesthetically via vorticity confinement (already flagged as the artistic knob in fluid-sim-best-practices.md); (c) larger RHO headroom within u16 to enlarge fneq counts (diminishing: already at 18000–24000 of 65535, and headroom is needed for compression transients); (d) stochastic rounding (conflicts with determinism unless the RNG is a deterministic hash of (cell, tick)). This decision shapes the whole game feel — do the tau-vs-look experiment early.

**S2. Dormant-cell skip is only valid where momentum ≈ 0, and the two variants differ.** Any skip scheme freezes a cell's slots while the AA parity of the world advances, so neighbors read frozen slots with swapped labels every other tick. At rest equilibrium f[q] = f[OPP[q]] → swap invisible → safe. At moving equilibrium (steady wind), f[q] − f[OPP[q]] = 2·linear ∝ u → neighbors read reversed-flow values → error injection at every dormant boundary. `dormant-validate.html` only tested pulses in quiescent fluid (rest background), so this is untested, not disproven. The dormant-flag variant gates on max|fneq| ≤ 5 only (`dormant-validate.html:200`) — UNSAFE, uniform wind is equilibrium with fneq≈0. The early-exit variant gates on activity = |jx|+|jy|+|jz| < 5 (`dormant-validate.html:230-231`) — gates momentum, safe by construction. Whatever ships must gate on momentum (or handle parity explicitly), and the dormancy rule must be re-derived against the FIXED AA scheme since skip semantics differ (correct-AA odd steps write into neighbors' cells — a skipped cell fails to deliver populations, not just to update itself; likely means: only skip cells on even steps, or require the dormant region to include the write-target halo).

**S3. The linear LUT reduces precision for zero benefit.** `sim_batch_u16.html:22-37, 207-213`: 256-entry LUT over ±SCALE quantizes u into buckets of SCALE/128 (= 2 at the winning SCALE=256, i.e. half the resolution of direct arithmetic) and costs a storage read per component. For LUT_CURVE='linear' this is strictly dominated by `clamp(u, -UMAX, UMAX)`. Keep the LUT mechanism only for tanh/soft-knee shaping; consider re-running the level count with direct clamp — the 53 may go up. Also `i = v*half/max(lut_range,1) + half` truncates toward zero, making the bucket at v≈0 double-width (asymmetric around zero; minor bias).

**S4. "53 velocity levels" has a geometric ceiling — don't oversell in disclosure docs.** The metric (`sim_batch_u16.html:459-465`) counts distinct trunc(jx·SCALE/RHO) over interior rows of a symmetric parabola: at WALL_Y=128 there are ~126 interior rows ≈ 63 unique half-profile values max. 53/63 is excellent, but the honest phrasing is "53 of ~63 resolvable profile rows distinguishable", not "the encoding supports 53 velocity levels" — the encoding's velocity resolution is SCALE/RHO-granular and much finer. Patent language should use the row-normalized framing (relevant to Claim IV support docs).

**S5. The mass-conservation benchmark is a tautology.** `packed-lbm-bench.html:1119-1131` computes finalMass = (rho0 − sum18) + sum18 — the comment admits it's rho0 by construction. The failure modes that actually exist (clamp/wrap corrupting momentum, Finding 4) are invisible to it. Replace with: total momentum drift over N ticks force-free (should be exactly 0 in periodic domain by integer symmetry), plus the clamp-hit atomic counter, plus min/max distribution tracking (the fmin/fmax code in sim_batch_u16's analysis is the right idea — port it).

**S6. 1D dispatch caps at 16.7M cells.** All benches use `dispatchWorkgroups(ceil(N/256))`, limit 65535 workgroups → N ≤ 16,776,960. The best-practices "Ultra" tier (256×256×192 = 12.6M) fits, but 256³ = 16.78M does NOT. sim_batch_u16 already has the correct 2D pattern (`wgX = min(total, 65535), wgY = ceil(total/65535)` with `linear_id = gid.x + gid.y*65535*64`, lines 381-384 + 217) — lift it into the shared module.

**S7. Repo/bench hygiene.** ~12 MB of results_*.jsonl in fluid_sandbox (ignored) plus one orphan 0-byte results file at repo root; duplicate Poiseuille PNGs at root and in fluid_ghost_encoding/; `readBuffer` helper leaks the staging buffer on mapAsync rejection (nit); ITERS=10 timing samples is thin for sub-2ms kernels — fine for 2x conclusions, don't quote 3.5% deltas without bumping to ~50 and reporting min/median.

---

## What SURVIVES this review (do not re-litigate)

- All timing/bandwidth conclusions: packed beats unpacked, sim is compute-bound not memory-bound, u10 AA ≈ 1.73 ms and u16 AA ≈ 1.79 ms at 4.72M cells (u16 ≈ +3.5%), eq-optimization gains, TRT ≈ BGK cost. Instruction mix of the buggy kernels matches correct ones; re-confirm timing once after fixes, expect parity.
- The ping-pong Poiseuille validation and clean53 result in sim_batch_u16.html (correct pairs, correct streaming, clamped writeback, LUT caveat S3 aside).
- The strategic decision: u16 (9 u32/cell) over u10 — precision 64x for ~3.5% time and +50% memory.
- The batched-sweep harness design, the isolation-testing methodology in dormant-validate (isolated buffers, GPU-side atomic diff), the `RESULT:` JSON + puppeteer protocol, the clean-divisor SCALE/RHO discipline, the pairBlock feq_b = feq_a − 2·linear trick.

## Recommended fix order

1. Shared `lbm-kernels.mjs` (Convention B, programmatic OPP/pairs) — makes fixes 2–4 single-point.
2. Finding 2 pair tables (mechanical, 5 min)
3. Finding 4 overflow reorder + writeback clamps (mechanical)
4. Finding 1 correct AA per the spec above + the three verification tests
5. Finding 3 decisive pressure experiment (block obstacle vs float reference), THEN decide rho storage
6. S2 dormancy re-derivation on the fixed kernel
7. S1 tau/viscosity exploration (biggest open design question)
