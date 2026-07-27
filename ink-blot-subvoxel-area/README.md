# codimango/ink-blot-subvoxel-area

## Description

Quality control for filter paper uses a single ink drop. The task is to report true inked area in square millimetres from a custom 2D scan format `.inkb` (magic `INKB`). The agent must produce `/app/solve.py` that parses the binary and prints the area as the final token.

A capillary wicking effect plus a cheap lens spreads ink far beyond the fiber saturated region. The photo appears as a dark fuzzy cloud with feathery extensions, while the reference area under ideal optics is smaller and includes thin wicking fingers that never become fully dark after blur. Simple dark pixel counting is unstable across paper batches because ink load, paper brightness, pixel pitch, and diffusion width vary per scan.

Accurate recovery needs statistical handling of paper texture, dust, and halo rather than thresholding. The benchmark grades at 3 percent relative error on hidden scans that differ from the sample in size, pitch, ink amount, and blur.

## Completion Rates

Sync'd from validation at commit 72e84de (15 trials + oracle):

| Model | Trials | Pass rate | Notes |
|-------|--------|-----------|-------|
| `claude-opus-4-8` | 5 | 2/5 = 40% | Genuine reconstruction, 3 fail |
| `gpt-5.5` | 5 | 4/5 = 80% | 4 passes |
| `meta/avocado-5.14-code` | 5 | 1/5 = 20% | 1 pass |
| `oracle` (golden `solution/solve.py`) | 3 | 3/3 = 100% | Validates grader |

Overall non-oracle 7/15 = 46.7 percent. Dominant failure is area counting instead of total ink reasoning.

## Model Analysis

This is a material science image reconstruction task without array libraries:

* **File layout:** 64 byte little-endian header, magic `INKB`, version, dtype 2 int16 or 16 float32, grid dimensions and millimetre pitch per axis, then x fastest pixels. Must be parsed with `struct`.
* **Paper texture:** scans are dominated by paper brightness that is flat plus uniform noise. Median of full image and MAD of lower half give stable background and noise scale.
* **Dust rejection:** distant dark specks are manufacturing dust. Keeping the clump with greatest summed residual using 8 connectivity removes them. This is about total ink, not pixel count.
* **Interior level:** saturated interior darkness is hidden by capillary spread plus noise. Averaging a few brightest local mean filtered values gives stable level, unlike raw peak.
* **Feather handling:** faint wicking tails still belong to blot. Growing outward while surrounding ring average stays above noise floor captures them without connecting to remote specks.
* **Physical units:** final area multiplies pixel estimate by `sx*sy` from header. Fixed cutoffs (absolute, fractional, Otsu, half max) deviate >12 percent worst case, while physics aware method stays <1 percent.

## Anti-Cheating Analysis

* Sample area differs from hidden areas, so memorizing sample fails. Hidden cases are synthesized fresh at grading time with random names in a temporary directory.
* Execution is confined to that temporary directory. Attempts to read the test tree or import imaging or subprocess modules are blocked.
* Source must be standard library only. Use of array, imaging, or graph libraries, shell execution, or path hiding tricks causes from scratch check to fail.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
