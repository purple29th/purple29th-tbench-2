# battery-dendrite-shorting-true-charge

## What this task is about
I inspect lithium ion pouch cells after fast charge cycling. Metallic lithium plates as dendrites that pierce the polyethylene separator and trap charge that can drive internal shorts. Imaging is done with X-ray fluorescence that lights up trapped lithium metal. The fluorescence volume is stored in custom binary .ldch with magic LDCH. Because carrier diffusion in the scintillator plus the optics point spread function smears intensity, the glow is spread far beyond the metal core. We need total trapped charge in milliCoulombs as safety metric, not the blurred blob size.

## Why this is not the usual volume task
The output asked is charge in mC. Lab calibration gives 2.8 mC per cubic mm of solid lithium dendrite. So we first recover hidden metal volume via energy conservation, then multiply by calibration to get charge. Grader checks charge, which couples voxel count, anisotropic spacing sx sy sz, and calibration. This is battery safety domain, not MEMS acoustic leak. The artefacts are round lithium plating islands that form on anode surface and are harmless for short risk, plus far dust specks. Only elongated branching dendrites that cross the separator count.

## How the hidden test is designed
This is a precision recovery problem where simple brightness binning is off by a lot. If you pick a low brightness level you swallow the whole smeared aureole and you overcount by nearly double. If you pick a high level you lose the needle tips that never reach full brightness and you undercount by third to half. The brightness, diffusion width, and spacing vary per file so no single level ever works. The smear does not create photons, it only relocates them, so total energy is conserved over dendrite plus its faint skirt.

A correct solver must:
* read header with data offset not hardcoded
* find main metal via 26 connectivity after 4 sigma seeding
* distinguish shapes: keep structures where longest side at least 8 and 1.6 times shortest (branching dendrites), discard near cubic plating islands
* get clean background from median of whole volume and noise scale from lower half MAD
* get true core intensity from 3 by 3 by 3 smoothed peak using top eight average, not raw max
* expand from main metal outward shell by shell until mean shell residual falls to noise floor, skipping artefact voxels so you do not bridge into a speck
* compute voxel count as integrated residual divided by core intensity, then physical volume via sx sy sz, then charge via 2.8 factor

Test suite generates volumes at runtime in temp dirs with random names input_<hex>.ldch, truth computed geometrically from true dendrite set outside solver sandbox. It includes speck heavy where large dust balls add more than three percent energy if not removed, and plating heavy where round plating islands outweigh dendrite tips. Naive whole volume energy sum fails speck heavy. Largest mass without shape check fails plating heavy.

## Files to look at
* /app/solve.py is what you must write, final printed token is charge
* /app/data/scene.ldch is example for development
* environment/Dockerfile installs pytest and copies example
* tests/test_outputs.py is secure verifier

## Expected behavior
* Oracle reference that does the steps above lands within one percent, grading tolerance three percent, so it passes all
* Fixed level, Otsu, half max fail all heldouts
* No numpy scipy imaging graph libs, stdlib struct sys math random tempfile re only, plus guards on os io pathlib etc
* You must work on any temp path, not hardcode scene

## Creation notes
Battery safety domain with pouch cell teardown, polyethylene separator pierce, lithium inventory tracking, X-ray fluorescence of trapped metal, calibration 2.8 mC per mm3, mass based main needle isolation and halo growth. Reference solution in solution/solve.py.
