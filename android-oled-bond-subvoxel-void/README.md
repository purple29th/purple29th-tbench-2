# codimango/android-oled-bond-subvoxel-void

## Description

Agent writes **stdlib-only** Python at `/app/solve.py` that reads a raw IR backscatter cube dumped by Pixel factory OLED bonding QA rig (under-display VCSEL diffuser + IR scatter sensor, custom binary `.obvl` with magic `OBVL`). Input path is argv[1]; sample at `/app/data/scene.obvl` for dev. Agent must print main air-void volume in mm³ as last token. Hidden grading uses different void sizes, diffuser power, voxel pitch, DC background, dust specks.

This is the **factory OLED QA precision escalation** of `android-depth-object-volume` and `android-tof-subvoxel-volume`. Those can be solved by threshold -> mask -> largest connected component counting. **Here that pipeline is 70-120% wrong.**

### What makes it harder vs previous Android depth family

Pixel OLED bonding rig reports per-voxel IR scatter where trapped air scatters strongest. VCSEL diffuser lens applies anisotropic PSF: OLED stack diffuses wide in XY, bond layer thin so Z diffusion narrow, plus dust fibre specks that create far bright blobs. Three stacked difficulties beyond manual little-endian parsing / per-scan anisotropic pitch from bonding rig calibration / speck filtering:

1. **No absolute or relative threshold works.** Bond void = thick bubble core (saturates to plateau after blur) + thin delamination channels along x/y where voxel partially filled -> intermediate intensity that never reaches any usable cut. Voxel counting above any cut either misses channels (cut high, -30 to -50%) or ingests diffuser halo (cut low, +70 to +120%). Optimal cut drifts per scan because diffuser power / ambient IR / pitch change per file (different OLED batches), no static rule generalizes.

2. **Correct method: IR scatter energy conservation over most-concentrated void region.** Normalized diffuser blur conserves total photon counts, only spreads them. True occupancy voxels = `sum(scatter - DC_background over void+halo)/plateau_amplitude` where plateau = saturated interior scatter concentration. Agent must (a) estimate DC floor robustly via median + MAD on background-dominated volume without bias from void itself, (b) isolate main void from dust specks via largest-mass 26-connected component (mass = integrated residual, not voxel count) to drop far artefacts, (c) estimate saturated interior plateau via 3x3x3 mean-filter peak over component median-of-top-8, (d) adaptively dilate to capture faint halo until shell mean ~ noise floor without bridging specks, then integrate signed residual (noise cancels).

3. **Tighter factory tolerance.** Grading at **3%** vs 5% family baseline. Conservation lands 0.2-1% here; every threshold shortcut >=12% off, so OLED QA would ship bad panels.

A one-shot template (`numpy` + `scipy.ndimage.label` + threshold count) is both forbidden by `test_from_scratch()` and physically wrong for diffuser halo - it fails dust isolation and thin channel handling.

## Measured difficulty (OLED bond void analysis)

Numbers measured by harness on sample + 3 held-out OLED scans. Generator used offline (now removed from grading bundle after BAD_LEAKAGE fix). Error = worst-case relative over scans. Verifier independent conservation pure-stdlib matches geometric truth within **0.95%** despite anisotropic pitch.

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

Measured offline over 18 validation trials (commit 6376c80) and TBR revalidation before fix v1.0. All trials used stdlib-only oracle/solve.py with 3% tolerance, 3 held-out scans.

| Model | Agent | Pass rate | Notes |
|-------|-------|-----------|-------|
| Oracle | oracle | 3/3 (100%) | Deterministic, all verifier checks including dust-speck isolation pass. |
| Opus 4.8 | claude-opus-4-8 | 4/5 (80%) | Strongest agentic. 1 fail = FAIL_INCOMPLETE (timeout during extended validation work, never left /app/solve.py). |
| GPT-5.5 / Codex | gpt-5.5 / codex | 5/5 (100%) | All 5 codex rollouts passed; sample outputs 1657-1670 mm³ matching ~1676 truth. Robust conservation estimator. |
| Avocado 5.14 / Metacode | meta/avocado-5.14-code / metacode | 3/5 (60%) | 2 fails: 1 FAIL_INCOMPLETE (analysis only, no file), 1 FAIL_REASONING (overestimate 18-27% on heldouts: 4823 vs 4086, 4331 vs 3416, 4147 vs 3510 -> plateau/background heuristic error). |

Build (TBR): PASS, Eval GT (TBR): PASS, Agentic Review (TBR): 12 pass (pre-hardening).

**Calibration achieved:** 1-4/5 for non-oracle family reuse vs 100% for correct energy conservation, as intended for OLED factory vision.

## Model Analysis

Primary discriminant is ability to derive energy-conservation volume vs reuse threshold-and-count family template.

**Dominant failure modes observed (real data):**

1. **Counting bright voxels instead of integrating conserved scatter** (70-120% error cluster) - occurs when agent does `sum(mask)` above fixed cut. Low cut grabs halo, high cut misses thin delam fingers. Optimal cut drifts per scan due to diffuser power / ambient IR / pitch. This is the reasoning gap, not setup.

2. **FAIL_INCOMPLETE / timeout** - 2/18 rollouts (Opus 1, Avocado 1) timed out during robust estimator development, never produced `/app/solve.py`. Indicates task genuinely hard: requires iterative background + plateau + region-growth tuning.

3. **Plateau/background mis-estimation causing 18-27% overestimate** - 1 Avocado rollout: sample 1968 vs expected ~1667, heldouts 4823 vs 4086, 4331 vs 3416, 4147 vs 3510. Root cause: global max for plateau overestimates amp, or no halo growth, or single fixed absolute cut + largest-mass CC. Falls just outside 3% band, proving tolerance discriminates.

4. **Dust handling errors:**
   - Missing dust filter includes far specks adds 30-80% over.
   - Using voxel count not mass for component selection picks speck over main void when speck massive.
   - Both blocked by largest-mass 26-connected component check; mass = integrated residual.

5. **Forgetting anisotropic pitch multiplication (sx*sy*sz)** - off by pitch volume product, fails all heldouts.

6. **No halo growth** - underestimates 2-4%, close but still fails 3% band, forcing genuine integration.

**Model trends:**

- **GPT-5.5/Codex 5/5**: Consistently implements adaptive background/noise via median+MAD low-half, mass-based CC, plateau via filtered peak median-of-top-8, halo dilation until shell mean ~ noise floor.
- **Opus 4/5**: Normally same conservation pipeline, but 1 timeout shows fragility under 30-min budget when exploring thresholds.
- **Avocado/Metacode 3/5**: Higher variance - succeeds when derives conservation, fails when reuses family threshold template or mis-estimates plateau.

## Anti-Cheating & Mobile Hardening

- **Hardcoded void sizes blocked:** verifier runs on 3 hidden OLED dumps whose true void volumes differ mutually and from visible sample (~1676 mm³) with different anisotropic pitch from OLED rig calibration per batch. Constant float cannot satisfy multiple dumps at 3%.

- **Overfit to visible file blocked:** only `/app/data/scene.obvl` exists in agent container, dumped via Android test rig FileOutputStream. Its void shape (ellipsoid + boxes + cylindrical delam fingers), diffuser power, DC background, voxel pitch, dust positions differ from grading scans. Hidden dumps under `/tests/data/` absent at agent run and mounted only at verify time. `run_agent()` copies scan to neutral temp name `scan.obvl` and copies `solve.py` into isolated `TemporaryDirectory` (cwd=td, PYTHONPATH=td) so agent cannot infer which heldout.

- **Generator leakage fixed (BAD_LEAKAGE remediation):** `_gen.py` containing exact hidden scan CONFIGS was previously under `/tests` and available to submitted code at grading time (R05 FAILED). Now removed from task bundle entirely. Ground truth recomputed stdlib-only via `reference_volume_mm3` with distinct heuristics vs oracle (different bg/amp/region thresholds), matching geometric truth within 0.95%. No generator, no readable verifier source in child process.

- **Reward-hacking hardened (BAD_GRADING_WEAK remediation):** `test_from_scratch()` now:
  - Bans modules: `numpy, scipy, skimage, cv2, PIL, networkx, igraph, imageio, pandas, torch, tensorflow, subprocess, importlib, runpy, ctypes, socket, multiprocessing, glob, pathlib, shutil, io, os` (strict).
  - Bans calls: `eval, exec, compile, __import__, getattr, setattr, hasattr, globals, locals, vars, dir, chr, ord, breakpoint`.
  - Bans tokens: `/tests, test_outputs, heldout, _gen, os.system/popen/exec/walk/listdir/scandir/open/stat/read/fdopen/path, pty., pathlib, Path(, shutil, io.open, __builtins__, __dict__, __subclasses__, __mro__, base64, binascii, codecs`.
  - Decoded string literal inspection: all `ast.Constant(str/bytes)` and f-string parts decoded and checked for `/tests`, `tests/data`, `heldout`, `_gen`, `test_output`. Prevents `\x2f\x74...` obfuscation.
  - Dunder audit: any attribute `__xxx__` other than `__name__`/`__main__` rejected.
  - Enforces genuine little-endian parsing via `struct` + hand-written 26-neighbour labelling + energy integration.

- **Library bypass blocked:** rejects banned array/image/graph helpers; forces stdlib-only.

Author: Tosin Daniel Jimoh <purple29th@meta.com> - Android OLED bonding factory QA track - distinct from TOF parcel but same subvoxel physics core
<!-- forced refresh Tue Jul 28 11:02:23 AM UTC 2026 -->

