# codimango/perovskite-film-pinhole-true-area

## Description

Agent writes from-scratch file at /app/solve.py using only standard library reading custom photoluminescence film scan with magic PPHA of pinhole defects in perovskite PV films and reporting true dead area in square millimetres.

PL imaging smears because photo generated carrier diffusion plus lens Airy spread is normalized blur conserving total quenched PL but inflating apparent dark area roughly twice. Threshold counting fails ninety to one hundred thirty percent over due to halo or forty to fifty five percent under due to thin feathered arms partial coverage. No fixed level works across films due to gain background diffusion noise shift.

Correct method is intensity conservation where true pixels equals sum of background subtracted signal over pinhole plus halo divided by plateau. That needs background estimation, isolation of main pinhole from dust, plateau via local mean filtered peak, and adaptive halo growth to noise floor without bridging specks. Area equals count times sx sy anisotropic.

## Completion Rates

Projected:

| Model | Pass | Notes |
|-------|------|-------|
| claude-opus-4-8 | 2-3/5 40-60% | sensitive to speck_heavy |
| gpt-5.5 | 1-2/5 20-40% | halo or branches |
| meta/avocado | 1-3/5 20-60% | background bias |
| oracle | 3/3 100% less than one percent error |

## Model Analysis

Fail modes are threshold any level twelve to one hundred thirty percent error, global integration without speck removal fails speck_heavy five to eight percent over, raw max plateau five to ten percent error, missing halo fifteen to twenty five percent under, counting pixels not energy thirty percent plus error. Requires binary parsing magic PPHA dtype nx ny sx sy millimetre per pixel offset, x fastest, robust background, main component isolation, filtered plateau, halo growth.

## Anti-Cheating Analysis

Hardcoded outputs are prevented because hidden scans are generated at runtime in temporary directory with random names, truth equals clean set size times pitch, different versus sample.
Overfitting is prevented because only scene file is in image, different pitch diffusion noise than hidden.
Secure runner uses audit hook blocking sensitive paths, blocking directory listings, blocking system popen exec fork and subprocess socket, blocking banned imports.
From-scratch guard uses AST checks for banned libraries and calls and attrs and substr bans.
New domain uses perovskite PL pinhole with slot die coating PL quench shunt risk, embedding dedup novel.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
