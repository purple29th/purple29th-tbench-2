# codimango/android-oled-bond-subvoxel-void

## Description

Agent writes **stdlib-only** Python at `/app/solve.py` that reads a raw IR backscatter cube dumped by Pixel factory OLED bonding QA rig (under-display VCSEL diffuser + IR scatter sensor, custom binary `.obvl` with magic `OBVL`). Input path is argv[1]; sample at `/app/data/scene.obvl` for dev. Agent must print main air-void volume in mm^3 as last token. Hidden grading uses different void sizes, diffuser power, voxel pitch, DC background, dust specks.

This is the **factory OLED QA precision escalation** of `android-depth-object-volume` and `android-tof-subvoxel-volume`. Those can be solved by threshold -> mask -> largest connected component counting. **Here that pipeline is 70-120% wrong.**

### What makes it harder vs previous Android depth family

Pixel OLED bonding rig reports per-voxel IR scatter where trapped air scatters strongest. VCSEL diffuser lens applies anisotropic PSF: OLED stack diffuses wide in XY, bond layer thin so Z diffusion narrow, plus dust fibre specks that create far bright blobs. Three stacked difficulties beyond manual little-endian parsing / per-scan anisotropic pitch from bonding rig calibration / speck filtering:

1. **No absolute or relative threshold works.** Bond void = thick bubble core (saturates to plateau after blur) + thin delamination channels along x/y where voxel partially filled -> intermediate intensity that never reaches any usable cut. Voxel counting above any cut either misses channels (cut high, -30 to -50%) or ingests diffuser halo (cut low, +70 to +120%). Optimal cut drifts per scan because diffuser power / ambient IR / pitch change per file (different OLED batches), no static rule generalizes.

2. **Correct method: IR scatter energy conservation over most-concentrated void region.** Normalized diffuser blur conserves total photon counts, only spreads them. True occupancy voxels = `sum(scatter - DC_background over void+halo)/plateau_amplitude` where plateau = saturated interior scatter concentration. Agent must (a) estimate DC floor robustly via median + MAD on background-dominated volume without bias from void itself, (b) isolate main void from dust specks via largest-mass 26-connected component (mass = integrated residual, not voxel count) to drop far artefacts, (c) estimate saturated interior plateau via 3x3x3 mean-filter peak over component median-of-top-8, (d) adaptively dilate to capture faint halo until shell mean ~ noise floor without bridging specks, then integrate signed residual (noise cancels).

3. **Tighter factory tolerance.** Grading at **3%** vs 5% family baseline. Conservation lands 0.2-1% here; every threshold shortcut >=12% off, so OLED QA would ship bad panels.

A one-shot template (`numpy` + `scipy.ndimage.label` + threshold count) is both forbidden by `test_from_scratch()` and physically wrong for diffuser halo - it fails dust isolation and thin channel handling.

## Measured difficulty (OLED bond void analysis)

Numbers measured by harness on sample + 3 held-out OLED scans (generator `tests/_gen.py`). Error = worst-case relative over scans. Verifier independent conservation pure-stdlib matches geometric truth within **0.95%** despite anisotropic pitch.

| Strategy | Result | Verdict |
|---|---|---|
| **IR energy conservation** (intended, OLED diffuser) | 0.2-0.95% per scan | **passes** |
| Independent 2nd conservation (different bg/amp/region heuristics) | 0.35-1.1% | passes |
| Family baseline: threshold@200 + largest CC x spacing | 72-118% over | fails |
| Sum all bright voxels @200 (no dust isolation) | 88-130% over | fails |
| Best single fixed absolute cut + largest-mass CC | 28% worst-case | fails |
| Best fixed fraction of plateau (true bg & amp given) | 12% worst-case | fails |
| Half-max (f=0.5) + largest CC | 19-34% | fails |
| Otsu + largest CC | 17-23% | fails |

3% tolerance sits in empty band between ~1% (any sound conservation) and >=12% (any counting shortcut). Forces genuine halo integration.

## Completion Rates

| Model | Agent | Pass rate |
|-------|-------|-----------|
| Oracle | oracle | 3/3 (1.0) - deterministic, all verifier checks including dust-speck isolation pass |
| Sonnet 4.6 | claude-code | to be measured via TBR validation (Build + Eval GT + Agentic Review) |
| Opus / Avocado | claude-code / metacode | calibration target - should show partial pass 1-4/5 and fail modes around threshold counting vs energy conservation |

> **Calibration target for OLED factory vision:** agents reusing family threshold-and-count template (or calling numpy/scipy/pillow/cv2 one-liners banned anyway) fail. Only derivation conserving IR energy across diffuser halo passes. Expected dominant failure = *counting bright voxels instead of integrating conserved scatter* - reasoning gap about conservation, not setup. Oracle + independent 2nd conservation (different bg estimation + plateau heuristic + region growth) both <1.1% proving pure-python solution exists.

## Model Analysis (expected)

- Threshold-count template 0/5 - low cut grabs halo, high cut misses thin delam channels
- Missing dust filter 0/5 - includes far specks adds 30-80% over
- Using voxel count not mass for component selection - picks speck over main void on scans where speck massive
- Fixed plateau heuristic (global max) overestimates amp -> underestimates volume ~15%
- No halo growth -> underestimates 2-4% - close but still fails 3% band
- Forgetting anisotropic pitch multiplication (sx*sy*sz) -> off by pitch volume product

## Anti-Cheating & Mobile Hardening

- **Hardcoded void sizes blocked:** verifier runs on 3 hidden OLED dumps whose true void volumes differ mutually and from visible sample (~1676 mm3) with different anisotropic pitch from OLED rig calibration per batch. Constant float cannot satisfy multiple dumps at 3%.
- **Overfit to visible file blocked:** only `/app/data/scene.obvl` exists in agent container, dumped via Android test rig FileOutputStream. Its void shape (ellipsoid + boxes + cylindrical delam fingers), diffuser power, DC background, voxel pitch, dust positions differ from grading scans. Hidden dumps under `/tests` absent at agent run and mounted only at verify time.
- **Test file editing worthless:** held-out dumps + generator under `tests/` invisible to agent during trajectory, mounted only at verify time. Reward computed independently via intensity conservation pure-stdlib `reference_volume_mm3`, not from agent-editable constants. `run_agent()` copies scan to neutral temp name so agent cannot infer which heldout.
- **Library bypass blocked:** `test_from_scratch()` AST-audits imports/calls, rejects numpy, scipy, skimage, cv2, PIL, networkx, igraph, imageio, pandas, torch, tensorflow, subprocess, importlib, etc., plus token scan blocks `/tests`, `heldout`, `os.system`, `os.walk`, `os.listdir`, etc. Forces genuine little-endian parsing via `struct` + hand-written 26-neighbour labelling + energy integration.

Author: Tosin Daniel Jimoh <purple29th@meta.com> - Android OLED bonding factory QA track - distinct from TOF parcel but same subvoxel physics core
