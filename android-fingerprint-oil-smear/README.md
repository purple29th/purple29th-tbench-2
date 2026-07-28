# codimango/android-fingerprint-oil-smear

## Description

Agent writes stdlib-only Python at /app/solve.py that reads under-display optical fingerprint frames in FPOS format (magic FPOS). Each frame contains a dominant oil smear from factory glue that attenuates light, plus narrow partially covered bleed strokes, plus thin halo from optical blur, plus isolated dust spots far away. Blur preserves integrated brightness, so peak is low but total energy is conserved. Ground truth in ground_truth.json is canonical count from generator: rounded sum of occupancy map covering full elliptical core, partial rim with 0.55 factor, and bleed strokes with partial occupancy, independent of any heuristic estimator. Agent must recover count by estimating background floor via median of lower half, noise sigma via MAD, dominant blob isolation via 8-direction connectivity weighted by integrated residual mass, distant dust rejection by mass and distance, peak amplitude from top smoothed values, halo growth until shell mean falls below noise sigma, and integration of residual over expanded region divided by amplitude.

Unlike OLED void OBVL which reports subvoxel volume mm3 from IR, unlike display ghost-touch CDMR which measures capacitive charge from ink pooling, and unlike battery BCTR which reports coulomb capacity mAh, this task reports pixel count of oil-covered area.

## Completion Rates

Target: oracle 4/4 within tol=max(2,3%) (errors 4,2,2,14 vs true 190,281,422,698), Avocado 3/5 60 percent (1 incomplete recursion, 1 plateau mis-estimate), Opus 4/5 80 percent (1 timeout), GPT 5/5 100 percent with light-conservation reasoning.

## Model Analysis

Typical failures: using fixed brightness threshold counting bright pixels without energy conservation, recursive flood fill hitting RecursionError, plateau amplitude estimated from max instead of median of top smoothed region, dust handling by pixel count instead of integrated mass, forgetting x-fastest int16 little endian decoding, ignoring data offset padding.

## Anti-Cheating

Hardcoded counts blocked: 4 hidden scenes have distinct counts 190,281,422,698 versus sample 251; any constant fails 3 of 4. Overfit blocked: only scene.fpos present at /app/data, hidden inputs under /tests/data mounted only at verification, copied to temporary neutral name scan.fpos with solve.py isolated in temp dir. Generator _gen.py never mounted, ground truth is canonical occupancy from _gen.py true_count rounded sum, not derived from solve.py. Reward hacking hardened via AST banned modules including pty, os and calls including breakpoint plus path-like literal scan blocking /tests, heldout, ground_truth, _gen, test_outputs when used as file paths. Data offset enforcement: hidden scenes use varying offsets 80,96,128,112 versus sample 64, so hardcoded offset 64 fails parsing.

Author: Tosin Daniel Jimoh - Android fingerprint oil smear under-display optical QA
