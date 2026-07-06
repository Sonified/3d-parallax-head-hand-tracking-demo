# Fluid Sim Best Practices

Notes from surveying real-time GPU fluid implementations. Focus on presentation-layer techniques that are solver-agnostic and applicable to our D3Q19 TRT LBM running on WebGPU compute.

## Adaptive Quality Stepping

Auto-downgrade simulation parameters when FPS drops. Detect device capability at startup, let user override.

Tunable knobs for LBM:
- Ticks per frame (4-12)
- Grid resolution
- Visual particle density
- Render resolution (can be lower than sim resolution)

Example tiers:
| Tier | Ticks/frame | Grid | Particles |
|------|-------------|------|-----------|
| Low | 4 | 96x96x64 | 10K |
| Medium | 6 | 128x128x96 | 50K |
| High | 8 | 192x192x128 | 100K |
| Ultra | 12 | 256x256x192 | 500K |

Source: haxiomic/GPU-Fluid-Experiments uses 5 tiers scaling particles (16K-1M), fluid grid (1/6 to 1/2 screen), and Jacobi iterations (12-30). GPL-3.0 licensed, no code reuse, concepts only.

## Dye / Passive Scalar Rendering

Per-channel color decay at different rates creates color-shifting trails from a single injection color.

Example decay rates per tick:
- R: 0.98
- G: 0.95
- B: 0.97

White injection gradually shifts through warm tones as channels decay at different speeds. Completely solver-agnostic. For SpellARia: inject dye where spells impact the fluid, let it advect with the velocity field, decay per-channel for elemental color signatures.

Implementation: separate passive scalar field (3 floats per cell for RGB), advected by the LBM velocity field each tick, no feedback into the fluid physics.

## Force Injection as Line Segment

Interpolate input force along the path between frames, not as a point splat at the current position.

Why: at low input framerates (hand tracking at 30fps, touch at variable rate), point splats create discontinuous impulses. Line-segment injection with Gaussian falloff gives smooth, continuous force regardless of input rate.

Technique:
- Store previous input position
- For each cell, compute distance to the line segment (prev_pos to curr_pos)
- Apply force with `exp(-distance / radius)` falloff
- Taper force along the segment so the leading edge is stronger

For hand tracking input into the sim, this is directly relevant. The hand position between frames should be interpolated and force injected along the path.

## Selective Bilinear Interpolation

Use NEAREST filtering on simulation data for speed. Only manually bilinear-interpolate where visual smoothness matters (rendering pass, dye advection).

For LBM on integer grids: the simulation operates on exact integer cell positions. When sampling the velocity field to drive visual particles or dye rendering, manual bilinear interpolation from the integer grid gives smoother visual results without affecting simulation performance.

Cost: 4 texture lookups + 2 mix operations per interpolated sample. Only pay this in the render path.

## Solver Comparison Notes

Surveyed the Stam/projection method (Chorin splitting, Semi-Lagrangian advection, Jacobi pressure solve). Key findings:

- Requires 18-30 iterative passes just for pressure. LBM gets pressure implicitly in 1 collision step.
- Semi-Lagrangian advection is unconditionally stable but introduces numerical diffusion (acts as low-pass filter). LBM streaming is exact (no interpolation, no diffusion from transport).
- Projection method is incompressible only. LBM is weakly compressible, capturing pressure waves at physical speed of sound (cs = 1/sqrt(3)).
- Fewer Jacobi iterations = physically incorrect results (vortices collapse). Fewer LBM ticks/frame = correct physics, just less elapsed sim-time. This is a fundamental architectural advantage.
- At equal resolution and dimensionality, LBM is approximately 2x more efficient (16 passes vs 35 per frame at 8 ticks).
- WebGPU compute shaders are 30-50% faster than WebGL fragment-shader GPGPU for data-parallel work (no rasterization tax).

## Vorticity Confinement (optional, aesthetic)

If visual curl feels damped, vorticity confinement is a standard forcing term that counteracts numerical diffusion. This is an artistic knob, not a solver fix. LBM at low viscosity (high Reynolds number) should produce rich vorticity naturally. Only add confinement if the visual result needs more dramatic swirl.

## Decoupled Grid and Visual Resolution

The simulation grid can be much coarser than the visual output. Trilinear interpolation between cells creates a smooth continuous field from a blocky grid.

**Trilinear interpolation**: sample the 8 surrounding grid cells, lerp along x (4 lerps), y (2 lerps), z (1 lerp). Cost: 8 buffer reads + 7 multiply-adds per sample. Trivial on GPU.

Three independent resolution layers:

| Layer | Resolution | Cost |
|-------|-----------|------|
| Physics grid (LBM) | 128^3 = 2M cells | Expensive (19 distributions, collision, streaming) |
| Velocity sampling | Continuous (trilinear) | Cheap (8 reads per sample) |
| Visual particles/dye | 100K-1M particles | Cheap (1 velocity lookup + Euler integrate per particle) |

A 128^3 grid with 500K interpolated particles can look as good as a 256^3 grid at 1/8th the physics cost. The grid is invisible once you render through particles or dye rather than coloring cells directly.

This also unlocks i32 over i16: 128^3 at i32 (160 MB) uses less memory than 192^3 at i16 (270 MB), with native WGSL types, no bit-packing, and massive precision headroom (+-2.1B vs +-32K).

## Meta-Layer: Material Properties as Scalars

Every cell carries scalar fields beyond the LBM distributions. These describe what's in the cell and how it behaves. All integer, all on the same grid, all processed by CA rules.

```
cell {
    f[19]: i32           // LBM distributions

    // what's here (concentrations, 0-10000)
    nature: i32
    fire: i32
    water: i32

    // how it behaves (material properties)
    stiffness: i32       // spring constant
    anchor: i32          // connection to ground
    mass: i32            // weight
    damping: i32         // oscillation decay rate
    porosity: i32        // how much fluid passes through
    
    // current state (signed, dynamic)
    stress_x: i32        // force being experienced
    stress_z: i32
    displacement_x: i32  // lean from rest position
    displacement_z: i32
}
```

Memory at 128^3 with ~10 extra i32 scalars: 2.1M cells x 10 x 4 bytes = 84 MB. Total with LBM = ~244 MB.

### Fluid-Structure Interaction via Porosity

The nature scalar directly controls partial bounce-back in the LBM collision:

```
porosity = nature[cell] / 10000
f_out = (1 - porosity) * f_collide + porosity * f_bounceback
```

High nature = more solid = more drag. A tree trunk (nature=9500) is nearly solid. A leafy canopy (nature=1500) barely disturbs the flow. Wind automatically diverts around trunks, slows through canopy, creates wakes and vortex shedding. One lerp per distribution.

### Structural Response: Bending and Springing Back

Structures that span multiple cells (trees, tall grasses, flags) respond to wind force and return to rest through scalar propagation:

1. **Force**: compute wind load from LBM momentum exchange at each cell
2. **Propagate down**: accumulate force downward through connected cells (stress flows toward roots)
3. **Restore up**: anchored cells generate restoring force proportional to displacement and stiffness
4. **Integrate**: update displacement from net force, apply damping
5. **Redistribute**: displacement smears effective nature into neighboring cells

```
// Cell with nature=8000, displacement_x=3000 (leaning 30% right):
effective_nature[here]  = 8000 * (10000 - 3000) / 10000 = 5600
effective_nature[right] += 8000 * 3000 / 10000           = 2400
```

When wind stops, displacement decays, nature returns to its home cell. The tree springs back. The fluid sees the effective (displaced) nature field, so aerodynamics respond to the bent shape. Wind load reduces as the tree streamlines itself.

### Material Properties via LUT

Different materials are just different rows of scalar values, same CA rules:

| Property | Trunk | Branch | Leaf | Rock | Water |
|----------|-------|--------|------|------|-------|
| stiffness | 9000 | 5000 | 1000 | 10000 | 0 |
| anchor | 10000 | 3000 | 0 | 10000 | 0 |
| mass | 8000 | 4000 | 500 | 10000 | 1000 |
| damping | 9500 | 9000 | 7000 | 10000 | 0 |
| porosity | 9500 | 6000 | 2000 | 10000 | 0 |

A rock is nature with max everything. A leaf is nature with min stiffness, zero anchor. Same rules, different numbers, different behavior. No special cases.

### Ecosystem Feedback Loop

The fluid can affect the structures, and structures affect the fluid:

- Wind force exceeds breaking threshold: nature decreases (branches snap)
- Broken nature advects downwind as debris (carried by the fluid)
- Debris settles where velocity is low (seeds new growth)
- New nature grows via CA rules (low nature spreads to neighbors over time)
- Growing nature increases porosity, redirecting wind, changing where seeds land

Trilinear interpolation of the effective nature field gives smooth visual transitions across all of this. A particle between a trunk cell and a displaced canopy sees a continuous gradient, not a blocky step.

## Spell Cohesion: Keeping Things Together

Fluids naturally diffuse concentrations. A fireball in a plain fluid sim will spread, thin, and vanish. Spells need a containment force to stay coherent.

### Cohesion as a Scalar

Add to each cell:

```
cohesion: i32    // 0 = gas/smoke (spreads freely), 10000 = tight orb
```

Each tick in the CA step, after fluid advection, apply an inward gathering force:

```
// Find local center of mass of this element
center = weighted average position of element in nearby cells
direction = center - this_cell_position

// Pull toward center, proportional to cohesion
gather_force = direction * cohesion * concentration[cell] / SCALE
```

High cohesion = stays together. Low cohesion = disperses. Same element, same physics, one number changes the behavior.

### Spell Catalog by Cohesion

| Spell | Element | Cohesion | Behavior |
|-------|---------|----------|----------|
| Fireball | fire | 9000 | Tight orb, travels as a unit |
| Flamethrower | fire | 2000 | Fans out from source |
| Wildfire | fire | 500 | Disperses, catches on nature |
| Fire tornado | fire | 6000 | Holds together but spirals |
| Ice shield | ice | 10000 | Nearly rigid, doesn't spread |
| Frost breath | ice | 1000 | Expanding cone, dissipates |
| Poison cloud | poison | 300 | Drifts with wind, spreads wide |

### Composite Forces: Fire Tornado Example

A fire tornado is three injected forces working with the fluid:

1. **Angular momentum**: tangential force in a circle around the cast point (makes it spin)
2. **Updraft**: vertical force (hot air rises)
3. **Cohesion**: medium-high, keeps fire from scattering as it spins

```
for each cell in circle(cast_position, radius):
    tangent = cross(up, cell - center)
    force[cell] += tangent * spin_strength
    force_y[cell] += updraft_strength
    fire[cell] += fire_amount
    cohesion[cell] = 6000
```

The LBM creates a real vortex: pressure drops at center, velocity increases at edges. The updraft stretches it vertically. Cohesion keeps the fire from flying apart. It's a real tornado with fire in it.

### Surface Tension (Alternative / Complement)

For more defined spell boundaries, apply force at the element's edge using concentration gradient:

```
grad_fire = (fire[right] - fire[left], fire[up] - fire[down], ...)
tension_force = -surface_tension * grad_fire
```

Force acts only at the boundary, pulling inward. Interior cells feel nothing. Creates well-defined surfaces like water droplets. Can combine with cohesion: surface tension for shape, cohesion for bulk gathering.

### Cohesion as Gameplay Target

Cohesion is a targetable property, not just a passive trait:

- **Dispel**: zeros out cohesion. The fire is still there but spreads and dissipates harmlessly.
- **Wind vs fireball**: push force vs cohesion. If wind force exceeds the gathering force, the fireball stretches, thins, breaks apart.
- **Strengthen**: a buff spell could increase cohesion, making an ally's fireball tighter and harder to deflect.
- **Merge**: two low-cohesion fire clouds that overlap combine into one larger fire. Two high-cohesion fireballs bounce off each other (pressure repulsion from the fluid).

No special-case code for any of these interactions. Just force vs cohesion, and the fluid resolves the outcome.
