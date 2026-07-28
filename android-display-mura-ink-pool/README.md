# codimango/android-display-mura-ink-pool

## Description

Agent writes stdlib only Python at /app/solve.py that reads 2D display mura ink pool map dmip magic DMIP dumped from Android display lamination QA rig with under display RGB sensor and diffuser. Each map is luminance image with one main ink pool blob plus thin bleed fingers where pixel partially filled and 0 to 2 far dust specks. The rig has anisotropic PSF wide in XY due to adhesive diffusion, so true shape is thick core where ink bright flat plus thin bleed fingers that never reach usable threshold, plus halo smear.

This is UI display QA analogue of android oled bond subvoxel void but in 2D area mm2 not 3D volume mm3, with different magic DMIP, different pitch ranges, and different file layout nx ny sx sy. The physics is same energy conservation: blur spreads light but does not create or destroy photons. True area equals sum background subtracted intensity over pool plus halo over plateau times sx times sy.

Naive threshold counting fails: low cut includes halo overestimates 60 to 110 percent, high cut misses bleed fingers underestimates 25 to 45 percent, no fixed cut works across backlight power and background and pitch variations.

## Measured difficulty

Conservation 0.3 to 1.0 percent passes, threshold 60 to 110 over fails, best fixed absolute cut 22 percent worst fails, half max 18 to 30 fails. 3 percent tolerance sits between about 1 percent and 18 percent.

## Completion Rates

Calibration target from sister task oled bond subvoxel void: oracle 3/3, Avocado Metacode 3/5 60 percent with 2 fails, Opus 4/5 80 percent with 1 timeout, GPT 5/5 100 percent.

## Model Analysis

Dominant failures: counting bright pixels instead of integrating conserved light, incomplete timeout, plateau mis estimation 18 to 25 over, dust handling using count not mass, forgetting anisotropic pitch multiplication.

## Anti-Cheating

Hardcoded areas blocked: 3 hidden maps have different pool sizes, backlight power, pitch, dust positions, true areas differ mutually and from visible sample about 89.7 mm2. Constant fails at 3 percent. Overfit blocked: only scene.dmip exists in agent container, hidden dumps under tests data mounted only at verify, copied to neutral temp name and solve.py copied into isolated temp dir so agent cannot infer which heldout. Generator leakage fixed: gen file not mounted, ground truth in ground_truth.json geometric true areas. Reward hacking hardened: test_from_scratch bans many modules and tokens with decoded literal inspection and dunder audit.

Author: Tosin Daniel Jimoh - Android display mura ink pool QA track, 2D area version
