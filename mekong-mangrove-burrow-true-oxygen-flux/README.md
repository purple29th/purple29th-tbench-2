# mekong-mangrove-burrow-true-oxygen-flux — Mekong Mangrove Burrow True Oxygen Flux — Ca Mau Fisher Daughter

Personal story: I am Linh, a fisher's daughter from Ca Mau, Mekong Delta, Vietnam. My father farms mudskippers in mangrove burrows. At 1am we image burrow cross-sections with oxygen-sensitive phosphor that glows where O2 leaks. Phosphor blur from mud turbidity smears glow but conserves photons. The rig writes BURW container, magic BURW, payload_start 48/64/80/96/128, burrow_multiplier at 40-43 (hidden 1.22 at 96)...

What works: photons conserved. Robust base median dimmest %, MAD sigma, candidates above background, 8-connected flood, keep elongated groups with mass filter dropping round and far dust, plateau mean of brightest interior, grow rings outward gathering residual until ring mean blends to noise while skipping dust groups to prevent bridging. flux = area * 0.45 uL/min/mm2 * multiplier. Within 1% if done right, graded 3%.

Unique — BURW container, uL/min burrow oxygen flux, payload_start + multiplier embed fix must be read — ignore payload_start fails 96/128, ignore gain fails 22%.

## Completion Rates
Oracle 3/3 expected on 10 configs including 96/128/48/80 + randomized + extra
Avocado 0-1/5 due to gain + multi-component + shape filter, Opus 4/5, GPT 3/5

## Anti-Cheating
Varied width height pitch brightness base blur multiplier seed far placement random temp names input_a3f9.burw so constant fails. Secure runner audit hook blocks /tests and link symlink hardlink bypass and banned imports. From-scratch stdlib only struct sys math random tempfile re.

Tags burw burrow-oxygen-flux uL/min halo-recovery gain-calibration payload-offset individualized-human-story
