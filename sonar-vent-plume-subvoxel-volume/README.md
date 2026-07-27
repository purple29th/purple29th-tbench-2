# codimango/sonar-vent-plume-subvoxel-volume

## Description

Hydrothermal vent mapping uses multibeam sonar to image bubble plumes rising from the seafloor. The task is to report true physical plume volume in cubic millimetres from a custom sonar volume format `.svol` (magic `SVOL`). The agent must produce `/app/solve.py` that parses the binary and prints the volume as the final token.

Sonar beam pattern plus water column scattering spreads acoustic backscatter beyond the actual bubble region. The display shows a bright cloudy mass with extended tails, while the true plume that would be measured with ideal deconvolution is smaller with thin tendrils that never appear fully bright after spread. Simple bright voxel counting is unstable across bubble density, seawater background, and anisotropic pitch.

Accurate estimation needs robust handling of seawater level, isolated fish or debris specks, interior level, and faint halo growth. The benchmark grades at 3 percent relative error on hidden scans that differ from the sample in size, pitch, density, background, and blur.

## Completion Rates

| Model | Agent | Pass rate |
|-------|-------|-----------|
| Oracle | `oracle` | 1.0 (deterministic, 5 checks with secure verifier) |
| Frontier | `metacode` / `claude-code` | to be measured |

> Calibration: bright counting shortcuts fail well outside tolerance; only careful energy aware reconstruction meets 3 percent.

## Model Analysis

Ocean acoustics reconstruction without array libraries:

* File layout: 64 byte little endian header with magic SVOL, version, dtype 2 int16 or 16 float32, grid and pitch, then x fastest voxels. Hand written parsing with struct.
* Seawater level: scans dominated by seawater background that is flat plus uniform noise. Median and MAD give stable level.
* Debris filtering: distant specks are fish or debris, removed by keeping clump with greatest summed residual using 26 connectivity.
* Interior level: saturated core hidden by scattering and noise, estimated via local mean filtering and averaging brightest few values.
* Tail growth: faint acoustic tails belong to plume, captured by outward ring growth while average stays above noise floor.

## Anti-Cheating Analysis

* Sample volume differs from hidden volumes, constant fails. Hidden cases are synthesized fresh at grading time with random names in a temp directory.
* Execution is confined to temp dir. Attempts to read test tree or import imaging or subprocess modules are blocked.
* Source must be standard library only. Array, imaging, graph libraries, shell execution, or path hiding tricks cause from scratch check to fail.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
