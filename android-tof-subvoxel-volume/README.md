# codimango/android-tof-subvoxel-volume

## Description

The agent writes a **from-scratch** Python script (`/app/solve.py`, standard
library only) that reads a small on-device ToF depth/occupancy volume (`.tvol`,
a custom binary format) and reports the physical volume, in cubic millimetres, of
the scanned object. The script takes the scan path as its first argument and
prints the volume as the final number on stdout, so it can be run against scans
it has never seen.

This is the **precision escalation** of `android-depth-object-volume` and
`mri-volume-calc`. Those tasks are solved by thresholding to a bright mask and
counting the largest connected component's voxels. **Here that entire approach
is wrong**, by 20–130%.

## What makes it harder

The sensor reports an *occupancy intensity* per voxel and its optics apply a
**point-spread function** (a normalized, anisotropic Gaussian — wide laterally,
narrow axially). Three consequences stack on top of the family's existing
difficulty (manual binary parsing; anisotropic, per-scan voxel spacing; specks
that force object isolation):

1. **No threshold recovers the volume.** The object is a solid core (which
   saturates to a peak amplitude after blur) plus thin fingers/slabs whose
   *partial-volume* intensity never reaches any usable threshold. Counting
   thresholded voxels either drops the thin parts (too high a cut) or balloons
   the core's blur halo (too low a cut). Because a per-scan-optimal threshold
   exists only if you already know the answer, no *static* rule an agent can
   write works across scans — see the measured table below.

2. **The correct method is intensity conservation.** A normalized blur conserves
   total intensity, so the object's true voxel count is
   `sum(intensity − background over the object) / plateau_amplitude`, not a voxel
   count. The agent must (a) estimate and subtract the background floor without
   bias, (b) isolate the object from the specks (largest-mass connected
   component), (c) estimate the interior plateau amplitude, and (d) integrate the
   background-subtracted intensity over the object and its faint halo — then
   multiply by the per-axis voxel size.

3. **Tighter tolerance.** Grading is at **3%** (vs 5% in the family). The
   conservation method lands under 1%; every thresholding shortcut is ≥12% off.

A one-shot template (`numpy` + `scipy.ndimage.label` + threshold-count) is both
forbidden *and* wrong, which is what makes the task resistant to training-data
recall and to the family's own known solution.

## Measured difficulty (static-strategy analysis)

All numbers below are measured by the bundled harness on the sample + 3 held-out
scans (see `tests/_gen.py`). "Error" is worst-case relative error over all scans
unless noted. Ground truth is the geometric object volume; the verifier recomputes
it independently with numpy/scipy by intensity conservation (matches geometric
truth within **0.99%**).

| Strategy | Result | Verdict |
|---|---|---|
| **Intensity conservation** (intended) | 0.19–0.99% per scan | **passes** |
| Independent 2nd conservation impl (different bg/amp/region choices) | 0.30–1.06% | passes |
| Prior-family solution: threshold@200 + largest CC × spacing | 88–128% over | fails |
| Sum all bright voxels @200 (no isolation) | 89–136% over | fails |
| Best single **fixed absolute** threshold + largest CC | 31% worst-case | fails |
| Best single **fixed fraction** of amplitude (handed true bg & amp) | 12% worst-case | fails |
| Half-max threshold (f=0.50) + largest CC | 21–35% | fails |
| Otsu threshold + largest CC | 18–21% | fails |

The 3% tolerance sits in the wide empty band between ~1% (any sound conservation
implementation) and ≥12% (any threshold-and-count strategy).

## Completion Rates

| Model | Agent | Pass rate |
|-------|-------|-----------|
| Oracle | `oracle` | 1.0 (deterministic; all 5 verifier tests pass) |
| Frontier models | `metacode` / `claude-code` | to be measured by the validation pipeline |

> **Calibration target:** models that reach for the family's threshold-and-count
> solution (or a numpy/scipy one-shot, which is also banned) fail here; only a
> genuine intensity-conservation derivation passes. The dominant expected failure
> mode is *counting thresholded voxels instead of integrating conserved
> intensity* — a reasoning gap, not a setup issue: the oracle and a second
> independent conservation implementation both pass under 1.1%, so a correct
> base-Python solution exists and matches ground truth within tolerance.

## Anti-Cheating Analysis

- **Hardcoded outputs:** grading runs the script on three hidden held-out scans
  whose object volumes (3977.5, 3983.4, 4428.0 mm³) differ from each other and
  from the visible sample (3206.3 mm³). A constant or sample-memorised value
  cannot satisfy multiple different held-outs.
- **Overfitting to visible tests:** the only data in the agent container is the
  sample scan, which has a different volume *and* different voxel spacing, PSF
  width, amplitude, and background than the graded scans. Held-outs live under
  `tests/` and are absent during the agent run.
- **Modifying test files:** tests and held-out data are copied in only at verify
  time. The reward is computed by the verifier from a ground truth it calculates
  independently with numpy + scipy by intensity conservation, not from anything
  the agent can edit. `tests/_gen.py` (the data generator) is co-located with the
  tests and is never present in the agent's container.
- **Bypassing the intended path:** `test_from_scratch()` rejects numpy, scipy,
  scikit-image, OpenCV, PIL/Pillow, networkx, igraph, etc. and shelling out —
  forcing genuine byte parsing and a hand-written solution. Crucially,
  from-scratch is **necessary but not sufficient**: the prior family's from-scratch
  threshold-and-count solution passes `test_from_scratch()` but fails every
  held-out by 88–128%. Per-scan varied spacing forces reading the header; the
  point-spread blur plus partial-volume geometry defeats every fixed threshold
  (≥12% off); the 3% tolerance rejects all naive shortcuts while admitting any
  sound conservation implementation.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
