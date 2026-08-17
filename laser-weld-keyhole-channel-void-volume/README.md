# laser-weld-keyhole-channel-void-volume

## Summary
I work on laser weld factory line. Weldment after high power laser sometimes forms keyhole collapse that leaves a long narrow channel along weld direction that can leak fluid. X ray shows bright channels but blurred by X ray PSF, so channel looks larger and fuzzier than true size.

This task requires a from scratch Python script that parses custom binary .weld and reports true channel porosity volume in mm3.

## Why This Is Hard
X ray blur makes threshold counting imprecise. Low cutoff includes huge halo and overcounts by 80 to 130 percent. High cutoff misses thin channel that never gets bright enough and undercounts by 30 to 50 percent. No fixed cutoff works across files because brightness and blur width change.

Correct method is intensity conservation. Total X ray signal is conserved despite blur. So true channel voxels equals sum of background subtracted intensity divided by plateau intensity.

To make it work you must separate main channels from far specks and round gas pores using 26 neighbour connectivity formed over voxels where residual exceeds three times noise sigma, plus shape filtering. Long narrow keyhole channels along weld count, round gas pores must be ignored. Estimate background without bias from channels, estimate true plateau intensity without being fooled by noise, and decide how far faint halo extends without merging specks or round pores. That is the hard part. Thin neck case has two segments each 14x8x8 with a 2 voxel bridge that after blur is about 10 to 20 percent of plateau, so they remain distinct at 3 sigma level but join at lower thresholds; widening to 14 ensures they satisfy elongation rule.

## Approach
To recover the true channel void volume you need to:
* Parse header respecting data offset, do not hardcode 64
* Estimate background median of lower half and noise via MAD
* Form initial binary mask over voxels where residual > 3 * noise_sigma (stated level), then 26 connectivity components
* Discard components with <30 voxels as sensor flicker before shape test (prevents small speck with extents 5,7,9 from passing)
* Keep only elongated wormhole components via explicit AABB test: dx,dy,dz = extents+1 sorted d0<=d1<=d2, wormhole iff d2>=8 and d2>1.6*d0. Example 14,8,8 -> 14>12.8 passes; 6,5,5 -> 6<8 fails. Several qualifying summed.
* Gas bubbles are exact negation d2<8 or d2<=1.6*d0, drop them
* Estimate plateau from core flat region via 3x3x3 filtered top-K mean to avoid hot spikes
* Integrate halo via growth until shell mean <= noise floor, recover volume scaling by sx sy sz

Method works for varied dimensions, spacings, brightness, blur widths.

## Files
* /app/solve.py is file agent must create, prints volume as last word
* /app/data/scene.weld is sample for local dev
* environment/Dockerfile installs python and pytest (minimal, no apt-get, no ctrf dep to avoid infra flakes)
* tests/test_outputs.py is evaluation suite with 11 checks: 7 heldouts (including thin_neck 14x8x8, speck_heavy, bubble_large, pixel_count_trap, plateau_trap, halo_heavy), randomized_extra, script_exists, from_scratch (scans all *.py under /app), global shortcut

## Model Analysis / Completion Rate

* Oracle 11/11 100 percent - reference solution passes all heldouts within 1 percent via intensity conservation plus shape discrimination with 3 sigma component formation and 30 voxel flicker filter
* Naive threshold counting fails all heldouts by 80 to 130 percent over or 30 to 50 percent under
* Global conservation without speck and round pore removal fails speck heavy and shape cases by more than 3 percent because detached round pores and specks contribute extra energy
* Shape discrimination is required: long narrow keyhole channels that count versus round gas pores that must be ignored. Largest mass may be round pore, so largest mass shortcut fails. Thin neck case specifically tests that two 14x8x8 segments with 2 voxel bridge are correctly kept as wormholes per rule (was previously 12x8x8 which failed rule 12>12.8 false, now 14>12.8 true)
* Component formation threshold sensitivity: sweeping occ_thr alone previously gave pass at 4.4 sigma, -49.6 percent from 4.5 to 8.5 sigma, pass again at 9 sigma with 4.0 sitting 0.45 sigma from cliff. Now stated at 3 sigma and bridge widened to 10-20 percent of plateau, classification stable
* Flicker conflict: heldout_1 previously yielded speck extents 5,7,9 that passed rule 9>=8 and 9>1.6*5, so fixed by discarding <30 voxel components before elongation test
* Expected difficulty: avocado 2/5 to 4/5 after fix (was 0-2/5), gpt 1-3/5, opus 2-3/5 - shape rule now explicit and least ambiguous
* int16 dtype path exercised via heldout 2 to ensure both dtype branches work

## Anti Cheating
* No numpy, scipy, imaging libraries - from scratch only, including networkx, igraph, imageio, Pillow, ctypes, importlib, runpy now banned in both AST check and runtime audit hook (lists made identical)
* No hardcoded sample volume, must work on any random temp file path
* Do not open or list /tests directory - secure runner blocks /tests, test_outputs, heldout via audit hook on open and listdir
* From scratch guard now scans every *.py under /app not just /app/solve.py, per reviewer fix, so helper modules cannot bypass bans
* Secure verifier generates heldouts at runtime in temp dir with random filenames and runs solver in isolated sandbox with audit hook
* Banned import check via AST in test_from_scratch plus runtime hook identical lists, avoids false positives like Grid.walk() (walk removed from BANNED_ATTRS)
