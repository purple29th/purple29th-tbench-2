# codimango/android-depth-object-volume

## Description

The agent writes a **from-scratch** Python script (`/app/solve.py`, standard
library only) that reads a small on-device depth/occupancy volume (`.avol`, a
custom ToF-style binary format) and reports the physical volume, in cubic
millimetres, of the scanned object. The script takes the scan path as its first
argument and prints the volume as the final number on stdout, so it can be run
against scans it has never seen.

This is built in the mold of `mri-volume-calc`: the difficulty is the
combination of low-level binary parsing and an image-reasoning step, with **no
library allowed to do either**:

1. **Manual binary parsing.** No numpy/scipy/imaging/graph libraries and no
   shelling out (enforced by `test_from_scratch()`), so the agent reads the
   header (magic, dtype code int16/float32, dims, per-axis voxel size,
   `data_offset`) and decodes the voxel array (x-fastest order) with `struct`.

2. **Anisotropic, per-scan voxel spacing.** Scans are not 1 mm³ isotropic and
   the spacing differs per scan (`0.9375×0.9375×3.0`, `1.0×1.0×2.5`,
   `0.8×0.8×4.0`, `1.0×1.0×3.0` mm). Volume is `voxel_count × sx × sy × sz` read
   from the header; the instruction does **not** spell out the multiplication or
   hint that the spacing is anisotropic.

3. **Object isolation, by hand.** Each scan has one solid bright object plus
   several small, scattered bright **specks** (sensor noise) elsewhere in the
   volume. The instruction asks for "the object" / "a bright region" (singular),
   so the naive reading — threshold to a bright mask and sum **every** bright
   voxel — over-counts by ~20% (verified across held-outs) by including the
   specks. The correct answer thresholds, labels 3D connected components by
   hand, and takes the **largest** one.

A one-shot template (`numpy` + `scipy.ndimage.label`) is exactly what the task
forbids, which is what makes it resistant to training-data recall. The reference
solution parses the header with `struct`, thresholds in the empty intensity band,
labels 26-connected components with a hand-written BFS, takes the largest, and
multiplies its voxel count by the product of the header voxel sizes.

## Completion Rates

Measured on this task (K=5 per model; oracle K=1, deterministic). The metacode
tester (Avocado) lands a genuine pass/fail split — the calibration target: it
passes when it isolates the object's largest connected component and fails when
it sums all bright voxels (including the scattered noise specks), over-counting
~20% past the 5% tolerance.

| Model | Agent | Pass rate |
|-------|-------|-----------|
| Oracle | `oracle` | 3/3 (1.0) |
| Avocado (`meta/avocado_dvsc_tester`) | `metacode` | 3/5 (0.60) |
| Opus 4.6 (`claude-opus-4-6`) | `metacode` | re-measured by the validation pipeline (local runs produced no agent output — infra) |

### Model Analysis

**Avocado — 3/5 passed, 2/5 failed** (real transcripts, 117–439 lines). The two
failures over-counted by summing the whole bright mask — including the scattered
specks — instead of isolating the object's largest connected component; the three
passing trials thresholded, labeled connected components by hand, and took the
largest. Failures were time-stable reasoning errors, not timeouts. This is the
intended dominant failure mode, mirroring `mri-volume-calc`.

## Anti-Cheating Analysis

- **Hardcoded outputs:** grading runs the script on three hidden held-out scans
  whose object volumes (3300.0, 1843.2, 3888.0 mm³) differ from each other and
  from the visible sample (1898.4 mm³). A constant or sample-memorized value
  cannot satisfy multiple different held-outs.
- **Overfitting to visible tests:** the only data in the agent container is the
  sample scan, which has a different volume *and* different voxel spacing than
  the graded scans. Held-outs live under `tests/` and are absent during the
  agent run.
- **Modifying test files:** tests and held-out data are copied in only at verify
  time. The reward is computed by the verifier from a ground truth it calculates
  independently with numpy + scipy.ndimage (26-connectivity), not from anything
  the agent can edit.
- **Bypassing the intended path:** `test_from_scratch()` rejects numpy, scipy,
  scikit-image, OpenCV, PIL/Pillow, networkx, igraph, etc. and shelling out,
  forcing genuine byte parsing and a hand-written component labeller. Per-scan
  varied spacing forces reading the header (spacing cannot be hardcoded);
  scattered specks force largest-component isolation (bright-voxel summing
  over-counts ~20%); the 5% tolerance rejects the naive shortcuts (isotropic
  assumption is far off, speck inclusion ~20% off, unit errors 1000× off).

Author: Tosin Daniel Jimoh <purple29th@meta.com>
