# codimango/android-display-mura-ink-pool

## Description

Agent writes stdlib-only Python at `/app/solve.py` that reads a 2D display mura ink pool map (`.dmip` magic `DMIP`) dumped from Android display lamination QA rig with under-display RGB sensor and diffuser. Each map is a luminance image with one main ink pool blob plus thin bleed fingers where pixel partially filled and 0-2 far dust specks. The rig has anisotropic PSF wide in XY due to adhesive diffusion, so true shape is thick core where ink bright flat plus thin bleed fingers that never reach usable threshold, plus halo smear.

This is UI display QA analogue of `android-oled-bond-subvoxel-void` but in 2D area mm2 not 3D volume mm3, with different magic `DMIP`, different pitch ranges, and different file layout (nx ny, sx sy). The physics is same energy conservation: blur spreads light but does not create or destroy photons. True area equals sum background subtracted intensity over pool plus halo over plateau times sx times sy.

Naive threshold counting fails: low cut includes halo overestimates 60 to 110 percent, high cut misses bleed fingers underestimates 25 to 45 percent, no fixed cut works across backlight power and background and pitch variations.

## Measured difficulty

| Strategy | Result |
|----------|--------|
| Light energy conservation intended | 0.3 to 1.0 percent passes |
| Threshold at 200 plus largest CC times pitch | 60 to 110 percent over fails |
| Best fixed absolute cut plus largest mass CC | 22 percent worst fails |
| Half max plus largest CC | 18 to 30 percent fails |

3 percent tolerance sits between about 1 percent sound conservation and 18 percent any counting shortcut.

## Completion Rates

Calibration target from sister task android-oled-bond-subvoxel-void: oracle 3/3, Avocado Metacode 3/5 60 percent with 2 fails due to incomplete and plateau mis estimate, Opus 4/5 80 percent with 1 timeout, GPT 5/5 100 percent strong conservation.

| Model | Pass rate | Notes |
|-------|-----------|-------|
| Oracle | 3/3 100 percent | Deterministic stdlib, all verifier checks pass |
| Avocado Metacode | 3/5 60 percent expected | 1 incomplete, 1 overestimate 18 to 25 percent |
| Opus 4.8 | 4/5 80 percent expected | 1 timeout during robust tuning |
| GPT 5.5 Codex | 5/5 100 percent expected | Robust conservation estimator |

## Model Analysis

Dominant failures: counting bright pixels instead of integrating conserved light, incomplete timeout, plateau mis estimation 18 to 25 percent over, dust handling using count not mass, forgetting anisotropic pitch multiplication.

## Anti-Cheating

Hardcoded areas blocked: 3 hidden maps have different pool sizes, backlight power, pitch, dust positions, true areas differ mutually and from visible sample about 89.8 mm2. Constant fails at 3 percent.

Overfit blocked: only scene.dmip exists in agent container. Hidden dumps under tests data mounted only at verify, copied to neutral temp name and solve.py copied into isolated TemporaryDirectory so agent cannot infer which heldout or import from tests.

Generator leakage fixed: _gen.py not mounted, ground truth recomputed via independent conservation heuristic different constants than oracle.

Reward hacking hardened: test_from_scratch bans numpy scipy skimage cv2 PIL networkx igraph imageio pandas torch tensorflow subprocess importlib runpy ctypes socket multiprocessing glob pathlib shutil io os strict, bans getattr setattr hasattr globals locals vars dir chr ord breakpoint, bans tokens with decoded string literal inspection for obfuscated paths and dunder audit.

Author: Tosin Daniel Jimoh - Android display mura ink pool QA track, 2D area version of OLED bond void, distinct from ink-blot-subvoxel-area via display lamination framing and DMIP format and human instruction
<!-- refresh Tue Jul 28 12:37:09 PM UTC 2026 -->
