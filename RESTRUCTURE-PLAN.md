# Restructure Plan: TECHNICAL-DISCLOSURE.md

## Goal
Reorder claims so the most fundamental contributions lead. Biggest discoveries first, enabling technology second, applications third.

## Current Order → New Order

| Current | Title | New Position | New Number |
|---|---|---|---|
| IV.G (subclaim) | Ghost Mode Metadata Transport | Independent claim, position 1 | **Claim I** |
| IV (independent) | Packed Integer LBM (minus IV.G) | Position 2 | **Claim II** |
| VII (independent) | Flat-Grid Force Field Approximation | Position 3 | **Claim III** |
| V (independent) | Integer Voxel Physics Substrate | Position 4 | **Claim IV** |
| II (independent) | Zero-Readback GPU ML Pipeline | Position 5 | **Claim V** |
| I (independent) | Embodied Interaction System | Position 6 | **Claim VI** |
| III (independent) | Gesture Intelligence | Position 7 | **Claim VII** |
| VI (independent) | Deterministic Multiplayer | Position 8 | **Claim VIII** |

## Subclaim Renumbering

| Old | New |
|---|---|
| IV.A-IV.F | II.A-II.F (stays same letters, claim number changes) |
| VII.A-VII.E | III.A-III.E |
| V.A-V.F | IV.A-IV.F |
| II.A-II.F | V.A-V.F |
| I.A-I.N | VI.A-VI.N |
| III.A-III.C | VII.A-VII.C |
| VI.A-VI.F | VIII.A-VIII.F |

## Cross-Reference Map (all 37 references)

Each entry: line (approx), old reference → new reference

### References FROM old Claim I (becoming VI):
1. "Claim II" (latency) → "Claim V"
2. "I.C" (coordinate system) → "VI.C"
3. "I.F" (aim ray, 2 occurrences) → "VI.F"
4. "I.G" (gaze) → "VI.G"
5. "Claim I" (parallax, 2 occurrences) → "Claim VI"
6. "I.M" (spatial audio, 2 occurrences) → "VI.M"
7. "I.J" (lip sync, 3 occurrences) → "VI.J"
8. "Claim II.A" (benchmarks) → "Claim V.A"
9. "Claim II" (pipeline, 2 occurrences) → "Claim V"
10. "Claim III" (gesture) → "Claim VII"
11. "Claim VI" (multiplayer) → "Claim VIII"
12. "Claim V" (meta grid) → "Claim IV"

### References FROM old Claim II (becoming V):
13. "II.A" (self-refs, 3 occurrences) → "V.A"
14. "II.B" (preprocessing) → "V.B"
15. "II.C" (kernel fusion) → "V.C"
16. "II.E" (op decomposition) → "V.E"
17. "I.A and I.J" → "VI.A and VI.J"
18. "Claim II" (self-ref) → "Claim V"
19. "I.K" (networked state) → "VI.K"
20. "Claim V" (simulation) → "Claim IV"

### References FROM old Claim IV (becoming II):
21. "IV.B" (sub-word packing) → "II.B"
22. "Claim VI" (multiplayer) → "Claim VIII"

### References FROM old Claim V (becoming IV):
23. "V.E" (universal blur) → "IV.E"
24. "V.B" (behavior LUT) → "IV.B"
25. "II.C" (kernel fusion) → "V.C"
26. "VI.C" (field coherence) → "VIII.C"

### References FROM old Claim VI (becoming VIII):
27. "Claim V" (substrate) → "Claim IV"
28. "Claim VII" (force field) → "Claim III"
29. "V.E" (blur shader) → "IV.E"
30. "VI.E" (rollback) → "VIII.E"
31. "Claim VI" (self-ref) → "Claim VIII"

### References FROM old Claim VII (becoming III):
32. "V.A" (cell packing) → "IV.A"
33. "Claim V" (simulation) → "Claim IV"

## Header text changes
- Preamble: "four independent invention families" → "eight independent invention families"
- Prior art context section: move to after Claim VIII or keep at top (keep at top, it applies broadly)
- Ghost mode claim (new I): needs its own independent claim opener (currently subclaim language)

## Execution order
1. Extract all claim sections as text blocks
2. Write new Claim I (ghost modes) with independent claim language
3. Reassemble in new order
4. Find-replace all cross-references per map above
5. Update preamble ("eight independent invention families")
6. Push
7. Spin up audit agent to verify all cross-references

## Risk mitigation
- Do NOT do surgical edits. Write the complete file in one pass.
- Verify line count is similar before and after.
- Git diff will show the restructure clearly.
