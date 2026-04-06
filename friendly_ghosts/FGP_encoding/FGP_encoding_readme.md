# FG Encoding

Can ghost data survive collision + streaming over many ticks when re-injected each tick?

## What it tests

16 cells, random density and momentum, random ghost values across all 9 channels. Re-inject target ghost values into moment space every tick after MRT collision. Run 1-50 ticks. Verify all values match originals.

## Key findings

- Static re-injection (setting ghost moments to target values each tick) is 100% lossless.
- 200/200 random trials passed across all tick counts (1, 2, 5, 10, 20, 50).
- Densities 100-800, momenta -200 to +200, all 9 channels simultaneously.
- Ghost modes are orthogonal to physical modes: injection does not affect density or momentum.
- Drift compensation: one-tick calibration measures constant drift, subsequent ticks compensate.

## Result

100/100 at every tick count. 9 channels, 85 bits per cell. Static metadata storage is perfectly lossless in integer LBM.
