# electroless-nickel-pit-true-area

## Description
Car connector pins plated with electroless Ni-P about twelve microns on copper. Hydrogen bubbles during plating block deposition and leave a tiny pit down to copper that fails salt spray. White light interferometer height map is blurred by Airy disk and stage wobble, so tiny deep pit looks like wide shallow cloud. Need true pit area mm2 from blurry map, not cloud size.

Input is custom binary ENPP with header magic, version, dtype, dims nx ny, spacing sx sy mm per pixel anisotropic, data offset, then pixel values x fastest. Background bright pits flipped bright. File contains one main pit which is roundish with two thin lips left and right that count as part of pit even though faint after blur, plus far specks from dust and sometimes a wide shallow scratch far away covering many pixels but dim. Ignore artefacts, main pit is dominant bright blob.

Low brightness level includes big halo and area about twice real, high level cuts lips and halo and gives half. No single level works for all panels because gain and blur and tilt and noise shift. Optics keep total brightness, normalized blur preserves integral, so true area recoverable via energy.

Tolerance three percent. Simple thresholds ten percent or more off. Stdlib only, parse with struct.

## Completion Rates
Synced from validation at commit ac583a6 (per-run random configs, 9+guards)

- claude-opus-4-8: 4/5 = 80 percent, robust on speck and scratch
- gpt-5.5: 4/5 = 80 percent, passes halo and tilted cases
- avocado-5.14-code: 2/5 = 40 percent, fails on tilt and speck-heavy overcount
- oracle: 3/3 = 100 percent, all 15 checks pass (including pixel-count guard)

Overall non-oracle around 68 percent, genuinely hard, discrimination rests on avocado robustness (2/5) vs frontier at 80 percent. Naive global and count shortcuts fail by more than 3 percent on speck_heavy and scratch cases.

## Model Analysis
Binary parsing little endian header magic ENPP, version, dtype 2 int16 16 float32, nx ny, sx sy anisotropic, data offset. X fastest. From scratch check rejects numpy etc.

Failure modes: halo overcount double, lips undercount half, far dust and shallow scratch must be ignored. Dust can have more pixels than pit but less total brightness, so picker must use brightness not count, proven by scratch_shallow where dust count greater than main count but mass smaller.

Tilt: background has linear tilt per pixel, need plane fit from lower half to avoid bias.

Area: truth is fractional support times spacing, mm2 equals pixels times sx times sy with anisotropic pitch.

Threshold strategies low 85 to 125 percent over, best fixed 31 percent worst, half max 18 to 35 off. Energy method under one percent per scan.

## Anti-Cheating Analysis
Hardcoded outputs: grading generates scans at runtime from configs with geometric truth computed inside verifier, not static files. Areas differ from sample, constant fails.

Overfitting: only sample scan at data scene.enpp, hidden scans generated in temp dir random filenames input hex enpp, not byte identical.

Secure runner: now default-deny os.* namespace – only realpath, join, abspath, dirname, basename, exists, listdir, scandir, walk, stat, isdir, isfile, islink, getcwd allowed for verifier's own path checks; explicitly blocks os.link, os.symlink, os.rename, os.replace to prevent hardlink leak (tempfile._os.link bypass). Also blocks open on paths containing /tests, test_outputs, heldout, GEOM_TRUTH, geometric_truth, reference_volume with realpath and inode hardlink check (stat st_ino compare to /tests/test_outputs.py). Blocks dir listing on sensitive dirs, blocks subprocess/socket. Import denylist includes tempfile (removed from allowed – it exposed os via _os) plus numpy, scipy, skimage, etc. Does not block /app/data sample, so reading sample allowed but hardcoding sample fails hidden random.

From scratch guard: now allowlist – only struct, sys, math, random, re allowed. Every import base must be in allowlist, so ast, collections, itertools, array, shutil etc blocked. Attribute check scoped to os-qualified only: e.g., os.walk, os.system, os.listdir blocked, but plain helper named walk() allowed. Substring checks for /tests, test_outputs, heldout, GEOM_TRUTH, geometric_truth, reference_volume plus chr/fromhex/b64decode banned, documented in instruction.

Dynamic configs: ALL_TEST_CONFIGS and randomized_extra now drawn from per-run random seed at collection time via os.urandom(8) master RNG, not fixed table. Dims, spacing, amp, bg, sig, noise, tilt, object shapes, specks all random per run, with far-position enforcement (>25px from main) and scratch guard validation (dust count > main but mass smaller). No constant table can be memorized; static lookup hash fails.

Distinct from sintered silver die attach void (SSDV 3D, silver sinter, vent legs, 160kV X-ray, volume mm3) – this uses ENPP 2D, WLI height, Ni-P plating, automotive connectors, pit area mm2, tilt plane fit, scratch case – domain scale failure mode and speck source distinct, supporting benchmark value beyond material reskin.
