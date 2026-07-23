# codimango/android-tof-subvoxel-volume

## Description

The agent writes a **from-scratch** Python script (`/app/solve.py`, stdlib only)
that reads a raw occupancy confidence cube dumped by an Android warehouse scanner
app using the phone's rear Time-of-Flight LiDAR (`ARCore Depth API` + 
`Sensor.TYPE_TOF` extended confidence, custom binary `.tvol` with magic `TVOL`).
The script receives a scan path as first arg and must print physical parcel
volume in mm^3 as final token. Grading uses hidden parcel dumps with different
dimensions, VCSEL power, voxel pitch, ambient IR background, and multipath.

This is the **mobile-logistics precision escalation** of `android-depth-object-volume`
and `mri-volume-calc`. Those are solved by threshold→bright-mask→largest-CC count.
**Here that pipeline is 20–130% wrong.**

## What makes it harder

Android ToF hardware reports per-voxel occupancy confidence from a VCSEL IR
emitter. The emitter lens applies an anisotropic **PSF** (wide XY from lens,
narrow Z from timing jitter, flying pixels from multipath). Three stacked
difficulties beyond the family baseline (manual little-endian parsing; per-scan
anisotropic pitch from camera intrinsics + ToF timing; flying-pixel specks):

1. **No absolute or relative threshold works.** Parcel is thick core (saturated
   plateau after blur) plus thin flaps, straps, tape fingers where voxel is only
   partially filled so intensity never hits any usable cut. Counting voxels above
   a cut either misses flaps (cut high) or balloons VCSEL halo (cut low). Because
   optimal cut depends on per-scan emitter power/background/pitch that change
   every file, no static rule generalizes — see measured table.

2. **Correct method: IR energy conservation over most-concentrated region.**
   Normalized blur conserves total energy. True voxel count =
   `sum(occupancy - ambient over parcel+halo) / plateau_amplitude`, not a count.
   Agent must (a) estimate ambient IR floor without bias from parcel itself
   (median + MAD on background-dominated volume), (b) isolate main parcel from
   flying-pixel multipath specks by largest-mass 26-connected component, not
   voxel count, (c) estimate saturated interior plateau via 3x3x3 mean-filter peak
   over component, (d) adaptively grow region to capture faint halo until shell
   mean ≤ noise floor without bridging specks, then integrate signed residual.

3. **Tighter tolerance for warehouse billing.** Grading at **3%** vs 5% family.
   Conservation lands 0.2–1% here; every threshold shortcut ≥12% off, so billing
   would be wrong.

A one-shot template (`numpy` + `scipy.ndimage.label` + threshold-count) is both
forbidden by `test_from_scratch()` and physically wrong for VCSEL halo.

## Measured difficulty (Android ToF static-strategy analysis)

Numbers measured by harness on sample + 3 held-out parcel scans (`tests/_gen.py`).
Error = worst-case relative over scans. Ground truth = geometric parcel volume;
verifier recomputes via independent intensity-conservation pure-stdlib impl and
matches geometric truth within **0.99%** despite anisotropic voxel pitch.

| Strategy | Result | Verdict |
|---|---|---|
| **IR energy conservation** (intended, ToF) | 0.19–0.99% per scan | **passes** |
| Independent 2nd conservation (different bg/amp/region heuristics) | 0.30–1.06% | passes |
| Prior family: threshold@200 + largest CC × spacing | 88–128% over | fails |
| Sum all bright voxels @200 (no flying-pixel isolation) | 89–136% over | fails |
| Best single **fixed absolute** cut + largest-mass CC | 31% worst-case | fails |
| Best single **fixed fraction** of plateau (true bg & amp given) | 12% worst-case | fails |
| Half-max (f=0.50) + largest CC | 21–35% | fails |
| Otsu + largest CC | 18–21% | fails |

3% tolerance sits in empty band between ~1% (any sound conservation) and ≥12%
(any threshold/count shortcut). Narrow band forces genuine halo integration.

## Completion Rates (Android Warehouse)

| Model | Agent | Pass rate |
|-------|-------|-----------|
| Oracle | `oracle` | 1.0 (deterministic; all 5 verifier checks including flying-pixel isolation pass) |
| Frontier | `metacode` / `claude-code` | to be measured by TBR validation pipeline (Build + Eval GT + Agentic Review) |

> **Calibration target for mobile vision:** agents that reuse family threshold-and-count template (or call numpy/scipy/pillow/cv2 one-liners, which are banned anyway) fail here. Only derivation that conserves IR energy across VCSEL halo passes. Expected failure is *counting bright voxels instead of integrating conserved occupancy* — reasoning gap about energy conservation, not setup. Oracle + independent 2nd conservation (different background estimation + plateau heuristic + region growth) both land <1.1%, proving a correct pure-python solution exists.

## Anti-Cheating & Mobile Hardening

- **Hardcoded parcel sizes blocked:** verifier runs script on three hidden parcel dumps whose true billable volumes (3977.5, 3983.4, 4428.0 mm³) differ mutually and from visible sample (3206.3 mm³) with different anisotropic pitch from camera intrinsics + ToF timing. Constant or sample-memorized float cannot satisfy multiple hidden dumps.
- **Overfit to visible file blocked:** only `/app/data/scene.tvol` exists in agent container, created by Kotlin `ByteBuffer` + `FileOutputStream` dump. Its geometry, VCSEL power, ambient IR, voxel spacing, and multipath specks differ from grading scans. Hidden dumps under `/tests` are absent during agent run and mounted only at verify time.
- **Test file editing worthless:** held-out dumps + generator `_gen.py` are co-located under `tests/` and invisible to agent. Reward computed by verifier independently via intensity conservation pure-stdlib (`reference_volume_mm3` in `test_outputs.py`), not from agent-editable constants.
- **Library bypass blocked:** `test_from_scratch()` AST-audits imports/calls, rejects numpy, scipy, skimage, cv2, PIL, networkx, igraph, imageio, pandas, torch, tensorflow, subprocess, importlib, etc., plus token scan blocks `/tests`, `heldout`, `os.system`, etc. Forces genuine little-endian parsing (`struct`) + hand-written 26-neighbour labelling + energy integration. Crucially from-scratch is necessary but not sufficient: family threshold solution passes scratch check yet fails every held-out 88–128% because VCSEL blur + partial-volume flaps defeat any static cut; per-scan varied sx sy sz from ARCore calibration forces header read; 3% tolerance rejects naive shortcuts.

Author: Tosin Daniel Jimoh <purple29th@meta.com> — Android ToF LiDAR warehouse scanning track
