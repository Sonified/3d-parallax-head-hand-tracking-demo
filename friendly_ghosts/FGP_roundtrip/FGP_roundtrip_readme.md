# FG Roundtrip

Can ghost data survive the integer MRT transform round-trip?

## What it tests

Inject a known value into a ghost moment, transform to distribution space (M_inv), transform back (M), read it out. Does the value come back?

## Key findings

- The standard d'Humieres MRT matrix is NOT weight-orthogonal (16 off-diagonal nonzero entries). This causes cross-channel leakage in integer arithmetic.
- LCD (least common denominator) of M_inv is 47880. Dividing by this truncates and leaks mass.
- Ghost channels 16, 17, 18 have column LCD of 8 (power of 2). Exact with bit shift.
- Ghost channels 10, 12 have LCD 72 and 24. Exact when values are multiples of LCD.
- All 9 channels achieve exact round-trip when values are scaled by their channel's LCD.
- Mass correction (f[0] absorbs truncation) keeps total mass exact.
- Round-to-nearest decoding ((moment + LCD/2) / LCD) recovers all 9 channels.

## Result

9 channels, 85 bits per cell, exact round-trip in integer arithmetic. 200/200 random stress tests with drift compensation.
