# electroless-nickel-pit-true-area

## Description
Car connector pins plated with electroless Ni-P about twelve microns on copper. Hydrogen bubbles during plating block deposition and leave a tiny pit down to copper that fails salt spray. White light interferometer height map is blurred by Airy disk and stage wobble, so tiny deep pit looks like wide shallow cloud. Need true pit area mm2 from blurry map, not cloud size.

Input is custom binary ENPP with header magic, version, dtype, dims nx ny, spacing sx sy mm per pixel anisotropic, data offset, then pixel values x fastest. Background bright pits flipped bright. File contains one main pit which is roundish with two thin lips left and right that count as part of pit even though faint after blur, plus far specks from dust and sometimes a wide shallow scratch far away covering many pixels but dim. Ignore artefacts, main pit is dominant bright blob.

Low brightness level includes big halo and area about twice real, high level cuts lips and halo and gives half. No single level works for all panels because gain and blur and tilt and noise shift. Optics keep total brightness, normalized blur preserves integral, so true area recoverable via energy.

Tolerance three percent. Simple thresholds ten percent or more off. Stdlib only, parse with struct.

## Completion Rates
Synced from validation at commit cb57ac9 (9 configs plus guards)

- claude-opus-4-6: 2/5 = 40 percent, fails speck heavy and lips
- gpt-5: 2/5 = 40 percent, fails halo plus speck
- avocado: 1/5 = 20 percent, incomplete and halo overcount
- oracle: 3/3 = 100 percent, all 15 checks pass (including new pixel-count guard)

Overall non-oracle around 35 percent, genuinely hard, oracle confirms solvable. Naive global and count shortcuts fail by more than 3 percent on speck_heavy and scratch cases.

## Model Analysis
Binary parsing little endian header magic ENPP, version, dtype 2 int16 16 float32, nx ny, sx sy anisotropic, data offset. X fastest. From scratch check rejects numpy etc.

Failure modes: halo overcount double, lips undercount half, far dust and shallow scratch must be ignored. Dust can have more pixels than pit but less total brightness, so picker must use brightness not count, proven by scratch_shallow where dust count greater than main count but mass smaller.

Tilt: background has linear tilt per pixel, need plane fit from lower half to avoid bias.

Area: truth is fractional support times spacing, mm2 equals pixels times sx times sy with anisotropic pitch.

Threshold strategies low 85 to 125 percent over, best fixed 31 percent worst, half max 18 to 35 off. Energy method under one percent per scan.

## Anti-Cheating Analysis
Hardcoded outputs: grading generates scans at runtime from configs with geometric truth computed inside verifier, not static files. Areas differ from sample, constant fails.

Overfitting: only sample scan at data scene.enpp, hidden scans generated in temp dir random filenames input hex enpp, not byte identical.

Secure runner: verifier generates heldouts in temp dir random names and runs solver via secure runner with audithook blocking open on paths containing tests, test_outputs, heldout, GEOM_TRUTH, geometric_truth, reference_volume, blocking dir listing on tests, blocking system popen exec fork and subprocess socket, blocking banned imports numpy scipy skimage etc. Does not block data, so reading sample allowed but hardcoding sample fails.

From scratch guard: AST checks for banned modules and calls and substring checks.

Distinct from sintered silver die attach void and other void area tasks, uses WLI height and Ni-P plating chemistry and automotive connectors, not X-ray silver sinter.
