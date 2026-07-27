# codimango/wafer-etch-pit-thermal-area

## Description

Semiconductor fabs use laser pulses to etch tiny pits on silicon wafers for photonic crystals. You get a custom thermal map `.weta` with magic `WETA` that encodes one etch pit. The job is to output true etched area in mm2.

The thermal image is misleading because heat diffusion plus IR optics smears hot glow into a bloated halo. What looks like a large bright region is actually a compact saturated core with thin micro crack extensions that never become fully hot after spread. Simple hot pixel counting is unstable across etch depth, wafer background temperature, and anisotropic pitch.

Accurate recovery needs robust handling of background, isolated particle contamination specks, interior brightness, and faint halo growth rather than thresholding. The benchmark grades at 5 percent tolerance on hidden scans that differ from the sample in size, pitch, depth, background, and blur.

## Completion Rates

New task, no trials yet. Expected to be hard like other vent and ink family tasks where only careful reconstruction meets tolerance. Edge that makes avocado fail is banning builtin open() so solver must use os.open and os.read.

## Model Analysis

* **Header:** manual parsing of 64 byte little endian header magic WETA, version, dtype 2 int16 or 16 float32, dimensions and pitch, then voxels x fastest.
* **Wafer floor:** background is flat wafer temperature plus uniform noise, estimated via median and MAD of lower half.
* **Particle rejection:** far specks are particle contamination, removed by keeping region with largest summed residual via 8 connectivity.
* **Core level:** saturated interior never directly seen, estimated via 3x3 mean filter averaging brightest few values.
* **Halo growth:** faint thermal halo belongs to pit, captured by outward ring growth while average stays above noise floor.

## Anti-Cheating Analysis

Hidden scans are built fresh at grading time with random names in temp dir, so memorizing sample fails. Execution is jailed and disallowed imports and filesystem snooping are blocked. Source must be stdlib only with low level file reading; imaging libraries or open() tricks fail from scratch.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
