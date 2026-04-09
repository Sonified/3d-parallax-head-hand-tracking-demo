# FGE Two Population: Isolation and Classification

Proves that two ghost populations coexist in a shared 128x128 domain with perfect binary classification for 32 seconds on a single ghost channel.

## File

- `two_population_isolation.py`

## What it proves

Population A (value 50,000) fills the left half. Population B (value 5,000,000) fills the right half. 100x magnitude separation. Pure diffusion, no body force. 128x128x1 = 16,384 cells.

Column-level classification: each x-column assigned to whichever population has higher average.

### Results

| Tick | Contrast | Classified | At 120fps |
|------|----------|-----------|-----------|
| 0 | 0.980 | 128/128 | cast moment |
| 120 | 0.741 | 128/128 | 1 second |
| 240 | 0.642 | 128/128 | 2 seconds |
| 480 | 0.502 | 128/128 | 4 seconds |
| 960 | 0.315 | 128/128 | 8 seconds |
| 1920 | 0.125 | 128/128 | 16 seconds |
| 3840 | 0.020 | 128/128 | 32 seconds |

Conservation: **100.000%** at all checkpoints.

At tick 3840, A_avg=2,475,437 and B_avg=2,574,563 -- only 4% apart -- yet every column is still correctly classified. The gradient direction is the information carrier, not the magnitude contrast.

## Key insight

The diffusion front creates a monotonically softening gradient that never reverses direction. Classification persists for the full diffusion timescale (~21,845 ticks), not because the magnitudes are different, but because the spatial gradient still points the right way.

## Generalizes to

Any two-source scenario: competing chemical species, drug compounds, player factions, labeled flow streams, ecological populations, epidemiological spread.

## Claim support

Supports **I.L** (two-population isolation) and **I.M** (population distribution statistics). The gradient as information carrier is the key claim: the gradient direction persists long after magnitude contrast has faded.
