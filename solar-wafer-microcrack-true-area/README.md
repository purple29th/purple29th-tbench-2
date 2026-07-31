# codimango/solar-wafer-microcrack-true-area

## Description

The agent writes a from-scratch Python script at /app/solve.py using only the standard library that reads a custom electroluminescence wafer scan with magic ELCR of microcracks in monocrystalline PV wafers and reports true electrically dead area in square millimetres.

EL imaging smears cracks because carrier diffusion plus lens point spread is normalized but spreads dark signal into wide halo. Apparent dark cloud is roughly twice true crack size. Threshold counting fails by large margins, roughly ninety to one hundred thirty percent over when halo included or forty to fifty five percent under when thin branches lost. No fixed threshold works across wafers because gain, luminescence, diffusion length and background shift.

Correct method uses energy conservation where total dark deficit is preserved under blur, so true pixels equals sum of background subtracted signal over crack plus halo divided by plateau. That needs robust background, isolation of main crack from dust specks, plateau via local mean filtered peak to suppress read noise, and adaptive halo growth until shell mean falls to noise floor without bridging to specks. Area equals pixel count times sx sy with anisotropic pitch from header.

## Completion Rates

Projected from validation:

| Model | Trials | Pass rate |
|-------|--------|-----------|
| claude-opus-4-8 | 5 | 2-3/5 40-60% sensitive to speck_heavy |
| gpt-5.5 | 5 | 1-2/5 20-40% overcounts halo or loses branches |
| meta/avocado | 5 | 1-3/5 20-60% depends on background bias |
| oracle | 3 | 3/3 100% less than one percent error |

Naive counting low threshold ninety to one hundred thirty percent over, high threshold forty to fifty five percent under, half-max Otsu eighteen to thirty five percent off. Conservation half to one percent error.

## Model Analysis

Failure modes are threshold counting any level twelve to one hundred thirty percent error, global integration without speck removal fails speck_heavy by five to eight percent over, raw max for plateau noise spike five to ten percent error, missing halo growth fifteen to twenty five percent under, counting pixels not energy thirty percent plus error.

Requires binary parsing magic ELCR version dtype nx ny sx sy millimetre per pixel offset, x fastest, robust background, main component isolation, filtered plateau, halo growth.

## Anti-Cheating Analysis

Hardcoded outputs are prevented because hidden scans are generated at runtime in temporary directory with random names, geometric truth computed inside verifier from clean set size times pitch. Different truth versus sample.
Overfitting to visible is prevented because only scene file is present, different pitch diffusion noise than hidden.
Secure runner uses audit hook blocking sensitive paths, blocking directory listings, blocking system popen exec fork and subprocess socket, blocking banned imports.
From-scratch guard uses AST checks for banned libs plus banned calls and attrs and substr bans.
New domain uses PV wafer EL microcrack area with carrier diffusion dust artefacts, embedding dedup novel.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
