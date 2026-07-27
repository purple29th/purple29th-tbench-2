# codimango/hydrothermal-sonar-heat-mapping

## Description

An autonomous underwater vehicle carries multibeam sonar over active seafloor. You receive a custom acoustic block `.svol` (magic `SVOL`) that contains one hydrothermal vent plume. Output its physical size in mm3.

Seawater scattering plus sonar side lobes smear bubble clouds into a bloated halo. The true plume that matters for flux is a compact high density core of microbubbles plus fine wispy tendrils that are dim after spread. Counting bright samples fails because bubble output, ambient level, and voxel pitch change per dive, and the sample file at `/app/data/scene.svol` has a different scale than hidden cases.

Subvoxel recovery is possible because scattering conserves total acoustic return. A careful implementation must parse the binary header manually, estimate sea water floor, discard isolated fish echoes, estimate interior acoustic level, and grow the region to capture faint tails without bridging to debris.

## Completion Rates

New task, no agent trials yet. Expected hard — similar family tasks require energy aware reasoning and fail pure threshold counting well outside tolerance.

## Model Analysis

* Header decode uses `struct` little endian, magic check, dtype 2 int16 or 16 float32, dimensions and millimetre pitch, then x fastest voxels. No array libraries allowed.
* Sea water floor is flat plus uniform noise, estimated from lower half via median and MAD, avoiding plume bias.
* Fish hits are removed by keeping plume with largest total residual via 26 connectivity flood fill, not largest count.
* Core level is hidden by blur and noise, recovered by 3x3x3 mean filtering and averaging a handful of brightest filtered voxels, not raw max.
* Fringe growth expands outward while shell average stays above noise floor, capturing diffuse halo without merging remote specks. Final mm3 multiplies by sx*sy*sz from header.

## Anti-Cheating Analysis

Hidden volumes are built fresh at test time in a random temp directory with random names, so sample memorization fails. The runner jails execution and blocks attempts to read the test directory or import disallowed imaging and system modules. Source must be stdlib only parsing.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
