# FG Midstream

Can ghost data be injected into an already-flowing simulation?

## What it tests

32 cells. Uniform fluid (rho=400, momX=120) flowing for 10 ticks with zero ghost data. At tick 10, inject ghost=900 into cells 14-18. Continue flowing for 50 more ticks. Verify conservation.

This simulates a player casting a spell into existing fluid.

## Key findings

- Ghost injection at tick 10 succeeds immediately. No setup, no warm-up.
- Ghost total = 4500 exact from tick 11 through tick 60. Zero drift.
- Mass = 12800 exact throughout. Zero drift.
- The fluid was already in motion when ghost data was injected. No interaction.
- Ghost values lock in and hold perfectly regardless of prior flow state.

## Result

Mid-stream injection works. 0.00% mass drift. 0.00% ghost drift. 50 ticks after injection. Ghost data doesn't care when it arrives.
