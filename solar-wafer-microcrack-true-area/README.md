# codimango/solar-wafer-microcrack-true-area

## Description

The agent writes a from-scratch Python script `/app/solve.py` (stdlib only: `struct`, `sys`, `math`) that reads a custom electroluminescence wafer scan `.elcr` magic `ELCR` of microcracks in monocrystalline PV wafers and reports true electrically dead area in mm².

EL imaging smears cracks: carrier diffusion plus Si CCD lens PSF is normalized but spreads dark signal into wide halo. Apparent dark cloud is ~2× true crack size. Threshold counting fails 80-130% over (halo included) or 30-50% under (thin branches lost, partial coverage). No fixed threshold works across wafers because gain, luminescence, diffusion length, background shift per batch.

Correct method is **intensity/energy conservation**: total dark deficit is preserved under blur, so true pixels = sum(background-subtracted over crack+halo) / plateau. Requires robust background via median/MAD lower half, isolation of main crack from dust/chamfer specks via largest-mass 8-connected component (mass = sum residual, not pixel count – dust can be larger in pixels but less energy), plateau via 3×3 local-mean filtered top-K peak (top-12) to suppress read noise, and adaptive halo growth until shell mean falls to 1×sigma without bridging to specks. Area = pixel_count * sx * sy with anisotropic pitch from header.

Sister family reference: `foundry-thermal-subvoxel-void`, `ceramic-sinter-pore-subvoxel-void`, `confocal-gold-subvoxel-volume`, `ink-blot-subvoxel-area`, `aero-composite-delam-subvoxel-area`, `pcb-copper-trace-undercut-gap` – all same hard reasoning (blur conserves energy, speck removal, plateau, halo, 3% tolerance) but different domains. This variant is **2D area in mm²** (not mm³) and name avoids `void`/`sub` substrings per request.

## Completion Rates

Projected from sister family (foundry/ceramic at v2.0):

| Model | Trials | Pass rate |
|-------|--------|-----------|
| `claude-opus-4-8` | 5 | ~2-3/5 40-60% sensitive to speck_heavy |
| `gpt-5.5` | 5 | ~1-2/5 20-40% overcounts halo or loses branches |
| `meta/avocado-5.14-code` | 5 | ~1-3/5 20-60% depends on background bias |
| `oracle` | 3 | 3/3 100% <1% error |

Naive counting: low threshold 90-130% over, high threshold 40-55% under, half-max/Otsu 18-35% off. Conservation 0.5-1% error.

## Model Analysis

Failure modes:
- Threshold counting any level → 12-130% error
- Global integration without speck removal → fails speck_heavy by 5-8% over (dust)
- Raw max for plateau → noise spike → 5-10% error
- Missing halo growth → 15-25% under (diffusion wide)
- Counting pixels not energy → 30%+ error

Requires: binary parsing (magic ELCR, version, dtype 2=int16 16=float32, nx ny, sx sy mm/pixel, offset 28, x-fastest), robust background, 8-connected main component, filtered plateau, halo growth.

## Anti-Cheating Analysis

- Hardcoded outputs: hidden scans generated at runtime in temp dir with random names `input_<hex>.elcr`, geometric truth computed inside verifier from clean set size * pitch. Different truth vs sample (scene 8.16 mm² vs heldouts 8.5, 11.1, 9.7 mm²).
- Overfitting to visible: only `/app/data/scene.elcr` present, different pitch/diffusion/noise than hidden.
- Secure runner: `_secure_runner.py` with `sys.addaudithook` blocking `/tests`, `test_outputs`, `heldout`, `_gen`, etc., blocking os.listdir/scandir/walk on /tests, blocking os.system/popen/exec/fork and subprocess/socket, blocking banned imports os/io/pathlib/glob/multiprocessing.
- From-scratch guard: AST checks for numpy/scipy/skimage/cv2/PIL/pandas/torch/... plus banned calls eval/exec/compile/__import__/chr, attrs system/popen/walk/listdir, substr bans for /tests etc., bans chr(, fromhex, b64decode, pathlib, rglob, glob(.
- New domain: PV wafer EL microcrack area is distinct from ceramic sinter pore, thermal turbine void, gold tumor, ink blot – uses carrier diffusion, PV, dust/chamfer artefacts – dedup NOVEL.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
