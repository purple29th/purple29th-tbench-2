# codimango/hydrothermal-sonar-heat-mapping

## Description

Autonomous underwater vehicles map black smokers with multibeam sonar. You get a custom acoustic volume `.svol` (magic `SVOL`) that contains one hydrothermal plume. Report true plume volume in mm3.

Sonar side lobes plus suspended scatter turn a compact core of dense microbubbles with delicate wispy tendrils into a bloated cloudy mass. Counting bright voxels is unstable because bubble output, sea water return, and anisotropic pitch change per dive. Sample file at `/app/data/scene.svol` differs in scale from hidden cases.

Accurate sizing needs careful handling of ambient level, isolated fish echoes, core brightness, and diffuse fringe rather than simple thresholding. Benchmark grades at 5 percent relative error on hidden volumes.

## Completion Rates

No trials yet — new task. Expected hard like ink and gold family where only careful reconstruction meets tolerance. Previous validation at b9a256a showed 0 of 10 avocado, 0 of 5 opus, 0 of 5 gpt fail not solvable due to over broad reference ban and tight 3 percent. After narrowing ban and raising tolerance to 5 percent, oracle passes and some frontier attempts should pass, while avocado still fails dominant threshold counting.

## Model Analysis

* **Header:** parse 64 byte little endian header with magic, version, dtype 2 int16 or 16 float32, extents and pitch, then voxels x fastest. Hand written with struct.
* **Sea floor:** background is flat sea water plus uniform noise, median and MAD of lower half give stable floor without plume bias.
* **Fish rejection:** far bright spots are fish or debris, keep region with largest summed residual via 26 neighbour flood fill.
* **Peak level:** saturated interior never directly seen after blur and noise, estimated via 3x3x3 mean filter averaging a few brightest filtered values.
* **Fringe expansion:** energy extends beyond mask, grow outward while ring mean stays above noise floor and stop before bridging to remote specks.

## Anti-Cheating Analysis

Hidden cases are built fresh at grading time with random file names in temp dir, so memorizing example fails. Runner confines execution and blocks attempts to read test directory or import disallowed libraries. Source must be stdlib only.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
