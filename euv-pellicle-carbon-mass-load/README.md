# euv-pellicle-carbon-mass-load

## What this task is
I inspect EUV pellicles that protect reticles in lithography scanners. During exposure the pellicle slowly grows carbon soot from cracked hydrocarbons. The soot absorbs EUV and heats, so we need to know total carbon mass in micrograms on the freestanding membrane.

Imaging is with X-ray fluorescence that lights up carbon. The data is custom binary .epcm with magic EPCM. Diffusion in the scintillator plus lens point spread smears the soot signal far beyond the true carbon core. The job is to recover hidden carbon mass in ug.

## Why precision matters
Simple brightness cut fails badly. Low level pulls in the whole aureole and overcounts near double. High level misses thin feathered soot edges that never get fully bright and undercounts by third to half. Background brightness gain and diffusion width vary per file so no single level works.

Blur does not create photons, it only moves them, so total energy is conserved over soot plus its skirt. That lets us recover true metal via sum over skirt divided by true core level.

Correct approach must:
* read header with data offset not hardcoded
* get background from median and noise from lower half MAD
* find main carbon via 26 connectivity seeded at 4 sigma, keep elongated streaks along pellicle crazing where longest at least 8 and more than 1.6 times shortest, drop near cubic airborne particles
* get core level via 3 by 3 by 3 local mean smoothed peak using top four average not raw max
* expand outward shell by shell until mean shell residual falls to noise floor while skipping artefact voxels
* compute voxel count as total residual divided by core level, volume via sx sy sz, mass via 2.1 ug per mm3 calibration

## Files
* /app/solve.py you write, last token is mass ug
* /app/data/scene.epcm sample
* environment/Dockerfile installs pytest and copies sample
* tests secure verifier generates volumes at runtime in temp dirs with random names

## Pass criteria
Error less than 3 percent on heldouts including speck heavy where large dust balls add more than 3 percent energy if not removed and particle heavy where round airborne particles outweigh thin soot tips. Naive whole volume energy sum fails speck heavy. Largest mass without shape check fails particle heavy.

## Difficulty
* Oracle 100 percent via conservation plus shape plus halo
* Naive threshold 0 percent 80 to 130 over or 30 to 50 under
* Global without filter 0 on speck heavy
* Expected similar to foundry thermal void: gpt 2 out of 5, opus 2 out of 5, avocado 0 to 1 out of 5

## Anti cheating
Stdlib only struct sys math random tempfile re. No numpy scipy imaging graph libs, no os io pathlib etc. No hardcoded sample mass. Secure runner audit hook blocks /tests test_outputs heldout _gen GEOM_TRUTH etc.
