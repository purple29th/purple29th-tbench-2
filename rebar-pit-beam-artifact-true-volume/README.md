# codimango/rebar-pit-beam-artifact-true-volume

## Description

Agent writes from-scratch file at /app/solve.py using only standard library reading custom industrial CT scan with magic RPBV of corrosion pits in steel rebar inside concrete and reporting true pit volume in cubic millimetres.

Industrial CT has two artefacts at once. Beam hardening makes background drift slowly across the volume, not flat. Focal spot plus scatter blur is normalized but smears bright signal into wide halo while keeping total energy. A compact pit therefore looks like a large glowing cloud roughly twice the true size. Additionally concrete contains round air bubbles from mixing. The real corrosion pit is elongated along the rebar, while bubbles are round. In some scans a round bubble is larger and heavier than the real pit, so picking the biggest bright blob fails. Shape must be used.

Threshold counting fails by large margins. Generous level includes halo and gradient makes one side brighter, strict level loses thin elongation. No global level works. What is preserved is total signal under blur. Using it requires handling drifting background, separating elongated from round by shape, and deciding where faint halo ends without stepping into a nearby bubble. We grade at three percent.

## Completion Rates

Projected:

| Model | Pass | Notes |
|-------|------|-------|
| claude-opus-4-8 | 2/5 40% | sensitive to heavy round and halo |
| gpt-5.5 | 1/5 20% | overcounts halo or picks round bubble |
| meta/avocado | 1-2/5 20-40% | background bias or shape miss |
| oracle | 3/3 100% <3% error |

Naive: low threshold 90-130% over, high threshold 40-60% under, half-max Otsu 18-35% off, global integral without speckle filter fails heavy round by 5-8% over, largest-mass without shape filter picks round bubble and fails by large margin. Conservation with shape filter 1-2.7% error.

## Model Analysis

Requires binary parsing magic RPBV, version, dtype, nx ny nz, sx sy sz mm per voxel anisotropic, offset 36, x fastest. Background varies slowly due to beam hardening, must be estimated robustly. Elongated pit versus round bubble must be distinguished by aspect ratio. Plateau from most concentrated region, halo growth until shell mean hits noise floor but must avoid bridging to nearby bubbles. Volume equals integrated residual divided by plateau times voxel pitch.

## Anti-Cheating Analysis

Hardcoded outputs prevented because hidden scans generated at runtime in temp directory with random names, truth computed from clean set size times pitch, different versus sample. Different pitch, gradient, blur, noise.
Overfitting prevented because only scene file present.
Secure runner uses audit hook blocking sensitive paths and syscalls and banned imports.
From-scratch guard uses AST checks for banned libs and calls and attrs and substr bans.
New domain uses industrial CT rebar corrosion pit with beam hardening gradient and shape filter elongated versus round, embedding dedup novel and more tricky than flat background tasks.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
