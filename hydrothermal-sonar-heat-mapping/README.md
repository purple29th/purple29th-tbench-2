# codimango/hydrothermal-sonar-heat-mapping

## Description

Deep ocean robots use multibeam sonar to map heat plumes above black smokers. You get a custom 3D acoustic volume `.svol` with magic `SVOL` that encodes a single vent plume. The job is to output true heat plume size in mm3.

The sonar image is misleading because beam side lobes plus suspended particles scatter sound. What looks like a bloated bright cloud is actually a compact core of dense microbubbles with delicate wispy tendrils that are invisible after scattering. If you count bright voxels you will be far off, because the same threshold fails when bubble output, ambient sea level, and anisotropic sampling change per dive. Header fields `sx,sy,sz` differ every scan.

The only way to hit 3 percent tolerance is to understand the sonar physics and recover subvoxel accuracy from total acoustic energy, handling sea water, fish echoes, core brightness, and diffuse tails.

## Completion Rates

No trials yet — new task. Expected to be hard like other vent and ink family tasks where only energy aware methods pass.

## Model Analysis

* **Header:** manual little endian parsing of magic, version, dtype code, grid extents and pitch, then voxel payload in x fastest order.
* **Ambient sea:** background is flat seawater return plus uniform noise, estimated via median of whole stack and MAD of lower half to avoid plume bias.
* **Biological hits:** isolated bright spots are fish or debris, not plume. Keeping region with largest summed background subtracted signal via 26 neighbour flood fill discards them.
* **Core acoustic level:** true saturated backscatter never seen directly after scattering plus noise. A 3x3x3 mean filter and averaging the brightest few filtered voxels gives stable reference.
* **Diffuse fringe:** plume energy extends beyond obvious bright mask. Expanding outward while shell average stays above noise floor captures it, stopping before connecting to far specks.

## Anti-Cheating Analysis

Grading builds new plumes on the fly with random temporary file names, so memorizing the example fails. Execution is jailed to a temp directory and any attempt to open the test tree or import disallowed libraries is intercepted. Source must be pure standard library parsing; imaging libraries or shell tricks are rejected.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
