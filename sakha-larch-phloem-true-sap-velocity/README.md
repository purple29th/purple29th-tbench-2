# sakha-larch-phloem-true-sap-velocity — Sakha Larch Phloem True Sap Velocity — Verkhoyansk Evenk Reindeer

Personal story: I am Ayta, an Evenk reindeer herder's granddaughter from Batagay, Verkhoyansk, Sakha Republic — coldest inhabited place. My grandmother marks larch trunks for resin. At 1am in January at -52C we cut a 0.3 mm thick phloem slab, drip fluorescein tracer, and image with a Hamamatsu ORCA sCMOS in a heated yurt lab. The tracer is carried by sap flow; blur from ice fog and lens smears the streak, but pho...

What works: photons conserved. Robust base median dimmest %, MAD sigma, candidates above background, 8-connected flood, keep elongated groups with mass filter dropping round and far dust, plateau mean of brightest interior, grow rings outward gathering residual until ring mean blends to noise while skipping dust groups to prevent bridging. Area = count*sx*sy, length = area / 0.30 mm vessel width, velocity = length / 0.60 s * multiplier = area * 5.555... * multiplier mm/s. Within 1% if done right, graded 3%.

Unique — SAPF container, mm/s phloem sap flow velocity, payload_start + multiplier embed fix must be read — ignore payload_start fails 96/128, ignore gain fails 22%.

## Completion Rates
Oracle 3/3 expected on 10 configs including 96/128/48/80 + randomized + extra
Avocado 0-1/5 due to gain + multi-component + shape filter, Opus 4/5, GPT 3/5

## Anti-Cheating
Varied width height pitch brightness base blur multiplier seed far placement random temp names input_a3f9.sapf so constant fails. Secure runner audit hook blocks /tests and link symlink hardlink bypass and banned imports. From-scratch stdlib only struct sys math random tempfile re.

Tags sapf phloem-sap-flow-velocity mm/s halo-recovery gain-calibration payload-offset individualized-human-story
