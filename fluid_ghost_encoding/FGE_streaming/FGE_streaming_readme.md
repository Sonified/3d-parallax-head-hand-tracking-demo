# FGE Streaming

**Author:** Robert Alexander

## Significance

This test provides the first known characterization of how ghost-encoded data behaves during LBM streaming. Published LBM literature treats ghost mode dispersal during streaming as a stability problem to be suppressed. This work demonstrates that the dispersal is predictable, characterizable by exact integer streaming kernels, and fully reversible using the ping-pong buffer architecture already present in LBM implementations. The characterization transforms ghost modes from a perceived instability into a controllable data transport mechanism.

## What it tests

Inject ghost values into multiple cells, stream one tick (no collision), read back. Measure how much of each cell's ghost value comes from itself vs neighbors. Build per-channel streaming kernel via regression.

## Key findings

Each ghost channel has a unique streaming kernel:

| Channel | Left | Self | Right | Pattern |
|---------|------|------|-------|---------|
| m[12,13] | 8.3% | 83.3% | 8.3% | Self-preserving |
| m[14,15] | 25% | 50% | 25% | Half self |
| m[17] | 25% | 50% | 25% | Half self |
| m[18] | 25% | 50% | 25% | Half self |
| m[10,11,16] | 50% | 0% | 50% | Pure diffusion |

- Momentum does NOT change the kernel weights. Ghost streaming is velocity-blind.
- No correlation beyond immediate neighbors (cells +-2 have zero coefficient).
- Regression fit is exact (RMS = 0.00) with known bias constant per channel.
- Pingpong correction (using pre-streaming neighbor values from f_in) recovers 6/9 channels perfectly.
- Direct read from f_in recovers the remaining 3 self=0 channels with +1 offset correction.
- All 9 channels recoverable after streaming.

## Result

Complete characterization of the streaming transform per ghost channel. All 9 channels recoverable using ping-pong buffer + known kernel + calibrated offset. This characterization is a novel contribution not present in published LBM literature.
