# Android OLED Bond Subvoxel Void

## Lab context

Pixel OLED bonding QA line uses an under-display IR scanner. Under the OLED stack a VCSEL diffuser illuminates the adhesive layer. Trapped air scatters IR strongly. The rig dumps a raw IR backscatter cube via a Kotlin test rig (`ByteBuffer` little-endian + `FileOutputStream` into app private storage, same pattern as ARCore depth dumps).

Your job: turn one cube into the true trapped-air void volume in mm³.

## Goal

Write a pure-stdlib Python program at:

```
/app/solve.py
```

It will be executed as:

```
python3 /app/solve.py /path/to/scan.obvl
```

Your program must print the main air-void volume in mm³ as the last whitespace-separated token on stdout. One sample scan exists for local dev at `/app/data/scene.obvl`. Hidden grading uses different scans you never saw.

Do not hardcode any numbers from the sample.

## OBVL format (custom, little-endian)

All integers and floats are little-endian.

Offset | Size | Type | Meaning
------ | ---- | ---- | -------
0 | 4 | ASCII | Magic `OBVL`
4 | 4 | u32 | Version = 1
8 | 4 | u32 | dtype code: 2 = int16 scatter, 16 = float32 scatter
12 | 12 | 3×u32 | `nx ny nz` voxel counts per axis (width, height, depth). Total voxels = nx*ny*nz.
24 | 12 | 3×f32 | `sx sy sz` mm per voxel per axis. Anisotropic calibration from OLED stack diffusion (XY) and bond thickness (Z). Different per file - must read header every time, never assume same pitch.
36 | 4 | u32 | `data_offset` where payload starts (currently 64)
data_offset | nx*ny*nz × dtype | dtype | Payload. X is fastest. Linear index for (x,y,z) = `x + nx * (y + ny*z)`.

Payload interpretation: per-voxel IR scatter. One main air void bubble plus occasional far dust speck blobs / fibre reflections that are NOT part of the void.

## Cube physics

- VCSEL diffuser + OLED stack gives anisotropic PSF: wide laterally (XY) through OLED diffusion, narrow axially (Z) through thin bond.
- True shape: thick core where air bubble scatters bright and saturates to a flat plateau after blur, plus thin delamination channels/fingers along X/Y where voxel is only partly filled -> intermediate intensity that never reaches any usable threshold. Border voxels dimmer from partial fill and smear.
- Content: flat ambient IR background (DC floor) + faint per-voxel noise + one main void + 0-3 far dust artefacts far from main void.
- You must drop dust: keep the main connected component via 26-neighbour connectivity, selected by integrated mass (sum of background-subtracted intensity), NOT voxel count. Otherwise you may pick a dust speck.

## Why threshold counting fails (tested)

- Low cut includes huge blurred halo: +70% to +120% overestimate.
- High cut misses thin delamination channels: -30% to -50% underestimate.
- No single fixed absolute or relative cut works across files because diffuser power, DC background, voxel pitch, and noise change per OLED batch.
- Family baseline `threshold@200 + largest CC * spacing` from `android-depth-object-volume` is 72-118% wrong here.

## Correct method: IR scatter energy conservation

Blur is normalized and conserves total photon counts, only spreads them. Interior is flat but hidden by blur and noise. Best clue is where scatter is most concentrated, not how many voxels are bright.

True occupancy voxels = `sum(background_subtracted intensity over void+halo) / plateau_amplitude`

Where:

- `plateau_amplitude` = saturated interior scatter where air scattering is most concentrated (robust peak estimate).
- Void+halo = main void plus its faint diffused halo captured via adaptive dilation until shell mean ~ noise floor, without bridging to far specks.

Required sub-steps:

1. Parse binary yourself using only stdlib (`struct`).
2. Estimate DC background robustly: median + MAD on background-dominated volume, without bias from void itself. Use low-half median/MAD for noise sigma.
3. Residual = scatter - background.
4. 26-connected components above noise floor. Keep largest-mass component (mass = integrated residual) to drop dust.
5. Estimate saturated interior plateau via 3x3x3 mean-filter peak over component, median of top-8 filtered values.
6. Adaptively dilate to capture faint halo: grow frontier while shell mean > ~0.9*noise_sigma, max ~60 iterations, without bridging specks. Then integrate signed residual (noise cancels) over grown region.
7. Volume = `voxels * sx*sy*sz` mm³.

## Output spec

- Print volume mm³ as last token. Example: `python3 /app/solve.py /app/data/scene.obvl` -> prints something like `1667.04` (exact depends on estimator, ~1676 geometric truth for sample).
- Grading tolerance: 3% relative vs independent conservation reference (distinct heuristics vs oracle, pure-stdlib, matches geometric truth within 0.95%).

## Hidden grading

- 3 hidden OLED dumps with different void sizes, diffuser power, voxel pitch, DC background, dust positions/sizes. True volumes differ mutually and from visible sample (~1676 mm³ sample). Constant float cannot pass multiple dumps at 3%.
- Only `/app/data/scene.obvl` exists in agent container. Hidden dumps under `/tests/data/` are absent at agent run and mounted only at verify time. Generator that created them (`_gen.py`) is NOT included in grading bundle after hardening (removed to close BAD_LEAKAGE).
- Reward computed independently via intensity conservation pure-stdlib `reference_volume_mm3`, not from agent-editable constants. `run_agent()` copies scan to neutral temp name and copies `solve.py` into isolated TemporaryDirectory (cwd=td, PYTHONPATH=td) so agent cannot infer which heldout or import from /tests.

## Bans / anti-cheat

- Implement parsing, labeling, and integration from scratch. Banned imports: `numpy`, `scipy`, `skimage`, `cv2`, `PIL`, `pillow`, `networkx`, `igraph`, `imageio`, `pandas`, `torch`, `tensorflow`, `subprocess`, `importlib`, `runpy`, `ctypes`, `socket`, `multiprocessing`, `glob`, `pathlib`, `shutil`, `io`, `os` (strict). Banned calls: `eval`, `exec`, `compile`, `__import__`, `getattr`, `setattr`, `hasattr`, `globals`, `locals`, `vars`, `dir`, `chr`, `ord`, `breakpoint`.
- Banned filesystem tricks: `os.system`, `os.popen`, `os.exec`, `os.walk`, `os.listdir`, `os.scandir`, `os.open`, `os.stat`, `os.read`, `os.fdopen`, `os.path`, `pty.`, `pathlib.Path`, `shutil`, `io.open`, `/tests`, `test_outputs`, `heldout`, `_gen`, `__builtins__`, `__dict__`, `__subclasses__`, `__mro__`, `base64`, `binascii`, `codecs`, double-underscore dunder attributes other than `__name__`/`__main__`.
- Also: do not open/read tests directory or heldout files. String literals are decoded and checked for obfuscated paths (`\x2f...` -> `/tests`). Obfuscated path construction via `chr`/`ord`/dynamic getattr is blocked.
- AST-audit via `test_from_scratch()`. Violation = immediate fail.

## Notes

- Exact thresholds not prescribed - you must find robust ones that work across power/background/pitch/dust variations. 3% band allows heuristic variation but threshold shortcuts fail.
- Apply anisotropic pitch multiplication `sx*sy*sz` - forgetting it fails volume product.
- Pure stdlib only; handwritten 26-neighbour BFS/DFS required.

Author: Pixel OLED bonding factory QA track - distinct from TOF parcel but same subvoxel physics core.
