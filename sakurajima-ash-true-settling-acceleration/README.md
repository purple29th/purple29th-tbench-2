# sakurajima-ash-true-settling-acceleration — Sakurajima Ash True Settling Acceleration — Kagoshima Tea Farmer

Personal story: I am Haru, a tea farmer from Sakurajima, Kagoshima, Japan. Sakurajima erupts daily, ash falls on tea leaves, stunts growth. At 1am we image ash fall streaks on sticky glass slides with IR phosphor, tracer shows settling dynamics. Blur from humid air and lens smears but conserves photons. Rig writes ASHF container, magic ASHF, payload_start 48/64/80/96/128, ash_multiplier at 40-43 (hidden 1.22). De...

What works: photons conserved. Robust base median dimmest %, MAD sigma, candidates above background, 8-connected flood, keep elongated groups with mass filter dropping round and far dust, plateau mean of brightest interior, grow rings outward gathering residual until ring mean blends to noise while skipping dust groups to prevent bridging. length=area/0.35, velocity=length/0.80, acceleration=velocity/1.20*multiplier = area*2.976*multiplier mm/s^2. Within 1% if done right, graded 3%.

Unique — ASHF container, mm/s^2 ash settling acceleration, payload_start + multiplier embed fix must be read — ignore payload_start fails 96/128, ignore gain fails 22%.

## Completion Rates
Oracle 3/3 expected on 10 configs including 96/128/48/80 + randomized + extra
Avocado 0-1/5 due to gain + multi-component + shape filter, Opus 4/5, GPT 3/5

## Anti-Cheating
Varied width height pitch brightness base blur multiplier seed far placement random temp names input_a3f9.ashf so constant fails. Secure runner audit hook blocks /tests and link symlink hardlink bypass and banned imports. From-scratch stdlib only struct sys math random tempfile re.

Tags ashf ash-settling-acceleration mm/s^2 halo-recovery gain-calibration payload-offset individualized-human-story
