# codimango/hydrothermal-sonar-heat-mapping

## Description

ROVs survey black smokers. A single sonar block `.svol` holds one hot bubble plume. You must output true plume extent in mm3.

Beam side lobes plus particle scatter inflate a compact high density microbubble core with feathery tendrils into a large cloudy blob. Bright voxel tallies swing wildly across dives because vent output, sea water level, and anisotropic voxel size change every file. The example at `/app/data/scene.svol` has a different scale than secret cases.

Hitting 5 percent tolerance needs subvoxel energy reasoning, not a brightness cutoff, plus careful handling of ambient, fish returns, core level, and diffuse edge.

## Completion Rates

New task. Prior run at b9a256a was unsolvable due to broad reference ban and 3 percent tightness. After fix to narrow ban to reference_volume and 5 percent tolerance, oracle passes locally 7 of 7.

## Model Analysis

* ROV block is 64 byte header, magic SVOL, grid extents and pitch, then x fastest voxels, parsed with struct, no numpy.
* Sea return is flat plus uniform grain, lower half median and MAD give unbiased floor.
* Fish echoes far away are removed by keeping plume with largest summed signal using 26 connectivity.
* Saturated acoustic core is hidden after blur and noise, recovered by small mean filter and top few brightest filtered values average.
* Plume extends beyond mask, grown outward while surrounding ring average stays above noise, stopping before merging distant debris. Final size uses pitch multiplication.

## Anti-Cheating Analysis

Secret plumes are created per evaluation with random names, memorizing sample fails. Jailed execution blocks test directory snooping and disallowed library use. Only standard library parsing allowed.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
