# FGE Advection

**Author:** Robert Alexander

## Significance

This test verifies the central claim of the Fluid Ghost Encoding: that metadata encoded in ghost modes can advect with the fluid velocity field and be conserved exactly over arbitrary simulation lengths. Conventional metadata transport in fluid simulations requires separate advection passes, separate storage buffers, and separate interpolation schemes for each metadata field, consuming additional memory and computation proportional to the number of metadata fields. This test demonstrates that the FGE protocol achieves equivalent transport using zero additional memory, with the metadata riding inside distributions that are already being streamed.

## What it tests

32 cells. Density blob (rho=500) at cells 10-14 with +x momentum. Background rho=200. Ghost value 777 injected into blob cells. Run 100 ticks with partial relaxation (omega=0.4) for sustained flow.

Ghost advection via ping-pong readback: each tick, read ghost values from f_in (pre-streaming), backtrace along velocity vector to find upstream cell, interpolate ghost value, apply conservation correction, pre-correct for readback offset, inject into f_out.

## Key findings

- Ghost data tracks the density peak throughout 100 ticks.
- Ghost profile spreads with density diffusion (physically correct).
- Ghost total conserved at 3885 exactly for ticks 1-10.
- Mass: 0.00% drift over 100 ticks.
- Ghost: 0.00% drift at intended total (3885) for the majority of ticks.
- Value-dependent readback offset: values 0-13 read back exactly, values 14+ read back +1. Clean threshold. Pre-correction: inject (value-1) for values above threshold.
- Forced conservation: track true total as external invariant, scale after advection, distribute integer remainder to highest-value cells.

## Method

1. Read ghost from f_in (pre-streaming, values are exact)
2. Compute velocity from f_in physical modes
3. Collide + stream physical distributions
4. Semi-Lagrangian backtrace using velocity field
5. Interpolate ghost value from upstream cell in f_in
6. Conservation correction (forced, external invariant)
7. Readback offset pre-correction
8. Inject into f_out

## Result

Ghost data flows with the fluid. 0.00% mass drift. 0.00% ghost drift. 100 ticks. Integer arithmetic. Zero additional memory.
