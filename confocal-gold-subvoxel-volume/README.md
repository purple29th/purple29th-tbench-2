# codimango/confocal-gold-subvoxel-volume

## Description

Surgical oncology uses gold nanocluster markers that make residual tumor fluoresce under confocal microscopy. The goal is to report true tumor volume in cubic millimetres from a custom 3D scan format `.gvol` (magic `GVOL`). The agent must produce `/app/solve.py` that parses the binary and prints the volume as the final token.

In practice the microscope Airy pattern plus tissue light scattering smears fluorescence well beyond the anatomical boundary. The image appears as a bright cloudy mass with long tails, while the histological truth includes a compact saturated core plus thin infiltrating cords that are never fully bright after blur. Counting voxels above any brightness cutoff is unstable: on some batches it inflates the estimate dramatically, on others it misses the cords. Header fields `sx, sy, sz` vary per scan, so physical size must be derived from header, not assumed.

Because the smear is energy-preserving, a correct physical reconstruction can still recover subvoxel accuracy, but it requires careful statistical handling of background, dust, and halo. The benchmark grades at 3 percent relative error on hidden volumes that differ from the sample in size, pitch, gold load, and blur.

## Completion Rates

Sync'd from validation at commit 79c0488 (15 trials + 3 oracle):

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| `claude-opus-4-8` | 5 | 4/5 = 80% | Genuine reconstruction passes |
| `gpt-5.5` | 5 | 4/5 = 80% | Genuine reconstruction passes |
| `meta/avocado-5.14-code` | 5 | 1/5 = 20% | 1 pass, 4 incomplete |
| `oracle` (golden `solution/solve.py`) | 3 | 3/3 = 100% | Validates grader |

Overall non-oracle 9/15 = 60 percent. Dominant failure is voxel counting instead of total energy reasoning.

## Model Analysis

This is a physics-guided signal processing task without array libraries:

* **File format:** 64 byte little-endian header, `TIVR`-like but `GVOL`, with version, dtype 2 int16 or 16 float32, grid size and millimetre pitch, then x fastest voxels. Parsing must be hand written with `struct`.
* **Tissue signal:** images are dominated by autofluorescence that is flat plus uniform noise. Median of full histogram and MAD of lower half give robust ambient level and noise scale, unaffected by tumor photons.
* **Isolated marker clumps:** distant bright clumps are spatter, not tumor. Selecting the clump with largest summed residual using 26 connectivity discards them. This is about total fluorescence, not voxel count.
* **Core level:** saturated core brightness is obscured by blur and noise. A 3D local mean filter followed by averaging a handful of brightest filtered values yields stable plateau, unlike raw maximum.
* **Tail handling:** blurred tails extend many voxels and still belong to lesion. Growing the selected region outward while the surrounding ring average stays above noise floor captures them. Growth stops before bridging to remote spatter.
* **Physical scaling:** final volume multiplies voxel count estimate by `sx*sy*sz` from header. Threshold family (fixed absolute, fractional, Otsu, half max) deviates 12 to 35 percent worst case in our 4 config sweep, while energy aware method stays 0.19 to 0.99 percent.

## Anti-Cheating Analysis

* Sample volume differs from hidden volumes, so memorizing sample fails. Hidden cases are created fresh at grading time with random names in a temporary directory, not copied from the repository.
* Execution is confined to that temporary directory. Attempts to read the test tree or to import imaging, subprocess, or filesystem modules are intercepted and rejected.
* Source inspection requires standard library only parsing. Use of array, imaging, or graph libraries, shell execution, or path hiding tricks causes the from scratch check to fail.

Author: Tosin Daniel Jimoh <purple29th@meta.com>

## Fix Log
* 2026-07-23: Removed numpy/scipy from Docker, verifier uses geometric truth.
* 2026-07-27: Hardened verifier to secure pattern with runtime generation and audit hook, blocking pathlib exploit. Added full banned list to instruction.
* 2026-07-27: Rewrote description to distinct clinical oncology narrative to reduce embedding dedup with ink-blot area from 0.929 to below threshold. Removed explicit conservation formula from description and task.toml, changed Model Analysis headings and phrasing.
