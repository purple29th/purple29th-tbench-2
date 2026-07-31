# codimango/perovskite-film-pinhole-true-area

## Description

Agent writes from-scratch `/app/solve.py` (stdlib only) reading custom photoluminescence film scan `.ppha` magic `PPHA` of pinhole defects in perovskite PV films and reporting true dead area mm².

PL imaging smears: photo-generated carrier diffusion + sCMOS lens Airy spread is normalized blur conserving total quenched PL but inflating apparent dark area ~2×. Threshold counting fails 90-130% over (halo) or 40-55% under (thin feathered pinhole arms partial coverage). No fixed level works across films due to gain, background, diffusion length, noise shift.

Correct method intensity conservation: true pixels = sum(bg-subtracted over pinhole+halo)/plateau. Needs median/MAD lower-half background, largest-mass 8-connected component to discard coating dust specks, filtered top-12 plateau via 3×3 mean, adaptive halo growth to 1×sigma floor without bridging specks, area = count * sx*sy anisotropic.

Sister family: `foundry-thermal-subvoxel-void`, `ceramic-sinter-pore-subvoxel-void`, `solar-wafer-microcrack-true-area`, `confocal-gold-subvoxel-volume`, `ink-blot-subvoxel-area`, `aero-composite-delam-subvoxel-area` – same hard reasoning (blur conserves energy, speck removal, plateau, halo, 3% tolerance). This variant is perovskite PL pinhole area mm², name avoids void/sub.

## Completion Rates

Projected from sisters:

| Model | Pass | Notes |
|-------|------|-------|
| `claude-opus-4-8` | 2-3/5 40-60% | sensitive to speck_heavy |
| `gpt-5.5` | 1-2/5 20-40% | halo or branches |
| `meta/avocado` | 1-3/5 20-60% | background bias |
| `oracle` | 3/3 100% <1% error |

## Model Analysis

Fail modes: threshold any level 12-130% error, global integration without speck removal fails speck_heavy 5-8% over, raw max plateau 5-10% error, missing halo 15-25% under, counting pixels not energy 30%+ error. Requires binary parsing magic PPHA, dtype 2=int16 16=float32, nx ny, sx sy mm/pixel, offset 28, x-fastest, robust background, 8-connected main, filtered plateau, halo growth.

## Anti-Cheating Analysis

- Hardcoded: hidden scans generated at runtime temp dir random `input_<hex>.ppha`, truth = clean set size * pitch, different vs sample 8.16 vs 8.5/11.1/9.7 mm².
- Overfitting: only scene.ppha in image, different pitch/diffusion/noise than hidden.
- Secure runner: sys.addaudithook blocking /tests, test_outputs, heldout, _gen, GEOM_TRUTH etc., blocking listdir/scandir/walk, blocking os.system/popen/exec/fork, subprocess/socket, blocking banned imports os/io/pathlib/glob etc.
- From-scratch: AST checks numpy/scipy/skimage/cv2/PIL/pandas/torch/..., banned calls eval/exec/compile/__import__/chr, attrs system/popen/walk/listdir, substr bans /tests etc., bans chr(, fromhex, b64decode, pathlib, rglob, glob(.
- New domain: perovskite PL pinhole distinct from PV wafer EL microcrack, ceramic sinter pore, thermal turbine void, gold tumor, ink blot – uses slot-die coating, perovskite, PL quench, shunt-risk – dedup NOVEL.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
