# Fluid Ghost Encoding (FGE): Comprehensive Patent Disclosure
## A Computational Substrate for Data Storage and Transport Within Lattice Boltzmann Method Simulations

**Inventor:** Robert Alexander, Auralab Technologies
**Date of Disclosure:** April 8-9, 2026
**Document Type:** Patent Disclosure for Counsel

---

## Table of Contents

1. Summary of Invention
2. Background and Prior Art
3. The Discovery Chain
4. Mathematical Foundation
5. The Ghost Mode Diffusion Kernel
6. Bounce-Back Symmetry Classification
7. Ghost Persistence Under Correct Physics
8. The Ghost Stamp Mechanism
9. Ghost-Independence Proof
10. Exact Integer Encoding via Power-of-Two Norms
11. Bit Depth Scaling Analysis
12. Spatial Multiplexing
13. Claims Structure
14. Supporting Experimental Evidence
15. Definitions

---

## 1. Summary of Invention

Fluid Ghost Encoding (FGE) is a method for embedding, storing, transporting, and recovering arbitrary digital data within the distribution functions of a Lattice Boltzmann Method (LBM) fluid simulation, using the non-hydrodynamic ("ghost") moment channels of the Multiple Relaxation Time (MRT) collision operator as a zero-cost data plane.

The key insight: in D3Q19 MRT-LBM, the 19x19 transformation matrix has 19 moment rows. Rows 0-3 are conserved quantities (density and momentum). Rows 4-10 are physical non-conserved quantities (energy and stress). Rows 11-18 are non-hydrodynamic "ghost" modes that do not appear in the macroscopic Navier-Stokes equations. The published literature treats these 8 ghost modes as numerical artifacts to be damped. FGE instead treats them as free data channels.

By setting the relaxation rate for selected ghost channels to zero ("passthrough"), data encoded into those channels survives the collision step unchanged. The standard forward transform (M @ f) reads the data; the standard inverse transform (M_inv @ m) writes it back. No additional computation is required beyond what the MRT collision already performs. The data is encoded as weighted contributions distributed across all 19 velocity distributions at each lattice cell, transported through the lattice by the standard streaming step, and reconstituted at destination cells by the same matrix transforms.

The result is a data storage, transport, and broadcast mechanism that operates inside a fluid simulation at zero additional computational cost, zero additional memory, and zero modification to the streaming step.

---

## 2. Background and Prior Art

### 2.1 Lattice Boltzmann Method (LBM)

The Lattice Boltzmann Method simulates fluid dynamics by evolving probability distribution functions f_q on a discrete lattice. Each lattice cell stores 19 distribution values (in D3Q19) corresponding to 19 velocity directions including rest. At each timestep, two operations occur:

**Collision:** distributions are relaxed toward a local equilibrium that depends on macroscopic density and velocity. In the Single Relaxation Time (BGK) scheme, all distributions relax at the same rate. In Multiple Relaxation Time (MRT), the collision is performed in moment space, allowing independent relaxation rates for each moment.

**Streaming:** each distribution propagates to the neighboring cell along its velocity direction. This step is identical regardless of collision scheme.

### 2.2 MRT Collision

In MRT-LBM, the collision step is:

1. Forward transform: m = M @ f (convert distributions to moments)
2. Relaxation: m_new[k] = m[k] - S[k] * (m[k] - meq[k]) for each moment k
3. Inverse transform: f = M_inv @ m_new (convert moments back to distributions)

The matrix M is a 19x19 transformation matrix. Each row defines a moment as a linear combination of the 19 distributions. The inverse M_inv reconstructs distributions from moments.

### 2.3 The Transformation Matrix

The specific matrix used in this invention is the weight-orthogonal D3Q19 MRT matrix published by Fakhari, Bolster, and Luo (2017) in the Journal of Computational Physics (Vol. 341, pp. 22-43, Appendix A.2, Eq. A.6). This matrix satisfies the weight-orthogonality condition:

    sum_q W[q] * M[k][q] * M[j][q] = 0  for k != j

where W = [12,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1] are the integer lattice weights (with factor of 36 absorbed). The Fakhari 2017 paper provides:

- Chapman-Enskog proof that this matrix recovers the incompressible Navier-Stokes equations
- Six 3D benchmark validations including rising bubbles at 1000:1 density ratio, falling drops with bag breakup, crown splashing, and coalescence cascades at Ohnesorge number 10^-4

### 2.4 Ghost Modes in Prior Art

The published LBM literature universally treats non-hydrodynamic ghost modes (rows 11-18 in our ordering) as numerical artifacts. Standard practice is to relax them toward zero at maximum rate (S[k] = 1 or 2) to improve numerical stability. No prior art was found for:

- Using ghost modes as data storage channels
- Setting ghost relaxation rates to zero for data preservation
- Encoding arbitrary data via the M_inv back-transform
- Exploiting the ghost diffusion kernel for data transport
- Classifying ghost channels by bounce-back symmetry for wall-safe encoding
- The ghost stamp mechanism (self-replicating spatial broadcast)

---

## 3. The Discovery Chain

The invention emerged through a specific chain of discoveries, each building on the last:

### 3.1 Initial Observation

In the process of developing SpellARia (an ASL gesture-based browser game with WebGPU fluid simulation), the inventor observed that the D3Q19 MRT matrix contains 19 rows but only 11 correspond to physical quantities (density, 3 momentum, energy, energy-squared, 2 normal stress differences, 3 shear stresses). The remaining 8 rows (indices 11-18) are non-hydrodynamic modes that do not appear in the macroscopic equations. Setting their relaxation rate to zero (passthrough) means data in those channels survives collision unchanged.

### 3.2 The Encoding Mechanism

Data is encoded into ghost channels via the standard inverse transform. To store value G in ghost channel k at a given cell:

1. Compute moments: m = M @ f
2. Set m[k] = G * norms[k] (where norms[k] is the weighted norm of row k)
3. Reconstruct: f[q] = sum_k(M_inv_s[q][k] * m[k]) / LCD

The data G is distributed as weighted fragments across all 19 distributions according to the k-th column of M_inv. To read the data back: compute m = M @ f, then G = m[k] / norms[k]. The encode and decode are performed by the same matrix operations that the MRT collision already executes. No additional computation is required.

### 3.3 The Zero-Cost Proof

The ghost passthrough requires FEWER operations than standard MRT collision, not more. Standard MRT computes relaxation for all 19 moments. Ghost passthrough skips the relaxation computation for channels 11-18 (or a selected subset). The operations saved (8 multiplications and 8 additions per cell per timestep for full ghost passthrough) exceed the operations added (none). The net computational cost of ghost data storage is negative.

### 3.4 The Row 10 Correction

During verification, it was discovered that row 10 of the transformation matrix (pxz, the xz shear stress) is a physical moment, not a ghost mode. The physical shear stress moments are pxy (row 8), pyz (row 9), and pxz (row 10). The ghost modes begin at row 11. This yields exactly 8 ghost channels (rows 11-18), not 9 as initially assumed.

Moment classification:
- Rows 0-3: Conserved (density, 3 momentum components)
- Rows 4-10: Physical non-conserved (energy, energy-square, 2 normal stress differences, 3 shear stresses)
- Rows 11-18: Non-hydrodynamic ghost modes (8 channels)

### 3.5 Matrix Identification

The weight-orthogonal D3Q19 MRT matrix used throughout this work was identified as equivalent (up to row reordering) to the matrix published by Fakhari, Bolster, and Luo (2017). This identification provides external validation via the published Chapman-Enskog analysis and benchmark tests. The integer weights W = [12,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1] and the full 19x19 matrix entries match exactly.

---

## 4. Mathematical Foundation

### 4.1 Weight-Orthogonality

The transformation matrix M satisfies:

    sum_q W[q] * M[k][q] * M[j][q] = norms[k] * delta(k,j)

where delta is the Kronecker delta. This means every ghost moment is orthogonal to every physical moment under the weighted inner product. The practical consequence: data encoded in ghost channel k contributes ZERO to every physical moment at the cell where it is stored. The ghost is invisible to the physics locally.

### 4.2 Integer Arithmetic Framework

All operations are performed in integer arithmetic. The key quantities:

- Weighted norms: norms[k] = sum_q W[q] * M[k][q]^2
- Least Common Multiple: LCD = lcm(norms[0], norms[1], ..., norms[18]) = 144
- Scaled inverse: Minv_s[q][k] = W[q] * M[k][q] * (LCD / norms[k])
- Back-transform: f[q] = sum_k(Minv_s[q][k] * m[k]) / LCD (with integer rounding)

The integer framework eliminates floating-point error entirely. All operations are deterministic and reproducible across platforms.

### 4.3 Equilibrium Distribution

The velocity-dependent equilibrium distribution is computed as:

    feq[q] = W[q]*rho/36 + W[q]*rho*3*(c.u)/(36*SCALE) + W[q]*rho*9*(c.u)^2/(72*SCALE^2) - W[q]*rho*3*u^2/(72*SCALE^2)

where SCALE is a velocity scaling factor (typically 1000) that maps the low-Mach-number velocity field to integer range. This is the same equilibrium that produces correct Poiseuille flow (q/c approximately 0.75) in BGK simulations.

---

## 5. The Ghost Mode Diffusion Kernel

### 5.1 Kernel Equation

Each ghost channel has a characteristic transport fingerprint described by the Ghost Mode Diffusion Kernel:

    K[i] = W[i] * M[k][i]^2 / d_k

where K[i] is the kernel weight for lattice direction i, and d_k = norms[k] is the weighted norm. This equation was derived from the structure of the MRT inverse transform and verified computationally for all 8 ghost channels with zero error.

### 5.2 Channel Classification

The 8 ghost channels organize into four symmetry groups reflecting the cubic lattice structure:

**Group 1: Shear Plane (1 channel)**
m[10] (reclassified as physical in the corrected analysis; originally described here but removed from the ghost channel count)

**Group 2: Directional Beams (3 channels, rows 11-13)**
m[11] (X Beam), m[12] (Y Beam), m[13] (Z Beam). Each has approximately 6x anisotropy along its primary axis. Two-thirds of kernel weight on the axis-aligned directions, one-third leaking into diagonals. Together they form a natural coordinate basis.

**Group 3: Diagonal Crosses (3 channels, rows 14-16)**
m[14] (YZ Cross), m[15] (XZ Cross), m[16] (XY Cross). Kernel weight distributed across edge diagonals with no axis-aligned component. Approximately 2x anisotropy.

**Group 4: Isotropic Breaths (2 channels, rows 17-18)**
m[17] (The Breath) and m[18] (The Second Breath). Both have 1.00x anisotropy (perfectly isotropic). They spread data equally in all directions. m[17] has LCD=48, m[18] has LCD=16. These two channels provide the largest encoding capacity among ghost channels.

---

## 6. Bounce-Back Symmetry Classification

### 6.1 Discovery

All 8 ghost channels were classified by their behavior under the bounce-back boundary condition (standard LBM wall treatment, which reverses the direction of distributions). For each channel k, the symmetry condition is:

    M[k][q] compared to M[k][opp(q)]

where opp(q) is the opposite lattice direction to q.

### 6.2 Results

**Anti-symmetric channels (rows 11-16):** M[k][q] = -M[k][opp(q)] for all q. Ghost data encoded in these channels NEGATES at wall boundaries. Data is destroyed by bounce-back.

**Symmetric channels (rows 17-18):** M[k][q] = M[k][opp(q)] for all q. Ghost data encoded in these channels is PRESERVED under bounce-back. Data survives wall interaction unchanged.

### 6.3 Structural Origin

Channels 17 and 18 are fourth-order even-parity polynomial moments. Their basis polynomials are:
- Row 17: (2|c|^2 - 3)(3cx^2 - |c|^2)
- Row 18: (2|c|^2 - 3)(cy^2 - cz^2)

Even-order polynomials are invariant under direction reversal (c -> -c) by definition. The wall-safety of channels 17 and 18 is a structural property of the polynomial moment basis under the cubic symmetry group, not a numerical coincidence.

### 6.4 Practical Implication

In any simulation with solid boundaries (walls, obstacles, complex geometry), channels 17 and 18 are the preferred ghost data channels because they are immune to the bounce-back boundary condition. Together they provide approximately 43 bits of wall-safe ghost storage per cell at u32 precision.

---

## 7. Ghost Persistence Under Correct Physics

### 7.1 Experimental Setup

Two parallel simulation universes were constructed using identical code, identical initial conditions, and identical parameters. The only difference: Universe A contains ghost data (value = 1,000,000) in channel m[18] at the center cell; Universe B has no ghost data. Both use:

- Grid: 3x3x3 periodic lattice (27 cells)
- Arithmetic: 64-bit integer (no floating point)
- Density: 10^9 integer units per cell
- Collision: MRT with velocity-dependent equilibrium (same formula that produces correct Poiseuille flow in BGK), stress relaxation at omega = 10/13 (kinematic viscosity nu = 0.267), ghost channel m[18] at passthrough (rate = 0)
- Streaming: standard push scheme with periodic boundaries
- Duration: 180,000+ timesteps (limited by wall-clock time, not instability)

### 7.2 Results: Ghost Conservation

| Timestep | Ghost Value | Conservation |
|----------|-------------|--------------|
| 1 | 1,000,000 | 100.000% |
| 100 | 999,989 | 99.999% |
| 1,000 | 999,981 | 99.998% |
| 10,000 | 999,981 | 99.998% |
| 100,000 | 999,981 | 99.998% |
| 180,032 | 999,982 | 99.998% |

The ghost value stabilized at 999,981 +/- 1 from timestep 1,000 onward. The 18-unit discrepancy (0.002%) is attributable to accumulated integer division rounding (LCD=144). This error scales inversely with integer precision and vanishes at u32 scale with properly sized values.

### 7.3 Results: Physics Convergence

The maximum difference in any physical moment (density, momentum, energy, stress) between the ghost universe and the no-ghost control universe:

| Timestep | Max Physical Difference (ppm) |
|----------|-------------------------------|
| 1 | 4,000 |
| 10 | 808 |
| 50 | 31 |
| 100 | 0.3 |
| 200 | 0.015 |
| 1,000+ | 0.014 (rounding floor) |

By timestep 200, the two universes are physically indistinguishable. The residual difference of approximately 15 integer units is at the floor of integer arithmetic precision.

### 7.4 Mechanism

**Why the ghost survives:** The MRT collision operator relaxes each moment independently. Ghost channel m[18] has relaxation rate zero (passthrough). The collision reads m[18] from distributions via M @ f, leaves it unchanged, and writes it back via M_inv @ m. The data passes through without modification.

**Why the physics heals:** When ghost-carrying distributions stream to neighboring cells, they create small perturbations in the neighbors' physical moments. These perturbations are non-equilibrium contributions. The MRT collision relaxes all non-equilibrium physical moments toward equilibrium at each timestep. Energy moments (rate 1.0) are fully corrected in one tick. Stress moments (rate omega) are partially corrected each tick. The perturbation decays exponentially to zero while the ghost data remains invariant.

---

## 8. The Ghost Stamp Mechanism

### 8.1 Discovery

When ghost data is injected at a single lattice cell and the simulation is allowed to evolve, the ghost data propagates through the lattice via the diffusion kernel (Section 5). In a periodic domain, the ghost value spreads from the injection point to all cells, eventually reaching a uniform distribution where every cell carries an equal share of the original value.

### 8.2 Experimental Demonstration

Ghost value 2^20 = 1,048,576 was injected at the center of a 3x9x9 periodic lattice (243 cells). MRT collision with correct velocity-dependent equilibrium, omega = 10/13.

**Propagation timeline:**

- Tick 0: Ghost at one cell (1,048,576). All others zero.
- Tick 1: Diamond pattern emerges. Nearest neighbors receive ~25% each.
- Tick 5: Bell-curve distribution. Ghost has reached most cells.
- Tick 10: Ghost present at all 27 cells. Gradient from center.
- Tick 30: Nearly uniform across all cells.
- Tick 50: Perfectly uniform. Every cell holds approximately 4,315 (= 1,048,576 / 243).
- Tick 100-200: Remains uniform. Conservation: 100.003%.

### 8.3 Properties of the Ghost Stamp

1. **Self-replicating:** A single write propagates to all cells automatically via physics.
2. **Self-healing:** If any cell's ghost value is damaged, neighboring cells' values diffuse to restore it.
3. **Readable from any cell:** After equilibration, every cell contains the stamp. Read any cell, multiply by N_cells, recover the original.
4. **Globally conserved:** The sum of ghost values across all cells is invariant (to within integer rounding).
5. **Zero transport cost:** The standard streaming step carries the ghost data. No additional transport code.
6. **Deterministic:** The spreading pattern follows the kernel equation exactly. The evolution is predictable and reproducible.

### 8.4 Stamp as Watermark

The ghost stamp functions as an indelible watermark embedded in the fluid simulation. The watermark:
- Cannot be removed without disrupting the simulation state
- Is distributed across all cells (no single point of failure)
- Survives wall interactions (channels 17, 18)
- Is readable at any spatial location
- Persists indefinitely (180,000+ timesteps demonstrated)
- Encodes a numerical value with exponential precision (2^N distinguishable levels)

---

## 9. Ghost-Independence Proof

### 9.1 Discovery

A critical experiment tested the physics divergence between MRT-with-passthrough and standard BGK across a range of ghost values from 1 to 10^6. The result:

| Ghost Value | Physics Divergence at Tick 50 (ppm) |
|-------------|-------------------------------------|
| 1 | 17,308.2 |
| 10 | 17,308.2 |
| 100 | 17,308.2 |
| 1,000 | 17,308.2 |
| 10,000 | 17,308.2 |
| 100,000 | 17,308.2 |
| 1,000,000 | 17,308.2 |

The physics divergence is EXACTLY identical regardless of ghost value. The ghost data has zero effect on the physics divergence between MRT and BGK.

### 9.2 Interpretation

The 17,308 ppm divergence is caused by the MRT collision operator treating ghost moment m[18] differently than BGK would (passthrough vs. relaxation toward equilibrium). This is a difference between two valid numerical methods for the Navier-Stokes equations, not an error introduced by the ghost data. The Chapman-Enskog analysis proves that ghost mode relaxation rates do not appear in the macroscopic equations. Both MRT-with-passthrough and BGK recover the same Navier-Stokes equations at the continuum limit.

### 9.3 Significance for Patent

This result proves that FGE introduces zero physics contamination from the ghost data itself. The ghost data is truly decoupled from the fluid dynamics. The differences between MRT-with-passthrough and BGK are properties of the numerical method, independent of whether any ghost data is present.

---

## 10. Exact Integer Encoding via Power-of-Two Norms

### 10.1 Discovery

Channel 18 has norm (weighted inner product with itself) equal to 16 = 2^4, which is a power of two. The LCD (Least Common Denominator across all moment norms) is 144 = 16 * 9. The ghost contribution to each distribution during the back-transform is:

    f_ghost[q] = Minv_s[q][18] * m[18] / LCD
              = W[q] * M[18][q] * 9 * m[18] / 144
              = W[q] * M[18][q] * m[18] / 16

Since m[18] = ghost_value * norms[18] = ghost_value * 16, this simplifies to:

    f_ghost[q] = W[q] * M[18][q] * ghost_value

This is an exact integer with zero remainder for ANY integer ghost value. The ghost contribution to every distribution divides the LCD exactly. No rounding error is introduced by the ghost encoding or decoding.

### 10.2 Verification

Computational verification confirmed that for all 19 directions q and all tested ghost values, the remainder of (Minv_s[q][18] * ghost_moment) modulo LCD is exactly zero.

### 10.3 Split Back-Transform

This property enables a "split back-transform" where the physical and ghost contributions to each distribution are computed separately:

    f[q] = round(sum_{k=0..17} Minv_s[q][k] * m[k] / LCD) + Minv_s[q][18] * m[18] / LCD

The physical part uses standard integer rounding. The ghost part divides exactly. This ensures that rounding errors from physical moments never contaminate the ghost channel, and the ghost channel never introduces rounding errors into the physical distributions.

### 10.4 Power-of-Two Ghost Values

When the ghost value itself is a power of two (e.g., 2^20), the entire ghost encoding pathway operates exclusively with bit shifts and integer multiplies. No division is required. This is optimal for GPU hardware where bit-shift operations are single-cycle.

---

## 11. Bit Depth Scaling Analysis

### 11.1 Framework

The ghost encoding capacity depends on the integer bit depth of the simulation. Each distribution f[q] is stored as an unsigned integer of B bits. The density RHO approximately equals 2^B. The ghost value must be small enough that the ghost perturbation does not cause any distribution to overflow or underflow.

### 11.2 Per-Cell Ghost Capacity

The maximum ghost value per cell is approximately:

    ghost_max approximately RHO / 144 approximately 2^(B-7)

This yields "ghost bits" approximately equal to B - 6 per cell.

### 11.3 Stamp Bits After Spatial Spreading

After the ghost stamp equilibrates across N cells, each cell holds ghost_max / N. The number of distinguishable levels ("stamp bits") is:

    stamp_bits = ghost_bits - log2(N)

### 11.4 Bit Depth Table (81-cell grid, 3x3x9)

| Bit Depth | Ghost Bits | Stamp Bits | Per-Cell Levels | Encoding Capacity |
|-----------|------------|------------|-----------------|-------------------|
| u8 | 2 | 0 | 1 | Boolean flag |
| u10 | 4 | 0 | 1 | Existence detection |
| u16 | 10 | 4 | 17 | Team ID, zone type |
| u20 | 14 | 8 | 270 | Color, item class |
| u24 | 18 | 12 | 4,315 | Rich metadata |
| u32 | 26 | 20 | 1,104,672 | Arbitrary data |

### 11.5 Experimental Verification

Each bit depth was tested with a full 100-tick simulation including ghost injection, MRT collision with correct equilibrium, streaming, and ghost readback. Conservation at u32: 100.00%. At u24: 100.01%. At u20: 100.22%.

---

## 12. Spatial Multiplexing

### 12.1 Concept

Multiple ghost stamps can coexist in the same simulation by injecting different values at spatially separated locations. Each stamp spreads locally via diffusion. Before the stamps mix (interference), each can be read back independently from its local neighborhood.

### 12.2 Mixing Time

Two stamps separated by D cells will interfere after approximately D^2 / (2 * D_eff) timesteps, where D_eff approximately 0.75 cells^2/tick for channel 18 (isotropic diffusion).

### 12.3 Application Example

In a 128^3 game grid with stamps every 32 cells:
- Number of stamps: 64 (= 4^3)
- Bits per stamp: approximately 9 (at u32)
- Total ghost data: 576 bits
- Time before interference: approximately 512 ticks (approximately 8 seconds at 60 fps)
- Use case: region-level metadata (team ownership, zone type, environmental state)

### 12.4 Using Both Wall-Safe Channels

Channels 17 and 18 are independent. Each can carry a separate ghost stamp at the same spatial locations. Channel 17 (norm=48) provides approximately 19 bits per cell. Channel 18 (norm=16) provides approximately 24 bits per cell. Combined: approximately 43 bits of wall-safe ghost data per spatial stamp location.

---

## 13. Claims Structure

### Claim I: Ghost Mode Data Encoding

A method for encoding digital data into the non-hydrodynamic moment channels of a lattice Boltzmann simulation, comprising: computing the forward moment transform (M @ f), setting one or more non-hydrodynamic moment values to encode desired data, and computing the inverse moment transform (M_inv @ m) to distribute the encoded data across the lattice velocity distributions.

### Claim II: Zero-Cost Data Preservation via Passthrough Relaxation

A method for preserving encoded data through the MRT collision step by setting the relaxation rate of the data-carrying moment channels to zero, whereby the encoded data passes through the collision step unchanged while all physical moments are relaxed normally.

### Claim III: Ghost Mode Diffusion Kernel for Data Transport

A method for transporting encoded data through a lattice via the standard streaming step, wherein the encoded data propagates according to the ghost mode diffusion kernel K[i] = W[i] * M[k][i]^2 / d_k, requiring no additional transport computation beyond the standard LBM streaming step.

### Claim IV: Bounce-Back Symmetry Classification for Wall-Safe Encoding

A method for selecting ghost channels that preserve encoded data under the bounce-back boundary condition, comprising: classifying ghost channels by their symmetry under direction reversal, and selecting channels with even parity (symmetric) polynomial basis functions, specifically channels corresponding to fourth-order even-parity moments.

### Claim V: Ghost Stamp Broadcast Mechanism

A method for broadcasting a single data value to all cells in a lattice region, comprising: injecting the value into a ghost channel at a single cell, allowing the simulation to evolve until the ghost data equilibrates to a uniform field, and reading the stamp value from any cell by multiplying the local value by the number of cells.

### Claim VI: Exact Integer Encoding via Power-of-Two Norms

A method for eliminating rounding error in ghost data encoding by selecting ghost channels whose weighted norms are powers of two, and encoding ghost values as multiples of said norms, whereby the ghost contribution to each distribution divides the LCD exactly.

### Claim VII: Split Back-Transform

A method for computing the MRT inverse transform in two parts: a physical part (columns 0-17 of M_inv) with standard integer rounding, and a ghost part (column 18 of M_inv) with exact integer division, ensuring zero cross-contamination between physical rounding errors and ghost data.

### Claim VIII: Spatial Multiplexing of Ghost Stamps

A method for encoding multiple independent data values in a single lattice simulation by injecting different ghost values at spatially separated locations, wherein each stamp occupies a local region determined by the diffusion timescale, and stamps are read back before mutual interference.

### Claim IX: Bit-Depth-Adaptive Ghost Encoding

A method for adapting ghost data capacity to the integer precision of the simulation, comprising: computing the maximum ghost value as a function of bit depth and lattice weights, computing the stamp capacity as a function of ghost bits and cell count, and selecting encoding parameters to maximize data capacity at the target bit depth.

### Claim X: Ghost Data as Simulation Watermark

A method for embedding an indelible, self-replicating watermark in a fluid simulation, comprising: encoding a numerical value into a ghost channel at one or more cells, allowing the simulation to broadcast the value to all cells via natural physics evolution, and reading the watermark from any cell at any subsequent timestep.

---

## 14. Supporting Experimental Evidence

All results were produced by Python scripts using NumPy with 64-bit integer arithmetic (dtype=np.int64). No floating-point operations appear in any simulation loop. All scripts are available as source code and produce the results described above when executed.

### 14.1 Key Scripts

1. **ghost-180k-ticks.py**: Two parallel universes, 180,032 timesteps, ghost conservation and physics convergence proof
2. **collision_is_the_correction.py**: Tick-by-tick two-universe comparison showing physics healing around ghost
3. **tea_with_ghost.py**: Single ghost cell analysis showing exact coupling coefficients to all neighbors
4. **the_equation.py**: Complete neighbor interaction table (small integer coefficients, global sum zero)
5. **ghost_ride.py**: Bounce-back symmetry classification (wall-safe vs. anti-symmetric channels)
6. **ghost_scaling.py**: Ghost-independence proof (identical 17,308.2 ppm for ghost=1 through ghost=10^6)
7. **exact_ghost.py**: Power-of-two norm proof (all remainders exactly zero)
8. **harmonic_thread.py**: Ghost stamp propagation in 3x3x3 (100% conservation, uniform by tick 70)
9. **thread_corridor.py**: Ghost stamp in 3x3x9 corridor (100% conservation, uniform by tick 50)
10. **ghost_expands.py**: Ghost stamp in 3x9x9 volume (100.003% conservation, uniform by tick 50)
11. **bit_worlds.py**: Multi-bit-depth comparison (u8 through u32)
12. **inverse_readout.py**: BGK ghost recovery via inverse transfer function
13. **advective_ghost.py**: Ghost behavior under correct BGK physics (exponential decay analysis)

### 14.2 Reference Publication

Fakhari, A., Bolster, D., and Luo, L.-S. (2017). "A weighted multiple-relaxation-time lattice Boltzmann method for multiphase flows and its application to partial coalescence cascades." Journal of Computational Physics, 341, 22-43. DOI: 10.1016/j.jcp.2017.03.062

### 14.3 Related Publication

Hartinger, M. D., et al. (2026). Frontiers in Astronomy and Space Sciences. DOI: 10.3389/fspas.2026.1700061 (co-authored by inventor, establishing research context in data sonification and novel data encoding methods)

---

## 15. Definitions

**Distribution function (f[q]):** The probability of finding a fluid particle at a given lattice cell moving in velocity direction q. In integer LBM, this is a non-negative integer proportional to the particle count.

**Moment (m[k]):** A linear combination of distribution functions defined by the k-th row of the transformation matrix M. Physical moments include density, momentum, energy, and stress. Ghost moments are non-hydrodynamic quantities that do not appear in the macroscopic equations.

**Ghost mode:** A non-hydrodynamic moment (rows 11-18 in D3Q19 with this ordering) that has no effect on the recovered Navier-Stokes equations. In standard LBM practice, ghost modes are damped. In FGE, they carry data.

**Passthrough:** A relaxation rate of zero, meaning the moment value is unchanged by the collision step. In the relaxation equation m_new = m - S*(m - meq), passthrough corresponds to S = 0, giving m_new = m.

**Bounce-back:** A boundary condition that reverses the direction of distributions at a wall. A distribution heading into the wall is reflected back in the opposite direction. This is the standard wall treatment in LBM.

**Weight-orthogonality:** The property that distinct rows of the transformation matrix are orthogonal under the weighted inner product defined by the lattice weights W. This ensures that ghost moments do not couple to physical moments at any cell where all 19 distributions are present.

**LCD (Least Common Denominator):** The least common multiple of all weighted norms, used as the common denominator in the integer back-transform. For the D3Q19 matrix used here, LCD = 144.

**Ghost stamp:** The equilibrium state reached when a ghost value injected at a single cell spreads to fill all cells uniformly via the diffusion kernel. The stamp value at each cell equals the original value divided by the number of cells.

**Split back-transform:** A method for computing the inverse moment transform in two parts (physical and ghost) to exploit the exact divisibility of the ghost contribution.

---

*End of Disclosure*

*Prepared: April 9, 2026*
*Inventor: Robert Alexander, Auralab Technologies*
*For review by: Michael Lubitz, GTT Group/Ideaship*
