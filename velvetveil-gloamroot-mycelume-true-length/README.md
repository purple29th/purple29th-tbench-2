# velvetveil-gloamroot-mycelume-true-length — Willamette Foxfire v2

I work at H.J. Andrews Experimental Forest, Oregon, mapping Armillaria ostoyae honey fungus foxfire that glows faintly at 1am on duff slabs. Family are foragers — need total active rhizomorph cord length per slab to predict bloom zones where boar dig. Image with Hamamatsu ORCA sCMOS, rig writes custom MYCR container magic MYCR dtype 2=int16/16=float32 width height sx sy anisotropic mm per pixel payload_start 48/64/80/96/128 at byte 28 post_veil_multiplier at byte 40 scaling mm 0.85-1.35 hidden 1.22 at offset 96. Embed fix must be read — ignore payload_start fails 96/128, ignore gain fails 22%.

We have elongated ragged cords along fir grain that are signal, plus round Bacillus bacterial colonies compact false foxlights to skip, plus far corner soil dust specks near 5,5 and 75,75 that add 6-12% each if summed. Some slabs have two distant cords both counted — single biggest fails 40-50%. Fog scattering plus lens PSF smears glow into halo, low threshold doubles length, high clips 1/3-1/2. No fixed threshold works because base, blur, gain shift per lot. Elongated means long side at least ten and more than one point six times short side and at most thirty five, mass at least zero point three five times biggest.

What works: photons conserved. Estimate base from dimmest fraction, noise from lower half deviation, candidates above background, eight connected flood, keep elongated groups via shape filter dropping round and far dust, plateau mean of brightest inside kept cords, grow shells outward collecting residual until ring blends to noise floor while skipping dust groups to prevent bridging. Area via residual over plateau times sx sy, length via hyphal repeat zero point four mm divided i.e. times two point five times multiplier. Within one percent if done right, graded three percent. Sample about thirteen to fifteen mm.

Unique name not element, not mg, forest mycology domain.

Author Tosin Daniel Jimoh purple29th@meta.com

## Completion Rates v2

Each run is k=5 trials. Trial scores 1.0 only if all verifier cases pass.

| Model | Pass rate (k=5) |
|---|---|
| Oracle | 3/3 deterministic, local 13/13 pytest including 96/128/48/80 + randomized + extra, 2 configs dtype 2 for int16 coverage, 3 configs anisotropic sx!=sy |
| Avocado | 0-1/5 due to gain + multi-pool + aspect filter |
| Opus | 4/5 |
| GPT | 3/5 |

## Model Analysis

Low thr grabs fog aureole doubles, high clips tails loses half. No base inflates. Dust adds 6-12% per dot. Round bacterial overcounts. Missing halo under 15-25%. Ignoring multiplier low by 0.85-1.35 fails 96. Hardcoded offset 64 fails 96/128. Anisotropic mishandle fails square-pixel assumptions.

## Anti-Cheating v2

Varied width height pitch brightness base blur multiplier seed far placement random temp names input_a3f9.mycr so constant fails. Secure runner audit hook blocks /tests and link symlink hardlink bypass and banned imports os link etc and chr/fromhex/b64decode tricks. From-scratch stdlib only.

## Tags

Tags willamette foxfire gloamroot mycelume honey-fungus armillaria rhizomorph photon-veil duff-slab halo-recovery gain-calibration payload-offset forest-mycology individualized-human-story anisotropic

Author Tosin Daniel Jimoh purple29th@meta.com
